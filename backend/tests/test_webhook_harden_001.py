"""WEBHOOK-HARDEN-001 · Retryable failure when provider credentials are missing.

Pins the contract:
  1. Missing Motive credentials → HTTP 503 (retryable)
  2. Missing credentials still creates the credential-missing alert
  3. Missing credentials does NOT store the event as accepted
  4. Valid credentials + valid signature → HTTP 200
  5. Valid credentials + valid signature → event persisted
  6. Invalid signature → HTTP 401 (no false success)
  7. Existing Motive sync behavior unaffected (smoke)
  8. Credential auto-resolve unaffected (smoke)

Fixes WEBHOOK-2XX-ON-MISCONFIG-001.

Runs with:
    cd /app/backend && pytest tests/test_webhook_harden_001.py -q -W ignore::DeprecationWarning
"""
from __future__ import annotations
import asyncio
import hashlib
import hmac
import importlib
import json
import os
import sys
import time
import uuid

import pytest
from pymongo import MongoClient


# ── Session-scoped client + DB ────────────────────────────────────────
# Boot the server ONCE per test session. Use a stable _preview-suffixed
# DB so the env-safety guard accepts it. Cleanup between tests.

_SESSION_DB_NAME = f"masci_test_webhook_harden_{uuid.uuid4().hex[:8]}_preview"


@pytest.fixture(scope="session")
def app_client():
    sys.path.insert(0, "/app/backend")
    os.environ["DB_NAME"] = _SESSION_DB_NAME
    srv = sys.modules.get("server") or importlib.import_module("server")
    from fastapi.testclient import TestClient
    srv.app.state.ready = True
    # Use TestClient as a context manager so its event loop persists
    # across all tests in the session — motor's collection handles
    # remain bound to one stable loop. Otherwise each request creates
    # and destroys a loop, leaving motor with stale executor handles.
    with TestClient(srv.app) as client:
        yield client


@pytest.fixture()
def db():
    """Sync pymongo handle for state setup/inspection."""
    return MongoClient(os.environ["MONGO_URL"])[_SESSION_DB_NAME]


def _seed_motive(db, *, secret: str = "", api_key: str = "", enabled: bool = False, test_mode: bool = False):
    db.integration_settings.update_one(
        {"provider": "motive"},
        {"$set": {
            "provider": "motive",
            "api_key_value": api_key,
            "webhook_secret_value": secret,
            "enabled": enabled,
            "demo_mode": False,
            "test_mode": test_mode,
            "status": "Connected" if (api_key and enabled) else "Not Connected",
            "api_base": "https://api.gomotive.com",
            "webhook_url_path": "/api/integrations/motive/webhook",
        }, "$setOnInsert": {
            "id": str(uuid.uuid4()),
            "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "updated_by": "test",
        }},
        upsert=True,
    )


def _cleanup(db):
    for col in ["integration_settings", "integration_sync_logs",
                "integration_error_logs", "production_incidents",
                "admin_audit", "motive_events"]:
        db[col].delete_many({})


# ── 1. Missing credentials → 503 retryable ─────────────────────────────
def test_missing_credentials_returns_503(app_client, db):
    _cleanup(db)
    _seed_motive(db, secret="", api_key="", enabled=False)

    r = app_client.post("/api/integrations/motive/webhook",
                        content=b'{"event_type":"vehicle_gps"}',
                        headers={"Content-Type": "application/json"})

    assert r.status_code == 503, f"expected 503, got {r.status_code} body={r.text}"
    body = r.json()
    assert body["ok"] is False
    assert body["status"] == "awaiting_credentials"
    assert body["stored"] is False
    assert body["provider"] == "motive"
    assert "credentials" in body["message"].lower()


# ── 2. Missing credentials creates credential-missing incident + audit ─
def test_missing_credentials_creates_alert(app_client, db):
    _cleanup(db)
    _seed_motive(db, secret="", api_key="", enabled=False)

    app_client.post("/api/integrations/motive/webhook",
                    content=b'{}',
                    headers={"Content-Type": "application/json"})
    time.sleep(0.5)  # let asyncio.create_task() flush
    incident = db.production_incidents.find_one({
        "provider": "motive", "kind": "credential_missing", "resolved": False,
    })
    audit = db.admin_audit.find_one({
        "action": "integration_credential_missing_detected", "target": "motive",
    })
    sync_log = db.integration_sync_logs.find_one({
        "integration": "motive", "sync_type": "webhook",
    })
    assert incident is not None
    assert incident["hit_count"] >= 1
    assert audit is not None
    assert sync_log is not None
    assert sync_log["status"] == "Awaiting Credentials"


# ── 3. Missing creds: no event stored as accepted ──────────────────────
def test_missing_credentials_does_not_store_event(app_client, db):
    _cleanup(db)
    _seed_motive(db, secret="", api_key="", enabled=False)

    app_client.post("/api/integrations/motive/webhook",
                    content=b'{"event_type":"vehicle_gps","vehicle":{"id":1}}',
                    headers={"Content-Type": "application/json"})

    n = db.motive_events.count_documents({})
    assert n == 0


# ── 4 & 5. Valid creds + valid signature → 200 + event stored ──────────
def test_valid_signed_webhook_returns_200_and_stores(app_client, db):
    _cleanup(db)
    secret = "test-secret-32chars-aaaaaaaaaaaaaa"
    _seed_motive(db, secret=secret, api_key="test-api-key", enabled=True)

    body = json.dumps({
        "event_type": "vehicle_gps",
        "id": "test-evt-1",
        "vehicle": {"id": 9999, "current_location": {"lat": 28.5, "lon": -81.4,
                                                      "located_at": "2026-06-09T17:00:00Z"}},
    }, separators=(',', ':')).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    r = app_client.post("/api/integrations/motive/webhook",
                        content=body,
                        headers={"X-Motive-Signature": sig, "Content-Type": "application/json"})

    assert r.status_code == 200, f"expected 200, got {r.status_code} body={r.text}"
    payload = r.json()
    assert payload.get("ok") is True
    assert payload.get("stored") is True
    assert payload.get("event_kind") == "vehicle_gps"

    n = db.motive_events.count_documents({})
    assert n == 1


# ── 6. Invalid signature → 401, no false success ──────────────────────
def test_invalid_signature_returns_401(app_client, db):
    _cleanup(db)
    secret = "test-secret-32chars-bbbbbbbbbbbbbb"
    _seed_motive(db, secret=secret, api_key="test-api-key", enabled=True)

    r = app_client.post("/api/integrations/motive/webhook",
                        content=b'{}',
                        headers={"X-Motive-Signature": "a" * 64,
                                 "Content-Type": "application/json"})

    assert r.status_code == 401, f"expected 401, got {r.status_code} body={r.text}"
    n = db.motive_events.count_documents({})
    assert n == 0


# ── 7. MotiveService sync code path unaffected (smoke) ────────────────
def test_motive_service_smoke_with_no_creds():
    sys.path.insert(0, "/app/backend")
    srv = sys.modules.get("server") or importlib.import_module("server")
    from services.motive_service import MotiveService

    async def _go():
        svc = MotiveService(srv.db, {})  # no api_key
        return await svc.test_connection()

    r = asyncio.new_event_loop().run_until_complete(_go())
    assert r["ok"] is False
    assert r["status"] == "awaiting_credentials"


# ── 8. Auto-resolve still works ───────────────────────────────────────
def test_credential_auto_resolve():
    sys.path.insert(0, "/app/backend")
    name = f"masci_test_autoresolve_{uuid.uuid4().hex[:8]}_preview"

    from motor.motor_asyncio import AsyncIOMotorClient
    from routes.integrations._credential_alerts import (
        record_credential_missing, mark_resolved,
    )

    async def _scenario():
        mclient = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db_ = mclient[name]
        await record_credential_missing(db_, provider="motive")
        await record_credential_missing(db_, provider="motive")
        open_before = await db_.production_incidents.count_documents({
            "provider": "motive", "kind": "credential_missing", "resolved": False,
        })
        closed = await mark_resolved(db_, provider="motive", resolved_by="test")
        open_after = await db_.production_incidents.count_documents({
            "provider": "motive", "kind": "credential_missing", "resolved": False,
        })
        resolved_audit = await db_.admin_audit.find_one({
            "action": "integration_credential_missing_resolved", "target": "motive",
        })
        await db_.production_incidents.delete_many({})
        await db_.admin_audit.delete_many({})
        mclient.close()
        return open_before, closed, open_after, resolved_audit

    open_before, closed, open_after, resolved_audit = asyncio.new_event_loop().run_until_complete(_scenario())
    assert open_before == 1
    assert closed == 1
    assert open_after == 0
    assert resolved_audit is not None
