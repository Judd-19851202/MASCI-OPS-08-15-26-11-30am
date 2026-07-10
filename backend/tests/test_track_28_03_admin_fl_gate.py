"""TRACK 28.03-A · Regression lock — admin tokens minted by
``/api/auth/multi-login`` must unlock every Field Leadership form
endpoint.

Root cause of the P0 (discovered during Track 28.03 pre-walk):
``routes/field_leadership.py::_admin_token_valid`` only consulted the
sync ``_is_valid_admin_token`` sentinel, which was retired in TRACK
15.32 and unconditionally returns False. That silently rejected every
directory-hydrated admin token with 401 "Field Leadership access
required" on every FL POST/GET/DELETE endpoint.

Fix: fall through to the async directory-hydrated validator
(``_is_valid_directory_admin_token_async``) — mirrors the Track
28.02-A fix on the Safety gate factories.

Blast radius before fix:
  • FL admin browser (list, detail, CSV export, PDF)
  • FL form POST from any admin session
  • Every /api/field-leadership/* endpoint

This test locks the fix by hitting the two hottest FL surfaces
(POST /api/field-leadership + GET /api/field-leadership/check) with
the admin portal token from multi-login.
"""
from __future__ import annotations

import httpx
import pytest


BACKEND = "http://localhost:8001"


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = httpx.post(
        f"{BACKEND}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    r.raise_for_status()
    tok = (r.json().get("portal_tokens") or {}).get("admin")
    assert tok and "." in tok, "expected UUID.HMAC admin token"
    return tok


def test_admin_token_unlocks_field_leadership_check(admin_token: str) -> None:
    r = httpx.get(
        f"{BACKEND}/api/field-leadership/check",
        headers={"X-Admin-Token": admin_token},
        timeout=15,
    )
    assert r.status_code == 200, r.text[:200]
    assert r.json().get("ok") is True


def test_admin_token_unlocks_field_leadership_list(admin_token: str) -> None:
    r = httpx.get(
        f"{BACKEND}/api/field-leadership",
        headers={"X-Admin-Token": admin_token},
        params={"limit": 5},
        timeout=15,
    )
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert "items" in body


def test_no_token_still_rejected() -> None:
    r = httpx.get(f"{BACKEND}/api/field-leadership/check", timeout=15)
    assert r.status_code == 401, f"expected 401 for missing token; got {r.status_code}"
