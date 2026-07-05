"""TRACK 22.4a · Operator Trust Repair — backend contract tests.

Focused verification of the dispatch-safe Motive posture endpoint
introduced to surface Integration Truth honesty to dispatchers on the
Live Fleet Map (no admin token required).
"""
from __future__ import annotations

import os

import httpx
import pytest

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=10.0,
    )
    r.raise_for_status()
    token = (r.json().get("portal_tokens") or {}).get("admin") or ""
    assert token, "admin multi-login did not return an admin portal token"
    return token


def test_dispatch_motive_posture_requires_auth():
    r = httpx.get(f"{BACKEND_URL}/api/dispatch/motive-posture", timeout=10.0)
    assert r.status_code == 401, (
        f"dispatch motive posture must require auth (got {r.status_code})"
    )


def test_dispatch_motive_posture_accepts_admin_token():
    r = httpx.get(
        f"{BACKEND_URL}/api/dispatch/motive-posture",
        headers={"X-Admin-Token": _admin_token()},
        timeout=15.0,
    )
    assert r.status_code == 200
    body = r.json()
    for key in (
        "id", "name", "config_status", "connectivity_status",
        "operational_status", "overall", "doctrine",
    ):
        assert key in body, f"missing key: {key}"
    assert body["id"] == "motive"


def test_dispatch_motive_posture_never_leaks_admin_only_fields():
    """The dispatch-safe endpoint must not include admin-only detail
    such as api_key_source. Prevents accidental privilege escalation
    via response payload.
    """
    r = httpx.get(
        f"{BACKEND_URL}/api/dispatch/motive-posture",
        headers={"X-Admin-Token": _admin_token()},
        timeout=15.0,
    )
    body = r.json()
    for forbidden in ("api_key_last4", "api_key_source", "api_key_present"):
        assert forbidden not in body, (
            f"dispatch endpoint leaked admin-only field: {forbidden}"
        )


def test_dispatch_motive_posture_never_live_verified_without_proof():
    """F-02 invariant: overall LIVE_VERIFIED requires operational_status
    LIVE_VERIFIED.
    """
    r = httpx.get(
        f"{BACKEND_URL}/api/dispatch/motive-posture",
        headers={"X-Admin-Token": _admin_token()},
        timeout=15.0,
    )
    body = r.json()
    if body["overall"] == "LIVE_VERIFIED":
        assert body["operational_status"] == "LIVE_VERIFIED", (
            "overall=LIVE_VERIFIED without operational_status=LIVE_VERIFIED "
            "would revive the F-02 lie."
        )
