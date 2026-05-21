"""iter323 · Safety Forms ownership closure — RBAC matrix test.

Closes the operator complaint that Safety Forms still used the legacy
`1982` shared password while every other Safety-owned workflow had
moved to the Safety Portal sign-in model.

Backend contract (locked here):
  • Safety Portal user (X-Safety-Token) ─→ 200 on list + detail
  • Admin (X-Admin-Token)                ─→ 200 (no regression)
  • Legacy Safety-Forms (X-Safety-Forms-Token) ─→ 200 (backwards compat)
  • PM (X-PM-Token)                      ─→ 401 (NOT part of this model)
  • Anonymous                            ─→ 401

Surfaces under contract:
  - GET /api/safety-forms/equipment-issuances        (list)
  - GET /api/safety-forms/equipment-trainings        (list)
  - GET /api/safety-forms/check                      (auth probe)

Uses urllib for anon/PM negatives so the conftest's auto-admin-token
patch doesn't mask the RBAC behavior.
"""
from __future__ import annotations

import json as _json
import os
import urllib.error
import urllib.request

import pytest
import requests


def _read_env_var(key, default=None):
    for path in ("/app/frontend/.env", "/app/backend/.env"):
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass
    return os.environ.get(key, default)


def _env(key: str):
    path = "/app/backend/.env"
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
    except Exception:
        return None
    return None


BASE_URL = _read_env_var("REACT_APP_BACKEND_URL").rstrip("/")
TIMEOUT = 60


def _raw_request(method, path, headers=None):
    """Bypass conftest's auto-admin-token monkeypatch by using urllib."""
    h = {"User-Agent": "Mozilla/5.0 pytest-iter323"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(f"{BASE_URL}{path}", headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


# ───────── Fixtures ─────────


@pytest.fixture(scope="module")
def admin_token():
    pw = _env("ADMIN_PASSWORD") or "MASCI1982!"
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": pw}, timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def safety_token(admin_token):
    """Self-bootstrap a Safety Portal user token via admin reset."""
    r = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": "SafetyTest2026!"},
        timeout=TIMEOUT,
    )
    if r.status_code == 200:
        return r.json()["token"]

    users_resp = requests.get(
        f"{BASE_URL}/api/admin/safety-users",
        headers={"X-Admin-Token": admin_token},
        timeout=TIMEOUT,
    )
    if users_resp.status_code != 200:
        pytest.skip(f"Could not list safety users: {users_resp.status_code}")
    users = users_resp.json()
    users = users if isinstance(users, list) else users.get("items", [])
    target = next((u for u in users if u.get("email") == "safety@mascigc.com"), None)
    if not target:
        pytest.skip("safety@mascigc.com not in directory")
    rp = requests.post(
        f"{BASE_URL}/api/admin/safety-users/{target['id']}/reset-password",
        json={},
        headers={"X-Admin-Token": admin_token},
        timeout=TIMEOUT,
    )
    if rp.status_code != 200:
        pytest.skip(f"Safety reset failed: {rp.status_code}")
    temp_pw = rp.json().get("temp_password")
    r2 = requests.post(
        f"{BASE_URL}/api/safety/login",
        json={"email": "safety@mascigc.com", "password": temp_pw},
        timeout=TIMEOUT,
    )
    if r2.status_code != 200:
        pytest.skip(f"Safety login after reset failed: {r2.status_code}")
    return r2.json()["token"]


@pytest.fixture(scope="module")
def safety_forms_token():
    """Legacy Safety-Forms shared-password token (backwards compat)."""
    pw = _env("SAFETY_FORMS_PASSWORD") or "1982"
    r = requests.post(
        f"{BASE_URL}/api/safety-forms/login",
        json={"password": pw},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        pytest.skip(f"Legacy safety-forms login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def pm_token():
    """PM token must remain BLOCKED on this review model."""
    r = requests.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": "chriswright@mascigc.com", "password": "ChrisRocksThis2026"},
        timeout=TIMEOUT,
    )
    if r.status_code != 200:
        pytest.skip(f"PM login failed: {r.status_code}")
    return r.json()["token"]


READ_PATHS = [
    "/api/safety-forms/equipment-issuances",
    "/api/safety-forms/equipment-trainings",
    "/api/safety-forms/check",
]


# ───────── Positive paths ─────────


@pytest.mark.parametrize("path", READ_PATHS)
def test_iter323_safety_token_200_on_safety_forms_endpoint(safety_token, path):
    """Operator bug closure — signed-in Safety reviewer MUST get 200."""
    r = requests.get(
        f"{BASE_URL}{path}",
        headers={"X-Safety-Token": safety_token},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, (
        f"Safety token rejected on {path}: {r.status_code} · {r.text[:200]}"
    )


@pytest.mark.parametrize("path", READ_PATHS)
def test_iter323_admin_token_still_200(admin_token, path):
    """Regression — admin must continue to pass (global view)."""
    r = requests.get(
        f"{BASE_URL}{path}",
        headers={"X-Admin-Token": admin_token},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, (
        f"Admin regression on {path}: {r.status_code} · {r.text[:200]}"
    )


@pytest.mark.parametrize("path", READ_PATHS)
def test_iter323_legacy_safety_forms_token_still_200(safety_forms_token, path):
    """Backwards compat — legacy X-Safety-Forms-Token must keep working
    for any existing field bookmark or automation."""
    r = requests.get(
        f"{BASE_URL}{path}",
        headers={"X-Safety-Forms-Token": safety_forms_token},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, (
        f"Legacy SF token broke on {path}: {r.status_code} · {r.text[:200]}"
    )


# ───────── Negative paths (use urllib to bypass conftest auto-admin) ─────────


@pytest.mark.parametrize("path", READ_PATHS)
def test_iter323_anonymous_returns_401(path):
    """Anonymous request must remain 401 and use the new wording."""
    status, body = _raw_request("GET", path)
    assert status == 401, f"Anon leak on {path}: {status} · {body[:200]}"
    try:
        detail = _json.loads(body).get("detail", "")
    except Exception:
        detail = body
    assert "login required" in detail.lower(), (
        f"401 detail on {path} should mention 'login required', got: {detail}"
    )


@pytest.mark.parametrize("path", READ_PATHS)
def test_iter323_pm_token_blocked(pm_token, path):
    """PM tokens are intentionally NOT part of the Safety Forms review
    model. RBAC must not be widened to PM (per user directive)."""
    status, body = _raw_request("GET", path, headers={"X-PM-Token": pm_token})
    assert status == 401, (
        f"PM leak on {path}: {status} · {body[:200]} (PM should NOT see Safety Forms)"
    )


# ───────── DELETE / write surfaces — RBAC NOT widened ─────────


def test_iter323_no_unintended_delete_route_for_safety_forms():
    """Safety Forms module has no DELETE endpoints in scope. Sanity
    check — the write-side ``/return`` surface still requires auth at
    the dep layer (uses urllib to bypass conftest's auto-admin patch)."""
    status, body = _raw_request(
        "POST",
        "/api/safety-forms/equipment-issuances/iter323-nonexistent/return",
    )
    # No token → 401 from the dep layer (before any body validation).
    assert status == 401, (
        f"Return endpoint must require auth, got {status}: {body[:200]}"
    )
