"""
lib/event_fanout.py — Iter153E (Phase E completeness).

Tiny convenience wrappers around `task_service.create` +
`notification_service.fanout` so source modules don't repeat the same
try/except/fire-and-forget pattern. EVERY operational module (incidents,
inspections, pre-ops, fire-ext, etc.) routes through these helpers so
we keep a single audit point and avoid duplicate task/notification
logic creeping back into the codebase.

Design rules:
  * NEVER raise. The originating write must always succeed even if
    the task/notification fan-out fails — fan-out is best-effort
    operational signal, not a transactional dependency.
  * Always log a warning on failure so issues are observable in supervisor logs.
  * Pass-through to the existing shared services — no separate state
    or queue. If/when we add a job queue, this is the single entry
    point we'd swap.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


async def emit_task_and_notification(
    db,
    *,
    task: Dict[str, Any],
    notification: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Emit one task and (optionally) one notification, both fire-and-forget.

    Returns (task_id, notification_id) — either may be None if the call
    failed. The task itself ALWAYS produces a `task.assigned`
    notification to the assignee_role inside `task_service.create`, so
    the explicit `notification` arg is for a SEPARATE topical
    notification (e.g., "incident.created", "preop.failed", etc.).
    """
    # Lazy import — avoids circular dep with tasks_notifications.py.
    from routes.tasks_notifications import task_service, notification_service  # noqa: PLC0415

    task_id: Optional[str] = None
    notif_id: Optional[str] = None
    try:
        task_id = await task_service.create(db, task)
    except Exception as e:  # noqa: BLE001
        logger.warning("[event_fanout] task create failed (%s): %s",
                       task.get("source_module"), e)
    if notification:
        try:
            notif_id = await notification_service.fanout(db, notification)
        except Exception as e:  # noqa: BLE001
            logger.warning("[event_fanout] notification fanout failed (%s): %s",
                           notification.get("type"), e)
    return task_id, notif_id


async def emit_notification(db, payload: Dict[str, Any]) -> Optional[str]:
    """Fire-and-forget notification (no task). Returns notification id or None."""
    from routes.tasks_notifications import notification_service  # noqa: PLC0415
    try:
        return await notification_service.fanout(db, payload)
    except Exception as e:  # noqa: BLE001
        logger.warning("[event_fanout] notification fanout failed (%s): %s",
                       payload.get("type"), e)
        return None


__all__ = ["emit_task_and_notification", "emit_notification"]
