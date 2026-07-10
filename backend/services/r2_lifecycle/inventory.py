"""
Phase 1 · Complete R2 inventory walker.

Contract
--------
- Paginated listing via boto3 ``list_objects_v2`` (never assumes 1000-key
  cap is enough).
- Persists one document per object to the `r2_inventory` collection with
  `_id = key` (idempotent — repeated scans upsert without producing
  duplicates).
- Records the last-seen-run so we can identify objects that disappeared
  (i.e. deleted outside our pipeline).
- ZERO mutations to R2.  This is read-only.

The client is injected via `IR2Client` so unit tests can pass a fake and
the boto3 dependency stays lazy.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional, Protocol
from uuid import uuid4

logger = logging.getLogger(__name__)


# ── R2 client protocol ─────────────────────────────────────────────────
class IR2Client(Protocol):
    """The minimum surface of a boto3 S3 client the walker needs."""

    def list_objects_v2(self, **kwargs) -> Dict[str, Any]: ...  # pragma: no cover
    def head_object(self, **kwargs) -> Dict[str, Any]: ...  # pragma: no cover


# ── Prefix / project extraction ────────────────────────────────────────
_PROJECT_RE = re.compile(r"(?<![0-9])(\d{2}-\d{2,3})(?![0-9])")


def _top_prefix(key: str) -> str:
    """Return the first path segment, or `<root>` for keys without a
    slash.  Used for the executive `GB by prefix` roll-up."""
    if "/" not in key:
        return "<root>"
    return key.split("/", 1)[0]


def _project_number(key: str) -> Optional[str]:
    """Extract a project number of the form `NN-NNN` (or `NN-NN`) from
    the key. Returns None if no match — the classifier treats absence
    as "no project owner"."""
    m = _PROJECT_RE.search(key)
    return m.group(1) if m else None


def _year(last_modified: Optional[datetime]) -> Optional[int]:
    if not last_modified:
        return None
    return last_modified.year


# ── Scan ────────────────────────────────────────────────────────────────
@dataclass
class InventoryPage:
    """A single boto3 page projected into the fields we care about."""
    items: List[Dict[str, Any]]
    is_last: bool
    continuation_token: Optional[str]


async def _iter_pages(
    client: IR2Client,
    bucket: str,
    max_pages: Optional[int] = None,
) -> AsyncIterator[InventoryPage]:
    """Async wrapper around boto3's synchronous ``list_objects_v2`` so
    the caller can await pages without blocking the event loop."""
    token: Optional[str] = None
    page_no = 0
    while True:
        kwargs: Dict[str, Any] = {"Bucket": bucket, "MaxKeys": 1000}
        if token:
            kwargs["ContinuationToken"] = token
        resp = await asyncio.to_thread(client.list_objects_v2, **kwargs)
        contents = resp.get("Contents") or []
        yield InventoryPage(
            items=contents,
            is_last=not resp.get("IsTruncated", False),
            continuation_token=resp.get("NextContinuationToken"),
        )
        page_no += 1
        if not resp.get("IsTruncated", False):
            return
        if max_pages is not None and page_no >= max_pages:
            return
        token = resp.get("NextContinuationToken")


async def run_inventory_scan(
    db,
    r2_client: IR2Client,
    bucket: str,
    *,
    max_pages: Optional[int] = None,
    initiator: str = "manual",
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Walk the entire R2 bucket, upsert one doc per object into
    `r2_inventory`, and record a run summary in `r2_lifecycle_runs`.

    Returns the run summary."""
    now = now or datetime.now(timezone.utc)
    run_id = f"inv-{uuid4().hex[:12]}"
    total_objects = 0
    total_bytes = 0
    prefixes: Dict[str, int] = {}
    ops: List[Any] = []

    async for page in _iter_pages(r2_client, bucket, max_pages=max_pages):
        for it in page.items:
            key = it["Key"]
            size = int(it.get("Size") or 0)
            etag = (it.get("ETag") or "").strip('"')
            last_modified = it.get("LastModified")
            if isinstance(last_modified, datetime) and last_modified.tzinfo is None:
                last_modified = last_modified.replace(tzinfo=timezone.utc)
            storage_class = it.get("StorageClass") or "STANDARD"
            prefix = _top_prefix(key)
            project = _project_number(key)
            year = _year(last_modified)

            total_objects += 1
            total_bytes += size
            prefixes[prefix] = prefixes.get(prefix, 0) + size

            ops.append({
                "filter": {"_id": key},
                "update": {
                    "$set": {
                        "bucket": bucket,
                        "key": key,
                        "prefix": prefix,
                        "project_number": project,
                        "year": year,
                        "size": size,
                        "etag": etag,
                        "last_modified": last_modified.isoformat() if isinstance(last_modified, datetime) else None,
                        "storage_class": storage_class,
                        "last_seen_run_id": run_id,
                        "last_seen_at": now.isoformat(),
                    },
                    "$setOnInsert": {
                        "first_seen_at": now.isoformat(),
                        "first_seen_run_id": run_id,
                    },
                },
                "upsert": True,
            })
            if len(ops) >= 500:
                await _flush_upserts(db, ops)
                ops.clear()
    if ops:
        await _flush_upserts(db, ops)

    summary = {
        "run_id": run_id,
        "kind": "inventory",
        "bucket": bucket,
        "started_at": now.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total_objects": total_objects,
        "total_bytes": total_bytes,
        "top_prefixes": sorted(
            [{"prefix": k, "bytes": v} for k, v in prefixes.items()],
            key=lambda r: r["bytes"], reverse=True,
        )[:20],
        "initiator": initiator,
    }
    await db.r2_lifecycle_runs.insert_one(dict(summary))
    return summary


async def _flush_upserts(db, ops: Iterable[Dict[str, Any]]) -> None:
    """Small wrapper so we can swap for bulk_write later without
    plumbing every caller."""
    from pymongo import UpdateOne  # noqa: PLC0415 — lazy import
    bulk = [UpdateOne(o["filter"], o["update"], upsert=o["upsert"]) for o in ops]
    if bulk:
        await db.r2_inventory.bulk_write(bulk, ordered=False)


# ── Read-side helpers ──────────────────────────────────────────────────
async def latest_run_id(db, kind: str = "inventory") -> Optional[str]:
    row = await db.r2_lifecycle_runs.find_one(
        {"kind": kind}, {"_id": 0, "run_id": 1}, sort=[("completed_at", -1)],
    )
    return row.get("run_id") if row else None


async def inventory_summary(db) -> Dict[str, Any]:
    """Return the persisted latest run summary, or an empty structure
    when no scan has ever been executed."""
    row = await db.r2_lifecycle_runs.find_one(
        {"kind": "inventory"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    if not row:
        return {
            "has_data": False,
            "total_objects": 0,
            "total_bytes": 0,
            "top_prefixes": [],
        }
    row["has_data"] = True
    return row
