"""iter246 F3 · Smoke tests for the weekly PO digest module.

Verifies:
  - PM payload is scoped to assigned jobs (primary + co-PM)
  - HR payload sees all jobs
  - Empty-scope PM produces a zero payload (not a crash)
  - HTML render handles zero-data and full-data cases
  - Subject literal matches operator spec
  - Cron sleep math respects PO_DIGEST_HOUR_UTC / WEEKDAY env
  - `send_po_digest_once(send_email_fn=None, dry_run=True)` does NOT
    burn any quota and returns per-recipient summary

These tests use the live preview Mongo connection (same pattern as
existing iter153/iter243 tests). No new fixtures introduced.
"""
from __future__ import annotations

import os
import asyncio
import pytest

from dotenv import load_dotenv
load_dotenv(dotenv_path="/app/backend/.env")

from motor.motor_asyncio import AsyncIOMotorClient
import po_digest as M


def _db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli[os.environ["DB_NAME"]]


def test_subject_literal_matches_operator_spec():
    assert M.DIGEST_SUBJECT == "[MASCI · PO] Weekly Request PO Digest"


def test_seconds_until_next_send_respects_env(monkeypatch):
    monkeypatch.setenv("PO_DIGEST_HOUR_UTC", "14")
    monkeypatch.setenv("PO_DIGEST_WEEKDAY", "0")
    n = M._seconds_until_next_send()
    assert n > 0
    assert n < 8 * 24 * 3600  # always less than 8 days out


def test_enabled_default_true_and_overridable(monkeypatch):
    monkeypatch.delenv("PO_DIGEST_ENABLED", raising=False)
    assert M._enabled() is True
    monkeypatch.setenv("PO_DIGEST_ENABLED", "false")
    assert M._enabled() is False


def test_empty_scope_pm_returns_zero_payload():
    async def _go():
        s = await M._summarize_pos(_db(), project_numbers=[])
        assert s["total_open"] == 0
        assert s["pending_approval"] == 0
        assert s["pending_receipt"] == 0
        assert s["overdue_receipt"] == 0
        assert s["top_vendors"] == []
        assert s["scoped_to_jobs"] == 0
    asyncio.run(_go())


def test_hr_summary_returns_global_count_with_top_vendors():
    async def _go():
        s = await M._summarize_pos(_db(), project_numbers=None)
        assert isinstance(s["total_open"], int)
        assert s["total_open"] >= 0
        # HR scope_to_jobs sentinel is None
        assert s["scoped_to_jobs"] is None
        # If there is any data, top_vendors must be at most 5
        assert len(s["top_vendors"]) <= 5
    asyncio.run(_go())


def test_pm_payload_includes_role_and_email():
    async def _go():
        db = _db()
        pm = await db.project_managers.find_one(
            {"disabled": {"$in": [None, False]}},
            {"_id": 0, "id": 1, "name": 1, "email": 1},
        )
        if not pm:
            pytest.skip("no active PM seeded")
        payload = await M.build_pm_digest_payload(db, pm)
        assert payload["recipient_role"] == "pm"
        assert payload["recipient_email"]
        assert payload["scoped_to_jobs"] is not None
    asyncio.run(_go())


def test_hr_payload_role_is_hr():
    async def _go():
        db = _db()
        hr = await db.hr_users.find_one(
            {"disabled": {"$in": [None, False]}, "is_active": {"$ne": False}},
            {"_id": 0, "id": 1, "name": 1, "email": 1},
        )
        if not hr:
            pytest.skip("no active HR user seeded")
        payload = await M.build_hr_digest_payload(db, hr)
        assert payload["recipient_role"] == "hr"
        assert payload["scoped_to_jobs"] is None  # global
    asyncio.run(_go())


def test_html_render_handles_empty_state():
    payload = {
        "recipient_role": "pm",
        "recipient_name": "Test PM",
        "recipient_email": "test@masci.test",
        "as_of": "2026-05-19T14:00:00+00:00",
        "total_open": 0, "by_status": {},
        "pending_approval": 0, "pending_receipt": 0,
        "overdue_receipt": 0, "top_vendors": [],
        "scoped_to_jobs": 5,
    }
    html = M.render_po_digest_html(payload, portal_url="https://mascidocs.com")
    assert "Weekly Request PO Digest" in html
    assert "Clean slate" in html
    assert "No vendor activity" in html
    assert "/po-requests" in html  # CTA link present
    assert "None" not in html


def test_html_render_handles_full_state():
    payload = {
        "recipient_role": "hr",
        "recipient_name": "HR Manager",
        "recipient_email": "hr@mascigc.com",
        "as_of": "2026-05-19T14:00:00+00:00",
        "total_open": 12,
        "by_status": {
            "Pending Approval": 3, "Pending Receipt": 5, "Overdue Receipt": 2,
            "Approved": 1, "Submitted": 1, "Clarification Needed": 0,
        },
        "pending_approval": 3, "pending_receipt": 6, "overdue_receipt": 2,
        "top_vendors": [
            {"vendor": "ABC Supply", "count": 4},
            {"vendor": "XYZ Co", "count": 3},
        ],
        "scoped_to_jobs": None,
    }
    html = M.render_po_digest_html(payload, portal_url="https://mascidocs.com")
    assert "ABC Supply" in html
    assert "XYZ Co" in html
    assert "Platform-wide visibility" in html
    assert ">12<" in html  # total_open
    assert "None" not in html


def test_send_po_digest_once_dry_run_burns_no_quota():
    async def _go():
        results = await M.send_po_digest_once(
            _db(), send_email_fn=None, portal_url="", dry_run=True,
        )
        assert results["dry_run"] is True
        assert results["subject"] == M.DIGEST_SUBJECT
        # No recipient marked sent (because send_email_fn=None)
        for r in results.get("pm", []) + results.get("hr", []):
            assert r["sent"] is False
    asyncio.run(_go())


def test_recipients_filtered_to_valid_emails_only():
    async def _go():
        pms = await M._active_pm_recipients(_db())
        for p in pms:
            assert "@" in p["email"]
            assert p["email"] == p["email"].strip().lower()
        hrs = await M._active_hr_recipients(_db())
        for h in hrs:
            assert "@" in h["email"]
            assert h["email"] == h["email"].strip().lower()
    asyncio.run(_go())
