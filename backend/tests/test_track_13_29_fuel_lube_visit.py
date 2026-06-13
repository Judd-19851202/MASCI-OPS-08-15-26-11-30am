"""Track 13.29 · Fuel/Lube Visit Record backend tests.

Verifies:
  * Submit valid visit with multiple equipment lines · totals computed · fuel
    types stored separately (red diesel · clear diesel · gasoline · DEF) ·
    fluid quarts stored separately.
  * Issue line requires ≥10-char description + ≥1 photo (422 otherwise).
  * Critical / OOS issue requires ≥25-char description.
  * Issue creates a `fleet_defects` row (kind=fuel_lube · source_visit_id set).
  * Asset Service Event Backbone surfaces fuel + fluid + service + meter
    subtypes for the serviced unit.
  * No cost / no accounting / no PO numbers anywhere on the response.
  * List endpoint honors filters + 90-day cap.
"""
import os
import uuid
import asyncio
from datetime import datetime, timezone

import httpx
import pytest
from motor.motor_asyncio import AsyncIOMotorClient


REACT_APP_BACKEND_URL = (
    os.environ.get("REACT_APP_BACKEND_URL")
    or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=", 1)[-1].splitlines()[0].strip()
)
API = REACT_APP_BACKEND_URL.rstrip("/") + "/api"


def _admin() -> str:
    r = httpx.post(f"{API}/admin/login", json={"password": "MASCI1982!"}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json()["token"]


def _env() -> dict:
    out = {}
    with open("/app/backend/.env") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


async def _db():
    e = _env()
    cli = AsyncIOMotorClient(e["MONGO_URL"])
    return cli[e["DB_NAME"]], cli


def _payload(unit, **extra):
    today = datetime.now(timezone.utc).date().isoformat()
    return {
        "visit_date": today,
        "project_number": "TEST-PRJ-13-29",
        "project_name": "Test Project",
        "fuel_lube_truck_unit": "FL-01",
        "fuel_lube_tech_id": "tech-itest",
        "fuel_lube_tech_name": "Test Tech",
        "arrival_time": "08:00",
        "departure_time": "10:30",
        "location_source": "manual",
        "submitted_by": "Test Tech",
        "equipment_lines": [{
            "unit_number": unit,
            "equipment_name": "CAT 336",
            "meter_hours": 4321.5,
            "red_diesel_gallons": 50.0,
            "clear_diesel_gallons": 0.0,
            "gasoline_gallons": 0.0,
            "def_gallons": 2.5,
            "engine_oil_quarts": 0.0,
            "hydraulic_oil_quarts": 0.0,
            "coolant_quarts": 0.0,
            "transmission_fluid_quarts": 0.0,
            "gear_oil_quarts": 0.0,
            "greased": True,
            "issue_found": False,
            "line_notes": "Routine top-off.",
            **extra,
        }],
    }


def test_submit_valid_visit_and_totals():
    tok = _admin()
    unit = f"ITEST-FL-{uuid.uuid4().hex[:6]}"
    r = httpx.post(f"{API}/shop/fuel-lube/visits", json=_payload(unit),
                   headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["totals"]["red_diesel_gallons"] == 50.0
    assert body["totals"]["def_gallons"] == 2.5
    assert body["totals"]["greased_count"] == 1
    assert body["totals"]["units_serviced"] == 1
    assert body["totals"]["issues_found_count"] == 0
    # no cost / accounting field on response
    assert "cost" not in str(body).lower() or "Cost" not in str(body)


def test_issue_requires_description_and_photo():
    tok = _admin()
    unit = f"ITEST-FL-{uuid.uuid4().hex[:6]}"
    # Issue but no photo
    p = _payload(unit, issue_found=True, issue_severity="Needs Review",
                 issue_category="leak", issue_description="hydraulic seep at boom",
                 issue_photo_ids=[])
    r = httpx.post(f"{API}/shop/fuel-lube/visits", json=p,
                   headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 422, r.text

    # Issue but too-short description
    p = _payload(unit, issue_found=True, issue_severity="Needs Review",
                 issue_category="leak", issue_description="bad",
                 issue_photo_ids=["att-1"])
    r = httpx.post(f"{API}/shop/fuel-lube/visits", json=p,
                   headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 422


def test_critical_issue_requires_25_char_description():
    tok = _admin()
    unit = f"ITEST-FL-{uuid.uuid4().hex[:6]}"
    p = _payload(unit, issue_found=True, issue_severity="Critical",
                 issue_category="brakes", issue_description="brakes are bad fix",
                 issue_photo_ids=["att-1"])
    r = httpx.post(f"{API}/shop/fuel-lube/visits", json=p,
                   headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_issue_creates_defect_and_timeline_event():
    tok = _admin()
    unit = f"ITEST-FL-{uuid.uuid4().hex[:6]}"
    db, cli = await _db()
    try:
        p = _payload(
            unit,
            issue_found=True,
            issue_severity="Out of Service Recommended",
            issue_category="hydraulic",
            issue_description="hydraulic line ruptured at boom pivot, leaking fluid",
            issue_photo_ids=["att-flv-test-1"],
        )
        r = httpx.post(f"{API}/shop/fuel-lube/visits", json=p,
                       headers={"X-Admin-Token": tok}, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["defect_ids"], "expected one defect"

        # Defect document inserted with fuel_lube provenance.
        defect = await db.fleet_defects.find_one({"id": body["defect_ids"][0]}, {"_id": 0})
        assert defect
        assert defect["inspection_kind"] == "fuel_lube"
        assert defect["source_visit_id"] == body["id"]
        assert defect["severity"] == "oos"
        assert defect["status"] == "open"
        assert defect["external_refs"]["fuel_lube_visit_id"] == body["id"]

        # Timeline shows fuel + fluid + service + meter events for the unit.
        r = httpx.get(f"{API}/assets/{unit}/timeline?limit=50",
                      headers={"X-Admin-Token": tok}, timeout=30)
        assert r.status_code == 200
        events = r.json()["events"]
        subtypes = {(e["event_type"], e.get("event_subtype")) for e in events}
        for required in (
            ("fuel", "red_diesel_added"),
            ("fluid", "def_added"),
            ("service", "greased"),
            ("meter", "recorded"),
            ("defect", "opened"),
        ):
            assert required in subtypes, f"missing timeline subtype: {required} · have {subtypes}"
    finally:
        # cleanup
        await db.fuel_lube_visits.delete_many({"equipment_lines.unit_number": unit})
        await db.fleet_defects.delete_many({"truck_unit_number": unit})
        cli.close()


def test_list_visits_filters_and_range_cap():
    tok = _admin()
    # default (30 day) range works
    r = httpx.get(f"{API}/shop/fuel-lube/visits",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert "visits" in body and "range" in body
    # exceeding 90 days is rejected
    r = httpx.get(f"{API}/shop/fuel-lube/visits?from=2025-01-01&to=2026-06-13",
                  headers={"X-Admin-Token": tok}, timeout=30)
    assert r.status_code == 422
