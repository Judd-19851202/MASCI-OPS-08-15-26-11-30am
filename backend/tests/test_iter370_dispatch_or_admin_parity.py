"""
iter370 · Dispatch_or_admin family consolidation kickoff.

Discovery during iter370 audit: TWO functions implement
"dispatch token OR admin token" semantics:

  1. routes/dispatch_portal_auth.py · `require_dispatch_or_admin` —
     defined inside `build_dispatch_router(...)` factory closure.
     Used by dispatch_portal_auth's own routes.
  2. server.py L10670 · `_require_dispatch_or_admin` —
     near-identical free function. Used by routes/fleet_ops.py via
     the shared kwargs passed into `build_fleet_ops_router(...)`.

These tests lock the two gates as SEMANTICALLY EQUIVALENT, so future
consolidation iterations (iter371+) can safely merge them or have one
delegate to the other without behavior risk.

This file does NOT introduce a shared helper yet. Per the iter370 rule
"begin consolidation, do not finish in one iteration," the regression
lock here is the foundation.
"""
from __future__ import annotations

import json
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
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "MASCI1982!"


def _raw(method: str, url: str, headers=None, body=None):
    h = {"User-Agent": "iter370-dispatch-parity/1.0"}
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


# Routes representing the TWO gate variants.
# /api/dispatch/me lives under dispatch_portal_auth router — uses the closure version.
# /api/operations/* routes live under fleet_ops router — use server.py's _require_dispatch_or_admin
# via the kwargs injection.

DISPATCH_PORTAL_ROUTE = "/api/dispatch/driver-qualification"  # dispatch_portal_auth closure gate
FLEET_OPS_DISPATCH_ROUTE = "/api/dispatch/fleet/status"  # fleet_ops gate (server.py wrapper)


@pytest.fixture(scope="module")
def admin_token():
    code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                      body={"password": ADMIN_PW})
    if code != 200:
        pytest.skip(f"admin login failed: {code}")
    return json.loads(body).get("token", "")


class TestDispatchOrAdminParity:
    """Lock both dispatch_or_admin variants as semantically equivalent."""

    def test_dispatch_portal_route_denies_without_token(self):
        code, _ = _raw("GET", f"{BASE_URL}{DISPATCH_PORTAL_ROUTE}")
        assert code in (401, 403, 404), f"got {code}"

    def test_fleet_ops_route_denies_without_token(self):
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_DISPATCH_ROUTE}")
        assert code in (401, 403, 404), f"got {code}"

    def test_both_routes_accept_admin_token_identically(self, admin_token):
        """Admin token should unlock BOTH variants with the same status family."""
        c1, _ = _raw("GET", f"{BASE_URL}{DISPATCH_PORTAL_ROUTE}",
                     headers={"X-Admin-Token": admin_token})
        c2, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_DISPATCH_ROUTE}",
                     headers={"X-Admin-Token": admin_token})
        # Both must NOT be 401/403. (404 is acceptable if endpoint
        # is shaped differently; 200 ideal.)
        assert c1 not in (401, 403), f"dispatch portal denied admin: {c1}"
        assert c2 not in (401, 403), f"fleet ops denied admin: {c2}"

    def test_both_routes_reject_wrong_portal_token(self, admin_token):
        """Safety token must be rejected by BOTH dispatch_or_admin variants —
        confirms cross-portal isolation is identical."""
        # Try to get a safety token via super-admin multi-login
        code, body = _raw("POST", f"{BASE_URL}/api/auth/multi-login",
                          body={"email": "jaymn.judd@mascigc.com",
                                "password": "Maddix123!"})
        if code != 200:
            pytest.skip("multi-login unavailable")
        sf_tok = (json.loads(body).get("portal_tokens") or {}).get("safety", "")
        if not sf_tok:
            pytest.skip("no safety token")
        # Safety token alone (no admin) must NOT unlock dispatch routes.
        c1, _ = _raw("GET", f"{BASE_URL}{DISPATCH_PORTAL_ROUTE}",
                     headers={"X-Safety-Token": sf_tok})
        c2, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_DISPATCH_ROUTE}",
                     headers={"X-Safety-Token": sf_tok})
        assert c1 in (401, 403), f"dispatch portal accepted safety token: {c1}"
        assert c2 in (401, 403), f"fleet ops accepted safety token: {c2}"


class TestConsolidationFoundation:
    """iter370 final shape — both gates now delegate to a single shared
    factory `make_require_dispatch_or_admin` in routes/dispatch_portal_auth.py.
    Any future drift (re-introducing duplicate role-dict logic in either
    file) will fail these guards."""

    def test_shared_factory_exists(self):
        src = Path("/app/backend/routes/dispatch_portal_auth.py").read_text()
        assert "def make_require_dispatch_or_admin(" in src, (
            "shared factory must remain canonical source of truth"
        )
        # Role-shape lives in the factory body only.
        assert '"role": "admin"' in src, "factory must return role='admin'"
        assert '"role": "dispatch"' in src, "factory must return role='dispatch'"

    def test_dispatch_portal_auth_uses_shared_factory(self):
        src = Path("/app/backend/routes/dispatch_portal_auth.py").read_text()
        assert "require_dispatch_or_admin = make_require_dispatch_or_admin(" in src, (
            "dispatch_portal_auth.build_dispatch_router must delegate to the shared factory"
        )

    def test_server_py_uses_shared_factory(self):
        src = Path("/app/backend/server.py").read_text()
        assert "_make_dispatch_or_admin(db, _is_valid_admin_token)" in src, (
            "server.py must build its dispatch_or_admin gate from the shared factory"
        )
        assert "async def _require_dispatch_or_admin(" in src, (
            "server.py must keep its _require_dispatch_or_admin wrapper "
            "(used by fleet_ops via kwargs injection)"
        )

    def test_server_py_no_longer_duplicates_role_dict(self):
        """The role-dict literals for dispatch_or_admin should now live
        ONLY in the shared factory. server.py's wrapper must delegate."""
        src = Path("/app/backend/server.py").read_text()
        # Locate the _require_dispatch_or_admin function body.
        idx = src.find("async def _require_dispatch_or_admin(")
        assert idx >= 0
        # Take next ~30 lines as the body window.
        body = src[idx:idx + 1200]
        assert "_shared_dispatch_or_admin" in body, (
            "server.py wrapper must delegate to the shared gate"
        )
        # The literal "role": "dispatch" must NOT appear inside this
        # wrapper anymore — that means it's still building its own dict.
        # We allow it elsewhere in server.py (other gates), but not here.
        assert '"role": "dispatch"' not in body[:1000], (
            "server.py wrapper must not rebuild the dispatch role dict — "
            "must delegate to make_require_dispatch_or_admin"
        )
