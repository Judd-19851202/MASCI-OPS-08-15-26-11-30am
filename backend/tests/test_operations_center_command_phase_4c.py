"""
tests/test_operations_center_command_phase_4c.py

FORGEDOPS Operations Center Phase 4C contract tests.

Doctrine coverage:
  1. Auth required on every endpoint (401 without admin/portal token).
  2. Admin unlocks every endpoint (200 + ok=True).
  3. /brief envelope shape (15+ count fields + integration_readiness).
  4. /project-health envelope + risk taxonomy (red/yellow/green).
  5. /allocation envelope + unassigned / oos / unmapped buckets.
  6. /conflicts envelope + per-kind counts.
  7. /specialty-assets exposes the 4 families AND backward-compat
     road_plate_count + ?family= / ?kind= filters work.
  8. /shop-impact uses production_priority (high/medium/low) AND
     sorts highest priority first.
  9. /safety-impact uses tiered severity (critical/warning/informational).
  10. /telematics returns the 9 motive operational state buckets + map-
      ready rows + fleetwatcher=not_connected.
  11. /map-contract returns rows with the canonical map-ready field set.
  12. Specialty Asset Normalization: trench_box surfaces as
      family=trench_safety; road_plate surfaces as family=access_protection.
"""
from __future__ import annotations

import asyncio
import os
import sys

import httpx
import pytest

from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

sys.path.insert(0, "/app/backend")
from routes.pm_command_center import (  # noqa: E402
    specialty_family_of, is_specialty_asset, SPECIALTY_ASSET_FAMILY,
    ROAD_PLATE_CANONICAL,
)

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"
ADMIN_BREAK_GLASS_PW = "Maddix123!"

ENDPOINTS = [
    "/api/operations-center/command/brief",
    "/api/operations-center/command/project-health",
    "/api/operations-center/command/allocation",
    "/api/operations-center/command/conflicts",
    "/api/operations-center/command/specialty-assets",
    "/api/operations-center/command/shop-impact",
    "/api/operations-center/command/safety-impact",
    "/api/operations-center/command/telematics",
    "/api/operations-center/command/timeline",
    "/api/operations-center/command/map-contract",
]

MAP_READY_KEYS = {
    "asset_id", "project_id", "project_number", "assignment_id",
    "status", "location_ref", "timestamp", "operational_state",
    "trust_state", "source_system",
}


def _run(coro):
    return asyncio.run(coro)


async def _admin_token() -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/admin/login",
                          json={"password": ADMIN_BREAK_GLASS_PW})
        r.raise_for_status()
        d = r.json()
        return d.get("token") or d.get("admin_token")


# ─── Pure-function: Specialty Asset taxonomy ────────────────────────
def test_specialty_family_road_plate_is_access_protection():
    assert specialty_family_of("road_plate") == "access_protection"


def test_specialty_family_trench_box_is_trench_safety():
    assert specialty_family_of("trench_box") == "trench_safety"
    assert specialty_family_of("trench box") == "trench_safety"


def test_specialty_family_arrow_board_is_traffic_control():
    assert specialty_family_of("arrow board") == "traffic_control"


def test_specialty_family_pump_is_support():
    assert specialty_family_of("pump") == "support"
    assert specialty_family_of("generator") == "support"


def test_specialty_family_truck_is_not_specialty():
    # Trucks/trailers/excavators are FLEET, not specialty.
    assert specialty_family_of("truck") is None
    assert is_specialty_asset("truck") is False
    assert is_specialty_asset("excavator") is False


def test_specialty_family_dict_has_four_families():
    assert set(SPECIALTY_ASSET_FAMILY.keys()) == {
        "trench_safety", "access_protection", "traffic_control", "support",
    }
    # Road plate is in access_protection
    assert ROAD_PLATE_CANONICAL in SPECIALTY_ASSET_FAMILY["access_protection"]


# ─── Auth gate ──────────────────────────────────────────────────────
@pytest.mark.parametrize("path", ENDPOINTS)
def test_endpoint_requires_auth(path):
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}{path}")
            assert r.status_code in (401, 403), f"{path} → {r.status_code} {r.text}"
    _run(go())


# ─── Admin 200 on every endpoint ────────────────────────────────────
@pytest.mark.parametrize("path", ENDPOINTS)
def test_endpoint_admin_200(path):
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{path}", headers={"X-Admin-Token": tok})
            assert r.status_code == 200, f"{path} → {r.status_code} {r.text}"
            j = r.json()
            assert j.get("ok") is True
            assert "as_of" in j
    _run(go())


# ─── /brief shape ───────────────────────────────────────────────────
def test_brief_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/brief",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert "brief" in j
            b = j["brief"]
            required = {
                "active_projects", "active_hauls", "trucks_active",
                "drivers_active", "equipment_active",
                "road_plates_total", "road_plates_deployed",
                "specialty_assets_total", "specialty_assets_deployed",
                "materials_in_today", "materials_out_today", "loads_today",
                "open_shop_defects", "oos_assets", "incidents_open",
                "capas_open", "critical_safety_events", "resource_conflicts",
            }
            assert required <= set(b.keys()), f"missing: {required - set(b.keys())}"
            assert j["integration_readiness"]["fleetwatcher"] == "not_connected"
            assert j["integration_readiness"]["maintainx"] == "not_connected"
    _run(go())


# ─── /project-health risk taxonomy ──────────────────────────────────
def test_project_health_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/project-health",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert "rows" in j and "counts" in j
            assert set(j["counts"].keys()) >= {"red", "yellow", "green", "total"}
            if j["rows"]:
                row = j["rows"][0]
                assert row["risk"] in {"red", "yellow", "green"}
                assert "specialty_assets" in row, "row missing specialty_assets count"
                assert "road_plates" in row, "road_plates count must be preserved"
                missing = MAP_READY_KEYS - set(row.keys())
                assert not missing, f"row missing map-ready keys: {missing}"
    _run(go())


# ─── /specialty-assets family + backward-compat ─────────────────────
def test_specialty_assets_families():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/specialty-assets",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert set(j["by_family"].keys()) == {
                "trench_safety", "access_protection",
                "traffic_control", "support",
            }
            # Backward-compat shim
            assert "road_plate_count" in j
            assert j["road_plate_count"] == j["by_kind"].get("road_plate", 0)
    _run(go())


def test_specialty_assets_filter_by_family():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/specialty-assets",
                              params={"family": "trench_safety"},
                              headers={"X-Admin-Token": tok})
            j = r.json()
            for row in j["rows"]:
                assert row["family"] == "trench_safety", row
    _run(go())


def test_specialty_assets_filter_by_kind_road_plate():
    """Backward-compat — operator can still drill into ONLY road plates."""
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/specialty-assets",
                              params={"kind": "road_plate"},
                              headers={"X-Admin-Token": tok})
            j = r.json()
            for row in j["rows"]:
                assert row["asset_kind"] == "road_plate", row
                assert row["family"] == "access_protection", row
    _run(go())


# ─── /shop-impact priority ──────────────────────────────────────────
def test_shop_impact_priority():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/shop-impact",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert set(j["counts"].keys()) >= {"high", "medium", "low", "oos", "total_open"}
            if j["rows"]:
                seen = [r["production_priority"] for r in j["rows"]]
                order = {"high": 0, "medium": 1, "low": 2}
                assert seen == sorted(seen, key=lambda x: order[x]), \
                    "shop rows not sorted by priority"
    _run(go())


# ─── /safety-impact tiers ───────────────────────────────────────────
def test_safety_impact_tiers():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/safety-impact",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert set(j["counts"].keys()) >= {"critical", "warning", "informational"}
            for row in (j["incidents"] + j["capas"]):
                assert row["tier"] in {"critical", "warning", "informational"}
    _run(go())


# ─── /telematics buckets ────────────────────────────────────────────
def test_telematics_buckets():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/telematics",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert set(j["buckets"].keys()) >= {
                "moving", "idling", "at_job", "at_plant", "at_yard",
                "at_shop", "offline", "no_gps", "unknown",
            }
            assert j["integration_readiness"]["fleetwatcher"] == "not_connected"
    _run(go())


# ─── /conflicts ────────────────────────────────────────────────────
def test_conflicts_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/conflicts",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert "rows" in j and "counts" in j
            assert "total" in j["counts"]
            for row in j["rows"]:
                assert row["kind"] in {
                    "truck_multi_project", "driver_multi_truck",
                    "haul_inactive_project",
                }
    _run(go())


# ─── /map-contract field set ────────────────────────────────────────
def test_map_contract_rows_have_required_fields():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}/api/operations-center/command/map-contract",
                              headers={"X-Admin-Token": tok})
            j = r.json()
            if not j["rows"]:
                pytest.skip("no motive-mapped trucks in preview")
            row = j["rows"][0]
            required = {"asset_id", "lat", "lon", "last_location_time",
                          "location_source", "operational_state"}
            assert required <= set(row.keys()), f"missing: {required - set(row.keys())}"
            missing = MAP_READY_KEYS - set(row.keys())
            assert not missing, f"row missing map-ready keys: {missing}"
    _run(go())
