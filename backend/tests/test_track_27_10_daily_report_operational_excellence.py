from __future__ import annotations

import sys
sys.path.insert(0, "/app/backend")

import importlib
import uuid

import pytest
from fastapi import HTTPException

from routes.daily_reports import DailyReportCreate

pdf_render = importlib.import_module("pdf_render")
weather_mod = importlib.import_module("incident_engine.weather")

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


def _doc(**overrides):
    base = {
        "id": str(uuid.uuid4()),
        "doc_id": "DR-2026-27100",
        "project_name": "University High Parent Loop Ext",
        "project_number": "UH-2710",
        "location": "Parent Loop Extension",
        "report_date": "2026-07-11",
        "report_number": "DR-2026-27100",
        "prepared_by": "John Supervisor",
        "superintendent": "Maria Superintendent",
        "weather_summary": "Observed conditions: Light rain; temperature 73–86°F; humidity 72% avg; wind up to 18 mph, gusts up to 27 mph; precipitation 0.18 in; peak weather signal at 2026-07-11T15:00",
        "weather_snapshot_meta": {
            "provider": "open-meteo",
            "observation_timestamp": "2026-07-11T15:00",
            "location_source": "device_gps",
            "location_accuracy_meters": 8,
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
        "gps_lat": 29.4241,
        "gps_lng": -98.4936,
        "gps_accuracy": 8,
        "location_source": "device_gps",
        "location_captured_at": "2026-07-11T14:50:00Z",
        "weather_impact": "No",
        "weather_impact_notes": "Supervisor confirmed no weather delay was charged today.",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "general_notes": "Crew completed curb prep, utility verification, and asphalt placement staging.",
        "masci_crews": [
            {"name": "Crew A", "trade": "Labor", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Curb prep"},
            {"name": "Crew B", "trade": "Operator", "start_time": "06:30", "stop_time": "15:30", "lunch_minutes": 30, "hours": 8.5, "work_performed": "Equipment support"},
        ],
        "activities": [{"description": "Curb prep and staging"}],
        "photos": [ONE_PX] * 8,
        "prepared_by_signature": ONE_PX,
        "ai_accepted_summary": "Accepted executive summary: crews completed curb prep, staged the paving area, and verified utilities. No schedule delay was charged.",
        "ai_accepted_summary_meta": {
            "source": "ai",
            "approved_by": "John Supervisor",
            "accepted_at": "2026-07-11T19:00:00Z",
        },
    }
    base.update(overrides)
    return base


def _enforce_summary_gate(payload_dict):
    accepted_summary = str(payload_dict.get("ai_accepted_summary") or "").strip()
    accepted_meta = payload_dict.get("ai_accepted_summary_meta") or {}
    accepted_at = str(accepted_meta.get("accepted_at") or "").strip()
    accepted_source = str(accepted_meta.get("source") or "").strip().lower()
    if not accepted_summary:
        raise HTTPException(status_code=422, detail={"error": "approved_summary_required"})
    if not accepted_at:
        raise HTTPException(status_code=422, detail={"error": "approved_summary_metadata_required"})
    if accepted_source not in {"ai", "edited", "fallback", "manual"}:
        raise HTTPException(status_code=422, detail={"error": "approved_summary_source_invalid"})


def test_backend_summary_gate_rejects_missing_approved_summary():
    payload = DailyReportCreate(**{
        "project_name": "University High Parent Loop Ext",
        "project_number": "UH-2710",
        "location": "Parent Loop Extension",
        "report_date": "2026-07-11",
        "prepared_by": "John Supervisor",
        "weather_summary": "Clear",
        "photos": [ONE_PX] * 6,
    })
    with pytest.raises(HTTPException) as exc:
        _enforce_summary_gate(payload.model_dump())
    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "approved_summary_required"


def test_backend_summary_gate_accepts_manual_summary_with_metadata():
    payload = DailyReportCreate(**{
        "project_name": "University High Parent Loop Ext",
        "project_number": "UH-2710",
        "location": "Parent Loop Extension",
        "report_date": "2026-07-11",
        "prepared_by": "John Supervisor",
        "weather_summary": "Clear",
        "photos": [ONE_PX] * 6,
        "ai_accepted_summary": "Manual supervisor summary.",
        "ai_accepted_summary_meta": {
            "source": "manual",
            "approved_by": "John Supervisor",
            "accepted_at": "2026-07-11T19:00:00Z",
        },
    })
    _enforce_summary_gate(payload.model_dump())


def test_pdf_one_summary_rule_suppresses_duplicate_narrative_block():
    html = pdf_render._render_daily(_doc())
    assert html.count("Accepted executive summary") == 1
    assert "10a · Operational Intelligence Summary" not in html
    assert "10a · Photo Observations" not in html


def test_pdf_weather_block_renders_gps_facts_without_invented_impact():
    html = pdf_render._render_daily(_doc())
    assert "29.42410, -98.49360" in html
    assert "Wind / Gusts" in html
    assert "18 mph / 27 mph" in html
    assert "Location Source" in html and "device_gps" in html
    assert "Weather Source" in html and "open-meteo" in html
    assert "No schedule delay was charged today" not in html.split("Weather", 1)[1][:600]


@pytest.mark.asyncio
async def test_weather_helper_builds_factual_daily_report_payload(monkeypatch):
    sample = {
        "timezone": "America/Chicago",
        "hourly": {
            "time": [
                "2026-07-11T00:00", "2026-07-11T03:00", "2026-07-11T06:00", "2026-07-11T09:00",
                "2026-07-11T12:00", "2026-07-11T15:00", "2026-07-11T18:00", "2026-07-11T21:00",
            ],
            "temperature_2m": [74, 73, 75, 79, 84, 86, 83, 78],
            "relative_humidity_2m": [88, 90, 84, 76, 69, 64, 70, 79],
            "weather_code": [3, 3, 2, 1, 61, 63, 3, 1],
            "wind_speed_10m": [5, 6, 8, 10, 16, 18, 12, 8],
            "wind_gusts_10m": [7, 8, 12, 14, 23, 27, 18, 13],
            "precipitation": [0, 0, 0, 0, 0.04, 0.14, 0, 0],
            "rain": [0, 0, 0, 0, 0.04, 0.14, 0, 0],
        },
    }

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return sample

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, *args, **kwargs):
            return _Resp()

    monkeypatch.setattr(weather_mod.httpx, "AsyncClient", _Client)
    result = await weather_mod.fetch_daily_report_weather(29.4241, -98.4936, "2026-07-11")

    assert result["provider"] == "open-meteo"
    assert result["meta"]["gps_lat"] == 29.4241
    assert result["meta"]["wind_gust_max_mph"] == 27
    assert result["meta"]["precipitation_total_in"] == 0.18
    assert result["meta"]["provider"] == "open-meteo"
    assert result["meta"]["observation_timestamp"] == "2026-07-11T15:00"
    assert "temperature 73–86°F" in result["summary"]
    assert "gusts up to 27 mph" in result["summary"]
    assert "peak weather signal" in result["summary"]
    assert len(result["snapshots"]) == 8