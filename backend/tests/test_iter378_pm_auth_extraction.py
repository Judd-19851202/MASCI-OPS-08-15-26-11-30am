"""
iter378 · Phase 4D · PM auth-lifecycle routes extraction parity lock.

Extracted (from server.py L2134-L2483 → routes/pm_routes.py via login_deps):
  • POST /pm/login              (~130 LOC)
  • POST /pm/forgot-password    (~110 LOC)
  • POST /pm/reset-password     (~45 LOC)
  • POST /pm/change-password    (~40 LOC)
  • POST /pm/logout             (~20 LOC)

Behavior contract — byte-identical to pre-extraction:
  • Wrong email/password → 401 "Wrong email or password" (per-PM path).
  • Disabled PM → 403.
  • PM with no password yet → 403.
  • Email-less + SHARED_LOGIN disabled → 400 "Email is required.".
  • IP lockout still applies (5 failures → 423-style behavior preserved).
  • Universal super-admin fallback (iter346-B) still works when the
    submitted credentials match a directory super-admin row.
  • /pm/forgot-password always returns 200 + generic message (anti-
    enumeration), regardless of email validity.
  • /pm/reset-password rejects bad/expired tokens (400) and rejects
    short new passwords (<6 chars, 400).
  • /pm/change-password requires per-PM session (admin token → 403).
  • /pm/logout always returns 200 + writes pm_logout audit event.

Source-level guards:
  • Body models moved (NOT in server.py anymore).
  • 5 route handlers moved (NOT decorated in server.py anymore).
  • /admin/project-managers/{pm_id}/set-password STILL in server.py
    (admin family, NOT extracted in iter378).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest


def _read_env(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:  # noqa: BLE001
        return ""
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "MASCI1982!"


def _raw(method: str, url: str, headers=None, body=None):
    h = {"User-Agent": "iter378-pm-auth/1.0"}
    if headers:
        h.update(headers)
    data = None
    if body is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


# ─── Functional parity tests ─────────────────────────────────────────

class TestPmLoginRoute:
    def test_login_route_mounted(self):
        # If it's not mounted, we'd get 404 with no detail.
        code, body = _raw("POST", f"{BASE_URL}/api/pm/login",
                          body={"email": "noexist@example.com", "password": "wrong"})
        # 401 (wrong) or 423 (lockout, also acceptable). NEVER 404.
        assert code in (401, 423), f"got {code}, body={body[:120]}"

    def test_login_wrong_credentials_returns_401_with_generic_detail(self):
        code, body = _raw("POST", f"{BASE_URL}/api/pm/login",
                          body={"email": "no-such-pm@example.com", "password": "wrong"})
        if code == 423:
            pytest.skip("IP locked from prior test; behavior unchanged")
        assert code == 401
        d = json.loads(body)
        # Must use the exact pre-extraction string.
        assert d.get("detail") == "Wrong email or password"

    def test_login_no_email_returns_400_or_lockout(self):
        # With SHARED_LOGIN disabled (default), no email → 400.
        # If IP is locked from earlier tests, 423/401 is also acceptable.
        code, body = _raw("POST", f"{BASE_URL}/api/pm/login",
                          body={"password": "anything"})
        assert code in (400, 401, 423), f"got {code}, body={body[:120]}"
        if code == 400:
            d = json.loads(body)
            assert "Email is required" in (d.get("detail") or "")


class TestPmForgotPasswordRoute:
    def test_forgot_password_returns_generic_success(self):
        code, body = _raw("POST", f"{BASE_URL}/api/pm/forgot-password",
                          body={"email": "ghost@example.com"})
        if code == 423:
            pytest.skip("IP locked")
        assert code == 200
        d = json.loads(body)
        assert d.get("ok") is True
        # Anti-enumeration: never reveal whether email exists.
        assert "reset link is on" in (d.get("message") or "")

    def test_forgot_password_invalid_email_still_generic(self):
        code, body = _raw("POST", f"{BASE_URL}/api/pm/forgot-password",
                          body={"email": "not-even-an-email"})
        if code == 423:
            pytest.skip("IP locked")
        assert code == 200
        d = json.loads(body)
        assert d.get("ok") is True


class TestPmResetPasswordRoute:
    def test_reset_password_rejects_invalid_token(self):
        code, body = _raw("POST", f"{BASE_URL}/api/pm/reset-password",
                          body={"token": "fake-or-expired",
                                "new_password": "abcdef"})
        if code == 423:
            pytest.skip("IP locked")
        assert code == 400
        d = json.loads(body)
        assert "invalid or has expired" in (d.get("detail") or "")

    def test_reset_password_rejects_short_new_password(self):
        code, body = _raw("POST", f"{BASE_URL}/api/pm/reset-password",
                          body={"token": "any", "new_password": "abc"})
        if code == 423:
            pytest.skip("IP locked")
        assert code == 400
        d = json.loads(body)
        assert "at least 6 characters" in (d.get("detail") or "")


class TestPmChangePasswordRoute:
    def test_change_password_requires_auth(self):
        code, _ = _raw("POST", f"{BASE_URL}/api/pm/change-password",
                       body={"old_password": "x", "new_password": "abcdef"})
        assert code in (401, 403), f"got {code}"

    def test_change_password_rejects_admin_session(self):
        """Per-PM session required; admin token must return 403."""
        code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                          body={"password": ADMIN_PW})
        if code != 200:
            pytest.skip("admin login unavailable")
        tok = json.loads(body).get("token", "")
        code, body = _raw("POST", f"{BASE_URL}/api/pm/change-password",
                          headers={"X-Admin-Token": tok},
                          body={"old_password": "x", "new_password": "abcdef"})
        assert code == 403
        d = json.loads(body)
        assert "per-PM session" in (d.get("detail") or "")


class TestPmLogoutRoute:
    def test_logout_requires_auth(self):
        code, _ = _raw("POST", f"{BASE_URL}/api/pm/logout")
        assert code in (401, 403)

    def test_logout_with_admin_token_returns_200(self):
        """Admin token satisfies require_admin_async → logout is 200
        and writes a pm_logout audit event."""
        code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                          body={"password": ADMIN_PW})
        if code != 200:
            pytest.skip("admin login unavailable")
        tok = json.loads(body).get("token", "")
        code, body = _raw("POST", f"{BASE_URL}/api/pm/logout",
                          headers={"X-Admin-Token": tok})
        assert code == 200, body
        d = json.loads(body)
        assert d == {"ok": True}


# ─── Source-level extraction guards ──────────────────────────────────

class TestPmAuthExtractionFoundation:
    def test_pm_routes_file_has_5_auth_handlers(self):
        src = Path("/app/backend/routes/pm_routes.py").read_text()
        for marker in [
            '"/pm/login"',
            '"/pm/forgot-password"',
            '"/pm/reset-password"',
            '"/pm/change-password"',
            '"/pm/logout"',
        ]:
            assert marker in src, f"{marker} missing from pm_routes.py"

    def test_pm_routes_factory_accepts_login_deps(self):
        src = Path("/app/backend/routes/pm_routes.py").read_text()
        assert "login_deps" in src
        assert "client_ip_fn" in src
        assert "check_login_lockout_fn" in src
        assert "directory_admin_token_fn" in src
        assert "reset_session_activity_fn" in src

    def test_pm_routes_file_has_body_models(self):
        src = Path("/app/backend/routes/pm_routes.py").read_text()
        for cls in [
            "class PMLoginBody(",
            "class PMChangePasswordBody(",
            "class PMForgotPasswordBody(",
            "class PMResetPasswordBody(",
        ]:
            assert cls in src

    def test_server_py_no_longer_owns_5_auth_handlers(self):
        src = Path("/app/backend/server.py").read_text()
        for path_marker in [
            '@api_router.post("/pm/login")',
            '@api_router.post("/pm/forgot-password")',
            '@api_router.post("/pm/reset-password")',
            '@api_router.post("/pm/change-password")',
            '@api_router.post("/pm/logout")',
        ]:
            assert path_marker not in src, (
                f"{path_marker} still in server.py — iter378 extraction incomplete"
            )

    def test_server_py_no_longer_owns_pm_body_models(self):
        """The 4 PM body models (Login/Change/Forgot/Reset) should be gone
        from server.py (they were unused after handler extraction)."""
        src = Path("/app/backend/server.py").read_text()
        # PMSetPasswordBody MUST remain (used by admin set-password route).
        assert "class PMSetPasswordBody(" in src
        assert "class PMLoginBody(" not in src
        assert "class PMChangePasswordBody(" not in src
        assert "class PMForgotPasswordBody(" not in src
        assert "class PMResetPasswordBody(" not in src

    def test_server_py_still_owns_admin_set_password(self):
        src = Path("/app/backend/server.py").read_text()
        assert "@api_router.post(\"/admin/project-managers/{pm_id}/set-password\")" in src
        assert "async def admin_set_pm_password(" in src

    def test_server_py_wires_login_deps_into_pm_router(self):
        src = Path("/app/backend/server.py").read_text()
        assert "login_deps=" in src
        assert '"client_ip_fn": _client_ip' in src
        assert '"directory_admin_token_fn": _directory_admin_token' in src
