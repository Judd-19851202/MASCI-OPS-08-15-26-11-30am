"""DR-PDF-003 · PDF Polish & Production Intelligence regression.

Covers R-PDF-4 (Hide Empty Photos), R-PDF-5 (Legacy Section 09
Rationalization), R-PDF-6 (Production Totals). Also asserts that
every prior certified surface (Exec Summary, Safe Day Badge, Crew
Math Collapse, Excavation Surface, MM-001B 09d, DR-FIX-3 signer,
audit footer) is preserved unchanged.
"""
from __future__ import annotations
import importlib
import sys
import uuid
from typing import Any, Dict, List

import pytest

sys.path.insert(0, "/app/backend")
pdf_render = importlib.import_module("pdf_render")

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _doc(**overrides):
    base = {
        "id": str(uuid.uuid4()),
        "doc_id": "DR-2026-77777",
        "project_name": "DR-PDF-003 fixture",
        "project_number": "JOB-PDF003-ABC",
        "location": "Yard",
        "report_date": "2026-06-08",
        "report_number": "DR-20260608-001",
        "prepared_by": "Test Foreman",
        "superintendent": "Test Super",
        "schedule_delays": "No",
        "weather_impact": "No",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "general_notes": "fixture",
        "photos": [],  # default to empty for R-PDF-4 tests
        "prepared_by_signature": ONE_PX,
        "created_at": "2026-06-08T22:00:00+00:00",
    }
    base.update(overrides)
    return base


# ─────────────────────────────────────────────────────────────────────
# R-PDF-4 · Hide empty Photos
# ─────────────────────────────────────────────────────────────────────

def test_r_pdf_4_no_photos_section_when_photos_empty():
    html = pdf_render._render_daily(_doc(photos=[]))
    # The entire "10 · Photos" section header must be absent.
    assert "10 · Photos" not in html
    assert "10 \u00b7 Photos" not in html  # mid-dot variant


def test_r_pdf_4_no_photos_section_when_only_unresolvable_refs():
    """If photos[] contains entries but NONE resolve to a valid image
    (e.g., only `photo://` refs that fail resolution), the section
    must STILL be skipped — `_photos_block` returns empty in that case."""
    # Use a deliberately unresolvable photo:// ref
    html = pdf_render._render_daily(_doc(photos=["photo://nonexistent-key-12345"]))
    assert "10 · Photos" not in html


def test_r_pdf_4_renders_when_valid_photos_present():
    html = pdf_render._render_daily(_doc(photos=[ONE_PX] * 6))
    assert "10 · Photos" in html
    # Six img tags should appear inside the photos block
    photos_start = html.index("10 · Photos")
    photos_block = html[photos_start:photos_start + 30000]
    assert photos_block.count("<img ") >= 6


def test_r_pdf_4_renders_when_mixed_resolvable_and_unresolvable():
    """If at least one photo resolves, the section must render."""
    html = pdf_render._render_daily(
        _doc(photos=["photo://bad-ref-1", ONE_PX, "photo://bad-ref-2"])
    )
    assert "10 · Photos" in html


# ─────────────────────────────────────────────────────────────────────
# R-PDF-5 · Legacy Section 09 Rationalization
# ─────────────────────────────────────────────────────────────────────

def test_r_pdf_5_legacy_only_renders_full_legacy_table():
    """Pre-Wave-1B doc: activities present, production empty → legacy 09
    must render in its FULL 5-column form (no data lost)."""
    html = pdf_render._render_daily(_doc(
        activities=[
            {"activity": "Excavation", "percent_complete": 60,
             "station_from": "10+00", "station_to": "12+00",
             "notes": "Started SB lane"},
        ],
        production=[],
    ))
    assert "09 · Activities Performed" in html
    # Full-table columns must all appear in the legacy render
    legacy_block = html[html.index("09 · Activities Performed"):
                        html.index("09 · Activities Performed") + 3000]
    for col in ("Activity", "% Done", "From", "To", "Notes"):
        assert col in legacy_block
    # Data preserved (station + activity)
    assert "10+00" in legacy_block
    assert "Excavation" in legacy_block


def test_r_pdf_5_slimmed_when_production_populated():
    """When BOTH activities and production exist, legacy renders as the
    slimmed 09a · Activity Progress (Activity + % Done + Notes only).
    Station and quantity live in 09b — no duplication on the PDF."""
    html = pdf_render._render_daily(_doc(
        activities=[
            {"activity": "Mainline paving", "percent_complete": 100,
             "station_from": "12+50", "station_to": "23+50",
             "notes": "1100 LF complete"},
        ],
        production=[
            {"description": "SP-12.5 placed", "quantity": 240, "unit": "TON",
             "station_from": "12+50", "station_to": "23+50",
             "notes": "1.5 in lift"},
        ],
    ))
    # Legacy section is now "09a · Activity Progress"
    assert "09a · Activity Progress" in html
    # Legacy 09 (full title) must be GONE — replaced by 09a
    assert "09 · Activities Performed" not in html
    # Production section still present
    assert "09b · Production Quantities" in html

    # Slimmed 09a must NOT carry From/To columns
    slim_start = html.index("09a · Activity Progress")
    slim_end = html.index("09b · Production Quantities")
    slim_block = html[slim_start:slim_end]
    assert "From" not in slim_block
    assert "To" not in slim_block
    # But MUST carry the unique columns (Activity, % Done, Notes)
    assert "Activity" in slim_block
    assert "% Done" in slim_block
    assert "Notes" in slim_block
    # Unique value (percent_complete) preserved
    assert "100%" in slim_block


def test_r_pdf_5_no_information_lost():
    """Every unique datapoint in the legacy activities row must still
    appear somewhere on the PDF (either in 09a or in 09b)."""
    doc = _doc(
        activities=[
            {"activity": "Curb pour", "percent_complete": 75,
             "station_from": "5+00", "station_to": "6+25",
             "notes": "RT side"},
        ],
        production=[
            {"description": "Curb installed", "quantity": 125, "unit": "LF",
             "station_from": "5+00", "station_to": "6+25", "notes": ""},
        ],
    )
    html = pdf_render._render_daily(doc)
    # Activity descriptor + % preserved in 09a
    assert "Curb pour" in html
    assert "75%" in html
    assert "RT side" in html
    # Station ranges still on the PDF (now in 09b)
    assert "5+00" in html
    assert "6+25" in html
    # Production qty/unit visible in 09b
    assert "125" in html


def test_r_pdf_5_no_activities_no_legacy_section():
    """If activities[] is empty, neither 09 nor 09a should render —
    behavior unchanged from prior baseline."""
    html = pdf_render._render_daily(_doc(
        activities=[],
        production=[{"description": "x", "quantity": 1, "unit": "EA"}],
    ))
    assert "09 · Activities Performed" not in html
    assert "09a · Activity Progress" not in html


# ─────────────────────────────────────────────────────────────────────
# R-PDF-6 · Production Totals
# ─────────────────────────────────────────────────────────────────────

def test_r_pdf_6_totals_row_renders_for_single_unit():
    html = pdf_render._render_daily(_doc(
        production=[
            {"description": "SP-12.5 placed", "quantity": 240, "unit": "TON",
             "station_from": "12+50", "station_to": "23+50"},
        ],
    ))
    assert "Production Totals" in html
    assert "240 TON" in html


def test_r_pdf_6_totals_aggregate_by_unit():
    """Multiple rows of the same unit must sum; multiple units must all
    appear in the totals row separated by `·`."""
    html = pdf_render._render_daily(_doc(
        production=[
            {"description": "SP-12.5 lift 1", "quantity": 120, "unit": "TON"},
            {"description": "SP-12.5 lift 2", "quantity": 120, "unit": "TON"},
            {"description": "Tack coat",      "quantity": 165, "unit": "GAL"},
            {"description": "RCP install",    "quantity": 1100, "unit": "LF"},
        ],
    ))
    # Two TON rows must sum to 240
    assert "Production Totals" in html
    assert "240 TON" in html
    assert "165 GAL" in html
    assert "1100 LF" in html


def test_r_pdf_6_totals_use_custom_unit_label_for_OTHER():
    """OTHER + custom_unit_label must aggregate by the custom label,
    not by the literal 'OTHER' string."""
    html = pdf_render._render_daily(_doc(
        production=[
            {"description": "Lane miles A", "quantity": 0.21, "unit": "OTHER",
             "custom_unit_label": "Lane-Mi"},
            {"description": "Lane miles B", "quantity": 0.14, "unit": "OTHER",
             "custom_unit_label": "Lane-Mi"},
        ],
    ))
    assert "Production Totals" in html
    # 0.21 + 0.14 = 0.35
    assert "0.35 Lane-Mi" in html


def test_r_pdf_6_detail_rows_preserved():
    """Totals row must NOT replace the detail rows — both must coexist
    in the 09b table."""
    html = pdf_render._render_daily(_doc(
        production=[
            {"description": "RCP install", "quantity": 100, "unit": "LF",
             "station_from": "10+00", "station_to": "11+00",
             "notes": "Class III"},
        ],
    ))
    # Detail row data
    assert "RCP install" in html
    assert "10+00" in html
    assert "11+00" in html
    assert "Class III" in html
    # Totals row
    assert "Production Totals" in html
    assert "100 LF" in html


def test_r_pdf_6_no_totals_when_production_empty():
    """No production rows → no totals row and no 09b section at all."""
    html = pdf_render._render_daily(_doc(production=[]))
    assert "Production Totals" not in html
    assert "09b · Production Quantities" not in html


def test_r_pdf_6_zero_quantity_excluded_from_totals():
    """Rows with quantity 0 should not produce a 'Production Totals: 0 X' line."""
    html = pdf_render._render_daily(_doc(
        production=[
            {"description": "Placeholder", "quantity": 0, "unit": "TON"},
            {"description": "Actual placement", "quantity": 50, "unit": "TON"},
        ],
    ))
    assert "Production Totals" in html
    # Sum is 50, not 0
    assert "50 TON" in html


def test_r_pdf_6_no_persistence_pure_derivation():
    """Static guard: the production totals logic must not write to MongoDB."""
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    # The unit_totals dict must never be persisted
    assert "unit_totals" in src
    # Should appear ONLY inside _render_daily (no exports, no insert calls)
    for forbidden in ("insert_one(unit_totals", "update_one(unit_totals",
                      "insert_many(unit_totals"):
        assert forbidden not in src


# ─────────────────────────────────────────────────────────────────────
# Backward compatibility — every prior certified surface preserved
# ─────────────────────────────────────────────────────────────────────

def _full_doc():
    """Realistic populated DR fixture used for regression sweeps."""
    return _doc(
        photos=[ONE_PX] * 6,
        general_notes="Detailed narrative for the day.",
        masci_crews=[
            {"name": "Carlos M.", "trade": "Foreman", "start_time": "06:30",
             "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5,
             "work_performed": "Supervised crew"},
            {"name": "Diego R.", "trade": "Paver Op", "start_time": "06:30",
             "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5,
             "work_performed": "Operated paver"},
        ],
        production=[
            {"description": "SP-12.5 placed", "quantity": 240, "unit": "TON",
             "station_from": "12+50", "station_to": "23+50"},
        ],
        constraints=[
            {"constraint_type": "trucking", "hours_impact": 0.75,
             "may_affect_schedule": True, "notes": "Truck shortage"},
        ],
        activities=[
            {"activity": "Mainline paving", "percent_complete": 100,
             "station_from": "12+50", "station_to": "23+50",
             "notes": "1100 LF complete"},
        ],
    )


def test_compat_executive_summary_card_still_renders():
    html = pdf_render._render_daily(_full_doc())
    idx = html.find("Executive Summary")
    assert idx != -1
    assert idx < html.find("01 · Project Information")


def test_compat_safe_day_badge_still_renders():
    html = pdf_render._render_daily(_full_doc())
    assert "SAFE DAY" in html


def test_compat_crew_collapse_still_works():
    html = pdf_render._render_daily(_full_doc())
    crew_start = html.find("04 · MASCI Crews on Site")
    crew_block = html[crew_start:crew_start + 6000]
    assert "Common schedule" in crew_block
    assert "Total Hours" in crew_block


def test_compat_excavation_surface_still_hidden_when_inactive():
    html = pdf_render._render_daily(_full_doc())
    assert "03b · Excavation Activity" not in html


def test_compat_signature_section_preserved():
    html = pdf_render._render_daily(_full_doc())
    assert "11 · Signature" in html
    sig_block = html.split("11 · Signature", 1)[1]
    assert "Superintendent signature" not in sig_block.lower()


def test_compat_full_pdf_pipeline_renders():
    blob = pdf_render.render_record_pdf("daily-report", _full_doc())
    assert isinstance(blob, (bytes, bytearray)) and blob[:5] == b"%PDF-"


def test_compat_audit_footer_machinery_intact():
    src = open("/app/backend/pdf_render.py", "r", encoding="utf-8").read()
    assert "_compute_audit_envelope_sha256" in src
    assert "@bottom-center" in src
    assert "Official Record" in src


def test_compat_mm_001b_section_unchanged(monkeypatch):
    def _stub(*args, **kwargs):
        return {
            "dispatch_rows": [
                {"haul_type": "Inbound · Material", "material": "SP-12.5",
                 "source_location": "Plant", "destination": "Job",
                 "load_count": 10, "carrier": "Lopez", "truck_id": "T-1",
                 "id": "d-1"},
            ],
            "excavation_rows": [],
        }
    monkeypatch.setattr(pdf_render, "_fetch_dr_render_extras", _stub)
    html = pdf_render._render_daily(_full_doc())
    assert "09d · MASCI Hauling Today" in html
    assert "Lopez" in html
