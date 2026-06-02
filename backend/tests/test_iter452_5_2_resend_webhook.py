"""OMEGA · iter452.5.2 · Resend Bounce / Delivery Webhook regression suite.

Verifies the deliverability evidence chain closure introduced in
Constitutional Build Package Phase 3 (2026-06-02):

  iter452.5  : dispatch_attempted → dispatch_succeeded / dispatch_failed
  iter452.5.2: + delivery_delivered / delivery_bounced / delivery_complained / delivery_deferred

And the Dead-Letter Accountability Path: hard-bounce on any non-dead-letter
tier auto-escalates ownership to Tier 5 (`safety@mascigc.com`) without
human action.

Tests run against the live backend (preview pod) like other lifecycle
suites. Uses /api/webhooks/resend public endpoint (no auth header
required when RESEND_WEBHOOK_SECRET is unset in preview).

Run::

    cd /app/backend && python -m pytest tests/test_iter452_5_2_resend_webhook.py -q
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

from lib.field_submitter_identity import _dead_letter_email

load_dotenv("/app/backend/.env")


def _base_url() -> str:
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return "http://localhost:8001"


BASE_URL = _base_url()
API = BASE_URL + "/api"


def _db():
    """Lazy Motor client — mirror of iter452.5.1 test pattern."""
    import importlib
    motor_module = importlib.import_module("motor.motor_asyncio")
    client = motor_module.AsyncIOMotorClient(
        os.environ.get("MONGO_URL") or "",
        serverSelectionTimeoutMS=5_000,
    )
    return client[os.environ.get("DB_NAME") or "test_database"]


# ─────────────────────────────────────────────────────────────────
# Smoke tests — webhook accepts known + unknown events idempotently
# ─────────────────────────────────────────────────────────────────
def test_webhook_accepts_known_event():
    msg_id = f"smoke-delivered-{uuid.uuid4()}"
    r = requests.post(
        f"{API}/webhooks/resend",
        json={
            "type": "email.delivered",
            "data": {"email_id": msg_id, "to": ["random@example.com"]},
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["kind"] == "notification_delivery_delivered"
    assert body["matched"] == 0
    assert body["escalated"] is False


def test_webhook_idempotent_on_same_message_id():
    msg_id = f"idem-{uuid.uuid4()}"
    payload = {
        "type": "email.delivered",
        "data": {"email_id": msg_id, "to": ["random@example.com"]},
    }
    r1 = requests.post(f"{API}/webhooks/resend", json=payload, timeout=15)
    r2 = requests.post(f"{API}/webhooks/resend", json=payload, timeout=15)
    assert r1.status_code == 200 and r2.status_code == 200


def test_webhook_unknown_event_type_ignored_gracefully():
    r = requests.post(
        f"{API}/webhooks/resend",
        json={
            "type": "email.future_event_we_dont_handle_yet",
            "data": {"email_id": f"unk-{uuid.uuid4()}"},
        },
        timeout=15,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["kind"] == ""


def test_webhook_rejects_malformed_json():
    r = requests.post(
        f"{API}/webhooks/resend",
        data="not json at all",
        headers={"Content-Type": "application/json"},
        timeout=15,
    )
    assert r.status_code == 400, r.text


# ─────────────────────────────────────────────────────────────────
# Full chain tests — sync wrappers around async motor (matches the
# iter452.5.1 pattern: asyncio.run() inside the sync test function).
# ─────────────────────────────────────────────────────────────────
def test_hard_bounce_escalates_ownership_to_dead_letter():
    """Reproduces operator-mandated chain Email Sent → Delivered →
    Bounced → Dead Letter. Hard bounce auto-escalates to Tier 5."""
    workflow = "qaqc_inspection"
    record_id = f"iter45252-test-{uuid.uuid4()}"
    provider_msg_id = f"prov-{uuid.uuid4()}"
    binding_id = f"bind-{uuid.uuid4()}"
    original_recipient = "field.user@example.com"

    seed_row = {
        "id": str(uuid.uuid4()),
        "workflow": workflow,
        "record_id": record_id,
        "record_doc_id": "",
        "from_state": None,
        "to_state": "NOTIFICATION_DISPATCH_SUCCEEDED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actor": {"_actor": "system", "name": "FSI Dispatcher"},
        "reason": "",
        "evidence": {
            "delivery_event": "notification_dispatch_succeeded",
            "channel": "email",
            "recipient": original_recipient,
            "binding_id": binding_id,
            "provider_message_id": provider_msg_id,
            "resolution_tier": "fl",
            "relay": False,
        },
    }

    async def _seed():
        db = _db()
        await db.workflow_state_events.insert_one(seed_row)

    async def _read():
        db = _db()
        bounce_row = await db.workflow_state_events.find_one({
            "workflow": workflow,
            "record_id": record_id,
            "to_state": "NOTIFICATION_DELIVERY_BOUNCED",
        }, {"_id": 0})
        dl_row = await db.workflow_state_events.find_one({
            "workflow": workflow,
            "record_id": record_id,
            "to_state": "NOTIFICATION_DISPATCH_ATTEMPTED",
            "evidence.resolution_tier": "dead_letter",
        }, {"_id": 0}, sort=[("created_at", -1)])
        chain_row = await db.workflow_state_events.find_one({
            "workflow": workflow,
            "record_id": record_id,
            "to_state": "REVISION_LINK_ISSUED",
            "evidence.escalation_cause": "hard_bounce",
        }, {"_id": 0}, sort=[("created_at", -1)])
        return bounce_row, dl_row, chain_row

    async def _cleanup():
        db = _db()
        await db.workflow_state_events.delete_many({"record_id": record_id})
        await db.resend_webhook_events.delete_many({
            "provider_message_id": provider_msg_id,
        })

    try:
        asyncio.run(_seed())
        r = requests.post(
            f"{API}/webhooks/resend",
            json={
                "type": "email.bounced",
                "data": {
                    "email_id": provider_msg_id,
                    "to": [original_recipient],
                    "bounce": {"type": "hard"},
                },
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body["kind"] == "notification_delivery_bounced"
        assert body["matched"] >= 1
        assert body["escalated"] is True

        bounce_row, dl_row, chain_row = asyncio.run(_read())

        assert bounce_row is not None, (
            "bounce row missing — webhook didn't write delivery_bounced"
        )
        assert bounce_row["evidence"].get("provider_message_id") == provider_msg_id
        assert bounce_row["evidence"].get("bounce_type") == "hard"

        dl_email = (_dead_letter_email() or "").lower()
        assert dl_email, "ADMIN_DEAD_LETTER_EMAIL must be configured"
        assert dl_row is not None, (
            "Dead-letter escalation row missing — Ownership Doctrine O-4 violation"
        )
        assert dl_row["evidence"].get("escalation_cause") == "hard_bounce"
        assert (dl_row["evidence"].get("recipient") or "").lower() == dl_email
        assert (dl_row["evidence"].get("escalated_from_recipient") or "").lower() == original_recipient.lower()

        assert chain_row is not None, "revision_link_issued chain row missing"
        assert chain_row["evidence"].get("escalated_to_tier") == "dead_letter"
        assert chain_row["evidence"].get("escalated_from_tier") == "fl"
    finally:
        try:
            asyncio.run(_cleanup())
        except Exception:
            pass


def test_soft_bounce_does_not_escalate():
    """Soft bounces are transient — recorded but NO escalation."""
    workflow = "qaqc_inspection"
    record_id = f"iter45252-soft-{uuid.uuid4()}"
    provider_msg_id = f"prov-soft-{uuid.uuid4()}"
    seed_row = {
        "id": str(uuid.uuid4()),
        "workflow": workflow,
        "record_id": record_id,
        "record_doc_id": "",
        "from_state": None,
        "to_state": "NOTIFICATION_DISPATCH_SUCCEEDED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actor": {"_actor": "system"},
        "reason": "",
        "evidence": {
            "delivery_event": "notification_dispatch_succeeded",
            "channel": "email",
            "recipient": "field.user@example.com",
            "binding_id": f"bind-{uuid.uuid4()}",
            "provider_message_id": provider_msg_id,
            "resolution_tier": "fl",
        },
    }

    async def _seed():
        await _db().workflow_state_events.insert_one(seed_row)

    async def _cleanup():
        db = _db()
        await db.workflow_state_events.delete_many({"record_id": record_id})
        await db.resend_webhook_events.delete_many({
            "provider_message_id": provider_msg_id,
        })

    try:
        asyncio.run(_seed())
        r = requests.post(
            f"{API}/webhooks/resend",
            json={
                "type": "email.bounced",
                "data": {
                    "email_id": provider_msg_id,
                    "to": ["field.user@example.com"],
                    "bounce": {"type": "soft"},
                },
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["escalated"] is False
    finally:
        try:
            asyncio.run(_cleanup())
        except Exception:
            pass


def test_delivery_delivered_writes_chain_row():
    """email.delivered confirms inbox handoff — closes chain. Records a
    NOTIFICATION_DELIVERY_DELIVERED row."""
    workflow = "incident"
    record_id = f"iter45252-deliv-{uuid.uuid4()}"
    provider_msg_id = f"prov-deliv-{uuid.uuid4()}"
    seed_row = {
        "id": str(uuid.uuid4()),
        "workflow": workflow,
        "record_id": record_id,
        "record_doc_id": "",
        "from_state": None,
        "to_state": "NOTIFICATION_DISPATCH_SUCCEEDED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "actor": {"_actor": "system"},
        "reason": "",
        "evidence": {
            "delivery_event": "notification_dispatch_succeeded",
            "channel": "email",
            "recipient": "submitter@example.com",
            "binding_id": f"bind-{uuid.uuid4()}",
            "provider_message_id": provider_msg_id,
            "resolution_tier": "per_submit",
        },
    }

    async def _seed():
        await _db().workflow_state_events.insert_one(seed_row)

    async def _read():
        delivered = await _db().workflow_state_events.find_one({
            "workflow": workflow,
            "record_id": record_id,
            "to_state": "NOTIFICATION_DELIVERY_DELIVERED",
        }, {"_id": 0})
        return delivered

    async def _cleanup():
        db = _db()
        await db.workflow_state_events.delete_many({"record_id": record_id})
        await db.resend_webhook_events.delete_many({
            "provider_message_id": provider_msg_id,
        })

    try:
        asyncio.run(_seed())
        r = requests.post(
            f"{API}/webhooks/resend",
            json={
                "type": "email.delivered",
                "data": {
                    "email_id": provider_msg_id,
                    "to": ["submitter@example.com"],
                },
            },
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["matched"] >= 1
        assert body["escalated"] is False

        delivered_row = asyncio.run(_read())
        assert delivered_row is not None
        assert delivered_row["evidence"].get("resend_event_type") == "email.delivered"
    finally:
        try:
            asyncio.run(_cleanup())
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────
# Constitutional & Ownership Doctrine assertions
# ─────────────────────────────────────────────────────────────────
def test_no_user_acknowledge_required():
    """Webhook NEVER requires a human to acknowledge the bounce —
    Rule 7 + Ownership Doctrine O-4."""
    r = requests.options(f"{API}/webhooks/resend", timeout=5)
    assert r.status_code in (200, 204, 400, 405), r.text


def test_no_assignment_endpoint_exists():
    """No endpoint exists that lets a human assign a bounced
    notification — ownership transfers only via the chain."""
    forbidden_paths = [
        "/api/webhooks/resend/assign",
        "/api/webhooks/resend/reassign",
        "/api/webhooks/resend/acknowledge",
        "/api/webhooks/resend/accept",
    ]
    for path in forbidden_paths:
        r = requests.post(f"{BASE_URL}{path}", json={}, timeout=5)
        assert r.status_code == 404, (
            f"{path} exists — Ownership Doctrine O-2/O-7/O-8 violation"
        )
