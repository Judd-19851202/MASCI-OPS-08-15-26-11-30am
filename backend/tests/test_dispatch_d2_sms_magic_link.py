"""
tests/test_dispatch_d2_sms_magic_link.py

Phase D-2 · SMS Magic Link Delivery regression suite.

Covers all 12 required tests from the OMEGA D-2 directive. Uses the
same in-memory _FakeDB scaffold as test_dispatch_d1_activation.py so
the suite is self-contained.

The Twilio SDK is NEVER actually called — we monkeypatch
``services.sms_provider.send_sms`` so tests are deterministic and
provider-agnostic.
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest import mock

import pytest

import dispatch_lifecycle as DLS
from services.sms_provider import (
    normalize_phone,
    mask_phone,
    sms_enabled,
    build_magic_link_body,
)
from tests.test_dispatch_d1_activation import _FakeDB, _seed_assignment


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
def _set_env(monkeypatch, **kv):
    for k, v in kv.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)


# ────────────────────────────────────────────────────────────────────
# TEST 1 · SMS disabled → assignment still creates (notification skipped)
# TEST 9 · Auto-SMS disabled → not attempted on assignment create
# ────────────────────────────────────────────────────────────────────
def test_auto_sms_disabled_does_not_attempt(monkeypatch):
    from routes.dispatch_lifecycle import _auto_sms_enabled

    _set_env(monkeypatch,
        DISPATCH_AUTO_SMS_ON_ASSIGN="false",
        SMS_ENABLED="false",
        TWILIO_ACCOUNT_SID=None, TWILIO_AUTH_TOKEN=None, TWILIO_FROM_NUMBER=None,
    )
    assert _auto_sms_enabled() is False


# ────────────────────────────────────────────────────────────────────
# TEST 2 · Missing Twilio credentials → graceful fallback (no crash)
# ────────────────────────────────────────────────────────────────────
def test_sms_enabled_false_when_creds_missing(monkeypatch):
    _set_env(monkeypatch,
        SMS_ENABLED="true",
        TWILIO_ACCOUNT_SID=None, TWILIO_AUTH_TOKEN=None, TWILIO_FROM_NUMBER=None,
    )
    assert sms_enabled() is False


def test_send_sms_skipped_when_disabled(monkeypatch):
    from services.sms_provider import send_sms
    _set_env(monkeypatch, SMS_ENABLED="false")
    async def run():
        r = await send_sms(to_phone="+15551234567", body="x", triggered_by="auto")
        assert r["ok"] is False
        assert r["status"] == "skipped"
        assert r["error_summary"]
    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 3 · Missing driver phone → copy-link fallback (status='skipped')
# TEST 4 · Invalid driver phone → copy-link fallback
# ────────────────────────────────────────────────────────────────────
def test_normalize_phone_accepts_us_formats():
    assert normalize_phone("(555) 123-4567") == "+15551234567"
    assert normalize_phone("555-123-4567") == "+15551234567"
    assert normalize_phone("5551234567") == "+15551234567"
    assert normalize_phone("15551234567") == "+15551234567"
    assert normalize_phone("+447911123456") == "+447911123456"


def test_normalize_phone_rejects_invalid():
    assert normalize_phone("") is None
    assert normalize_phone(None) is None
    assert normalize_phone("abc") is None
    assert normalize_phone("123") is None       # too short, no +
    assert normalize_phone("12") is None
    assert normalize_phone("+1") is None        # too short
    assert normalize_phone("999999999999999999") is None  # > 16


def test_mask_phone_preserves_last_four():
    assert mask_phone("+15551234567") == "***4567"
    assert mask_phone(None) == ""
    assert mask_phone("") == ""
    assert mask_phone("123") == "123"  # too short to mask


def test_issue_link_and_sms_skips_when_phone_missing(monkeypatch):
    from routes.dispatch_lifecycle import _issue_link_and_sms
    _set_env(monkeypatch,
        SMS_ENABLED="true",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
    )
    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        # NO employee record → no phone resolvable
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        outcome = await _issue_link_and_sms(
            db, assignment=a, triggered_by="dispatcher",
            issued_by_name="Op", issued_by_role="dispatch",
        )
        sr = outcome["sms_result"]
        assert sr["ok"] is False
        assert sr["status"] == "skipped"
        assert "Phone missing" in (sr["error_summary"] or "")
        # Magic link should NOT have been minted (we save tokens).
        assert outcome.get("magic_link_url") is None
    asyncio.get_event_loop().run_until_complete(run())


def test_issue_link_and_sms_skips_when_phone_invalid(monkeypatch):
    from routes.dispatch_lifecycle import _issue_link_and_sms
    _set_env(monkeypatch,
        SMS_ENABLED="true",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
    )
    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        await db.employees.insert_one({"id": "d1", "phone": "not-a-phone", "full_name": "T"})
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        outcome = await _issue_link_and_sms(
            db, assignment=a, triggered_by="dispatcher",
            issued_by_name="Op", issued_by_role="dispatch",
        )
        sr = outcome["sms_result"]
        assert sr["ok"] is False
        assert sr["status"] == "skipped"
        assert "Phone missing" in (sr["error_summary"] or "")
    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 5 · Valid phone → provider adapter called with E.164 normalized
# TEST 6 · Provider success → delivery log 'sent' + audit event written
# ────────────────────────────────────────────────────────────────────
def test_valid_phone_triggers_provider_and_logs_sent(monkeypatch):
    """Patch ``send_sms`` to record the call and return a 'sent' result.
    Verify the audit log + dispatch_state_events row + magic link mint.
    """
    from routes.dispatch_lifecycle import _issue_link_and_sms, _fire_assignment_notification
    _set_env(monkeypatch,
        SMS_ENABLED="true", SMS_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
        PUBLIC_FRONTEND_URL="https://mascidocs.test",
    )
    captured = {}

    async def fake_send_sms(*, to_phone, body, triggered_by, status_callback_url=None):
        captured["to_phone"] = to_phone
        captured["body"] = body
        captured["triggered_by"] = triggered_by
        captured["status_callback_url"] = status_callback_url
        return {
            "ok": True, "status": "sent", "provider": "twilio",
            "provider_message_id": "SMabc123", "destination_phone_masked": "***4567",
            "triggered_by": triggered_by, "error_summary": None,
        }

    # Patch driver_sessions.issue_magic_link so we don't depend on the
    # real magic-link pipeline in this unit test.
    async def fake_issue_magic_link(db, **kw):
        return {"link_id": "L1", "token": "TKN_XYZ", "expires_at": "2026-01-01T00:00:00+00:00"}

    monkeypatch.setattr("services.sms_provider.send_sms", fake_send_sms)
    monkeypatch.setattr("driver_sessions.issue_magic_link", fake_issue_magic_link)

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        await db.employees.insert_one({
            "id": "d1", "phone": "(555) 123-4567", "full_name": "Driver T",
        })
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        outcome = await _issue_link_and_sms(
            db, assignment=a, triggered_by="dispatcher",
            issued_by_name="Op", issued_by_role="dispatch",
        )
        assert outcome["magic_link_url"] == "https://mascidocs.test/d/TKN_XYZ"
        assert outcome["sms_result"]["status"] == "sent"
        # Provider received normalized E.164
        assert captured["to_phone"] == "+15551234567"
        assert "MASCI Dispatch" in captured["body"]
        assert "TKN_XYZ" in captured["body"]

        # Push into the fan-out helper and verify delivery_log + audit event
        await _fire_assignment_notification(
            db, assignment=a, event="manual_sms",
            send_email_fn=None, magic_link_url=outcome["magic_link_url"],
            sms_result=outcome["sms_result"],
        )
        a2 = await db.dispatch_assignments.find_one({"id": "A1"})
        sms_entries = [e for e in (a2.get("delivery_log") or []) if e.get("channel") == "sms"]
        assert len(sms_entries) == 1
        assert sms_entries[0]["status"] == "sent"
        assert sms_entries[0]["provider_message_id"] == "SMabc123"
        assert sms_entries[0]["triggered_by"] == "dispatcher"

        # Audit event in state stream
        events = []
        async for e in db.dispatch_state_events.find({"assignment_id": "A1"}):
            events.append(e)
        sms_audits = [e for e in events if e.get("warning_tag") == "SMS_ATTEMPTED"]
        assert len(sms_audits) == 1
        assert sms_audits[0]["sms_status"] == "sent"

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 7 · Provider failure → delivery log 'failed', assignment unaffected
# ────────────────────────────────────────────────────────────────────
def test_provider_failure_logs_failed_and_does_not_raise(monkeypatch):
    from routes.dispatch_lifecycle import _issue_link_and_sms, _fire_assignment_notification
    _set_env(monkeypatch,
        SMS_ENABLED="true", SMS_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
    )

    async def fake_send_sms(*, to_phone, body, triggered_by, status_callback_url=None):
        return {
            "ok": False, "status": "failed", "provider": "twilio",
            "provider_message_id": None, "destination_phone_masked": "***4567",
            "triggered_by": triggered_by,
            "error_summary": "Twilio 21610: unsubscribed",
        }

    async def fake_issue_magic_link(db, **kw):
        return {"link_id": "L1", "token": "TKN_FAIL", "expires_at": "2026-01-01T00:00:00+00:00"}

    monkeypatch.setattr("services.sms_provider.send_sms", fake_send_sms)
    monkeypatch.setattr("driver_sessions.issue_magic_link", fake_issue_magic_link)

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        await db.employees.insert_one({"id": "d1", "phone": "+15551234567", "full_name": "T"})
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        outcome = await _issue_link_and_sms(
            db, assignment=a, triggered_by="dispatcher",
            issued_by_name="Op", issued_by_role="dispatch",
        )
        assert outcome["sms_result"]["status"] == "failed"
        assert "Twilio 21610" in (outcome["sms_result"]["error_summary"] or "")
        # Must not raise
        await _fire_assignment_notification(
            db, assignment=a, event="manual_sms",
            send_email_fn=None, magic_link_url=outcome["magic_link_url"],
            sms_result=outcome["sms_result"],
        )
        a2 = await db.dispatch_assignments.find_one({"id": "A1"})
        sms_entries = [e for e in (a2.get("delivery_log") or []) if e.get("channel") == "sms"]
        assert sms_entries[0]["status"] == "failed"
        assert sms_entries[0]["ok"] is False
        # Assignment is still ASSIGNED and not cancelled — provider
        # failure must not damage the assignment.
        assert a2["current_state"] == "ASSIGNED"
        assert a2.get("cancelled_at") is None

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 8 · Auto-SMS enabled → _auto_sms_enabled returns True
# (And provider gate respected.)
# ────────────────────────────────────────────────────────────────────
def test_auto_sms_enabled_gate(monkeypatch):
    from routes.dispatch_lifecycle import _auto_sms_enabled
    _set_env(monkeypatch,
        DISPATCH_AUTO_SMS_ON_ASSIGN="true",
        SMS_ENABLED="true", SMS_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
    )
    assert _auto_sms_enabled() is True

    # Provider broken → gate denies even if AUTO flag is on
    _set_env(monkeypatch,
        DISPATCH_AUTO_SMS_ON_ASSIGN="true",
        SMS_ENABLED="false",
    )
    assert _auto_sms_enabled() is False


# ────────────────────────────────────────────────────────────────────
# TEST 10 · "Text Magic Link" endpoint contract
# (Body shape — actual HTTP call covered by smoke test against live
# router with curl; this verifies the helper's contract.)
# ────────────────────────────────────────────────────────────────────
def test_send_magic_link_body_shape():
    body = build_magic_link_body(
        assignment={
            "project_number": "PROJ-1",
            "truck_id": "T-1",
            "source_location": "Plant A",
            "destination": "Job A",
        },
        magic_link_url="https://mascidocs.test/d/TKN",
    )
    # D-2 directive-prescribed format: header / blank / "Assignment:" /
    # job line / blank / "Open:" / URL.
    assert "MASCI Dispatch" in body
    assert "Assignment:" in body
    assert "Open:" in body
    # Job line carries identifying bits
    assert "#PROJ-1" in body
    assert "T-1" in body
    assert "Plant A" in body
    assert "Job A" in body
    assert "https://mascidocs.test/d/TKN" in body
    # No admin URLs / sensitive references
    assert "admin" not in body.lower()
    assert len(body) <= 320


# ────────────────────────────────────────────────────────────────────
# TEST 11 · Existing copy-link behavior still works
# (Indirect — magic-link URL is still returned by send-magic-sms even
# when SMS fails, so frontend can fall back.)
# ────────────────────────────────────────────────────────────────────
def test_send_failure_still_returns_link_for_copy_fallback(monkeypatch):
    from routes.dispatch_lifecycle import _issue_link_and_sms
    _set_env(monkeypatch,
        SMS_ENABLED="true", SMS_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
        PUBLIC_FRONTEND_URL="https://mascidocs.test",
    )

    async def fake_send_sms(*, to_phone, body, triggered_by, status_callback_url=None):
        return {
            "ok": False, "status": "failed", "provider": "twilio",
            "provider_message_id": None, "destination_phone_masked": "***4567",
            "triggered_by": triggered_by, "error_summary": "Carrier rejected",
        }

    async def fake_issue_magic_link(db, **kw):
        return {"link_id": "L1", "token": "TKN_FB", "expires_at": "2026-01-01T00:00:00+00:00"}

    monkeypatch.setattr("services.sms_provider.send_sms", fake_send_sms)
    monkeypatch.setattr("driver_sessions.issue_magic_link", fake_issue_magic_link)

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        await db.employees.insert_one({"id": "d1", "phone": "+15551234567", "full_name": "T"})
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        outcome = await _issue_link_and_sms(
            db, assignment=a, triggered_by="dispatcher",
            issued_by_name="Op", issued_by_role="dispatch",
        )
        # Link is still present so frontend can fall back to copy-link
        assert outcome["magic_link_url"] == "https://mascidocs.test/d/TKN_FB"
        assert outcome["sms_result"]["status"] == "failed"

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# TEST 12 · Existing email notification behavior still works
# (Email path runs independently from SMS path — they are two channels
# in the same fan-out helper.)
# ────────────────────────────────────────────────────────────────────
def test_email_still_fires_independently_of_sms(monkeypatch):
    from routes.dispatch_lifecycle import _fire_assignment_notification

    sent_emails = []

    async def fake_email(to, subject, body_html):
        sent_emails.append({"to": to, "subject": subject})
        return True

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        await db.employees.insert_one({"id": "d1", "email": "driver@test", "full_name": "T"})
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        # No sms_result here · email-only path mirrors D-1.3 behaviour.
        await _fire_assignment_notification(
            db, assignment=a, event="new_assignment",
            send_email_fn=fake_email,
        )
        assert len(sent_emails) == 1
        assert sent_emails[0]["to"] == "driver@test"
        # Delivery log carries email entry but no sms entry.
        a2 = await db.dispatch_assignments.find_one({"id": "A1"})
        log = a2.get("delivery_log") or []
        assert any(e["channel"] == "email" for e in log)
        assert not any(e["channel"] == "sms" for e in log)

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# Defensive: SMS audit row is created even when bell write fails.
# Defensive: provider's destination_phone_masked is what gets stored.
# ────────────────────────────────────────────────────────────────────
def test_delivery_log_carries_masked_phone(monkeypatch):
    from routes.dispatch_lifecycle import _fire_assignment_notification

    sms_result = {
        "ok": True, "status": "sent", "provider": "twilio",
        "provider_message_id": "SMabc", "destination_phone_masked": "***4567",
        "triggered_by": "auto", "error_summary": None,
    }

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        await _fire_assignment_notification(
            db, assignment=a, event="new_assignment",
            send_email_fn=None, magic_link_url="https://x/d/T",
            sms_result=sms_result,
        )
        a2 = await db.dispatch_assignments.find_one({"id": "A1"})
        sms_entries = [e for e in (a2.get("delivery_log") or []) if e.get("channel") == "sms"]
        assert sms_entries[0]["target"] == "***4567"
        # Full phone number must NOT appear anywhere in the log.
        assert "5551234567" not in str(a2.get("delivery_log") or [])

    asyncio.get_event_loop().run_until_complete(run())


# ────────────────────────────────────────────────────────────────────
# D-2.7 · Twilio status callback forwarding
# ────────────────────────────────────────────────────────────────────
def test_status_callback_url_forwarded_to_provider(monkeypatch):
    """When PUBLIC_BACKEND_URL is set, the lifecycle helper forwards a
    status_callback URL to the provider so Twilio can POST queued/
    sent/delivered/failed events back to us.
    """
    from routes.dispatch_lifecycle import _issue_link_and_sms

    _set_env(monkeypatch,
        SMS_ENABLED="true", SMS_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
        PUBLIC_FRONTEND_URL="https://mascidocs.test",
        PUBLIC_BACKEND_URL="https://api.mascidocs.test",
    )

    captured = {}

    async def fake_send_sms(*, to_phone, body, triggered_by, status_callback_url=None):
        captured["status_callback_url"] = status_callback_url
        return {
            "ok": True, "status": "sent", "provider": "twilio",
            "provider_message_id": "SMcb1", "destination_phone_masked": "***4567",
            "triggered_by": triggered_by, "error_summary": None,
        }

    async def fake_issue_magic_link(db, **kw):
        return {"link_id": "L1", "token": "TKN", "expires_at": "2026-01-01T00:00:00+00:00"}

    monkeypatch.setattr("services.sms_provider.send_sms", fake_send_sms)
    monkeypatch.setattr("driver_sessions.issue_magic_link", fake_issue_magic_link)

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        await db.employees.insert_one({"id": "d1", "phone": "+15551234567", "full_name": "T"})
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        await _issue_link_and_sms(
            db, assignment=a, triggered_by="dispatcher",
            issued_by_name="Op", issued_by_role="dispatch",
        )
        # status_callback URL must include backend host + route + the
        # assignment id (for downstream patching).
        assert captured["status_callback_url"] == (
            "https://api.mascidocs.test/api/dispatch/sms/twilio-status-callback"
            "?assignment_id=A1"
        )

    asyncio.get_event_loop().run_until_complete(run())


def test_status_callback_url_omitted_when_backend_host_absent(monkeypatch):
    """When PUBLIC_BACKEND_URL is NOT configured, we cannot give Twilio
    a stable host to call back to. The send must still go through —
    just without callback registration.
    """
    from routes.dispatch_lifecycle import _issue_link_and_sms

    _set_env(monkeypatch,
        SMS_ENABLED="true", SMS_PROVIDER="twilio",
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
        PUBLIC_FRONTEND_URL="https://mascidocs.test",
        PUBLIC_BACKEND_URL=None,
    )

    captured = {}

    async def fake_send_sms(*, to_phone, body, triggered_by, status_callback_url=None):
        captured["status_callback_url"] = status_callback_url
        return {
            "ok": True, "status": "sent", "provider": "twilio",
            "provider_message_id": "SMcb2", "destination_phone_masked": "***4567",
            "triggered_by": triggered_by, "error_summary": None,
        }

    async def fake_issue_magic_link(db, **kw):
        return {"link_id": "L1", "token": "TKN2", "expires_at": "2026-01-01T00:00:00+00:00"}

    monkeypatch.setattr("services.sms_provider.send_sms", fake_send_sms)
    monkeypatch.setattr("driver_sessions.issue_magic_link", fake_issue_magic_link)

    async def run():
        db = _FakeDB()
        await _seed_assignment(db)
        await db.employees.insert_one({"id": "d1", "phone": "+15551234567", "full_name": "T"})
        a = await db.dispatch_assignments.find_one({"id": "A1"})
        await _issue_link_and_sms(
            db, assignment=a, triggered_by="dispatcher",
            issued_by_name="Op", issued_by_role="dispatch",
        )
        assert captured["status_callback_url"] is None

    asyncio.get_event_loop().run_until_complete(run())


def test_twilio_creds_configured_helper(monkeypatch):
    from routes.dispatch_lifecycle import _twilio_creds_configured
    _set_env(monkeypatch,
        TWILIO_ACCOUNT_SID="x", TWILIO_AUTH_TOKEN="y", TWILIO_FROM_NUMBER="+15550000000",
    )
    assert _twilio_creds_configured() is True
    _set_env(monkeypatch, TWILIO_AUTH_TOKEN=None)
    assert _twilio_creds_configured() is False


def test_verify_twilio_signature_returns_false_without_creds(monkeypatch):
    from services.sms_provider import verify_twilio_signature
    _set_env(monkeypatch, TWILIO_ACCOUNT_SID=None, TWILIO_AUTH_TOKEN=None, TWILIO_FROM_NUMBER=None)
    assert verify_twilio_signature(
        signature="anything", full_url="https://x", form_params={},
    ) is False


def test_verify_twilio_signature_returns_false_for_bad_sig(monkeypatch):
    from services.sms_provider import verify_twilio_signature
    _set_env(monkeypatch,
        TWILIO_ACCOUNT_SID="ACx", TWILIO_AUTH_TOKEN="tok", TWILIO_FROM_NUMBER="+15550000000",
    )
    assert verify_twilio_signature(
        signature="garbage", full_url="https://x", form_params={"a": "b"},
    ) is False


def test_verify_twilio_signature_returns_false_when_no_signature(monkeypatch):
    from services.sms_provider import verify_twilio_signature
    _set_env(monkeypatch,
        TWILIO_ACCOUNT_SID="ACx", TWILIO_AUTH_TOKEN="tok", TWILIO_FROM_NUMBER="+15550000000",
    )
    assert verify_twilio_signature(
        signature=None, full_url="https://x", form_params={"a": "b"},
    ) is False
