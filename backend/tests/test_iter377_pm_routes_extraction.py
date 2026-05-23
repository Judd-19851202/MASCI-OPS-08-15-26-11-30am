"""
iter377 · Phase 4D · PM read-only routes extraction parity lock.

Scope:
  Extracted from server.py → routes/pm_routes.py:
    • /pm/check
    • /pm/me
    • /pm/crew/training-records
    • /pm/crew/ppe
    • /pm/crew/capas
    • /pm/crew/summary

Behavior contract MUST be byte-identical to pre-extraction:
  • Admin token unlocks all six → 200.
  • No token → 401.
  • Cross-portal tokens rejected where original handlers rejected them
    (Safety/HR/Shop/Dispatch must NOT unlock PM routes).
  • Response shape unchanged (verified by key inventory + types).
  • The 5 NON-EXTRACTED PM routes still live in server.py
    (/pm/login, /pm/forgot-password, /pm/reset-password,
     /pm/change-password, /pm/logout) — locked by source-level guard.
  • _pm_crew_employee_names helper migrated, original removed.
"""
from __future__ import annotations

import json
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
    h = {"User-Agent": "iter377-pm-extract/1.0"}
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


PM_READONLY_ROUTES = [
    "/api/pm/check",
    "/api/pm/me",
    "/api/pm/crew/training-records",
    "/api/pm/crew/ppe",
    "/api/pm/crew/capas",
    "/api/pm/crew/summary",
]


@pytest.fixture(scope="module")
def admin_token():
    code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                      body={"password": ADMIN_PW})
    if code != 200:
        pytest.skip(f"admin login unavailable: {code}")
    return json.loads(body).get("token", "")


@pytest.fixture(scope="module")
def portal_tokens():
    code, body = _raw("POST", f"{BASE_URL}/api/auth/multi-login",
                      body={"email": "jaymn.judd@mascigc.com",
                            "password": "Maddix123!"})
    if code != 200:
        return {}
    return (json.loads(body).get("portal_tokens") or {})


class TestPmRoutesFunctionalParity:
    """Functional behavior must match pre-extraction baseline exactly."""

    def test_admin_token_unlocks_all_routes(self, admin_token):
        for path in PM_READONLY_ROUTES:
            code, _ = _raw("GET", f"{BASE_URL}{path}",
                           headers={"X-Admin-Token": admin_token})
            assert code == 200, f"{path} expected 200, got {code}"

    def test_no_token_denies_all_routes(self):
        for path in PM_READONLY_ROUTES:
            code, _ = _raw("GET", f"{BASE_URL}{path}")
            assert code in (401, 403), f"{path} expected 401/403, got {code}"

    def test_safety_token_rejected_on_pm_routes(self, portal_tokens):
        """Cross-portal isolation: safety must not unlock PM."""
        sf = portal_tokens.get("safety", "")
        if not sf:
            pytest.skip("no safety token")
        for path in PM_READONLY_ROUTES:
            code, _ = _raw("GET", f"{BASE_URL}{path}",
                           headers={"X-Safety-Token": sf})
            assert code in (401, 403), f"{path} accepted safety token: {code}"

    def test_dispatch_token_rejected_on_pm_routes(self, portal_tokens):
        dp = portal_tokens.get("dispatch", "")
        if not dp:
            pytest.skip("no dispatch token")
        for path in PM_READONLY_ROUTES:
            code, _ = _raw("GET", f"{BASE_URL}{path}",
                           headers={"X-Dispatch-Token": dp})
            assert code in (401, 403), f"{path} accepted dispatch token: {code}"


class TestPmRoutesResponseShape:
    """The response shape must remain unchanged."""

    def test_pm_check_returns_ok_true(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/pm/check",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert d == {"ok": True}

    def test_pm_me_admin_shape(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/pm/me",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert d.get("is_admin_or_legacy") is True
        assert d.get("pm") is None

    def test_pm_crew_summary_admin_shape(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/pm/crew/summary",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert d["ok"] is True
        assert d["scope"] == "admin_all"
        assert d["crew_size"] is None
        for k in ("expiring_30d", "expired", "open_capas", "ppe_records"):
            assert k in d

    def test_pm_crew_training_records_shape(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/pm/crew/training-records",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert d["ok"] is True
        assert d["scope"] == "admin_all"
        assert isinstance(d["items"], list)
        assert "count" in d

    def test_pm_crew_capas_shape(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/pm/crew/capas",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert d["ok"] is True
        assert isinstance(d["items"], list)

    def test_pm_crew_ppe_shape(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/pm/crew/ppe",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert d["ok"] is True
        assert isinstance(d["items"], list)


class TestPmRoutesQueryLimits:
    """Query limit validation should still work post-extraction."""

    def test_limit_lower_bound_enforced(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}/api/pm/crew/training-records?limit=0",
                       headers={"X-Admin-Token": admin_token})
        assert code == 422, f"limit=0 should be rejected: {code}"

    def test_limit_upper_bound_enforced(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}/api/pm/crew/training-records?limit=999",
                       headers={"X-Admin-Token": admin_token})
        assert code == 422, f"limit=999 should be rejected: {code}"

    def test_limit_in_range_accepted(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}/api/pm/crew/training-records?limit=50",
                       headers={"X-Admin-Token": admin_token})
        assert code == 200


# ─── Source-level extraction locks ───────────────────────────────────

class TestExtractionFoundation:
    """Lock the iter377 source-level extraction shape."""

    def test_pm_routes_file_exists(self):
        assert Path("/app/backend/routes/pm_routes.py").exists()

    def test_pm_routes_file_defines_factory(self):
        src = Path("/app/backend/routes/pm_routes.py").read_text()
        assert "def build_pm_router(" in src

    def test_pm_routes_file_owns_the_6_handlers(self):
        src = Path("/app/backend/routes/pm_routes.py").read_text()
        for path in ['"/pm/check"', '"/pm/me"',
                     '"/pm/crew/training-records"',
                     '"/pm/crew/ppe"',
                     '"/pm/crew/capas"',
                     '"/pm/crew/summary"']:
            assert path in src, f"{path} missing from pm_routes.py"

    def test_pm_routes_file_owns_crew_helper(self):
        src = Path("/app/backend/routes/pm_routes.py").read_text()
        assert "async def _pm_crew_employee_names(" in src

    def test_server_py_no_longer_owns_extracted_handlers(self):
        """The 6 extracted routes must NOT have @api_router decorators
        in server.py anymore."""
        src = Path("/app/backend/server.py").read_text()
        # Each path should appear ZERO times as a route decorator now.
        for path_marker in [
            '@api_router.get("/pm/check")',
            '@api_router.get("/pm/me")',
            '@api_router.get("/pm/crew/training-records")',
            '@api_router.get("/pm/crew/ppe")',
            '@api_router.get("/pm/crew/capas")',
            '@api_router.get("/pm/crew/summary")',
        ]:
            assert path_marker not in src, (
                f"{path_marker} still present in server.py — extraction incomplete"
            )

    def test_server_py_still_owns_non_extracted_pm_routes(self):
        """iter377-locked baseline. Updated in iter378: ALL 5 PM auth-
        lifecycle routes (/pm/login, /pm/forgot-password, /pm/reset-password,
        /pm/change-password, /pm/logout) have now been extracted as well.
        The ONLY remaining PM-related route in server.py is the
        admin-side set-password route, which belongs to the admin family
        and is not a PM-portal endpoint."""
        src = Path("/app/backend/server.py").read_text()
        # Admin-side PM management route still here.
        assert '@api_router.post("/admin/project-managers/{pm_id}/set-password")' in src, (
            "admin set-password route must remain in server.py (admin family)"
        )
        # All 5 PM-portal auth routes are now in pm_routes.py.
        for path_marker in [
            '@api_router.post("/pm/login")',
            '@api_router.post("/pm/forgot-password")',
            '@api_router.post("/pm/reset-password")',
            '@api_router.post("/pm/change-password")',
            '@api_router.post("/pm/logout")',
        ]:
            assert path_marker not in src, (
                f"{path_marker} re-introduced in server.py — iter378 extraction must hold"
            )

    def test_server_py_no_longer_owns_crew_helper(self):
        src = Path("/app/backend/server.py").read_text()
        # The helper SIGNATURE we removed; the import statement and the
        # router-mount line are fine.
        assert "async def _pm_crew_employee_names(actor, days: int = 180)" not in src, (
            "_pm_crew_employee_names still inline in server.py — extraction incomplete"
        )

    def test_server_py_mounts_new_router(self):
        src = Path("/app/backend/server.py").read_text()
        assert "build_pm_router(" in src
        assert "include_router(_pm_router)" in src
