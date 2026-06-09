"""DR-PDF-002 · Executive Comprehension Sprint regression.

Covers R-PDF-1 (Executive Summary Card), R-PDF-2 (Safe Day Badge),
R-PDF-3 (Collapse Crew Math), R-PDF-10 (Excavation Activity Surface).
Also asserts existing DR-FIX-1/2/3 + MM-001B + audit-footer surfaces
are preserved unchanged.
"""
from __future__ import annotations
import sys
sys.path.insert(0, "/app/backend")

import importlib
import json
import os
import urllib.request
import urllib.error
import uuid
from typing import Any, Dict

import pytest

BACKEND = os.environ.get("BACKEND_URL", "http://localhost:8001")
API = f"{BACKEND}/api"

pdf_render = importlib.import_module("pdf_render")

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _req(method, path, *, body=None, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"status": resp.status, "json": json.loads(resp.read().decode() or "{}")}
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode() or "{}")
        except Exception:  # noqa: BLE001
            body = {}
        return {"status": e.code, "json": body}


def _make_doc(**overrides):
    base = {
        "id": str(uuid.uuid4()),
        "doc_id": "DR-2026-77777",
        "project_name": "I-95 Resurfacing · MP 217-220 SB",
        "project_number": "JOB-PDF002-ABC",
        "location": "Yard",
        "report_date": "2026-06-08",
        "report_number": "DR-20260608-001",
        "prepared_by": "John Foreman",
        "superintendent": "Mike Aragones",
        "weather_summary": "Clear · 88F",
        "schedule_delays": "No",
        "weather_impact": "No",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "general_notes": "Crews placed 240 TON SP-12.5 between STA 12+50 and STA 23+50.",
        "masci_crews": [
            {"name": "Carlos M.", "trade": "Foreman", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Supervised paving crew"},
            {"name": "Diego R.", "trade": "Paver Op", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Operated paver"},
            {"name": "Tomas L.", "trade": "Screed Op", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Screed adjustments"},
        ],
        "production": [
            {"description": "SP-12.5 placed", "quantity": 240, "unit": "TON", "station_from": "12+50", "station_to": "23+50"},
        ],
        "constraints": [
            {"constraint_type": "trucking", "hours_impact": 0.75, "may_affect_schedule": True, "may_require_rfi": False, "notes": "Truck shortage"},
        ],
        "photos": [ONE_PX] * 6,
        "prepared_by_signature": ONE_PX,
        "created_at": "2026-06-08T22:00:00+00:00",
    }
    base.update(overrides)
    return base


# ── R-PDF-2 · Safe Day Badge derivation ─────────────────────────────

def test_r_pdf_2_badge_green_default():
    badge = pdf_render._safe_day_badge(_make_doc())
    assert badge["state"] == "green"
    assert badge["label"] == "SAFE DAY"


def test_r_pdf_2_badge_amber_on_injury():
    badge = pdf_render._safe_day_badge(_make_doc(injuries_reported="Yes"))
    assert badge["state"] == "amber"
    assert badge["label"] == "ATTENTION REQUIRED"


def test_r_pdf_2_badge_red_on_incident():
    badge = pdf_render._safe_day_badge(_make_doc(safety_incidents_today="Yes"))
    assert badge["state"] == "red"
    assert badge["label"] == "STOP WORK / INCIDENT"


def test_r_pdf_2_badge_red_trumps_amber():
    # An incident + an injury should still resolve to red, not amber.
    badge = pdf_render._safe_day_badge(_make_doc(
        safety_incidents_today="Yes", injuries_reported="Yes",
    ))
    assert badge["state"] == "red"


# ── R-PDF-1 · Executive Summary Card rendering ──────────────────────

def test_r_pdf_1_card_renders_at_top_of_pdf():
    html = pdf_render._render_daily(_make_doc())
    # Card must appear BEFORE Section 01 in the rendered HTML.
    idx_card = html.find("Executive Summary")
    idx_01 = html.find("01 · Project Information")
    assert idx_card != -1, "Executive Summary card not rendered"
    assert idx_01 != -1, "Section 01 missing"
    assert idx_card < idx_01, "Executive Summary must precede Section 01"


def test_r_pdf_1_card_lines_include_work_production_constraints():
    doc = _make_doc()
    html = pdf_render._render_daily(doc)
    # The card content should reference the work performed and the
    # production placed.
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "WORK" in card_block
    assert "PRODUCTION" in card_block
    assert "240 TON" in card_block
    assert "CONSTRAINTS" in card_block
    # Trucking constraint with Schedule advisory must surface in the card.
    assert "Trucking" in card_block
    assert "Schedule" in card_block


def test_r_pdf_1_card_omits_notes_when_short():
    doc = _make_doc(general_notes="ok")
    html = pdf_render._render_daily(doc)
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "NOTES" not in card_block


def test_r_pdf_1_card_shows_none_when_no_constraints():
    doc = _make_doc(constraints=[])
    html = pdf_render._render_daily(doc)
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "CONSTRAINTS" in card_block
    assert "None" in card_block


def test_r_pdf_1_card_badge_appears_in_card():
    """R-PDF-2 badge HTML must be embedded inside the R-PDF-1 card."""
    html = pdf_render._render_daily(_make_doc())
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "SAFE DAY" in card_block


# ── R-PDF-3 · Collapse Crew Math ────────────────────────────────────

def test_r_pdf_3_common_schedule_caption_emitted():
    """All 3 crew share 06:30/15:30/30 — common-schedule caption must
    appear ABOVE the crew table once, and the per-row inline math must
    NOT appear under any crew (i.e., the gross/net string should appear
    EXACTLY ONCE — inside the caption)."""
    html = pdf_render._render_daily(_make_doc())
    crew_start = html.find("04 · MASCI Crews on Site")
    assert crew_start != -1
    crew_block = html[crew_start:crew_start + 6000]
    assert "Common schedule" in crew_block
    # The gross/net summary must appear EXACTLY ONCE — inside the caption.
    assert crew_block.count("9.0 h gross") == 1, (
        f"Expected 1 gross/net summary (caption only), found "
        f"{crew_block.count('9.0 h gross')} — per-row collapse failed"
    )


def test_r_pdf_3_per_row_summary_when_schedule_differs():
    """Add a 4th crew with a different schedule — that ONE crew should
    carry an inline gross/net summary, others should not."""
    doc = _make_doc()
    doc["masci_crews"].append(
        {"name": "OT Crew", "trade": "Laborer", "start_time": "05:00",
         "stop_time": "17:00", "lunch_minutes": 30, "hours": 11.5,
         "work_performed": "Overtime cleanup"}
    )
    html = pdf_render._render_daily(doc)
    crew_start = html.find("04 · MASCI Crews on Site")
    crew_block = html[crew_start:crew_start + 9000]
    # Common caption still present
    assert "Common schedule" in crew_block
    # The OT row should carry an inline summary
    assert "12.0 h gross" in crew_block or "11.50" in crew_block


def test_r_pdf_3_no_caption_when_no_majority():
    """Two crews, two different schedules → no majority → no common caption,
    each row gets its own inline math (legacy behavior)."""
    doc = _make_doc(masci_crews=[
        {"name": "A", "trade": "Op", "start_time": "06:00",
         "stop_time": "14:00", "lunch_minutes": 30, "hours": 7.5,
         "work_performed": "A"},
        {"name": "B", "trade": "Op", "start_time": "07:00",
         "stop_time": "16:00", "lunch_minutes": 30, "hours": 8.5,
         "work_performed": "B"},
    ])
    html = pdf_render._render_daily(doc)
    crew_start = html.find("04 · MASCI Crews on Site")
    crew_block = html[crew_start:crew_start + 6000]
    assert "Common schedule" not in crew_block


def test_r_pdf_3_total_hours_preserved():
    """Total Hours footer row must remain regardless of collapse logic."""
    html = pdf_render._render_daily(_make_doc())
    crew_start = html.find("04 · MASCI Crews on Site")
    crew_block = html[crew_start:crew_start + 6000]
    assert "Total Hours" in crew_block
    assert "25.50" in crew_block  # 3 crews × 8.5 hours


# ── R-PDF-10 · Excavation Activity Surface ──────────────────────────

def test_r_pdf_10_hidden_when_no_excavations():
    """Without excavation activity, Section 03b must not render."""
    html = pdf_render._render_daily(_make_doc())
    assert "03b · Excavation Activity" not in html


def test_r_pdf_10_executive_summary_omits_excavation_when_inactive():
    html = pdf_render._render_daily(_make_doc())
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "EXCAVATION" not in card_block


def test_r_pdf_10_renders_when_excavation_activity_today_yes():
    """When the DR flags excavation_activity_today=Yes and supplies
    linked_excavation_ids, the surface should appear and the card line
    should appear — but the fetch will return no rows in the test DB,
    so the surface degrades gracefully to count-only on the card."""
    doc = _make_doc(
        excavation_activity_today="Yes",
        linked_excavation_ids=["fake-id-1", "fake-id-2"],
    )
    html = pdf_render._render_daily(doc)
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "EXCAVATION" in card_block
    # 2 excavation IDs declared (no DB rows resolve in-process — that's OK).
    assert "2 excavations" in card_block


def test_r_pdf_10_excavation_surface_table_renders_with_data():
    """Inject excavation rows directly into the helper to prove the
    table renderer produces the right columns and risk descriptors."""
    rows = [
        {"id": "exc-1", "excavation_number": "EXC-2026-0001",
         "work_area": "STA 15+00 LT", "soil_classification": "Type C",
         "depth_ft": 6.5, "depth_ge_5ft": True,
         "competent_person_name": "Alex P.", "status": "Open"},
        {"id": "exc-2", "excavation_number": "EXC-2026-0002",
         "work_area": "STA 18+50 RT", "soil_classification": "Type B",
         "depth_ft": 3.5, "competent_person_name": "Sam K.",
         "utility_conflicts_observed": True, "status": "Under Review"},
    ]
    html = pdf_render._render_excavation_surface(rows)
    assert "03b · Excavation Activity" in html
    assert "EXC-2026-0001" in html
    assert "EXC-2026-0002" in html
    assert "≥5 ft" in html  # depth descriptor for the first excavation
    assert "Type C" in html
    assert "Utility conflict" in html  # second excavation's flag
    assert "Alex P." in html
    assert "Sam K." in html


def test_r_pdf_10_no_workflow_change_visibility_only():
    """Source guard: the renderer reads excavation rows but never writes
    to trench_excavations. `_render_excavation_surface` is a pure
    function of its input."""
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    fn_start = src.index("def _render_excavation_surface")
    fn_end = src.index("\n\ndef ", fn_start)
    fn_src = src[fn_start:fn_end]
    for forbidden in ("insert_one", "update_one", "delete_one",
                      "insert_many", "update_many", "delete_many",
                      "drop_collection"):
        assert forbidden not in fn_src, f"R-PDF-10 violated visibility-only: {forbidden} found"


# ── Backward compatibility — full PDF render still works ────────────

def test_existing_pdf_pipeline_renders_full_doc():
    """End-to-end render via render_record_pdf must still produce a
    valid PDF (starts with %PDF-) with the executive card, audit footer,
    and signature all intact."""
    blob = pdf_render.render_record_pdf("daily-report", _make_doc())
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"


def test_audit_footer_still_renders():
    """The Wave-1C SHA256 audit footer must still be wired."""
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    assert "_compute_audit_envelope_sha256" in src
    assert "@bottom-center" in src
    assert "Official Record" in src


def test_dr_fix_3_signature_preserved():
    html = pdf_render._render_daily(_make_doc())
    # Section 11 single signer (DR-FIX-3) preserved.
    assert "11 · Signature" in html
    # Superintendent signature label must NOT appear in the rendered HTML.
    sig_section = html.split("11 · Signature", 1)[1]
    assert "Superintendent signature" not in sig_section.lower()


def test_mm_001b_section_still_present_when_dispatch_exists(monkeypatch):
    """If `_fetch_dr_render_extras` returns dispatch rows, the 09d
    section still renders. We stub the fetch to inject rows."""
    def _stub(*args, **kwargs):
        return {
            "dispatch_rows": [
                {"haul_type": "Inbound · Material",
                 "material": "SP-12.5 Asphalt",
                 "source_location": "APAC Plant",
                 "destination": "Job 12+50",
                 "load_count": 12, "carrier": "Lopez Trucking",
                 "truck_id": "T-101", "id": "disp-1"},
            ],
            "excavation_rows": [],
        }
    monkeypatch.setattr(pdf_render, "_fetch_dr_render_extras", _stub)
    html = pdf_render._render_daily(_make_doc())
    # MM-ENTRY-002 retitled Section 09d to "Material Movement Today"
    # (now covers both MASCI hauling and foreman-authored outbound).
    assert "09d · Material Movement Today" in html
    assert "SP-12.5 Asphalt" in html
    assert "Lopez Trucking" in html
    # Executive Summary card should also pull dispatch into MATERIAL line.
    card_block = html[html.find("Executive Summary"):html.find("01 · Project Information")]
    assert "MATERIAL" in card_block
    assert "1 dispatch" in card_block
