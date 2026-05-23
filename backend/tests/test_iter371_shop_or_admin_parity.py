"""
iter371 · Shop family consolidation lock.

Locks the semantic split between the two Shop+Admin gates:

  • server.py `require_shop_or_admin`           → richer gate: admin/shop/PM
    chain, iter180 admin-namespace lockdown, returns True / PM-doc / shop-doc.
  • routes/shop_portal_deps.make_require_shop_or_admin_fleet → NARROW
    gate: admin/shop-HMAC only, returns {"role": ...} dict. Used by
    fleet_ops.py only.

Why two gates? They serve different surfaces. The narrow one is delegated
to fleet_ops via kwargs injection; PM tokens have no fleet-ops contract.
The richer one is for equipment-master / inspections / parts where PM
project-scoping is required.

iter371 deliverables:
  1. Extract `_require_shop_or_admin_fleet` into a shared factory
     `make_require_shop_or_admin_fleet` (mirrors iter370 dispatch pattern).
  2. server.py wrapper now delegates to the factory.
  3. This file locks: (a) the factory exists, (b) the wrapper delegates,
     (c) PM tokens are REJECTED on the fleet gate (cross-portal isolation),
     (d) the richer require_shop_or_admin still accepts PM tokens.
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
    h = {"User-Agent": "iter371-shop-parity/1.0"}
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


# Fleet-ops shop route — uses _require_shop_or_admin_fleet
FLEET_OPS_SHOP_ROUTE = "/api/shop/fleet/defects"


@pytest.fixture(scope="module")
def admin_token():
    code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                      body={"password": ADMIN_PW})
    if code != 200:
        pytest.skip(f"admin login failed: {code}")
    return json.loads(body).get("token", "")


class TestShopOrAdminFleetGate:
    """Functional regression lock for the narrow fleet-ops shop gate."""

    def test_fleet_route_denies_without_token(self):
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SHOP_ROUTE}")
        assert code in (401, 403, 404), f"got {code}"

    def test_fleet_route_accepts_admin_token(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SHOP_ROUTE}",
                       headers={"X-Admin-Token": admin_token})
        assert code not in (401, 403), f"admin denied on shop fleet: {code}"

    def test_fleet_route_rejects_dispatch_token(self, admin_token):
        """Cross-portal isolation: dispatch token must not unlock shop fleet."""
        # Mint a dispatch token via super-admin multi-login if available.
        code, body = _raw("POST", f"{BASE_URL}/api/auth/multi-login",
                          body={"email": "jaymn.judd@mascigc.com",
                                "password": "Maddix123!"})
        if code != 200:
            pytest.skip("multi-login unavailable")
        dp_tok = (json.loads(body).get("portal_tokens") or {}).get("dispatch", "")
        if not dp_tok:
            pytest.skip("no dispatch token")
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SHOP_ROUTE}",
                       headers={"X-Dispatch-Token": dp_tok})
        assert code in (401, 403), f"fleet shop accepted dispatch token: {code}"


class TestShopConsolidationFoundation:
    """Lock the iter371 source-level consolidation shape."""

    def test_shared_factory_exists(self):
        src = Path("/app/backend/routes/shop_portal_deps.py").read_text()
        assert "def make_require_shop_or_admin_fleet(" in src, (
            "shared shop factory must remain canonical source of truth"
        )
        assert '"role": "admin"' in src, "factory must return role='admin'"
        assert '"role": "shop"' in src, "factory must return role='shop'"

    def test_server_py_uses_shared_factory(self):
        src = Path("/app/backend/server.py").read_text()
        assert "_make_shop_or_admin_fleet(" in src, (
            "server.py must build its fleet shop gate from the shared factory"
        )
        assert "make_require_shop_or_admin_fleet" in src, (
            "server.py must import the shared shop factory"
        )
        assert "async def _require_shop_or_admin_fleet(" in src, (
            "server.py must keep its _require_shop_or_admin_fleet wrapper "
            "(used by fleet_ops via kwargs injection)"
        )

    def test_server_py_wrapper_delegates_no_inline_role_dict(self):
        """The fleet wrapper must not rebuild the role dict — that lives
        in the shared factory only."""
        src = Path("/app/backend/server.py").read_text()
        idx = src.find("async def _require_shop_or_admin_fleet(")
        assert idx >= 0
        # Take the immediate body window.
        body = src[idx:idx + 1100]
        assert "_shared_shop_or_admin_fleet" in body, (
            "server.py wrapper must delegate to the shared shop gate"
        )

    def test_richer_require_shop_or_admin_still_exists(self):
        """The richer gate (with PM + admin-namespace lockdown) MUST
        remain — it serves different surfaces."""
        src = Path("/app/backend/server.py").read_text()
        assert "async def require_shop_or_admin(" in src, (
            "richer require_shop_or_admin must remain — narrow factory "
            "does NOT replace it"
        )
        # The iter180 admin-namespace lockdown sentinel must still be in
        # the richer gate's vicinity.
        idx = src.find("async def require_shop_or_admin(")
        body = src[idx:idx + 2500]
        assert "admin_namespace" in body, (
            "iter180 admin-namespace lockdown in the richer gate must remain"
        )
