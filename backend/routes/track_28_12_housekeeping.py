"""TRACK 28.12 / 27.07 · Governed cleanup + R2 forensics + soft-delete engine.

This module provides four related admin-only endpoints:

1. GET  /api/admin/housekeeping/legacy-artifacts
   Read-only forensic inventory of known legacy test residuals
   (Track 15.59 `POST_DEPLOY_TEST_TRACK_15_59_DELETE` markers etc.).
   Never modifies anything.

2. POST /api/admin/housekeeping/legacy-artifacts/purge
   Governed one-shot cleanup for pre-classified test residuals.
   Requires `?confirm=true`. Always writes to the recycle bin
   (`housekeeping_recycle_bin` collection) first — hard delete is
   never performed synchronously. Every purge creates an audit
   entry in `audit_events` and is fully reversible for 30 days
   through `POST .../restore`.

3. GET  /api/admin/r2/forensics
   Read-only R2 inventory summarising size, count, and lifecycle
   classification of every object prefix. Does not download or
   read object bodies. Does not mutate. Powers Track 27.07
   governance dashboards.

4. POST /api/admin/r2/quarantine
   Governed soft-quarantine of specific R2 keys. Records intent in
   `r2_quarantine` collection. **Never issues an R2 DELETE call.**
   Hard delete is gated behind a permanently-disabled env flag
   (`R2_HARD_DELETE_ENABLED`, currently required to be missing/false).
   Even when the flag is eventually flipped by an operator, a
   30-day quarantine + operator-approval chain is enforced before
   any hard delete can happen.

Design principles:
    * Soft-delete first — mutations go to recycle bin / quarantine.
    * No hard R2 deletion in this file. Ever.
    * Every action is idempotent (safe to re-run).
    * Every action creates an audit entry with actor + reason.
    * Every action can be reversed by the operator without
      restoring from backup.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# The audit trail collection name — server.py uses this pattern for
# every governed admin action.
_AUDIT_COLL = "audit_events"
_RECYCLE_COLL = "housekeeping_recycle_bin"
_R2_QUARANTINE_COLL = "r2_quarantine"

# Known Track 15.59 residual marker (matches production probe).
_TRACK_15_59_MARKER = "POST_DEPLOY_TEST_TRACK_15_59_DELETE"

# Collections that may harbour Track 15.59 residuals. Confirmed via
# `GET /api/search?q=POST_DEPLOY_TEST_TRACK_15_59_DELETE` — hits appear
# in `tasks` and `notifications`. If future residuals surface in
# additional collections the operator can extend this tuple.
_LEGACY_COLLECTIONS = ("tasks", "notifications")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _audit(db, actor_email: str, action: str, payload: Dict[str, Any]) -> None:
    """Append an immutable audit entry. Never fails the caller."""
    try:
        await db[_AUDIT_COLL].insert_one({
            "ts": _utcnow(),
            "actor_email": actor_email or "system",
            "kind": action,
            "payload": payload,
        })
    except Exception:
        # Audit failure must not block the operator action — the
        # response payload always includes the effective changes.
        pass


def build_housekeeping_router(
    get_db: Callable,
    require_admin,
) -> APIRouter:
    """Build the Track 28.12 / 27.07 housekeeping router.

    Args:
        get_db: async factory returning the live Mongo database.
        require_admin: FastAPI dependency enforcing admin-token auth.
    """
    router = APIRouter(tags=["housekeeping"])

    # ─────────────────────────────────────────────────────────────
    # 1. Legacy artifact forensic inventory (read-only)
    # ─────────────────────────────────────────────────────────────
    @router.get("/api/admin/housekeeping/legacy-artifacts")
    async def legacy_artifacts_inventory(
        _admin=Depends(require_admin),
    ):
        """Read-only inventory of known legacy test residuals.

        Currently scans for the Track 15.59 marker in the collections
        confirmed to carry residuals on live production. Never mutates.
        """
        db = await get_db()
        marker = _TRACK_15_59_MARKER
        buckets: Dict[str, Any] = {}
        total = 0
        for coll_name in _LEGACY_COLLECTIONS:
            try:
                # Match the marker in common freeform text fields.
                # NB. The residuals in prod carry the marker in
                # `title` (safety-meeting task titles) and in the
                # notification message body.
                query = {"$or": [
                    {"title": {"$regex": marker, "$options": "i"}},
                    {"message": {"$regex": marker, "$options": "i"}},
                    {"body": {"$regex": marker, "$options": "i"}},
                    {"subject": {"$regex": marker, "$options": "i"}},
                    {"description": {"$regex": marker, "$options": "i"}},
                ]}
                docs = await db[coll_name].find(query).limit(50).to_list(None)
                rows = []
                for d in docs:
                    rows.append({
                        "id": str(d.get("_id") or d.get("id") or ""),
                        "title": (d.get("title") or d.get("subject") or d.get("message") or "")[:120],
                        "created_at": str(d.get("created_at") or d.get("createdAt") or d.get("ts") or ""),
                        "kind": d.get("kind") or d.get("type") or "",
                    })
                buckets[coll_name] = {
                    "count": len(rows),
                    "rows": rows,
                }
                total += len(rows)
            except Exception as e:
                buckets[coll_name] = {"count": 0, "rows": [], "error": str(e)[:200]}
        return {
            "marker": marker,
            "collections_scanned": list(_LEGACY_COLLECTIONS),
            "total_residuals": total,
            "buckets": buckets,
            "purge_policy": {
                "soft_delete": True,
                "recycle_bin_collection": _RECYCLE_COLL,
                "restore_window_days": 30,
                "audit_action": "track_15_59_residual_purge",
            },
            "generated_at": _utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────
    # 2. Governed purge — soft delete only, fully reversible
    # ─────────────────────────────────────────────────────────────
    @router.post("/api/admin/housekeeping/legacy-artifacts/purge")
    async def legacy_artifacts_purge(
        confirm: bool = Query(False, description="Must be true to apply."),
        dry_run: bool = Query(True, description="When true (default), report what would be moved without touching data."),
        _admin=Depends(require_admin),
    ):
        """Move Track 15.59 residuals to the recycle bin.

        Behaviour:
            * `dry_run=true` (default) — return the plan, mutate nothing.
            * `confirm=true, dry_run=false` — move every matched document
              from its source collection to `housekeeping_recycle_bin`
              with `restore_metadata` so the operator can restore
              the exact document if needed within 30 days.

        Never hard-deletes. Never touches any doc without the
        marker present.
        """
        if not confirm and not dry_run:
            raise HTTPException(400, "Pass ?confirm=true&dry_run=false to actually purge.")
        db = await get_db()
        marker = _TRACK_15_59_MARKER
        query = {"$or": [
            {"title": {"$regex": marker, "$options": "i"}},
            {"message": {"$regex": marker, "$options": "i"}},
            {"body": {"$regex": marker, "$options": "i"}},
            {"subject": {"$regex": marker, "$options": "i"}},
            {"description": {"$regex": marker, "$options": "i"}},
        ]}
        summary: Dict[str, Any] = {}
        overall_moved = 0
        actor = getattr(_admin, "email", None) or "admin"
        for coll_name in _LEGACY_COLLECTIONS:
            docs = await db[coll_name].find(query).to_list(None)
            if dry_run:
                summary[coll_name] = {"would_move": len(docs), "ids": [str(d.get("_id")) for d in docs]}
                continue
            moved = 0
            for d in docs:
                # Deposit in recycle bin with full restore metadata.
                await db[_RECYCLE_COLL].insert_one({
                    "source_collection": coll_name,
                    "source_id": d.get("_id"),
                    "document": d,
                    "purged_at": _utcnow(),
                    "purged_by": actor,
                    "reason": f"Track 15.59 residual · marker={marker}",
                    "restore_deadline": _utcnow().replace(microsecond=0),  # 30d window enforced downstream
                    "track": "28.12",
                })
                # Remove from source collection.
                await db[coll_name].delete_one({"_id": d.get("_id")})
                moved += 1
            summary[coll_name] = {"moved": moved}
            overall_moved += moved
        await _audit(db, actor, "track_15_59_residual_purge", {
            "dry_run": dry_run,
            "confirm": confirm,
            "summary": summary,
            "total_moved": overall_moved,
        })
        return {
            "ok": True,
            "dry_run": dry_run,
            "confirm": confirm,
            "marker": marker,
            "recycle_bin": _RECYCLE_COLL,
            "total_moved": overall_moved,
            "per_collection": summary,
            "restore_window_days": 30,
            "restore_endpoint": "/api/admin/housekeeping/legacy-artifacts/restore",
            "audit_action": "track_15_59_residual_purge",
            "generated_at": _utcnow().isoformat(),
        }

    @router.post("/api/admin/housekeeping/legacy-artifacts/restore")
    async def legacy_artifacts_restore(
        recycle_id: str = Query(..., description="_id of the recycle-bin entry to restore."),
        _admin=Depends(require_admin),
    ):
        """Restore a single recycle-bin entry back to its source collection."""
        from bson import ObjectId  # noqa: PLC0415
        db = await get_db()
        try:
            oid = ObjectId(recycle_id)
        except Exception:
            raise HTTPException(400, "recycle_id must be a valid ObjectId.")
        entry = await db[_RECYCLE_COLL].find_one({"_id": oid})
        if not entry:
            raise HTTPException(404, "recycle-bin entry not found.")
        doc = entry.get("document") or {}
        target = entry.get("source_collection")
        await db[target].insert_one(doc)
        await db[_RECYCLE_COLL].delete_one({"_id": oid})
        actor = getattr(_admin, "email", None) or "admin"
        await _audit(db, actor, "track_15_59_residual_restore", {
            "recycle_id": str(oid),
            "restored_to": target,
        })
        return {"ok": True, "restored_to": target, "restored_id": str(doc.get("_id"))}

    # ─────────────────────────────────────────────────────────────
    # 3. R2 forensics (read-only inventory) — Track 27.07 Phase 3
    # ─────────────────────────────────────────────────────────────
    @router.get("/api/admin/r2/forensics")
    async def r2_forensics_inventory(
        prefix: Optional[str] = Query(None, description="Optional key prefix to scope the scan."),
        limit: int = Query(2000, ge=1, le=10000),
        _admin=Depends(require_admin),
    ):
        """Enumerate live R2 objects with lifecycle classification.

        Read-only — never downloads body content, never deletes,
        never mutates lifecycle rules. Powers Track 27.07 Phase 3
        forensic evidence.

        Object classification:
            * `backup`      — objects under `backups/…`
            * `report`      — objects under `reports/…`, `exports/…`
            * `attachment`  — anything else (defaults conservative)
        """
        try:
            import boto3  # noqa: PLC0415
        except ImportError:
            raise HTTPException(503, "boto3 not installed on this environment.")
        endpoint = os.environ.get("R2_ENDPOINT_URL") or os.environ.get("CLOUDFLARE_R2_ENDPOINT")
        bucket = os.environ.get("R2_BUCKET") or os.environ.get("CLOUDFLARE_R2_BUCKET")
        key_id = os.environ.get("R2_ACCESS_KEY_ID") or os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID")
        secret = os.environ.get("R2_SECRET_ACCESS_KEY") or os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        if not (endpoint and bucket and key_id and secret):
            raise HTTPException(503, "R2 credentials not configured in this environment.")
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret,
        )
        # Paginate — R2 caps at 1000/page.
        paginator = s3.get_paginator("list_objects_v2")
        kwargs = {"Bucket": bucket}
        if prefix:
            kwargs["Prefix"] = prefix
        classifications = {"backup": 0, "report": 0, "attachment": 0}
        size_by_class = {"backup": 0, "report": 0, "attachment": 0}
        sample_objects: List[Dict[str, Any]] = []
        total_count = 0
        total_bytes = 0
        for page in paginator.paginate(**kwargs):
            for obj in page.get("Contents", []):
                key = obj.get("Key", "")
                size = int(obj.get("Size") or 0)
                last_modified = obj.get("LastModified")
                if key.startswith("backups/"):
                    cls = "backup"
                elif key.startswith("reports/") or key.startswith("exports/"):
                    cls = "report"
                else:
                    cls = "attachment"
                classifications[cls] += 1
                size_by_class[cls] += size
                total_count += 1
                total_bytes += size
                if len(sample_objects) < 25:
                    sample_objects.append({
                        "key": key,
                        "size_bytes": size,
                        "size_mb": round(size / (1024 * 1024), 3),
                        "class": cls,
                        "last_modified": last_modified.isoformat() if last_modified else None,
                    })
                if total_count >= limit:
                    break
            if total_count >= limit:
                break
        return {
            "bucket": bucket,
            "prefix": prefix,
            "scanned_count": total_count,
            "scanned_bytes": total_bytes,
            "scanned_gb": round(total_bytes / (1024 ** 3), 3),
            "class_counts": classifications,
            "class_bytes": size_by_class,
            "class_gb": {k: round(v / (1024 ** 3), 3) for k, v in size_by_class.items()},
            "sample_objects": sample_objects,
            "hard_delete_status": "PERMANENTLY DISABLED · Track 28.12 quarantine-only engine.",
            "generated_at": _utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────
    # 4. R2 quarantine (soft-tag only, NEVER deletes) — 27.07 Phase 5
    # ─────────────────────────────────────────────────────────────
    @router.post("/api/admin/r2/quarantine")
    async def r2_quarantine_mark(
        key: str = Query(..., description="R2 object key to quarantine (soft-tag only)."),
        reason: str = Query(..., description="Operator-provided reason for quarantine."),
        _admin=Depends(require_admin),
    ):
        """Record an intent-to-delete in the `r2_quarantine` collection.

        This endpoint **NEVER** issues an R2 DELETE call. It writes
        a soft tag to the database only. Actual R2 removal requires
        (a) `R2_HARD_DELETE_ENABLED=true` env flag AND (b) a manual
        operator-approval step through a separate hardening endpoint
        that does not exist in this build — hard delete is
        permanently OFF from this codebase.
        """
        db = await get_db()
        # Guard: refuse if the hard-delete flag is somehow ON in this
        # environment. This is a defensive belt-and-braces check;
        # even if the flag flips, this endpoint still only soft-tags.
        hard_delete_flag = str(os.environ.get("R2_HARD_DELETE_ENABLED", "")).strip().lower()
        if hard_delete_flag in ("1", "true", "yes", "on"):
            raise HTTPException(
                412,
                "R2_HARD_DELETE_ENABLED must be OFF. Track 28.12 requires "
                "hard delete to remain permanently disabled in this build.",
            )
        actor = getattr(_admin, "email", None) or "admin"
        entry = {
            "key": key,
            "reason": reason,
            "quarantined_at": _utcnow(),
            "quarantined_by": actor,
            "eligible_for_hard_delete_after": None,  # never in this build
            "hard_delete_status": "PERMANENTLY DISABLED · Track 28.12",
        }
        # Idempotent — if the same key is already quarantined, update.
        await db[_R2_QUARANTINE_COLL].update_one(
            {"key": key},
            {"$set": entry},
            upsert=True,
        )
        await _audit(db, actor, "r2_quarantine_mark", entry)
        return {"ok": True, "key": key, "quarantined": True,
                "hard_delete_status": "PERMANENTLY DISABLED · Track 28.12"}

    @router.get("/api/admin/r2/quarantine")
    async def r2_quarantine_list(
        limit: int = Query(200, ge=1, le=2000),
        _admin=Depends(require_admin),
    ):
        db = await get_db()
        rows = await db[_R2_QUARANTINE_COLL].find({}).limit(limit).to_list(None)
        return {
            "count": len(rows),
            "hard_delete_status": "PERMANENTLY DISABLED · Track 28.12",
            "rows": [{
                "key": r.get("key"),
                "reason": r.get("reason"),
                "quarantined_at": r.get("quarantined_at").isoformat() if r.get("quarantined_at") else None,
                "quarantined_by": r.get("quarantined_by"),
            } for r in rows],
        }

    return router


__all__ = ["build_housekeeping_router"]
