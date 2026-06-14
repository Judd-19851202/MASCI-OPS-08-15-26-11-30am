"""
lib/team_routing.py — Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 2B.

Thin shim that producers call in ONE line to (a) embed a frozen
`team_snapshot` on the operational record at submit-time and (b)
resolve the active rostered recipient for a notification event.

Gated by env var ``OWNERSHIP_LOCK_ENABLED``. When the flag is absent
or "false", `resolve_routing` is a no-op (returns `recipient_user_id=None`)
and producers continue to route by role bucket only — exactly the
pre-Phase-2B behaviour. When the flag flips to "true", producers
that opt in begin populating `recipient_user_id` from the roster.

Snapshot capture is ALWAYS on (even when flag is off). Snapshots are
historical truth; they never change behaviour by themselves, so it is
safe to start collecting them immediately.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def ownership_lock_enabled() -> bool:
    return (os.environ.get("OWNERSHIP_LOCK_ENABLED", "false") or "").lower() == "true"


async def snapshot_team(db, project_number: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return a frozen snapshot of the active roster on `project_number`.
    Safe to call with `None` or with a non-existent project — returns
    None in both cases so writers can branch cleanly.

    Producers should call this once at submit/create time and embed the
    result on the record's `team_snapshot` field. Never call it on
    update / edit paths."""
    if not project_number:
        return None
    try:
        from routes.ownership_lifecycle import capture_team_snapshot
        return await capture_team_snapshot(db, project_number)
    except Exception as exc:  # pragma: no cover
        logger.warning("[team-routing] snapshot capture failed: %s", exc)
        return None


async def resolve_routing(
    db,
    *,
    project_number: Optional[str],
    role_chain: List[str],
    fallback_role: Optional[str] = None,
) -> Dict[str, Any]:
    """Return ``{recipient_user_id, resolved_via, resolved_email}``.
    When OWNERSHIP_LOCK_ENABLED is off, returns all-None so producers
    fall back to their existing role-bucket behaviour. When on, walks
    the role priority chain over active rostered users and returns the
    first match.

    Returned dict is shaped to be sliced directly into a
    notification.fanout() payload alongside ``recipient_role=fallback``::

        routing = await resolve_routing(db, project_number=pn,
                                        role_chain=["super","co_pm","pm"],
                                        fallback_role="fl")
        notif["recipient_user_id"] = routing["recipient_user_id"]
        notif["recipient_role"]    = fallback_role  # ALWAYS keep the scope guard
    """
    if not ownership_lock_enabled() or not project_number or not role_chain:
        return {"recipient_user_id": None,
                "resolved_via": None,
                "resolved_email": None}
    try:
        from routes.ownership_lifecycle import resolve_recipient_for_event
        r = await resolve_recipient_for_event(
            db, project_number=project_number,
            role_chain=role_chain,
            fallback_role=fallback_role,
        )
        return {
            "recipient_user_id": r.get("recipient_user_id"),
            "resolved_via": r.get("resolved_via"),
            "resolved_email": r.get("resolved_email"),
        }
    except Exception as exc:  # pragma: no cover
        logger.warning("[team-routing] resolver failed: %s", exc)
        return {"recipient_user_id": None,
                "resolved_via": None,
                "resolved_email": None}


# Producer-event role chains (single source of truth — bug-fix here
# propagates platform-wide).
ROLE_CHAIN: Dict[str, List[str]] = {
    "daily_report.submitted":   ["superintendent", "co_pm", "pm"],
    "daily_report.needs_revision": ["foreman", "superintendent", "pm"],
    "incident.created":         ["safety_lead", "superintendent", "pm"],
    "trench.hold_opened":       ["safety_lead", "superintendent", "foreman", "pm"],
    "trench.reinspection":      ["safety_lead", "superintendent", "foreman"],
    "qaqc.deficiency":          ["project_engineer", "pm", "co_pm", "superintendent"],
    "safety_meeting.submitted": ["safety_lead", "superintendent", "pm"],
    "preop.failed":             ["shop_contact", "superintendent", "pm"],
    "dvir.failed":              ["shop_contact", "dispatcher_contact", "superintendent"],
    "asset_doc.expired":        ["asset_admin", "locate_coordinator", "pm"],
    "asset_doc.expires":        ["asset_admin", "locate_coordinator", "pm"],
    "locate_ticket.opened":     ["locate_coordinator", "asset_admin", "pm"],
    "locate_ticket.expiring":   ["locate_coordinator", "asset_admin", "pm"],
    "dispatch.stale_location":  ["dispatcher_contact", "superintendent", "pm"],
    "fl.submitted":             ["superintendent", "safety_lead", "pm"],
}


__all__ = [
    "ownership_lock_enabled",
    "snapshot_team",
    "resolve_routing",
    "ROLE_CHAIN",
]
