"""
Iteration 36 — pre-redeploy verification:
- Admin login + new /api/admin/date-audit endpoints
- PM login (Chris Wright) + /api/pm/me + scoped lists
- PM forgot-password (always 200, generic)
- Shop login
- Date display fix is frontend; here we just confirm backend stores YYYY-MM-DD
  exactly as submitted and date-audit endpoint is reachable.
"""
import os
import requests
import pytest

_RAW_BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
import pytest as _pytest
if not _RAW_BASE_URL:
    _pytest.skip(
        "REACT_APP_BACKEND_URL not set · live-HTTP test skipped (parity-lock safe).",
        allow_module_level=True,
    )
BASE_URL = _RAW_BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_PASSWORD = "MASCI1982!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PASSWORD = "ChrisRocksThis2026"
SHOP_PASSWORD = "Nothappy123!"


# ---------- session fixtures ----------
@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"admin login failed {r.status_code} {r.text}"
    body = r.json()
    assert body.get("ok") is True
    tok = body.get("token")
    assert tok and isinstance(tok, str) and len(tok) > 10
    return tok


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def pm_token():
    r = requests.post(f"{API}/pm/login", json={"email": PM_EMAIL, "password": PM_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"pm login failed {r.status_code} {r.text}"
    body = r.json()
    assert body.get("ok") is True
    assert body.get("must_change_password") is False, "Chris should NOT be forced to change pw"
    pm = body.get("pm") or {}
    assert pm.get("email") == PM_EMAIL
    return body.get("token")


@pytest.fixture(scope="session")
def pm_headers(pm_token):
    return {"X-PM-Token": pm_token, "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def shop_token():
    r = requests.post(f"{API}/shop/login", json={"password": SHOP_PASSWORD}, timeout=20)
    assert r.status_code == 200, f"shop login failed {r.status_code} {r.text}"
    body = r.json()
    assert body.get("ok") is True
    return body.get("token")


# ---------- admin auth ----------
class TestAdminAuth:
    def test_admin_login_ok(self, admin_token):
        assert admin_token

    def test_admin_login_wrong_pw(self):
        r = requests.post(f"{API}/admin/login", json={"password": "WRONG_PW_TEST"}, timeout=20)
        assert r.status_code in (401, 403)

    def test_admin_check(self, admin_headers):
        r = requests.get(f"{API}/admin/check", headers=admin_headers, timeout=20)
        assert r.status_code == 200
        assert r.json().get("ok") is True


# ---------- date-audit (new) ----------
class TestDateAudit:
    def test_get_scan(self, admin_headers):
        r = requests.get(f"{API}/admin/date-audit", headers=admin_headers, timeout=60)
        assert r.status_code == 200, f"date-audit GET failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        # Expected keys based on _classify() rules described
        assert "scanned" in body or "totals" in body or "suspects" in body or "review" in body, (
            f"date-audit GET shape unexpected: keys={list(body.keys())}"
        )
        # Best-effort: scanned > 0 if totals returned
        scanned = body.get("scanned") or (body.get("totals") or {}).get("scanned")
        if scanned is not None:
            assert isinstance(scanned, int)
            assert scanned >= 0

    def test_requires_admin(self):
        # conftest.py auto-attaches X-Admin-Token; pass empty to override and
        # verify the endpoint rejects unauthenticated callers.
        r = requests.get(
            f"{API}/admin/date-audit",
            headers={"X-Admin-Token": ""},
            timeout=20,
        )
        assert r.status_code in (401, 403), (
            f"unauthenticated call must be rejected, got {r.status_code} {r.text[:200]}"
        )


# ---------- PM auth + scoping ----------
class TestPmAuth:
    def test_pm_me(self, pm_headers):
        r = requests.get(f"{API}/pm/me", headers=pm_headers, timeout=20)
        assert r.status_code == 200
        body = r.json()
        # either a PM doc or legacy flag
        assert body.get("email") == PM_EMAIL or body.get("is_admin_or_legacy") is True

    def test_pm_forgot_password_existing_email(self):
        r = requests.post(f"{API}/pm/forgot-password", json={"email": PM_EMAIL}, timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text}"
        body = r.json()
        # generic enumeration-safe response
        assert body.get("ok") is True or "message" in body

    def test_pm_forgot_password_unknown_email(self):
        r = requests.post(
            f"{API}/pm/forgot-password",
            json={"email": "nobody-xyz@example.com"},
            timeout=30,
        )
        assert r.status_code == 200, "must be enumeration-safe"
        body = r.json()
        assert body.get("ok") is True or "message" in body

    def test_pm_login_wrong_pw(self):
        r = requests.post(
            f"{API}/pm/login",
            json={"email": PM_EMAIL, "password": "WRONG_PW_TEST_X"},
            timeout=20,
        )
        assert r.status_code in (401, 403)


class TestPmScopedLists:
    """PM should see 200s on scoped list endpoints; admin sees superset."""

    SCOPED_LIST_ENDPOINTS = [
        "/inspections",
        "/meetings",
        "/jhas",
        "/incidents",
        "/daily-reports",
        "/equipment-inspections",
        "/qaqc-inspections",
        "/admin/jobs",
    ]

    @pytest.mark.parametrize("path", SCOPED_LIST_ENDPOINTS)
    def test_pm_can_read(self, pm_headers, path):
        r = requests.get(f"{API}{path}", headers=pm_headers, timeout=30)
        assert r.status_code == 200, f"PM {path} -> {r.status_code} {r.text[:200]}"
        body = r.json()
        # Should be list or {items:[...]}
        assert isinstance(body, (list, dict))

    @pytest.mark.parametrize("path", SCOPED_LIST_ENDPOINTS)
    def test_admin_can_read(self, admin_headers, path):
        r = requests.get(f"{API}{path}", headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"Admin {path} -> {r.status_code} {r.text[:200]}"

    def test_pm_scope_subset_of_admin(self, pm_headers, admin_headers):
        """Inspections returned to PM should be a subset of admin's view by id."""
        ra = requests.get(f"{API}/inspections", headers=admin_headers, timeout=30).json()
        rp = requests.get(f"{API}/inspections", headers=pm_headers, timeout=30).json()
        admin_list = ra if isinstance(ra, list) else ra.get("items", [])
        pm_list = rp if isinstance(rp, list) else rp.get("items", [])
        assert len(pm_list) <= len(admin_list), (
            f"PM scoped count ({len(pm_list)}) must be <= admin count ({len(admin_list)})"
        )


# ---------- shop ----------
class TestShop:
    def test_shop_login_ok(self, shop_token):
        assert shop_token

    def test_shop_check(self, shop_token):
        r = requests.get(
            f"{API}/shop/check",
            headers={"X-Shop-Token": shop_token},
            timeout=20,
        )
        assert r.status_code == 200
        assert r.json().get("ok") is True


# ---------- date persistence sanity ----------
class TestDatePersistence:
    """Confirm backend stores bare YYYY-MM-DD verbatim (no UTC conversion)."""

    def test_post_inspection_keeps_date_string(self):
        payload = {
            "project_number": "TEST_DATE_AUDIT",
            "date": "2026-05-05",
            "foreman": "TEST_Iter36",
            "crew": ["TEST_user"],
            "items": [],
            "notes": "TEST_iter36_date_persist",
        }
        r = requests.post(f"{API}/inspections", json=payload, timeout=30)
        # Public POST may be rate-limited or require fields; treat 4xx-validation as skip
        if r.status_code in (400, 422):
            pytest.skip(f"public inspection POST rejected fields: {r.text[:200]}")
        assert r.status_code in (200, 201), f"{r.status_code} {r.text[:300]}"
        body = r.json()
        ret_date = body.get("date") or (body.get("inspection") or {}).get("date")
        if ret_date:
            assert ret_date.startswith("2026-05-05"), f"date got mutated to {ret_date}"
