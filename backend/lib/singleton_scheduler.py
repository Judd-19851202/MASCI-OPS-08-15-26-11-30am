"""singleton_scheduler.py — iter441 · Phase 31.4 · multi-worker scheduler safety.

Problem
-------
Every `@app.on_event("startup")` handler runs ONCE PER UVICORN WORKER. If
production ever boots with ``--workers 2`` (or higher), each one of our
~5 long-running scheduler tasks would fire twice — double R2 archives,
double Monday-morning operator digests, double PO digests, double safety
digests, double verification probes. That's a survivability defect waiting
to be triggered the day operations decide to scale.

Solution
--------
A small Mongo-based singleton lock. Each scheduler now boots through
``run_with_singleton_lock(db, lock_name, scheduler_fn)`` instead of being
fire-and-forget. The helper:

  1. Tries to insert/refresh a lock document in ``scheduler_locks``.
  2. If it wins the lock, starts the scheduler AND a 30s heartbeat task
     that refreshes the lock's ``expires_at`` field every 30 seconds.
  3. If another worker already holds the lock, sleeps 60s and re-tries —
     this is the automatic-failover path. If the holder dies, the lock's
     TTL (90s by default) expires and the next polling worker takes over.

The lock uses a fixed ``_id`` per scheduler name so MongoDB's natural
``_id`` uniqueness gives us the atomic-claim guarantee for free.

Doctrine
--------
* Zero impact when workers == 1 (the first try always succeeds).
* Zero impact on existing schedulers' code — they don't know they're gated.
* Failures during lock acquisition are calm-degraded: scheduler skips
  this tick and tries again next loop. No crash, no panic email.
* No new endpoints. No new UI. Operational hygiene only.
"""
from __future__ import annotations

import asyncio
import logging
import os
import socket
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Optional

from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

LOCK_COLLECTION = "scheduler_locks"
DEFAULT_TTL_SECONDS = 90  # lock auto-expires if not refreshed within this window
HEARTBEAT_INTERVAL_SECONDS = 30  # refresh cadence (well under TTL)
POLL_INTERVAL_SECONDS = 60  # how often a losing worker re-checks for failover


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _generate_owner_id() -> str:
    """Worker-process-unique identifier. Includes hostname + pid + uuid
    so we can tell workers apart across pods and restarts."""
    return f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"


async def ensure_lock_indexes(db: Any) -> None:
    """Create the TTL index on ``expires_at`` so dead locks are auto-cleaned
    even if no worker is alive to release them. Idempotent · safe to call
    every startup."""
    try:
        await db[LOCK_COLLECTION].create_index(
            "expires_at", expireAfterSeconds=0, name="ix_scheduler_locks_ttl"
        )
    except Exception as e:  # noqa: BLE001
        # If the index can't be created we still function — the lock TTL
        # check below uses explicit datetime comparison.
        logger.warning(f"[singleton-lock] ensure index failed (non-fatal): {e}")


async def _try_acquire_lock(db: Any, lock_name: str, owner_id: str) -> bool:
    """Atomic claim. Returns True only if we now hold the lock.

    Two paths:
      a) The lock document doesn't exist → ``insert_one`` succeeds.
      b) The lock document exists but expired → ``find_one_and_update``
         with ``expires_at < now`` succeeds and we steal it.
      c) The lock is held by someone else and fresh → both fail, return False.

    A holder can re-acquire its own lock (idempotent re-entry on restart).
    """
    now = _now_utc()
    expires = now + timedelta(seconds=DEFAULT_TTL_SECONDS)

    # Path (b) + (c): try to steal an expired lock OR refresh our own
    try:
        result = await db[LOCK_COLLECTION].find_one_and_update(
            {
                "_id": lock_name,
                "$or": [
                    {"expires_at": {"$lt": now}},
                    {"owner_id": owner_id},
                ],
            },
            {
                "$set": {
                    "owner_id": owner_id,
                    "acquired_at": now,
                    "expires_at": expires,
                }
            },
        )
        if result is not None:
            return True
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[singleton-lock:{lock_name}] update probe failed: {e}")

    # Path (a): no doc yet — try to insert
    try:
        await db[LOCK_COLLECTION].insert_one(
            {
                "_id": lock_name,
                "owner_id": owner_id,
                "acquired_at": now,
                "expires_at": expires,
            }
        )
        return True
    except DuplicateKeyError:
        # Some other worker inserted in the meantime — they own it.
        return False
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[singleton-lock:{lock_name}] insert probe failed: {e}")
        return False


async def _refresh_lock(db: Any, lock_name: str, owner_id: str) -> bool:
    """Extend our own lock by another TTL window. Returns True if the
    refresh landed (i.e., we still hold the lock)."""
    now = _now_utc()
    expires = now + timedelta(seconds=DEFAULT_TTL_SECONDS)
    try:
        result = await db[LOCK_COLLECTION].update_one(
            {"_id": lock_name, "owner_id": owner_id},
            {"$set": {"expires_at": expires}},
        )
        return result.modified_count > 0
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[singleton-lock:{lock_name}] heartbeat refresh failed: {e}")
        return False


async def _release_lock(db: Any, lock_name: str, owner_id: str) -> None:
    """Best-effort release on clean shutdown / scheduler crash. If the
    delete fails, the TTL index will clean up within 90s anyway."""
    try:
        await db[LOCK_COLLECTION].delete_one(
            {"_id": lock_name, "owner_id": owner_id}
        )
    except Exception:
        pass


async def _heartbeat_loop(db: Any, lock_name: str, owner_id: str) -> None:
    """Background task that refreshes the lock every HEARTBEAT_INTERVAL.
    Exits silently when the parent scheduler is cancelled."""
    while True:
        try:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
            ok = await _refresh_lock(db, lock_name, owner_id)
            if not ok:
                # We lost the lock (another worker stole it after our TTL expired
                # — likely because we were stuck doing slow work). Calm exit;
                # the scheduler's parent loop will rediscover on next iteration.
                logger.warning(
                    f"[singleton-lock:{lock_name}] lost lock during heartbeat — "
                    f"another worker has taken over"
                )
                return
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[singleton-lock:{lock_name}] heartbeat tick failed: {e}")


async def run_with_singleton_lock(
    db: Any,
    lock_name: str,
    scheduler_fn: Callable[..., Awaitable[Any]],
    *fn_args: Any,
    **fn_kwargs: Any,
) -> None:
    """Run ``scheduler_fn(db, *args, **kwargs)`` exactly once across all
    workers in the deployment. Acquires the lock, kicks off a heartbeat,
    then awaits the scheduler. On loss-of-lock or crash, falls back to
    re-polling so the cluster heals itself.

    Usage
    -----
        asyncio.create_task(
            run_with_singleton_lock(db, "backup_scheduler", _backup_scheduler_loop)
        )

    Replaces the previous direct ``asyncio.create_task(scheduler_fn(db))``.
    """
    owner_id = _generate_owner_id()
    logger.info(
        f"[singleton-lock:{lock_name}] starting under owner_id={owner_id}"
    )
    while True:
        try:
            acquired = await _try_acquire_lock(db, lock_name, owner_id)
            if not acquired:
                # Lost the race · another worker holds the lock · sleep and
                # re-check. If the holder dies, its TTL will expire and we'll
                # pick it up here.
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
                continue

            logger.info(
                f"[singleton-lock:{lock_name}] LOCK ACQUIRED · "
                f"scheduler is now active on this worker"
            )

            hb_task = asyncio.create_task(_heartbeat_loop(db, lock_name, owner_id))
            try:
                await scheduler_fn(db, *fn_args, **fn_kwargs)
                # Scheduler returned normally (rare for a `while True` loop) —
                # release and exit.
                logger.info(
                    f"[singleton-lock:{lock_name}] scheduler returned normally — releasing"
                )
                return
            except asyncio.CancelledError:
                logger.info(
                    f"[singleton-lock:{lock_name}] cancelled · releasing lock"
                )
                raise
            except Exception as e:  # noqa: BLE001
                logger.exception(
                    f"[singleton-lock:{lock_name}] scheduler crashed: {e!r}"
                )
                # Crash inside the scheduler · release the lock so a sibling
                # worker can pick it up, then back off before retrying.
                await asyncio.sleep(POLL_INTERVAL_SECONDS)
            finally:
                hb_task.cancel()
                try:
                    await hb_task
                except (asyncio.CancelledError, Exception):
                    pass
                await _release_lock(db, lock_name, owner_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.exception(
                f"[singleton-lock:{lock_name}] outer loop hiccup: {e!r}"
            )
            await asyncio.sleep(POLL_INTERVAL_SECONDS)


__all__ = [
    "run_with_singleton_lock",
    "ensure_lock_indexes",
    "LOCK_COLLECTION",
    "DEFAULT_TTL_SECONDS",
    "HEARTBEAT_INTERVAL_SECONDS",
]
