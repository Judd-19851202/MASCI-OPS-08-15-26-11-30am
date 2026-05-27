"""iter437 follow-up · /api/pm/jobs endpoint contract.

Locks the behaviour of the new PM-scoped jobs endpoint:
  • PM token → 200, scope='pm_assigned', items filtered to assigned jobs
  • Admin token → 200, scope='admin_all', every job visible
  • No token → 401 (PM token alone, no admin shadow)
  • Read-only (POST is not exposed on /pm/jobs)
  • Lives under /api/pm/* so iter180 admin-namespace boundary is
    preserved (the regression that prompted PORTAL_AUTH_TOKEN_AUDIT.md).

NOTE: `tests/conftest.py` auto-attaches `X-Admin-Token` to every
`requests` call hitting our backend URL. To exercise the no-token and
PM-only branches truthfully, this module uses `urllib` directly,
bypassing the monkey-patched `requests` layer.
"""
from __future__ import annotations

import json as _json
import urllib.request
import urllib.error

import pytest
from dotenv import dotenv_values

FRONTEND_ENV = dotenv_values("/app/frontend/.env")
BASE_URL = (FRONTEND_ENV.get("REACT_APP_BACKEND_URL") or "").strip().rstrip("/")
PM_EMAIL = "chriswright@mascigc.com"
PM_PASSWORD = "ChrisRocksThis2026"
SUPER_EMAIL = (dotenv_values("/app/backend/.env").get("SUPER_ADMIN_EMAIL") or "").strip()
SUPER_PW = (dotenv_values("/app/backend/.env").get("SUPER_ADMIN_BOOTSTRAP_PASSWORD") or "").strip()


def _http(method: str, path: str, *, headers=None, body=None, timeout: int = 15):
    """Bare urllib HTTP client — bypasses the conftest requests patch.

    Cloudflare in front of preview ingress rejects raw urllib UA strings
    with 403 "Forbidden", so we send a Mozilla UA to pass bot-detection.
    """
    url = f"{BASE_URL}{path}"
    data = None
    hdrs = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
    hdrs.update(headers or {})
    if body is not None:
        data = _json.dumps(body).encode()
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, _json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            payload = _json.loads(e.read() or b"{}")
        except Exception:
            payload = {}
        return e.code, payload


def _pm_token() -> str:
    status, body = _http(
        "POST",
        "/api/pm/login",
        body={"email": PM_EMAIL, "password": PM_PASSWORD},
    )
    assert status == 200, f"PM login failed: {status} · {body}"
    tok = body.get("token")
    assert tok
    return tok


def _admin_token() -> str:
    status, body = _http(
        "POST",
        "/api/auth/multi-login",
        body={"email": SUPER_EMAIL, "password": SUPER_PW},
    )
    assert status == 200, f"Admin multi-login failed: {status} · {body}"
    return body["portal_tokens"]["admin"]


@pytest.fixture(scope="module")
def pm_tok() -> str:
    return _pm_token()


@pytest.fixture(scope="module")
def admin_tok() -> str:
    return _admin_token()


def test_pm_jobs_requires_token():
    status, body = _http("GET", "/api/pm/jobs")
    assert status == 401, f"expected 401 without token, got {status} · {body}"


def test_pm_jobs_returns_scoped_jobs_for_pm(pm_tok):
    status, d = _http("GET", "/api/pm/jobs", headers={"X-PM-Token": pm_tok})
    assert status == 200
    assert d["ok"] is True
    assert d["scope"] == "pm_assigned"
    assert isinstance(d["items"], list)
    assert d["count"] == len(d["items"])
    for j in d["items"]:
        assert "project_number" in j
        # Never leak MongoDB internals.
        assert "_id" not in j


def test_pm_jobs_returns_all_jobs_for_admin(admin_tok, pm_tok):
    s_admin, da = _http("GET", "/api/pm/jobs", headers={"X-Admin-Token": admin_tok})
    assert s_admin == 200
    assert da["scope"] == "admin_all"
    s_pm, dp = _http("GET", "/api/pm/jobs", headers={"X-PM-Token": pm_tok})
    assert s_pm == 200
    # Admin count is a superset of PM-assigned count by definition.
    assert da["count"] >= dp["count"]


def test_pm_jobs_rejects_post():
    """The new endpoint is read-only; POST must not be mounted."""
    tok = _pm_token()
    status, _ = _http(
        "POST",
        "/api/pm/jobs",
        headers={"X-PM-Token": tok},
        body={"project_number": "evil"},
    )
    # 404 (no such method binding) or 405 (method not allowed) are both
    # valid for "no write surface". Anything in the 2xx range is a bug.
    assert status in (404, 405), f"PmJobsRead must be read-only — got {status}"
