"""
Cluster capacity probe — iter437 (2026-05-26).

Exposes `/api/cluster/capacity` (PUBLIC — no auth) so every authenticated and
unauthenticated page can render an immediate operational banner when the
MongoDB Atlas cluster approaches its storage quota.

Why public:
  - The data exposed is non-sensitive (total cluster storage size + tier ceiling).
  - The banner must render on the login page, before any auth header exists,
    so field crews see the warning *before* they bother submitting a form
    that would silently fail.

Quota detection:
  - Reads `ATLAS_QUOTA_MB` from env. Defaults to 512 (M0 free tier).
  - When set to 0, the banner suppresses itself (interpreted as
    "unmanaged / unbounded tier", e.g. M10+).

Thresholds (matching ops doctrine):
  - >= 95% → severity=critical (red banner, blocks-imminent warning)
  - >= 80% → severity=warning  (amber banner, plan upgrade)
  - else   → severity=ok       (banner hidden)

Output (sub-50ms typical, since `dbStats` is a single RTT to Atlas):
  {
    "ok": true,
    "tier_quota_mb": 512,
    "storage_used_mb": 524.2,
    "storage_used_pct": 102.4,
    "severity": "critical",
    "dbs": {"masci_safety": 522.8, "masci_safety_preview": 1.4},
    "ts": "2026-05-26T22:00:00Z"
  }
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from motor.motor_asyncio import AsyncIOMotorClient

from lib.runtime_identity import runtime_identity_public_payload

logger = logging.getLogger(__name__)

# Cache the probe result for 60s — `dbStats` is cheap but no need to hit
# Atlas on every page load if 50 crew members open the app simultaneously.
_CACHE: Dict[str, Any] = {"ts": 0.0, "payload": None}
_CACHE_TTL_S = 60

# iter437 Phase Sigma-II — history collection name + TTL window (90 days).
HISTORY_COLLECTION = "cluster_capacity_history"
HISTORY_TTL_SECONDS = 90 * 86400


async def ensure_history_indexes(db) -> None:
    """One-time TTL on `ts` so the history collection self-prunes.
    Safe to call repeatedly — Mongo no-ops on duplicate index specs."""
    try:
        await db[HISTORY_COLLECTION].create_index(
            "ts", expireAfterSeconds=HISTORY_TTL_SECONDS,
            name="ts_ttl_90d",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("[cluster_capacity] history index ensure failed: %s", e)


def _quota_mb() -> int:
    try:
        v = int(os.environ.get("ATLAS_QUOTA_MB", "512"))
    except ValueError:
        v = 512
    return v


def build_cluster_capacity_router(get_client: callable, get_runtime_identity: callable | None = None) -> APIRouter:
    """`get_client` is a zero-arg callable that returns the live
    AsyncIOMotorClient. We accept it as a closure rather than importing
    server.py to avoid circular imports."""
    router = APIRouter(prefix="/api")

    @router.get("/cluster/capacity")
    async def cluster_capacity():
        now = time.monotonic()
        if _CACHE["payload"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_S:
            return _CACHE["payload"]

        quota_mb = _quota_mb()
        client: AsyncIOMotorClient = get_client()
        dbs: Dict[str, float] = {}
        total_storage_mb = 0.0

        # List candidate DB names (the two MASCI databases). We never
        # touch other Atlas projects.
        candidates = [
            os.environ.get("DB_NAME", "masci_safety"),
            "masci_safety",
            "masci_safety_preview",
        ]
        seen = set()
        for db_name in candidates:
            if not db_name or db_name in seen:
                continue
            seen.add(db_name)
            try:
                stats = await client[db_name].command("dbStats")
                storage_mb = (stats.get("storageSize", 0) or 0) / (1024 * 1024)
                index_mb = (stats.get("indexSize", 0) or 0) / (1024 * 1024)
                # Storage + indexes both count toward Atlas quota
                dbs[db_name] = round(storage_mb + index_mb, 2)
                total_storage_mb += dbs[db_name]
            except Exception as e:  # noqa: BLE001 — DB may not exist
                logger.debug(f"cluster_capacity: skip {db_name} ({e})")

        used_pct = (total_storage_mb / quota_mb * 100.0) if quota_mb > 0 else 0.0

        if quota_mb == 0:
            severity = "ok"
        elif used_pct >= 95.0:
            severity = "critical"
        elif used_pct >= 80.0:
            severity = "warning"
        else:
            severity = "ok"

        payload = {
            "ok": True,
            "tier_quota_mb": quota_mb,
            "storage_used_mb": round(total_storage_mb, 2),
            "storage_used_pct": round(used_pct, 1),
            "severity": severity,
            "dbs": dbs,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        if callable(get_runtime_identity):
            payload["runtime_identity"] = runtime_identity_public_payload(get_runtime_identity())
        _CACHE["ts"] = now
        _CACHE["payload"] = payload
        return payload

    # ------------------------------------------------------------------
    # iter437 · Phase Sigma-II · history endpoint
    # ------------------------------------------------------------------
    @router.get("/cluster/capacity/history")
    async def cluster_capacity_history(
        days: int = Query(default=7, ge=1, le=90, description="lookback window in days, max 90"),
    ):
        """Return hourly capacity snapshots for the last `days` days.

        Also computes a simple linear-fit slope (MB/day) over the
        retrieved window and projects days-to-quota at current rate.
        """
        client: AsyncIOMotorClient = get_client()
        # Read from whichever DB the backend currently writes to —
        # `cluster_capacity_history` lives in masci_safety_preview when
        # APP_ENV=preview, masci_safety when production. We never read
        # cross-environment for history (preview history is preview-only).
        db = client[os.environ.get("DB_NAME", "masci_safety")]
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        cursor = db[HISTORY_COLLECTION].find(
            {"ts": {"$gte": cutoff}},
            {"_id": 0},
        ).sort("ts", 1)
        rows: List[Dict[str, Any]] = []
        async for r in cursor:
            # Mongo decoded `ts` as a datetime — emit ISO string for JSON.
            if isinstance(r.get("ts"), datetime):
                r["ts"] = r["ts"].isoformat()
            rows.append(r)

        # Compute slope (MB/day) over the points we have.
        slope_mb_per_day: Optional[float] = None
        days_to_quota: Optional[float] = None
        first_mb: Optional[float] = None
        last_mb: Optional[float] = None
        if len(rows) >= 2:
            first = rows[0]
            last = rows[-1]
            try:
                first_mb = float(first["storage_used_mb"])
                last_mb = float(last["storage_used_mb"])
                t0 = datetime.fromisoformat(first["ts"].replace("Z", "+00:00")) \
                    if isinstance(first["ts"], str) else first["ts"]
                t1 = datetime.fromisoformat(last["ts"].replace("Z", "+00:00")) \
                    if isinstance(last["ts"], str) else last["ts"]
                dt_days = max((t1 - t0).total_seconds() / 86400.0, 1 / 24.0)
                slope_mb_per_day = round((last_mb - first_mb) / dt_days, 3)
                quota = _quota_mb()
                if slope_mb_per_day and slope_mb_per_day > 0 and quota > 0:
                    headroom = quota - last_mb
                    days_to_quota = round(headroom / slope_mb_per_day, 1)
            except Exception:  # noqa: BLE001
                pass

        return {
            "ok": True,
            "days": days,
            "samples": len(rows),
            "first_mb": first_mb,
            "last_mb": last_mb,
            "slope_mb_per_day": slope_mb_per_day,
            "days_to_quota": days_to_quota,
            "ts": datetime.now(timezone.utc).isoformat(),
            "rows": rows,
        }

    return router


# ----------------------------------------------------------------------
# iter437 · Phase Sigma-II · hourly snapshot recorder.
# Called from server.py scheduler. Idempotent and best-effort — failures
# are logged but never propagate.
# ----------------------------------------------------------------------
async def record_capacity_snapshot(client) -> Optional[Dict[str, Any]]:
    """Insert a single capacity snapshot into `cluster_capacity_history`."""
    try:
        quota_mb = _quota_mb()
        candidates = [
            os.environ.get("DB_NAME", "masci_safety"),
            "masci_safety",
            "masci_safety_preview",
        ]
        seen = set()
        dbs: Dict[str, float] = {}
        total_mb = 0.0
        for db_name in candidates:
            if not db_name or db_name in seen:
                continue
            seen.add(db_name)
            try:
                stats = await client[db_name].command("dbStats")
                storage_mb = (stats.get("storageSize", 0) or 0) / (1024 * 1024)
                index_mb = (stats.get("indexSize", 0) or 0) / (1024 * 1024)
                dbs[db_name] = round(storage_mb + index_mb, 2)
                total_mb += dbs[db_name]
            except Exception:  # noqa: BLE001
                pass

        used_pct = (total_mb / quota_mb * 100.0) if quota_mb > 0 else 0.0
        record = {
            "ts": datetime.now(timezone.utc),
            "tier_quota_mb": quota_mb,
            "storage_used_mb": round(total_mb, 2),
            "storage_used_pct": round(used_pct, 1),
            "dbs": dbs,
        }
        # Write to the DB the backend is currently using (preview or prod).
        target_db = client[os.environ.get("DB_NAME", "masci_safety")]
        await ensure_history_indexes(target_db)
        await target_db[HISTORY_COLLECTION].insert_one(record)
        # Strip _id for return
        record.pop("_id", None)
        return record
    except Exception as e:  # noqa: BLE001
        logger.warning("[cluster_capacity] snapshot record failed: %s", e)
        return None
