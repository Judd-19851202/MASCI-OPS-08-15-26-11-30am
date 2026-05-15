"""Iter153E · Phase E — Cross-System Integration completeness tests.

Verifies that operational modules correctly fan out to the shared
task_service + notification_service infrastructure:

  * Incidents (source_module="safety.incidents")
  * Inspections (source_module="safety.inspections")
  * QA/QC Inspections (source_module="qaqc.inspections")
  * Equipment Pre-Op (source_module="equipment.preop")
  * Fire Extinguishers (source_module="safety.fire_extinguishers")

Each test:
  1. Posts a record that should trigger fan-out.
  2. Filters /api/tasks by source_module and checks that the new
     source_record_id appears (so we don't depend on other tests'
     records).
  3. Confirms NO duplicate tasks (idempotency).
"""
import os
import time
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(p, k):
    try:
        with open(p) as f:
            for line in f:
                if line.startswith(f"{k}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
NO_ADMIN = {"X-Admin-Token": ""}
TAG = f"PhaseE_{uuid.uuid4().hex[:6]}"


def _safety_token():
    r = requests.post(f"{BASE_URL}/api/safety/login",
                       json={"email": "safety@mascigc.com",
                             "password": "SafetyTest2026!"}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Safety login failed: {r.status_code}")
    return r.json()["token"]


def _tasks_for(source_module: str, source_record_id: str, tries: int = 4):
    """Poll for a few hundred ms because fan-out is fire-and-forget."""
    for _ in range(tries):
        r = requests.get(
            f"{BASE_URL}/api/tasks",
            params={"source_module": source_module, "limit": 100},
            timeout=20,
        )
        if r.status_code == 200:
            items = [t for t in r.json().get("items", [])
                     if t.get("source_record_id") == source_record_id]
            if items:
                return items
        time.sleep(0.25)
    return []


def _notifs_for(source_module: str, source_record_id: str, tries: int = 4):
    for _ in range(tries):
        r = requests.get(
            f"{BASE_URL}/api/notifications",
            params={"limit": 100}, timeout=20,
        )
        if r.status_code == 200:
            items = [n for n in r.json().get("items", [])
                     if n.get("linked_source_module") == source_module
                     and n.get("linked_source_record_id") == source_record_id]
            if items:
                return items
        time.sleep(0.25)
    return []


# ─── INCIDENTS ────────────────────────────────────────────────────
def test_incident_fanout():
    body = {
        "project_name": f"{TAG}-PROJ",
        "project_number": f"{TAG}-NUM",
        "location": "test",
        "incident_date": "2026-05-15",
        "incident_time": "10:00",
        "reported_date": "2026-05-15",
        "reported_by": "PhaseE",
        "incident_type": "Near Miss",
        "severity": "High",
        "osha_recordable": "No",
        "work_stopped": "No",
        "person_name": "Tester",
        "description": "Phase E test incident",
    }
    r = requests.post(f"{BASE_URL}/api/incidents", json=body, timeout=20)
    assert r.status_code in (200, 201), r.text
    inc_id = r.json()["id"]
    items = _tasks_for("safety.incidents", inc_id)
    assert len(items) == 1, f"expected 1 task, got {len(items)}"
    assert items[0]["assignee_role"] == "safety"
    assert items[0]["priority"] in ("Critical", "High")
    notifs = _notifs_for("safety.incidents", inc_id)
    roles = {nf["recipient_role"] for nf in notifs}
    assert "safety" in roles, f"safety notif missing; got: {roles}"
    assert "pm" in roles, f"pm notif missing; got: {roles}"


def test_incident_idempotent_no_duplicates():
    body = {
        "project_name": f"{TAG}-PROJ2", "project_number": f"{TAG}-NUM2",
        "location": "x", "incident_date": "2026-05-15",
        "incident_time": "10:00", "reported_date": "2026-05-15",
        "reported_by": "x", "incident_type": "Property Damage",
        "severity": "Medium", "osha_recordable": "No",
        "work_stopped": "No", "person_name": "x", "description": "x",
    }
    r = requests.post(f"{BASE_URL}/api/incidents", json=body, timeout=20)
    inc_id = r.json()["id"]
    items = _tasks_for("safety.incidents", inc_id)
    assert len(items) == 1


# ─── INSPECTIONS ──────────────────────────────────────────────────
def _insp_body(**overrides):
    body = {
        "project_name": f"{TAG}-IP",
        "project_number": f"{TAG}-IPN",
        "location": "test",
        "inspection_date": "2026-05-15",
        "inspection_time": "10:00",
        "operation": "Day",
        "inspector_name": "PhaseE Inspector",
        "foreman_name": "PhaseE Foreman",
        "work_activity": "Test work",
        "hazards_observed": "No",
        "stop_work_issued": "No",
    }
    body.update(overrides)
    return body


def test_inspection_autofail_fanout():
    body = _insp_body(auto_fail_count=2, hazards_observed="Yes")
    r = requests.post(f"{BASE_URL}/api/inspections", json=body, timeout=20)
    assert r.status_code in (200, 201), r.text
    iid = r.json()["id"]
    items = _tasks_for("safety.inspections", iid)
    assert len(items) == 1
    assert items[0]["assignee_role"] == "safety"
    assert items[0]["priority"] == "High"
    notifs = _notifs_for("safety.inspections", iid)
    roles = {nf["recipient_role"] for nf in notifs}
    assert "safety" in roles and "pm" in roles


def test_inspection_stopwork_critical_priority():
    body = _insp_body(stop_work_issued="Yes")
    r = requests.post(f"{BASE_URL}/api/inspections", json=body, timeout=20)
    iid = r.json()["id"]
    items = _tasks_for("safety.inspections", iid)
    assert len(items) == 1
    assert items[0]["priority"] == "Critical"


def test_inspection_pass_no_task():
    body = _insp_body()  # all clean defaults
    r = requests.post(f"{BASE_URL}/api/inspections", json=body, timeout=20)
    iid = r.json()["id"]
    # Wait briefly to confirm NO task appears
    time.sleep(0.5)
    items = _tasks_for("safety.inspections", iid, tries=2)
    assert len(items) == 0


# ─── QA/QC ────────────────────────────────────────────────────────
def test_qaqc_fail_fanout():
    body = {
        "project_name": f"{TAG}-QC",
        "project_number": f"{TAG}-QCN",
        "location": "loc",
        "inspection_kind": "concrete_form",
        "inspection_date": "2026-05-15",
        "inspection_time": "10:00",
        "work_area": "Test area",
        "inspector_name": "PhaseE",
        "foreman_name": "PhaseE",
        "checklist": [
            {"key": "k1", "label": "rebar tie", "result": "pass"},
            {"key": "k2", "label": "form clean", "result": "fail"},
            {"key": "k3", "label": "alignment", "result": "fail"},
        ],
        "deficiencies": "two fail items"
    }
    r = requests.post(f"{BASE_URL}/api/qaqc-inspections", json=body, timeout=20)
    assert r.status_code in (200, 201), r.text
    iid = r.json()["id"]
    items = _tasks_for("qaqc.inspections", iid)
    assert len(items) == 1
    assert items[0]["assignee_role"] == "pm"


# ─── EQUIPMENT PRE-OP ─────────────────────────────────────────────
def _preop_body(**overrides):
    body = {
        "project_name": f"{TAG}-PO",
        "location": "yard",
        "inspection_date": "2026-05-15",
        "inspection_time": "08:00",
        "operator_name": "PhaseE",
        "equipment_type": "Skid Steer",
        "equipment_unit": f"PE-{uuid.uuid4().hex[:8]}",
        "equipment_make": "Bobcat",
        "equipment_model": "S650",
        "equipment_serial": "PHASE-E-SN",
        "checklist": {},
        "fail_count": 0,
    }
    body.update(overrides)
    return body


def test_preop_fanout():
    body = _preop_body(fail_count=2)
    r = requests.post(f"{BASE_URL}/api/equipment-inspections", json=body, timeout=20)
    assert r.status_code in (200, 201), r.text
    iid = r.json()["id"]
    items = _tasks_for("equipment.preop", iid)
    assert len(items) == 1
    assert items[0]["assignee_role"] == "shop"
    notifs = _notifs_for("equipment.preop", iid)
    roles = {nf["recipient_role"] for nf in notifs}
    assert "shop" in roles and "dispatch" in roles


def test_preop_clean_no_task():
    body = _preop_body(fail_count=0)
    r = requests.post(f"{BASE_URL}/api/equipment-inspections", json=body, timeout=20)
    iid = r.json()["id"]
    time.sleep(0.5)
    items = _tasks_for("equipment.preop", iid, tries=2)
    assert len(items) == 0


# ─── FIRE EXTINGUISHERS ──────────────────────────────────────────
def test_fire_ext_inspection_fail_fanout():
    safety = _safety_token()
    h = {"X-Safety-Token": safety, **NO_ADMIN}
    create = requests.post(
        f"{BASE_URL}/api/safety/fire-extinguishers", headers=h,
        json={
            "unit_id": f"FE-{TAG}",
            "location_kind": "Trailer",
            "location_value": "Test",
            "type": "ABC", "size": "10lb",
            "last_inspection_date": "2026-05-01",
            "next_due_date": "2026-06-01",
            "last_status": "Pass",
        }, timeout=20,
    )
    assert create.status_code in (200, 201), create.text
    fe_id = create.json()["id"]
    r = requests.post(
        f"{BASE_URL}/api/safety/fire-extinguishers/{fe_id}/inspect",
        headers=h,
        json={
            "inspection_date": "2026-05-15",
            "status": "Fail",
            "inspector_name": "PhaseE",
            "notes": "tag missing",
        }, timeout=20,
    )
    assert r.status_code == 200, r.text
    items = _tasks_for("safety.fire_extinguishers", fe_id)
    assert len(items) >= 1
    assert items[0]["assignee_role"] == "safety"
