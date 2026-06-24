"""TRACK 15.76 · P0 regression — meeting/incident email body must not
crash with ``NameError: name '_wl' is not defined``.

The Trust Spine surfaced this defect: every meeting/incident submit
was firing ``_dispatch_auto_email`` which called
``render_email_html(kind, record, note)`` — and that function
referenced ``_wl`` (white-label config) without resolving it locally.
The error was silently swallowed by ``except Exception`` in the
dispatcher, so emails simply never went out.

This test calls ``render_email_html`` directly for every supported
``kind`` and asserts it returns a non-empty HTML body without raising.
"""
from __future__ import annotations

import pytest

KINDS = (
    "daily-report",
    "meeting",
    "inspection",
    "incident",
    "jha",
    "qaqc",
    "equipment-inspection",
    "dvir",
)


@pytest.mark.parametrize("kind", KINDS)
def test_render_email_html_does_not_raise(kind):
    from pdf_render import render_email_html  # noqa: PLC0415
    record = {
        "id": f"regression-{kind}",
        "project_name": "Test Project",
        "project_number": "20-07",
        "report_date": "2026-02-15",
        "severity": "minor",
        "osha_recordable": "No",
    }
    html = render_email_html(kind, record, note="Routine submission.")
    assert html and isinstance(html, str)
    assert "MASCI" in html or "Operations" in html


def test_render_email_html_severe_note_path():
    """The warn-tone branch (SEVERE, EQUIPMENT FAIL, ⚠) must also
    render without the ``_wl`` NameError."""
    from pdf_render import render_email_html  # noqa: PLC0415
    html = render_email_html(
        "incident",
        {"id": "x", "project_number": "20-07"},
        note="SEVERE INCIDENT — please review immediately.",
    )
    assert html
    html2 = render_email_html(
        "equipment-inspection",
        {"id": "x", "project_number": "20-07",
         "fail_count": 2, "equipment_unit": "TR-101"},
        note="EQUIPMENT FAIL — 2 item(s) failed inspection. TR-101 tagged OUT OF SERVICE.",
    )
    assert html2
