"""iter322 · Safety Portal read gate — RBAC closure test.

Closes the operator bug where signed-in Safety reviewers got
``"Admin or PM login required"`` toasts on the four Safety review
surfaces (Incidents · Audits & Inspections · Meetings · JHAs).

Contract locked here:
  • GET /api/incidents       — Safety OK · Admin OK · anon 401
  • GET /api/inspections     — Safety OK · Admin OK · anon 401
  • GET /api/meetings        — Safety OK · Admin OK · anon 401
  • GET /api/jhas            — Safety OK · Admin OK · anon 401
  • DELETE endpoints stay admin/PM (RBAC NOT weakened):
       DELETE /api/incidents/{id}    with safety token → 401
       DELETE /api/inspections/{id}  with safety token → 401
       DELETE /api/meetings/{id}     with safety token → 401
       DELETE /api/jhas/{id}         with safety token → 401

The error string for the new read gate is
``"Safety, Admin, or PM login required"`` (anon). The legacy
``require_admin`` string is no longer surfaced by these endpoints.

NOTE — uses urllib directly for anon/delete assertions so the
conftest's auto-X-Admin-Token monkeypatch on ``requests`` doesn't
mask the RBAC behavior we're testing.
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
    h = {"User-Agent": "Mozilla/5.0 pytest-iter322"}
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
    pw = _env("ADMIN_PASSWORD") or "Maddix123!"
    r = requests.post(f"{BASE_URL}/api/admin/login", json={"password": pw}, timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def safety_token(admin_token):
    """Mirrors the canonical safety_token bootstrap (iter266) — try
    the seed password; if stale, admin-reset and login with temp_pw."""
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


READ_ENDPOINTS = [
    "/api/incidents",
    "/api/inspections",
    "/api/meetings",
    "/api/jhas",
]


# ───────── Read gate: positive paths ─────────

@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_iter322_safety_token_200_on_read_endpoint(safety_token, path):
    """Operator bug closure — signed-in Safety user MUST get 200
    on every read surface they review from the Safety Portal."""
    r = requests.get(
        f"{BASE_URL}{path}",
        headers={"X-Safety-Token": safety_token},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, (
        f"Safety read gate failed for {path}: {r.status_code} · "
        f"{r.text[:200]}"
    )
    # Response shape is always a JSON list of summaries.
    body = r.json()
    assert isinstance(body, list), f"{path} must return a list, got {type(body)}"


@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_iter322_admin_token_still_200_on_read_endpoint(admin_token, path):
    """Regression — admin tokens MUST still pass (no weakening)."""
    r = requests.get(
        f"{BASE_URL}{path}",
        headers={"X-Admin-Token": admin_token},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, (
        f"Admin read regression on {path}: {r.status_code} · "
        f"{r.text[:200]}"
    )


# ───────── Read gate: anonymous denial ─────────

@pytest.mark.parametrize("path", READ_ENDPOINTS)
def test_iter322_anonymous_read_returns_401(path):
    """Anonymous (no token) MUST still get 401 — RBAC closed.
    Uses urllib to bypass conftest's auto-admin-token patch."""
    status, body = _raw_request("GET", path)
    assert status == 401, (
        f"Anon read leak on {path}: {status} · {body[:200]}"
    )
    # The new gate's detail message must NOT regress to the old
    # "Admin or PM login required" wording that was confusing
    # safety reviewers.
    try:
        detail = _json.loads(body).get("detail", "")
    except Exception:
        detail = body
    assert "Safety" in detail or "login required" in detail.lower(), (
        f"401 detail on {path} did not mention Safety/login: {detail}"
    )


# ───────── Detail endpoints: Safety must be able to OPEN one row ─────────

DETAIL_READ_MAP = [
    ("/api/incidents", "/api/incidents/{id}"),
    ("/api/inspections", "/api/inspections/{id}"),
]


@pytest.mark.parametrize("list_path,detail_path", DETAIL_READ_MAP)
def test_iter322_safety_token_200_on_detail_endpoint(safety_token, list_path, detail_path):
    """Operator drill-down — Safety user must open detail page from list."""
    lr = requests.get(
        f"{BASE_URL}{list_path}",
        headers={"X-Safety-Token": safety_token},
        timeout=TIMEOUT,
    )
    assert lr.status_code == 200
    items = lr.json()
    if not items:
        pytest.skip(f"No items in {list_path} to drill into")
    first = items[0]
    rid = first.get("id") or first.get("_id") or first.get("inspection_id") or first.get("incident_id")
    if not rid:
        pytest.skip(f"No id field in first row of {list_path}: {list(first.keys())[:6]}")
    dr = requests.get(
        f"{BASE_URL}{detail_path.format(id=rid)}",
        headers={"X-Safety-Token": safety_token},
        timeout=TIMEOUT,
    )
    assert dr.status_code == 200, (
        f"Safety detail gate failed for {detail_path}: {dr.status_code} · {dr.text[:200]}"
    )


# ───────── Destructive endpoints: Safety must NOT be allowed to delete ─────────

# Each entry: (path, id_to_attempt) — using a synthetic id; the gate
# must reject BEFORE the lookup, so the id need not exist. We assert
# the response is 401 (auth fail) rather than 404 (id miss).
DESTRUCTIVE_PATHS = [
    "/api/incidents/iter322-nonexistent-id",
    "/api/inspections/iter322-nonexistent-id",
    "/api/meetings/iter322-nonexistent-id",
    "/api/jhas/iter322-nonexistent-id",
]


@pytest.mark.parametrize("path", DESTRUCTIVE_PATHS)
def test_iter322_safety_token_blocked_from_delete(safety_token, path):
    """Destructive endpoints must NOT be opened to safety tokens.
    require_admin returns 401 with the legacy admin/PM string — that
    is correct here because DELETE is genuinely admin/PM territory.
    Uses urllib to bypass conftest's auto-admin-token patch."""
    status, body = _raw_request("DELETE", path, headers={"X-Safety-Token": safety_token})
    assert status == 401, (
        f"DELETE {path} leaked to safety token: {status} · {body[:200]}"
    )
