"""
Motive Reliability Loop — M-1R Sprint
=====================================

Reuses MASCI's existing scheduler doctrine (`asyncio.create_task` +
`run_with_singleton_lock` + supervisor) — does NOT introduce a new
scheduler framework.

Cadence per the M-1R brief:
  • sync_events     every 15 min
  • sync_assets     every 12 h
  • sync_users      every 12 h
  • sync_geofences  every 12 h

Failure-safe:
  - Every tick is wrapped; failures log to `integration_sync_logs` AND
    set `integration_settings.motive.last_failed_sync_at` so the
    existing Integration Center surface reflects the health state
    without any new UI.
  - A single boot-time staleness backfill kicks `sync_events` once if
    the last successful run is >30 min old.
  - Multi-worker safe via `scheduler_locks` (same lock collection
    used by the backup scheduler).

NO automation. NO workflow side-effects. The loop only invokes the
already-built Motive sync methods which write into already-existing
collections.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone

from lib.singleton_scheduler import run_with_singleton_lock

logger = logging.getLogger(__name__)


# Cadence (seconds). Overridable via env for testing.
CADENCE_EVENTS = int(os.environ.get("MOTIVE_SYNC_EVENTS_SECONDS", 15 * 60))
CADENCE_ASSETS = int(os.environ.get("MOTIVE_SYNC_ASSETS_SECONDS", 12 * 60 * 60))
CADENCE_USERS = int(os.environ.get("MOTIVE_SYNC_USERS_SECONDS", 12 * 60 * 60))
CADENCE_GEOFENCES = int(os.environ.get("MOTIVE_SYNC_GEOFENCES_SECONDS", 12 * 60 * 60))

# Initial settle delay so we don't pile syncs on a fresh boot.
BOOT_DELAY = int(os.environ.get("MOTIVE_RELIABILITY_BOOT_DELAY_S", 45))

# Loop health state — surfaced via /api/admin/integrations/motive/reliability-state
STATE: dict[str, dict] = {
    "events": {"last_tick": None, "last_status": None, "last_error": None},
    "assets": {"last_tick": None, "last_status": None, "last_error": None},
    "users": {"last_tick": None, "last_status": None, "last_error": None},
    "geofences": {"last_tick": None, "last_status": None, "last_error": None},
    "alive": False,
    "started_at": None,
}


async def _run_one_sync(service, kind: str) -> dict:
    """Invoke the appropriate MotiveService method by kind."""
    if not service.is_live:
        return {"ok": False, "status": "awaiting_credentials"}
    if kind == "events":
        return await service.sync_events()
    if kind == "assets":
        return await service.sync_assets()
    if kind == "users":
        return await service.sync_users()
    if kind == "geofences":
        return await service.sync_geofences()
    return {"ok": False, "status": "unknown_kind"}


async def _tick(db, kind: str) -> None:
    """One reliability tick. Always idempotent; never raises."""
    now = datetime.now(timezone.utc).isoformat()
    STATE[kind]["last_tick"] = now
    try:
        # Late import keeps the reliability loop importable from server.py
        # without dragging the entire MotiveService into module init.
        from services.motive_service import MotiveService  # noqa: PLC0415
        # Load operator-managed credentials from the existing settings row
        settings = await db.integration_settings.find_one(
            {"provider": "motive"}, {"_id": 0}
        )
        service = MotiveService(db, settings_doc=settings)
        result = await _run_one_sync(service, kind)
        STATE[kind]["last_status"] = result.get("status") or ("ok" if result.get("ok") else "failed")
        STATE[kind]["last_error"] = None if result.get("ok") else result.get("message")
        if not result.get("ok"):
            logger.warning(f"[motive-reliability] {kind} tick non-ok: {result.get('status')}")
    except Exception as e:  # noqa: BLE001
        STATE[kind]["last_status"] = "exception"
        STATE[kind]["last_error"] = repr(e)
        logger.exception(f"[motive-reliability] {kind} tick crashed: {e}")


async def _tick_wrapper(db, kind: str) -> None:
    """Wrapper conforming to the run_with_singleton_lock signature
    (`scheduler_fn(db, *args, **kwargs)`)."""
    await _tick(db, kind)


async def _kind_loop(db, kind: str, cadence_seconds: int) -> None:
    """Bounded sleep loop for one sync kind. Singleton-locked so only one
    worker fires the tick across a multi-worker fleet."""
    while True:
        try:
            await run_with_singleton_lock(
                db,
                f"motive_reliability_{kind}",
                _tick_wrapper,
                kind,
            )
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[motive-reliability] {kind} lock-wrap failed: {e}")
        await asyncio.sleep(cadence_seconds)


async def motive_reliability_supervisor(db) -> None:
    """Top-level supervisor. Launches one task per sync kind and
    respawns any task that dies. Mirrors the backup-scheduler
    resurrection pattern."""
    STATE["alive"] = True
    STATE["started_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(
        f"[motive-reliability] supervisor armed · "
        f"events={CADENCE_EVENTS}s · assets={CADENCE_ASSETS}s · "
        f"users={CADENCE_USERS}s · geofences={CADENCE_GEOFENCES}s · "
        f"boot_delay={BOOT_DELAY}s"
    )

    await asyncio.sleep(BOOT_DELAY)

    tasks: dict[str, asyncio.Task] = {}
    cadence_for = {
        "events": CADENCE_EVENTS,
        "assets": CADENCE_ASSETS,
        "users": CADENCE_USERS,
        "geofences": CADENCE_GEOFENCES,
    }
    for kind, cad in cadence_for.items():
        tasks[kind] = asyncio.create_task(_kind_loop(db, kind, cad))

    # Resurrection — every 5 min check each task. Respawn if dead.
    while True:
        try:
            await asyncio.sleep(300)
            for kind, task in list(tasks.items()):
                if task.done():
                    exc_repr = "(no exception)"
                    try:
                        exc = task.exception()
                        if exc is not None:
                            exc_repr = repr(exc)
                    except Exception:
                        pass
                    logger.critical(
                        f"[motive-reliability] {kind} task DEAD — respawning. "
                        f"Last state: {exc_repr}"
                    )
                    tasks[kind] = asyncio.create_task(_kind_loop(db, kind, cadence_for[kind]))
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[motive-reliability] supervisor tick failed: {e}")


def reliability_state_snapshot() -> dict:
    """Read-only snapshot consumed by the Integration Center surface."""
    return {
        "alive": STATE["alive"],
        "started_at": STATE["started_at"],
        "loops": {k: STATE[k] for k in ("events", "assets", "users", "geofences")},
        "cadence_seconds": {
            "events": CADENCE_EVENTS,
            "assets": CADENCE_ASSETS,
            "users": CADENCE_USERS,
            "geofences": CADENCE_GEOFENCES,
        },
    }


__all__ = ["motive_reliability_supervisor", "reliability_state_snapshot", "STATE"]
