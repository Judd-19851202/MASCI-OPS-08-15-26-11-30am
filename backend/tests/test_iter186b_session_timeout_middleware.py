"""iter186b — session_timeout middleware integration test.

Drives the actual FastAPI middleware against an isolated TestClient with
a mocked Mongo replacement so we can simulate idle / absolute expiry
without waiting wall-clock time.

This is independent from the unit tests in test_iter186_phase2_hardening.py
which only exercise the config surface; here we prove the middleware
makes correct allow/deny decisions.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

sys.path.insert(0, "/app/backend")


class _FakeUpdateResult:
    pass


class _FakeColl:
    def __init__(self, store):
        self.store = store

    async def find_one(self, q, projection=None):
        return self.store.get(q.get("token_hash"))

    async def update_one(self, q, update, upsert=False):
        th = q.get("token_hash")
        existing = self.store.get(th)
        if "$setOnInsert" in update and existing is None and upsert:
            self.store[th] = dict(update["$setOnInsert"])
        if "$set" in update:
            self.store.setdefault(th, {}).update(update["$set"])
        if "$unset" in update:
            for k in update["$unset"].keys():
                self.store.setdefault(th, {}).pop(k, None)
        if "$max" in update:
            for k, v in update["$max"].items():
                cur = self.store.get(th, {}).get(k)
                if cur is None or v > cur:
                    self.store.setdefault(th, {})[k] = v
        return _FakeUpdateResult()

    async def create_index(self, *_args, **_kw):
        return None


class _FakeDB:
    def __init__(self):
        self._store = {}
        self.session_activity = _FakeColl(self._store)


def _make_app(db):
    from session_timeout import install_session_timeout_middleware
    app = FastAPI()
    install_session_timeout_middleware(app, db)

    @app.get("/api/secured")
    async def secured(request: Request):
        return JSONResponse({"ok": True})

    @app.get("/api/health")
    async def health():
        return {"ok": True}

    return app


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch):
    for k in list(os.environ):
        if k.startswith("SESSION_"):
            monkeypatch.delenv(k, raising=False)
    yield


def test_middleware_noop_when_disabled():
    """No env vars set → middleware passes everything through unchanged."""
    db = _FakeDB()
    client = TestClient(_make_app(db))
    r = client.get("/api/secured", headers={"X-Admin-Token": "abc"})
    assert r.status_code == 200
    # No session_activity row should have been created
    assert db._store == {}


def test_middleware_first_seen_creates_row(monkeypatch):
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    db = _FakeDB()
    client = TestClient(_make_app(db))
    r = client.get("/api/secured", headers={"X-Admin-Token": "abc"})
    assert r.status_code == 200
    assert len(db._store) == 1
    row = list(db._store.values())[0]
    assert row["tier"] == "ADMIN_HR"
    assert "first_seen_at" in row
    assert "last_seen_at" in row


def test_middleware_idle_timeout_enforced(monkeypatch):
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    monkeypatch.setenv("SESSION_IDLE_MIN_ADMIN_HR", "15")
    db = _FakeDB()
    # Pre-seed a row whose last_seen_at is 16 min ago
    import hashlib
    th = hashlib.sha256(b"abc").hexdigest()
    old = datetime.now(timezone.utc) - timedelta(minutes=16)
    db._store[th] = {
        "token_hash": th, "tier": "ADMIN_HR",
        "first_seen_at": old, "last_seen_at": old,
    }
    client = TestClient(_make_app(db))
    r = client.get("/api/secured", headers={"X-Admin-Token": "abc"})
    assert r.status_code == 401
    body = r.json()
    assert body["detail"] == "session_idle_timeout"
    assert body["tier"] == "ADMIN_HR"


def test_middleware_absolute_timeout_enforced(monkeypatch):
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    monkeypatch.setenv("SESSION_ABS_HOUR_ADMIN_HR", "4")
    db = _FakeDB()
    import hashlib
    th = hashlib.sha256(b"abc").hexdigest()
    now = datetime.now(timezone.utc)
    first = now - timedelta(hours=5)
    # last_seen = now (active) but first_seen is 5h ago (over abs)
    db._store[th] = {
        "token_hash": th, "tier": "ADMIN_HR",
        "first_seen_at": first, "last_seen_at": now,
    }
    client = TestClient(_make_app(db))
    r = client.get("/api/secured", headers={"X-Admin-Token": "abc"})
    assert r.status_code == 401
    body = r.json()
    assert body["detail"] == "session_absolute_timeout"


def test_middleware_health_exempt(monkeypatch):
    """Health endpoints must bypass timeout enforcement so uptime
    monitors keep working."""
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    db = _FakeDB()
    client = TestClient(_make_app(db))
    r = client.get("/api/health", headers={"X-Admin-Token": "abc"})
    assert r.status_code == 200
    # No row written for health probe
    assert db._store == {}


def test_middleware_anonymous_passes(monkeypatch):
    """No token header → middleware passes through and lets downstream
    auth dependency decide. The middleware itself must not 401."""
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    db = _FakeDB()
    client = TestClient(_make_app(db))
    r = client.get("/api/secured")  # no token
    assert r.status_code == 200  # middleware allowed; downstream is open in test


def test_middleware_tier_picks_strictest(monkeypatch):
    """If both Admin and PM tokens are sent, Admin tier wins."""
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    db = _FakeDB()
    client = TestClient(_make_app(db))
    client.get("/api/secured", headers={
        "X-Admin-Token": "admin-abc",
        "X-PM-Token": "pm-xyz",
    })
    # Only one session row, tagged ADMIN_HR
    rows = list(db._store.values())
    assert len(rows) == 1
    assert rows[0]["tier"] == "ADMIN_HR"


def test_middleware_dev_token_excluded(monkeypatch):
    """X-Dev-Token must NOT be subject to timeout (vendor-only)."""
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    db = _FakeDB()
    client = TestClient(_make_app(db))
    r = client.get("/api/secured", headers={"X-Dev-Token": "vendor-xyz"})
    assert r.status_code == 200
    # No row written for dev tokens
    assert db._store == {}


@pytest.mark.asyncio
async def test_reset_session_activity_clears_stale_directory_binding(monkeypatch):
    monkeypatch.setenv("SESSION_TIMEOUTS_ENABLED", "true")
    from session_timeout import reset_session_activity, _hash_token

    db = _FakeDB()
    token = "pm-token-123"
    token_hash = _hash_token(token)
    db._store[token_hash] = {
        "token_hash": token_hash,
        "tier": "OPERATIONS",
        "directory_session_token_hash": "stale-directory-binding",
    }

    await reset_session_activity(
        db,
        token,
        "OPERATIONS",
        user_id="pm-1",
        email="pm@example.com",
        actor_label="pm",
    )

    assert db._store[token_hash]["user_id"] == "pm-1"
    assert db._store[token_hash]["email"] == "pm@example.com"
    assert "directory_session_token_hash" not in db._store[token_hash]
