"""OMEGA · Phase 1A · iter451 — OC-001 Incident Lifecycle regression suite.

Two layers:
  1. Pure-Python state-machine unit tests (no I/O).
  2. Live HTTP integration tests against the running backend, mirroring
     the existing ``test_incidents.py`` pattern (requests + REACT_APP_BACKEND_URL).

Run::

    cd /app/backend && python -m pytest tests/test_iter451_incident_lifecycle.py -q
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time

import pytest
import requests
from dotenv import load_dotenv

from lib.workflow_state_machine import (
    INCIDENT_DEFAULT_STATE,
    INCIDENT_STATES,
    validate_incident_transition,
)

# ─────────────────────────────────────────────────────────────────
# State-machine unit tests (pure Python, no HTTP)
# ─────────────────────────────────────────────────────────────────
def test_states_canonical_order():
    assert INCIDENT_DEFAULT_STATE == "OPEN"
    assert INCIDENT_STATES == (
        "OPEN", "UNDER_INVESTIGATION", "CORRECTIVE_ACTION_REQUIRED",
        "PENDING_CLOSURE", "CLOSED",
    )


def test_open_to_investigation_safety_allowed():
    ok, err = validate_incident_transition(
        from_state="OPEN",
        to_state="UNDER_INVESTIGATION",
        actor={"_actor_kind": "safety_user"},
    )
    assert ok and err == ""


def test_open_to_closed_forbidden_skipping_states():
    ok, err = validate_incident_transition(
        from_state="OPEN",
        to_state="CLOSED",
        actor={"_actor_kind": "safety_user"},
        evidence={
            "investigation_complete": True,
            "capa_complete": True,
            "safety_review_complete": True,
        },
    )
    assert not ok
    assert err == "transition_not_allowed"


def test_closure_requires_three_attestations():
    ok, err = validate_incident_transition(
        from_state="PENDING_CLOSURE",
        to_state="CLOSED",
        actor={"_actor_kind": "safety_user"},
        evidence={"investigation_complete": True, "capa_complete": True},
    )
    assert not ok
    assert err.startswith("closure_attestation_missing:safety_review_complete")


def test_osha_recordable_closure_requires_extra_ack():
    ok, err = validate_incident_transition(
        from_state="PENDING_CLOSURE",
        to_state="CLOSED",
        actor=True,  # super_admin
        evidence={
            "investigation_complete": True,
            "capa_complete": True,
            "safety_review_complete": True,
        },
        osha_recordable=True,
    )
    assert not ok
    assert err == "closure_attestation_missing:osha_recordable_ack"


def test_reopen_requires_reason():
    ok, err = validate_incident_transition(
        from_state="CLOSED",
        to_state="UNDER_INVESTIGATION",
        actor=True,
        reason="",
    )
    assert not ok
    assert err == "reopen_reason_required"


def test_reopen_with_reason_allowed_for_super_admin():
    ok, err = validate_incident_transition(
        from_state="CLOSED",
        to_state="UNDER_INVESTIGATION",
        actor=True,
        reason="New evidence surfaced from witness re-interview.",
    )
    assert ok and err == ""


def test_pm_actor_cannot_transition():
    ok, err = validate_incident_transition(
        from_state="OPEN",
        to_state="UNDER_INVESTIGATION",
        actor={"role": "pm"},
    )
    assert not ok
    assert err == "role_not_authorized"


def test_full_happy_path_state_sequence():
    """Walk OPEN → UNDER_INVESTIGATION → CORRECTIVE_ACTION_REQUIRED →
    PENDING_CLOSURE → CLOSED using a Super Admin actor."""
    sequence = [
        ("OPEN", "UNDER_INVESTIGATION"),
        ("UNDER_INVESTIGATION", "CORRECTIVE_ACTION_REQUIRED"),
        ("CORRECTIVE_ACTION_REQUIRED", "PENDING_CLOSURE"),
        ("PENDING_CLOSURE", "CLOSED"),
    ]
    for f, t in sequence:
        ok, err = validate_incident_transition(
            from_state=f,
            to_state=t,
            actor=True,
            evidence={
                "investigation_complete": True,
                "capa_complete": True,
                "safety_review_complete": True,
                "osha_recordable_ack": True,
            },
        )
        assert ok, f"{f}→{t} blocked unexpectedly: {err}"


# ─────────────────────────────────────────────────────────────────
# Live integration — uses the running preview backend, mirroring
# /app/backend/tests/test_incidents.py
# ─────────────────────────────────────────────────────────────────
load_dotenv("/app/backend/.env")


def _base_url() -> str:
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


BASE_URL = _base_url()
API = f"{BASE_URL}/api"


def _admin_token() -> str:
    """Reconstruct the deterministic admin portal token from ADMIN_PASSWORD."""
    from server import _admin_token_for  # type: ignore
    pw = os.environ.get("ADMIN_PASSWORD", "")
    return _admin_token_for(pw) if pw else ""


@pytest.fixture(scope="module")
def admin_headers():
    tok = _admin_token()
    if not tok:
        pytest.skip("ADMIN_PASSWORD not configured")
    # Clear any prior session_activity row so session_timeout middleware
    # treats this run as a fresh login.
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        async def _clear():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            th = hashlib.sha256(tok.encode()).hexdigest()
            await db.session_activity.delete_many({"token_hash": th})
        asyncio.get_event_loop().run_until_complete(_clear()) if False else asyncio.run(_clear())
    except Exception:
        pass
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


@pytest.fixture
def fresh_incident(admin_headers):
    """Create an incident, yield its id, delete on teardown."""
    payload = {
        "project_name": "iter451 lifecycle test",
        "project_number": "TEST-451",
        "location": "Lab",
        "incident_date": "2026-06-01",
        "incident_time": "10:00",
        "reported_date": "2026-06-01",
        "reported_by": "pytest harness",
        "incident_type": "Near Miss",
        "severity": "low",
        "osha_recordable": "No",
        "description": "iter451 seed",
    }
    r = requests.post(f"{API}/incidents", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    incident_id = r.json()["id"]
    yield incident_id
    requests.delete(f"{API}/incidents/{incident_id}",
                    headers=admin_headers, timeout=15)
    # Purge audit rows so the collection stays clean.
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        async def _purge():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            await db.workflow_state_events.delete_many(
                {"workflow": "incident", "record_id": incident_id}
            )
        asyncio.run(_purge())
    except Exception:
        pass


@pytest.fixture
def fresh_osha_incident(admin_headers):
    payload = {
        "project_name": "iter451 OSHA lifecycle test",
        "project_number": "TEST-451-OSHA",
        "location": "Lab",
        "incident_date": "2026-06-01",
        "incident_time": "10:00",
        "reported_date": "2026-06-01",
        "reported_by": "pytest harness",
        "incident_type": "Recordable Injury",
        "severity": "medical",
        "osha_recordable": "Yes",
        "description": "iter451 OSHA seed",
    }
    r = requests.post(f"{API}/incidents", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    incident_id = r.json()["id"]
    yield incident_id
    requests.delete(f"{API}/incidents/{incident_id}",
                    headers=admin_headers, timeout=15)
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        async def _purge():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            await db.workflow_state_events.delete_many(
                {"workflow": "incident", "record_id": incident_id}
            )
        asyncio.run(_purge())
    except Exception:
        pass


def test_transition_unauthenticated_rejected(fresh_incident):
    # /app/backend/tests/conftest.py auto-attaches X-Admin-Token to every
    # requests call. Explicitly send an empty admin token to simulate the
    # unauthenticated case (the safety/pm gate falls through to 401).
    r = requests.post(
        f"{API}/incidents/{fresh_incident}/transition",
        json={"to_state": "UNDER_INVESTIGATION"},
        headers={"X-Admin-Token": "", "Content-Type": "application/json"},
        timeout=15,
    )
    assert r.status_code == 401, f"got {r.status_code}: {r.text[:200]}"


def test_lifecycle_view_initial_open(fresh_incident, admin_headers):
    r = requests.get(
        f"{API}/incidents/{fresh_incident}/lifecycle",
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["workflow"] == "incident"
    assert body["lifecycle_state"] == "OPEN"
    assert body["actor_role"] == "super_admin"
    legal = [t["to_state"] for t in body["legal_next_states"]
             if t["allowed_for_actor"]]
    assert legal == ["UNDER_INVESTIGATION"]


def test_full_lifecycle_with_reopen(fresh_incident, admin_headers):
    base = f"{API}/incidents/{fresh_incident}/transition"

    # Step 1 → UNDER_INVESTIGATION
    r = requests.post(base, json={"to_state": "UNDER_INVESTIGATION"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    assert r.json()["from_state"] == "OPEN"

    # Step 2 → CORRECTIVE_ACTION_REQUIRED
    r = requests.post(base, json={"to_state": "CORRECTIVE_ACTION_REQUIRED"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # Step 3 → PENDING_CLOSURE
    r = requests.post(base, json={"to_state": "PENDING_CLOSURE"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # Step 4a → CLOSED w/o attestation = 422
    r = requests.post(base, json={"to_state": "CLOSED"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"].startswith("closure_attestation_missing")

    # Step 4b → CLOSED with attestations
    r = requests.post(
        base,
        json={
            "to_state": "CLOSED",
            "evidence": {
                "investigation_complete": True,
                "capa_complete": True,
                "safety_review_complete": True,
            },
        },
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200, r.text

    # Step 5 → REOPEN without reason = 422
    r = requests.post(base, json={"to_state": "UNDER_INVESTIGATION"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "reopen_reason_required"

    # Step 5b → REOPEN with reason
    r = requests.post(
        base,
        json={"to_state": "UNDER_INVESTIGATION",
              "reason": "New witness statement contradicts initial findings."},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200, r.text

    # Verify audit history — 5 lifecycle transitions written.
    # iter452.5 introduces delivery-evidence rows (notification_*,
    # revision_link_*) in the same audit collection; filter them out
    # for the transition-count assertion.
    r = requests.get(
        f"{API}/incidents/{fresh_incident}/state-events",
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    lifecycle_rows = [
        x for x in rows
        if not (x.get("evidence") or {}).get("delivery_event")
    ]
    assert len(lifecycle_rows) == 5
    # Newest first
    assert lifecycle_rows[0]["to_state"] == "UNDER_INVESTIGATION"
    assert lifecycle_rows[0]["from_state"] == "CLOSED"
    assert lifecycle_rows[0]["reason"].startswith("New witness")
    # All transitions carry actor info
    for row in lifecycle_rows:
        assert row["actor_role"] in {"admin", "super_admin", "safety"}
        assert "at" in row


def test_osha_closure_requires_extra_ack(fresh_osha_incident, admin_headers):
    base = f"{API}/incidents/{fresh_osha_incident}/transition"
    for nxt in ("UNDER_INVESTIGATION", "CORRECTIVE_ACTION_REQUIRED",
                "PENDING_CLOSURE"):
        r = requests.post(base, json={"to_state": nxt},
                          headers=admin_headers, timeout=15)
        assert r.status_code == 200, f"{nxt}: {r.text}"

    # Without osha_recordable_ack → 422
    r = requests.post(
        base,
        json={
            "to_state": "CLOSED",
            "evidence": {
                "investigation_complete": True,
                "capa_complete": True,
                "safety_review_complete": True,
            },
        },
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 422
    assert "osha_recordable_ack" in r.json()["detail"]["code"]

    # With ack → 200
    r = requests.post(
        base,
        json={
            "to_state": "CLOSED",
            "evidence": {
                "investigation_complete": True,
                "capa_complete": True,
                "safety_review_complete": True,
                "osha_recordable_ack": True,
            },
        },
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200, r.text


def test_illegal_skip_transition_rejected(fresh_incident, admin_headers):
    """OPEN→CLOSED directly is not legal even with all attestations."""
    base = f"{API}/incidents/{fresh_incident}/transition"
    r = requests.post(
        base,
        json={
            "to_state": "CLOSED",
            "evidence": {
                "investigation_complete": True,
                "capa_complete": True,
                "safety_review_complete": True,
            },
        },
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "transition_not_allowed"


def test_state_events_for_nonexistent_returns_404(admin_headers):
    r = requests.get(
        f"{API}/incidents/__no_such_id__/state-events",
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 404


def test_transition_nonexistent_returns_404(admin_headers):
    r = requests.post(
        f"{API}/incidents/__no_such_id__/transition",
        json={"to_state": "UNDER_INVESTIGATION"},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 404


def test_existing_incidents_crud_untouched(fresh_incident, admin_headers):
    """Regression — the additive lifecycle endpoints must not break the
    existing GET /api/incidents/{id} contract."""
    r = requests.get(
        f"{API}/incidents/{fresh_incident}",
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == fresh_incident
    # State persists on the doc after a transition.
    requests.post(
        f"{API}/incidents/{fresh_incident}/transition",
        json={"to_state": "UNDER_INVESTIGATION"},
        headers=admin_headers, timeout=15,
    )
    r = requests.get(
        f"{API}/incidents/{fresh_incident}",
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200
    assert r.json().get("lifecycle_state") == "UNDER_INVESTIGATION"
