"""
iter373 · HR family consolidation lock.

Scope (after careful inventory):
  • `require_hr_user` closure in `routes/hr_portal.py` is the ONLY safe
    extraction candidate. Pure HR-token resolver, no semantic ambiguity.
    Migrated to `make_require_hr_user` factory in `routes/hr_portal_deps.py`
    (mirrors `make_require_safety_token`).
  • The two `require_hr_or_admin` closures (in employee_lifecycle.py and
    field_leadership_portal.py) are NOT migrated — they have intentionally
    different semantics (filter-on-aggregator vs direct token check) and
    different return shapes (`_actor` vs `_actor_kind`). Documented in
    `routes/hr_portal_deps.py` module docstring.

This regression lock covers:
  1. Factory exists at module scope and returns the correct shape.
  2. hr_portal.py delegates to the factory.
  3. HR-only surfaces still work end-to-end (HR ✓, anon ✗, wrong token ✗).
  4. Shared HR/Safety/Admin surface still works.
  5. The two `require_hr_or_admin` closures REMAIN in their files
     unchanged (intentional preservation guard).
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
    h = {"User-Agent": "iter373-hr-parity/1.0"}
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


# Canonical HR-only surface — uses require_hr_user
HR_ME_ROUTE = "/api/hr/me"
HR_TRAINING_ROUTE = "/api/hr/training-records"

# Shared HR/Safety/Admin surface — uses make_require_safety_or_hr_or_admin
SAFETY_TRAINING_RECORDS = "/api/safety/training-records"


@pytest.fixture(scope="module")
def admin_token():
    code, body = _raw("POST", f"{BASE_URL}/api/admin/login",
                      body={"password": ADMIN_PW})
    if code != 200:
        pytest.skip(f"admin login failed: {code}")
    return json.loads(body).get("token", "")


@pytest.fixture(scope="module")
def portal_tokens():
    code, body = _raw("POST", f"{BASE_URL}/api/auth/multi-login",
                      body={"email": "jaymn.judd@mascigc.com",
                            "password": "Maddix123!"})
    if code != 200:
        return {}
    return (json.loads(body).get("portal_tokens") or {})


# ─── Functional regression — HR-only gate ─────────────────────────────

class TestHrUserGate:
    """Lock the migrated HR-only gate's behavior."""

    def test_hr_me_denies_anonymous(self):
        code, _ = _raw("GET", f"{BASE_URL}{HR_ME_ROUTE}")
        assert code in (401, 403), f"got {code}"

    def test_hr_me_accepts_hr_token(self, portal_tokens):
        hr_tok = portal_tokens.get("hr", "")
        if not hr_tok:
            pytest.skip("no hr token")
        code, body = _raw("GET", f"{BASE_URL}{HR_ME_ROUTE}",
                          headers={"X-HR-Token": hr_tok})
        assert code == 200, f"hr token denied on its own portal: {code}"
        # Locks the return-shape contract: _actor_kind="hr_user".
        # `/hr/me` returns the public user view, not the raw actor; but
        # the actor SHAPE is locked by the factory unit (below).

    def test_hr_me_rejects_safety_token(self, portal_tokens):
        """Cross-portal isolation: safety must not unlock HR portal."""
        sf_tok = portal_tokens.get("safety", "")
        if not sf_tok:
            pytest.skip("no safety token")
        code, _ = _raw("GET", f"{BASE_URL}{HR_ME_ROUTE}",
                       headers={"X-Safety-Token": sf_tok})
        assert code in (401, 403), f"hr/me accepted safety token: {code}"

    def test_hr_me_rejects_admin_token(self, admin_token):
        """HR portal is HR-only — admin tokens must NOT unlock it.
        (Admin access is via the /admin/hr-users namespace.)"""
        code, _ = _raw("GET", f"{BASE_URL}{HR_ME_ROUTE}",
                       headers={"X-Admin-Token": admin_token})
        assert code in (401, 403), f"hr/me accepted admin token: {code}"

    def test_hr_training_records_accepts_hr(self, portal_tokens):
        hr_tok = portal_tokens.get("hr", "")
        if not hr_tok:
            pytest.skip("no hr token")
        code, _ = _raw("GET", f"{BASE_URL}{HR_TRAINING_ROUTE}",
                       headers={"X-HR-Token": hr_tok})
        assert code not in (401, 403), (
            f"hr training records denied hr token: {code}"
        )


class TestSharedHrSafetyAdminUnchanged:
    """Shared HR/Safety/Admin surface (via make_require_safety_or_hr_or_admin)
    must keep accepting all three. NOT touched by iter373 — locks the
    shared accountability contract."""

    def test_safety_training_admin(self, admin_token):
        code, _ = _raw("GET", f"{BASE_URL}{SAFETY_TRAINING_RECORDS}",
                       headers={"X-Admin-Token": admin_token})
        assert code not in (401, 403)

    def test_safety_training_safety(self, portal_tokens):
        sf_tok = portal_tokens.get("safety", "")
        if not sf_tok:
            pytest.skip("no safety token")
        code, _ = _raw("GET", f"{BASE_URL}{SAFETY_TRAINING_RECORDS}",
                       headers={"X-Safety-Token": sf_tok})
        assert code not in (401, 403)

    def test_safety_training_hr(self, portal_tokens):
        hr_tok = portal_tokens.get("hr", "")
        if not hr_tok:
            pytest.skip("no hr token")
        code, _ = _raw("GET", f"{BASE_URL}{SAFETY_TRAINING_RECORDS}",
                       headers={"X-HR-Token": hr_tok})
        assert code not in (401, 403), (
            f"hr denied shared accountability surface: {code}"
        )


# ─── Source-level consolidation locks ────────────────────────────────

class TestHrConsolidationFoundation:
    """Lock the iter373 source-level consolidation shape."""

    def test_shared_factory_exists(self):
        src = Path("/app/backend/routes/hr_portal_deps.py").read_text()
        assert "def make_require_hr_user(" in src, (
            "shared HR factory must remain canonical source of truth"
        )
        assert '"_actor_kind": "hr_user"' in src, (
            "factory must return _actor_kind='hr_user'"
        )

    def test_hr_portal_delegates_to_factory(self):
        src = Path("/app/backend/routes/hr_portal.py").read_text()
        assert "make_require_hr_user(db)" in src, (
            "hr_portal.build_hr_portal_router must delegate to the shared factory"
        )
        # The closure body (with raise HTTPException) must be gone — it's
        # now in the factory only.
        idx = src.find("# ─── HR token resolver")
        assert idx >= 0
        # Take a small window after that marker.
        window = src[idx:idx + 600]
        assert "make_require_hr_user(db)" in window
        # No inline closure body remains in this region.
        assert "async def require_hr_user(" not in window, (
            "hr_portal must NOT re-define require_hr_user inline — "
            "must delegate to make_require_hr_user(db)"
        )

    def test_intentional_ambiguity_preserved_employee_lifecycle(self):
        """The `require_hr_or_admin` closure in employee_lifecycle.py
        is INTENTIONALLY DIFFERENT (filter-on-aggregator pattern) and
        MUST remain inline. Locks that we did not accidentally merge it."""
        src = Path("/app/backend/routes/employee_lifecycle.py").read_text()
        assert "async def require_hr_or_admin(" in src, (
            "employee_lifecycle.require_hr_or_admin closure must remain "
            "(intentional filter-on-aggregator pattern)"
        )
        # Locks the specific filter-on-aggregator pattern is intact.
        assert "require_any_portal_token" in src, (
            "employee_lifecycle.require_hr_or_admin must keep filtering "
            "from require_any_portal_token"
        )

    def test_intentional_ambiguity_preserved_field_leadership(self):
        """The `require_hr_or_admin` closure in field_leadership_portal.py
        is INTENTIONALLY DIFFERENT (direct token chain with admin_dep
        exception-swallow + HR fallback) and MUST remain inline."""
        src = Path("/app/backend/routes/field_leadership_portal.py").read_text()
        assert "async def require_hr_or_admin(" in src, (
            "field_leadership_portal.require_hr_or_admin closure must remain "
            "(intentional direct token chain with admin_dep fallback)"
        )
        # Locks the specific direct-check pattern is intact.
        assert "is_valid_hr_user_token_async" in src

    def test_safety_or_hr_or_admin_factory_still_canonical(self):
        """The shared HR/Safety/Admin factory in safety_portal/_deps.py
        is the single source of truth for cross-portal HR visibility
        and MUST remain untouched."""
        src = Path("/app/backend/routes/safety_portal/_deps.py").read_text()
        assert "def make_require_safety_or_hr_or_admin(" in src
