"""DCP-1 · Driver Command Profile regression suite (2026-06-08)."""
from __future__ import annotations
import json as _json
import os
import urllib.request
import urllib.error
import pytest
import requests


def _raw_request(method: str, path: str, headers: dict, body: dict | None = None):
    """Bypass the conftest requests-patch by using urllib directly.

    This is the ONLY way to send a request with X-HR-Token but NO
    X-Admin-Token in this test setup."""
    url = f"{BASE}{path}"
    data = None
    headers = {**headers, "User-Agent": "Mozilla/5.0 (MASCI-pytest)"}
    if body is not None:
        data = _json.dumps(body).encode("utf-8")
        headers = {**headers, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


BASE = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://backup-forensics.preview.emergentagent.com",
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


@pytest.fixture
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
    status, body = _raw_request(
        "GET",
        f"/api/operations/drivers/{sample_driver}/profile",
        headers={"X-HR-Token": hr_token},
    )
    assert status == 200, body
    payload = _json.loads(body)
    assert payload["_role"] == "hr"
    assert "mapping_health" not in payload
    # HR still sees safety + training + motive
    assert "safety" in payload
    assert "training" in payload
    assert "motive" in payload


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
