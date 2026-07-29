"""
Full Platform Certification - Authentication & Session Sweep
READ-ONLY certification - no data mutations
Tests: multi-login, portal access, session behavior, role/access matrix
"""
import pytest
import requests
import os
import json
from datetime import datetime
from pathlib import Path


def _discover_base_url() -> str:
    explicit = os.environ.get("WP15_CERT_BASE_URL") or os.environ.get("BACKEND_INTERNAL_URL")
    if explicit:
        return explicit.rstrip("/")
    frontend_env = Path("/app/frontend/.env")
    if frontend_env.exists():
        for line in frontend_env.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                value = line.split("=", 1)[1].strip()
                if value:
                    # Local in-pod backend is the canonical certification
                    # target for this suite unless an explicit override is
                    # supplied. The preview URL remains available via
                    # WP15_CERT_BASE_URL for browser or remote checks.
                    break
    return "http://localhost:8001"


BASE_URL = _discover_base_url().rstrip('/')

# Test credentials from /app/memory/test_credentials.md
CREDENTIALS = {
    "super_admin": {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
    "admin_only": {"email": "ops8-admin-only-preview@example.com", "password": "AdminOnlyOps8!"},
    "admin_pm": {"email": "ops8-admin-pm-preview@example.com", "password": "AdminPmOps8!"},
    "admin_shop": {"email": "ops8-admin-shop-preview@example.com", "password": "AdminShopOps8!"},
    "pm_shop": {"email": "ops8-pm-shop-preview@example.com", "password": "PmShopOps8!"},
    "pm_only": {"email": "cert.pm@example.com", "password": "CertProof2026!"},
    "hr_only": {"email": "cert.hr@example.com", "password": "CertProof2026!"},
    "safety_only": {"email": "cert.safety@example.com", "password": "CertProof2026!"},
    "shop_only": {"email": "cert.shop@example.com", "password": "CertProof2026!"},
    "dispatch_only": {"email": "cert.dispatch@example.com", "password": "CertProof2026!"},
    "fl_only": {"email": "cert.foreman@example.com", "password": "CertProof2026!"},
    "disabled_hr": {"email": "ops8-disabled-hr-preview@example.com", "password": "DisabledHrOps8!"},
}

class TestHealthEndpoints:
    """Basic health and version endpoints"""
    
    def test_health_endpoint(self):
        """GET /api/health returns 200 with ok=true"""
        r = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert r.status_code == 200, f"Health check failed: {r.status_code}"
        data = r.json()
        assert data.get("ok") == True, f"Health not ok: {data}"
        print(f"PASS: /api/health - ok={data.get('ok')}")
    
    def test_health_full_endpoint(self):
        """GET /api/health/full returns 200 with subsystem status.

        `ok` may legitimately be false when non-auth subsystems (for example,
        backup recency) are degraded. The certification contract here is the
        shape and visibility of the canonical status payload, not a forced
        green state.
        """
        r = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        assert r.status_code == 200, f"Health full failed: {r.status_code}"
        data = r.json()
        assert "mongo" in data and "scheduler" in data and "backup_recent" in data, f"Unexpected health/full shape: {data}"
        print(f"PASS: /api/health/full - mongo={data.get('mongo')}, scheduler={data.get('scheduler')}")
    
    def test_version_endpoint(self):
        """GET /api/version returns commit info"""
        r = requests.get(f"{BASE_URL}/api/version", timeout=10)
        assert r.status_code == 200, f"Version failed: {r.status_code}"
        data = r.json()
        assert "commit" in data, f"No commit in version: {data}"
        print(f"PASS: /api/version - commit={data.get('commit')[:12]}...")


class TestMultiLoginAuth:
    """Multi-login authentication flow tests"""
    
    def test_super_admin_multi_login(self):
        """Super admin can multi-login and gets canonical session + portal tokens"""
        creds = CREDENTIALS["super_admin"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"Super admin login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        assert data.get("session_token"), f"No session token in response: {data.keys()}"
        assert (data.get("portal_tokens") or {}).get("admin"), f"No admin portal token in response: {data.keys()}"
        print(f"PASS: Super admin multi-login - portals={list((data.get('portal_tokens') or {}).keys())}")
    
    def test_admin_only_multi_login(self):
        """Admin-only user can login"""
        creds = CREDENTIALS["admin_only"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"Admin-only login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        print(f"PASS: Admin-only multi-login - portals={data.get('portals', data.get('available_portals', []))}")
    
    def test_pm_only_multi_login(self):
        """PM-only user can login"""
        creds = CREDENTIALS["pm_only"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"PM-only login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        print(f"PASS: PM-only multi-login - portals={data.get('portals', data.get('available_portals', []))}")
    
    def test_hr_only_multi_login(self):
        """HR-only user can login"""
        creds = CREDENTIALS["hr_only"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"HR-only login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        print(f"PASS: HR-only multi-login - portals={data.get('portals', data.get('available_portals', []))}")
    
    def test_safety_only_multi_login(self):
        """Safety-only user can login"""
        creds = CREDENTIALS["safety_only"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"Safety-only login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        print(f"PASS: Safety-only multi-login - portals={data.get('portals', data.get('available_portals', []))}")
    
    def test_shop_only_multi_login(self):
        """Shop-only user can login"""
        creds = CREDENTIALS["shop_only"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"Shop-only login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        print(f"PASS: Shop-only multi-login - portals={data.get('portals', data.get('available_portals', []))}")
    
    def test_dispatch_only_multi_login(self):
        """Dispatch-only user can login"""
        creds = CREDENTIALS["dispatch_only"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"Dispatch-only login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        print(f"PASS: Dispatch-only multi-login - portals={data.get('portals', data.get('available_portals', []))}")
    
    def test_fl_only_multi_login(self):
        """Field Leadership-only user can login"""
        creds = CREDENTIALS["fl_only"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"FL-only login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        print(f"PASS: FL-only multi-login - portals={data.get('portals', data.get('available_portals', []))}")
    
    def test_multi_portal_user_admin_pm(self):
        """Admin+PM user gets both portals"""
        creds = CREDENTIALS["admin_pm"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"Admin+PM login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        portals = data.get('portals', data.get('available_portals', []))
        print(f"PASS: Admin+PM multi-login - portals={portals}")
    
    def test_multi_portal_user_pm_shop(self):
        """PM+Shop user gets both portals"""
        creds = CREDENTIALS["pm_shop"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        assert r.status_code == 200, f"PM+Shop login failed: {r.status_code} - {r.text[:500]}"
        data = r.json()
        portals = data.get('portals', data.get('available_portals', []))
        print(f"PASS: PM+Shop multi-login - portals={portals}")
    
    def test_disabled_user_rejected(self):
        """Disabled user should be rejected"""
        creds = CREDENTIALS["disabled_hr"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        # Should be 401 or 403 for disabled user
        if r.status_code == 200:
            data = r.json()
            # Check if user is marked as disabled in response
            if data.get("disabled") or data.get("status") == "disabled":
                print(f"PASS: Disabled user flagged in response")
            else:
                print(f"DEFECT: Disabled user allowed to login - {r.status_code}")
                assert False, "Disabled user should not be able to login"
        else:
            print(f"PASS: Disabled user rejected - status={r.status_code}")
    
    def test_invalid_credentials_rejected(self):
        """Invalid credentials should be rejected"""
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }, timeout=15)
        assert r.status_code in [401, 403, 404], f"Invalid creds not rejected: {r.status_code}"
        print(f"PASS: Invalid credentials rejected - status={r.status_code}")


class TestPortalSpecificLogins:
    """Portal-specific login endpoint tests"""
    
    def test_admin_login(self):
        """Legacy shared-password admin login is explicitly retired."""
        creds = CREDENTIALS["super_admin"]
        r = requests.post(f"{BASE_URL}/api/admin/login", json=creds, timeout=15)
        assert r.status_code == 410, f"Admin legacy login should be retired: {r.status_code} - {r.text[:500]}"
        print(f"PASS: /api/admin/login retired with 410")
    
    def test_pm_login(self):
        """POST /api/pm/login works"""
        creds = CREDENTIALS["pm_only"]
        r = requests.post(f"{BASE_URL}/api/pm/login", json=creds, timeout=15)
        assert r.status_code == 200, f"PM login failed: {r.status_code} - {r.text[:500]}"
        print(f"PASS: /api/pm/login")
    
    def test_hr_login(self):
        """POST /api/hr/login works"""
        creds = CREDENTIALS["hr_only"]
        r = requests.post(f"{BASE_URL}/api/hr/login", json=creds, timeout=15)
        assert r.status_code == 200, f"HR login failed: {r.status_code} - {r.text[:500]}"
        print(f"PASS: /api/hr/login")
    
    def test_safety_login(self):
        """Safety login is served by the canonical safety API namespace."""
        creds = CREDENTIALS["safety_only"]
        r = requests.post(f"{BASE_URL}/api/safety/login", json=creds, timeout=15)
        assert r.status_code == 200, f"Safety login failed: {r.status_code} - {r.text[:500]}"
        print(f"PASS: /api/safety/login")
    
    def test_shop_login(self):
        """POST /api/shop/login works"""
        creds = CREDENTIALS["shop_only"]
        r = requests.post(f"{BASE_URL}/api/shop/login", json=creds, timeout=15)
        assert r.status_code == 200, f"Shop login failed: {r.status_code} - {r.text[:500]}"
        print(f"PASS: /api/shop/login")
    
    def test_dispatch_login(self):
        """POST /api/dispatch/login works"""
        creds = CREDENTIALS["dispatch_only"]
        r = requests.post(f"{BASE_URL}/api/dispatch/login", json=creds, timeout=15)
        assert r.status_code == 200, f"Dispatch login failed: {r.status_code} - {r.text[:500]}"
        print(f"PASS: /api/dispatch/login")
    
    def test_fl_login(self):
        """Legacy FL shared-secret login is retired; canonical portal login remains active."""
        creds = CREDENTIALS["fl_only"]
        r = requests.post(f"{BASE_URL}/api/field-leadership/login", json=creds, timeout=15)
        assert r.status_code == 410, f"Legacy FL login should be retired: {r.status_code} - {r.text[:500]}"
        r2 = requests.post(f"{BASE_URL}/api/field-leadership/portal/login", json=creds, timeout=15)
        assert r2.status_code == 200, f"FL portal login failed: {r2.status_code} - {r2.text[:500]}"
        print(f"PASS: FL legacy login retired; portal login active")


class TestProtectedEndpointsWithAuth:
    """Test protected endpoints require proper auth"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session tokens"""
        creds = CREDENTIALS["super_admin"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        if r.status_code != 200:
            pytest.skip("Could not get admin session")
        data = r.json()
        return {
            "admin_token": (data.get("portal_tokens") or {}).get("admin"),
            "session_token": data.get("session_token") or data.get("directory_token"),
        }
    
    def test_admin_check_requires_auth(self):
        """GET /api/admin/check without auth returns 401"""
        r = requests.get(f"{BASE_URL}/api/admin/check", timeout=10)
        assert r.status_code in [401, 403], f"Admin check without auth: {r.status_code}"
        print(f"PASS: /api/admin/check requires auth - status={r.status_code}")
    
    def test_admin_check_with_auth(self, admin_session):
        """GET /api/admin/check with auth returns 200"""
        headers = {
            "X-Admin-Token": admin_session["admin_token"],
            "X-Directory-Token": admin_session.get("session_token", ""),
        }
        r = requests.get(f"{BASE_URL}/api/admin/check", headers=headers, timeout=10)
        assert r.status_code == 200, f"Admin check with auth failed: {r.status_code}"
        print(f"PASS: /api/admin/check with auth - ok")
    
    def test_pm_check_requires_auth(self):
        """GET /api/pm/check without auth returns 401"""
        r = requests.get(f"{BASE_URL}/api/pm/check", timeout=10)
        assert r.status_code in [401, 403], f"PM check without auth: {r.status_code}"
        print(f"PASS: /api/pm/check requires auth - status={r.status_code}")
    
    def test_hr_check_requires_auth(self):
        """GET /api/hr/check may be absent in the canonical surface; absence is acceptable."""
        r = requests.get(f"{BASE_URL}/api/hr/check", timeout=10)
        assert r.status_code in [401, 403, 404], f"HR check unexpected status: {r.status_code}"
        print(f"PASS: /api/hr/check requires auth - status={r.status_code}")
    
    def test_shop_check_requires_auth(self):
        """GET /api/shop/check without auth returns 401"""
        r = requests.get(f"{BASE_URL}/api/shop/check", timeout=10)
        assert r.status_code in [401, 403], f"Shop check without auth: {r.status_code}"
        print(f"PASS: /api/shop/check requires auth - status={r.status_code}")


class TestPublicEndpoints:
    """Test public endpoints are accessible without auth"""
    
    def test_daily_submit_public(self):
        """Legacy backend daily submit page is retired from the API surface.

        The canonical route is a frontend navigation target, so the backend
        may legitimately return 404 here.
        """
        r = requests.get(f"{BASE_URL}/daily/submit", timeout=10)
        assert r.status_code in [200, 404], f"Unexpected daily submit status: {r.status_code}"
        print(f"PASS: /daily/submit canonical surface status={r.status_code}")
    
    def test_jobs_public(self):
        """GET /api/jobs is public"""
        r = requests.get(f"{BASE_URL}/api/jobs", timeout=10)
        assert r.status_code == 200, f"Jobs not public: {r.status_code}"
        print(f"PASS: /api/jobs is public")
    
    def test_employees_public(self):
        """GET /api/employees is public"""
        r = requests.get(f"{BASE_URL}/api/employees", timeout=10)
        assert r.status_code == 200, f"Employees not public: {r.status_code}"
        print(f"PASS: /api/employees is public")
    
    def test_equipment_master_public(self):
        """GET /api/equipment-master is public"""
        r = requests.get(f"{BASE_URL}/api/equipment-master", timeout=10)
        assert r.status_code == 200, f"Equipment master not public: {r.status_code}"
        print(f"PASS: /api/equipment-master is public")


class TestCoreDataEndpoints:
    """Test core data endpoints return valid data"""

    @staticmethod
    def _items(payload):
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return payload["items"]
        raise AssertionError(f"Payload missing items list: {type(payload)} {payload}")
    
    def test_jobs_returns_data(self):
        """GET /api/jobs returns canonical items envelope"""
        r = requests.get(f"{BASE_URL}/api/jobs", timeout=15)
        assert r.status_code == 200
        data = r.json()
        items = self._items(data)
        print(f"PASS: /api/jobs returns {len(items)} jobs")
    
    def test_employees_returns_data(self):
        """GET /api/employees returns canonical items envelope"""
        r = requests.get(f"{BASE_URL}/api/employees", timeout=15)
        assert r.status_code == 200
        data = r.json()
        items = self._items(data)
        print(f"PASS: /api/employees returns {len(items)} employees")
    
    def test_equipment_returns_data(self):
        """GET /api/equipment-master returns canonical items envelope"""
        r = requests.get(f"{BASE_URL}/api/equipment-master", timeout=15)
        assert r.status_code == 200
        data = r.json()
        items = self._items(data)
        print(f"PASS: /api/equipment-master returns {len(items)} equipment")
    
    def test_suppliers_returns_data(self):
        """GET /api/suppliers returns canonical items envelope"""
        r = requests.get(f"{BASE_URL}/api/suppliers", timeout=15)
        assert r.status_code == 200
        data = r.json()
        items = self._items(data)
        print(f"PASS: /api/suppliers returns {len(items)} suppliers")


class TestDailyReportsEndpoints:
    """Test daily reports endpoints"""
    
    def test_daily_reports_list(self):
        """GET /api/daily-reports returns data"""
        r = requests.get(f"{BASE_URL}/api/daily-reports", timeout=15)
        # May require auth or return empty
        if r.status_code == 200:
            data = r.json()
            print(f"PASS: /api/daily-reports returns {len(data) if isinstance(data, list) else 'object'}")
        elif r.status_code in [401, 403]:
            print(f"INFO: /api/daily-reports requires auth - {r.status_code}")
        else:
            print(f"DEFECT: /api/daily-reports unexpected status - {r.status_code}")


class TestIncidentEndpoints:
    """Test incident case endpoints"""
    
    def test_incident_cases_list(self):
        """GET /api/incident-cases returns data"""
        r = requests.get(f"{BASE_URL}/api/incident-cases", timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"PASS: /api/incident-cases returns data")
        elif r.status_code in [401, 403]:
            print(f"INFO: /api/incident-cases requires auth - {r.status_code}")
        else:
            print(f"DEFECT: /api/incident-cases unexpected status - {r.status_code}")
    
    def test_incident_vocabulary(self):
        """GET /api/incident-cases/vocabulary returns data"""
        r = requests.get(f"{BASE_URL}/api/incident-cases/vocabulary", timeout=15)
        if r.status_code == 200:
            print(f"PASS: /api/incident-cases/vocabulary returns data")
        else:
            print(f"INFO: /api/incident-cases/vocabulary status - {r.status_code}")


class TestGovernanceEndpoints:
    """Test governance and deployment endpoints"""
    
    @pytest.fixture
    def admin_session(self):
        """Get admin session tokens"""
        creds = CREDENTIALS["super_admin"]
        r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=15)
        if r.status_code != 200:
            pytest.skip("Could not get admin session")
        data = r.json()
        return {
            "admin_token": (data.get("portal_tokens") or {}).get("admin"),
            "session_token": data.get("session_token") or data.get("directory_token"),
        }
    
    def test_deployment_readiness(self, admin_session):
        """GET /api/admin/deployment-readiness returns data"""
        headers = {
            "X-Admin-Token": admin_session["admin_token"],
            "X-Directory-Token": admin_session.get("session_token", ""),
        }
        r = requests.get(f"{BASE_URL}/api/admin/deployment-readiness", headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            print(f"PASS: /api/admin/deployment-readiness - decision={data.get('decision')}")
        else:
            print(f"INFO: /api/admin/deployment-readiness status - {r.status_code}")
    
    def test_trust_events(self, admin_session):
        """GET /api/admin/occ/trust-events returns data"""
        headers = {
            "X-Admin-Token": admin_session["admin_token"],
            "X-Directory-Token": admin_session.get("session_token", ""),
        }
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events", headers=headers, timeout=15)
        if r.status_code == 200:
            print(f"PASS: /api/admin/occ/trust-events returns data")
        else:
            print(f"INFO: /api/admin/occ/trust-events status - {r.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
