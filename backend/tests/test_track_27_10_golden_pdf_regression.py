from __future__ import annotations

import sys
sys.path.insert(0, "/app/backend")

import importlib
from pathlib import Path

from pypdf import PdfReader

pdf_render = importlib.import_module("pdf_render")

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _golden_record():
    photos = [ONE_PX] * 8
    return {
        "id": "golden-dr-2710",
        "doc_id": "DR-2026-GOLDEN",
        "project_name": "University High Parent Loop Ext",
        "project_number": "UH-PLX-2710",
        "location": "Parent Loop Extension · North Side",
        "report_date": "2026-07-11",
        "report_number": "DR-2026-GOLDEN",
        "prepared_by": "John Supervisor",
        "superintendent": "Maria Superintendent",
        "weather_summary": "Observed conditions: Light rain; temperature 73–86°F; humidity 72% avg; wind up to 18 mph, gusts up to 27 mph; precipitation 0.18 in; peak weather signal at 2026-07-11T15:00",
        "weather_snapshot_meta": {
            "gps_lat": 29.4241,
            "gps_lng": -98.4936,
            "temperature_min_f": 73,
            "temperature_max_f": 86,
            "humidity_avg_pct": 72,
            "wind_max_mph": 18,
            "wind_gust_max_mph": 27,
            "precipitation_total_in": 0.18,
            "peak_condition": "Light rain",
            "peak_timestamp": "2026-07-11T15:00",
        },
        "weather_snapshots": [
            {"time": "06:00", "timestamp": "2026-07-11T06:00", "condition": "Overcast", "temp_f": 73, "humidity_pct": 81, "wind_mph": 8, "wind_gust_mph": 12, "precip_in": 0, "rain_in": 0},
            {"time": "15:00", "timestamp": "2026-07-11T15:00", "condition": "Light rain", "temp_f": 84, "humidity_pct": 68, "wind_mph": 18, "wind_gust_mph": 27, "precip_in": 0.18, "rain_in": 0.18},
        ],
        "schedule_delays": "No",
        "weather_impact": "No",
        "weather_impact_notes": "Supervisor confirmed no weather delay was charged today.",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "general_notes": "Crew completed curb prep, utility verification, and paving area staging.",
        "masci_crews": [
            {"name": "Crew A", "trade": "Labor", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Curb prep"},
            {"name": "Crew B", "trade": "Operator", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Equipment support"},
            {"name": "Crew C", "trade": "Finisher", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Utility verification"},
        ],
        "subcontractors": [{"company": "AAA Striping", "trade": "Striping", "workers": 4, "hours": 8}],
        "visitors": [{"name": "District Inspector", "company": "Owner Rep", "purpose": "Progress review"}],
        "equipment": [
            {"equipment_id": "EQ-01", "equipment_type": "Excavator", "hours": 8},
            {"equipment_id": "EQ-02", "equipment_type": "Dozer", "hours": 8},
            {"equipment_id": "EQ-03", "equipment_type": "Paver", "hours": 7},
            {"equipment_id": "EQ-04", "equipment_type": "Roller", "hours": 7},
            {"equipment_id": "EQ-05", "equipment_type": "Skid Steer", "hours": 6},
            {"equipment_id": "EQ-06", "equipment_type": "Water Truck", "hours": 6},
        ],
        "production": [
            {"description": "Curb prep", "quantity": 420, "unit": "LF", "station_from": "10+00", "station_to": "14+20"},
            {"description": "Base rock placed", "quantity": 180, "unit": "TON", "station_from": "10+00", "station_to": "14+20"},
            {"description": "Custom utility boxes", "quantity": 2, "unit": "OTHER", "custom_unit_label": "Vault Assemblies", "station_from": "12+10", "station_to": "12+20"},
        ],
        "constraints": [
            {"constraint_type": "weather", "hours_impact": 1.5, "notes": "Rain delay before paving."},
            {"constraint_type": "extra_work", "hours_impact": 2, "notes": "Added owner-requested cleanup."},
        ],
        "activities": [
            {"activity": "Curb prep and utility verification", "description": "Curb prep and utility verification", "percent_done": "100%"},
            {"activity": "Paving area staging", "description": "Paving area staging", "percent_done": "100%"},
        ],
        "photos": photos,
        "photo_captions": [f"Photo {i+1}" for i in range(len(photos))],
        "prepared_by_signature": ONE_PX,
        "ai_accepted_summary": "Accepted executive summary: crews completed curb prep, utility verification, subcontractor coordination, and paving area staging. No schedule delay was charged.",
        "ai_accepted_summary_meta": {
            "source": "manual",
            "approved_by": "Maria Superintendent",
            "accepted_at": "2026-07-11T19:00:00Z",
        },
        "attachments": [{"filename": "daily-cert.csv", "category": "Spreadsheet", "extension": "csv", "file_size": 1024}],
        "tomorrow_readiness": {"tomorrow_plan": "Continue base installation northbound.", "pm_needs": "Approve lane closure extension and verify trucking window."},
        "narrative_sections": {"tomorrow_plan": "Continue base installation northbound.", "follow_ups": "Approve lane closure extension and verify trucking window."},
        "created_at": "2026-07-11T22:00:00+00:00",
        "audit_envelope_sha256": "a" * 64,
    }


def _reader(tmp_path: Path):
    blob = pdf_render.render_record_pdf("daily-report", _golden_record())
    out = tmp_path / "golden_daily_report.pdf"
    out.write_bytes(blob)
    return PdfReader(str(out)), blob


def test_golden_pdf_opens_and_has_expected_page_range(tmp_path: Path):
    reader, blob = _reader(tmp_path)
    assert blob[:5] == b"%PDF-"
    assert 3 <= len(reader.pages) <= 6


def test_golden_pdf_structural_lock(tmp_path: Path):
    reader, _ = _reader(tmp_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    full = "\n".join(pages)

    assert full.count("Accepted executive summary") == 1
    assert "University High Parent Loop Ext" in full
    assert "OPERATIONS PLATFORM" in full
    assert "Operational Intelligence Summary" not in full
    assert "Photo Observations" not in full
    assert "University High Parent Loop Ext" in full
    assert "AAA Striping" in full
    assert "District Inspector" in full
    assert "Excavator" in full and "Water Truck" in full
    assert "Continue base installation northbound" in full
    assert "Approve lane closure extension and verify trucking window" in full
    assert "Maria Superintendent" in full
    assert "2026-07-11T19:00:00Z" in full
    assert "manual" in full.lower() or "supervisor accepted" in full.lower()
    assert "29.42410, -98.49360" in full
    assert full.count("Light rain") >= 1
    assert full.count("WEATHER") >= 1
    assert "Vault Assemblies" in full
    assert "Hours Delayed: 1.5 h" in full
    assert "Extra Work Hours: 2 h" in full
    assert "Page 1 of" in full or "PAGE 1 OF" in full


def test_golden_pdf_has_no_blank_or_footer_only_pages(tmp_path: Path):
    reader, _ = _reader(tmp_path)
    pages = [((page.extract_text() or "").strip()) for page in reader.pages]
    for idx, text in enumerate(pages, 1):
        assert text, f"page {idx} is blank"
        condensed = text.replace("MASCI · DAILY JOB", "").replace("REPORT", "").replace("Official Record", "")
        assert len(condensed.strip()) > 30, f"page {idx} is footer-only"


def test_golden_pdf_section_order_and_single_weather_block(tmp_path: Path):
    reader, _ = _reader(tmp_path)
    full = "\n".join((page.extract_text() or "") for page in reader.pages)
    order = [
        "01 · PROJECT INFORMATION",
        "03 · GENERAL INFORMATION",
        "04 · MASCI CREWS ON SITE",
        "05 · SUBCONTRACTORS",
        "06 · VISITORS",
        "07 · EQUIPMENT LOG",
        "09A · ACTIVITY PROGRESS",
        "09B · PRODUCTION QUANTITIES",
        "10 · PHOTOS",
        "11 · SIGNATURE",
    ]
    last = -1
    for marker in order:
        idx = full.find(marker)
        assert idx != -1, f"missing section {marker}"
        assert idx > last, f"section order broke at {marker}"
        last = idx
    assert full.count("COORDINATES USED 29.42410, -98.49360") == 1


def test_golden_pdf_equipment_and_signature_parity(tmp_path: Path):
    reader, _ = _reader(tmp_path)
    full = "\n".join((page.extract_text() or "") for page in reader.pages)

    assert "Excavator" in full and "Water Truck" in full
    assert "RUN HOURS" in full and "IDLE HOURS" in full
    assert "EXECUTIVE SUMMARY APPROVED" in full
    assert "EXECUTIVE SUMMARY ACCEPTED" in full
    assert "EXECUTIVE SUMMARY SOURCE" in full
    assert full.count("11 · SIGNATURE") == 1
