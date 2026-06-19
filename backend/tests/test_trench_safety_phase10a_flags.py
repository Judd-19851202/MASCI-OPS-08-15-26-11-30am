"""Phase 10A · Public Excavation Workflow — extended OSHA flag coverage.

Covers the 10 deterministic OSHA Subpart P flags (G-1 closure) and
ensures coaching language is preserved (no punitive vocabulary).
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
    pwd = os.environ.get("ADMIN_PASSWORD", "Maddix123!")
    r = requests.post(f"{API}/api/admin/login", json={"password": pwd}, timeout=15)
    r.raise_for_status()
    return r.json()["token"]


def _h(token: str) -> dict:
    return {"X-Admin-Token": token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def token():
    return _admin_token()


def _payload(**overrides):
    base = {
        "project_name": f"QA-Flag {uuid.uuid4().hex[:5]}",
        "supervisor_name": "Test Foreman",
        "submitted_by": "qa-flags@example.com",
        "date_of_work": "2026-02-07",
        "work_type": "Other",
        "soil_classification": "Type B",
        "protective_system": "Sloping",
    }
    base.update(overrides)
    return base


def _submit(p):
    r = requests.post(f"{API}/api/trench-safety/excavations/public/submit", json=p, timeout=15)
    r.raise_for_status()
    return r.json()


# Flag 1 · ACCESS_EGRESS — depth ≥ 4 ft, no access installed
def test_flag_access_egress():
    doc = _submit(_payload(depth_ge_4ft=True, depth_ft=4, access_egress_installed=False))
    codes = {f["code"] for f in doc["flags"]}
    assert "ACCESS_EGRESS" in codes


# Flag 2 · PROTECTIVE_SYSTEM — depth ≥ 5 ft and no system
def test_flag_protective_system():
    doc = _submit(_payload(depth_ge_5ft=True, depth_ft=6, protective_system="Not Required"))
    codes = {f["code"] for f in doc["flags"]}
    assert "PROTECTIVE_SYSTEM" in codes


# Flag 3 · SOIL_UNKNOWN
def test_flag_soil_unknown():
    doc = _submit(_payload(soil_classification="Unknown / Needs Review"))
    codes = {f["code"] for f in doc["flags"]}
    assert "SOIL_UNKNOWN" in codes


# Flag 4 · UTILITY_LOCATE — utility work + pending locate
def test_flag_utility_locate_pending():
    doc = _submit(_payload(work_type="Utility Work", locate_status="Pending"))
    codes = {f["code"] for f in doc["flags"]}
    assert "UTILITY_LOCATE" in codes


# Flag 5 · WATER — water present + no dewatering active
def test_flag_water_no_dewatering():
    doc = _submit(_payload(water_present=True, dewatering_active=False))
    codes = {f["code"] for f in doc["flags"]}
    assert "WATER" in codes


# Flag 6 · ATMOSPHERE — concern noted but testing not completed
def test_flag_atmosphere_not_tested():
    doc = _submit(_payload(hazardous_atmosphere_concern=True,
                            atmospheric_testing_completed=False))
    codes = {f["code"] for f in doc["flags"]}
    assert "ATMOSPHERE" in codes


# Flag 7 · TRENCH_BOX_ASSIGNMENT — trench box selected, no asset linked
def test_flag_trench_box_no_asset():
    doc = _submit(_payload(protective_system="Trench Box / Shielding"))
    codes = {f["code"] for f in doc["flags"]}
    assert "TRENCH_BOX_ASSIGNMENT" in codes


# Flag 8 · ROAD_PLATE_ASSIGNMENT — roadway work, no road plate assets
def test_flag_road_plate_no_asset():
    doc = _submit(_payload(work_type="Roadway Excavation"))
    codes = {f["code"] for f in doc["flags"]}
    assert "ROAD_PLATE_ASSIGNMENT" in codes


# Flag 9 · SPOIL_SETBACK — spoils < 2 ft from edge
def test_flag_spoil_setback():
    doc = _submit(_payload(spoils_2ft_from_edge=False))
    codes = {f["code"] for f in doc["flags"]}
    assert "SPOIL_SETBACK" in codes


# Flag 10 · REINSPECTION — required but not completed
def test_flag_reinspection_required_not_completed():
    doc = _submit(_payload(reinspection_required=True, reinspection_completed=False))
    codes = {f["code"] for f in doc["flags"]}
    assert "REINSPECTION" in codes


# Coaching language guard — never "Failed" / "Rejected" in flag levels
def test_flag_coaching_language_only():
    doc = _submit(_payload(
        depth_ge_5ft=True, depth_ft=6, protective_system="Not Required",
        access_egress_installed=False, soil_classification="Unknown / Needs Review",
    ))
    levels = {f["level"] for f in doc["flags"]}
    forbidden = {"Failed", "Rejected", "Violation", "Critical Failure"}
    assert not (levels & forbidden), f"punitive language found: {levels & forbidden}"
    assert levels.issubset({"Action Required", "Needs Review"})


# Status derivation — Action Required wins over Needs Review
def test_status_action_required_takes_priority():
    doc = _submit(_payload(
        depth_ge_5ft=True, depth_ft=6, protective_system="Not Required",  # Action Required
        soil_classification="Unknown / Needs Review",                     # Needs Review
    ))
    assert doc["status"] == "Action Required"


# Clean record — only protective system needs review when soil unknown removed
def test_clean_record_submitted_status():
    doc = _submit(_payload(
        depth_ge_5ft=False, depth_ge_4ft=False,
        protective_system="Sloping",
        soil_classification="Type B",
        work_type="Other",
        access_egress_required=False,
        access_egress_installed=True,
        spoils_2ft_from_edge=True,
        water_present=False,
        hazardous_atmosphere_concern=False,
        reinspection_required=False,
    ))
    # No flags expected
    assert doc["flags"] == []
    assert doc["status"] == "Submitted"


# Assigned asset IDs persist
def test_assigned_assets_persist(token):
    doc = _submit(_payload(
        protective_system="Trench Box / Shielding",
        assigned_asset_ids=["TB-01", "RP-002"],
    ))
    ex_id = doc["id"]
    r = requests.get(f"{API}/api/trench-safety/excavations/{ex_id}",
                     headers=_h(token), timeout=15)
    r.raise_for_status()
    fetched = r.json()
    assert "TB-01" in fetched.get("assigned_asset_ids", [])
    assert "RP-002" in fetched.get("assigned_asset_ids", [])


# Free-text Spanish field-notes are preserved verbatim
def test_spanish_field_notes_preserved(token):
    spanish_note = "Zanja profunda — necesita revisión del competente."
    doc = _submit(_payload(field_notes=spanish_note, language="es"))
    r = requests.get(f"{API}/api/trench-safety/excavations/{doc['id']}",
                     headers=_h(token), timeout=15)
    r.raise_for_status()
    fetched = r.json()
    assert fetched["field_notes"] == spanish_note
    assert fetched.get("language") == "es"


# Review actions full matrix
def test_review_action_matrix(token):
    p = _payload(soil_classification="Type B", protective_system="Sloping")
    ex_id = _submit(p)["id"]
    for action, expected in [
        ("request_clarification", "Needs Review"),
        ("review", "Reviewed"),
        ("reopen", "Reopened"),
        ("close", "Closed"),
    ]:
        r = requests.post(f"{API}/api/trench-safety/excavations/{ex_id}/review",
                          headers=_h(token),
                          json={"action": action, "coaching_note": f"{action}-note"},
                          timeout=15)
        r.raise_for_status()
        assert r.json()["status"] == expected, f"action {action} should yield {expected}"


# Year-scoped ID format
def test_id_year_scoped():
    doc = _submit(_payload())
    parts = doc["id"].split("-")
    assert len(parts) == 3
    assert parts[0] == "EX"
    assert parts[1].isdigit() and len(parts[1]) == 4
    assert parts[2].isdigit()
