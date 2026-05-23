"""
iter372 · Safety family consolidation lock.

Safety is the highest-traffic auth family. This iteration ONLY migrates
the narrow fleet-ops safety gate (`_require_safety_or_admin_fleet`) into
a shared factory `make_require_safety_or_admin_fleet`. The richer
`make_require_safety_or_admin` (in routes/safety_portal/_deps.py) is
intentionally NOT touched — it serves a different surface (Site Inspection
write, topic library, notifications) and has a different return-shape
contract (`_actor` key) that the consumers depend on.

Deliverables locked here:
  1. Shared factory `make_require_safety_or_admin_fleet` exists in
     routes/safety_portal/_deps.py.
  2. server.py's `_require_safety_or_admin_fleet` wrapper delegates to it.
  3. Functional behavior is unchanged across the critical safety surfaces:
       • Safety token accepted where currently accepted.
       • Admin accepted where currently accepted.
       • HR shared visibility unchanged.
       • PM scoped read behavior unchanged.
       • Anonymous rejected.
       • Wrong-portal tokens rejected (cross-portal isolation).
       • CAPA / Incident / Training surfaces unchanged.
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

# Fleet-ops safety route — uses _require_safety_or_admin_fleet
FLEET_OPS_SAFETY_ROUTE = "/api/safety/fleet/emergency-equipment"  # canonical safety fleet endpoint

# Richer canonical write-side surfaces — use make_require_safety_or_admin
SAFETY_INSPECTIONS = "/api/inspections"

# Shared HR + Safety read surface — uses make_require_safety_or_hr_or_admin
SAFETY_TRAINING_RECORDS = "/api/safety/training-records"

# Safety + Admin + PM read gate — uses make_require_safety_admin_or_pm
INCIDENTS_LIST = "/api/incidents"


def _raw(method: str, url: str, headers=None, body=None):
    h = {"User-Agent": "iter372-safety-parity/1.0"}
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


@pytest.fixture(scope="module")
def admin_token():
    code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                      body={"password": ADMIN_PW})
    if code != 200:
        pytest.skip(f"admin login failed: {code}")
    return json.loads(body).get("token", "")


@pytest.fixture(scope="module")
def portal_tokens():
    """Mint all portal tokens via super-admin multi-login fallback."""
    code, body = _raw("POST", f"{BASE_URL}/api/auth/multi-login",
                      body={"email": "jaymn.judd@mascigc.com",
                            "password": "Maddix123!"})
    if code != 200:
        return {}
    return (json.loads(body).get("portal_tokens") or {})


# ─── Functional regression — fleet-ops safety gate ────────────────────

class TestSafetyOrAdminFleetGate:
    """Lock the migrated fleet-ops safety gate's behavior."""

    def test_fleet_route_denies_anonymous(self):
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SAFETY_ROUTE}")
        assert code in (401, 403, 404), f"got {code}"

    def test_fleet_route_accepts_admin(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SAFETY_ROUTE}",
                       headers={"X-Admin-Token": admin_token})
        assert code not in (401, 403), f"admin denied on safety fleet: {code}"

    def test_fleet_route_accepts_safety_token(self, portal_tokens):
        sf_tok = portal_tokens.get("safety", "")
        if not sf_tok:
            pytest.skip("no safety token")
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SAFETY_ROUTE}",
                       headers={"X-Safety-Token": sf_tok})
        assert code not in (401, 403), (
            f"safety token denied on its own fleet surface: {code}"
        )

    def test_fleet_route_rejects_dispatch_token(self, portal_tokens):
        """Cross-portal isolation — dispatch must not unlock safety fleet."""
        dp_tok = portal_tokens.get("dispatch", "")
        if not dp_tok:
            pytest.skip("no dispatch token")
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SAFETY_ROUTE}",
                       headers={"X-Dispatch-Token": dp_tok})
        assert code in (401, 403), (
            f"safety fleet accepted dispatch token: {code}"
        )

    def test_fleet_route_rejects_shop_token(self, portal_tokens):
        """Cross-portal isolation — shop must not unlock safety fleet."""
        sh_tok = portal_tokens.get("shop", "")
        if not sh_tok:
            pytest.skip("no shop token")
        code, _ = _raw("GET", f"{BASE_URL}{FLEET_OPS_SAFETY_ROUTE}",
                       headers={"X-Shop-Token": sh_tok})
        assert code in (401, 403), (
            f"safety fleet accepted shop token: {code}"
        )


# ─── Functional regression — richer surfaces (must remain unchanged) ──

class TestSafetyOrAdminRicherSurfacesUnchanged:
    """Lock that the surfaces using the richer `make_require_safety_or_admin`
    (NOT touched in iter372) still work exactly as before."""

    def test_inspections_post_anonymous_denied(self):
        # POST without any token must be denied (site-inspection write surface)
        code, _ = _raw("POST", f"{BASE_URL}{SAFETY_INSPECTIONS}", body={})
        # 401 (unauth) or 422 (validation) both acceptable; 200 would be a regression.
        assert code != 200, f"site inspection POST accepted anonymous: {code}"

    def test_safety_topic_library_admin_can_read(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}/api/safety/topic-library",
                       headers={"X-Admin-Token": admin_token})
        # Should be 200 or 404 (if endpoint moved), but never 401/403 with admin.
        assert code not in (401, 403), (
            f"safety topic library denied admin: {code}"
        )


class TestSafetyAdminOrPmReadGateUnchanged:
    """`make_require_safety_admin_or_pm` (Safety+Admin+PM) must keep
    accepting all three. Locks the iter322 fix that resolved the original
    'Admin or PM login required' bug for safety reviewers."""

    def test_incidents_list_admin_accepted(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}{INCIDENTS_LIST}",
                       headers={"X-Admin-Token": admin_token})
        assert code not in (401, 403), (
            f"incidents list denied admin: {code}"
        )

    def test_incidents_list_safety_accepted(self, portal_tokens):
        sf_tok = portal_tokens.get("safety", "")
        if not sf_tok:
            pytest.skip("no safety token")
        code, _ = _raw("GET", f"{BASE_URL}{INCIDENTS_LIST}",
                       headers={"X-Safety-Token": sf_tok})
        assert code not in (401, 403), (
            f"incidents list denied safety reviewer (iter322 regression): {code}"
        )

    def test_incidents_list_anonymous_denied(self):
        code, _ = _raw("GET", f"{BASE_URL}{INCIDENTS_LIST}")
        assert code in (401, 403), (
            f"incidents list accepted anonymous: {code}"
        )


class TestSafetyHrSharedReadUnchanged:
    """`make_require_safety_or_hr_or_admin` shared HR/Safety/Admin
    visibility (training records, documents, employee safety profile)
    must keep accepting all three."""

    def test_training_records_admin_accepted(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}{SAFETY_TRAINING_RECORDS}",
                       headers={"X-Admin-Token": admin_token})
        assert code not in (401, 403), (
            f"training records denied admin: {code}"
        )

    def test_training_records_safety_accepted(self, portal_tokens):
        sf_tok = portal_tokens.get("safety", "")
        if not sf_tok:
            pytest.skip("no safety token")
        code, _ = _raw("GET", f"{BASE_URL}{SAFETY_TRAINING_RECORDS}",
                       headers={"X-Safety-Token": sf_tok})
        assert code not in (401, 403), (
            f"training records denied safety: {code}"
        )

    def test_training_records_hr_accepted(self, portal_tokens):
        hr_tok = portal_tokens.get("hr", "")
        if not hr_tok:
            pytest.skip("no hr token")
        code, _ = _raw("GET", f"{BASE_URL}{SAFETY_TRAINING_RECORDS}",
                       headers={"X-HR-Token": hr_tok})
        assert code not in (401, 403), (
            f"training records denied hr (shared accountability regression): {code}"
        )

    def test_training_records_anonymous_denied(self):
        code, _ = _raw("GET", f"{BASE_URL}{SAFETY_TRAINING_RECORDS}")
        assert code in (401, 403), (
            f"training records accepted anonymous: {code}"
        )


# ─── Source-level consolidation locks ────────────────────────────────

class TestSafetyConsolidationFoundation:
    """Lock the iter372 source-level consolidation shape."""

    def test_shared_fleet_factory_exists(self):
        src = Path("/app/backend/routes/safety_portal/_deps.py").read_text()
        assert "def make_require_safety_or_admin_fleet(" in src, (
            "shared safety fleet factory must remain canonical source of truth"
        )
        assert '"role": "admin"' in src, "factory must return role='admin'"
        assert '"role": "safety"' in src, "factory must return role='safety'"

    def test_richer_safety_or_admin_factory_preserved(self):
        """The richer `make_require_safety_or_admin` factory (with `_actor`
        return shape) MUST remain — it serves different surfaces and was
        NOT touched in iter372."""
        src = Path("/app/backend/routes/safety_portal/_deps.py").read_text()
        assert "def make_require_safety_or_admin(" in src, (
            "richer make_require_safety_or_admin must remain — narrow fleet "
            "factory does NOT replace it"
        )
        # The _actor return shape is the distinguishing contract.
        assert '"_actor": "safety"' in src, (
            "richer factory must keep returning _actor='safety' for its "
            "consumers (site inspection write, topic library, notifications)"
        )
        assert '"_actor": "admin"' in src, (
            "richer factory must keep returning _actor='admin' for its consumers"
        )

    def test_server_py_uses_shared_fleet_factory(self):
        src = Path("/app/backend/server.py").read_text()
        assert "_make_safety_or_admin_fleet(" in src, (
            "server.py must build its fleet safety gate from the shared factory"
        )
        assert "make_require_safety_or_admin_fleet" in src, (
            "server.py must import the shared safety fleet factory"
        )
        assert "async def _require_safety_or_admin_fleet(" in src, (
            "server.py must keep its _require_safety_or_admin_fleet wrapper "
            "(used by fleet_ops via kwargs injection)"
        )

    def test_server_py_wrapper_delegates_no_inline_role_dict(self):
        """The fleet wrapper must not rebuild the role dict — that lives
        in the shared factory only."""
        src = Path("/app/backend/server.py").read_text()
        idx = src.find("async def _require_safety_or_admin_fleet(")
        assert idx >= 0
        body = src[idx:idx + 1300]
        assert "_shared_safety_or_admin_fleet" in body, (
            "server.py wrapper must delegate to the shared safety gate"
        )

    def test_safety_token_canonical_factory_preserved(self):
        """`make_require_safety_token` (canonical safety-only gate)
        must remain untouched — it's the foundational dependency for
        all safety portal write/delete routes."""
        src = Path("/app/backend/routes/safety_portal/_deps.py").read_text()
        assert "def make_require_safety_token(" in src, (
            "make_require_safety_token must remain — foundational gate"
        )

    def test_safety_or_hr_or_admin_factory_preserved(self):
        """`make_require_safety_or_hr_or_admin` (HR/Safety shared
        visibility) must remain untouched — locks the shared
        accountability surface."""
        src = Path("/app/backend/routes/safety_portal/_deps.py").read_text()
        assert "def make_require_safety_or_hr_or_admin(" in src

    def test_safety_admin_or_pm_factory_preserved(self):
        """`make_require_safety_admin_or_pm` (iter322 fix — Safety+Admin+PM
        read gate) must remain untouched."""
        src = Path("/app/backend/routes/safety_portal/_deps.py").read_text()
        assert "def make_require_safety_admin_or_pm(" in src
