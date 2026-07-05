"""TRACK 22.4b-followup · Preview Validation Identities — regression locks.

Every test lands one of the following invariants:

- Production hard-guard cannot be bypassed.
- Anonymous / non-admin callers are rejected on every endpoint.
- Mint / list / revoke / introspect / audit work end-to-end in preview.
- Tokens carry role claims that survive HMAC verification and are
  rejected when the expected_role doesn't match.
- Revoked tokens cannot re-authenticate via introspect.
- Raw tokens never appear in list or audit responses.

All tests are non-mutating outside the ``preview_validation_identities``
and ``preview_validation_identity_audit`` collections owned by this
track.
"""
from __future__ import annotations

import os

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")

BASE = "/api/admin/preview-validation-identities"


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=10.0,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


@pytest.fixture(scope="module")
def headers() -> dict:
    return {"X-Admin-Token": _admin_token()}


# ── Env / hard guards ─────────────────────────────────────────────

def test_env_endpoint_reports_preview_available(headers):
    r = httpx.get(f"{BACKEND_URL}{BASE}/env", headers=headers, timeout=10.0)
    assert r.status_code == 200
    body = r.json()
    # Preview environment MUST show available=true and is_production=false.
    assert body["is_production"] is False
    assert body["available"] is True
    assert body["default_ttl_minutes"] == 240
    assert body["max_ttl_minutes"] == 1440
    assert "safety" in body["allowed_roles"]
    assert "driver" in body["allowed_roles"]


def test_production_marker_hard_disables_module(monkeypatch):
    """Directly exercise the module-level guard. If APP_ENV=production or
    the enable flag is missing, ``is_preview_validation_available``
    MUST return False — even if every other condition is true.
    """
    from routes import preview_validation_identities as pvi  # noqa: PLC0415

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ENABLE_PREVIEW_VALIDATION_IDENTITIES", "true")
    assert pvi.is_preview_validation_available() is False, (
        "production marker MUST disable the module regardless of flag"
    )

    monkeypatch.setenv("APP_ENV", "preview")
    monkeypatch.setenv("ENABLE_PREVIEW_VALIDATION_IDENTITIES", "")
    assert pvi.is_preview_validation_available() is False, (
        "missing enable flag MUST disable the module"
    )


# ── Anonymous / non-admin rejection ───────────────────────────────

@pytest.mark.parametrize("method,path", [
    ("GET", f"{BASE}/env"),
    ("GET", f"{BASE}"),
    ("POST", f"{BASE}/mint"),
    ("POST", f"{BASE}/introspect"),
    ("GET", f"{BASE}/audit"),
])
def test_anonymous_rejected(method, path):
    r = httpx.request(method, f"{BACKEND_URL}{path}", timeout=10.0)
    assert r.status_code in (401, 403), (
        f"{method} {path} must reject anonymous (got {r.status_code})"
    )


# ── Mint + introspect + revoke lifecycle ──────────────────────────

def test_mint_introspect_revoke_lifecycle(headers):
    # 1. mint
    mint = httpx.post(
        f"{BACKEND_URL}{BASE}/mint",
        headers=headers,
        json={"role": "safety", "purpose": "regression lock", "ttl_minutes": 5},
        timeout=15.0,
    )
    assert mint.status_code == 200
    body = mint.json()
    assert body["role"] == "safety"
    assert body["status"] == "active"
    assert body["token"].startswith("PVI."), "token must carry PVI prefix"
    assert body["environment"] == "preview"
    iid = body["validation_identity_id"]
    token = body["token"]

    # 2. introspect matches role
    intro = httpx.post(
        f"{BACKEND_URL}{BASE}/introspect",
        headers=headers,
        json={"token": token, "expected_role": "safety"},
        timeout=10.0,
    )
    assert intro.status_code == 200
    intro_body = intro.json()
    assert intro_body["valid"] is True
    assert intro_body["identity"]["role"] == "safety"
    # Never leak jti
    assert "jti" not in intro_body["identity"]

    # 3. wrong role introspection
    intro_wrong = httpx.post(
        f"{BACKEND_URL}{BASE}/introspect",
        headers=headers,
        json={"token": token, "expected_role": "admin"},
        timeout=10.0,
    )
    assert intro_wrong.status_code == 200
    assert intro_wrong.json()["valid"] is False

    # 4. revoke
    rev = httpx.post(
        f"{BACKEND_URL}{BASE}/{iid}/revoke",
        headers=headers,
        timeout=10.0,
    )
    assert rev.status_code == 200
    assert rev.json()["status"] == "revoked"

    # 5. post-revoke introspection returns invalid
    intro_after = httpx.post(
        f"{BACKEND_URL}{BASE}/introspect",
        headers=headers,
        json={"token": token},
        timeout=10.0,
    )
    assert intro_after.json()["valid"] is False


def test_mint_rejects_invalid_role(headers):
    r = httpx.post(
        f"{BACKEND_URL}{BASE}/mint",
        headers=headers,
        json={"role": "root", "purpose": "should fail", "ttl_minutes": 10},
        timeout=10.0,
    )
    assert r.status_code == 400


def test_mint_rejects_ttl_over_24_hours(headers):
    r = httpx.post(
        f"{BACKEND_URL}{BASE}/mint",
        headers=headers,
        json={"role": "safety", "purpose": "excessive ttl", "ttl_minutes": 24 * 60 + 1},
        timeout=10.0,
    )
    assert r.status_code == 400


# ── List + audit hygiene ──────────────────────────────────────────

def test_list_never_returns_raw_token(headers):
    """The list endpoint must return metadata only. No 'token' field."""
    httpx.post(
        f"{BACKEND_URL}{BASE}/mint",
        headers=headers,
        json={"role": "hr", "purpose": "list hygiene", "ttl_minutes": 5},
        timeout=15.0,
    )
    r = httpx.get(f"{BACKEND_URL}{BASE}", headers=headers, timeout=10.0)
    assert r.status_code == 200
    for identity in r.json()["identities"]:
        assert "token" not in identity, (
            f"list response leaked token field: {identity}"
        )


def test_audit_never_returns_raw_token(headers):
    r = httpx.get(f"{BACKEND_URL}{BASE}/audit?limit=20", headers=headers, timeout=10.0)
    assert r.status_code == 200
    for row in r.json()["audit"]:
        assert "token" not in row, "audit row leaked raw token"


# ── HMAC / verification safety ────────────────────────────────────

def test_forged_token_signature_rejected(headers):
    """A token with a valid JTI but the wrong signature must be
    rejected — proves HMAC verification is doing its job.
    """
    mint = httpx.post(
        f"{BACKEND_URL}{BASE}/mint",
        headers=headers,
        json={"role": "shop", "purpose": "hmac test", "ttl_minutes": 5},
        timeout=15.0,
    )
    body = mint.json()
    # Corrupt the signature (last 8 chars)
    real = body["token"]
    forged = real[:-8] + "deadbeef"
    r = httpx.post(
        f"{BACKEND_URL}{BASE}/introspect",
        headers=headers,
        json={"token": forged},
        timeout=10.0,
    )
    assert r.json()["valid"] is False, "forged token slipped past HMAC check"
