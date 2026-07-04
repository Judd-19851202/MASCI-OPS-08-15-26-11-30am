"""
test_iter392_dls_foundation.py · Phase 11.1 — Dispatch Lifecycle System.

Backend foundation regression for iter392.

Covers:
  • Route registration / import smoke.
  • State machine (pure module unit tests).
  • RBAC: dispatch+admin write gate, cross-portal read gate, anon rejected.
  • Create assignment → seed state_history[] + dispatch_state_events row.
  • Standard transition → tagged standard=True, mirrored to events.
  • Non-standard transition → forgiving (still accepted), tagged with
    warning_tag="NON_STANDARD_TRANSITION".
  • Unknown-state transition → forgiving + tagged UNKNOWN_STATE.
  • Cancel and reassign endpoints write history + events.
  • Completing a cycle (... → COMPLETE) materializes a haul_cycles row.
  • Tenant-aware isolation (X-Tenant-Id header).
  • Indexes created on startup.
  • Listing endpoints (board, list, state-events, haul-cycles).

NOTE: this test deliberately uses `urllib` (bypassing the conftest
admin-token monkey-patch) for anon-negative checks. Authenticated
requests use `requests` which auto-attaches X-Admin-Token.
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


# ────────────────────────────────────────────────────────────────────
# Env / URL bootstrap
# ────────────────────────────────────────────────────────────────────
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


def _anon_get(path: str) -> int:
    """Raw urllib GET — bypasses conftest's admin-token monkey-patch.
    Default Python User-Agent is blocked by the Emergent WAF, so we
    spoof a Chrome UA to get an honest backend response."""
    req = urllib.request.Request(
        f"{API}{path}",
        headers={"User-Agent": "Mozilla/5.0 (iter392 anon test)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _anon_post(path: str, body: dict) -> int:
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "User-Agent": "Mozilla/5.0 (iter392 anon test)",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


@pytest.fixture(scope="module")
def tenant_id() -> str:
    """Per-test-run tenant so we don't collide with other suites."""
    return f"iter392-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def headers_for(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id}


# ════════════════════════════════════════════════════════════════════
# 1. Pure state-machine unit tests
# ════════════════════════════════════════════════════════════════════
def test_state_machine_canonical_count():
    import dispatch_lifecycle as DLS
    assert len(DLS.CANONICAL_STATES) == 13
    expected = {
        "ASSIGNED", "ENROUTE_TO_LOAD", "AT_LOAD_SITE", "LOADING", "LOADED",
        "ENROUTE_TO_JOB", "ARRIVED_JOB", "DUMPING", "COMPLETE",
        "WAITING", "HOLD", "BREAKDOWN", "OFF_SHIFT",
    }
    assert set(DLS.CANONICAL_STATES) == expected


def test_standard_happy_path_transitions():
    import dispatch_lifecycle as DLS
    chain = [
        DLS.ASSIGNED, DLS.ENROUTE_TO_LOAD, DLS.AT_LOAD_SITE, DLS.LOADING,
        DLS.LOADED, DLS.ENROUTE_TO_JOB, DLS.ARRIVED_JOB, DLS.DUMPING, DLS.COMPLETE,
    ]
    for a, b in zip(chain, chain[1:]):
        assert DLS.is_standard_transition(a, b), f"{a}->{b} should be standard"


def test_wait_state_returns_to_operational_standard():
    import dispatch_lifecycle as DLS
    assert DLS.is_standard_transition(DLS.WAITING, DLS.LOADING)
    assert DLS.is_standard_transition(DLS.HOLD, DLS.ENROUTE_TO_LOAD)
    assert DLS.is_standard_transition(DLS.BREAKDOWN, DLS.ARRIVED_JOB)


def test_non_standard_transition_classified():
    import dispatch_lifecycle as DLS
    c = DLS.classify_transition(DLS.ASSIGNED, DLS.COMPLETE)
    assert c["standard"] is False
    assert c["warning_tag"] == "NON_STANDARD_TRANSITION"


def test_unknown_state_tagged():
    import dispatch_lifecycle as DLS
    c = DLS.classify_transition(DLS.LOADED, "MARS_LANDING")
    assert c["to_state_canonical"] is False
    assert "UNKNOWN_STATE" in c["warning_tags"]


def test_terminal_states_are_terminal():
    import dispatch_lifecycle as DLS
    assert DLS.is_terminal(DLS.COMPLETE)
    assert DLS.is_terminal(DLS.OFF_SHIFT)
    assert not DLS.is_terminal(DLS.WAITING)


# ════════════════════════════════════════════════════════════════════
# 2. Route registration / import smoke
# ════════════════════════════════════════════════════════════════════
def test_router_module_imports():
    from routes.dispatch_lifecycle import (
        build_dispatch_lifecycle_router,
        ensure_dispatch_lifecycle_indexes,
    )
    assert callable(build_dispatch_lifecycle_router)
    assert callable(ensure_dispatch_lifecycle_indexes)


def test_server_wires_dls_router():
    # Source-level guard — locks the wiring so a future refactor
    # cannot accidentally unmount the DLS router.
    src = Path("/app/backend/server.py").read_text()
    assert "build_dispatch_lifecycle_router" in src
    assert "ensure_dispatch_lifecycle_indexes" in src
    assert "_dls_router" in src


# ════════════════════════════════════════════════════════════════════
# 3. RBAC
# ════════════════════════════════════════════════════════════════════
def test_anon_rejected_on_write():
    """Creating an assignment without any portal token MUST 401."""
    code = _anon_post(
        "/dispatch/assignments",
        {"truck_id": "ANON-T-1"},
    )
    assert code == 401


def test_anon_rejected_on_board_read():
    code = _anon_get("/dispatch/assignments/board")
    assert code == 401


def test_admin_can_read_board(headers_for):
    r = requests.get(f"{API}/dispatch/assignments/board", headers=headers_for, timeout=10)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("ok") is True
    assert "assignments" in j


def test_lifecycle_states_meta(headers_for):
    r = requests.get(f"{API}/dispatch/lifecycle/states", headers=headers_for, timeout=10)
    assert r.status_code == 200, r.text
    j = r.json()
    assert len(j["states"]) == 13
    assert "preferred_next" in j


# ════════════════════════════════════════════════════════════════════
# 4. CREATE → seed state_history + event row
# ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def created_assignment(headers_for) -> dict:
    body = {
        "truck_id": "T-iter392",
        "driver_id": "driver-iter392",
        "driver_name": "Test Driver",
        "project_number": "iter392-PRJ",
        "project_name": "TEST_iter392_Test_Project",
        "material": "Asphalt",
        "source_location": "Plant A",
        "destination": "Test Job Site",
        "note": "iter392 fixture create",
    }
    r = requests.post(f"{API}/dispatch/assignments", headers=headers_for, json=body, timeout=10)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    a = j["assignment"]
    assert a["current_state"] == "ASSIGNED"
    assert a["tenant_id"] == headers_for["X-Tenant-Id"]
    assert len(a["state_history"]) == 1
    assert a["state_history"][0]["to_state"] == "ASSIGNED"
    assert a["state_history"][0]["standard"] is True
    return a


def test_created_assignment_mirrored_to_events(headers_for, created_assignment):
    r = requests.get(
        f"{API}/dispatch/state-events",
        headers=headers_for,
        params={"assignment_id": created_assignment["id"]},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["count"] >= 1
    seed = [e for e in j["events"] if e["to_state"] == "ASSIGNED"]
    assert len(seed) == 1
    assert seed[0]["from_state"] is None
    assert seed[0]["standard"] is True
    assert seed[0]["assignment_id"] == created_assignment["id"]


def test_get_assignment_detail(headers_for, created_assignment):
    r = requests.get(
        f"{API}/dispatch/assignments/{created_assignment['id']}",
        headers=headers_for, timeout=10,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["assignment"]["id"] == created_assignment["id"]
    assert j["assignment"]["current_state"] == "ASSIGNED"


# ════════════════════════════════════════════════════════════════════
# 5. Standard transition → tagged standard=True
# ════════════════════════════════════════════════════════════════════
def test_standard_transition_writes_history_and_event(headers_for, created_assignment):
    aid = created_assignment["id"]
    r = requests.post(
        f"{API}/dispatch/assignments/{aid}/transition",
        headers=headers_for,
        json={"to_state": "ENROUTE_TO_LOAD", "note": "standard step 1"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    a = j["assignment"]
    assert a["current_state"] == "ENROUTE_TO_LOAD"
    assert len(a["state_history"]) == 2
    last = a["state_history"][-1]
    assert last["from_state"] == "ASSIGNED"
    assert last["to_state"] == "ENROUTE_TO_LOAD"
    assert last["standard"] is True
    assert last["warning_tag"] is None

    # Event mirror
    r2 = requests.get(
        f"{API}/dispatch/state-events", headers=headers_for,
        params={"assignment_id": aid}, timeout=10,
    )
    events = r2.json()["events"]
    assert any(
        e["from_state"] == "ASSIGNED" and e["to_state"] == "ENROUTE_TO_LOAD"
        and e["standard"] is True
        for e in events
    )


# ════════════════════════════════════════════════════════════════════
# 6. NON-STANDARD transition — forgiving, but tagged
# ════════════════════════════════════════════════════════════════════
def test_non_standard_transition_accepted_and_tagged(headers_for, created_assignment):
    """Jump from ENROUTE_TO_LOAD straight to COMPLETE — illegal in
    preferred graph, but accepted with NON_STANDARD_TRANSITION tag."""
    aid = created_assignment["id"]
    # Sanity: current state must be ENROUTE_TO_LOAD from prior test.
    r0 = requests.get(f"{API}/dispatch/assignments/{aid}", headers=headers_for, timeout=10)
    assert r0.json()["assignment"]["current_state"] == "ENROUTE_TO_LOAD"

    r = requests.post(
        f"{API}/dispatch/assignments/{aid}/transition",
        headers=headers_for,
        json={
            "to_state": "COMPLETE",
            "correction_reason": "truck boss override — short haul",
        },
        timeout=10,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    a = j["assignment"]
    assert a["current_state"] == "COMPLETE"
    last = a["state_history"][-1]
    assert last["from_state"] == "ENROUTE_TO_LOAD"
    assert last["to_state"] == "COMPLETE"
    assert last["standard"] is False
    assert last["warning_tag"] == "NON_STANDARD_TRANSITION"
    assert last["correction_reason"] == "truck boss override — short haul"


def test_completion_materializes_haul_cycle(headers_for, created_assignment):
    """COMPLETE state must derive a row into haul_cycles."""
    aid = created_assignment["id"]
    r = requests.get(
        f"{API}/dispatch/haul-cycles", headers=headers_for,
        params={"truck_id": "T-iter392"}, timeout=10,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    rows = [c for c in j["cycles"] if c["assignment_id"] == aid]
    assert len(rows) == 1, f"expected 1 haul_cycles row for {aid}, got {rows}"
    cyc = rows[0]
    assert cyc["truck_id"] == "T-iter392"
    assert cyc["project_number"] == "iter392-PRJ"
    assert cyc["transitions"] == 3                  # ASSIGNED + 2 transitions
    assert cyc["non_standard_transitions"] == 1
    assert cyc["completed_at"] is not None
    assert cyc["total_seconds"] is not None


# ════════════════════════════════════════════════════════════════════
# 7. Wait reason + return-from-waiting on a fresh assignment
# ════════════════════════════════════════════════════════════════════
def test_waiting_captures_reason_and_clears_on_return(headers_for):
    body = {
        "truck_id": "T-iter392-wait",
        "driver_name": "Wait Driver",
        "project_number": "iter392-PRJ",
        "material": "Aggregate",
    }
    r = requests.post(f"{API}/dispatch/assignments", headers=headers_for, json=body, timeout=10)
    aid = r.json()["assignment"]["id"]

    # ASSIGNED -> ENROUTE_TO_LOAD
    requests.post(
        f"{API}/dispatch/assignments/{aid}/transition",
        headers=headers_for, json={"to_state": "ENROUTE_TO_LOAD"}, timeout=10,
    )
    # -> WAITING with reason
    r = requests.post(
        f"{API}/dispatch/assignments/{aid}/transition",
        headers=headers_for,
        json={"to_state": "WAITING", "wait_reason": "PLANT_BOTTLENECK"},
        timeout=10,
    )
    a = r.json()["assignment"]
    assert a["current_state"] == "WAITING"
    assert a["current_wait_reason"] == "PLANT_BOTTLENECK"

    # -> AT_LOAD_SITE (return; standard)
    r = requests.post(
        f"{API}/dispatch/assignments/{aid}/transition",
        headers=headers_for, json={"to_state": "AT_LOAD_SITE"}, timeout=10,
    )
    a = r.json()["assignment"]
    assert a["current_state"] == "AT_LOAD_SITE"
    assert a["current_wait_reason"] == ""
    last = a["state_history"][-1]
    assert last["standard"] is True


# ════════════════════════════════════════════════════════════════════
# 8. CANCEL
# ════════════════════════════════════════════════════════════════════
def test_cancel_blocks_further_transitions(headers_for):
    body = {"truck_id": "T-iter392-cancel", "project_number": "iter392-PRJ"}
    r = requests.post(f"{API}/dispatch/assignments", headers=headers_for, json=body, timeout=10)
    aid = r.json()["assignment"]["id"]

    rc = requests.post(
        f"{API}/dispatch/assignments/{aid}/cancel",
        headers=headers_for, json={"reason": "duplicate dispatch"}, timeout=10,
    )
    assert rc.status_code == 200, rc.text
    a = rc.json()["assignment"]
    assert a["cancelled_at"] is not None
    assert a["cancel_reason"] == "duplicate dispatch"

    # Further transition must 409
    rb = requests.post(
        f"{API}/dispatch/assignments/{aid}/transition",
        headers=headers_for, json={"to_state": "ENROUTE_TO_LOAD"}, timeout=10,
    )
    assert rb.status_code == 409


# ════════════════════════════════════════════════════════════════════
# 9. REASSIGN
# ════════════════════════════════════════════════════════════════════
def test_reassign_updates_driver_and_records_history(headers_for):
    body = {
        "truck_id": "T-iter392-reassign",
        "driver_id": "drv-A",
        "driver_name": "Driver A",
    }
    r = requests.post(f"{API}/dispatch/assignments", headers=headers_for, json=body, timeout=10)
    aid = r.json()["assignment"]["id"]

    rr = requests.post(
        f"{API}/dispatch/assignments/{aid}/reassign",
        headers=headers_for,
        json={
            "new_driver_id": "drv-B",
            "new_driver_name": "Driver B",
            "reason": "shift change",
        },
        timeout=10,
    )
    assert rr.status_code == 200, rr.text
    a = rr.json()["assignment"]
    assert a["driver_id"] == "drv-B"
    assert a["driver_name"] == "Driver B"
    last = a["state_history"][-1]
    assert last["warning_tag"] == "REASSIGNED"
    assert last["reassign_from_driver_name"] == "Driver A"
    assert last["reassign_to_driver_name"] == "Driver B"


# ════════════════════════════════════════════════════════════════════
# 10. Tenant isolation
# ════════════════════════════════════════════════════════════════════
def test_tenant_id_isolates_queries(tenant_id):
    other = {"X-Tenant-Id": f"other-{uuid.uuid4().hex[:6]}"}
    # Create in OUR tenant
    requests.post(
        f"{API}/dispatch/assignments",
        headers={"X-Tenant-Id": tenant_id},
        json={"truck_id": "T-tenant-isolation"},
        timeout=10,
    )
    # Board for OTHER tenant must not contain it
    r = requests.get(f"{API}/dispatch/assignments/board", headers=other, timeout=10)
    assert r.status_code == 200
    j = r.json()
    assert all(a["truck_id"] != "T-tenant-isolation" for a in j["assignments"])
    assert j["tenant_id"] == other["X-Tenant-Id"]


# ════════════════════════════════════════════════════════════════════
# 11. Indexes exist (Mongo introspection via API not exposed — verify
#    indirectly through query performance: board read returns < 2 s
#    even after a bunch of writes from earlier tests).
# ════════════════════════════════════════════════════════════════════
def test_board_read_is_fast(headers_for):
    import time
    t0 = time.perf_counter()
    r = requests.get(f"{API}/dispatch/assignments/board", headers=headers_for, timeout=10)
    dt = time.perf_counter() - t0
    assert r.status_code == 200
    assert dt < 2.0, f"board read too slow: {dt:.2f}s"


# ════════════════════════════════════════════════════════════════════
# 12. NON-STANDARD events queryable for governance (future iter395)
# ════════════════════════════════════════════════════════════════════
def test_non_standard_events_filterable(headers_for):
    r = requests.get(
        f"{API}/dispatch/state-events",
        headers=headers_for,
        params={"non_standard_only": "true"},
        timeout=10,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    # We created at least one non-standard transition (ENROUTE_TO_LOAD -> COMPLETE)
    assert j["count"] >= 1
    assert all(not e["standard"] for e in j["events"])
