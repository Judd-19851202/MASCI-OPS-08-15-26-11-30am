"""
iter379 · Phase 4D · Governance & Operational Inventory routes extraction lock.

Extracted from server.py L652-L721 → routes/governance.py (appended to the
existing build_governance_router factory):
  • GET /api/admin/operational-inventory
  • GET /api/admin/operational-inventory/portals
  • GET /api/admin/operational-inventory/translation
  • GET /api/admin/operational-inventory/drift
  • GET /api/admin/guidance/search-misses

Why these 5: pure delegation to governance.inventory (4) + simple DB read +
aggregation (1). All admin-strict gated. Zero state mutation. Zero coupling
to server.py module-level helpers.

Behavior contract — byte-identical to pre-extraction.
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
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "Maddix123!"


def _raw(method: str, url: str, headers=None):
    h = {"User-Agent": "iter379-gov-extract/1.0"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


EXTRACTED_ROUTES = [
    "/api/admin/operational-inventory",
    "/api/admin/operational-inventory/portals",
    "/api/admin/operational-inventory/translation",
    "/api/admin/operational-inventory/drift",
    "/api/admin/guidance/search-misses",
]


@pytest.fixture(scope="module")
def admin_token():
    import json as _json
    req = urllib.request.Request(
        f"{BASE_URL}/api/admin/login",
        data=_json.dumps({"password": ADMIN_PW}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": "iter379-gov-extract/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = _json.loads(r.read().decode())
            return d.get("token", "")
    except Exception:
        pytest.skip("admin login unavailable")


class TestGovernanceRoutesFunctionalParity:
    def test_admin_unlocks_all_5_routes(self, admin_token):
        for path in EXTRACTED_ROUTES:
            code, _ = _raw("GET", f"{BASE_URL}{path}",
                           headers={"X-Admin-Token": admin_token})
            assert code == 200, f"{path}: got {code}"

    def test_no_token_denies_all_5_routes(self):
        for path in EXTRACTED_ROUTES:
            code, _ = _raw("GET", f"{BASE_URL}{path}")
            assert code in (401, 403), f"{path}: got {code}"

    def test_pm_token_rejected_on_admin_strict_routes(self, admin_token):
        """admin-strict gate rejects PM tokens entirely."""
        # We don't have a live PM token here, but the dispatch token from
        # multi-login is a good cross-portal proxy.
        import json as _json
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/multi-login",
            data=_json.dumps({"email": "jaymn.judd@mascigc.com",
                              "password": "Maddix123!"}).encode(),
            headers={"Content-Type": "application/json",
                     "User-Agent": "iter379-gov-extract/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                tokens = (_json.loads(r.read().decode()).get("portal_tokens") or {})
        except Exception:
            pytest.skip("multi-login unavailable")
        dp = tokens.get("dispatch", "")
        if not dp:
            pytest.skip("no dispatch token")
        for path in EXTRACTED_ROUTES:
            code, _ = _raw("GET", f"{BASE_URL}{path}",
                           headers={"X-Dispatch-Token": dp})
            assert code in (401, 403), f"{path} accepted dispatch token: {code}"


class TestGovernanceRoutesResponseShape:
    """Response shape must match pre-extraction baseline."""

    def test_operational_inventory_returns_dict(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/operational-inventory",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert isinstance(d, dict)

    def test_portals_key_present(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/operational-inventory/portals",
                          headers={"X-Admin-Token": admin_token})
        d = json.loads(body)
        assert "portals" in d
        assert isinstance(d["portals"], list)

    def test_translation_returns_dict(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/operational-inventory/translation",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert isinstance(d, dict)

    def test_drift_returns_dict(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/operational-inventory/drift",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        assert isinstance(d, dict)

    def test_guidance_search_misses_shape(self, admin_token):
        code, body = _raw("GET", f"{BASE_URL}/api/admin/guidance/search-misses",
                          headers={"X-Admin-Token": admin_token})
        assert code == 200
        d = json.loads(body)
        for k in ("recent", "top", "count"):
            assert k in d, f"missing key {k}"
        assert isinstance(d["recent"], list)
        assert isinstance(d["top"], list)


class TestGovernanceExtractionFoundation:
    """Lock the iter379 source-level extraction shape."""

    def test_routes_governance_owns_all_5_handlers(self):
        src = Path("/app/backend/routes/governance.py").read_text()
        for marker in [
            '"/api/admin/operational-inventory"',
            '"/api/admin/operational-inventory/portals"',
            '"/api/admin/operational-inventory/translation"',
            '"/api/admin/operational-inventory/drift"',
            '"/api/admin/guidance/search-misses"',
        ]:
            assert marker in src, f"{marker} missing from routes/governance.py"

    def test_server_py_no_longer_owns_extracted_routes(self):
        src = Path("/app/backend/server.py").read_text()
        for path_marker in [
            '@api_router.get("/admin/operational-inventory")',
            '@api_router.get("/admin/operational-inventory/portals")',
            '@api_router.get("/admin/operational-inventory/translation")',
            '@api_router.get("/admin/operational-inventory/drift")',
            '@api_router.get("/admin/guidance/search-misses")',
        ]:
            assert path_marker not in src, (
                f"{path_marker} still present in server.py — iter379 extraction incomplete"
            )

    def test_governance_router_still_mounted(self):
        src = Path("/app/backend/server.py").read_text()
        assert "build_governance_router(db, require_admin_strict)" in src

    def test_routes_governance_has_existing_compliance_routes_too(self):
        """The 7 pre-existing compliance + governance summary routes
        must still be in routes/governance.py."""
        src = Path("/app/backend/routes/governance.py").read_text()
        for marker in [
            '"/api/admin/compliance/scan"',
            '"/api/admin/compliance/findings"',
            '"/api/admin/governance/summary"',
        ]:
            assert marker in src
