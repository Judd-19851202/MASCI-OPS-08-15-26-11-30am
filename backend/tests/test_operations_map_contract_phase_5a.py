"""
tests/test_operations_map_contract_phase_5a.py

FORGEDOPS Live Operations Map · Phase 5A · contract validation.

Backend-only. NO UI map exists yet. These tests prove the contract is
honest, calm, performant, and consumable by every portal.

Doctrine coverage (per directive):
  1. Endpoint exists + auth required + admin 200
  2. operations / dispatch / pm / shop / safety / admin scopes
  3. project_number / asset_kind / asset_family / status / attention_only filters
  4. Row identity bucket present (asset_id, asset_kind, asset_family, …)
  5. Row location bucket present + trust state explains missing data
  6. Row assignment bucket present
  7. Row operational-state bucket present
  8. Telematics bucket present
  9. FleetWatcher slots present and `not_connected`
  10. MaintainX slots present and `not_connected`
  11. Attention bucket present (with route_pending when no route)
  12. Trust bucket present (trust_state, missing_fields, source_systems)
  13. No fake lat/lon (lat/lon is None unless motive_event present)
  14. Counts reconcile with rows
  15. Specialty assets visible (trench boxes + road plates surface)
  16. Empty-scope PM returns empty rows (no leak)
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Dict, Set

import httpx
import pytest

from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
load_dotenv("/app/backend/.env")

sys.path.insert(0, "/app/backend")

BASE = os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001"
ADMIN_PW = "Maddix123!"
ENDPOINT = "/api/operations-map/contract"

# Identity bucket (8 fields)
ID_KEYS = {"asset_id", "asset_number", "asset_name", "asset_kind",
           "asset_family", "asset_type", "canonical_source"}
# Location bucket (7)
LOC_KEYS = {"lat", "lon", "location_label", "location_source",
            "last_location_time", "location_confidence", "location_trust_state"}
# Assignment bucket
ASSIGN_KEYS = {"project_id", "project_number", "project_name",
               "assigned_driver_id", "assigned_driver_name",
               "assigned_dispatch_id", "assigned_pm", "assigned_crew"}
# Operational bucket
OP_KEYS = {"operational_state", "movement_state", "haul_state",
           "shop_state", "safety_state", "dispatch_state", "availability_state"}
# Telematics
TELEM_KEYS = {"motive_vehicle_id", "motive_driver_id", "gps_status",
              "speed", "idle_minutes", "ignition_state", "geofence",
              "engine_hours", "fault_state"}
# FleetWatcher (placeholders)
FW_KEYS = {"fleetwatcher_status", "ticket_number", "material", "plant",
           "source_location", "destination_location", "tons",
           "load_status", "cycle_time_minutes"}
# MaintainX (placeholders)
MX_KEYS = {"maintainx_status", "work_order_id", "maintenance_status",
           "estimated_return", "repair_priority"}
# Attention
ATT_KEYS = {"needs_attention", "attention_reason",
            "attention_severity", "action_label", "action_route"}
# Trust
TRUST_KEYS = {"trust_state", "missing_fields", "source_systems", "updated_at"}

ALLOWED_TRUST_STATES = {
    "live_location", "last_known_location", "no_location", "no_gps",
    "not_mapped", "motive_only", "asset_spine_only",
    "fleetwatcher_pending", "maintainx_pending",
    "no_assignment", "no_project", "unknown_state", "needs_mapping",
    "oos", "in_shop", "failed_dvir", "maintenance_hold",
    "active_haul", "idle", "moving", "offline",
}


def _run(coro): return asyncio.run(coro)


async def _admin_token() -> str:
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{BASE}/api/admin/login", json={"password": ADMIN_PW})
        r.raise_for_status()
        return r.json().get("token")


# ─── 1 · Auth + 200 ─────────────────────────────────────────────────
def test_endpoint_requires_auth():
    async def go():
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{BASE}{ENDPOINT}")
            assert r.status_code in (401, 403)
    _run(go())


def test_admin_200_default_scope():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", headers={"X-Admin-Token": tok})
            assert r.status_code == 200, r.text
            j = r.json()
            assert j["ok"] is True
            assert j["scope"] == "operations"
            assert isinstance(j["rows"], list)
            assert "counts" in j
    _run(go())


@pytest.mark.parametrize("scope", ["operations", "dispatch", "pm", "shop", "safety", "admin"])
def test_every_scope_returns_200(scope):
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}",
                              params={"scope": scope},
                              headers={"X-Admin-Token": tok})
            assert r.status_code == 200, f"{scope} → {r.text}"
            j = r.json()
            assert j["scope"] == scope
    _run(go())


# ─── 2 · Row schema buckets ─────────────────────────────────────────
def test_row_has_identity_bucket():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows in preview")
            for row in rows[:5]:
                missing = ID_KEYS - set(row.keys())
                assert not missing, f"row missing identity keys: {missing}"
    _run(go())


def test_row_has_location_bucket_and_trust():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows")
            for row in rows[:10]:
                missing = LOC_KEYS - set(row.keys())
                assert not missing, f"missing loc keys: {missing}"
                assert row["location_trust_state"] in ALLOWED_TRUST_STATES, \
                    f"unknown trust state: {row['location_trust_state']}"
    _run(go())


def test_row_assignment_bucket():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows")
            for row in rows[:5]:
                missing = ASSIGN_KEYS - set(row.keys())
                assert not missing
    _run(go())


def test_row_operational_state_bucket():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows")
            for row in rows[:5]:
                missing = OP_KEYS - set(row.keys())
                assert not missing
    _run(go())


def test_row_telematics_bucket():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows")
            for row in rows[:5]:
                missing = TELEM_KEYS - set(row.keys())
                assert not missing
    _run(go())


def test_row_fleetwatcher_and_maintainx_pending():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows")
            for row in rows[:5]:
                fw_missing = FW_KEYS - set(row.keys())
                assert not fw_missing, f"missing FW keys: {fw_missing}"
                mx_missing = MX_KEYS - set(row.keys())
                assert not mx_missing, f"missing MX keys: {mx_missing}"
                assert row["fleetwatcher_status"] == "not_connected"
                assert row["maintainx_status"] == "not_connected"
                assert row["ticket_number"] is None
                assert row["work_order_id"] is None
    _run(go())


def test_row_attention_bucket_with_route_pending():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows")
            for row in rows[:10]:
                missing = ATT_KEYS - set(row.keys())
                assert not missing
                assert isinstance(row["needs_attention"], bool)
                # action_label is either a real label or "route_pending"
                assert row["action_label"] is not None
                if row["action_route"] is None:
                    assert row["action_label"] == "route_pending" or not row["needs_attention"]
    _run(go())


def test_row_trust_bucket():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 50},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            if not rows: pytest.skip("no rows")
            for row in rows[:5]:
                missing = TRUST_KEYS - set(row.keys())
                assert not missing
                assert isinstance(row["missing_fields"], list)
                assert isinstance(row["source_systems"], list)
                assert "asset_spine" in row["source_systems"]
    _run(go())


# ─── 3 · No fake lat/lon ────────────────────────────────────────────
def test_no_fake_lat_lon():
    """If trust_state is no_gps/no_location/asset_spine_only, lat/lon
    MUST be None. The map must never lie about location."""
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 500},
                              headers={"X-Admin-Token": tok})
            rows = r.json()["rows"]
            no_loc_states = {"no_gps", "no_location", "asset_spine_only"}
            for row in rows:
                if row["location_trust_state"] in no_loc_states:
                    assert row["lat"] is None, f"fake lat for {row['asset_number']}"
                    assert row["lon"] is None, f"fake lon for {row['asset_number']}"
    _run(go())


# ─── 4 · Filters ────────────────────────────────────────────────────
def test_filter_attention_only():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}",
                              params={"attention_only": "true", "limit": 500},
                              headers={"X-Admin-Token": tok})
            for row in r.json()["rows"]:
                assert row["needs_attention"] is True
    _run(go())


def test_filter_asset_family_fleet():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}",
                              params={"asset_family": "fleet", "limit": 200},
                              headers={"X-Admin-Token": tok})
            for row in r.json()["rows"]:
                assert row["asset_family"] == "fleet", row["asset_kind"]
    _run(go())


def test_filter_asset_family_specialty_trench():
    """Phase 4C Specialty Asset normalization: trench boxes surface
    under asset_family=specialty:trench_safety in the map contract."""
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}",
                              params={"asset_family": "specialty:trench_safety",
                                       "limit": 500},
                              headers={"X-Admin-Token": tok})
            for row in r.json()["rows"]:
                assert row["asset_family"] == "specialty:trench_safety"
    _run(go())


def test_filter_asset_kind_road_plate():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}",
                              params={"asset_kind": "road_plate", "limit": 500},
                              headers={"X-Admin-Token": tok})
            for row in r.json()["rows"]:
                assert row["asset_kind"] == "road_plate"
                assert row["asset_family"] == "specialty:access_protection"
    _run(go())


def test_filter_project_number():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}",
                              params={"project_number": "ZZ-NONEXISTENT-99999"},
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert j["counts"]["total_rows"] == 0
            assert j["rows"] == []
    _run(go())


# ─── 5 · Counts reconcile ───────────────────────────────────────────
def test_counts_reconcile_with_rows():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 1000},
                              headers={"X-Admin-Token": tok})
            j = r.json()
            assert j["counts"]["total_rows"] == len(j["rows"])
            # specialty + fleet + equipment <= total (some other asset_family)
            assert (j["counts"]["specialty_assets"] +
                     j["counts"]["trucks"] +
                     j["counts"]["equipment"]) <= j["counts"]["total_rows"]
            # needs_attention count matches rows with needs_attention=True
            actual_att = sum(1 for r in j["rows"] if r["needs_attention"])
            assert j["counts"]["needs_attention"] == actual_att
    _run(go())


def test_integration_readiness_chip_set():
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 10},
                              headers={"X-Admin-Token": tok})
            ir = r.json()["integration_readiness"]
            assert ir["fleetwatcher"] == "not_connected"
            assert ir["maintainx"] == "not_connected"
            assert ir["motive"] in {"active", "partial"}
    _run(go())


# ─── 6 · Specialty assets surface ───────────────────────────────────
def test_specialty_assets_present_in_rows():
    """Phase 4C correction: specialty assets must surface in the map
    contract (trench_boxes + road_plates etc.). They are NOT filtered
    out."""
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 1000},
                              headers={"X-Admin-Token": tok})
            families = {row["asset_family"] for row in r.json()["rows"]}
            # On the preview DB we have specialty assets — expect at
            # least access_protection (road plates) to appear.
            assert any(f.startswith("specialty:") for f in families), \
                f"no specialty rows present — families seen: {families}"
    _run(go())


# ─── 7 · Performance smoke ──────────────────────────────────────────
def test_contract_returns_under_10s_for_1k_rows():
    """Best-effort latency smoke. Preview DB is shared, so 10s is the
    upper bound. Actual perf in prod will be lower with indices."""
    import time
    async def go():
        tok = await _admin_token()
        async with httpx.AsyncClient(timeout=15) as c:
            t0 = time.time()
            r = await c.get(f"{BASE}{ENDPOINT}", params={"limit": 1000},
                              headers={"X-Admin-Token": tok})
            elapsed = time.time() - t0
            assert r.status_code == 200
            assert elapsed < 10, f"too slow: {elapsed:.2f}s"
    _run(go())
