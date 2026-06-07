"""FV-7 Safety Gap Closure tests."""
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


def _h(token):
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def token():
    return _admin_token()


def _submit(**overrides):
    base = {
        "project_name": f"FV7-{uuid.uuid4().hex[:5]}",
        "foreman_name": "Test Foreman",
        "submitted_by": "fv7@example.com",
        "date_of_work": "2026-02-07",
        "work_type": "Other",
        "soil_classification": "Type B",
        "protective_system": "Sloping",
    }
    base.update(overrides)
    r = requests.post(f"{API}/api/trench-safety/excavations/public/submit", json=base, timeout=15)
    r.raise_for_status()
    return r.json()


# ── FV-7.1 · Trench box rated depth validation ───────────────────────
def _find_box_with_rated_depth(token):
    """Find any trench box in the registry whose rated_depth_ft is set."""
    r = requests.get(f"{API}/api/trench-safety/excavations/public/asset-roster",
                     params={"asset_type": "Trench Box", "limit": 200}, timeout=15)
    items = r.json().get("items", [])
    return next((it for it in items if it.get("rated_depth_ft")), None)


def test_trench_box_depth_flag_fires_when_excavation_exceeds_rated():
    box = _find_box_with_rated_depth(None)
    if not box:
        pytest.skip("No trench box with rated_depth_ft in registry")
    deep = (box["rated_depth_ft"] or 0) + 4
    doc = _submit(
        depth_ft=deep, depth_ge_5ft=True,
        protective_system="Trench Box / Shielding",
        assigned_asset_ids=[box["asset_id"]],
    )
    codes = {f["code"] for f in doc["flags"]}
    assert "TRENCH_BOX_DEPTH" in codes, f"Expected TRENCH_BOX_DEPTH flag; got {codes}"


def test_trench_box_depth_flag_does_not_fire_when_within_rated():
    box = _find_box_with_rated_depth(None)
    if not box:
        pytest.skip("No trench box with rated_depth_ft in registry")
    safe = max(1, (box["rated_depth_ft"] or 0) - 1)
    doc = _submit(
        depth_ft=safe,
        protective_system="Trench Box / Shielding",
        assigned_asset_ids=[box["asset_id"]],
    )
    codes = {f["code"] for f in doc["flags"]}
    assert "TRENCH_BOX_DEPTH" not in codes


# ── FV-7.3 · Foreman reinspection request (public, no auth) ──────────
def test_foreman_reinspection_request_works_without_auth(token):
    doc = _submit()
    ex_id = doc["id"]
    r = requests.post(
        f"{API}/api/trench-safety/excavations/{ex_id}/public/reinspection-request",
        json={"reason": "Rain", "note": "Half inch rain at noon"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["reinspection_required"] is True
    assert updated["reinspection_completed"] is False
    history = updated.get("reinspection_history") or []
    assert any(h.get("source") == "foreman_request" for h in history)
    # Should now appear in admin reinspection queue
    q = requests.get(f"{API}/api/trench-safety/excavations/reinspection-queue",
                     headers=_h(token), timeout=15)
    q.raise_for_status()
    assert any(it["id"] == ex_id for it in q.json().get("items", []))


def test_foreman_reinspection_request_bad_id_returns_404():
    r = requests.post(
        f"{API}/api/trench-safety/excavations/EX-2026-999/public/reinspection-request",
        json={"reason": "Rain", "note": ""},
        timeout=15,
    )
    assert r.status_code == 404


# ── FV-7.4 · Road plate dimension sanity ────────────────────────────
def _find_road_plate_with_dims(token):
    r = requests.get(f"{API}/api/trench-safety/excavations/public/asset-roster",
                     params={"asset_type": "Road Plate", "limit": 200}, timeout=15)
    items = r.json().get("items", [])
    # Roster doesn't return dimensions; check raw asset doc via admin
    for it in items[:30]:
        d = requests.get(
            f"{API}/api/admin/trench-safety/assets/{it['asset_id']}",
            headers=_h(token), timeout=15,
        )
        if d.status_code != 200:
            continue
        a = d.json()
        dims = a.get("dimensions") or {}
        if dims.get("length_ft") and dims.get("width_ft"):
            return a
    return None


def test_road_plate_dimension_flag_fires_when_plate_too_small(token):
    plate = _find_road_plate_with_dims(token)
    if not plate:
        pytest.skip("No road plate with full dimensions in registry")
    dims = plate.get("dimensions") or {}
    huge = max(float(dims.get("length_ft") or 0), float(dims.get("width_ft") or 0)) * 3
    doc = _submit(
        work_type="Roadway Excavation",
        length_ft=huge, width_ft=huge,
        road_plates_used=True,
        road_plate_ids=[plate["asset_id"]],
    )
    codes = {f["code"] for f in doc["flags"]}
    assert "ROAD_PLATE_DIMENSION" in codes


# ── FV-7.2 · Competent person designation (data-tolerant) ──────────
def test_competent_person_designation_flag_data_tolerant():
    """If the employee record cannot be found, we do not false-positive."""
    doc = _submit(
        depth_ft=6, depth_ge_5ft=True,
        competent_person_id="nonexistent-cp-id",
        competent_person_name="Phantom CP",
    )
    codes = {f["code"] for f in doc["flags"]}
    # Data-tolerant: phantom CP not in roster → no false positive
    assert "COMPETENT_PERSON_QUALIFIED" not in codes


# ── Regression — no new false-positives on happy path ──────────────
def test_clean_record_still_submits_clean():
    doc = _submit(
        depth_ft=3, depth_ge_4ft=False,
        soil_classification="Type B",
        protective_system="Sloping",
        access_egress_required=False,
        access_egress_installed=True,
        spoils_2ft_from_edge=True,
        water_present=False,
        hazardous_atmosphere_concern=False,
        reinspection_required=False,
    )
    assert doc["flags"] == []
    assert doc["status"] == "Submitted"
