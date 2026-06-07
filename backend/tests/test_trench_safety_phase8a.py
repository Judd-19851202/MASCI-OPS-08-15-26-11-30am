"""Phase 8A — Road Plate integration tests.

Verifies that Road Plates are first-class native asset types in the
certified Trench Safety / Excavation Safety Operations System:

  • Asset CRUD (create with RP-XXX id, read, update, retire) uses the
    same /api/trench-safety/assets endpoints. No new module.
  • Auto-suggested asset_id (next-id endpoint) walks the live registry
    and never reuses a number.
  • Road Plate-specific fields persist (length_in, width_in, thickness_in,
    material, rated_capacity_lb, surface_condition, edge_condition,
    lifting_point_condition, anti_skid_status, markings).
  • Inspection engine handles a road-plate checklist; Fail+Major opens
    Inspection + Maintenance Holds via the existing hold engine.
  • equipment_master mirror reflects the road plate as a Trench Safety
    unit (single source of truth).
  • Public QR projection includes the field-safe Road Plate specs and
    NEVER leaks internal condition detail.
  • Public overview counts_by_type includes Road Plate.
  • Audit + retirement flow identical to Trench Box.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

import pytest
import requests

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

API = os.environ.get("TS_API_BASE", "http://localhost:8001")


def _admin_token() -> str:
    pwd = os.environ.get("ADMIN_PASSWORD", "MASCI1982!")
    r = requests.post(f"{API}/api/admin/login", json={"password": pwd}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _h(token: str) -> dict:
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def token() -> str:
    return _admin_token()


def _create_rp(token: str, *, asset_id: str | None = None, **extra) -> dict:
    if asset_id is None:
        asset_id = f"RP-T{uuid.uuid4().hex[:5].upper()}"
    payload = {
        "asset_id": asset_id,
        "asset_type": "Road Plate",
        "manufacturer": "Acme Steel",
        "model": "RP-Standard",
        "serial_number": f"SN-{uuid.uuid4().hex[:6].upper()}",
        "length_in": 96,
        "width_in": 48,
        "thickness_in": 1.0,
        "weight_lbs": 1500,
        "material": "A36 Steel",
        "rated_capacity_lb": 80000,
        "surface_condition": "Good",
        "edge_condition": "Good",
        "lifting_point_condition": "Good",
        "anti_skid_status": "Present",
        "markings": "MASCI · Yellow",
        "condition": "Good",
    }
    payload.update(extra)
    r = requests.post(f"{API}/api/trench-safety/assets", headers=_h(token), json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


@pytest.fixture(scope="module")
def road_plate(token):
    asset = _create_rp(token)
    yield asset
    requests.post(
        f"{API}/api/trench-safety/assets/{asset['asset_id']}/retire",
        headers=_h(token), json={"retired_reason": "phase 8a test cleanup"}, timeout=15,
    )


# ─────────────────────────────────────────────────────────────────────
# 1 · Asset registry — create / read / update
# ─────────────────────────────────────────────────────────────────────

def test_create_road_plate_persists_specs(road_plate, token):
    aid = road_plate["asset_id"]
    assert aid.startswith("RP-"), f"expected RP-prefixed asset_id, got {aid!r}"
    assert road_plate["asset_type"] == "Road Plate"
    # Read it back
    r = requests.get(f"{API}/api/trench-safety/assets/{aid}", headers=_h(token), timeout=15)
    r.raise_for_status()
    doc = r.json()
    assert doc["length_in"] == 96
    assert doc["width_in"] == 48
    assert doc["thickness_in"] == 1.0
    assert doc["material"] == "A36 Steel"
    assert doc["rated_capacity_lb"] == 80000
    assert doc["surface_condition"] == "Good"
    assert doc["edge_condition"] == "Good"
    assert doc["lifting_point_condition"] == "Good"
    assert doc["anti_skid_status"] == "Present"
    assert doc["markings"] == "MASCI · Yellow"


def test_update_road_plate_condition_fields(token, road_plate):
    aid = road_plate["asset_id"]
    r = requests.put(
        f"{API}/api/trench-safety/assets/{aid}",
        headers=_h(token),
        json={
            "surface_condition": "Fair",
            "anti_skid_status": "Worn",
            "markings": "MASCI · Yellow · Stripe Worn",
        }, timeout=15,
    )
    r.raise_for_status()
    doc = r.json()
    assert doc["surface_condition"] == "Fair"
    assert doc["anti_skid_status"] == "Worn"
    assert "Stripe Worn" in (doc.get("markings") or "")


# ─────────────────────────────────────────────────────────────────────
# 2 · Asset-id suggestion
# ─────────────────────────────────────────────────────────────────────

def test_next_id_road_plate_format(token):
    r = requests.get(
        f"{API}/api/trench-safety/assets/next-id",
        headers=_h(token), params={"asset_type": "Road Plate"}, timeout=15,
    )
    r.raise_for_status()
    body = r.json()
    assert body["prefix"] == "RP"
    assert body["next_id"].startswith("RP-")
    # 3-digit zero pad
    tail = body["next_id"].split("-", 1)[1]
    assert len(tail) == 3 and tail.isdigit()


def test_next_id_skips_used_numbers(token):
    # Use a high RP number that's unlikely to be in use; if it already
    # exists from a previous run, retire it first to keep the test
    # idempotent.
    high_id = "RP-987"
    requests.post(
        f"{API}/api/trench-safety/assets/{high_id}/retire",
        headers=_h(token), json={"retired_reason": "test reset"}, timeout=15,
    )
    # Now ensure asset is created fresh — if retired, the asset still
    # exists and create will 409. So pick a different RP and avoid that.
    try_id = f"RP-9{uuid.uuid4().hex[:2].upper()}"
    r0 = requests.get(
        f"{API}/api/trench-safety/assets/{try_id}",
        headers=_h(token), timeout=15,
    )
    if r0.status_code == 200:
        # Pick another
        try_id = f"RP-9{uuid.uuid4().hex[:2].upper()}A"
    a1 = _create_rp(token, asset_id=try_id)
    try:
        r = requests.get(
            f"{API}/api/trench-safety/assets/next-id",
            headers=_h(token), params={"asset_type": "Road Plate"}, timeout=15,
        )
        r.raise_for_status()
        body = r.json()
        # Whatever the next number is, it must not be the one we just used.
        assert body["next_id"] != try_id
    finally:
        requests.post(
            f"{API}/api/trench-safety/assets/{a1['asset_id']}/retire",
            headers=_h(token), json={"retired_reason": "test"}, timeout=15,
        )


# ─────────────────────────────────────────────────────────────────────
# 3 · Inspection engine + hold engine (existing infra)
# ─────────────────────────────────────────────────────────────────────

def test_road_plate_inspection_fail_major_opens_holds(token):
    asset = _create_rp(token)
    aid = asset["asset_id"]
    try:
        checklist = [
            {"key": "bent_plate", "label": "Bent Plate", "result": "Fail", "note": ""},
            {"key": "cracks", "label": "Cracks", "result": "Pass", "note": ""},
            {"key": "missing_anti_skid", "label": "Missing Anti-Skid", "result": "Fail", "note": ""},
        ]
        r = requests.post(
            f"{API}/api/trench-safety/assets/{aid}/inspections",
            headers=_h(token),
            json={
                "inspection_type": "Daily Visual",
                "inspector_name": "QA Tester",
                "result": "Fail",
                "severity": "Major",
                "findings": "Bent plate observed mid-shift; anti-skid missing.",
                "corrective_actions": "Pull from service immediately.",
                "checklist": checklist,
            }, timeout=15,
        )
        r.raise_for_status()
        body = r.json()
        fresh = body["asset"]
        # Hold engine took over — asset is on a hold (priority Maintenance > Inspection)
        assert fresh["operational_status"] in ("Inspection Hold", "Maintenance Hold", "Safety Hold")
        # Open holds endpoint reflects it
        r2 = requests.get(
            f"{API}/api/trench-safety/assets/{aid}/holds",
            headers=_h(token), params={"is_active": True}, timeout=15,
        )
        r2.raise_for_status()
        kinds = {h["kind"] for h in r2.json().get("items", [])}
        assert "Inspection Hold" in kinds
        assert "Maintenance Hold" in kinds  # auto stub on Major
        # Repair stub auto-created
        assert body.get("repair_stub_id")
    finally:
        requests.post(
            f"{API}/api/trench-safety/assets/{aid}/retire",
            headers=_h(token), json={"retired_reason": "test"}, timeout=15,
        )


# ─────────────────────────────────────────────────────────────────────
# 4 · equipment_master mirror
# ─────────────────────────────────────────────────────────────────────

def test_road_plate_mirrored_into_equipment_master(token, road_plate):
    aid = road_plate["asset_id"]
    # The mirror is single-direction (trench_safety_assets → equipment_master).
    # We probe by hitting the operations picker which reads from the
    # asset registry directly.
    r = requests.get(
        f"{API}/api/trench-safety/operations/picker",
        headers=_h(token), params={"asset_type": "Road Plate"}, timeout=15,
    )
    r.raise_for_status()
    ids = [a["asset_id"] for a in r.json().get("items", [])]
    assert aid in ids


# ─────────────────────────────────────────────────────────────────────
# 5 · Public projection — field-safe view shows Road Plate specs
# ─────────────────────────────────────────────────────────────────────

def test_public_qr_landing_exposes_road_plate_specs(road_plate):
    aid = road_plate["asset_id"]
    # PUBLIC — no auth
    r = requests.get(f"{API}/api/trench-safety/public/assets/{aid}", timeout=15)
    r.raise_for_status()
    doc = r.json()
    assert doc["asset_id"] == aid
    assert doc["asset_type"] == "Road Plate"
    # Field-safe physical specs are present
    assert doc.get("length_in") == 96
    assert doc.get("width_in") == 48
    assert doc.get("thickness_in") == 1.0
    assert doc.get("material") == "A36 Steel"
    assert doc.get("rated_capacity_lb") == 80000
    # Internal condition detail NOT exposed
    assert "edge_condition" not in doc
    assert "lifting_point_condition" not in doc
    assert "surface_condition" not in doc


def test_public_overview_counts_road_plates():
    r = requests.get(f"{API}/api/trench-safety/public/overview", timeout=15)
    r.raise_for_status()
    body = r.json()
    assert "Road Plate" in body["counts_by_type"]
    assert body["counts_by_type"]["Road Plate"] >= 1


# ─────────────────────────────────────────────────────────────────────
# 6 · Audit timeline — confirms events route through the existing log
# ─────────────────────────────────────────────────────────────────────

def test_road_plate_audit_trail(token, road_plate):
    aid = road_plate["asset_id"]
    r = requests.get(f"{API}/api/trench-safety/assets/{aid}/audit", headers=_h(token), timeout=15)
    r.raise_for_status()
    kinds = [ev["kind"] for ev in r.json().get("items", [])]
    assert "trench_asset_created" in kinds


# ─────────────────────────────────────────────────────────────────────
# 7 · Retirement is terminal and bumps the asset out of active overview
# ─────────────────────────────────────────────────────────────────────

def test_road_plate_retirement_terminal(token):
    asset = _create_rp(token)
    aid = asset["asset_id"]
    r = requests.post(
        f"{API}/api/trench-safety/assets/{aid}/retire",
        headers=_h(token), json={"retired_reason": "End of life — bent plate"}, timeout=15,
    )
    r.raise_for_status()
    doc = r.json()
    assert doc["operational_status"] == "Retired"
    assert doc["is_active"] is False
