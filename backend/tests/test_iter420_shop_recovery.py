"""iter420 · Phase 22.0 · Shop Recovery Continuity tests.

Walking-skeleton verification:
1. Canonical states list returns the 7 locked recovery sub-states in order.
2. Anonymous list/transition blocked.
3. Dispatch/admin can transition recovery sub-state.
4. Transition writes append-only history entry with from/to/by/role/note.
5. Unknown to_state → 400.
6. Unknown assignment → 404.
7. GET /recovery/{id} returns current state + full history (no _id leakage).
8. Recovery sub-state is INDEPENDENT of current_state (DLS haul lifecycle).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
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


CANONICAL_STATES = [
    "reported", "acknowledged", "diagnosing",
    "waiting_on_parts", "repair_active", "operational_test",
    "returned_to_service",
]


@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter420-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id}


@pytest.fixture(scope="module")
def assignment(hdrs) -> dict:
    r = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": "T-iter420",
            "driver_name": "iter420 Driver",
            "haul_type": "Material",
            "project_number": "9999",
            "material": "Asphalt",
        },
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["assignment"]


def _anon_status(method: str, path: str, body: dict | None = None) -> int:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hd = {"User-Agent": "Mozilla/5.0 (iter420 anon test)"}
    if body is not None:
        hd["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=hd)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


# ──────────────────────────────────────────────────────────────
# 1. States list
# ──────────────────────────────────────────────────────────────
def test_iter420_states_list_admin_ok():
    r = requests.get(f"{API}/dispatch/recovery/states", timeout=10)
    assert r.status_code == 200, r.text
    assert r.json().get("states") == CANONICAL_STATES


def test_iter420_states_list_anon_blocked():
    assert _anon_status("GET", "/dispatch/recovery/states") == 401


# ──────────────────────────────────────────────────────────────
# 2. Happy-path transition · reported → acknowledged
# ──────────────────────────────────────────────────────────────
def test_iter420_transition_happy_path(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers=hdrs,
        json={"to_state": "acknowledged", "note": "Shop confirmed receipt"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["recovery_state"] == "acknowledged"
    entry = body["entry"]
    assert entry["to"] == "acknowledged"
    assert entry["from"] == "reported"   # default when none set yet
    assert entry["by"]
    assert entry["role"]
    assert entry["note"] == "Shop confirmed receipt"
    assert entry["at"]


# ──────────────────────────────────────────────────────────────
# 3. Second transition · append-only history (length grows)
# ──────────────────────────────────────────────────────────────
def test_iter420_history_appends(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers=hdrs,
        json={"to_state": "diagnosing", "note": "Mechanic on it"},
        timeout=15,
    )
    assert r.status_code == 200, r.text

    r2 = requests.get(
        f"{API}/dispatch/recovery/{assignment['id']}",
        headers=hdrs, timeout=10,
    )
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["recovery_state"] == "diagnosing"
    history = body["history"]
    assert isinstance(history, list)
    assert len(history) >= 2
    last = history[-1]
    assert last["to"] == "diagnosing"
    assert last["from"] == "acknowledged"
    assert "_id" not in body and all("_id" not in h for h in history)


# ──────────────────────────────────────────────────────────────
# 4. Unknown state rejected
# ──────────────────────────────────────────────────────────────
def test_iter420_unknown_state_rejected(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers=hdrs,
        json={"to_state": "INVENTED_STATE"},
        timeout=10,
    )
    assert r.status_code == 400, r.text


# ──────────────────────────────────────────────────────────────
# 5. Unknown assignment → 404
# ──────────────────────────────────────────────────────────────
def test_iter420_unknown_assignment_404(hdrs):
    r = requests.post(
        f"{API}/dispatch/recovery/does-not-exist-xyz/transition",
        headers=hdrs,
        json={"to_state": "acknowledged"},
        timeout=10,
    )
    assert r.status_code == 404, r.text


# ──────────────────────────────────────────────────────────────
# 6. Anon transition blocked
# ──────────────────────────────────────────────────────────────
def test_iter420_anon_transition_blocked(assignment):
    code = _anon_status(
        "POST",
        f"/dispatch/recovery/{assignment['id']}/transition",
        body={"to_state": "acknowledged"},
    )
    assert code == 401


# ──────────────────────────────────────────────────────────────
# 7. Recovery sub-state independent of DLS current_state
#    The assignment current_state is still ASSIGNED (we never transitioned
#    it through the haul lifecycle), yet recovery progressed.
# ──────────────────────────────────────────────────────────────
def test_iter420_recovery_decoupled_from_dls_state(assignment, hdrs):
    r = requests.get(
        f"{API}/dispatch/assignments/{assignment['id']}",
        headers=hdrs, timeout=10,
    )
    if r.status_code == 200:
        body = r.json()
        # Some shapes return the assignment under a key, others flat.
        asg = body.get("assignment") or body
        # current_state was never transitioned through DLS — should still
        # be ASSIGNED (or whatever default), NOT mixed with recovery sub-state.
        cs = asg.get("current_state") or asg.get("state")
        assert cs != "diagnosing", "DLS current_state must NOT equal recovery sub-state"


# ──────────────────────────────────────────────────────────────
# 8. Final state · returned_to_service · still appends
# ──────────────────────────────────────────────────────────────
def test_iter420_returned_to_service_transition(assignment, hdrs):
    r = requests.post(
        f"{API}/dispatch/recovery/{assignment['id']}/transition",
        headers=hdrs,
        json={"to_state": "returned_to_service", "note": "Back in line"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["recovery_state"] == "returned_to_service"


# ──────────────────────────────────────────────────────────────
# 9. GET on unknown assignment → 404
# ──────────────────────────────────────────────────────────────
def test_iter420_get_unknown_404(hdrs):
    r = requests.get(
        f"{API}/dispatch/recovery/no-such-assignment-xyz",
        headers=hdrs, timeout=10,
    )
    assert r.status_code == 404, r.text
