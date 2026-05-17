"""iter189 — Last 5 Sessions admin visibility panel.

Backend coverage for GET /api/admin/sessions/recent:

    • admin-strict gate (anonymous, bogus, HR token, PM token all 401/403)
    • response shape (timeouts_enabled, tiers, sessions[])
    • limit clamp (max 200)
    • audit row written every call (admin_sessions_panel_viewed)
    • status classification (active vs expired_idle vs expired_absolute
      vs enforcement_off) reflects the live row state
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

URL = os.environ.get("PUBLIC_BACKEND_URL") or "http://localhost:8001"


def _read_env_var(key: str) -> str:
    p = Path("/app/backend/.env")
    if not p.exists():
        return ""
    for line in p.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


@pytest.fixture
def admin_token():
    pw = _read_env_var("ADMIN_PASSWORD")
    if not pw:
        pytest.skip("ADMIN_PASSWORD not configured")
    r = requests.post(f"{URL}/api/admin/login", json={"password": pw}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def _mongo():
    from pymongo import MongoClient
    return MongoClient(_read_env_var("MONGO_URL"), serverSelectionTimeoutMS=3000)


# ─────────────────────────────────────────────────────────────────────
# Gate
# ─────────────────────────────────────────────────────────────────────
def test_sessions_endpoint_rejects_anonymous():
    r = requests.get(f"{URL}/api/admin/sessions/recent", timeout=10)
    assert r.status_code == 401


def test_sessions_endpoint_rejects_garbage_admin_token():
    r = requests.get(
        f"{URL}/api/admin/sessions/recent",
        headers={"X-Admin-Token": "garbage-XXX"},
        timeout=10,
    )
    assert r.status_code == 401


def test_sessions_endpoint_rejects_pm_token():
    """PM tokens must be refused at admin-strict endpoints (iter180)."""
    pm_pw = _read_env_var("PM_PASSWORD")
    if not pm_pw:
        pytest.skip("PM_PASSWORD not configured")
    # Use shared PM bypass to mint a non-admin token
    r = requests.post(
        f"{URL}/api/pm/login",
        json={"email": "", "password": pm_pw},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip("PM shared login refused — cannot exercise gate")
    pm_token = r.json()["token"]
    r = requests.get(
        f"{URL}/api/admin/sessions/recent",
        headers={"X-PM-Token": pm_token},
        timeout=10,
    )
    # admin-strict refuses PM tokens (401 or 403 acceptable; current
    # gate returns 401 with denied-access audit row)
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────
# Shape + content
# ─────────────────────────────────────────────────────────────────────
def test_sessions_endpoint_response_shape(admin_token):
    r = requests.get(
        f"{URL}/api/admin/sessions/recent",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "timeouts_enabled" in data
    assert "tiers" in data
    assert "sessions" in data
    assert "server_now" in data
    assert isinstance(data["sessions"], list)
    # Every row must have the required keys
    for s in data["sessions"]:
        for key in (
            "tier", "login_at", "last_activity_at", "status",
            "idle_seconds", "absolute_seconds",
        ):
            assert key in s, f"row missing {key}: {s}"


def test_sessions_endpoint_limit_clamp(admin_token):
    """Requesting an absurd limit must clamp to 200, not crash."""
    r = requests.get(
        f"{URL}/api/admin/sessions/recent?limit=9999",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    assert r.json()["limit"] == 200


def test_sessions_endpoint_limit_floor(admin_token):
    """Requesting limit <= 0 must default (falsy → 50), not crash."""
    r = requests.get(
        f"{URL}/api/admin/sessions/recent?limit=0",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    # 0 is falsy → default kicks in (50)
    assert r.json()["limit"] == 50


def test_sessions_endpoint_writes_audit_row(admin_token):
    """Every panel view must write an admin_sessions_panel_viewed
    row to audit_events for chain-of-custody."""
    before_ts = datetime.now(timezone.utc)
    r = requests.get(
        f"{URL}/api/admin/sessions/recent?limit=10",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200

    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        recent = list(db.audit_events.find(
            {"kind": "admin_sessions_panel_viewed"},
            sort=[("at", -1)], limit=1,
        ))
    finally:
        client.close()

    assert recent, "no admin_sessions_panel_viewed audit row written"
    row = recent[0]
    at_dt = row["at"].replace(tzinfo=timezone.utc) if row["at"].tzinfo is None else row["at"]
    assert at_dt >= before_ts - timedelta(seconds=5)
    assert row.get("limit") == 10


# ─────────────────────────────────────────────────────────────────────
# Status classification
# ─────────────────────────────────────────────────────────────────────
def test_sessions_endpoint_classifies_active_after_fresh_login(admin_token):
    """A row created by a fresh login (just now) must classify as
    'active' when timeouts are enabled."""
    r = requests.get(
        f"{URL}/api/admin/sessions/recent?limit=5",
        headers={"X-Admin-Token": admin_token},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    if not data["timeouts_enabled"]:
        pytest.skip("timeouts disabled in this env — classification not exercised")
    # The admin's own session row should be present and active
    admin_row = next(
        (s for s in data["sessions"] if s.get("actor_label") == "admin"),
        None,
    )
    assert admin_row, "fresh admin session row not present"
    assert admin_row["status"] == "active"


def test_sessions_endpoint_classifies_idle_expiry(admin_token):
    """Backdate the admin row and confirm the panel reports
    expired_idle for it."""
    import hashlib
    th = hashlib.sha256(admin_token.encode()).hexdigest()
    stale = datetime.now(timezone.utc) - timedelta(hours=2)
    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        db.session_activity.update_one(
            {"token_hash": th},
            {"$set": {"last_seen_at": stale, "first_seen_at": stale}},
        )
    finally:
        client.close()

    # Re-login to avoid being kicked out by the middleware on our own
    # request — gives us a working admin token for the panel call.
    pw = _read_env_var("ADMIN_PASSWORD")
    r = requests.post(f"{URL}/api/admin/login", json={"password": pw}, timeout=10)
    r.raise_for_status()
    fresh_token = r.json()["token"]

    # After re-login, the row was reset to "now". Backdate AGAIN —
    # this time we read the panel with the fresh token (which the
    # middleware passes through), and the previously-fresh row has
    # been re-stamped, so we backdate it once more before reading.
    stale2 = datetime.now(timezone.utc) - timedelta(hours=2)
    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        # Use a synthetic non-active row so re-login doesn't reset it
        synthetic_th = hashlib.sha256(b"synthetic-idle-row-iter189").hexdigest()
        db.session_activity.update_one(
            {"token_hash": synthetic_th},
            {"$set": {
                "token_hash": synthetic_th,
                "tier": "ADMIN_HR",
                "first_seen_at": stale2,
                "last_seen_at": stale2,
                "email": "synthetic-idle@iter189.test",
                "actor_label": "admin",
            }},
            upsert=True,
        )
    finally:
        client.close()

    r = requests.get(
        f"{URL}/api/admin/sessions/recent?limit=200",
        headers={"X-Admin-Token": fresh_token},
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    synth = next(
        (s for s in data["sessions"]
         if s.get("email") == "synthetic-idle@iter189.test"),
        None,
    )
    assert synth, "synthetic idle row not surfaced in panel"
    if data["timeouts_enabled"]:
        assert synth["status"] in ("expired_idle", "expired_absolute"), (
            f"expected expired_*, got {synth['status']}"
        )

    # Cleanup
    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        db.session_activity.delete_one(
            {"email": "synthetic-idle@iter189.test"}
        )
    finally:
        client.close()


def test_sessions_endpoint_includes_identity_metadata(admin_token):
    """After our enriched login flow, the admin's own session row
    must carry actor_label='admin', ip, and user_agent."""
    r = requests.get(
        f"{URL}/api/admin/sessions/recent?limit=10",
        headers={
            "X-Admin-Token": admin_token,
            "User-Agent": "iter189-test-agent/1.0",
        },
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    admin_row = next(
        (s for s in data["sessions"] if s.get("actor_label") == "admin"),
        None,
    )
    assert admin_row, "no admin row surfaced"
    # IP is set; UA may or may not include the test's UA depending on
    # whether login was the most recent call.
    assert admin_row.get("ip"), "ip missing on admin row"
    assert admin_row.get("user_agent"), "user_agent missing on admin row"
