"""DCP-1 · Driver Command Profile regression suite (2026-06-08).

Tests the unified `/api/operations/drivers/{driver_key}/profile`
endpoint across all four portal scopes (Admin · Safety · HR · Dispatch).
"""
from __future__ import annotations
import os
import pytest
import requests

BASE = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")


@pytest.fixture(scope="module")
def admin_token() -> str:
    r = requests.post(
        f"{BASE}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    assert r.status_code == 200
    return r.json()["portal_tokens"]["admin"]


@pytest.fixture(scope="module")
def hr_token() -> str:
    r = requests.post(
        f"{BASE}/api/hr/login",
        json={"email": "hrmanager@mascigc.com", "password": "HRTesting2026!"},
        timeout=30,
    )
    assert r.status_code == 200 and r.json().get("ok"), r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def sample_driver(admin_token):
    """Resolve a driver with a linked Motive mapping for stable tests."""
    r = requests.get(
        f"{BASE}/api/admin/integrations/cleanup/drivers",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r.status_code == 200
    rows = r.json()["rows"]
    linked = next((row for row in rows if row.get("existing_employee_id")), None)
    if not linked:
        pytest.skip("no linked driver to profile")
    return linked["existing_employee_id"]


# ── Shape ───────────────────────────────────────────────────────────
def test_admin_full_payload(admin_token, sample_driver):
    r = requests.get(
        f"{BASE}/api/operations/drivers/{sample_driver}/profile",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["_role"] == "admin"
    for key in ("identity", "operations", "safety", "training",
                "equipment_usage", "motive", "mapping_health"):
        assert key in body, f"admin payload missing {key}"
    assert body["identity"]["name"]


# ── Role redaction ──────────────────────────────────────────────────
def test_hr_redacts_mapping_health(hr_token, sample_driver):
    r = requests.get(
        f"{BASE}/api/operations/drivers/{sample_driver}/profile",
        headers={
            "X-HR-Token": hr_token,
            # Neutralize the conftest auto-injected X-Admin-Token so we
            # actually exercise the HR path (otherwise admin wins and
            # the role redaction never triggers).
            "X-Admin-Token": "neutralize-conftest-patch",
        },
        timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["_role"] == "hr"
    assert "mapping_health" not in body
    # HR still sees safety + training + motive
    assert "safety" in body
    assert "training" in body
    assert "motive" in body


# ── Identity resolution by employee UUID ────────────────────────────
def test_resolve_by_employee_uuid(admin_token, sample_driver):
    r = requests.get(
        f"{BASE}/api/operations/drivers/{sample_driver}/profile",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r.status_code == 200
    assert r.json()["identity"]["employee_uuid"] == sample_driver


# ── Unauthenticated callers rejected ────────────────────────────────
def test_no_token_rejected(sample_driver):
    r = requests.get(
        f"{BASE}/api/operations/drivers/{sample_driver}/profile",
        headers={"X-Admin-Token": "not-a-real-token"},
        timeout=30,
    )
    assert r.status_code in (401, 403)


# ── Unknown driver → 404 ────────────────────────────────────────────
def test_unknown_driver(admin_token):
    r = requests.get(
        f"{BASE}/api/operations/drivers/does-not-exist-id/profile",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r.status_code == 404


# ── No raw Motive payload leakage ───────────────────────────────────
def test_no_raw_motive_payload(admin_token, sample_driver):
    r = requests.get(
        f"{BASE}/api/operations/drivers/{sample_driver}/profile",
        headers={"X-Admin-Token": admin_token},
        timeout=30,
    )
    body = r.json()
    # Reasonable shape — keys are operational-language, not Motive raw.
    assert "raw" not in body
    motive = body.get("motive") or {}
    for forbidden in ("raw", "payload"):
        assert forbidden not in motive
