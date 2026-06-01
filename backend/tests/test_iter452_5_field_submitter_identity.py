"""OMEGA · iter452.5 Tier 1 · Field Submitter Identity regression suite.

Layered like iter451/iter452:
  1. Pure-Python lib unit tests (no I/O).
  2. Live HTTP integration tests against the running backend.

Run::

    cd /app/backend && python -m pytest tests/test_iter452_5_field_submitter_identity.py -q
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import time
from datetime import datetime, timedelta, timezone

import pytest
import requests
from dotenv import load_dotenv

from lib.field_submitter_identity import (
    CONSENT_TEXT_VERSION,
    DELIVERY_EVENT_KINDS,
    FIELD_SUBMITTER_BINDINGS,
    mint_revision_token,
    verify_revision_token,
)

# ────────────────────────────────────────────────────────────────
# Unit tests — pure Python, no I/O
# ────────────────────────────────────────────────────────────────
def test_delivery_event_kinds_canonical():
    assert DELIVERY_EVENT_KINDS == (
        "notification_dispatch_attempted",
        "notification_dispatch_succeeded",
        "notification_dispatch_failed",
        "revision_link_issued",
        "revision_link_consumed",
        "revision_saved",
    )


def test_jwt_mint_roundtrip_success():
    tok, exp = mint_revision_token(
        workflow="daily_report",
        record_id="rec-123",
        binding_id="bind-456",
    )
    assert tok.count(".") == 2
    assert isinstance(exp, datetime)
    ok, payload, err = verify_revision_token(tok)
    assert ok and err == ""
    assert payload["wf"] == "daily_report"
    assert payload["rid"] == "rec-123"
    assert payload["bid"] == "bind-456"


def test_jwt_rejects_tampered_signature():
    tok, _ = mint_revision_token(
        workflow="incident", record_id="r", binding_id="b",
    )
    head, mid, _sig = tok.split(".")
    tampered = f"{head}.{mid}.AAAA"
    ok, _, err = verify_revision_token(tampered)
    assert not ok and err in ("bad_signature", "malformed")


def test_jwt_rejects_expired_token():
    past = datetime.now(timezone.utc) - timedelta(hours=10)
    tok, _ = mint_revision_token(
        workflow="incident", record_id="r", binding_id="b",
        issued_at=past, ttl_hours=1,
    )
    ok, _, err = verify_revision_token(tok)
    assert not ok and err == "expired"


def test_jwt_rejects_malformed_token():
    ok, _, err = verify_revision_token("not.a.token.with.dots")
    assert not ok and err == "malformed"
    ok, _, err = verify_revision_token("garbage")
    assert not ok and err == "malformed"


def test_consent_text_version_is_dated():
    # Sanity — version string must be parseable and dated.
    assert CONSENT_TEXT_VERSION.startswith("v1.")
    assert "2026" in CONSENT_TEXT_VERSION


# ────────────────────────────────────────────────────────────────
# Integration tests — live HTTP against the running backend
# ────────────────────────────────────────────────────────────────
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
        async def _clear():
            db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
            th = hashlib.sha256(tok.encode()).hexdigest()
            await db.session_activity.delete_many({"token_hash": th})
        asyncio.run(_clear())
    except Exception:
        pass
    return {"X-Admin-Token": tok, "Content-Type": "application/json"}


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    return AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


def _purge_record(workflow: str, record_id: str):
    async def _go():
        db = _db()
        await db.workflow_state_events.delete_many(
            {"workflow": workflow, "record_id": record_id}
        )
        await db[FIELD_SUBMITTER_BINDINGS].delete_many(
            {"submission_workflow": workflow, "submission_record_id": record_id}
        )
    asyncio.run(_go())


@pytest.fixture
def fresh_dr_with_fsi(admin_headers):
    payload = {
        "project_name": "iter452.5 FSI DR test",
        "project_number": "TEST-4525",
        "location": "Lab",
        "report_date": "2026-06-01",
        "prepared_by": "pytest harness",
        "submitter_employee_id": "pytest-employee-001",
        "submitter_email_at_submit": "pytest+fsi@example.com",
    }
    r = requests.post(f"{API}/daily-reports", json=payload, timeout=15)
    assert r.status_code in (200, 201), r.text
    dr_id = r.json()["id"]
    yield dr_id, r.json()
    try:
        requests.delete(f"{API}/daily-reports/{dr_id}",
                        headers=admin_headers, timeout=15)
    except Exception:
        pass
    _purge_record("daily_report", dr_id)


@pytest.fixture
def fresh_incident_with_fsi(admin_headers):
    payload = {
        "project_name": "iter452.5 FSI incident test",
        "project_number": "TEST-4525",
        "location": "Lab",
        "incident_date": "2026-06-01",
        "incident_time": "10:00",
        "reported_date": "2026-06-01",
        "reported_by": "pytest harness",
        "incident_type": "Near Miss",
        "severity": "low",
        "osha_recordable": "No",
        "description": "iter452.5 FSI seed",
        "submitter_employee_id": "pytest-employee-002",
        "submitter_email_at_submit": "pytest+fsi-inc@example.com",
    }
    r = requests.post(f"{API}/incidents", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    inc_id = r.json()["id"]
    yield inc_id, r.json()
    try:
        requests.delete(f"{API}/incidents/{inc_id}",
                        headers=admin_headers, timeout=15)
    except Exception:
        pass
    _purge_record("incident", inc_id)


def test_dr_submission_creates_binding(fresh_dr_with_fsi):
    dr_id, _payload = fresh_dr_with_fsi
    # Allow the upsert to settle (resolve_identity runs after insert).
    time.sleep(0.2)
    async def _check():
        db = _db()
        b = await db[FIELD_SUBMITTER_BINDINGS].find_one(
            {"submission_workflow": "daily_report",
             "submission_record_id": dr_id},
            {"_id": 0},
        )
        return b
    binding = asyncio.run(_check())
    assert binding is not None, "binding row missing"
    assert binding["submitter_employee_id"] == "pytest-employee-001"
    assert binding["submitter_email_at_submit"] == "pytest+fsi@example.com"
    # No employee match in directory → legacy_submitter must be True so
    # the kickback path falls back to PM-relay. (The synthetic
    # employee_id "pytest-employee-001" is not a real directory row.)
    assert binding["legacy_submitter"] is True


def test_incident_submission_creates_binding(fresh_incident_with_fsi):
    inc_id, _payload = fresh_incident_with_fsi
    time.sleep(0.2)
    async def _check():
        db = _db()
        return await db[FIELD_SUBMITTER_BINDINGS].find_one(
            {"submission_workflow": "incident",
             "submission_record_id": inc_id},
            {"_id": 0},
        )
    binding = asyncio.run(_check())
    assert binding is not None
    assert binding["submission_record_doc_id"].startswith("INC-")
    assert binding["submitter_email_at_submit"] == "pytest+fsi-inc@example.com"


def test_legacy_dr_submission_creates_binding_marked_legacy(admin_headers):
    """A DR submitted WITHOUT FSI fields still produces a binding row
    marked legacy_submitter=True so the kickback router can degrade
    gracefully to the PM-relay path."""
    payload = {
        "project_name": "iter452.5 legacy DR test",
        "project_number": "TEST-4525",
        "location": "Lab",
        "report_date": "2026-06-01",
        "prepared_by": "legacy submitter",
        # No submitter_employee_id, no submitter_email_at_submit.
    }
    r = requests.post(f"{API}/daily-reports", json=payload, timeout=15)
    assert r.status_code in (200, 201), r.text
    dr_id = r.json()["id"]
    try:
        time.sleep(0.2)
        async def _check():
            db = _db()
            return await db[FIELD_SUBMITTER_BINDINGS].find_one(
                {"submission_workflow": "daily_report",
                 "submission_record_id": dr_id},
                {"_id": 0},
            )
        binding = asyncio.run(_check())
        assert binding is not None
        assert binding["legacy_submitter"] is True
        assert binding["submitter_employee_id"] == ""
    finally:
        try:
            requests.delete(f"{API}/daily-reports/{dr_id}",
                            headers=admin_headers, timeout=15)
        except Exception:
            pass
        _purge_record("daily_report", dr_id)


def test_project_team_endpoint(admin_headers):
    r = requests.get(f"{API}/projects/TEST-4525/team", timeout=15)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "team" in data and isinstance(data["team"], list)
    assert "count" in data
    assert "project" in data
    # No email leak in public-safe roster (Tier 1 contract).
    if data["team"]:
        sample = data["team"][0]
        assert "email" not in sample, "team endpoint must not leak email"
        assert "phone" not in sample, "team endpoint must not leak phone"


def test_revise_token_resolve_and_save(fresh_dr_with_fsi):
    dr_id, _ = fresh_dr_with_fsi
    time.sleep(0.2)
    # Fetch the binding so we can mint a token that matches the binding id.
    async def _binding():
        db = _db()
        return await db[FIELD_SUBMITTER_BINDINGS].find_one(
            {"submission_workflow": "daily_report",
             "submission_record_id": dr_id},
            {"_id": 0},
        )
    binding = asyncio.run(_binding())
    assert binding is not None
    tok, _exp = mint_revision_token(
        workflow="daily_report",
        record_id=dr_id,
        binding_id=binding["id"],
    )
    r = requests.get(f"{API}/revise/{tok}", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["workflow"] == "daily_report"
    assert body["binding"]["submitter_email_at_submit"] == "pytest+fsi@example.com"
    assert body["submission"]["id"] == dr_id

    # Save a revision.
    r2 = requests.post(
        f"{API}/revise/{tok}",
        json={"changes": {"notes": "Field correction"}, "note": "Fixed weather"},
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["ok"] is True

    # Verify the chain events exist.
    async def _events():
        db = _db()
        cur = db.workflow_state_events.find(
            {"workflow": "daily_report", "record_id": dr_id,
             "evidence.delivery_event": {"$in": list(DELIVERY_EVENT_KINDS)}},
            {"_id": 0, "evidence.delivery_event": 1},
        )
        return await cur.to_list(100)
    rows = asyncio.run(_events())
    kinds = {r["evidence"]["delivery_event"] for r in rows}
    assert "revision_link_consumed" in kinds
    assert "revision_saved" in kinds


def test_revise_bad_token_rejected():
    r = requests.get(f"{API}/revise/garbage.token.value", timeout=15)
    assert r.status_code == 400
    body = r.json()
    assert "token_" in str(body.get("detail", ""))


def test_admin_bindings_listing(fresh_dr_with_fsi):
    dr_id, _ = fresh_dr_with_fsi
    time.sleep(0.2)
    r = requests.get(
        f"{API}/admin/field-submitter-bindings?workflow=daily_report&limit=50",
        timeout=15,
    )
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    matched = [i for i in items if i.get("submission_record_id") == dr_id]
    assert matched, f"binding for {dr_id} not surfaced by admin listing"


# ─────────────────────────────────────────────────────────────────
# Regression — the iter451 / iter452 suites must remain green.
# This test sanity-pings the prior lifecycle endpoints to verify
# this iteration did not break them. Light-weight smoke only.
# ─────────────────────────────────────────────────────────────────
def test_prior_iter451_iter452_lifecycle_endpoints_alive(admin_headers):
    r1 = requests.get(f"{API}/incidents/__non_existent__/lifecycle",
                      headers=admin_headers, timeout=15)
    # 404 is the correct response for a missing record — proves the
    # endpoint is still mounted and gating correctly.
    assert r1.status_code in (404, 400)
    r2 = requests.get(f"{API}/daily-reports/__non_existent__/lifecycle",
                      headers=admin_headers, timeout=15)
    assert r2.status_code in (404, 400)
