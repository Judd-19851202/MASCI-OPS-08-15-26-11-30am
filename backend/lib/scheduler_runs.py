"""scheduler_runs.py — iter445 · Sprint · Scheduler Hardening · Option C.

Universal execution audit + dedup layer for all schedulers.

What this provides
------------------
A single collection ``scheduler_runs`` that records every scheduled fire,
keyed by ``(scheduler_name, slot_key)``. The slot_key is the canonical
identifier of the scheduled time slot (e.g. ``"2026-06-01T14:00:00+00:00"``
for the Monday 14:00 UTC PO digest). A unique compound index on these
two fields makes duplicate execution at the same slot **physically
impossible**: the second worker's ``insert_one`` raises ``DuplicateKeyError``
and we know to skip the send.

Doctrine
--------
* Belt-and-suspenders alongside the singleton lock (which is the primary
  guard but has had a race · see PO_DIGEST_FORENSIC_REPORT.md).
* Even if the lock layer fails again in the future, the unique index here
  guarantees one digest per slot.
* Provides a queryable audit trail: "Why did this digest send? Which pod?
  When? How many recipients? Did the dedup trip?" — all answerable by
  ``db.scheduler_runs.find_one({"scheduler": "po_digest", "slot_key": …})``.

API
---
``claim_slot(db, scheduler, slot_key) -> claim_doc | None``

  Atomically claims the slot. Returns the claim document on success,
  or ``None`` if the slot was already claimed (dedup trip).

``mark_completed(db, scheduler, slot_key, *, recipients, status, error=None,
                  meta=None)``

  Updates the claim with completion status. Called by the scheduler at
  the end of its send.

``mark_failed(db, scheduler, slot_key, *, error)``

  Convenience for failure path.

``list_runs(db, scheduler=None, limit=50)``

  Read-only history for the admin audit UI.
"""
from __future__ import annotations

import logging
import os
import socket
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

SCHEDULER_RUNS_COLLECTION = "scheduler_runs"
DEFAULT_TTL_DAYS = 90  # auto-prune scheduler_runs older than this


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_scheduler_runs_indexes(db: Any) -> None:
    """Create indexes for ``scheduler_runs``. Idempotent.

    * Unique compound on (``scheduler``, ``slot_key``) — atomic dedup.
    * TTL on ``ttl_at`` — auto-prune at 90 days, capped.
    * Secondary on (``scheduler``, ``started_at``) — admin history queries.
    """
    coll = db[SCHEDULER_RUNS_COLLECTION]
    try:
        await coll.create_index(
            [("scheduler", 1), ("slot_key", 1)],
            unique=True,
            name="ix_scheduler_runs_slot_unique",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[scheduler-runs] unique-index create failed (non-fatal): {e}")
    try:
        await coll.create_index(
            "ttl_at", expireAfterSeconds=0, name="ix_scheduler_runs_ttl"
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[scheduler-runs] ttl-index create failed (non-fatal): {e}")
    try:
        await coll.create_index(
            [("scheduler", 1), ("started_at", -1)],
            name="ix_scheduler_runs_history",
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[scheduler-runs] history-index create failed (non-fatal): {e}")


async def claim_slot(
    db: Any,
    scheduler: str,
    slot_key: str,
    *,
    owner_id: Optional[str] = None,
) -> Optional[dict]:
    """Atomically claim a scheduled slot. Returns the claim doc on success,
    or ``None`` if the slot was already claimed (dedup trip).

    The slot_key must be stable for the slot (e.g. ISO timestamp of the
    canonical fire time). Any worker computing the same slot_key will
    deterministically race for the unique index.
    """
    now = _now()
    claim = {
        "scheduler": scheduler,
        "slot_key": slot_key,
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "owner_id": owner_id or f"{socket.gethostname()}:{os.getpid()}",
        "started_at": now,
        "status": "in_progress",
        "ttl_at": now + timedelta(days=DEFAULT_TTL_DAYS),
    }
    try:
        await db[SCHEDULER_RUNS_COLLECTION].insert_one(claim)
        logger.info(
            f"[scheduler-runs:{scheduler}] CLAIMED slot {slot_key} · owner={claim['owner_id']}"
        )
        # Pop the auto-inserted _id so we never leak it back to callers
        # (and so the dict matches our response models)
        claim.pop("_id", None)
        return claim
    except DuplicateKeyError:
        existing = await db[SCHEDULER_RUNS_COLLECTION].find_one(
            {"scheduler": scheduler, "slot_key": slot_key},
            {"_id": 0},
        )
        logger.warning(
            f"[scheduler-runs:{scheduler}] DEDUP TRIPPED · slot {slot_key} already "
            f"claimed by owner={(existing or {}).get('owner_id')!r} at "
            f"{(existing or {}).get('started_at')}"
        )
        # Audit the duplicate attempt so the operator can see how often
        # this trips even if no email goes out.
        try:
            await db[SCHEDULER_RUNS_COLLECTION].update_one(
                {"scheduler": scheduler, "slot_key": slot_key},
                {
                    "$inc": {"dedup_attempts": 1},
                    "$set": {"last_dedup_at": now},
                    "$push": {
                        "dedup_attempt_log": {
                            "ts": now,
                            "host": socket.gethostname(),
                            "pid": os.getpid(),
                            "owner_id": owner_id,
                        }
                    },
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[scheduler-runs:{scheduler}] dedup-audit update failed: {e}")
        return None


async def mark_completed(
    db: Any,
    scheduler: str,
    slot_key: str,
    *,
    recipients: int,
    status: str = "done",
    error: Optional[str] = None,
    meta: Optional[dict] = None,
) -> None:
    """Update the claim with completion data."""
    now = _now()
    update = {
        "$set": {
            "status": status,
            "finished_at": now,
            "recipients": int(recipients),
        }
    }
    if error:
        update["$set"]["error"] = str(error)[:1000]
    if meta:
        update["$set"]["meta"] = meta
    try:
        # Compute duration server-side using $expr is overkill; we read
        # back the claim and write duration explicitly so it's available
        # without aggregation.
        existing = await db[SCHEDULER_RUNS_COLLECTION].find_one(
            {"scheduler": scheduler, "slot_key": slot_key},
            {"_id": 0, "started_at": 1},
        )
        if existing and existing.get("started_at"):
            try:
                started = existing["started_at"]
                if isinstance(started, str):
                    started = datetime.fromisoformat(started.replace("Z", "+00:00"))
                # Mongo stores datetimes as tz-naive UTC by default.
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                update["$set"]["duration_s"] = (now - started).total_seconds()
            except Exception:
                pass
        await db[SCHEDULER_RUNS_COLLECTION].update_one(
            {"scheduler": scheduler, "slot_key": slot_key},
            update,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[scheduler-runs:{scheduler}] mark_completed failed: {e}")


async def mark_failed(
    db: Any,
    scheduler: str,
    slot_key: str,
    *,
    error: str,
) -> None:
    """Convenience: mark the claim failed."""
    await mark_completed(
        db, scheduler, slot_key,
        recipients=0,
        status="failed",
        error=error,
    )


async def list_runs(
    db: Any,
    *,
    scheduler: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Return recent scheduler runs, newest first. Used by admin audit UI."""
    q: dict = {}
    if scheduler:
        q["scheduler"] = scheduler
    cursor = (
        db[SCHEDULER_RUNS_COLLECTION]
        .find(q, {"_id": 0})
        .sort("started_at", -1)
        .limit(int(limit))
    )
    return [doc async for doc in cursor]


__all__ = [
    "SCHEDULER_RUNS_COLLECTION",
    "ensure_scheduler_runs_indexes",
    "claim_slot",
    "mark_completed",
    "mark_failed",
    "list_runs",
]
