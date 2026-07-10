"""TRACK 28.04 Phase 1 · Cross-portal auth regression lock.

Executes real portal-token auth via /api/auth/multi-login and hits
one representative endpoint per portal to prove the canonical
async validator chain is intact end-to-end after Track 28.03E's
factory-wiring changes.
"""
from __future__ import annotations

import httpx
import pytest


BACKEND = "http://localhost:8001"
CREDENTIALS = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}


@pytest.fixture(scope="module")
def portal_tokens() -> dict:
    r = httpx.post(f"{BACKEND}/api/auth/multi-login", json=CREDENTIALS, timeout=30)
    r.raise_for_status()
    tokens = r.json().get("portal_tokens") or {}
    for portal in ("admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership", "fl"):
        assert tokens.get(portal), f"multi-login did not issue a {portal} portal token"
    return tokens


@pytest.mark.parametrize("header,portal_key,endpoint", [
    ("X-Admin-Token",    "admin",   "/api/health"),
    ("X-HR-Token",       "hr",      "/api/hr/notifications/digest"),
    ("X-Safety-Token",   "safety",  "/api/incidents"),
    ("X-Shop-Token",     "shop",    "/api/shop/me/summary"),
    ("X-PM-Token",       "pm",      "/api/pm/notifications/digest"),
    ("X-Dispatch-Token", "dispatch","/api/dispatch/notifications/digest"),
    ("X-FL-Token",       "fl",      "/api/fl/notifications/digest"),
])
def test_portal_token_unlocks_representative_endpoint(portal_tokens: dict, header: str, portal_key: str, endpoint: str) -> None:
    tok = portal_tokens[portal_key]
    r = httpx.get(f"{BACKEND}{endpoint}", headers={header: tok}, timeout=15)
    assert r.status_code == 200, f"[{portal_key}] {endpoint} returned {r.status_code}: {r.text[:200]}"


@pytest.mark.parametrize("path", [
    "/api/hr/notifications/digest",
    "/api/pm/notifications/digest",
    "/api/dispatch/notifications/digest",
    "/api/fl/notifications/digest",
    "/api/incidents",
])
def test_missing_token_still_rejected(path: str) -> None:
    r = httpx.get(f"{BACKEND}{path}", timeout=15)
    assert r.status_code == 401, f"{path} expected 401, got {r.status_code}"


def test_invalid_token_still_rejected() -> None:
    r = httpx.get(
        f"{BACKEND}/api/hr/notifications/digest",
        headers={"X-HR-Token": "not-a-real-token.deadbeef"},
        timeout=15,
    )
    assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"
