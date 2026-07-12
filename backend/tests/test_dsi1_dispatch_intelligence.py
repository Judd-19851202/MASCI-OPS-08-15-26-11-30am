"""DSI-1 · Dispatch Situational Intelligence regression suite (2026-06-08)."""
from __future__ import annotations
import os
import pytest
import requests

BASE = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://backup-forensics.preview.emergentagent.com",
).rstrip("/")


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    assert r.status_code == 200
    return r.json()["portal_tokens"]["admin"]


def test_fleet_gps_enriched_fields_present(admin_token):
    """DSI-1A · every fleet-gps row carries the new per-asset health fields."""
    r = requests.get(
        f"{BASE}/api/operations/intelligence/fleet-gps",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    assert r.status_code == 200
    rows = r.json()["assets"]
    assert len(rows) > 0
    sample = rows[0]
    for key in ("gateway_status", "fault_status", "dvir_status",
                "last_event", "assigned_driver", "band", "label"):
        assert key in sample, f"missing {key} in fleet-gps row"


def test_fleet_gps_gateway_values_constrained(admin_token):
    """DSI-1F · gateway_status only in {'online','offline'}."""
    r = requests.get(
        f"{BASE}/api/operations/intelligence/fleet-gps",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    for row in r.json()["assets"]:
        assert row["gateway_status"] in ("online", "offline")
        assert row["fault_status"] in ("normal", "critical")
        assert row["dvir_status"] in ("pass", "needs_attention")


def test_ops_intelligence_dispatch_block(admin_token):
    """DSI-1D · /api/operations/intelligence now carries dispatch counts."""
    r = requests.get(
        f"{BASE}/api/operations/intelligence",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert "dispatch" in body
    for key in ("active_assignments", "active_drivers", "active_equipment"):
        assert key in body["dispatch"], f"missing {key} in dispatch block"


def test_shop_not_reporting_enriched(admin_token):
    """DSI-1E · shop not_reporting rows carry assigned_operator + last_known_location."""
    r = requests.get(
        f"{BASE}/api/operations/intelligence/shop",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    assert r.status_code == 200
    nr = r.json()["equipment_not_reporting"]
    if not nr:
        pytest.skip("no not-reporting equipment to assert on")
    sample = nr[0]
    for key in ("assigned_operator", "last_known_location"):
        assert key in sample


def test_driver_profile_activity_and_hos_status(admin_token):
    """DSI-1C · driver profile now carries activity[] + safety.hos_status."""
    drv = requests.get(
        f"{BASE}/api/admin/integrations/cleanup/drivers",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    ).json()
    linked = next((r for r in drv["rows"] if r.get("existing_employee_id")), None)
    if not linked:
        pytest.skip("no linked driver")
    r = requests.get(
        f"{BASE}/api/operations/drivers/{linked['existing_employee_id']}/profile",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert "activity" in body
    assert "hos_status" in body["safety"]
    assert body["safety"]["hos_status"] in ("violation_active", "clean", "unknown")
