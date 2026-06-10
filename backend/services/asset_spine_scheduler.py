"""
services/asset_spine_scheduler.py · FORGEDOPS P0.2 · Nightly reconciliation.

A single asyncio task wrapped in the existing `run_with_singleton_lock`
pattern. Runs `AssetSpine.scan_health` once per UTC day at the configured
hour (default 02:00 UTC). Persists every run to `asset_spine_health_runs`
exactly as the manual `POST /health/scan` endpoint does — same shape,
same audit, same indexing.

Why singleton-locked: multiple workers must not double-scan.
Why a separate file: keeps `server.py` boot block readable.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from services.asset_spine import AssetSpine

logger = logging.getLogger(__name__)

ASSET_SPINE_SCAN_HOUR_UTC = int(os.environ.get("ASSET_SPINE_SCAN_HOUR_UTC", "2"))
ASSET_SPINE_SCAN_ENABLED = os.environ.get("ASSET_SPINE_SCAN_ENABLED", "true").lower() == "true"


async def asset_spine_nightly_loop(db) -> None:
    """
    Sleep until next scan-hour UTC, then run scan_health. Wraps each scan
    in its own try/except so transient errors never kill the loop.
    """
    if not ASSET_SPINE_SCAN_ENABLED:
        logger.info("[asset-spine-scheduler] disabled via env (ASSET_SPINE_SCAN_ENABLED)")
        return
    logger.info(
        "[asset-spine-scheduler] started · target=%02d:00 UTC · daily",
        ASSET_SPINE_SCAN_HOUR_UTC,
    )
    while True:
        try:
            from datetime import timedelta as _td
            now = datetime.now(timezone.utc)
            target = now.replace(hour=ASSET_SPINE_SCAN_HOUR_UTC, minute=0, second=0, microsecond=0)
            if target <= now:
                target = target + _td(days=1)
            sleep_s = max((target - now).total_seconds(), 30.0)
            logger.info("[asset-spine-scheduler] sleeping %.0fs until %s", sleep_s, target.isoformat())
            await asyncio.sleep(sleep_s)
            try:
                spine = AssetSpine(db)
                run = await spine.scan_health(actor="scheduler")
                logger.info(
                    "[asset-spine-scheduler] scan complete · id=%s · findings=%s",
                    run.get("id"), run.get("findings_summary"),
                )
            except Exception as e:
                logger.exception("[asset-spine-scheduler] scan failed: %s", e)
        except asyncio.CancelledError:
            logger.info("[asset-spine-scheduler] cancelled")
            raise
        except Exception as e:
            logger.exception("[asset-spine-scheduler] loop iteration failed: %s", e)
            await asyncio.sleep(60)
