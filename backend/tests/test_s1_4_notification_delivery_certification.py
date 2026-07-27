from __future__ import annotations

import sys
import types
from datetime import datetime, timedelta, timezone

import pytest

from lib.notification_delivery import deliver_notification
from lib.preview_notification_certification import (
    STATUS_ACTIVE,
    STATUS_EXPIRED,
    STATUS_RECONCILED,
    STATUS_RETRYABLE_FAILURE_PENDING_RETRY,
    STATUS_USED_PENDING_RECONCILIATION,
    OVERRIDE_COLLECTION,
    provision_preview_live_override,
    record_provider_api_reconciliation,
    record_provider_attempt_result,
    record_webhook_reconciliation,
    resolve_active_preview_live_override,
    send_claim_matches,
)


class _UpdateResult:
    def __init__(self, matched_count: int = 1) -> None:
        self.matched_count = matched_count


class _Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def insert_one(self, doc):
        self.rows.append(dict(doc))
        return {"inserted_id": len(self.rows)}

    async def find_one(self, query, projection=None, sort=None):
        rows = [row for row in self.rows if _matches(row, query)]
        if sort and rows:
            key, direction = sort[0]
            rows = sorted(rows, key=lambda r: _lookup(r, key), reverse=direction < 0)
        if not rows:
            return None
        return _project(rows[0], projection)

    async def update_one(self, query, update, upsert=False):
        for row in self.rows:
            if _matches(row, query):
                _apply_update(row, update)
                return _UpdateResult(1)
        if upsert:
            doc = dict(query)
            _apply_update(doc, update)
            self.rows.append(doc)
            return _UpdateResult(1)
        return _UpdateResult(0)


def _lookup(doc, dotted: str):
    value = doc
    for part in dotted.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _matches(doc, query) -> bool:
    for key, expected in (query or {}).items():
        actual = _lookup(doc, key)
        if isinstance(expected, dict) and "$in" in expected:
            if actual not in expected["$in"]:
                return False
            continue
        if isinstance(actual, list) and not isinstance(expected, list):
            if expected not in actual:
                return False
            continue
        if actual != expected:
            return False
    return True


def _project(doc, projection):
    if projection is None:
        return dict(doc)
    include_keys = [k for k, v in projection.items() if v]
    if include_keys:
        out = {}
        for key in include_keys:
            out[key] = _lookup(doc, key)
        return out
    out = dict(doc)
    for key, value in projection.items():
        if value == 0 and key in out:
            out.pop(key, None)
    return out


def _apply_update(doc, update):
    for key, payload in (update or {}).items():
        if key == "$set":
            for field, value in payload.items():
                doc[field] = value


class _FakeDb:
    def __init__(self) -> None:
        self.notification_capture_v1 = _Collection()
        self.daily_reports = _Collection([{"id": "dr-cert-1"}])
        self.notifications = _Collection()
        self.collections = {
            OVERRIDE_COLLECTION: _Collection(),
        }

    def __getitem__(self, name: str):
        return self.collections.setdefault(name, _Collection())


@pytest.mark.asyncio
async def test_provision_preview_override_preserves_original_and_actual_recipients(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("EMAIL_SAFETY_MODE", "strict")
    db = _FakeDb()

    row = await provision_preview_live_override(
        db,
        workflow="daily-report",
        record={
            "id": "dr-cert-1",
            "doc_id": "DR-2026-00001",
            "project_number": "ZZ-RUNTIME-CERT-2026",
            "project_name": "Runtime Certification — Internal Test Project",
            "prepared_by": "Certification Foreman",
            "certification_record": True,
            "certification_run_id": "run-s1-4-001",
            "certification_track_id": "S1-4",
            "certification_release_reason": "notification_delivery_certification",
            "certification_delivery_override_requested": True,
            "certification_authorized_recipient": "jaymn.judd@mascigc.com",
            "certification_override_ttl_minutes": 10,
        },
        original_intended_recipients=["pm.one@mascigc.com", "pm.two@mascigc.com"],
    )

    assert row is not None
    assert row["actual_recipient"] == "jaymn.judd@mascigc.com"
    assert row["original_intended_recipients"] == [
        "pm.one@mascigc.com",
        "pm.two@mascigc.com",
    ]
    assert row["status"] == STATUS_ACTIVE

    stored = await db[OVERRIDE_COLLECTION].find_one({"id": row["id"]}, {"_id": 0})
    assert stored["preview_only"] is True
    assert stored["single_notification_record"] is True
    dr = await db.daily_reports.find_one({"id": "dr-cert-1"}, {"_id": 0})
    assert dr["notification_actual_recipient"] == "jaymn.judd@mascigc.com"
    assert dr["notification_original_intended_recipients"] == [
        "pm.one@mascigc.com",
        "pm.two@mascigc.com",
    ]


@pytest.mark.asyncio
async def test_resolve_override_fails_closed_on_expiry_or_recipient_mismatch(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    db = _FakeDb()
    expired_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    db[OVERRIDE_COLLECTION].rows.append(
        {
            "id": "ovr-1",
            "workflow": "daily-report",
            "record_id": "dr-cert-1",
            "actual_recipient": "jaymn.judd@mascigc.com",
            "status": STATUS_ACTIVE,
            "expires_at": expired_at,
        }
    )

    resolved = await resolve_active_preview_live_override(
        db,
        workflow="daily-report",
        record_id="dr-cert-1",
        recipients=["jaymn.judd@mascigc.com"],
    )
    assert resolved is None
    stored = await db[OVERRIDE_COLLECTION].find_one({"id": "ovr-1"}, {"_id": 0})
    assert stored["status"] == STATUS_EXPIRED

    db[OVERRIDE_COLLECTION].rows = [
        {
            "id": "ovr-2",
            "workflow": "daily-report",
            "record_id": "dr-cert-1",
            "actual_recipient": "jaymn.judd@mascigc.com",
            "status": STATUS_ACTIVE,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }
    ]
    mismatch = await resolve_active_preview_live_override(
        db,
        workflow="daily-report",
        record_id="dr-cert-1",
        recipients=["other@mascigc.com"],
    )
    assert mismatch is None


def test_send_claim_matches_only_exact_single_recipient(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    from lib.preview_notification_certification import activate_send_claim, clear_send_claim

    token = activate_send_claim(
        {
            "id": "ovr-1",
            "workflow": "daily-report",
            "record_id": "dr-cert-1",
            "actual_recipient": "jaymn.judd@mascigc.com",
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }
    )
    try:
        assert send_claim_matches({"to": ["jaymn.judd@mascigc.com"]}) is True
        assert send_claim_matches({"to": ["jaymn.judd@mascigc.com"], "cc": ["extra@mascigc.com"]}) is False
        assert send_claim_matches({"to": ["someone@mascigc.com"]}) is False
    finally:
        clear_send_claim(token)


@pytest.mark.asyncio
async def test_record_attempt_and_reconciliation_update_proof_source(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    db = _FakeDb()
    db[OVERRIDE_COLLECTION].rows.append(
        {
            "id": "ovr-1",
            "workflow": "daily-report",
            "record_id": "dr-cert-1",
            "record_doc_id": "DR-2026-00001",
            "certification_run_id": "run-s1-4-001",
            "actual_recipient": "jaymn.judd@mascigc.com",
            "original_intended_recipients": ["pm@mascigc.com"],
            "status": STATUS_ACTIVE,
            "attempt_count": 0,
            "provider_message_ids": [],
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
            "record_snapshot": {"project_number": "ZZ-RUNTIME-CERT-2026"},
        }
    )

    await record_provider_attempt_result(
        db,
        override=db[OVERRIDE_COLLECTION].rows[0],
        delivery={
            "notification_state": "provider_accepted",
            "provider_message_id": "msg-1",
            "failure_reason": None,
        },
    )
    stored = await db[OVERRIDE_COLLECTION].find_one({"id": "ovr-1"}, {"_id": 0})
    assert stored["status"] == STATUS_USED_PENDING_RECONCILIATION
    assert stored["provider_message_ids"] == ["msg-1"]

    await record_webhook_reconciliation(
        db,
        provider_message_id="msg-1",
        kind="notification_delivery_delivered",
        payload={"event_type": "email.delivered"},
    )
    stored = await db[OVERRIDE_COLLECTION].find_one({"id": "ovr-1"}, {"_id": 0})
    assert stored["status"] == STATUS_RECONCILED
    assert stored["final_proof_source"] == "WEBHOOK"

    await record_provider_api_reconciliation(
        db,
        provider_message_id="msg-1",
        payload={"id": "msg-1", "to": ["jaymn.judd@mascigc.com"]},
    )
    stored = await db[OVERRIDE_COLLECTION].find_one({"id": "ovr-1"}, {"_id": 0})
    assert stored["final_proof_source"] == "BOTH"


@pytest.mark.asyncio
async def test_record_attempt_retryable_failure_stays_retry_eligible(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    db = _FakeDb()
    override = {
        "id": "ovr-2",
        "workflow": "daily-report",
        "record_id": "dr-cert-1",
        "actual_recipient": "jaymn.judd@mascigc.com",
        "original_intended_recipients": ["pm@mascigc.com"],
        "attempt_count": 0,
    }
    db[OVERRIDE_COLLECTION].rows.append(dict(override))

    await record_provider_attempt_result(
        db,
        override=override,
        delivery={
            "notification_state": "retryable_failure",
            "failure_reason": "temporary timeout",
        },
    )
    stored = await db[OVERRIDE_COLLECTION].find_one({"id": "ovr-2"}, {"_id": 0})
    assert stored["status"] == STATUS_RETRYABLE_FAILURE_PENDING_RETRY
    assert stored["attempt_count"] == 1


@pytest.mark.asyncio
async def test_deliver_notification_uses_override_for_live_send_in_preview(monkeypatch):
    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("EMAIL_SAFETY_MODE", "strict")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_preview_live_123456")
    db = _FakeDb()
    db[OVERRIDE_COLLECTION].rows.append(
        {
            "id": "ovr-live-1",
            "workflow": "daily-report",
            "record_id": "dr-cert-1",
            "actual_recipient": "jaymn.judd@mascigc.com",
            "status": STATUS_ACTIVE,
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }
    )

    fake_resend = types.SimpleNamespace(
        api_key="",
        Emails=types.SimpleNamespace(send=lambda params: {"id": "provider-msg-1", "to": params.get("to")}),
    )
    monkeypatch.setitem(sys.modules, "resend", fake_resend)

    import branding_resolver

    async def _sender(_db):
        return "onboarding@resend.dev"

    async def _reply(_db):
        return "reply@mascigc.com"

    monkeypatch.setattr(branding_resolver, "resolve_sender_email", _sender)
    monkeypatch.setattr(branding_resolver, "resolve_reply_to_email", _reply)

    delivery = await deliver_notification(
        db=db,
        workflow="daily-report",
        correlation_id="cid-1",
        record_id="dr-cert-1",
        recipients=["jaymn.judd@mascigc.com"],
        subject="S1-4 test",
        html="<p>live preview certification</p>",
        metadata={"test": True},
    )

    assert delivery["notification_state"] == "provider_accepted"
    assert delivery["provider_called"] is True
    assert delivery["provider_message_id"] == "provider-msg-1"
    assert delivery["delivery_mode"] == "PROVIDER_LIVE"
    assert delivery["certification_override"] is True
    assert db.notification_capture_v1.rows == []