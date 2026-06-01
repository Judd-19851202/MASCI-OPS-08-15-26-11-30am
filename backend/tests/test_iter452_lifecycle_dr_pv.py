"""OMEGA · Phase 1A · iter452 · OC-002 + OC-007 regression suite.

Layers:
  1. Pure-Python state-machine unit tests (no I/O).
  2. Live HTTP integration tests against the running backend.

Mirrors the iter451 pattern.
"""
from __future__ import annotations

import hashlib
import os
import uuid

import pytest
import requests
from dotenv import load_dotenv

from lib.workflow_state_machine import (
    DAILY_REPORT_DEFAULT_STATE,
    DAILY_REPORT_STATES,
    PAYROLL_VARIANCE_DEFAULT_STATE,
    PAYROLL_VARIANCE_STATES,
    coerce_daily_report_state,
    coerce_payroll_variance_state,
    validate_daily_report_transition,
    validate_payroll_variance_transition,
)


# ═══════════════════════════════════════════════════════════════
# OC-002 Daily Report state-machine unit tests
# ═══════════════════════════════════════════════════════════════
def test_dr_states_canonical():
    assert DAILY_REPORT_DEFAULT_STATE == "OPEN"
    assert DAILY_REPORT_STATES == ("OPEN", "PENDING_REVIEW", "REVIEWED", "CLOSED")


def test_dr_coerce_state():
    assert coerce_daily_report_state(None) == "OPEN"
    assert coerce_daily_report_state("") == "OPEN"
    assert coerce_daily_report_state("CLOSED") == "CLOSED"
    assert coerce_daily_report_state("nope") == "OPEN"


def test_dr_pm_submit_allowed():
    ok, err = validate_daily_report_transition(
        from_state="OPEN", to_state="PENDING_REVIEW",
        actor={"_actor_kind": "pm_user"},
    )
    assert ok and err == ""


def test_dr_pm_cannot_review():
    ok, err = validate_daily_report_transition(
        from_state="PENDING_REVIEW", to_state="REVIEWED",
        actor={"_actor_kind": "pm_user"},
    )
    assert not ok and err == "role_not_authorized"


def test_dr_closure_requires_two_flags():
    ok, err = validate_daily_report_transition(
        from_state="REVIEWED", to_state="CLOSED",
        actor=True,
        evidence={"office_review_complete": True},
    )
    assert not ok
    assert err.startswith("closure_attestation_missing:payroll_inputs_verified")


def test_dr_kickback_requires_reason():
    ok, err = validate_daily_report_transition(
        from_state="PENDING_REVIEW", to_state="OPEN",
        actor=True,
    )
    assert not ok and err == "return_to_field_reason_required"


def test_dr_reopen_requires_reason():
    ok, err = validate_daily_report_transition(
        from_state="CLOSED", to_state="PENDING_REVIEW",
        actor=True,
    )
    assert not ok and err == "reopen_reason_required"


def test_dr_full_happy_path():
    seq = [
        ("OPEN", "PENDING_REVIEW"),
        ("PENDING_REVIEW", "REVIEWED"),
        ("REVIEWED", "CLOSED"),
    ]
    for f, t in seq:
        ok, _ = validate_daily_report_transition(
            from_state=f, to_state=t, actor=True,
            evidence={"office_review_complete": True, "payroll_inputs_verified": True},
        )
        assert ok, f"{f}→{t} blocked unexpectedly"


# ═══════════════════════════════════════════════════════════════
# OC-007 Payroll Variance state-machine unit tests
# ═══════════════════════════════════════════════════════════════
def test_pv_states_canonical():
    assert PAYROLL_VARIANCE_DEFAULT_STATE == "OPEN"
    assert PAYROLL_VARIANCE_STATES == ("OPEN", "UNDER_REVIEW", "APPROVED", "FINALIZED")


def test_pv_coerce_state():
    assert coerce_payroll_variance_state(None) == "OPEN"
    assert coerce_payroll_variance_state("FINALIZED") == "FINALIZED"
    assert coerce_payroll_variance_state("nope") == "OPEN"


def test_pv_hr_cannot_finalize():
    ok, err = validate_payroll_variance_transition(
        from_state="APPROVED", to_state="FINALIZED",
        actor={"_actor_kind": "hr_user"},
        evidence={"review_complete": True, "approval_complete": True,
                  "variance_decisions_complete": True},
    )
    assert not ok and err == "role_not_authorized"


def test_pv_admin_can_finalize_with_attestations():
    ok, err = validate_payroll_variance_transition(
        from_state="APPROVED", to_state="FINALIZED",
        actor=True,
        evidence={"review_complete": True, "approval_complete": True,
                  "variance_decisions_complete": True},
    )
    assert ok and err == ""


def test_pv_finalize_blocks_on_missing_attestation():
    ok, err = validate_payroll_variance_transition(
        from_state="APPROVED", to_state="FINALIZED",
        actor=True,
        evidence={"review_complete": True, "approval_complete": True},
    )
    assert not ok
    assert err == "finalize_attestation_missing:variance_decisions_complete"


def test_pv_back_step_requires_reason():
    ok, err = validate_payroll_variance_transition(
        from_state="APPROVED", to_state="UNDER_REVIEW",
        actor=True,
    )
    assert not ok and err == "back_step_reason_required"


def test_pv_reopen_requires_reason():
    ok, err = validate_payroll_variance_transition(
        from_state="FINALIZED", to_state="UNDER_REVIEW",
        actor=True,
    )
    assert not ok and err == "reopen_reason_required"


def test_pv_no_auto_finalize_from_open():
    """Cannot skip directly from OPEN to FINALIZED — operator's
    'NO AUTO FINALIZE' rule enforced by the state graph."""
    ok, err = validate_payroll_variance_transition(
        from_state="OPEN", to_state="FINALIZED",
        actor=True,
        evidence={"review_complete": True, "approval_complete": True,
                  "variance_decisions_complete": True},
    )
    assert not ok and err == "transition_not_allowed"


# ═══════════════════════════════════════════════════════════════
# Live HTTP integration — OC-002
# ═══════════════════════════════════════════════════════════════
load_dotenv("/app/backend/.env")


def _base_url() -> str:
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = _base_url()
API = f"{BASE_URL}/api"


def _admin_token() -> str:
    from server import _admin_token_for  # type: ignore
    pw = os.environ.get("ADMIN_PASSWORD", "")
    return _admin_token_for(pw) if pw else ""


@pytest.fixture(scope="module")
def admin_headers():
    tok = _admin_token()
    if not tok:
        pytest.skip("ADMIN_PASSWORD not configured")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        async def _clear():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            th = hashlib.sha256(tok.encode()).hexdigest()
            await db.session_activity.delete_many({"token_hash": th})
        asyncio.run(_clear())
    except Exception:
        pass
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


@pytest.fixture
def fresh_dr(admin_headers):
    payload = {
        "project_name": "iter452 DR test",
        "project_number": "TEST-452",
        "location": "Job site",
        "report_date": "2026-06-01",
        "prepared_by": "pytest",
        "work_completed": "iter452 seed",
    }
    r = requests.post(f"{API}/daily-reports", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    dr_id = r.json()["id"]
    yield dr_id
    requests.delete(f"{API}/daily-reports/{dr_id}", headers=admin_headers, timeout=15)
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        async def _purge():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            await db.workflow_state_events.delete_many(
                {"workflow": "daily_report", "record_id": dr_id}
            )
        asyncio.run(_purge())
    except Exception:
        pass


def test_dr_transition_unauthenticated(fresh_dr):
    r = requests.post(
        f"{API}/daily-reports/{fresh_dr}/transition",
        json={"to_state": "PENDING_REVIEW"},
        headers={"X-Admin-Token": ""}, timeout=15,
    )
    assert r.status_code == 401


def test_dr_full_lifecycle(fresh_dr, admin_headers):
    base = f"{API}/daily-reports/{fresh_dr}/transition"

    # OPEN → PENDING_REVIEW
    r = requests.post(base, json={"to_state": "PENDING_REVIEW"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # Kickback without reason → 422
    r = requests.post(base, json={"to_state": "OPEN"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "return_to_field_reason_required"

    # Kickback with reason → 200
    r = requests.post(base,
                      json={"to_state": "OPEN", "reason": "Missing crew hours"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # Resubmit
    r = requests.post(base, json={"to_state": "PENDING_REVIEW"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # PENDING_REVIEW → REVIEWED
    r = requests.post(base, json={"to_state": "REVIEWED"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # REVIEWED → CLOSED without attestation → 422
    r = requests.post(base, json={"to_state": "CLOSED"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"].startswith("closure_attestation_missing")

    # REVIEWED → CLOSED with full attestation → 200
    r = requests.post(
        base,
        json={"to_state": "CLOSED",
              "evidence": {"office_review_complete": True,
                           "payroll_inputs_verified": True}},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200

    # REOPEN without reason → 422
    r = requests.post(base, json={"to_state": "PENDING_REVIEW"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 422

    # REOPEN with reason → 200
    r = requests.post(
        base,
        json={"to_state": "PENDING_REVIEW",
              "reason": "Discovered missing material entry"},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200

    # Audit — filter out iter452.5 delivery-evidence rows so the
    # lifecycle transition count remains the contract under test.
    r = requests.get(f"{API}/daily-reports/{fresh_dr}/state-events",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200
    rows = r.json()
    lifecycle_rows = [
        x for x in rows
        if not (x.get("evidence") or {}).get("delivery_event")
    ]
    assert len(lifecycle_rows) == 6
    assert lifecycle_rows[0]["to_state"] == "PENDING_REVIEW"
    assert lifecycle_rows[0]["reason"].startswith("Discovered missing")


def test_dr_lifecycle_view(fresh_dr, admin_headers):
    r = requests.get(f"{API}/daily-reports/{fresh_dr}/lifecycle",
                     headers=admin_headers, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["workflow"] == "daily_report"
    assert body["lifecycle_state"] == "OPEN"
    legal = [t["to_state"] for t in body["legal_next_states"]
             if t["allowed_for_actor"]]
    assert legal == ["PENDING_REVIEW"]


# ═══════════════════════════════════════════════════════════════
# Live HTTP integration — OC-007
# ═══════════════════════════════════════════════════════════════
@pytest.fixture
def fresh_pv_batch(admin_headers):
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    bid = str(uuid.uuid4())
    async def _seed():
        from datetime import datetime, timezone
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        await db.payroll_variance_batches.insert_one({
            "id": bid,
            "week_ending": "2026-06-15",
            "rows": [
                {"employee_id": "EMP-X", "employee_name": "Carol",
                 "timesheet_hours": 40, "payroll_hours": 40, "flag": ""},
                {"employee_id": "EMP-Y", "employee_name": "Dave",
                 "timesheet_hours": 42, "payroll_hours": 40, "flag": "flag",
                 "decision": ""},
            ],
            "flagged_rows": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    asyncio.run(_seed())
    yield bid
    async def _cleanup():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        await db.payroll_variance_batches.delete_one({"id": bid})
        await db.workflow_state_events.delete_many(
            {"workflow": "payroll_variance", "record_id": bid}
        )
    asyncio.run(_cleanup())


def _set_decision(batch_id: str, employee_id: str, decision: str):
    from motor.motor_asyncio import AsyncIOMotorClient
    import asyncio
    async def go():
        db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
        await db.payroll_variance_batches.update_one(
            {"id": batch_id, "rows.employee_id": employee_id},
            {"$set": {"rows.$.decision": decision}},
        )
    asyncio.run(go())


def test_pv_full_lifecycle(fresh_pv_batch, admin_headers):
    base = f"{API}/hr/payroll-variance/batches/{fresh_pv_batch}/transition"

    # OPEN → UNDER_REVIEW (Admin since we only have admin headers here)
    r = requests.post(base, json={"to_state": "UNDER_REVIEW"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # UNDER_REVIEW → APPROVED
    r = requests.post(base, json={"to_state": "APPROVED"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 200

    # APPROVED → FINALIZED without attestation → 422
    r = requests.post(base, json={"to_state": "FINALIZED"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"].startswith("finalize_attestation_missing")

    # With all 3 attestations BUT undecided flagged row → 422 (server safety net)
    r = requests.post(
        base,
        json={"to_state": "FINALIZED",
              "evidence": {"review_complete": True, "approval_complete": True,
                           "variance_decisions_complete": True}},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == \
           "finalize_attestation_missing:variance_decisions_complete"

    # Decide the flagged row → finalize succeeds
    _set_decision(fresh_pv_batch, "EMP-Y", "approve")
    r = requests.post(
        base,
        json={"to_state": "FINALIZED",
              "evidence": {"review_complete": True, "approval_complete": True,
                           "variance_decisions_complete": True}},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200, r.text

    # Reopen no reason → 422
    r = requests.post(base, json={"to_state": "UNDER_REVIEW"},
                      headers=admin_headers, timeout=15)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "reopen_reason_required"

    # Reopen with reason → 200
    r = requests.post(
        base,
        json={"to_state": "UNDER_REVIEW",
              "reason": "Overtime miscalc discovered post-finalize."},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200

    # Audit
    r = requests.get(
        f"{API}/hr/payroll-variance/batches/{fresh_pv_batch}/state-events",
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 4
    assert rows[0]["to_state"] == "UNDER_REVIEW"
    assert rows[0]["reason"].startswith("Overtime miscalc")


def test_pv_no_auto_finalize_from_open(fresh_pv_batch, admin_headers):
    base = f"{API}/hr/payroll-variance/batches/{fresh_pv_batch}/transition"
    r = requests.post(
        base,
        json={"to_state": "FINALIZED",
              "evidence": {"review_complete": True, "approval_complete": True,
                           "variance_decisions_complete": True}},
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "transition_not_allowed"


def test_pv_lifecycle_view(fresh_pv_batch, admin_headers):
    r = requests.get(
        f"{API}/hr/payroll-variance/batches/{fresh_pv_batch}/lifecycle",
        headers=admin_headers, timeout=15,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["lifecycle_state"] == "OPEN"
    assert body["flagged_rows"] == 1
    assert body["all_flagged_decided"] is False  # seed has undecided
