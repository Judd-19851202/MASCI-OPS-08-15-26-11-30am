"""
dispatch_reminders.py · Phase D-1.4 · Unacknowledged-assignment reminders.

Doctrine
--------
- Reuses the existing scheduler pattern (asyncio background task,
  SCHEDULER_ENABLED env gate, identical-shape to ``_backup_scheduler_loop``).
- Reuses the existing bell rail (``db.tasks``) — no new notification engine.
- One bell entry per assignment, max. Idempotency via ``reminder_sent_at``
  so a reminder never duplicates on repeated scans.
- Threshold and tick interval are env-tunable; sensible defaults match
  the OMEGA directive (10 minutes unacked, 60 second scan cadence).

The reminder fires exactly when an assignment has been ASSIGNED but
not acknowledged for ``DISPATCH_REMINDER_THRESHOLD_MIN`` (default 10).
Subsequent scans skip it because ``reminder_sent_at`` is now non-null.

A second escalation tier is intentionally OUT OF SCOPE for D-1.4 —
the directive specifies one reminder, no spam.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger("dispatch_reminders")

# ── Tunables (env-overridable) ─────────────────────────────────────
DEFAULT_THRESHOLD_MIN = 10        # OMEGA directive default
DEFAULT_TICK_SECONDS = 60         # one scan/minute
DEFAULT_BATCH_LIMIT = 200         # safety cap per tick


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _threshold_min() -> int:
    try:
        return max(1, int(os.environ.get("DISPATCH_REMINDER_THRESHOLD_MIN") or DEFAULT_THRESHOLD_MIN))
    except Exception:
        return DEFAULT_THRESHOLD_MIN


def _tick_seconds() -> int:
    try:
        return max(10, int(os.environ.get("DISPATCH_REMINDER_TICK_SECONDS") or DEFAULT_TICK_SECONDS))
    except Exception:
        return DEFAULT_TICK_SECONDS


def _scheduler_enabled() -> bool:
    raw = (os.environ.get("SCHEDULER_ENABLED") or "").strip().lower()
    return raw in ("1", "true", "yes", "on")


async def scan_unacked_assignments(
    db,
    *,
    threshold_min: Optional[int] = None,
    now: Optional[datetime] = None,
    batch_limit: int = DEFAULT_BATCH_LIMIT,
) -> Dict[str, Any]:
    """Find ASSIGNED-not-acked assignments older than the threshold and
    fire ONE bell reminder for each. Returns a summary suitable for
    test assertions and operational logging.

    Idempotency: an assignment with ``reminder_sent_at`` already set
    is skipped. The scan therefore self-throttles even if it runs
    every second (within the same window).

    The function never raises — all per-row errors are logged and
    counted.
    """
    threshold = threshold_min or _threshold_min()
    moment = now or _now()
    cutoff = moment - timedelta(minutes=threshold)
    cutoff_iso = cutoff.isoformat()

    query = {
        "current_state": "ASSIGNED",
        "acked_at": None,
        "cancelled_at": None,
        "assigned_at": {"$lt": cutoff_iso},
        "$or": [
            {"reminder_sent_at": None},
            {"reminder_sent_at": {"$exists": False}},
        ],
    }
    cursor = db.dispatch_assignments.find(query, {"_id": 0}).limit(batch_limit)
    found = 0
    fired = 0
    errors = 0
    fired_ids = []
    async for assignment in cursor:
        found += 1
        try:
            await _fire_reminder(db, assignment, fired_at=moment)
            fired += 1
            fired_ids.append(assignment.get("id"))
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning(f"[dispatch-reminder] failed for {assignment.get('id')}: {e}")

    return {
        "ok": True,
        "scanned_at": moment.isoformat(),
        "threshold_min": threshold,
        "found": found,
        "fired": fired,
        "errors": errors,
        "fired_assignment_ids": fired_ids,
    }


async def _fire_reminder(db, assignment: Dict[str, Any], *, fired_at: datetime) -> None:
    """Idempotent — only flips ``reminder_sent_at`` from null to a
    timestamp, then writes ONE bell task assigned to ``dispatch``.

    The match condition includes ``reminder_sent_at: None`` so a
    concurrent scan (or one that crossed the threshold during the same
    tick) cannot double-fire.
    """
    tenant_id = assignment.get("tenant_id") or "masci"
    fired_iso = fired_at.isoformat()
    res = await db.dispatch_assignments.update_one(
        {
            "id": assignment["id"],
            "$or": [
                {"reminder_sent_at": None},
                {"reminder_sent_at": {"$exists": False}},
            ],
        },
        {
            "$set": {
                "reminder_sent_at": fired_iso,
                "updated_at": fired_iso,
            },
            "$inc": {"reminder_count": 1},
        },
    )
    if res.modified_count == 0:
        # Lost the race — another scan claimed it first.
        return

    title = (
        f"Unacknowledged assignment · {assignment.get('truck_id') or '—'}"
        f" · {assignment.get('driver_name') or 'unassigned'}"
    )
    descr_bits = []
    if assignment.get("project_number"):
        descr_bits.append(f"#{assignment.get('project_number')}")
    descr_bits.append(f"assigned {assignment.get('assigned_at')}")
    descr_bits.append("driver has not acknowledged · please follow up")
    task_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "kind": "dispatch_reminder_unacked",
        "title": title[:200],
        "description": " · ".join(descr_bits)[:400],
        "assignee_role": "dispatch",
        "assignee_id": None,
        "assignment_id": assignment["id"],
        "truck_id": assignment.get("truck_id"),
        "driver_id": assignment.get("driver_id"),
        "status": "open",
        "created_at": fired_iso,
        "updated_at": fired_iso,
        "source": "dispatch_reminders_v1",
    }
    try:
        await db.tasks.insert_one(task_doc)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[dispatch-reminder] bell write failed: {e}")
    # Always also append a structured entry on the assignment's
    # delivery_log so the operational record is the single source of truth.
    try:
        await db.dispatch_assignments.update_one(
            {"id": assignment["id"]},
            {"$push": {"delivery_log": {
                "channel": "bell",
                "target": "dispatch",
                "at": fired_iso,
                "ok": True,
                "kind": "reminder",
                "error": None,
            }}},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[dispatch-reminder] delivery_log append failed: {e}")


async def reminder_scheduler_loop(db) -> None:
    """Long-running background task. Wakes every ``_tick_seconds()`` and
    calls :func:`scan_unacked_assignments`. Mirrors the existing
    ``_backup_scheduler_loop`` pattern (singleton-safe, gated by
    ``SCHEDULER_ENABLED``).

    The loop is intentionally simple. The directive is "do not create a
    new scheduler" — so this is a single asyncio task that lives next
    to the existing backup loop. No APScheduler, no cron, no Celery.
    """
    if not _scheduler_enabled():
        logger.info("[dispatch-reminders] SCHEDULER_ENABLED is off — loop is a no-op.")
        return
    logger.info(
        f"[dispatch-reminders] starting · threshold={_threshold_min()}min "
        f"tick={_tick_seconds()}s"
    )
    while True:
        try:
            summary = await scan_unacked_assignments(db)
            if summary["fired"]:
                logger.info(
                    f"[dispatch-reminders] tick fired={summary['fired']} "
                    f"found={summary['found']} errors={summary['errors']}"
                )
        except asyncio.CancelledError:
            logger.info("[dispatch-reminders] cancelled — exiting cleanly.")
            raise
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[dispatch-reminders] tick exception: {e}")
        await asyncio.sleep(_tick_seconds())


__all__ = [
    "scan_unacked_assignments",
    "reminder_scheduler_loop",
    "DEFAULT_THRESHOLD_MIN",
    "DEFAULT_TICK_SECONDS",
]
