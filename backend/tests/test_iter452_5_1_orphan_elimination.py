"""OMEGA · iter452.5.1 (P0) · Orphan-elimination regression suite.

Asserts the operator-mandated 5-tier identity ladder:

  Tier 1  X-FL-Token              → fl user record email
  Tier 2  submitter_employee_id    → employee directory email
  Tier 3  submitter_email_at_submit
  Tier 4  project_number → jobs_master.pm_email
  Tier 5  ADMIN_DEAD_LETTER_EMAIL

The triple-failure orphan corner from the iter452.5 forensic audit
(question 8) must become structurally impossible: every binding row
written by ``resolve_identity`` carries a non-empty
``primary_recipient_email`` AND a ``resolution_tier`` in
{fl, employee, per_submit, pm_relay, dead_letter}.

Run::

    cd /app/backend && python -m pytest \
        tests/test_iter452_5_1_orphan_elimination.py -q
"""
from __future__ import annotations

import asyncio
import hashlib
import os
import time
import uuid
from datetime import datetime, timezone

import pytest
import requests
from dotenv import load_dotenv

from lib.field_submitter_identity import (
    FIELD_SUBMITTER_BINDINGS,
    _dead_letter_email,
    resolve_identity,
)

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


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    return AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


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


def _purge_binding(workflow: str, record_id: str):
    async def _go():
        db = _db()
        await db[FIELD_SUBMITTER_BINDINGS].delete_many(
            {"submission_workflow": workflow, "submission_record_id": record_id}
        )
        await db.workflow_state_events.delete_many(
            {"workflow": workflow, "record_id": record_id}
        )
    asyncio.run(_go())


# ────────────────────────────────────────────────────────────────
# Pure unit — dead-letter resolver honors env override
# ────────────────────────────────────────────────────────────────
def test_dead_letter_email_honors_env(monkeypatch):
    monkeypatch.setenv("ADMIN_DEAD_LETTER_EMAIL", "Triage@Example.com")
    assert _dead_letter_email() == "triage@example.com"


def test_dead_letter_email_default_when_unset(monkeypatch):
    monkeypatch.delenv("ADMIN_DEAD_LETTER_EMAIL", raising=False)
    assert _dead_letter_email() == "safety@mascigc.com"


# ────────────────────────────────────────────────────────────────
# Tier-by-tier — exercise resolve_identity() directly so we don't
# depend on whether the HTTP create routes are stable in CI.
# ────────────────────────────────────────────────────────────────
@pytest.fixture
def synthetic_fl_user():
    """Seed a synthetic Field Leadership user + a valid X-FL-Token
    for them; remove on teardown. Returns ``(token, email, name)``."""
    from field_leadership_users import make_fl_user_token  # noqa: PLC0415
    user_id = f"pytest-fl-{uuid.uuid4().hex[:8]}"
    email = f"{user_id}@example.com"
    name = "Pytest FL User"
    # Synthesize a password_hash via the existing helper so the
    # signature-stable token verifier accepts it.
    from field_leadership_users import hash_password  # noqa: PLC0415
    pwh = hash_password("pytest-password-do-not-use")
    async def _seed():
        db = _db()
        await db.field_leadership_users.insert_one({
            "id": user_id,
            "name": name,
            "email": email,
            "phone": "",
            "role": "supervisor",
            "is_active": True,
            "disabled": False,
            "password_hash": pwh,
            "password_set_at": datetime.now(timezone.utc).isoformat(),
            "must_change_password": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
    asyncio.run(_seed())
    token = make_fl_user_token(user_id, pwh)
    yield token, email, name
    async def _cleanup():
        db = _db()
        await db.field_leadership_users.delete_one({"id": user_id})
    asyncio.run(_cleanup())


def test_tier1_fl_token_resolves_supervisor_email(synthetic_fl_user):
    token, email, name = synthetic_fl_user
    rid = f"pytest-rid-{uuid.uuid4().hex[:8]}"
    try:
        async def _go():
            db = _db()
            return await resolve_identity(
                db,
                workflow="daily_report",
                record_id=rid,
                record_doc_id="DR-PYTEST-T1",
                project_number="TEST-4525",
                submitter_employee_id="",
                submitter_email_at_submit="",
                fl_token=token,
            )
        b = asyncio.run(_go())
        assert b["resolution_tier"] == "fl"
        assert b["primary_recipient_email"] == email.lower()
        assert b["fl_user_email"] == email.lower()
        assert b["legacy_submitter"] is False, "FL match must clear the legacy flag"
        assert b["submitter_name"] == name
    finally:
        _purge_binding("daily_report", rid)


def test_tier2_employee_directory_resolves_when_no_fl_token():
    rid = f"pytest-rid-{uuid.uuid4().hex[:8]}"
    # Find any active employee with an email to use as the directory subject.
    async def _go():
        db = _db()
        emp = await db.employees.find_one(
            {"email": {"$nin": ["", None]}, "is_active": {"$ne": False}},
            {"_id": 0, "id": 1, "email": 1, "name": 1, "employee_id": 1},
        )
        return emp, await resolve_identity(
            db,
            workflow="daily_report",
            record_id=rid,
            record_doc_id="DR-PYTEST-T2",
            project_number="TEST-4525",
            submitter_employee_id=emp.get("id") or emp.get("employee_id") or "",
        )
    try:
        emp, b = asyncio.run(_go())
        assert emp is not None, "no employee with email in directory — re-seed"
        assert b["resolution_tier"] == "employee"
        assert b["primary_recipient_email"] == (emp["email"] or "").strip().lower()
        assert b["employee_email"] == (emp["email"] or "").strip().lower()
        assert b["fl_user_email"] == ""
        assert b["legacy_submitter"] is False
    finally:
        _purge_binding("daily_report", rid)


def test_tier3_per_submit_email_resolves_when_no_directory_match():
    rid = f"pytest-rid-{uuid.uuid4().hex[:8]}"
    try:
        async def _go():
            db = _db()
            return await resolve_identity(
                db,
                workflow="daily_report",
                record_id=rid,
                record_doc_id="DR-PYTEST-T3",
                project_number="TEST-NO-PROJECT",
                submitter_employee_id="pytest-no-match",
                submitter_email_at_submit="Field.Crew@example.com",
            )
        b = asyncio.run(_go())
        assert b["resolution_tier"] == "per_submit"
        assert b["primary_recipient_email"] == "field.crew@example.com"
        assert b["fl_user_email"] == ""
        assert b["employee_email"] == ""
        # No employee directory match → legacy_submitter remains True
        # (preserves iter452.5 R1 semantic for admin UI badge).
        assert b["legacy_submitter"] is True
    finally:
        _purge_binding("daily_report", rid)


def test_tier4_pm_relay_when_no_submitter_or_directory_or_per_submit(admin_headers):
    """Seed a synthetic jobs_master row carrying a PM email; assert
    the resolver picks it when all of tiers 1–3 fail."""
    rid = f"pytest-rid-{uuid.uuid4().hex[:8]}"
    pn = f"PYTEST-PM-{uuid.uuid4().hex[:6].upper()}"
    pm_email = f"pm-{uuid.uuid4().hex[:6]}@example.com"
    try:
        async def _seed_and_resolve():
            db = _db()
            await db.jobs_master.insert_one({
                "id": f"pytest-job-{uuid.uuid4().hex[:6]}",
                "project_number": pn,
                "project_name": "TEST_Pytest_PM_relay_seed",
                "primary_pm_name": "Pytest PM",
                "pm_email": pm_email,
                "is_active": True,
            })
            b = await resolve_identity(
                db,
                workflow="daily_report",
                record_id=rid,
                record_doc_id="DR-PYTEST-T4",
                project_number=pn,
                submitter_employee_id="",
                submitter_email_at_submit="",
            )
            return b
        b = asyncio.run(_seed_and_resolve())
        assert b["resolution_tier"] == "pm_relay"
        assert b["primary_recipient_email"] == pm_email.lower()
        assert b["resolved_pm_email"] == pm_email.lower()
        assert b["legacy_submitter"] is True
    finally:
        async def _cleanup():
            db = _db()
            await db.jobs_master.delete_many({"project_number": pn})
        asyncio.run(_cleanup())
        _purge_binding("daily_report", rid)


def test_tier5_dead_letter_when_nothing_else_resolves():
    """The critical P0 assertion: even with NO identity hints AND NO
    project ownership, the binding row carries a non-empty primary
    recipient. The orphan corner is now structurally impossible."""
    rid = f"pytest-rid-{uuid.uuid4().hex[:8]}"
    try:
        async def _go():
            db = _db()
            return await resolve_identity(
                db,
                workflow="daily_report",
                record_id=rid,
                record_doc_id="DR-PYTEST-T5",
                project_number="",                # no project
                submitter_employee_id="",          # no directory key
                submitter_email_at_submit="",      # no per-submit email
                # no fl_token
            )
        b = asyncio.run(_go())
        assert b["resolution_tier"] == "dead_letter"
        assert b["primary_recipient_email"]  # MUST be non-empty
        assert b["primary_recipient_email"] == _dead_letter_email()
        assert b["resolved_dead_letter_email"] == _dead_letter_email()
        assert b["legacy_submitter"] is True
    finally:
        _purge_binding("daily_report", rid)


# ────────────────────────────────────────────────────────────────
# Integration — verify the public POST routes propagate X-FL-Token
# through to resolve_identity (the smallest end-to-end proof).
# ────────────────────────────────────────────────────────────────
def test_public_post_with_fl_token_header_resolves_tier1(synthetic_fl_user, admin_headers):
    token, email, _name = synthetic_fl_user
    payload = {
        "project_name": "TEST_iter452_5_1_P0_smoke",
        "project_number": "TEST-4525",
        "location": "Lab",
        "report_date": "2026-06-01",
        "prepared_by": "P0 harness",
    }
    r = requests.post(
        f"{API}/daily-reports",
        json=payload,
        headers={"X-FL-Token": token, "Content-Type": "application/json"},
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    rid = r.json()["id"]
    try:
        time.sleep(0.3)
        async def _b():
            db = _db()
            return await db[FIELD_SUBMITTER_BINDINGS].find_one(
                {"submission_workflow": "daily_report",
                 "submission_record_id": rid},
                {"_id": 0},
            )
        b = asyncio.run(_b())
        assert b is not None, "binding row missing"
        assert b["resolution_tier"] == "fl"
        assert b["primary_recipient_email"] == email.lower()
        assert b["legacy_submitter"] is False
    finally:
        try:
            requests.delete(f"{API}/daily-reports/{rid}",
                            headers=admin_headers, timeout=15)
        except Exception:
            pass
        _purge_binding("daily_report", rid)


def test_orphan_corner_is_impossible_via_public_post(admin_headers):
    """End-to-end · the original RED corner from the forensic audit.
    No FL token, no employee_id, no per-submit email, no project_number.
    The binding row MUST still carry a dead-letter primary recipient."""
    payload = {
        "project_name": "TEST_iter452_5_1_ORPHAN_corner",
        "location": "Unknown",
        "report_date": "2026-06-01",
        "prepared_by": "anonymous field hand",
        # NO project_number, NO submitter_employee_id, NO email.
    }
    r = requests.post(f"{API}/daily-reports", json=payload, timeout=15)
    assert r.status_code in (200, 201), r.text
    rid = r.json()["id"]
    try:
        time.sleep(0.3)
        async def _b():
            db = _db()
            return await db[FIELD_SUBMITTER_BINDINGS].find_one(
                {"submission_workflow": "daily_report",
                 "submission_record_id": rid},
                {"_id": 0},
            )
        b = asyncio.run(_b())
        assert b is not None, "binding missing — orphan corner returned!"
        assert b["resolution_tier"] == "dead_letter", \
            "Tier 5 must catch the orphan corner"
        assert b["primary_recipient_email"] == _dead_letter_email()
    finally:
        try:
            requests.delete(f"{API}/daily-reports/{rid}",
                            headers=admin_headers, timeout=15)
        except Exception:
            pass
        _purge_binding("daily_report", rid)
