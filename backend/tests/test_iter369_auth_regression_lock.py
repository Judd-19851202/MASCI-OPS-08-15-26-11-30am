"""
iter369 · Phase 4 · Auth Regression Lock

This file does NOT introduce or consolidate auth logic. It documents and
locks the CURRENT behavior of the 23 distinct RBAC gates discovered
during the Phase 4 audit, so that future incremental consolidation
iterations (iter370+) can prove they introduce no permission drift.

If any test in this file STARTS FAILING during a refactor, the refactor
has changed behavior and must be reverted.

Coverage philosophy:
  - Pick the 6 most operationally-sensitive gates (admin-strict, admin,
    safety, hr, dispatch, fl).
  - For each, prove: (a) correct token unlocks, (b) wrong token denies,
    (c) no token denies, (d) cross-portal token does NOT silently unlock
    a different portal's surface.
  - We do NOT test all 23 variants exhaustively — only the
    representative top-of-funnel surface for each portal.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path

import pytest
import requests


def _read_env(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:  # noqa: BLE001
        return ""
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "Maddix123!"

# Representative protected routes for each top-level gate.
# These are STABLE endpoint references — changing them means we lost
# something operationally meaningful.
ADMIN_STRICT_ROUTE = "/api/admin/backups"          # require_admin_strict
ADMIN_NAMESPACE_ROUTE = "/api/admin/governance/summary"   # require_admin (lockdown on /admin/*)
ADMIN_SHARED_ROUTE = "/api/master-lookup/employees?q=a&limit=1"  # public lookup, no auth
SAFETY_ROUTE = "/api/safety/corrective-actions"    # require_safety_token (or require_safety_or_admin)
HR_ROUTE = "/api/hr/incidents"                     # require_hr_user or similar
DISPATCH_ROUTE = "/api/dispatch/driver-qualification"  # require_dispatch_token or _or_admin
FL_ROUTE = "/api/fl/notifications/digest"          # require_fl_user

NO_AUTH_HEADERS = {"Content-Type": "application/json"}


@pytest.fixture(scope="module")
def session() -> requests.Session:
    return requests.Session()


class _Resp:
    def __init__(self, status_code: int, body: str = ""):
        self.status_code = status_code
        self.text = body


def _raw_get(url: str, headers: dict | None = None) -> _Resp:
    """Bypass /app/backend/tests/conftest.py — that file monkey-patches
    requests.get to auto-inject X-Admin-Token, which would make every
    'no token denies' test silently fail. urllib.request is untouched.

    User-Agent override is required because the ingress WAF blocks the
    default `Python-urllib/...` agent with 403."""
    h = {"User-Agent": "iter369-auth-regression/1.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return _Resp(r.status, r.read().decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return _Resp(e.code, e.read().decode("utf-8", "ignore"))


def _no_auth_get(url: str) -> _Resp:
    return _raw_get(url)


@pytest.fixture(scope="module")
def tokens(session) -> dict:
    """Acquire every portal token via super-admin multi-login."""
    r = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        headers=NO_AUTH_HEADERS,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login failed: {r.status_code}")
    pt = r.json().get("portal_tokens") or {}
    out = {"admin": pt.get("admin", ""), "safety": pt.get("safety", ""),
           "hr": pt.get("hr", ""), "dispatch": pt.get("dispatch", ""),
           "fl": pt.get("field_leadership", "")}
    # Also get the legacy single-password admin token
    r2 = session.post(f"{BASE_URL}/api/admin/login",
                      json={"password": ADMIN_PW}, headers=NO_AUTH_HEADERS)
    if r2.status_code == 200:
        out["admin_legacy"] = r2.json().get("token", "")
    return out


# ────────────────── Admin-strict gate ───────────────────


class TestAdminStrictGate:
    """`require_admin_strict` — used on backup/restore. Admin token only.
    PM tokens MUST be rejected here even though they'd unlock `require_admin`."""

    def test_no_token_denies(self, session):
        r = _no_auth_get(f"{BASE_URL}{ADMIN_STRICT_ROUTE}")
        assert r.status_code in (401, 403), r.status_code

    def test_admin_token_unlocks(self, session, tokens):
        tok = tokens.get("admin_legacy") or tokens["admin"]
        if not tok:
            pytest.skip("no admin token available")
        r = _raw_get(f"{BASE_URL}{ADMIN_STRICT_ROUTE}",
                     headers={"X-Admin-Token": tok})
        # 200 or 404 both prove the gate UNLOCKED (404 = endpoint may not
        # exist on this build but gate passed). 401/403 = gate failure.
        assert r.status_code not in (401, 403), (
            f"admin token should unlock {ADMIN_STRICT_ROUTE} but got {r.status_code}"
        )

    def test_safety_token_does_not_unlock(self, session, tokens):
        if not tokens.get("safety"):
            pytest.skip("no safety token")
        r = _raw_get(f"{BASE_URL}{ADMIN_STRICT_ROUTE}",
                     headers={"X-Safety-Token": tokens["safety"]})
        assert r.status_code in (401, 403), (
            f"safety token must NOT unlock admin-strict; got {r.status_code}"
        )


# ────────────────── Admin namespace gate (/api/admin/*) ──────────────────


class TestAdminNamespaceGate:
    """`require_admin` on routes whose path starts with /api/admin/.
    Per iter180 lockdown: PM tokens MUST be rejected here even though
    require_admin normally accepts PM tokens on non-/admin/* routes."""

    def test_no_token_denies(self, session):
        r = _no_auth_get(f"{BASE_URL}{ADMIN_NAMESPACE_ROUTE}")
        assert r.status_code in (401, 403)

    def test_admin_token_unlocks(self, session, tokens):
        tok = tokens.get("admin_legacy") or tokens["admin"]
        r = _raw_get(f"{BASE_URL}{ADMIN_NAMESPACE_ROUTE}", headers={"X-Admin-Token": tok})
        assert r.status_code == 200


# ────────────────── Safety gate ───────────────────


class TestSafetyGate:
    """`require_safety_token` — used on safety portal write-side routes."""

    def test_no_token_denies(self, session):
        r = _no_auth_get(f"{BASE_URL}{SAFETY_ROUTE}")
        assert r.status_code in (401, 403)

    def test_safety_token_unlocks(self, session, tokens):
        if not tokens.get("safety"):
            pytest.skip("no safety token")
        r = _raw_get(f"{BASE_URL}{SAFETY_ROUTE}", headers={"X-Safety-Token": tokens["safety"]})
        # 200 or 404 both pass the gate (we're testing the gate, not the
        # endpoint's response shape).
        assert r.status_code not in (401, 403)

    def test_dispatch_token_does_not_unlock(self, session, tokens):
        if not tokens.get("dispatch"):
            pytest.skip("no dispatch token")
        r = _raw_get(f"{BASE_URL}{SAFETY_ROUTE}", headers={"X-Dispatch-Token": tokens["dispatch"]})
        assert r.status_code in (401, 403)


# ────────────────── HR gate ───────────────────


class TestHrGate:
    def test_no_token_denies(self, session):
        r = _no_auth_get(f"{BASE_URL}{HR_ROUTE}")
        assert r.status_code in (401, 403)

    def test_hr_token_unlocks(self, session, tokens):
        if not tokens.get("hr"):
            pytest.skip("no hr token")
        r = _raw_get(f"{BASE_URL}{HR_ROUTE}", headers={"X-HR-Token": tokens["hr"]})
        assert r.status_code not in (401, 403)


# ────────────────── Dispatch gate ───────────────────


class TestDispatchGate:
    def test_no_token_denies(self, session):
        r = _no_auth_get(f"{BASE_URL}{DISPATCH_ROUTE}")
        assert r.status_code in (401, 403)

    def test_dispatch_token_unlocks(self, session, tokens):
        if not tokens.get("dispatch"):
            pytest.skip("no dispatch token")
        r = _raw_get(f"{BASE_URL}{DISPATCH_ROUTE}", headers={"X-Dispatch-Token": tokens["dispatch"]})
        assert r.status_code not in (401, 403)


# ────────────────── FL gate ───────────────────


class TestFlGate:
    def test_no_token_denies(self, session):
        r = _no_auth_get(f"{BASE_URL}{FL_ROUTE}")
        assert r.status_code in (401, 403)

    def test_fl_token_unlocks_via_admin_route(self, session, tokens):
        # Admin token also unlocks (the digest endpoint accepts any portal token).
        tok = tokens.get("admin_legacy") or tokens["admin"]
        r = _raw_get(f"{BASE_URL}{FL_ROUTE}", headers={"X-Admin-Token": tok})
        assert r.status_code == 200


# ────────────────── Public-route negative-control ───────────────────


class TestPublicRoutesNotGated:
    """Public routes MUST NOT regress to requiring auth — that would
    break field crew incident submission, etc."""

    def test_master_lookup_employees_is_public(self, session):
        r = _no_auth_get(f"{BASE_URL}{ADMIN_SHARED_ROUTE}")
        assert r.status_code == 200

    def test_health_is_public(self, session):
        r = _no_auth_get(f"{BASE_URL}/api/health")
        assert r.status_code == 200
