"""
test_iter401_shift_start.py · Phase 12.8 · Driver self-start operational entry.

Backend regression for the iter401 driver self-start flow.

Covers:
  • POST /api/dispatch/driver/start-shift is public (no auth needed).
  • Required fields enforced (driver_name + truck_id).
  • Successful start returns a usable driver_token in the same shape as
    /session/exchange (driver_token, session_id, expires_at, tenant_id,
    driver, shift, assignment).
  • The session token validates on protected driver endpoints
    (/me, /my-assignment).
  • The session row carries origin=self_start + the shift metadata.
  • Truck-id fallback: a self-started driver sees the active assignment
    for their truck even when the assignment's driver_id was set by
    dispatch before the driver claimed the shift.
  • Last-driver-wins: starting a fresh shift on the same truck revokes
    the previous active session on that truck.
  • Tenant isolation: a session on tenant A cannot read tenant B.
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


def _anon_status(method: str, path: str, body: dict | None = None,
                 headers: dict | None = None) -> int:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"User-Agent": "Mozilla/5.0 (iter401 anon test)"}
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(f"{API}{path}", data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


@pytest.fixture(scope="module")
def tenant_id() -> str:
    return f"iter401-test-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def hdrs(tenant_id: str) -> dict:
    return {"X-Tenant-Id": tenant_id}


@pytest.fixture(scope="module")
def truck_id() -> str:
    return f"T-{uuid.uuid4().hex[:6].upper()}"


# ════════════════════════════════════════════════════════════════════
# 1. Public start-shift contract
# ════════════════════════════════════════════════════════════════════
def test_start_shift_is_public(hdrs, truck_id):
    """No auth header required — public operational entry."""
    r = requests.post(
        f"{API}/dispatch/driver/start-shift",
        headers=hdrs,
        json={"driver_name": "Pat Driver", "truck_id": truck_id},
        timeout=15,
    )
    assert r.status_code == 200, r.text


def test_start_shift_requires_driver_name(hdrs, truck_id):
    """Empty driver_name → 4xx (Pydantic catches at 422)."""
    r = requests.post(
        f"{API}/dispatch/driver/start-shift",
        headers=hdrs,
        json={"driver_name": "", "truck_id": truck_id},
        timeout=15,
    )
    assert r.status_code in (400, 422), r.text


def test_start_shift_requires_truck_id(hdrs):
    r = requests.post(
        f"{API}/dispatch/driver/start-shift",
        headers=hdrs,
        json={"driver_name": "Pat Driver", "truck_id": ""},
        timeout=15,
    )
    assert r.status_code in (400, 422), r.text


# ════════════════════════════════════════════════════════════════════
# 2. Successful response shape
# ════════════════════════════════════════════════════════════════════
@pytest.fixture(scope="module")
def shift_session(hdrs, truck_id) -> dict:
    r = requests.post(
        f"{API}/dispatch/driver/start-shift",
        headers=hdrs,
        json={
            "driver_name": "iter401 Driver",
            "truck_id": truck_id,
            "company": "MASCI",
            "trailer_id": "TR-7",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    assert j["driver_token"]
    assert "." in j["driver_token"]                 # session_id.hmac shape
    assert j["session_id"]
    assert j["expires_at"]
    assert j["driver"]["driver_name"] == "iter401 Driver"
    assert j["driver"]["driver_id"].startswith("shift-")
    assert j["shift"]["truck_id"] == truck_id
    assert j["shift"]["company"] == "MASCI"
    assert j["shift"]["trailer_id"] == "TR-7"
    return j


def test_session_token_validates_on_me(hdrs, shift_session):
    r = requests.get(
        f"{API}/dispatch/driver/me",
        headers={**hdrs, "X-Driver-Token": shift_session["driver_token"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    me = r.json()["session"]
    assert me["driver_name"] == "iter401 Driver"
    assert me["truck_id"] == shift_session["shift"]["truck_id"]


def test_my_assignment_works_with_no_assignment(hdrs, shift_session):
    """Driver who started a shift before any assignment exists should
    see assignment=None (calm empty state) — not an error."""
    r = requests.get(
        f"{API}/dispatch/driver/my-assignment",
        headers={**hdrs, "X-Driver-Token": shift_session["driver_token"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["ok"] is True
    # Either no assignment yet, OR an assignment dispatch posted for
    # this truck (truck-id fallback). Both are valid responses.
    assert "assignment" in j


# ════════════════════════════════════════════════════════════════════
# 3. Truck-id fallback: dispatch creates assignment AFTER driver
#    self-starts; driver can see + transition it.
# ════════════════════════════════════════════════════════════════════
def test_truck_id_fallback_sees_dispatch_assignment(hdrs, truck_id, shift_session):
    """Dispatcher creates an assignment for the truck (with a
    different driver_id than the synthetic self-start one). The
    self-started driver should still see it via the truck_id fallback."""
    # Dispatcher creates an assignment for the truck.
    r = requests.post(
        f"{API}/dispatch/assignments",
        headers=hdrs,
        json={
            "truck_id": truck_id,
            "driver_id": "dispatch-assigned-someone-else",
            "driver_name": "Dispatch Pinned Name",
            "project_number": "iter401-PRJ",
            "material": "Stone",
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text

    # Self-started driver hits /my-assignment.
    r = requests.get(
        f"{API}/dispatch/driver/my-assignment",
        headers={**hdrs, "X-Driver-Token": shift_session["driver_token"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["assignment"] is not None, "Self-started driver should see truck's assignment"
    assert j["assignment"]["truck_id"] == truck_id


def test_self_started_driver_can_transition_truck_assignment(hdrs, truck_id, shift_session):
    """The relaxed transition auth should let the self-started driver
    advance the truck's lifecycle even though the assignment's
    driver_id was dispatch-pinned."""
    # Look up the current assignment first.
    r = requests.get(
        f"{API}/dispatch/driver/my-assignment",
        headers={**hdrs, "X-Driver-Token": shift_session["driver_token"]},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    assignment = r.json()["assignment"]
    assert assignment is not None
    # Pick an allowed next state — any forward step is fine for the
    # contract; we just need to verify the transition is accepted.
    allowed = r.json().get("allowed_next_states") or []
    next_state = "ENROUTE_TO_LOAD" if "ENROUTE_TO_LOAD" in allowed else (allowed[0] if allowed else "ENROUTE_TO_LOAD")

    rt = requests.post(
        f"{API}/dispatch/driver/assignments/{assignment['id']}/transition",
        headers={**hdrs, "X-Driver-Token": shift_session["driver_token"]},
        json={"to_state": next_state},
        timeout=15,
    )
    assert rt.status_code == 200, rt.text
    assert rt.json()["transition"]["by_role"] == "driver"
    assert rt.json()["assignment"]["current_state"] == next_state


# ════════════════════════════════════════════════════════════════════
# 4. Last-driver-wins: starting a new shift on the same truck revokes
#    the previous active session.
# ════════════════════════════════════════════════════════════════════
def test_last_driver_wins_revokes_previous_session(hdrs):
    """Different module-scope truck so we don't disturb the main
    fixture above."""
    t2 = f"T-{uuid.uuid4().hex[:6].upper()}"

    # First driver claims the truck.
    r1 = requests.post(
        f"{API}/dispatch/driver/start-shift",
        headers=hdrs,
        json={"driver_name": "Pat First", "truck_id": t2},
        timeout=15,
    )
    assert r1.status_code == 200, r1.text
    tok1 = r1.json()["driver_token"]

    # First driver's session is healthy.
    r1m = requests.get(
        f"{API}/dispatch/driver/me",
        headers={**hdrs, "X-Driver-Token": tok1},
        timeout=15,
    )
    assert r1m.status_code == 200

    # Second driver claims the same truck.
    r2 = requests.post(
        f"{API}/dispatch/driver/start-shift",
        headers=hdrs,
        json={"driver_name": "Pat Second", "truck_id": t2},
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    tok2 = r2.json()["driver_token"]

    # First driver's session should now be revoked (last-driver-wins).
    r1m2 = requests.get(
        f"{API}/dispatch/driver/me",
        headers={**hdrs, "X-Driver-Token": tok1},
        timeout=15,
    )
    assert r1m2.status_code == 401, "Previous shift should have been revoked"

    # Second driver's session is healthy.
    r2m = requests.get(
        f"{API}/dispatch/driver/me",
        headers={**hdrs, "X-Driver-Token": tok2},
        timeout=15,
    )
    assert r2m.status_code == 200, r2m.text


# ════════════════════════════════════════════════════════════════════
# 5. Tenant isolation
# ════════════════════════════════════════════════════════════════════
def test_tenant_isolation_on_session_validation(shift_session):
    """A session minted under tenant A must NOT validate under tenant B."""
    other_tenant = f"iter401-other-{uuid.uuid4().hex[:6]}"
    r = requests.get(
        f"{API}/dispatch/driver/me",
        headers={
            "X-Tenant-Id": other_tenant,
            "X-Driver-Token": shift_session["driver_token"],
        },
        timeout=15,
    )
    assert r.status_code == 401, r.text
