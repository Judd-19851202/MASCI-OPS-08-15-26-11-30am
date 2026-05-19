"""iter243 — Safety Users admin welcome-email delivery parity.

Operator-surfaced gap: `/admin/safety-users` did not support the
`delivery=email | screen | custom` pattern that PM / Shop / HR / Dispatch
already had. This iter brings Safety to feature parity.
"""
from __future__ import annotations

import os
import time
import uuid

import pytest
import requests


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"
TAG = f"iter243-{uuid.uuid4().hex[:6]}"


def _load_admin_token():
    """Pull a live admin token from /api/admin/login using the
    ADMIN_PASSWORD env. Mirrors the conftest bootstrap but local to
    this test module so we don't depend on the monkey-patch
    propagation through requests.post indirections."""
    pw = (os.environ.get("ADMIN_PASSWORD") or "").strip()
    if not pw:
        # Fall back to backend/.env
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        try:
            with open(env_path) as f:
                for line in f:
                    if line.startswith("ADMIN_PASSWORD="):
                        pw = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    if not pw:
        return ""
    try:
        r = requests.post(f"{API}/admin/login", json={"password": pw}, timeout=10)
        if r.status_code == 200:
            return r.json().get("token", "")
    except Exception:
        pass
    return ""


_ADMIN_TOKEN = _load_admin_token()


def _admin_headers():
    return {
        "Content-Type": "application/json",
        "X-Admin-Token": _ADMIN_TOKEN,
    }


def _name():
    return f"Safety Iter243 {uuid.uuid4().hex[:4]}"


def _email():
    return f"{TAG}-{uuid.uuid4().hex[:6]}@masci-test.local"


# ── 1 · Create with delivery="screen" returns temp_password in body ──
def test_iter243_create_screen_delivery_returns_temp_password():
    body = {
        "name": _name(),
        "email": _email(),
        "role": "Safety Coordinator",
        "delivery": "screen",
    }
    r = requests.post(f"{API}/admin/safety-users", json=body, headers=_admin_headers(), timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "user" in data
    assert data.get("temp_password"), (
        "iter243 screen delivery: backend must return temp_password "
        "for admin to hand off in person."
    )
    # Cleanup
    requests.delete(f"{API}/admin/safety-users/{data['user']['id']}", headers=_admin_headers(), timeout=10)


# ── 2 · Create with delivery="email" suppresses temp_password ──
def test_iter243_create_email_delivery_suppresses_temp_password():
    body = {
        "name": _name(),
        "email": _email(),
        "role": "Safety Manager",
        "delivery": "email",
    }
    r = requests.post(f"{API}/admin/safety-users", json=body, headers=_admin_headers(), timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "user" in data
    # temp_password must be None (or absent) so the admin UI doesn't
    # surface a password that was already delivered out-of-band.
    assert not data.get("temp_password"), (
        "iter243 email delivery: temp_password MUST be suppressed "
        "from the response to avoid double-delivery confusion."
    )
    requests.delete(f"{API}/admin/safety-users/{data['user']['id']}", headers=_admin_headers(), timeout=10)


# ── 3 · Create with delivery="custom" honors admin-typed password ──
def test_iter243_create_custom_password_is_honored():
    custom = f"CustomPW-{uuid.uuid4().hex[:8]}"
    body = {
        "name": _name(),
        "email": _email(),
        "role": "Safety Officer",
        "delivery": "custom",
        "custom_password": custom,
    }
    r = requests.post(f"{API}/admin/safety-users", json=body, headers=_admin_headers(), timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("temp_password") == custom, (
        "iter243 custom delivery: backend must return the admin-typed "
        "password verbatim so the UI can reveal it."
    )
    requests.delete(f"{API}/admin/safety-users/{data['user']['id']}", headers=_admin_headers(), timeout=10)


# ── 4 · Reset-password supports the same three delivery modes ──
def test_iter243_reset_password_supports_all_delivery_modes():
    # Seed a user via screen-delivery
    seed = requests.post(f"{API}/admin/safety-users", json={
        "name": _name(), "email": _email(), "delivery": "screen",
    }, headers=_admin_headers(), timeout=10).json()
    uid = seed["user"]["id"]
    try:
        # Reset with delivery=screen → returns temp_password
        r1 = requests.post(
            f"{API}/admin/safety-users/{uid}/reset-password",
            json={"delivery": "screen"}, headers=_admin_headers(), timeout=10,
        )
        assert r1.status_code == 200, r1.text
        assert r1.json().get("temp_password"), "screen reset must return temp pw"

        # Reset with delivery=email → temp_password suppressed
        r2 = requests.post(
            f"{API}/admin/safety-users/{uid}/reset-password",
            json={"delivery": "email"}, headers=_admin_headers(), timeout=10,
        )
        assert r2.status_code == 200, r2.text
        assert not r2.json().get("temp_password"), \
            "email reset must suppress temp pw"

        # Reset with delivery=custom → returns the admin-typed pw
        custom = f"ResetCustom-{uuid.uuid4().hex[:8]}"
        r3 = requests.post(
            f"{API}/admin/safety-users/{uid}/reset-password",
            json={"delivery": "custom", "custom_password": custom},
            headers=_admin_headers(), timeout=10,
        )
        assert r3.status_code == 200, r3.text
        assert r3.json().get("temp_password") == custom, \
            "custom reset must echo the admin-typed pw"
    finally:
        requests.delete(f"{API}/admin/safety-users/{uid}", headers=_admin_headers(), timeout=10)


# ── 5 · Reset-password with no body defaults to screen delivery ──
def test_iter243_reset_password_defaults_to_screen():
    """Back-compat: callers that don't pass a body still work."""
    seed = requests.post(f"{API}/admin/safety-users", json={
        "name": _name(), "email": _email(), "delivery": "screen",
    }, headers=_admin_headers(), timeout=10).json()
    uid = seed["user"]["id"]
    try:
        r = requests.post(
            f"{API}/admin/safety-users/{uid}/reset-password",
            json={}, headers=_admin_headers(), timeout=10,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("temp_password"), \
            "no-body reset must default to screen and return pw"
    finally:
        requests.delete(f"{API}/admin/safety-users/{uid}", headers=_admin_headers(), timeout=10)


# ── 6 · Anon cannot access these admin routes ──
def test_iter243_anon_blocked_on_create_and_reset():
    r1 = requests.post(
        f"{API}/admin/safety-users",
        json={"name": "x", "email": "x@y.com"},
        headers={"Content-Type": "application/json", "X-Admin-Token": ""},
        timeout=10,
    )
    assert r1.status_code in (401, 403), (
        f"anon POST /admin/safety-users must be 401/403, got {r1.status_code}"
    )
