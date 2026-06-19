"""
test_iter409_haul_activity.py · Phase 14.3 · PM Haul Activity Tile.

Covers GET /api/dispatch/haul-activity — the read-only production
awareness endpoint that feeds the PM Hub tile.

Doctrine:
  • Project-scoped (PM passes their project_numbers).
  • Tenant-wide when no projects passed (admin/dispatch usage).
  • Derived from `dispatch_assignments` + `haul_cycles`.
  • No new collection, no new write surface.
"""
from __future__ import annotations

import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests


def _read_kv(path: Path, key: str) -> str:
    try:
        for line in path.read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        return ""
    return ""


URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
API = f"{URL}/api"


def _anon_status(path: str) -> int:
    req = urllib.request.Request(
        f"{API}{path}", method="GET",
        headers={"User-Agent": "Mozilla/5.0 (iter409 anon test)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _admin_hdrs():
    r = requests.post(
        f"{API}/admin/login",
        json={"password": "Maddix123!"},
        timeout=15,
    )
    if r.status_code == 200:
        token = r.json().get("token")
        if token:
            return {"X-Admin-Token": token}
    pytest.skip("No admin token in this env.")


def _seed_assignment(tenant, **fields):
    """Create + drive an assignment to COMPLETE so it materializes in
    haul_cycles. Returns the created assignment dict."""
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = tenant

    payload = {
        "truck_id": f"T-409-{uuid.uuid4().hex[:6]}",
        "project_number": "PROJ-409-A",
        "material": "Hot Mix Asphalt",
        "source_location": "MASCI Hot Plant 1",
        "destination": "Job Site",
        "haul_type": "Material",
    }
    payload.update(fields)

    rc = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs, json=payload, timeout=15,
    )
    assert rc.status_code == 200, rc.text
    a = rc.json()["assignment"]
    return a, hdrs


def _transition(hdrs, assignment_id, to_state, **kwargs):
    payload = {"to_state": to_state, **kwargs}
    r = requests.post(
        f"{API}/dispatch/assignments/{assignment_id}/transition",
        headers=hdrs, json=payload, timeout=15,
    )
    assert r.status_code == 200, r.text
    return r.json()


# ════════════════════════════════════════════════════════════════════
# 1. Auth gate
# ════════════════════════════════════════════════════════════════════
def test_haul_activity_requires_auth():
    assert _anon_status("/dispatch/haul-activity") == 401


# ════════════════════════════════════════════════════════════════════
# 2. Shape & defaults on an empty tenant
# ════════════════════════════════════════════════════════════════════
def test_empty_tenant_zeros():
    hdrs = _admin_hdrs()
    hdrs["X-Tenant-Id"] = f"iter409-empty-{uuid.uuid4().hex[:6]}"
    r = requests.get(f"{API}/dispatch/haul-activity", headers=hdrs, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["loads_completed_today"] == 0
    assert j["material_loads_completed_today"] == 0
    assert j["equipment_moves_completed_today"] == 0
    assert j["active_hauls"] == 0
    assert j["equipment_moves_active"] == 0
    assert j["waiting_on_plant"] == 0
    assert j["waiting_on_dump"] == 0
    assert j["breakdown_impacts"] == 0
    assert j["top_materials"] == []
    assert j["scope"] == "tenant"


# ════════════════════════════════════════════════════════════════════
# 3. Project scoping
# ════════════════════════════════════════════════════════════════════
def test_project_scope_only_counts_matching_assignments():
    tenant = f"iter409-scope-{uuid.uuid4().hex[:6]}"
    # 2 assignments on PROJ-A, 1 on PROJ-B
    a1, hdrs = _seed_assignment(tenant, project_number="PROJ-A")
    a2, _ = _seed_assignment(tenant, project_number="PROJ-A")
    a3, _ = _seed_assignment(tenant, project_number="PROJ-B")

    # Scope to PROJ-A only
    r = requests.get(
        f"{API}/dispatch/haul-activity?project_number=PROJ-A",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    assert j["scope"] == "project"
    assert j["project_numbers"] == ["PROJ-A"]
    assert j["active_hauls"] == 2

    # Multi-project scope
    r2 = requests.get(
        f"{API}/dispatch/haul-activity?project_numbers=PROJ-A,PROJ-B",
        headers=hdrs, timeout=15,
    )
    j2 = r2.json()
    assert set(j2["project_numbers"]) == {"PROJ-A", "PROJ-B"}
    assert j2["active_hauls"] == 3


# ════════════════════════════════════════════════════════════════════
# 4. Loads completed today (haul_cycles materialization)
# ════════════════════════════════════════════════════════════════════
def test_loads_completed_today_split_by_haul_type():
    tenant = f"iter409-loads-{uuid.uuid4().hex[:6]}"
    # Material haul → drive to COMPLETE
    a1, hdrs = _seed_assignment(
        tenant, project_number="PROJ-LOAD",
        material="Hot Mix Asphalt", haul_type="Material",
    )
    for st in ["ENROUTE_TO_LOAD", "AT_LOAD", "LOADING", "ENROUTE_TO_JOB",
               "ARRIVED_JOB", "DUMPING", "COMPLETE"]:
        _transition(hdrs, a1["id"], st)

    # Equipment move → drive to COMPLETE
    a2, _ = _seed_assignment(
        tenant, project_number="PROJ-LOAD", haul_type="Equipment Move",
        equipment_label="EX-99", pickup_location="415 Yard", dropoff_location="Job Site",
        material="Equipment Move",
    )
    for st in ["ENROUTE_TO_LOAD", "AT_LOAD", "LOADING", "ENROUTE_TO_JOB",
               "ARRIVED_JOB", "DUMPING", "COMPLETE"]:
        _transition(hdrs, a2["id"], st)

    r = requests.get(
        f"{API}/dispatch/haul-activity?project_number=PROJ-LOAD",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    assert j["loads_completed_today"] == 2
    assert j["material_loads_completed_today"] == 1
    assert j["equipment_moves_completed_today"] == 1
    # Completed cycles are not "active" anymore
    assert j["active_hauls"] == 0


# ════════════════════════════════════════════════════════════════════
# 5. Wait-state signals (plant, dump/site)
# ════════════════════════════════════════════════════════════════════
def test_waiting_signals_classify_by_reason():
    tenant = f"iter409-wait-{uuid.uuid4().hex[:6]}"
    a1, hdrs = _seed_assignment(tenant, project_number="PROJ-W")
    a2, _ = _seed_assignment(tenant, project_number="PROJ-W")
    # Drive both into WAITING with different reasons
    _transition(hdrs, a1["id"], "ENROUTE_TO_LOAD")
    _transition(hdrs, a1["id"], "AT_LOAD")
    _transition(hdrs, a1["id"], "WAITING", wait_reason="WAIT_ON_PLANT")
    _transition(hdrs, a2["id"], "ENROUTE_TO_LOAD")
    _transition(hdrs, a2["id"], "AT_LOAD")
    _transition(hdrs, a2["id"], "WAITING", wait_reason="WAIT_ON_DUMP")

    r = requests.get(
        f"{API}/dispatch/haul-activity?project_number=PROJ-W",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    assert j["waiting_on_plant"] == 1
    assert j["waiting_on_dump"] == 1


# ════════════════════════════════════════════════════════════════════
# 6. Breakdown impact counted
# ════════════════════════════════════════════════════════════════════
def test_breakdown_counted_in_impacts():
    tenant = f"iter409-bd-{uuid.uuid4().hex[:6]}"
    a, hdrs = _seed_assignment(tenant, project_number="PROJ-BD")
    _transition(hdrs, a["id"], "ENROUTE_TO_LOAD")
    _transition(hdrs, a["id"], "BREAKDOWN", note="Engine overheat")
    r = requests.get(
        f"{API}/dispatch/haul-activity?project_number=PROJ-BD",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    assert j["breakdown_impacts"] == 1


# ════════════════════════════════════════════════════════════════════
# 7. Top materials list
# ════════════════════════════════════════════════════════════════════
def test_top_materials_today_capped_and_sorted():
    tenant = f"iter409-top-{uuid.uuid4().hex[:6]}"
    # Make Hot Mix Asphalt the dominant material
    for _ in range(3):
        a, hdrs = _seed_assignment(
            tenant, project_number="PROJ-TOP",
            material="Hot Mix Asphalt",
        )
        for st in ["ENROUTE_TO_LOAD", "AT_LOAD", "LOADING", "ENROUTE_TO_JOB",
                   "ARRIVED_JOB", "DUMPING", "COMPLETE"]:
            _transition(hdrs, a["id"], st)
    a, _ = _seed_assignment(
        tenant, project_number="PROJ-TOP", material="Limerock",
    )
    for st in ["ENROUTE_TO_LOAD", "AT_LOAD", "LOADING", "ENROUTE_TO_JOB",
               "ARRIVED_JOB", "DUMPING", "COMPLETE"]:
        _transition(hdrs, a["id"], st)

    r = requests.get(
        f"{API}/dispatch/haul-activity?project_number=PROJ-TOP",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    assert len(j["top_materials"]) == 2
    assert j["top_materials"][0] == {"label": "Hot Mix Asphalt", "loads": 3}
    assert j["top_materials"][1] == {"label": "Limerock", "loads": 1}


# ════════════════════════════════════════════════════════════════════
# 8. Equipment Move excluded from material top-list
# ════════════════════════════════════════════════════════════════════
def test_equipment_move_not_in_top_materials():
    tenant = f"iter409-em-mat-{uuid.uuid4().hex[:6]}"
    a, hdrs = _seed_assignment(
        tenant, project_number="PROJ-EM", haul_type="Equipment Move",
        equipment_label="EX-1", material="Equipment Move",
    )
    for st in ["ENROUTE_TO_LOAD", "AT_LOAD", "LOADING", "ENROUTE_TO_JOB",
               "ARRIVED_JOB", "DUMPING", "COMPLETE"]:
        _transition(hdrs, a["id"], st)

    r = requests.get(
        f"{API}/dispatch/haul-activity?project_number=PROJ-EM",
        headers=hdrs, timeout=15,
    )
    j = r.json()
    assert j["equipment_moves_completed_today"] == 1
    assert j["top_materials"] == []  # "Equipment Move" string filtered out


# ════════════════════════════════════════════════════════════════════
# 9. Cycle doc carries haul_type
# ════════════════════════════════════════════════════════════════════
def test_haul_cycle_doc_includes_haul_type():
    tenant = f"iter409-cycle-{uuid.uuid4().hex[:6]}"
    a, hdrs = _seed_assignment(
        tenant, project_number="PROJ-CYC", haul_type="Equipment Move",
        equipment_label="LB-08", pickup_location="Vendor", dropoff_location="Shop",
        material="Equipment Move",
    )
    for st in ["ENROUTE_TO_LOAD", "AT_LOAD", "LOADING", "ENROUTE_TO_JOB",
               "ARRIVED_JOB", "DUMPING", "COMPLETE"]:
        _transition(hdrs, a["id"], st)
    # Pull the cycle via existing endpoint
    rc = requests.get(
        f"{API}/dispatch/haul-cycles?project_number=PROJ-CYC",
        headers=hdrs, timeout=15,
    )
    assert rc.status_code == 200
    cycles = rc.json().get("cycles") or []
    assert len(cycles) == 1
    cycle = cycles[0]
    assert cycle["haul_type"] == "Equipment Move"
    assert cycle["equipment_label"] == "LB-08"
    assert cycle["pickup_location"] == "Vendor"
    assert cycle["dropoff_location"] == "Shop"
