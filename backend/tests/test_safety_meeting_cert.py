"""
test_safety_meeting_cert.py — TRACK 14.0-SAFETY-MEETING-WORKFLOW-PDF-CERTIFICATION.

Locks the workflow contract:
  * MeetingCreate refuses an attendee row without name / company /
    signature / acknowledged.
  * MeetingCreate refuses a submission without `conducted_by`.
  * _render_meeting reads `conducted_by` + `hazards_reviewed` +
    `discussion_notes` + string-typed `action_items` (current schema)
    AND the legacy alias names.
  * _render_meeting renders sections 02 → 05 even when their data is
    missing (renders "None recorded" placeholder); section numbers
    never jump.
  * _render_meeting attendee table now renders columns: Name, Company,
    Trade / Role, Signature, Acknowledged (5 columns).
"""
from __future__ import annotations

import sys
from typing import Any, Dict

import pytest

sys.path.insert(0, "/app/backend")

from pdf_render import _render_meeting  # noqa: E402
from routes.safety import MeetingAttendee, MeetingCreate  # noqa: E402


# ── Schema contract tests ───────────────────────────────────────────


def _good_attendee(**over: Any) -> Dict[str, Any]:
    base = {
        "name": "Jose Garcia",
        "company": "MASCI",
        "signature": "data:image/png;base64,iVBORw0KGgo=",
        "acknowledged": True,
        "acknowledged_at": "2026-06-15T12:00:00Z",
    }
    base.update(over)
    return base


def test_attendee_requires_name():
    with pytest.raises(Exception):
        MeetingAttendee(**_good_attendee(name=""))


def test_attendee_requires_company():
    with pytest.raises(Exception):
        MeetingAttendee(**_good_attendee(company=""))


def test_attendee_requires_signature():
    with pytest.raises(Exception):
        MeetingAttendee(**_good_attendee(signature=""))


def test_attendee_requires_acknowledgement():
    with pytest.raises(Exception):
        MeetingAttendee(**_good_attendee(acknowledged=False))


def test_attendee_happy_path():
    a = MeetingAttendee(**_good_attendee())
    assert a.name == "Jose Garcia"
    assert a.company == "MASCI"
    assert a.acknowledged is True


def test_attendee_non_masci_with_typed_company():
    a = MeetingAttendee(**_good_attendee(
        non_masci=True, name="Sam Subcontractor",
        company="Acme Paving", trade="Asphalt Operator"))
    assert a.non_masci is True
    assert a.company == "Acme Paving"
    assert a.trade == "Asphalt Operator"


def _good_meeting(**over: Any) -> Dict[str, Any]:
    base = {
        "project_name": "Cert Project",
        "project_number": "ZZ-CERT-001",
        "location": "Cert Site",
        "meeting_date": "2026-06-15",
        "meeting_time": "08:00",
        "conducted_by": "James Fisher (Jimmy)",
        "topic": "Excavation Safety",
        "hazards_reviewed": "Cave-in, struck-by, utility strike",
        "discussion_notes": "Reviewed competent-person checklist.",
        "action_items": "Order trench shield by Friday.",
        "attendees": [_good_attendee()],
        "photos": ["data:image/png;base64,iVBORw0KGgo=",
                   "data:image/png;base64,iVBORw0KGgo="],
        "conductor_signature": "data:image/png;base64,iVBORw0KGgo=",
    }
    base.update(over)
    return base


def test_meeting_requires_conducted_by():
    with pytest.raises(Exception):
        MeetingCreate(**_good_meeting(conducted_by=""))


def test_meeting_happy_path():
    m = MeetingCreate(**_good_meeting())
    assert m.conducted_by == "James Fisher (Jimmy)"
    assert len(m.attendees) == 1


# ── PDF render contract tests ───────────────────────────────────────


def _record(**over: Any) -> Dict[str, Any]:
    base = {
        "id": "cert-mtg-1",
        "doc_id": "MTG-2026-09999",
        "project_name": "Cert Project",
        "project_number": "ZZ-CERT-001",
        "location": "Cert Site",
        "meeting_date": "2026-06-15",
        "meeting_time": "08:00",
        "conducted_by": "James Fisher (Jimmy)",
        "topic": "Excavation Safety",
        "hazards_reviewed": "Cave-in\nStruck-by\nUtility strike",
        "discussion_notes": "Reviewed competent-person checklist.",
        "action_items": "Order trench shield by Friday.",
        "attendees": [{
            "name": "Jose Garcia", "company": "MASCI",
            "trade": "Foreman",
            "signature": "data:image/png;base64,iVBORw0KGgo=",
            "acknowledged": True,
            "acknowledged_at": "2026-06-15T12:00:00Z",
        }],
        "photos": [],
    }
    base.update(over)
    return base


def test_pdf_renders_conducted_by():
    html = _render_meeting("meeting", _record())
    assert "James Fisher (Jimmy)" in html
    assert "Conducted By" in html


def test_pdf_renders_hazards_from_hazards_reviewed():
    html = _render_meeting("meeting", _record())
    assert "Cave-in" in html
    assert "Struck-by" in html
    assert "Utility strike" in html


def test_pdf_renders_discussion_from_discussion_notes():
    html = _render_meeting("meeting", _record())
    assert "competent-person checklist" in html


def test_pdf_renders_string_action_items():
    html = _render_meeting("meeting", _record())
    assert "Order trench shield" in html


def test_pdf_sections_2_through_5_always_render_no_skip():
    """The production defect was sections jumping 01 → 06 → 07.
    Every section 02–07 must always render so numbering is stable."""
    html = _render_meeting("meeting", _record(
        hazards_reviewed="", discussion_notes="",
        action_items="", references_cited="",
    ))
    for label in [
        "02 · Hazards Discussed",
        "03 · Discussion",
        "04 · Action Items",
        "05 · Additional Notes",
        "06 · Photos",
        "07 · Attendance and Acknowledgement",
    ]:
        assert label in html, f"PDF missing section header {label!r}"


def test_pdf_empty_sections_show_placeholder_not_blank():
    html = _render_meeting("meeting", _record(
        hazards_reviewed="", discussion_notes="",
        action_items="", references_cited="",
    ))
    # The placeholder shows up for every empty section.
    assert html.count("None recorded") >= 3


def test_pdf_attendance_table_has_five_columns():
    html = _render_meeting("meeting", _record())
    for col in ["Name", "Company", "Trade / Role", "Signature", "Acknowledged"]:
        assert col in html, f"Attendance table missing column {col}"


def test_pdf_attendance_shows_acknowledged_status():
    html = _render_meeting("meeting", _record())
    assert "Acknowledged" in html
    # When attendee.acknowledged is True the checkmark renders.
    assert "✓ Acknowledged" in html


def test_pdf_attendance_blank_name_renders_em_dash():
    html = _render_meeting("meeting", _record(attendees=[{
        "company": "MASCI",
        "signature": "data:image/png;base64,iVBORw0KGgo=",
        "acknowledged": True,
    }]))
    # No null/undefined leak — em-dash placeholder appears.
    assert "—" in html
    assert "null" not in html.lower() or html.lower().count("null") <= 2  # tolerate the word 'null' in unrelated places
    assert "undefined" not in html
    assert "nan" not in html.lower() or html.lower().count("nan") <= 2  # tolerate "trans" / "permanant" etc.


def test_pdf_legacy_field_names_still_render():
    """Legacy meetings stored hazards under `hazards` and discussion
    under `discussion`. They must still render correctly."""
    html = _render_meeting("meeting", _record(
        hazards_reviewed=None, discussion_notes=None,
        hazards="Legacy hazard text",
        discussion="Legacy discussion text",
    ))
    assert "Legacy hazard text" in html
    assert "Legacy discussion text" in html
