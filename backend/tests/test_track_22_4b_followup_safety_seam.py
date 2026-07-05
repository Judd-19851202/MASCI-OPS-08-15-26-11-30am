"""TRACK 22.4b-followup-Safety · role_guard_validation_seam regression locks.

Every test below encodes an invariant the shared seam MUST uphold:

1. Real per-role auth still works (regression proof — the seam did not
   weaken production auth).
2. A valid PVI token for role X is accepted on role-X endpoints.
3. A valid PVI token for role X is REJECTED on role-Y endpoints
   (role-scoped, cross-role leakage is impossible).
4. Garbage / malformed tokens still 401.
5. Admin tokens still bypass safety+shop gates (no regression to admin
   power).
6. Revoked PVI tokens 401 immediately.

These lock the seam so future refactors cannot silently regress
production RBAC.
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


def _login() -> dict:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=10.0,
    )
    r.raise_for_status()
    return r.json()


@pytest.fixture(scope="module")
def admin_token() -> str:
    return (_login().get("portal_tokens") or {}).get("admin") or ""


@pytest.fixture(scope="module")
def real_safety_token() -> str:
    # Master directory login fans out per-portal tokens including safety.
    return (_login().get("portal_tokens") or {}).get("safety") or ""


def _mint(admin_token: str, role: str, ttl_minutes: int = 30) -> dict:
    r = httpx.post(
        f"{BACKEND_URL}/api/admin/preview-validation-identities/mint",
        headers={"X-Admin-Token": admin_token},
        json={
            "role": role,
            "purpose": f"seam-regression-{role}",
            "ttl_minutes": ttl_minutes,
            "validation_track": "TRACK_22_4B_FOLLOWUP_SAFETY_SEAM_REGRESSION",
        },
        timeout=10.0,
    )
    r.raise_for_status()
    return r.json()


@pytest.fixture
def safety_pvi(admin_token) -> dict:
    return _mint(admin_token, "safety")


@pytest.fixture
def shop_pvi(admin_token) -> dict:
    return _mint(admin_token, "shop")


# ── 1. Regression: real safety token still passes ─────────────────

def test_real_safety_token_still_works(real_safety_token):
    assert real_safety_token, "master directory must issue a real safety portal token"
    r = httpx.get(
        f"{BACKEND_URL}/api/safety/overview",
        headers={"X-Safety-Token": real_safety_token},
        timeout=10.0,
    )
    assert r.status_code == 200, f"real safety token must still work: {r.text}"


# ── 2. Valid PVI accepted on same-role endpoint ────────────────────

def test_safety_pvi_accepted_on_safety_overview(safety_pvi):
    tok = safety_pvi["token"]
    r = httpx.get(
        f"{BACKEND_URL}/api/safety/overview",
        headers={"X-Safety-Token": tok},
        timeout=10.0,
    )
    assert r.status_code == 200, f"safety PVI must reach /api/safety/overview: {r.text}"


def test_shop_pvi_accepted_on_shop_me(shop_pvi):
    tok = shop_pvi["token"]
    r = httpx.get(
        f"{BACKEND_URL}/api/shop/me",
        headers={"X-Shop-Token": tok},
        timeout=10.0,
    )
    assert r.status_code == 200, f"shop PVI must reach /api/shop/me: {r.text}"


# ── 3. Cross-role rejection ────────────────────────────────────────

def test_shop_pvi_rejected_on_safety_endpoint(shop_pvi):
    r = httpx.get(
        f"{BACKEND_URL}/api/safety/overview",
        headers={"X-Safety-Token": shop_pvi["token"]},
        timeout=10.0,
    )
    assert r.status_code == 401


def test_safety_pvi_rejected_on_shop_endpoint(safety_pvi):
    r = httpx.get(
        f"{BACKEND_URL}/api/shop/me",
        headers={"X-Shop-Token": safety_pvi["token"]},
        timeout=10.0,
    )
    assert r.status_code == 401


# ── 4. Garbage tokens still rejected ───────────────────────────────

@pytest.mark.parametrize("bad", [
    "totally-invalid",
    "PVI.malformed",
    "PVI.fake.badsignature",
    "",
])
def test_garbage_tokens_still_401_on_safety(bad):
    r = httpx.get(
        f"{BACKEND_URL}/api/safety/overview",
        headers={"X-Safety-Token": bad},
        timeout=10.0,
    )
    assert r.status_code == 401, f"expected 401 for token={bad!r}"


# ── 5. Admin token still bypasses (no regression) ─────────────────

def test_admin_token_still_bypasses_shop_gate(admin_token):
    r = httpx.get(
        f"{BACKEND_URL}/api/shop/me",
        headers={"X-Admin-Token": admin_token},
        timeout=10.0,
    )
    assert r.status_code == 200


# ── 6. Revoked PVI 401s immediately ────────────────────────────────

def test_revoked_safety_pvi_401s_immediately(admin_token):
    minted = _mint(admin_token, "safety")
    tok = minted["token"]
    identity_id = minted["validation_identity_id"]
    # sanity — it works first
    r = httpx.get(
        f"{BACKEND_URL}/api/safety/overview",
        headers={"X-Safety-Token": tok},
        timeout=10.0,
    )
    assert r.status_code == 200
    # revoke
    r = httpx.post(
        f"{BACKEND_URL}/api/admin/preview-validation-identities/{identity_id}/revoke",
        headers={"X-Admin-Token": admin_token},
        timeout=10.0,
    )
    assert r.status_code == 200
    # now must 401
    r = httpx.get(
        f"{BACKEND_URL}/api/safety/overview",
        headers={"X-Safety-Token": tok},
        timeout=10.0,
    )
    assert r.status_code == 401
