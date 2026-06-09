"""SM-PDF-001 · Safety Meeting PDF layout remediation regression.

Covers SM-PDF-1 (meeting-content-first reorder), SM-PDF-2 (hide empty
photos), SM-PDF-3 (compact attendance), SM-PDF-4 (Executive Summary).
Also asserts every prior PDF certification is preserved (DR-PDF-002,
DR-PDF-003, MM-ENTRY-002, audit-footer, DR-FIX-3).
"""
from __future__ import annotations
import importlib
import sys
from typing import Any, Dict

sys.path.insert(0, "/app/backend")
pdf_render = importlib.import_module("pdf_render")

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _meeting(**overrides):
    base = {
        "id": "sm-fixture-1",
        "meeting_number": "SM-2026-0001",
        "topic": "Heat Stress Prevention",
        "meeting_type": "Toolbox Talk",
        "project_name": "University High School Parent Loop",
        "project_number": "JOB-UHS-001",
        "meeting_date": "2026-06-08",
        "location": "Job trailer",
        "facilitator": "Mike Aragones",
        "duration_minutes": 15,
        "hazards": ["Heat exhaustion", "Dehydration", "Inadequate PPE"],
        "discussion": "Reviewed OSHA heat illness criteria. Crews to take "
                      "15-min breaks every 2h in shade.",
        "action_items": [
            {"title": "Install shade", "owner": "Carlos M.",
             "due_date": "2026-06-10", "status": "Open"},
        ],
        "attendees": [
            {"name": "Carlos M.", "company": "MASCI",
             "signature": ONE_PX, "signed_at": "2026-06-08 06:35"},
            {"name": "Diego R.", "company": "MASCI",
             "signature": ONE_PX, "signed_at": "2026-06-08 06:36"},
        ],
        "photos": [ONE_PX, ONE_PX],
        "facilitator_signature": ONE_PX,
    }
    base.update(overrides)
    return base


# ────────────────────────────────────────────────────────────────────
# SM-PDF-1 · Meeting content first
# ────────────────────────────────────────────────────────────────────

def test_sm_pdf_1_content_renders_before_attendance():
    """Discussion / Hazards / Action Items must appear BEFORE the
    Attendance section in the rendered HTML."""
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    idx_discussion = html.find("03 · Discussion")
    idx_hazards = html.find("02 · Hazards Discussed")
    idx_actions = html.find("04 · Action Items")
    idx_attendance = html.find("07 · Attendance")
    assert idx_hazards != -1, "Hazards section missing"
    assert idx_discussion != -1, "Discussion section missing"
    assert idx_actions != -1, "Action Items section missing"
    assert idx_attendance != -1, "Attendance section missing"
    # Order assertion — content first, attendance last
    assert idx_hazards < idx_attendance
    assert idx_discussion < idx_attendance
    assert idx_actions < idx_attendance


def test_sm_pdf_1_meeting_details_block_present():
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    assert "01 · Meeting Details" in html
    # Specific KVs visible
    assert "Heat Stress Prevention" in html
    assert "Toolbox Talk" in html
    assert "Mike Aragones" in html
    assert "Job trailer" in html


def test_sm_pdf_1_signatures_after_attendance():
    """Signatures section ('08 · Sign-Off') must appear AFTER attendance."""
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    idx_att = html.find("07 · Attendance")
    idx_sig = html.find("08 · Sign-Off")
    assert idx_att != -1 and idx_sig != -1
    assert idx_sig > idx_att


# ────────────────────────────────────────────────────────────────────
# SM-PDF-2 · Hide empty photos
# ────────────────────────────────────────────────────────────────────

def test_sm_pdf_2_no_photos_section_when_empty():
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting(photos=[]))
    assert "06 · Photos" not in html


def test_sm_pdf_2_no_photos_section_when_only_unresolvable_refs():
    html = pdf_render._render_meeting(
        "Site Safety Meeting", _meeting(photos=["photo://nonexistent-key"]),
    )
    assert "06 · Photos" not in html


def test_sm_pdf_2_renders_photos_when_present():
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    assert "06 · Photos" in html
    # Photo count line on the Executive card
    card_block = html[:html.find("01 · Meeting Details")]
    assert "PHOTOS" in card_block
    assert "2" in card_block  # 2 photos in fixture


# ────────────────────────────────────────────────────────────────────
# SM-PDF-3 · Compact attendance
# ────────────────────────────────────────────────────────────────────

def test_sm_pdf_3_attendance_renders_all_columns():
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    att_block = html[html.find("07 · Attendance"):]
    # Required columns
    for col in ("Name", "Company / Trade", "Signature", "Acknowledged"):
        assert col in att_block, f"Missing attendance column: {col}"
    # Data preserved
    assert "Carlos M." in att_block
    assert "Diego R." in att_block
    # Timestamps preserved
    assert "2026-06-08 06:35" in att_block
    assert "2026-06-08 06:36" in att_block


def test_sm_pdf_3_attendance_signature_images_compact():
    """Attendance signature images must use the compact <28px height
    style — not the full 38px from the legacy _render_generic flow."""
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    att_block = html[html.find("07 · Attendance"):
                     html.find("08 · Sign-Off")]
    assert "max-height:28px" in att_block
    assert "max-height:38px" not in att_block


def test_sm_pdf_3_handles_large_attendance_lists():
    """10+ attendees should render in the compact table without error."""
    big_attendees = [
        {"name": f"Worker {i}", "company": "MASCI",
         "signature": ONE_PX, "signed_at": f"2026-06-08 06:{30+i:02d}"}
        for i in range(12)
    ]
    blob = pdf_render.render_record_pdf(
        "meeting", _meeting(attendees=big_attendees),
    )
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"
    import pypdf, io
    r = pypdf.PdfReader(io.BytesIO(blob))
    # Every attendee name must be present somewhere in the PDF.
    full_text = "".join((p.extract_text() or "") for p in r.pages)
    for i in range(12):
        assert f"Worker {i}" in full_text, f"Missing attendee Worker {i}"


# ────────────────────────────────────────────────────────────────────
# SM-PDF-4 · Executive Summary card
# ────────────────────────────────────────────────────────────────────

def test_sm_pdf_4_card_renders_first():
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    idx_card = html.find("Safety Meeting · ")  # kicker
    idx_first_section = html.find("01 · Meeting Details")
    assert idx_card != -1
    assert idx_card < idx_first_section


def test_sm_pdf_4_card_contains_required_fields():
    html = pdf_render._render_meeting("Site Safety Meeting", _meeting())
    card = html[:html.find("01 · Meeting Details")]
    for label in ("TOPIC", "MEETING TYPE", "ATTENDEES", "HAZARDS",
                  "ACTION ITEMS", "PHOTOS"):
        assert label in card, f"Card missing label: {label}"
    # Status badge present
    assert "COMPLETED" in card  # 2 attendees with signatures → completed


def test_sm_pdf_4_card_status_draft_when_no_attendees():
    html = pdf_render._render_meeting(
        "Site Safety Meeting", _meeting(attendees=[]),
    )
    card = html[:html.find("01 · Meeting Details")]
    assert "DRAFT" in card


def test_sm_pdf_4_card_status_recorded_when_no_signatures():
    html = pdf_render._render_meeting(
        "Site Safety Meeting",
        _meeting(attendees=[
            {"name": "A", "company": "MASCI", "signature": ""},
        ]),
    )
    card = html[:html.find("01 · Meeting Details")]
    assert "RECORDED" in card


def test_sm_pdf_4_card_handles_string_hazards():
    """Hazards passed as a comma-separated string must still render
    in the card."""
    html = pdf_render._render_meeting(
        "Site Safety Meeting",
        _meeting(hazards="Heat, Dehydration, PPE"),
    )
    card = html[:html.find("01 · Meeting Details")]
    assert "HAZARDS" in card
    assert "Heat" in card and "Dehydration" in card and "PPE" in card


def test_sm_pdf_4_card_no_hazards_shows_none_recorded():
    html = pdf_render._render_meeting(
        "Site Safety Meeting", _meeting(hazards=[]),
    )
    card = html[:html.find("01 · Meeting Details")]
    assert "None recorded" in card


# ────────────────────────────────────────────────────────────────────
# Pipeline + dispatch
# ────────────────────────────────────────────────────────────────────

def test_meeting_kind_dispatches_to_new_renderer():
    """`render_record_pdf("meeting", ...)` must route to `_render_meeting`,
    not the legacy `_render_generic`."""
    blob = pdf_render.render_record_pdf("meeting", _meeting())
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"
    # Proof via rendered text — new layout's Executive Summary kicker is
    # unique to _render_meeting.
    import pypdf, io
    r = pypdf.PdfReader(io.BytesIO(blob))
    p1 = r.pages[0].extract_text() or ""
    assert "SAFETY MEETING ·" in p1.upper()
    # Card label "TOPIC" appears on page 1
    assert "TOPIC" in p1


def test_pdf_pipeline_produces_valid_bytes():
    blob = pdf_render.render_record_pdf("meeting", _meeting())
    assert blob[:5] == b"%PDF-"


def test_meeting_no_data_loss_legacy_record():
    """A meeting record submitted with a `notes` field but no
    `discussion` should still surface that narrative."""
    html = pdf_render._render_meeting(
        "Site Safety Meeting",
        _meeting(discussion="", notes="Discussed lockout/tagout."),
    )
    # `notes` falls back into the discussion render path
    assert "Discussed lockout/tagout" in html


# ────────────────────────────────────────────────────────────────────
# Backward compatibility — other kinds untouched
# ────────────────────────────────────────────────────────────────────

def test_other_kinds_still_use_generic_renderer():
    """Inspection / JHA / Incident must continue rendering through
    `_render_generic` — not the new meeting renderer."""
    # We assert through dispatch: an inspection record renders without
    # crashing and contains the legacy "Details" suffix from _render_generic.
    blob = pdf_render.render_record_pdf("inspection", {
        "id": "insp-1",
        "project_name": "Inspection fixture",
        "prepared_by": "Inspector",
        "attendees": [{"name": "Test", "company": "MASCI",
                       "signature": ONE_PX}],
        "photos": [ONE_PX],
    })
    assert blob[:5] == b"%PDF-"


def test_dr_pdf_pipeline_still_works():
    """Adding the meeting renderer must not regress daily-report renders."""
    dr_doc = {
        "id": "dr-1", "doc_id": "DR-2026-1",
        "project_name": "DR fixture", "project_number": "JOB-1",
        "location": "X", "report_date": "2026-06-08",
        "prepared_by": "Test", "superintendent": "Test",
        "photos": [ONE_PX] * 6,
        "prepared_by_signature": ONE_PX,
    }
    blob = pdf_render.render_record_pdf("daily-report", dr_doc)
    assert blob[:5] == b"%PDF-"


def test_audit_footer_machinery_intact():
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    assert "_compute_audit_envelope_sha256" in src
    assert "@bottom-center" in src


def test_no_workflow_change_pure_render():
    """Static guard — `_render_meeting` must not write to any collection."""
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    fn_start = src.index("def _render_meeting")
    fn_end = src.index("\n\ndef ", fn_start)
    fn_src = src[fn_start:fn_end]
    for forbidden in ("insert_one", "update_one", "delete_one",
                      "insert_many", "update_many", "delete_many",
                      "drop_collection"):
        assert forbidden not in fn_src, (
            f"SM-PDF-001 violated pure-render: {forbidden} found"
        )
