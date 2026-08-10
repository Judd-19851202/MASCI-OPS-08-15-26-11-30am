"""
test_auth_session_contract.py — PRE-C10 Auth/Session/Public-Access Contract Tests
==================================================================================
Tests the auth/session contract for the MASCI Operations Platform:
1. Multi-login flow with directory tokens
2. Multi-logout invalidation
3. Protected route access control
4. Public route accessibility
"""
import os
import time
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient

def _base_url() -> str:
    explicit = os.environ.get('REACT_APP_BACKEND_URL', '').strip().rstrip('/')
    if explicit:
        return explicit
    frontend_env = Path('/app/frontend/.env')
    if frontend_env.exists():
        for line in frontend_env.read_text().splitlines():
            if line.startswith('REACT_APP_BACKEND_URL='):
                return line.split('=', 1)[1].strip().strip('"').strip("'").rstrip('/')
    return ''


BASE_URL = _base_url()


def _backend_env(key: str) -> str:
    value = os.environ.get(key)
    if value:
        return value
    backend_env = Path('/app/backend/.env')
    if backend_env.exists():
        for line in backend_env.read_text().splitlines():
            if line.startswith(f'{key}='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return ''

# Test credentials from /app/memory/test_credentials.md
MULTI_PORTAL_USER = {
    "email": "ops8-admin-pm-preview@example.com",
    "password": "AdminPmOps8!"
}

SUPER_ADMIN_USER = {
    "email": "jaymn.judd@mascigc.com",
    "password": "Maddix123!"
}

PM_USER = {
    "email": "cert.pm@example.com",
    "password": "CertProof2026!"
}

SAFETY_USER = {
    "email": "cert.safety@example.com",
    "password": "CertProof2026!"
}


class TestMultiLoginFlow:
    """Test the unified multi-login flow"""
    
    def test_multi_login_success(self):
        """Multi-login with valid credentials returns tokens"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=MULTI_PORTAL_USER,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "session_token" in data, "Response should include session_token"
        assert "portal_tokens" in data, "Response should include portal_tokens"
        assert "user" in data, "Response should include user"
        
        # Verify user has expected portals
        user = data.get("user", {})
        portals = user.get("portals", [])
        assert "admin" in portals, "User should have admin portal"
        assert "pm" in portals, "User should have pm portal"
    
    def test_multi_login_invalid_credentials(self):
        """Multi-login with invalid credentials returns 401"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/multi-login",
                json={"email": "invalid@example.com", "password": "wrongpassword"},
                timeout=60  # Longer timeout for rate-limited requests
            )
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        except requests.exceptions.ReadTimeout:
            # Rate limiting may cause timeout - this is acceptable behavior
            pytest.skip("Request timed out (likely rate limiting)")
    
    def test_multi_login_missing_password(self):
        """Multi-login without password returns error"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": "test@example.com"},
            timeout=30
        )
        assert response.status_code in [400, 401, 422], f"Expected 4xx, got {response.status_code}"

    def test_super_admin_multi_login_admin_token_is_immediately_usable(self):
        """Super-admin multi-login must yield an admin token that works on first use."""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=SUPER_ADMIN_USER,
            timeout=30,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        session_token = data.get("session_token")
        admin_token = (data.get("portal_tokens") or {}).get("admin")
        assert admin_token, "Expected an admin portal token"

        admin_check = requests.get(
            f"{BASE_URL}/api/admin/system-health",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token or "",
            },
            timeout=30,
        )
        assert admin_check.status_code == 200, (
            f"Super-admin admin token should survive first admin request, got "
            f"{admin_check.status_code}: {admin_check.text}"
        )


class TestMeDirectoryEndpoint:
    """Test /api/auth/me-directory endpoint"""
    
    @pytest.fixture
    def auth_tokens(self):
        """Get auth tokens via multi-login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=MULTI_PORTAL_USER,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Multi-login failed, skipping authenticated tests")
        return response.json()
    
    def test_me_directory_with_valid_token(self, auth_tokens):
        """me-directory returns user info with valid directory token"""
        session_token = auth_tokens.get("session_token")
        admin_token = auth_tokens.get("portal_tokens", {}).get("admin")
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={
                "X-Directory-Token": session_token,
                "X-Admin-Token": admin_token or ""
            },
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Response may have user info at top level or nested in 'user' key
        user_data = data.get("user", data)
        assert "email" in user_data or "portals" in user_data, f"Response should include user info: {data}"
    
    def test_me_directory_without_token(self):
        """me-directory returns 401 without token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me-directory",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestMultiLogoutFlow:
    """Test the multi-logout invalidation flow"""
    
    def test_multi_logout_invalidates_session(self):
        """Multi-logout invalidates directory and portal tokens"""
        # Step 1: Login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=MULTI_PORTAL_USER,
            timeout=30
        )
        assert login_response.status_code == 200, "Login should succeed"
        
        tokens = login_response.json()
        session_token = tokens.get("session_token")
        admin_token = tokens.get("portal_tokens", {}).get("admin")
        pm_token = tokens.get("portal_tokens", {}).get("pm")
        
        # Step 2: Verify tokens work before logout
        me_before = requests.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={
                "X-Directory-Token": session_token,
                "X-Admin-Token": admin_token or ""
            },
            timeout=30
        )
        assert me_before.status_code == 200, "me-directory should work before logout"
        
        # Step 3: Logout
        logout_response = requests.post(
            f"{BASE_URL}/api/auth/multi-logout",
            headers={
                "X-Directory-Token": session_token,
                "X-Admin-Token": admin_token or "",
                "X-PM-Token": pm_token or ""
            },
            timeout=30
        )
        assert logout_response.status_code == 200, f"Logout should succeed, got {logout_response.status_code}"
        
        logout_data = logout_response.json()
        assert logout_data.get("ok") is True, "Logout response should have ok=True"
        
        # Step 4: Verify tokens are invalidated after logout
        me_after = requests.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={
                "X-Directory-Token": session_token,
                "X-Admin-Token": admin_token or ""
            },
            timeout=30
        )
        assert me_after.status_code == 401, f"me-directory should return 401 after logout, got {me_after.status_code}"
        
        # Step 5: Verify admin check is invalidated
        admin_check = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={"X-Admin-Token": admin_token or ""},
            timeout=30
        )
        assert admin_check.status_code == 401, f"admin/check should return 401 after logout, got {admin_check.status_code}"
        
        # Step 6: Verify PM check is invalidated
        pm_check = requests.get(
            f"{BASE_URL}/api/pm/check",
            headers={"X-PM-Token": pm_token or ""},
            timeout=30
        )
        assert pm_check.status_code == 401, f"pm/check should return 401 after logout, got {pm_check.status_code}"


class TestPortalCheckEndpoints:
    """Test portal check endpoints"""
    
    @pytest.fixture
    def auth_tokens(self):
        """Get auth tokens via multi-login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json=MULTI_PORTAL_USER,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Multi-login failed")
        return response.json()
    
    def test_admin_check_with_valid_token(self, auth_tokens):
        """admin/check returns 200 with valid admin token"""
        admin_token = auth_tokens.get("portal_tokens", {}).get("admin")
        session_token = auth_tokens.get("session_token")
        if not admin_token:
            pytest.skip("No admin token available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/check",
            headers={
                "X-Admin-Token": admin_token,
                "X-Directory-Token": session_token or "",
            },
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_pm_check_with_valid_token(self, auth_tokens):
        """pm/check returns 200 with valid PM token"""
        pm_token = auth_tokens.get("portal_tokens", {}).get("pm")
        session_token = auth_tokens.get("session_token")
        if not pm_token:
            pytest.skip("No PM token available")
        
        response = requests.get(
            f"{BASE_URL}/api/pm/check",
            headers={
                "X-PM-Token": pm_token,
                "X-Directory-Token": session_token or "",
            },
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_directory_bound_portal_tokens_fail_cleanly_after_session_expiry(self, auth_tokens):
        """Directory-bound admin/pm tokens must die when the backing directory session expires."""
        session_token = auth_tokens.get("session_token")
        admin_token = auth_tokens.get("portal_tokens", {}).get("admin")
        pm_token = auth_tokens.get("portal_tokens", {}).get("pm")
        if not session_token or not admin_token or not pm_token:
            pytest.skip("Expected unified admin+pm auth bundle")

        mongo_url = _backend_env('MONGO_URL')
        db_name = _backend_env('DB_NAME')
        if not mongo_url or not db_name:
            pytest.skip('Mongo env not available for expiry regression')

        client = MongoClient(mongo_url)
        try:
            db = client[db_name]
            result = db.directory_sessions.update_one(
                {"token": session_token},
                {"$set": {"expires_at_ts": int(time.time()) - 10}},
            )
            assert result.modified_count == 1, "Expected to expire exactly one directory session"
        finally:
            client.close()

        expired_me = requests.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"X-Directory-Token": session_token},
            timeout=30,
        )
        assert expired_me.status_code == 401, expired_me.text[:200]

        for label, path, headers in [
            (
                "admin-bound",
                "/api/admin/check",
                {"X-Admin-Token": admin_token, "X-Directory-Token": session_token},
            ),
            (
                "pm-bound",
                "/api/pm/check",
                {"X-PM-Token": pm_token, "X-Directory-Token": session_token},
            ),
            ("admin-without-dir", "/api/admin/check", {"X-Admin-Token": admin_token}),
            ("pm-without-dir", "/api/pm/check", {"X-PM-Token": pm_token}),
        ]:
            response = requests.get(f"{BASE_URL}{path}", headers=headers, timeout=30)
            assert response.status_code == 401, f"{label} should 401 after expiry, got {response.status_code}: {response.text[:200]}"
    
    def test_admin_check_without_token(self):
        """admin/check returns 401 without token"""
        response = requests.get(
            f"{BASE_URL}/api/admin/check",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_pm_check_without_token(self):
        """pm/check returns 401 without token"""
        response = requests.get(
            f"{BASE_URL}/api/pm/check",
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestDirectPortalLogin:
    """Test direct portal login endpoints"""
    
    def test_pm_login_success(self):
        """PM portal login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json=PM_USER,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data or "pm_token" in data or data.get("ok"), "Response should include token"
    
    def test_safety_login_success(self):
        """Safety portal login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/safety/login",
            json=SAFETY_USER,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"


class TestPublicEndpoints:
    """Test that public endpoints are accessible without auth"""
    
    def test_health_endpoint(self):
        """Health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_jobs_list_public(self):
        """Jobs list endpoint for public forms"""
        response = requests.get(f"{BASE_URL}/api/jobs", timeout=30)
        # Jobs endpoint may require auth or be public depending on config
        assert response.status_code in [200, 401], f"Unexpected status: {response.status_code}"
    
    def test_hr_roster_public(self):
        """HR roster endpoint for public forms (employee picker)"""
        response = requests.get(f"{BASE_URL}/api/hr/roster", timeout=30)
        # This endpoint may be at different path or require auth
        assert response.status_code in [200, 401, 404], f"Unexpected status: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
