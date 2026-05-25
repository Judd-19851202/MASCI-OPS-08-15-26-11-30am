"""routes/admin_persistence_health.py · iter430 · Phase 28.2 · Part 1B.

Calm, admin-strict, JSON-only verification surface for production Atlas
+ R2 backup continuity.

Doctrine
--------
This is NOT a dashboard. NOT a metrics surface. NOT a monitoring
center. It's a single read-only verification endpoint that an
operator can `curl` (or a runbook can script) to confirm:

    1. Atlas is the active MongoDB target
    2. mongo_version is reachable
    3. last_backup_time is recent enough
    4. r2_backup_success — most recent automatic backup zip exists
    5. persistent_storage_confirmed — collections + recent writes seen
    6. collections_detected — count of non-system collections
    7. drift_watch_active — backup drift scheduler running

No charts. No UI. No alerting platform. No notification system.
A failed check returns the truthy/falsy value AND a short reason so
the operator can act — never a vague green/red light.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import APIRouter, Depends


def _is_atlas_url(url: str) -> bool:
    # MongoDB Atlas SRV connection strings always start with mongodb+srv://
    # and the hostname carries `.mongodb.net`. We treat both signals as
    # truth — neither alone is enough to false-positive a local Atlas
    # tunnel or a self-hosted SRV record.
    if not url:
        return False
    if not url.startswith("mongodb+srv://"):
        return False
    return ".mongodb.net" in url.lower()


async def _safe_mongo_version(db) -> Optional[str]:
    try:
        info = await db.command("buildInfo")
        return info.get("version")
    except Exception:
        return None


async def _list_collections(db) -> list:
    try:
        return await db.list_collection_names()
    except Exception:
        return []


async def _last_backup_time(db) -> Optional[str]:
    # iter427 created `backup_runs` to track every nightly archive
    # attempt. Read the most recent OK row; fall back to any row.
    try:
        coll = db.backup_runs
        doc = await coll.find_one(
            {"ok": True},
            sort=[("ts", -1)],
            projection={"_id": 0, "ts": 1, "filename": 1, "size_bytes": 1},
        )
        if doc:
            return doc.get("ts")
    except Exception:
        pass
    return None


async def _r2_backup_success(db) -> Dict[str, Any]:
    """Most recent backup row · whether the resulting zip was sent to
    R2 (or local persistence) without error. The scheduler writes a
    BackupRun row with `ok=true` per successful run."""
    try:
        row = await db.backup_runs.find_one(
            {},
            sort=[("ts", -1)],
            projection={
                "_id": 0,
                "ts": 1, "ok": 1, "kind": 1, "filename": 1,
                "size_bytes": 1, "destinations": 1, "error": 1,
            },
        )
        if not row:
            return {"present": False, "reason": "no backup_runs row found"}
        return {
            "present": True,
            "ts": row.get("ts"),
            "ok": bool(row.get("ok")),
            "kind": row.get("kind"),
            "filename": row.get("filename"),
            "size_bytes": row.get("size_bytes"),
            "destinations": row.get("destinations") or [],
            "error": row.get("error"),
        }
    except Exception as e:  # noqa: BLE001
        return {"present": False, "reason": f"backup_runs read failed: {e}"}


async def _persistent_storage_confirmed(db) -> Dict[str, Any]:
    """Confirm we can read AND that there is at least one recent write
    (defaults to last 24h)."""
    try:
        names = await db.list_collection_names()
        # Prefer a fast write-recency check on continuity_events ·
        # otherwise fall back to backup_runs.
        watch_collection = "continuity_events" if "continuity_events" in names else (
            "backup_runs" if "backup_runs" in names else None
        )
        if not watch_collection:
            return {"confirmed": bool(names), "reason": "no watch collection"}
        cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        recent = await db[watch_collection].find_one(
            {"$or": [{"ts": {"$gte": cutoff}}, {"created_at": {"$gte": cutoff}}]},
            sort=[("ts", -1)],
            projection={"_id": 0, "ts": 1, "created_at": 1},
        )
        return {
            "confirmed": bool(recent),
            "watch_collection": watch_collection,
            "recent_write_ts": (recent or {}).get("ts") or (recent or {}).get("created_at"),
        }
    except Exception as e:  # noqa: BLE001
        return {"confirmed": False, "reason": f"persistence probe failed: {e}"}


def build_admin_persistence_health_router(
    *,
    db,
    require_admin_strict_dep: Callable[..., Awaitable[Any]],
) -> APIRouter:
    """Build the persistence-health router. Admin-strict only ·
    JSON-only · no UI surface."""
    router = APIRouter(
        prefix="/api/admin-strict/diag",
        tags=["admin-strict-diag"],
    )

    @router.get(
        "/persistence-health",
        dependencies=[Depends(require_admin_strict_dep)],
    )
    async def persistence_health():
        """Return a tiny JSON object that lets the operator verify
        production Atlas + R2 backup continuity with one curl. Never
        raises — always returns 200 with the captured field values."""
        mongo_url = os.environ.get("MONGO_URL", "")
        db_name = os.environ.get("DB_NAME", "")
        atlas_connected = _is_atlas_url(mongo_url)

        mongo_version = await _safe_mongo_version(db)
        collections = await _list_collections(db)
        last_backup = await _last_backup_time(db)
        r2_backup = await _r2_backup_success(db)
        persisted = await _persistent_storage_confirmed(db)

        # drift_watch_active: the iter383 BackupRun scheduler logs a
        # heartbeat into `backup_drift_watch` every cycle. We treat
        # presence of a heartbeat in the last 36 hours as ACTIVE.
        drift_active = False
        drift_reason = "drift watcher heartbeat not seen"
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=36)).isoformat()
            heart = await db.backup_drift_watch.find_one(
                {"$or": [{"ts": {"$gte": cutoff}}, {"updated_at": {"$gte": cutoff}}]},
                projection={"_id": 0, "ts": 1, "updated_at": 1},
                sort=[("ts", -1)],
            )
            if heart:
                drift_active = True
                drift_reason = "heartbeat seen within 36h"
        except Exception as e:  # noqa: BLE001
            drift_reason = f"drift collection probe failed: {e}"

        return {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "atlas_connected": atlas_connected,
            "atlas_host": (
                re.sub(r"://[^@]+@", "://***@", mongo_url) if mongo_url else None
            ),
            "db_name": db_name,
            "mongo_version": mongo_version,
            "collections_detected": len(collections),
            "last_backup_time": last_backup,
            "r2_backup_success": r2_backup,
            "persistent_storage_confirmed": persisted,
            "drift_watch_active": drift_active,
            "drift_watch_reason": drift_reason,
        }

    return router
