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

from lib.database_authority import database_authority_public_payload
from lib.runtime_identity import runtime_identity_public_payload


def _is_atlas_runtime_identity(identity: Dict[str, Any]) -> bool:
    if not isinstance(identity, dict):
        return False
    if identity.get("is_atlas") is True:
        return True
    scheme = str(identity.get("mongo_scheme") or "").strip().lower()
    if scheme == "mongodb+srv":
        return True
    mongo_url = str(identity.get("mongo_url_redacted") or "").strip().lower()
    return mongo_url.startswith("mongodb+srv://") or ".mongodb.net" in mongo_url


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
    # iter440 · Phase 31.2 health-lock · the scheduler writes every run
    # into `backup_health` (NOT `backup_runs`). Field schema:
    # {ts, ok, mode, filename, size_bytes, records, emailed_to, error}.
    # IMPORTANT: filter to rows that actually produced a backup file
    # (filename != null) — `backup_health` ALSO records mode='r2-usage-alert'
    # rows that have no filename and are NOT backups (just storage probes).
    try:
        coll = db.backup_health
        doc = await coll.find_one(
            {"ok": True, "filename": {"$nin": [None, ""]}},
            sort=[("ts", -1)],
            projection={"_id": 0, "ts": 1, "filename": 1, "size_bytes": 1},
        )
        if doc:
            return doc.get("ts")
    except Exception:
        pass
    return None


async def _r2_backup_success(db) -> Dict[str, Any]:
    """Most recent ACTUAL backup row (i.e., a run that produced a zip)
    · whether the resulting zip was sent to R2 (or local persistence)
    without error. The scheduler writes a backup_health row with
    `ok=true` per successful run.

    iter440 · Phase 31.2 health-lock · the field `kind` in the diag
    output is sourced from the real `mode` field on `backup_health`
    rows, and we filter out non-backup quota-probe rows
    (mode='r2-usage-alert' · filename=None)."""
    try:
        row = await db.backup_health.find_one(
            {"filename": {"$nin": [None, ""]}},
            sort=[("ts", -1)],
            projection={
                "_id": 0,
                "ts": 1, "ok": 1, "mode": 1, "filename": 1,
                "size_bytes": 1, "records": 1, "error": 1,
            },
        )
        if not row:
            return {"present": False, "reason": "no backup_health row with filename found"}
        return {
            "present": True,
            "ts": row.get("ts"),
            "ok": bool(row.get("ok")),
            "kind": row.get("mode"),
            "filename": row.get("filename"),
            "size_bytes": row.get("size_bytes"),
            "records": row.get("records"),
            "error": row.get("error"),
        }
    except Exception as e:  # noqa: BLE001
        return {"present": False, "reason": f"backup_health read failed: {e}"}


async def _persistent_storage_confirmed(db) -> Dict[str, Any]:
    """Confirm we can read AND that there is at least one recent write
    (defaults to last 24h)."""
    try:
        names = await db.list_collection_names()
        # Prefer a fast write-recency check on continuity_events ·
        # otherwise fall back to backup_health (iter440 collection-name
        # correctness fix).
        watch_collection = "continuity_events" if "continuity_events" in names else (
            "backup_health" if "backup_health" in names else None
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
    app,
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
        bundle = getattr(app.state, "runtime_identity_bundle", None)
        runtime_identity = runtime_identity_public_payload(bundle) if bundle else {}
        identity = (runtime_identity or {}).get("identity") or {}
        mongo_url = identity.get("mongo_url_redacted") or ""
        db_name = identity.get("db_name") or ""
        atlas_connected = _is_atlas_runtime_identity(identity)

        mongo_version = await _safe_mongo_version(db)
        collections = await _list_collections(db)
        last_backup = await _last_backup_time(db)
        r2_backup = await _r2_backup_success(db)
        persisted = await _persistent_storage_confirmed(db)

        # drift_watch_active: the complete-archive scheduler appends a
        # snapshot into `backup_drift_history` on every run (iter440
        # collection-name correctness fix). Schema:
        # {id, recorded_at (datetime), captured_collections,
        #  total_records, explicit_exclusions}. We treat presence of a
        # snapshot in the last 36h as ACTIVE.
        drift_active = False
        drift_reason = "drift watcher heartbeat not seen"
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=36)
            heart = await db.backup_drift_history.find_one(
                {"recorded_at": {"$gte": cutoff}},
                projection={"_id": 0, "recorded_at": 1, "captured_collections": 1},
                sort=[("recorded_at", -1)],
            )
            if heart:
                drift_active = True
                drift_reason = "snapshot recorded within 36h"
        except Exception as e:  # noqa: BLE001
            drift_reason = f"drift collection probe failed: {e}"

        return {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "atlas_connected": atlas_connected,
            "atlas_detection_basis": {
                "runtime_identity_is_atlas": bool(identity.get("is_atlas")),
                "mongo_scheme": identity.get("mongo_scheme"),
                "mongo_hostname": identity.get("mongo_hostname_redacted"),
            },
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
            "database_authority": database_authority_public_payload(
                getattr(app.state, "database_authority_plan", None),
                lifecycle_state="ready" if getattr(app.state, "mongo_client", None) is not None else "not_initialized",
                connection_state="connected" if getattr(app.state, "db", None) is not None else "disconnected",
                last_successful_ping=getattr(app.state, "database_authority_last_ping", None),
                last_error_category=getattr(app.state, "database_authority_last_error", None),
            ),
        }

    return router
