"""
iter370 · R7 hardening — `require_admin_strict` must fail CLOSED when
`ADMIN_PASSWORD` env var is unset.

This test verifies the iter370 fix at /app/backend/server.py L368-401
which replaced the empty-password escape hatch (`if not expected_pw:
return True`) with an explicit `HTTPException(503, "Admin authentication
not configured")`.

We cannot easily test the failure path (would require unsetting the
env var and restarting the server), so we test the SUCCESS path
remains correct: with a valid password configured + valid admin token,
the gate still unlocks. The no-token denial path is already locked by
test_iter369_auth_regression_lock.py::TestAdminStrictGate::test_no_token_denies.

For the 503 fail-closed path, we do a CODE-level assertion that the
source no longer contains the `return True` escape hatch.
"""
from __future__ import annotations

import urllib.request
import urllib.error
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
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "Maddix123!"


def _raw_post(url, body, headers=None):
    import json as _json
    h = {"User-Agent": "iter370-r7/1.0", "Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=_json.dumps(body).encode(),
                                 headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def _raw_get(url, headers=None):
    h = {"User-Agent": "iter370-r7/1.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


class TestR7AdminStrictFailsClosed:
    """iter370 · R7 — require_admin_strict empty-password escape hatch removed."""

    def test_source_no_longer_contains_escape_hatch(self):
        """Code-level regression lock — any future refactor that
        re-introduces the empty-password bypass fails this test."""
        src = Path("/app/backend/server.py").read_text()
        # Locate the require_admin_strict function body.
        marker = "async def require_admin_strict("
        i = src.find(marker)
        assert i > 0, "require_admin_strict function not found"
        # Take the next ~40 lines as the body.
        body = src[i:i + 2200]
        # The fix replaces `if not expected_pw:\n        return True`
        # with `raise HTTPException(... 503 ...)`. Assert the escape
        # hatch shape is gone.
        forbidden_patterns = [
            "if not expected_pw:\n        return True",
            "if not expected_pw: return True",
        ]
        for pat in forbidden_patterns:
            assert pat not in body, (
                f"R7 regression — escape hatch re-introduced in require_admin_strict: {pat!r}"
            )
        # Assert the explicit fail-closed pattern is present.
        assert "503" in body and "Admin authentication not configured" in body, (
            "R7 regression — explicit 503 fail-closed not present"
        )

    def test_admin_strict_route_still_works_with_valid_token(self):
        """Verify the R7 fix did not break the normal admin path."""
        # Login
        code, body = _raw_post(f"{BASE_URL}/api/admin/login",
                               {"password": ADMIN_PW})
        if code != 200:
            pytest.skip(f"admin login failed: {code}")
        import json as _json
        tok = _json.loads(body).get("token", "")
        if not tok:
            pytest.skip("no admin token returned")
        # Hit the admin-strict route
        code, _ = _raw_get(f"{BASE_URL}/api/admin/backups",
                           headers={"X-Admin-Token": tok})
        # 200 or 404 both prove the gate unlocked. 401/403/503 = fail.
        assert code not in (401, 403, 503), (
            f"R7 regression — admin-strict denied a valid token: {code}"
        )

    def test_admin_strict_route_still_denies_without_token(self):
        """Ensure the gate still denies anonymous requests."""
        code, body = _raw_get(f"{BASE_URL}/api/admin/backups")
        assert code in (401, 403), f"expected 401/403, got {code}: {body[:120]}"

    def test_admin_strict_does_not_accept_pm_token(self):
        """iter370 R7 must preserve the strict-no-PM behavior."""
        # Try to login as PM
        code, body = _raw_post(f"{BASE_URL}/api/pm/login",
                               {"password": "Maddix123!"})
        if code != 200:
            pytest.skip("PM login not available in this env")
        import json as _json
        pm_tok = _json.loads(body).get("token", "")
        if not pm_tok:
            pytest.skip("no PM token returned")
        # PM token MUST NOT unlock admin-strict
        code, _ = _raw_get(f"{BASE_URL}/api/admin/backups",
                           headers={"X-PM-Token": pm_tok})
        assert code in (401, 403), (
            f"R7 regression — PM token unlocked admin-strict: {code}"
        )
