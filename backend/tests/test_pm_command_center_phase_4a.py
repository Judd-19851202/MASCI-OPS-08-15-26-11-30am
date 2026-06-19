"""
tests/test_pm_command_center_phase_4a.py

FORGEDOPS PM Command Center · Phase 4A · contract tests.

Run with:
    cd /app/backend && python -m pytest tests/test_pm_command_center_phase_4a.py -v

Doctrine coverage (per Phase 4A authorization):
  1. Auth required (401 without admin/PM token)
  2. Admin token unlocks every endpoint (200)
  3. All 7 endpoints return the expected envelope
     (/overview, /resources, /hauls, /materials,
      /shop-impact, /safety-impact, /timeline)
  4. Road-plate legacy normalization (Steel Plate, Trench Plate, …
     → road_plate)
  5. Empty-scope PM (no assigned jobs) sees empty rows / zero counts
     instead of accidentally seeing all data
  6. Map-ready field set present on every operational row when data
     exists (asset_id/project_id/project_number/assignment_id/status/
     location_ref/timestamp/operational_state/trust_state/source_system)
  7. project_number filter respected (admin scoped to one project)
  8. FleetWatcher / MaintainX templates returned as `not_connected`
  9. No mutation on GET endpoints
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Dict

import httpx
import pytest

from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

# Local import for the pure-function normalizer (no network).
sys.path.insert(0, "/app/backend")
from routes.pm_command_center import (  # noqa: E402
    ROAD_PLATE_CANONICAL,
    ROAD_PLATE_LEGACY_VALUES,
    normalize_asset_kind,
    _map_ready,
)
from pm_auth import PmScope  # noqa: E402

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"
ADMIN_BREAK_GLASS_PW = "Maddix123!"

ENDPOINTS = [
    "/api/pm/command-center/overview",
    "/api/pm/command-center/resources",
    "/api/pm/command-center/hauls",
    "/api/pm/command-center/materials",
    "/api/pm/command-center/shop-impact",
    "/api/pm/command-center/safety-impact",
    "/api/pm/command-center/timeline",
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
        r = await c.post(
            f"{BASE}/api/admin/login",
            json={"password": ADMIN_BREAK_GLASS_PW},
        )
        r.raise_for_status()
        data = r.json()
        tok = data.get("token") or data.get("admin_token")
        assert tok, f"no admin token in response: {data}"
        return tok


# ─── 1 · Auth required on every GET ────────────────────────────────
@pytest.mark.parametrize("path", ENDPOINTS)
def test_endpoint_requires_auth(path):
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}{path}")
            assert r.status_code == 401, f"{path} → {r.status_code} {r.text}"
    _run(go())


# ─── 2 · Admin token unlocks every endpoint ────────────────────────
@pytest.mark.parametrize("path", ENDPOINTS)
def test_endpoint_admin_200(path):
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{BASE}{path}", headers={"X-Admin-Token": tok})
            assert r.status_code == 200, f"{path} → {r.status_code} {r.text}"
            j = r.json()
            assert j.get("ok") is True, f"{path} ok!=True: {j}"
            assert "as_of" in j, f"{path} missing as_of"
    _run(go())


# ─── 3 · /overview envelope ────────────────────────────────────────
def test_overview_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/pm/command-center/overview",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            j = r.json()
            assert "counts" in j
            assert "integration_readiness" in j
            ir = j["integration_readiness"]
            assert ir.get("fleetwatcher") == "not_connected"
            assert ir.get("maintainx") == "not_connected"
            counts = j["counts"]
            required = {
                "equipment_assigned", "trucks_assigned", "drivers_assigned",
                "trailers_assigned", "road_plates_assigned",
                "specialty_assets_assigned", "specialty_by_family",
                "active_assignments", "active_hauls", "loads_today",
                "defects_open", "incidents_open", "capas_open",
                "materials_in_today", "materials_out_today",
            }
            missing = required - set(counts.keys())
            assert not missing, f"overview counts missing keys: {missing}"
            for k, v in counts.items():
                # specialty_by_family is a nested dict; every other count is int.
                if k == "specialty_by_family":
                    assert isinstance(v, dict), f"counts.{k} not dict: {v!r}"
                    continue
                assert isinstance(v, int), f"counts.{k} not int: {v!r}"
    _run(go())


# ─── 4 · Road-plate legacy normalization (pure-function) ───────────
def test_road_plate_normalization_canonical():
    assert normalize_asset_kind("road_plate") == ROAD_PLATE_CANONICAL


@pytest.mark.parametrize("legacy", sorted(ROAD_PLATE_LEGACY_VALUES))
def test_road_plate_normalization_legacy(legacy):
    assert normalize_asset_kind(legacy) == ROAD_PLATE_CANONICAL
    # Case-insensitive
    assert normalize_asset_kind(legacy.upper()) == ROAD_PLATE_CANONICAL
    assert normalize_asset_kind(legacy.title()) == ROAD_PLATE_CANONICAL
    # Whitespace tolerant
    assert normalize_asset_kind(f"  {legacy}  ") == ROAD_PLATE_CANONICAL


def test_road_plate_normalization_misc():
    assert normalize_asset_kind(None) is None
    assert normalize_asset_kind("") is None
    assert normalize_asset_kind("Truck") == "truck"
    assert normalize_asset_kind("trailer") == "trailer"
    assert normalize_asset_kind("Backhoe") == "backhoe"  # untouched


# ─── 5 · Map-ready helper produces the canonical field set ─────────
def test_map_ready_field_set():
    mr = _map_ready(asset_id="EQ-1", project_number="9999",
                    status="in_motion", trust_state="active_haul")
    assert set(mr.keys()) == MAP_READY_KEYS, (
        f"map_ready keys drift: {set(mr.keys())} vs {MAP_READY_KEYS}")
    assert mr["asset_id"] == "EQ-1"
    assert mr["project_number"] == "9999"
    assert mr["source_system"] == "forgedops"  # default


# ─── 6 · Empty-scope PM (no jobs) → empty rows, not all-data ───────
def test_empty_scope_pm_returns_empty():
    """PmScope with no project_numbers must not leak to all rows.
    We verify by constructing the scope object and calling the
    filter helpers directly — protects against future regressions
    where someone removes the empty-scope guard."""
    scope = PmScope(is_admin=False, project_numbers=set())
    filt = scope.filter({"foo": "bar"})
    # Empty-scope filter must contain the impossible-match sentinel
    assert filt.get("__pm_empty_scope__") is True
    # allows() must be False for any project number
    assert scope.allows("9999") is False
    assert scope.allows(None) is False


def test_scoped_pm_filter_contains_in_clause():
    scope = PmScope(is_admin=False, project_numbers={"9999", "1234"})
    filt = scope.filter()
    assert "project_number" in filt
    assert "$in" in filt["project_number"]
    assert set(filt["project_number"]["$in"]) == {"9999", "1234"}
    assert scope.allows("9999") is True
    assert scope.allows("0000") is False


def test_admin_scope_no_filter():
    scope = PmScope(is_admin=True)
    filt = scope.filter({"existing": 1})
    assert filt == {"existing": 1}
    assert scope.allows("anything") is True


# ─── 7 · project_number filter respected on /overview ──────────────
def test_overview_project_filter_respected():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            # Use an obviously non-existent project number — counts
            # MUST all be 0 because the filter narrows scope.
            r = await c.get(
                f"{BASE}/api/pm/command-center/overview",
                params={"project_number": "ZZ-NONEXISTENT-99999"},
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200, r.text
            j = r.json()
            assert j.get("project_number_filter") == "ZZ-NONEXISTENT-99999"
            counts = j["counts"]
            # Every count should be 0 since no records match.
            # specialty_by_family is a dict of family→0 — flatten to scalars
            # for the zero-check.
            flat: Dict[str, int] = {}
            for k, v in counts.items():
                if isinstance(v, dict):
                    flat.update({f"{k}.{kk}": vv for kk, vv in v.items()})
                else:
                    flat[k] = v
            non_zero = {k: v for k, v in flat.items() if v != 0}
            assert not non_zero, f"non-zero counts on unknown project: {non_zero}"
    _run(go())


# ─── 8 · Map-ready fields on operational rows (when present) ───────
def test_resources_rows_map_ready_when_present():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(
                f"{BASE}/api/pm/command-center/resources",
                headers={"X-Admin-Token": tok},
                params={"limit": 50},
            )
            assert r.status_code == 200
            j = r.json()
            rows = j.get("rows") or []
            if not rows:
                pytest.skip("no resource rows in preview db — skip map-ready row shape check")
            sample = rows[0]
            missing = MAP_READY_KEYS - set(sample.keys())
            assert not missing, f"resources row missing map-ready keys: {missing}"
            # Integration templates always present
            assert sample.get("fleetwatcher", {}).get("status") == "not_connected"
            assert sample.get("maintainx", {}).get("status") == "not_connected"
    _run(go())


def test_hauls_rows_map_ready_when_present():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(
                f"{BASE}/api/pm/command-center/hauls",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            j = r.json()
            rows = j.get("rows") or []
            if not rows:
                pytest.skip("no haul rows in preview db")
            sample = rows[0]
            missing = MAP_READY_KEYS - set(sample.keys())
            assert not missing, f"hauls row missing map-ready keys: {missing}"
            assert sample.get("fleetwatcher", {}).get("status") == "not_connected"
    _run(go())


# ─── 9 · /materials and /shop-impact / /safety-impact / /timeline ──
def test_materials_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/pm/command-center/materials",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            j = r.json()
            assert "rows" in j and isinstance(j["rows"], list)
            assert "totals" in j
            assert set(j["totals"].keys()) >= {"deliveries", "removals", "hauls"}
    _run(go())


def test_shop_impact_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/pm/command-center/shop-impact",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            j = r.json()
            assert "rows" in j and "counts" in j
            assert set(j["counts"].keys()) >= {"oos", "open_defects", "maintenance_holds"}
    _run(go())


def test_safety_impact_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/pm/command-center/safety-impact",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            j = r.json()
            assert "incidents" in j and isinstance(j["incidents"], list)
            assert "capas" in j and isinstance(j["capas"], list)
            assert "counts" in j
    _run(go())


def test_timeline_envelope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(
                f"{BASE}/api/pm/command-center/timeline",
                headers={"X-Admin-Token": tok},
            )
            assert r.status_code == 200
            j = r.json()
            assert "events" in j and isinstance(j["events"], list)
            # Each event (when present) carries the map-ready field set.
            if j["events"]:
                ev = j["events"][0]
                missing = MAP_READY_KEYS - set(ev.keys())
                assert not missing, f"timeline event missing map-ready keys: {missing}"
                assert "kind" in ev and "timestamp" in ev
    _run(go())


# ─── 10 · No mutation on GET — sanity hit twice ────────────────────
def test_overview_no_mutation_repeat():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=30) as c:
            r1 = await c.get(f"{BASE}/api/pm/command-center/overview",
                              headers={"X-Admin-Token": tok})
            r2 = await c.get(f"{BASE}/api/pm/command-center/overview",
                              headers={"X-Admin-Token": tok})
            assert r1.status_code == 200 and r2.status_code == 200
            # counts stable between two reads
            assert r1.json()["counts"] == r2.json()["counts"]
    _run(go())
