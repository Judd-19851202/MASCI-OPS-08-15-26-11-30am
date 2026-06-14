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


async def apply_routing(
    db,
    notification: Dict[str, Any],
    *,
    project_number: Optional[str],
    event_key: str,
) -> Dict[str, Any]:
    """Mutate ``notification`` in place to populate ``recipient_user_id``
    from the active project roster for the given ``event_key`` (a key
    of ROLE_CHAIN). Returns the same dict so producers can chain.

    Behaviour is gated by ``OWNERSHIP_LOCK_ENABLED``:
      * Flag OFF / no project / no chain → no-op (notification unchanged).
      * Flag ON → walks the role chain; on first active rostered match,
        sets ``recipient_user_id`` AND ``linked_project_number`` (if not
        already set). The existing ``recipient_role`` is preserved as the
        scope/fallback guard — never removed, never broadened.

    Never raises. The originating producer must always succeed even if
    routing resolution fails — Phase-2B routing is best-effort.
    """
    chain = ROLE_CHAIN.get(event_key) or []
    fallback = notification.get("recipient_role")
    routing = await resolve_routing(
        db, project_number=project_number,
        role_chain=chain, fallback_role=fallback,
    )
    uid = routing.get("recipient_user_id")
    if uid:
        notification["recipient_user_id"] = uid
    # Stamp linked_project_number defensively so consumers can scope the
    # bell to the project even if they do not re-derive it.
    if project_number and not notification.get("linked_project_number"):
        notification["linked_project_number"] = project_number
    return notification


# Producer-event role chains (single source of truth — bug-fix here
# propagates platform-wide).
ROLE_CHAIN: Dict[str, List[str]] = {
    "daily_report.submitted":   ["superintendent", "co_pm", "pm"],
    "daily_report.needs_revision": ["foreman", "superintendent", "pm"],
    "incident.created":         ["safety_lead", "superintendent", "pm"],
    "incident.pm_visibility":   ["pm", "co_pm", "superintendent"],
    "inspection.deficiency":    ["safety_lead", "superintendent", "foreman"],
    "inspection.pm_visibility": ["pm", "co_pm", "superintendent"],
    "trench.hold_opened":       ["safety_lead", "superintendent", "foreman", "pm"],
    "trench.reinspection":      ["safety_lead", "superintendent", "foreman"],
    "qaqc.deficiency":          ["project_engineer", "pm", "co_pm", "superintendent"],
    "qaqc.safety_visibility":   ["safety_lead", "superintendent"],
    "safety_meeting.submitted": ["safety_lead", "superintendent", "pm"],
    "jha.submitted":            ["safety_lead", "superintendent", "foreman"],
    "preop.failed":             ["shop_contact", "superintendent", "pm"],
    "preop.dispatch_visibility": ["dispatcher_contact", "superintendent"],
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
    "apply_routing",
    "ROLE_CHAIN",
]
