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
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Cache the probe result for 60s — `dbStats` is cheap but no need to hit
# Atlas on every page load if 50 crew members open the app simultaneously.
_CACHE: Dict[str, Any] = {"ts": 0.0, "payload": None}
_CACHE_TTL_S = 60


def _quota_mb() -> int:
    try:
        v = int(os.environ.get("ATLAS_QUOTA_MB", "512"))
    except ValueError:
        v = 512
    return v


def build_cluster_capacity_router(get_client: callable) -> APIRouter:
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
        _CACHE["ts"] = now
        _CACHE["payload"] = payload
        return payload

    return router
