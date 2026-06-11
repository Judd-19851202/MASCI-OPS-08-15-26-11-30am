"""RC-2 · TRACK-2 GUARDRAIL — Auth / Role / Cross-Portal Smuggling.

Smoke that confirms the auth surfaces are still locked down:
* Admin-strict endpoints reject empty / non-admin tokens.
* Multi-login still mints all 7 portal tokens for super-admin.
* FL token (`field_leadership`) is part of the fan-out.
* Wrong-portal token cannot impersonate a different portal.
"""
from __future__ import annotations

import pytest
import requests
from dotenv import dotenv_values

FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BASE = (FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "").rstrip("/")

EMAIL = "jaymn.judd@mascigc.com"
PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def tokens() -> dict:
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_rc2_multi_login_returns_all_portals(tokens):
    pt = tokens.get("portal_tokens") or {}
    expected = {"admin", "pm", "shop", "hr", "safety",
                "dispatch", "field_leadership"}
    missing = expected - set(pt.keys())
    assert not missing, f"Multi-login missing portal tokens: {missing}"
    for portal, tok in pt.items():
        assert tok, f"Portal {portal} returned empty token"


def test_rc2_admin_strict_rejects_empty_token():
    r = requests.get(
        f"{BASE}/api/admin/backups",
        headers={"X-Admin-Token": ""},
        timeout=20,
    )
    assert r.status_code in (401, 403), (
        f"Admin-strict endpoint must reject empty token, got {r.status_code}"
    )


def test_rc2_admin_strict_rejects_garbage_token():
    r = requests.get(
        f"{BASE}/api/admin/backups",
        headers={"X-Admin-Token": "nope-not-a-real-token"},
        timeout=20,
    )
    assert r.status_code in (401, 403), (
        f"Admin-strict endpoint must reject garbage token, got {r.status_code}"
    )


def test_rc2_pm_token_cannot_reach_admin(tokens):
    pm_token = (tokens.get("portal_tokens") or {}).get("pm", "")
    assert pm_token, "Need a PM token to test cross-portal lockdown"
    r = requests.get(
        f"{BASE}/api/admin/backups",
        headers={"X-Admin-Token": pm_token},
        timeout=20,
    )
    assert r.status_code in (401, 403), (
        f"PM token must NOT pass admin-strict; got {r.status_code}"
    )
