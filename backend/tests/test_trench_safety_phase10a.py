"""Phase 10A · Public Excavation Workflow tests (G-1 closure)."""
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
def token():
    return _admin_token()


def _minimal_payload(**overrides):
    base = {
        "project_name": f"QA Test {uuid.uuid4().hex[:5]}",
        "supervisor_name": "Test Foreman",
        "submitted_by": "qa@example.com",
        "date_of_work": "2026-02-07",
        "work_type": "Utility Work",
        "soil_classification": "Unknown / Needs Review",
        "protective_system": "Needs Safety Review",
    }
    base.update(overrides)
    return base


# 1 · Public submit (no auth)
def test_public_submit_works():
    r = requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                      json=_minimal_payload(), timeout=15)
    r.raise_for_status()
    doc = r.json()
    assert doc["id"].startswith("EX-")
    # Soil unknown + Needs Safety Review protective system → Needs Review flag from SOIL_UNKNOWN at minimum
    assert any(f["code"] == "SOIL_UNKNOWN" for f in doc["flags"])
    assert doc["status"] in ("Needs Review", "Action Required", "Submitted")


# 2 · Flag engine — deep + no protective system → Action Required
def test_flag_engine_depth_5ft_no_protect(token):
    p = _minimal_payload(depth_ft=6, depth_ge_5ft=True, depth_ge_4ft=True,
                         protective_system="Not Required",
                         access_egress_installed=False,
                         soil_classification="Type B")
    r = requests.post(f"{API}/api/trench-safety/excavations/public/submit", json=p, timeout=15)
    r.raise_for_status()
    doc = r.json()
    codes = {f["code"] for f in doc["flags"]}
    assert "PROTECTIVE_SYSTEM" in codes
    assert "ACCESS_EGRESS" in codes  # depth ≥ 4 ft, no access installed
    assert doc["status"] == "Action Required"


# 3 · Flag engine — utility pending
def test_flag_engine_utility_pending():
    p = _minimal_payload(work_type="Utility Work", locate_status="Pending",
                         soil_classification="Type C")
    r = requests.post(f"{API}/api/trench-safety/excavations/public/submit", json=p, timeout=15)
    r.raise_for_status()
    codes = {f["code"] for f in r.json()["flags"]}
    assert "UTILITY_LOCATE" in codes


# 4 · Trench box selected but no asset
def test_flag_engine_trench_box_no_asset():
    p = _minimal_payload(protective_system="Trench Box / Shielding",
                         soil_classification="Type B")
    r = requests.post(f"{API}/api/trench-safety/excavations/public/submit", json=p, timeout=15)
    r.raise_for_status()
    codes = {f["code"] for f in r.json()["flags"]}
    assert "TRENCH_BOX_ASSIGNMENT" in codes


# 5 · List + filter (requires safety/admin)
def test_list_filter(token):
    r = requests.get(f"{API}/api/trench-safety/excavations",
                     headers=_h(token), params={"status": "Action Required"}, timeout=15)
    r.raise_for_status()
    body = r.json()
    assert "items" in body
    for it in body["items"]:
        assert it["status"] == "Action Required"


# 6 · Review flow
def test_review_action_closes_record(token):
    p = _minimal_payload(soil_classification="Type B", protective_system="Sloping")
    create = requests.post(f"{API}/api/trench-safety/excavations/public/submit", json=p, timeout=15)
    create.raise_for_status()
    ex_id = create.json()["id"]
    r = requests.post(f"{API}/api/trench-safety/excavations/{ex_id}/review",
                      headers=_h(token),
                      json={"action": "close", "coaching_note": "Looks good."}, timeout=15)
    r.raise_for_status()
    assert r.json()["status"] == "Closed"
    # Verify audit row + coaching note
    detail = requests.get(f"{API}/api/trench-safety/excavations/{ex_id}",
                          headers=_h(token), timeout=15).json()
    assert detail["status"] == "Closed"
    assert any(n["note"] == "Looks good." for n in detail.get("coaching_notes", []))


# 7 · Reports summary
def test_reports_summary(token):
    r = requests.get(f"{API}/api/trench-safety/excavations/reports/summary",
                     headers=_h(token), timeout=15)
    r.raise_for_status()
    body = r.json()
    for k in ("total", "by_status", "action_required", "missing_protective_system", "soil_unknown"):
        assert k in body
    assert isinstance(body["total"], int)


# 8 · Auto-incrementing year-scoped IDs (never reused)
def test_excavation_id_unique():
    seen = set()
    for _ in range(3):
        r = requests.post(f"{API}/api/trench-safety/excavations/public/submit",
                          json=_minimal_payload(), timeout=15)
        r.raise_for_status()
        eid = r.json()["id"]
        assert eid not in seen
        seen.add(eid)
