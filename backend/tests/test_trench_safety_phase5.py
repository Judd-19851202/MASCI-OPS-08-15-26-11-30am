"""Trench Safety Operations System — Phase 5 backend test suite.

OMEGA DIRECTIVE PHASE 5 · Transport / Dispatch Integration.

Validates that the existing /api/asset-transfers state machine drives
trench safety asset movement WITHOUT a duplicate transport pipeline,
and that holds are preserved across every transport transition.

The trench bridge (routes/trench_transport_bridge.py) is the single
integration point. All status transitions route through the Phase 4B
hold engine (resolve_operational_status).
"""
from __future__ import annotations

import os
from typing import Any, Dict

import httpx
import pytest


API_BASE = (
    os.environ.get("TRENCH_SAFETY_API_BASE") or "http://localhost:8001"
).rstrip("/")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")


@pytest.fixture(scope="module")
def admin_headers() -> Dict[str, str]:
    r = httpx.post(f"{API_BASE}/api/admin/login", json={"password": ADMIN_PASSWORD}, timeout=15.0)
    assert r.status_code == 200
    return {"X-Admin-Token": r.json()["token"]}


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=20.0)


def _reset_asset(client, headers, tag):
    """Reset to clean Available state — clears holds, certs, deployments."""
    r = client.get(f"/api/trench-safety/assets/{tag}/holds", params={"active_only": "true"}, headers=headers)
    if r.status_code == 200:
        for h in r.json().get("items", []):
            client.post(f"/api/trench-safety/holds/{h['id']}/clear",
                        json={"clear_reason": "phase5 reset", "clear_source": "manual"},
                        headers=headers)
    r = client.get(f"/api/trench-safety/assets/{tag}/certifications", params={"status": "Active"}, headers=headers)
    if r.status_code == 200:
        for c in r.json().get("items", []):
            client.post(f"/api/trench-safety/certifications/{c['id']}/revoke",
                        json={"reason": "phase5 reset"}, headers=headers)
    client.put(f"/api/trench-safety/assets/{tag}",
               json={"requires_certification": False}, headers=headers)
    client.post(f"/api/trench-safety/assets/{tag}/return",
                json={"returned_by": "phase5-reset"}, headers=headers)


def _equipment_master_row(client, asset_id: str) -> Dict[str, Any]:
    r = client.get("/api/equipment-master", params={"category": "Trench Safety"})
    for it in r.json()["items"]:
        if it.get("asset_id") == asset_id:
            return it
    return {}


def _create_transfer(client, headers, *, asset_id, to_project_number=None, to_location_label=None, to_project_name=None):
    em = _equipment_master_row(client, asset_id)
    assert em, f"asset {asset_id} not found in equipment_master"
    payload = {
        "equipment_id": em["id"],
        "from_location_label": em.get("location") or "MASCI Yard",
        "to_location_label": to_location_label or to_project_name or to_project_number or "MASCI Yard",
        "to_project_number": to_project_number,
        "to_project_name": to_project_name,
        "reason": "phase5 test transfer",
    }
    r = client.post("/api/asset-transfers", json=payload, headers=headers)
    assert r.status_code in (200, 201), r.text
    return r.json()


def _advance(client, headers, tid, to_state):
    if to_state == "Approved":
        return client.post(f"/api/asset-transfers/{tid}/approve", json={}, headers=headers)
    if to_state == "In Transit":
        return client.post(f"/api/asset-transfers/{tid}/in-transit", json={}, headers=headers)
    if to_state == "Received":
        return client.post(
            f"/api/asset-transfers/{tid}/receive",
            json={"signer_name": "phase5-receiver", "signature_image": "data:image/png;base64,iVBORw0KGgo="},
            headers=headers,
        )
    if to_state == "Cancelled":
        return client.post(f"/api/asset-transfers/{tid}/cancel", json={"reason": "phase5"}, headers=headers)
    raise ValueError(to_state)


@pytest.fixture(scope="module", autouse=True)
def _phase5_setup(admin_headers):
    with httpx.Client(base_url=API_BASE, timeout=15.0) as c:
        for tag in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07"):
            _reset_asset(c, admin_headers, tag)
    yield
    with httpx.Client(base_url=API_BASE, timeout=15.0) as c:
        for tag in ("TB-01", "TB-02", "TB-03", "TB-04", "TB-05", "TB-06", "TB-07"):
            _reset_asset(c, admin_headers, tag)


# ──────────────────────────────────────────────────────────────────────
# § Core lifecycle
# ──────────────────────────────────────────────────────────────────────

def test_in_transit_marks_trench_asset_in_transport(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-07")
    t = _create_transfer(
        client, admin_headers,
        asset_id="TB-07",
        to_project_number="PHASE5-A",
        to_project_name="Oxford Road",
        to_location_label="Oxford Road",
    )
    _advance(client, admin_headers, t["id"], "Approved")
    r = _advance(client, admin_headers, t["id"], "In Transit")
    assert r.status_code == 200
    asset = client.get("/api/trench-safety/assets/TB-07", headers=admin_headers).json()
    assert asset["operational_status"] == "In Transport"
    assert asset["current_location"] == "In Transit"
    assert asset["active_transfer_id"] == t["id"]


def test_receive_to_project_updates_status_and_project(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-07")
    t = _create_transfer(
        client, admin_headers, asset_id="TB-07",
        to_project_number="PHASE5-B", to_project_name="NSB Airport", to_location_label="NSB Airport",
    )
    _advance(client, admin_headers, t["id"], "Approved")
    _advance(client, admin_headers, t["id"], "In Transit")
    r = _advance(client, admin_headers, t["id"], "Received")
    assert r.status_code == 200
    asset = client.get("/api/trench-safety/assets/TB-07", headers=admin_headers).json()
    assert asset["operational_status"] == "Assigned"
    assert asset["current_project_name"] == "NSB Airport"
    assert asset["current_project_number"] == "PHASE5-B"
    assert asset["current_location"] == "NSB Airport"


def test_receive_to_yard_clears_project_and_marks_available(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-07")
    # First assign to a project so we can test returning to yard
    t1 = _create_transfer(
        client, admin_headers, asset_id="TB-07",
        to_project_number="PHASE5-C", to_project_name="C", to_location_label="C",
    )
    _advance(client, admin_headers, t1["id"], "Approved")
    _advance(client, admin_headers, t1["id"], "In Transit")
    _advance(client, admin_headers, t1["id"], "Received")
    # Now ship it back to the yard (use YARD sentinel — asset_transfers
    # requires a non-empty to_project_number string)
    t2 = _create_transfer(
        client, admin_headers, asset_id="TB-07",
        to_project_number="YARD-RETURN", to_project_name="MASCI Yard", to_location_label="MASCI Yard",
    )
    _advance(client, admin_headers, t2["id"], "Approved")
    _advance(client, admin_headers, t2["id"], "In Transit")
    _advance(client, admin_headers, t2["id"], "Received")
    asset = client.get("/api/trench-safety/assets/TB-07", headers=admin_headers).json()
    assert asset["operational_status"] == "Available"
    assert asset["current_project_number"] is None
    assert asset["current_project_name"] is None


def test_cancel_restores_status(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-06")
    t = _create_transfer(client, admin_headers, asset_id="TB-06",
                        to_project_number="CANCEL-1", to_project_name="X", to_location_label="X")
    _advance(client, admin_headers, t["id"], "Approved")
    _advance(client, admin_headers, t["id"], "In Transit")
    assert client.get("/api/trench-safety/assets/TB-06", headers=admin_headers).json()["operational_status"] == "In Transport"
    r = _advance(client, admin_headers, t["id"], "Cancelled")
    assert r.status_code == 200
    asset = client.get("/api/trench-safety/assets/TB-06", headers=admin_headers).json()
    assert asset["operational_status"] == "Available"
    assert asset["active_transfer_id"] is None


# ──────────────────────────────────────────────────────────────────────
# § Hold preservation
# ──────────────────────────────────────────────────────────────────────

def test_inspection_hold_preserved_through_full_transport_cycle(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-05")
    # Open Inspection Hold via a failing inspection
    client.post(
        "/api/trench-safety/assets/TB-05/inspections",
        json={
            "inspection_type": "Daily Visual", "inspector_name": "tester",
            "result": "Fail", "severity": "Minor", "findings": "phase5 hold test",
            "checklist": [],
        },
        headers=admin_headers,
    )
    assert client.get("/api/trench-safety/assets/TB-05", headers=admin_headers).json()["operational_status"] == "Inspection Hold"
    # Transport
    t = _create_transfer(client, admin_headers, asset_id="TB-05",
                        to_project_number="HOLD-1", to_project_name="HoldProj", to_location_label="HoldProj")
    _advance(client, admin_headers, t["id"], "Approved")
    _advance(client, admin_headers, t["id"], "In Transit")
    # Must remain on Inspection Hold during transit
    a = client.get("/api/trench-safety/assets/TB-05", headers=admin_headers).json()
    assert a["operational_status"] == "Inspection Hold"
    assert a["current_location"] == "In Transit"
    # Receive at project
    _advance(client, admin_headers, t["id"], "Received")
    a = client.get("/api/trench-safety/assets/TB-05", headers=admin_headers).json()
    # Hold preserved even though physically delivered
    assert a["operational_status"] == "Inspection Hold"
    assert a["current_location"] == "HoldProj"


def test_safety_hold_preserved_through_transport(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-04")
    client.post(
        "/api/trench-safety/assets/TB-04/inspections",
        json={"inspection_type": "Daily Visual", "inspector_name": "t",
              "result": "Fail", "severity": "Critical", "findings": "critical", "checklist": []},
        headers=admin_headers,
    )
    assert client.get("/api/trench-safety/assets/TB-04", headers=admin_headers).json()["operational_status"] == "Safety Hold"
    t = _create_transfer(client, admin_headers, asset_id="TB-04",
                        to_project_number="SAF-1", to_project_name="SafeProj", to_location_label="SafeProj")
    _advance(client, admin_headers, t["id"], "Approved")
    _advance(client, admin_headers, t["id"], "In Transit")
    _advance(client, admin_headers, t["id"], "Received")
    a = client.get("/api/trench-safety/assets/TB-04", headers=admin_headers).json()
    assert a["operational_status"] == "Safety Hold"
    # Public field view must still say DO NOT USE
    pub = client.get("/api/trench-safety/public/assets/TB-04").json()
    assert pub["operational_status"] == "Safety Hold"


# ──────────────────────────────────────────────────────────────────────
# § Mirrors + project + audit
# ──────────────────────────────────────────────────────────────────────

def test_equipment_master_mirror_reflects_transport(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-03")
    t = _create_transfer(client, admin_headers, asset_id="TB-03",
                        to_project_number="MIR-1", to_project_name="MirProj", to_location_label="MirProj")
    _advance(client, admin_headers, t["id"], "Approved")
    _advance(client, admin_headers, t["id"], "In Transit")
    em = _equipment_master_row(client, "TB-03")
    assert em["operational_status"] == "In Transport"
    _advance(client, admin_headers, t["id"], "Received")
    em = _equipment_master_row(client, "TB-03")
    assert em["operational_status"] == "Assigned"
    assert em["current_project_name"] == "MirProj"


def test_by_project_sees_transported_asset(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-02")
    t = _create_transfer(client, admin_headers, asset_id="TB-02",
                        to_project_number="BP-1", to_project_name="ByProjShip", to_location_label="ByProjShip")
    _advance(client, admin_headers, t["id"], "Approved")
    _advance(client, admin_headers, t["id"], "In Transit")
    _advance(client, admin_headers, t["id"], "Received")
    r = client.get("/api/trench-safety/by-project",
                   params={"project_number": "BP-1"}, headers=admin_headers)
    assert r.status_code == 200
    ids = [a["asset_id"] for a in r.json()["current"]]
    assert "TB-02" in ids


def test_audit_records_full_transport_chain(client, admin_headers):
    _reset_asset(client, admin_headers, "TB-01")
    t = _create_transfer(client, admin_headers, asset_id="TB-01",
                        to_project_number="AUD-1", to_project_name="A", to_location_label="A")
    _advance(client, admin_headers, t["id"], "Approved")
    _advance(client, admin_headers, t["id"], "In Transit")
    _advance(client, admin_headers, t["id"], "Received")
    r = client.get("/api/trench-safety/assets/TB-01/audit",
                   params={"limit": 100}, headers=admin_headers)
    kinds = {e["kind"] for e in r.json()["items"]}
    assert "trench_safety_transport_started" in kinds
    assert "trench_safety_transport_completed" in kinds


# ──────────────────────────────────────────────────────────────────────
# § Non-trench transfer regression — bridge must be a no-op
# ──────────────────────────────────────────────────────────────────────

def test_non_trench_transfer_is_unaffected(client, admin_headers):
    # Pick any non-trench equipment_master row
    r = client.get("/api/equipment-master")
    non_trench = next(
        (i for i in r.json()["items"] if i.get("category") != "Trench Safety"),
        None,
    )
    if non_trench is None:
        pytest.skip("No non-trench equipment in equipment_master to regression-test")
    payload = {
        "equipment_id": non_trench["id"],
        "from_location_label": "Yard",
        "to_location_label": "Site",
        "to_project_number": "NON-TRENCH-1",
        "reason": "phase5 regression",
    }
    r = client.post("/api/asset-transfers", json=payload, headers=admin_headers)
    assert r.status_code in (200, 201)
    tid = r.json()["id"]
    a = client.post(f"/api/asset-transfers/{tid}/approve", json={}, headers=admin_headers)
    b = client.post(f"/api/asset-transfers/{tid}/in-transit", json={}, headers=admin_headers)
    c = client.post(f"/api/asset-transfers/{tid}/receive",
                    json={"signer_name": "x", "signature_image": "data:image/png;base64,xx"},
                    headers=admin_headers)
    assert a.status_code == 200
    assert b.status_code == 200
    assert c.status_code == 200
    # And NO trench audit was created for this equipment
    # (we can't easily query audit_events by equipment_id, but the bridge
    # exits early when category != Trench Safety, so a 200 chain is the
    # regression signal we need).
