"""
test_safety_context_cert.py — TRACK 14.0-SAFETY-PORTAL-CONTEXT-INCIDENT-CLOSURE-FIX.

Locks the portal-context contract:
  * Safety-role notifications targeting incidents resolve to
    /safety-portal/incidents/{id} (not /admin/incidents/{id}).
  * Safety-role notifications targeting safety meetings resolve to
    /safety-portal/meetings/{id} (not /meetings/{id}).
  * Non-safety roles still get the legacy admin/portal routes
    (no security regression for Admin/PM).
"""
from __future__ import annotations

import sys

sys.path.insert(0, "/app/backend")

from routes.tasks_notifications import _resolve_link_url  # noqa: E402


def _payload(**over):
    base = {
        "linked_source_record_id": "abc-123",
        "linked_source_module": "safety.incidents",
        "type": "incident.opened",
    }
    base.update(over)
    return base


def test_safety_role_incident_routes_to_safety_portal():
    url = _resolve_link_url(_payload(recipient_role="safety"))
    assert url == "/safety-portal/incidents/abc-123", url


def test_admin_role_incident_still_routes_to_admin():
    url = _resolve_link_url(_payload(recipient_role="admin"))
    assert url == "/admin/incidents/abc-123", url


def test_pm_role_incident_routes_to_admin_legacy():
    """PM users see admin chrome for incidents currently (existing
    behavior — not part of this track). Confirm we did NOT widen the
    rewrite to PM."""
    url = _resolve_link_url(_payload(recipient_role="pm"))
    assert url == "/admin/incidents/abc-123", url


def test_safety_role_meeting_routes_to_safety_portal():
    url = _resolve_link_url(_payload(
        linked_source_module="safety.meeting",
        type="meeting.submitted",
        recipient_role="safety",
    ))
    assert url == "/safety-portal/meetings/abc-123", url


def test_admin_role_meeting_keeps_legacy_route():
    url = _resolve_link_url(_payload(
        linked_source_module="safety.meeting",
        type="meeting.submitted",
        recipient_role="admin",
    ))
    assert url == "/meetings/abc-123", url


def test_safety_role_incident_type_prefix_also_rewrites():
    """When the source_module isn't set but the type prefix matches
    incident.*, the rewrite must still apply for safety recipients."""
    url = _resolve_link_url(_payload(
        linked_source_module="",
        type="incident.opened",
        recipient_role="safety",
    ))
    assert url == "/safety-portal/incidents/abc-123", url


def test_safety_role_non_admin_template_unchanged():
    """Templates that already use safety routes pass through unchanged."""
    url = _resolve_link_url(_payload(
        linked_source_module="safety.inspections",
        type="safety.inspection.opened",
        recipient_role="safety",
    ))
    assert url == "/safety-portal", url
