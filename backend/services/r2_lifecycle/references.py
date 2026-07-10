"""
Phase 2/3 · Ownership resolver + database cross-reference.

This module holds the EXTENSIBLE registry of Mongo collections that
legitimately reference R2 objects. Each source describes:

- `collection`     — the Mongo collection name.
- `owner`          — the human-readable owner label (e.g. "Daily Report").
- `feature`        — the platform feature (e.g. "daily_reports").
- `paths`          — a list of JSONPath-style dot paths where R2 refs
                     may appear. Wildcards `*` traverse arrays.
- `ref_scheme`     — the string scheme this source uses ("photo://",
                     "r2://", or "raw_key" for direct S3 keys).

The walker extracts every R2 key mentioned by any document in the
listed collections and persists them to `r2_references`, keyed by the
extracted R2 key. This is the source-of-truth Mongo → R2 back-index
that the classifier consumes.

Adding a new source is a one-line append to `REFERENCE_SOURCES`;
no code change elsewhere.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# ── Reference source registry ──────────────────────────────────────────
@dataclass
class ReferenceSource:
    collection: str
    owner: str
    feature: str
    paths: List[str]
    ref_scheme: str = "photo://"  # photo:// | r2:// | raw_key
    doc_id_field: str = "id"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "collection": self.collection,
            "owner": self.owner,
            "feature": self.feature,
            "paths": self.paths,
            "ref_scheme": self.ref_scheme,
        }


# Extend this list — never hardcode outside it.
REFERENCE_SOURCES: List[ReferenceSource] = [
    # `photos` collection stayed empty in practice — daily_reports/etc.
    # store photo:// URIs directly in top-level arrays. Kept here for
    # forward compatibility (any future photo-index rebuild lands here).
    ReferenceSource("photos",                "Photo",             "photos",           ["storage_ref", "url", "photo_ref"]),
    # `daily_reports.photos` is a list of raw photo:// strings.
    ReferenceSource("daily_reports",         "Daily Report",      "daily_reports",    ["photos.*", "attachments.*"]),
    ReferenceSource("meetings",              "Meeting",           "meetings",         ["photos.*", "attachments.*"]),
    ReferenceSource("qaqc_inspections",      "QA/QC Inspection",  "qaqc",             ["photos.*", "photo_captions.*"]),
    ReferenceSource("site_inspections",      "Site Inspection",   "site_inspections", ["photos.*", "attachments.*"]),
    # `incidents.photos` is base64 data URIs — no R2 reference. Keep
    # attachments-style paths only in case a future migration lands.
    ReferenceSource("incidents",             "Incident",          "incidents",        ["evidence.*", "attachments.*"]),
    ReferenceSource("training_records",      "Training Record",   "training",         ["media.*", "attachments.*"]),
    # Documents with raw-key pattern (bucket embedded in the key).
    ReferenceSource("equipment_documents",   "Equipment Document","equipment",        ["storage_ref", "url", "file_ref"]),
    ReferenceSource("asset_documents",       "Asset Document",    "assets",           ["storage_ref", "url", "file_ref"]),
    ReferenceSource("dispatch_continuity",   "Dispatch Evidence", "dispatch",         ["photos.*", "attachments.*"]),
    ReferenceSource("legacy_imports",        "Historical Import", "legacy_imports",   ["source_document_ref", "photos.*"]),
    # Operational attachments — uses `r2_key` (raw key, not photo:// URI).
    ReferenceSource("operational_attachments","Operational Attachment","attachments", ["r2_key"], ref_scheme="raw_key"),
    # Carrier + driver document store — uses `file_ref` (photo:// URI).
    # `file_key` also has R2 key but with bucket prefix, so keep photo:// path.
    ReferenceSource("carrier_documents",     "Carrier Document",  "carriers",         ["file_ref"]),
    ReferenceSource("driver_documents",      "Driver Document",   "drivers",          ["file_ref"]),
    # HR employee records — uses `source_file_ref` (photo:// URI).
    ReferenceSource("employee_records",      "Employee Record",   "hr",               ["source_file_ref"]),
    ReferenceSource("promo_assets",          "Promo Asset",       "promo_assets",     ["storage_ref", "url"]),
    ReferenceSource("pdf_packages",          "PDF Package",       "pdf_packages",     ["storage_ref", "url"]),
    ReferenceSource("exports",               "Export",            "exports",          ["storage_ref", "url"]),
    # Backups — the recovery archives themselves. These are BACKUP_PROTECTED.
    ReferenceSource("backup_health",         "Backup Archive",    "backups",          ["filename", "key", "url"], ref_scheme="raw_key"),
    ReferenceSource("recovery_snapshots",    "Recovery Snapshot", "recovery",         ["archive_key", "key"], ref_scheme="raw_key"),
]


# ── Reference extraction ───────────────────────────────────────────────
_PHOTO_REF_RE = re.compile(r"^photo://([^/]+)/(.+)$")
_R2_REF_RE = re.compile(r"^r2://([^/]+)/(.+)$")


def _extract_key(ref: Any, scheme: str) -> Optional[str]:
    """Return the R2 key portion of ``ref``, or None if ``ref`` doesn't
    match the expected scheme.  Empty strings and non-strings return
    None (they're not R2 references — they're empty fields)."""
    if not ref or not isinstance(ref, str):
        return None
    if scheme == "photo://":
        m = _PHOTO_REF_RE.match(ref)
        return m.group(2) if m else None
    if scheme == "r2://":
        m = _R2_REF_RE.match(ref)
        return m.group(2) if m else None
    if scheme == "raw_key":
        # Direct S3 key — accept if it looks like a path (no scheme prefix).
        if "://" in ref:
            return None
        return ref.lstrip("/")
    return None


def _walk_path(doc: Dict[str, Any], path: str) -> Iterable[Any]:
    """Yield every value at the JSONPath-style dot path in ``doc``.
    A `*` segment expands array elements. Missing keys are silent."""
    parts = path.split(".")
    stack: List[Tuple[int, Any]] = [(0, doc)]
    while stack:
        depth, node = stack.pop()
        if depth == len(parts):
            yield node
            continue
        seg = parts[depth]
        if seg == "*":
            if isinstance(node, list):
                for item in node:
                    stack.append((depth + 1, item))
            continue
        if isinstance(node, dict) and seg in node:
            stack.append((depth + 1, node[seg]))


async def scan_mongo_references(db, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Walk every registered reference source and persist a fresh
    Mongo → R2 back-index into `r2_references`. Prior rows are
    truncated so stale references don't cause false VERIFIED_OWNER
    classifications."""
    now = now or datetime.now(timezone.utc)
    run_id = f"ref-{uuid4().hex[:12]}"

    await db.r2_references.delete_many({})

    total_sources_scanned = 0
    total_refs_found = 0
    by_source: Dict[str, int] = {}
    ops: List[Dict[str, Any]] = []

    for source in REFERENCE_SOURCES:
        try:
            total_sources_scanned += 1
            source_hits = 0
            cursor = db[source.collection].find({}, {"_id": 0} | {p.split(".")[0]: 1 for p in source.paths} | {source.doc_id_field: 1})
            async for doc in cursor:
                doc_id = doc.get(source.doc_id_field) or doc.get("_id")
                for p in source.paths:
                    for val in _walk_path(doc, p):
                        key = _extract_key(val, source.ref_scheme)
                        if not key:
                            continue
                        ops.append({
                            "r2_key": key,
                            "collection": source.collection,
                            "owner": source.owner,
                            "feature": source.feature,
                            "doc_id": str(doc_id) if doc_id is not None else None,
                            "field_path": p,
                            "raw_ref": val if isinstance(val, str) else None,
                            "captured_at": now.isoformat(),
                            "run_id": run_id,
                        })
                        source_hits += 1
                        total_refs_found += 1
                        if len(ops) >= 500:
                            await db.r2_references.insert_many(ops, ordered=False)
                            ops.clear()
            by_source[source.collection] = source_hits
        except Exception as e:  # noqa: BLE001
            # Missing collection is fine — just report zero refs from it.
            logger.info(
                "[r2-references] skipping %s (source unavailable): %s",
                source.collection, e,
            )
            by_source[source.collection] = 0
    if ops:
        await db.r2_references.insert_many(ops, ordered=False)

    summary = {
        "run_id": run_id,
        "kind": "references",
        "started_at": now.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "sources_scanned": total_sources_scanned,
        "references_found": total_refs_found,
        "refs_by_source": by_source,
    }
    await db.r2_lifecycle_runs.insert_one(dict(summary))
    return summary


async def reference_summary(db) -> Dict[str, Any]:
    row = await db.r2_lifecycle_runs.find_one(
        {"kind": "references"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    return row or {"has_data": False}
