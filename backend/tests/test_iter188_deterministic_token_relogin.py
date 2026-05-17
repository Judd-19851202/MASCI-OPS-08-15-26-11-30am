"""iter188 — Phase 2 Initiative 4 follow-up: deterministic-token
session re-login regression suite.

Surfaced by the 2026-02-XX documentation reconciliation pass. The
original Initiative 4 build had a latent defect: stateless HMAC tokens
are deterministic per (epoch, namespace, password) — so the
``session_activity`` row keyed by sha256(token) survived across logins
and a re-login after the idle window was immediately rejected by the
middleware as ``session_idle_timeout``.

The fix: every login endpoint resets/upserts the caller's
``session_activity`` row to ``first_seen_at = last_seen_at = now``.
Tests below exercise the scenarios the operator requested:

    • idle timeout (no fresh login)        → still expires
    • post-timeout re-login                → fresh login resets the row
    • multi-login cycles                   → repeated logins always succeed
    • cross-portal auth                    → admin+HR+PM each reset their own
    • logout → login loops                 → logout clears, login re-issues
    • browser refresh behavior             → same token survives without re-login
    • multi-tab behavior                   → concurrent requests share row

Tests hit the live preview backend and require
``SESSION_TIMEOUTS_ENABLED=true`` in ``/app/backend/.env``. If the flag
is off, the tests SKIP — the regressions only exist under enforcement.
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
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


def _timeouts_enabled() -> bool:
    val = (_read_env_var("SESSION_TIMEOUTS_ENABLED") or "").lower()
    return val in ("1", "true", "yes", "on")


pytestmark = pytest.mark.skipif(
    not _timeouts_enabled(),
    reason="iter188 regression suite only meaningful when SESSION_TIMEOUTS_ENABLED=true",
)


def _mongo():
    from pymongo import MongoClient
    return MongoClient(_read_env_var("MONGO_URL"), serverSelectionTimeoutMS=3000)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _force_stale_session_row(token: str, idle_minutes: int = 999) -> None:
    """Backdate ``last_seen_at`` so the next middleware check would
    declare the session idle-expired. Used to simulate the operator
    having walked away for hours."""
    th = _hash(token)
    stale_at = datetime.now(timezone.utc) - timedelta(minutes=idle_minutes)
    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        db.session_activity.update_one(
            {"token_hash": th},
            {"$set": {"last_seen_at": stale_at, "first_seen_at": stale_at}},
            upsert=False,
        )
    finally:
        client.close()


# ════════════════════════════════════════════════════════════════════
# Admin login flows
# ════════════════════════════════════════════════════════════════════
def _admin_login() -> str:
    pw = _read_env_var("ADMIN_PASSWORD")
    if not pw:
        pytest.skip("ADMIN_PASSWORD not configured")
    r = requests.post(f"{URL}/api/admin/login", json={"password": pw}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def test_admin_fresh_login_first_request_returns_200():
    """Regression for the original defect: fresh login + immediate
    authenticated call must NOT 401 with session_idle_timeout."""
    token = _admin_login()
    r = requests.get(
        f"{URL}/api/admin/check",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    assert r.status_code == 200, (
        f"fresh admin token rejected: {r.status_code} {r.text}"
    )


def test_admin_post_idle_relogin_succeeds():
    """Login, simulate operator-idle past the admin tier limit
    (15 min idle), then log in again. The second login must produce
    a working token — the original bug failed here."""
    token1 = _admin_login()
    # Backdate so the middleware would expire token1 on next use
    _force_stale_session_row(token1, idle_minutes=120)

    # Verify backdating took effect — token1 is now considered expired
    r = requests.get(
        f"{URL}/api/admin/check",
        headers={"X-Admin-Token": token1},
        timeout=10,
    )
    assert r.status_code == 401
    assert "session_idle_timeout" in r.text

    # Re-login. Admin tokens are deterministic so token2 == token1.
    token2 = _admin_login()
    assert token2 == token1, (
        "expected deterministic admin token; got a different value — "
        "the test premise (and the fix it validates) does not apply"
    )

    # The fresh login MUST have reset session_activity. token1/token2
    # should now authenticate again.
    r = requests.get(
        f"{URL}/api/admin/check",
        headers={"X-Admin-Token": token2},
        timeout=10,
    )
    assert r.status_code == 200, (
        f"post-idle re-login still rejected: {r.status_code} {r.text}"
    )


def test_admin_multi_login_cycles_all_succeed():
    """Repeated logout/login cycles must all produce a working session.
    Catches a scenario where logout clears the row but login fails to
    re-create it (or vice versa)."""
    for i in range(5):
        token = _admin_login()
        r = requests.get(
            f"{URL}/api/admin/check",
            headers={"X-Admin-Token": token},
            timeout=10,
        )
        assert r.status_code == 200, f"cycle {i}: check failed {r.status_code}"
        # logout
        r = requests.post(
            f"{URL}/api/admin/logout",
            headers={"X-Admin-Token": token},
            timeout=10,
        )
        assert r.status_code == 200


def test_admin_logout_login_loop_recovers_from_stale_row():
    """logout clears the row → login re-upserts. After 3 cycles the
    row exists and last_seen_at is fresh."""
    for _ in range(3):
        token = _admin_login()
        requests.post(
            f"{URL}/api/admin/logout",
            headers={"X-Admin-Token": token},
            timeout=10,
        )
    # One more login then verify the row state
    token = _admin_login()
    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        row = db.session_activity.find_one({"token_hash": _hash(token)})
        assert row is not None, "session_activity row missing after login"
        age_s = (
            datetime.now(timezone.utc)
            - row["last_seen_at"].replace(tzinfo=timezone.utc)
        ).total_seconds()
        assert age_s < 60, f"last_seen_at not fresh: {age_s}s old"
    finally:
        client.close()


# ════════════════════════════════════════════════════════════════════
# Browser-refresh & multi-tab behavior
# ════════════════════════════════════════════════════════════════════
def test_browser_refresh_does_not_force_relogin():
    """Browser refresh = same token replayed; no fresh /login call.
    The middleware should bump last_seen_at via $max and pass through.
    Specifically — three rapid requests with the same token must all
    succeed and last_seen_at must monotonically increase."""
    token = _admin_login()
    times = []
    for _ in range(3):
        r = requests.get(
            f"{URL}/api/admin/check",
            headers={"X-Admin-Token": token},
            timeout=10,
        )
        assert r.status_code == 200
        client = _mongo()
        try:
            db = client[_read_env_var("DB_NAME")]
            row = db.session_activity.find_one({"token_hash": _hash(token)})
            times.append(row["last_seen_at"])
        finally:
            client.close()
        time.sleep(0.05)
    # last_seen_at must be monotonically non-decreasing across the 3 hits
    assert times[0] <= times[1] <= times[2], (
        f"last_seen_at went backwards: {times}"
    )


def test_multi_tab_concurrent_requests_share_row():
    """Multiple concurrent requests with the same token must all
    succeed and end up with exactly ONE session_activity row (uniqueness
    of token_hash)."""
    import concurrent.futures

    token = _admin_login()

    def _hit():
        return requests.get(
            f"{URL}/api/admin/check",
            headers={"X-Admin-Token": token},
            timeout=10,
        ).status_code

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        codes = list(ex.map(lambda _i: _hit(), range(8)))
    assert all(c == 200 for c in codes), f"some concurrent calls failed: {codes}"

    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        rows = list(db.session_activity.find({"token_hash": _hash(token)}))
        assert len(rows) == 1, f"expected exactly 1 row, got {len(rows)}"
    finally:
        client.close()


# ════════════════════════════════════════════════════════════════════
# Cross-portal: HR + PM share the same defect class — verify each
# ════════════════════════════════════════════════════════════════════
def _hr_login_seed_user():
    """Return the seeded HR test credentials from
    /app/memory/test_credentials.md. The seeded HR Manager
    (hrmanager@mascigc.com / HRTesting2026!) is documented as
    must_change_password=false for automation."""
    return ("hrmanager@mascigc.com", "HRTesting2026!")


def test_hr_post_idle_relogin_succeeds():
    """HR login parallel: tokens are deterministic per (user_id, pwh)
    so the same defect class applies. Verify the fix covers it."""
    email, pw = _hr_login_seed_user()
    r = requests.post(
        f"{URL}/api/hr/login",
        json={"email": email, "password": pw},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"HR login failed ({r.status_code}); seed creds stale")
    token1 = r.json()["token"]

    _force_stale_session_row(token1, idle_minutes=240)
    # Verify expiry triggers (use any /hr/* endpoint)
    r = requests.get(
        f"{URL}/api/hr/employees",
        headers={"X-HR-Token": token1},
        timeout=10,
    )
    # 401 with session_idle_timeout OR a legitimate downstream 401/403
    # are both acceptable here — what matters is the next login flow.

    # Re-login
    r = requests.post(
        f"{URL}/api/hr/login",
        json={"email": email, "password": pw},
        timeout=10,
    )
    assert r.status_code == 200, f"HR re-login failed: {r.status_code} {r.text}"
    token2 = r.json()["token"]
    # Deterministic by (user_id, pwh) — should match
    assert token1 == token2

    # Authenticated request must now succeed
    r = requests.get(
        f"{URL}/api/hr/employees",
        headers={"X-HR-Token": token2},
        timeout=10,
    )
    # We don't assert 200 (HR /employees may have additional gates);
    # we assert NOT 401-with-session-timeout.
    if r.status_code == 401:
        assert "session_idle_timeout" not in r.text, (
            "HR re-login did not reset session_activity"
        )


def test_pm_shared_login_post_idle_relogin_succeeds():
    """PM shared-password mode: token is deterministic on PM_PASSWORD.
    Verify the fix covers it."""
    pw = _read_env_var("PM_PASSWORD")
    if not pw:
        pytest.skip("PM_PASSWORD not configured (per-PM-only deployment)")
    # PM shared login defaults to enabled if the env var is unset
    # (see pm_auth.shared_pm_login_enabled). Only skip when it's
    # explicitly disabled.
    flag = (_read_env_var("PM_SHARED_LOGIN_ENABLED") or "true").lower()
    if flag not in ("1", "true", "yes", "on"):
        pytest.skip("PM_SHARED_LOGIN_ENABLED is off — shared path disabled")

    r = requests.post(
        f"{URL}/api/pm/login",
        json={"email": "", "password": pw},
        timeout=10,
    )
    if r.status_code != 200:
        pytest.skip(f"PM shared login refused: {r.status_code}")
    token1 = r.json()["token"]

    _force_stale_session_row(token1, idle_minutes=600)

    r = requests.post(
        f"{URL}/api/pm/login",
        json={"email": "", "password": pw},
        timeout=10,
    )
    assert r.status_code == 200
    token2 = r.json()["token"]
    assert token1 == token2

    # Use a benign PM-readable endpoint to confirm the session works
    r = requests.get(
        f"{URL}/api/pm/check",
        headers={"X-PM-Token": token2},
        timeout=10,
    )
    if r.status_code == 401:
        assert "session_idle_timeout" not in r.text, (
            "PM shared re-login did not reset session_activity"
        )


# ════════════════════════════════════════════════════════════════════
# Logout explicitly clears server-side row
# ════════════════════════════════════════════════════════════════════
def test_admin_logout_deletes_session_activity_row():
    """POST /api/admin/logout must remove the session_activity row
    for the bearer token. Belt-and-suspenders with the 30-day TTL."""
    token = _admin_login()
    # Confirm row exists
    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        row = db.session_activity.find_one({"token_hash": _hash(token)})
        assert row is not None
    finally:
        client.close()

    r = requests.post(
        f"{URL}/api/admin/logout",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    assert r.status_code == 200

    client = _mongo()
    try:
        db = client[_read_env_var("DB_NAME")]
        row = db.session_activity.find_one({"token_hash": _hash(token)})
        assert row is None, "session_activity row not cleared by logout"
    finally:
        client.close()
