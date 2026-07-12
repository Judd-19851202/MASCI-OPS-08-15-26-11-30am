"""TRACK 26.02 · Daily Report P0/P1 recovery — regression locks.

Verifies that:

* Production rows accept vernacular unit labels ("Tons", "Cubic Yards",
  "Loads", "cubes") as well as canonical codes ("TON", "LF").
* Extra UI-side fields (`unit_snapshot`, `unit_code`, `percent_complete`)
  no longer cause a 422.
* Constraint categories accept any case ("WEATHER", "Weather", "weather")
  and bucket unknowns to "other" with the original word preserved in
  notes.
* Weather sampling picks the max-severity WMO code across 24 hours
  (frontend-level, exercised in the jsdom-free contract test below).

These tests exercise the running preview backend at the URL configured
in ``frontend/.env`` (REACT_APP_BACKEND_URL). If the backend is not
reachable the tests skip — this is a live-integration lock, not a
unit test.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import requests


def _api_url() -> str:
    """Read REACT_APP_BACKEND_URL from frontend/.env (single source of truth)."""
    env_path = Path("/app/frontend/.env")
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not set")


API_URL = _api_url()
POST_URL = f"{API_URL}/api/daily-reports"


def _payload(**overrides):
    base = {
        "project_name": "T2602-CERT",
        "location": "X",
        "report_date": "2026-02-07",
        "prepared_by": "Cert",
        "ai_accepted_summary": "Approved summary: regression payload accepted for daily report certification.",
        "ai_accepted_summary_meta": {
            "source": "manual",
            "approved_by": "Cert",
            "accepted_at": "2026-02-07T19:00:00Z",
        },
        "photos": [],
    }
    base.update(overrides)
    return base


def _post(payload):
    try:
        return requests.post(POST_URL, json=payload, timeout=15)
    except requests.RequestException as e:  # pragma: no cover
        pytest.skip(f"Backend not reachable: {e}")


# ── D-01 · unit widened to str ─────────────────────────────────────

@pytest.mark.parametrize(
    "label",
    ["Tons", "Cubic Yards", "Loads", "Truckloads", "Gallons",
     "LF", "TON", "CY", "SY", "EA", "ACRE", "cubes", "OTHER"],
)
def test_production_row_accepts_common_unit_labels(label):
    r = _post(_payload(production=[
        {"description": "asphalt", "quantity": 10, "unit": label}
    ]))
    assert r.status_code == 200, (
        f"TRACK 26.02 · unit={label!r} should be accepted but got "
        f"HTTP {r.status_code}: {r.text[:400]}"
    )


# ── D-03 · extra="ignore" on ProductionRow ─────────────────────────

def test_production_row_ignores_ui_helper_fields():
    r = _post(_payload(production=[{
        "description": "asphalt", "quantity": 10, "unit": "TON",
        "unit_snapshot": "Tons", "unit_code": "TON",
        "percent_complete": 50, "activity_code": "P-001",
        "cost_code_snapshot": "01-100-000",
    }]))
    assert r.status_code == 200, (
        f"TRACK 26.02 · UI helper fields must not 422 the payload. "
        f"Got {r.status_code}: {r.text[:400]}"
    )


# ── D-10 · constraint_type case-insensitive + free-text bucketed ───

@pytest.mark.parametrize(
    "value",
    ["WEATHER", "Weather", "weather", "utility", "Owner_Engineer",
     "BAD_WEATHER", "custom_thing", ""],
)
def test_constraint_type_accepts_any_case_and_unknown(value):
    r = _post(_payload(constraints=[{"constraint_type": value}]))
    assert r.status_code == 200, (
        f"TRACK 26.02 · constraint_type={value!r} should be accepted "
        f"but got HTTP {r.status_code}: {r.text[:400]}"
    )


# ── D-03 · extra fields on ConstraintRow ──────────────────────────

def test_constraint_row_ignores_ui_helper_fields():
    r = _post(_payload(constraints=[{
        "constraint_type": "weather",
        "delay_reason": "morning shower",  # not a declared field
        "recorded_by": "supervisor",
    }]))
    assert r.status_code == 200, (
        f"TRACK 26.02 · constraint UI helper fields must not 422. "
        f"Got {r.status_code}: {r.text[:400]}"
    )


# ── D-01 · positive control: canonical codes still work ──────────

def test_canonical_unit_codes_still_accepted():
    for code in ("LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"):
        r = _post(_payload(production=[{
            "description": "row", "quantity": 1, "unit": code,
        }]))
        assert r.status_code == 200


# ── Photos-not-blocker positive control ──────────────────────────

def test_empty_photos_array_still_accepted():
    r = _post(_payload(photos=[], production=[
        {"description": "asphalt", "quantity": 10, "unit": "TON"}
    ]))
    assert r.status_code == 200, (
        "TRACK 26.02 · photos=[] must not block submit — proves "
        "'photos blocked submit' symptom is misattributed."
    )


# ── D-04 · frontend weather.js contract lock ─────────────────────

WEATHER_JS = Path("/app/frontend/src/lib/weather.js")


def test_weather_samples_include_overnight():
    """Overnight hours (00:00, 03:00) must be in the picks so
    overnight rain surfaces to the operator instead of being hidden."""
    src = WEATHER_JS.read_text(encoding="utf-8")
    assert '"00:00"' in src and '"03:00"' in src, (
        "TRACK 26.02 · D-04: weather.js must sample overnight hours "
        "(00:00 and 03:00) so overnight rain surfaces in snapshots."
    )


def test_weather_summary_uses_max_severity_not_middle_of_day():
    """The old code used ``conds[Math.floor(conds.length / 2)]`` — a
    middle-of-day pick. The fixed code iterates all 24 hourly codes
    and picks the max-severity code. Lock the specific text so a
    regression is obvious in review."""
    src = WEATHER_JS.read_text(encoding="utf-8")
    assert "Math.floor(conds.length / 2)" not in src, (
        "TRACK 26.02 · D-04: middle-of-day summary must be removed."
    )
    assert "WMO_SEVERITY" in src, (
        "TRACK 26.02 · D-04: max-severity table WMO_SEVERITY must be "
        "the source of the summary word."
    )
    assert "max_severity_code" in src and "total_precip_in" in src, (
        "TRACK 26.02 · D-04: summary envelope must include "
        "`max_severity_code` and `total_precip_in` so downstream "
        "consumers (AI, PDF, email) can trust the sampling."
    )
    assert "overridden" in src, (
        "TRACK 26.02 · D-04: `overridden` flag must be exposed so "
        "the AI evidence bundle can differentiate operator overrides."
    )
    assert "fetched_at_iso" in src, (
        "TRACK 26.02 · D-04: `fetched_at_iso` must be surfaced so "
        "the UI can render a stale-timestamp pill."
    )


# ── D-02 · UnitCombo posts canonical codes ───────────────────────

UNIT_COMBO_JS = Path("/app/frontend/src/components/daily-report-v3/UnitCombo.jsx")


def test_unit_combo_dropdown_codes_match_backend_literals():
    """Every canonical code the frontend dropdown offers MUST match
    a value the backend accepts. The backend canonical set is
    {LF, SY, CY, TON, EA, ACRE, OTHER}. Free-text still works
    (backend has `unit: str`), so this is a UX cleanliness lock."""
    src = UNIT_COMBO_JS.read_text(encoding="utf-8")
    # Extract the code strings from the DEFAULT_MATERIAL_UNITS block.
    import re
    codes = set(re.findall(r'code:\s*"([^"]+)"', src))
    assert codes, "UnitCombo has no codes declared"
    backend_canonical = {"LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"}
    orphans = codes - backend_canonical
    assert not orphans, (
        f"TRACK 26.02 · D-02: UnitCombo declares codes not in the "
        f"backend canonical set: {orphans}. Every dropdown code must "
        "resolve to a backend-accepted canonical code (or 'OTHER')."
    )


# ── D-09 · submit toast surfaces Pydantic detail ─────────────────

def test_submit_toast_surfaces_pydantic_detail():
    """The V3 submit handler must extract the first Pydantic error
    (loc + msg) and render it in the toast, not the generic fallback."""
    src = Path("/app/frontend/src/pages/NewDailyReportV3.jsx").read_text(encoding="utf-8")
    assert "Array.isArray(detail)" in src, (
        "TRACK 26.02 · D-09: submit handler must detect Pydantic's "
        "list-shaped detail and render the first field-level error."
    )
    assert "first?.msg" in src or 'first?.["msg"]' in src, (
        "TRACK 26.02 · D-09: toast must extract the Pydantic `msg` "
        "so the operator sees the real reason instead of 'Submit failed.'"
    )
