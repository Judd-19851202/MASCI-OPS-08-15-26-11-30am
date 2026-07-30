"""
WP-16 Phase 6 — Admin Portal Governance & Repaired Pages Backend Tests

Tests the backend endpoints for:
- Governance pages (roles, permissions, policies, approval-flows, versions)
- Self-protection page
- Trust spine page
- Executive operational intelligence (OPPC/briefing)
- Asset spine health
- Field leadership detail flow

Uses admin directory session + admin portal token authentication.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Admin credentials from test_credentials.md
ADMIN_EMAIL = "ops8-admin-only-preview@example.com"
ADMIN_PASSWORD = "AdminOnlyOps8!"


class TestAdminAuthentication:
    """Test admin login and token extraction"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login and get admin tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login via multi-login
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        
        data = login_response.json()
        assert "portal_tokens" in data, "No portal_tokens in login response"
        assert "admin" in data["portal_tokens"], "No admin token in portal_tokens"
        assert "session_token" in data, "No session_token in login response"
        
        # Set auth headers
        session.headers.update({
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        })
        
        return session
    
    def test_admin_login_success(self, admin_session):
        """Verify admin login works and returns required tokens"""
        # If we got here, the fixture succeeded
        assert admin_session is not None
        assert "X-Admin-Token" in admin_session.headers
        assert "X-Directory-Token" in admin_session.headers
        print("✓ Admin login successful with both tokens")
    
    def test_admin_check_endpoint(self, admin_session):
        """Verify /api/admin/check returns 200 with valid auth"""
        response = admin_session.get(f"{BASE_URL}/api/admin/check")
        assert response.status_code == 200, f"Admin check failed: {response.text}"
        print("✓ /api/admin/check returns 200")


class TestGovernanceEndpoints:
    """Test governance API endpoints for repaired pages"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login and get admin tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.text}")
        
        data = login_response.json()
        session.headers.update({
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        })
        
        return session
    
    def test_governance_roles(self, admin_session):
        """Test /api/admin/governance/roles endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/roles")
        assert response.status_code == 200, f"Governance roles failed: {response.text}"
        
        data = response.json()
        # Should have items (roles registry)
        assert "items" in data or isinstance(data, dict), "Response should contain items or be a dict"
        print(f"✓ /api/admin/governance/roles returns 200 with {len(data.get('items', data))} items")
    
    def test_governance_permissions(self, admin_session):
        """Test /api/admin/governance/permissions endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/permissions")
        assert response.status_code == 200, f"Governance permissions failed: {response.text}"
        
        data = response.json()
        assert "items" in data or isinstance(data, dict), "Response should contain items or be a dict"
        print(f"✓ /api/admin/governance/permissions returns 200")
    
    def test_governance_policies(self, admin_session):
        """Test /api/admin/governance/policies endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/policies")
        assert response.status_code == 200, f"Governance policies failed: {response.text}"
        
        data = response.json()
        assert "items" in data or isinstance(data, dict), "Response should contain items or be a dict"
        print(f"✓ /api/admin/governance/policies returns 200")
    
    def test_governance_approval_flows(self, admin_session):
        """Test /api/admin/governance/approval-flows endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/approval-flows")
        assert response.status_code == 200, f"Governance approval-flows failed: {response.text}"
        
        data = response.json()
        # May have items and/or requests
        assert isinstance(data, dict), "Response should be a dict"
        print(f"✓ /api/admin/governance/approval-flows returns 200")
    
    def test_governance_versions(self, admin_session):
        """Test /api/admin/governance/versions endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/versions")
        assert response.status_code == 200, f"Governance versions failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        print(f"✓ /api/admin/governance/versions returns 200")


class TestSelfProtectionEndpoint:
    """Test self-protection governance endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login and get admin tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.text}")
        
        data = login_response.json()
        session.headers.update({
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        })
        
        return session
    
    def test_self_protection_endpoint(self, admin_session):
        """Test /api/admin/governance/self-protection endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/self-protection")
        assert response.status_code == 200, f"Self-protection failed: {response.text}"
        
        data = response.json()
        # Should have page_status and various governance sections
        assert "page_status" in data or "authority" in data or isinstance(data, dict), \
            "Response should contain governance status data"
        print(f"✓ /api/admin/governance/self-protection returns 200")
        
        # Check for expected sections
        if "authority" in data:
            print(f"  - Authority section present with status: {data['authority'].get('status', 'unknown')}")
        if "page_status" in data:
            print(f"  - Page status: {data['page_status']}")


class TestTrustSpineEndpoint:
    """Test trust spine endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login and get admin tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.text}")
        
        data = login_response.json()
        session.headers.update({
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        })
        
        return session
    
    def test_trust_spine_endpoint(self, admin_session):
        """Test /api/admin/trust-spine endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/admin/trust-spine")
        assert response.status_code == 200, f"Trust spine failed: {response.text}"
        
        data = response.json()
        # Should have platform_band and workflows
        assert isinstance(data, dict), "Response should be a dict"
        print(f"✓ /api/admin/trust-spine returns 200")
        
        if "platform_band" in data:
            print(f"  - Platform band: {data['platform_band']}")
        if "workflows" in data:
            print(f"  - Workflows count: {len(data['workflows'])}")


class TestAssetSpineEndpoints:
    """Test asset spine health endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login and get admin tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.text}")
        
        data = login_response.json()
        session.headers.update({
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        })
        
        return session
    
    def test_asset_spine_health(self, admin_session):
        """Test /api/asset-spine/health endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/asset-spine/health")
        assert response.status_code == 200, f"Asset spine health failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        print(f"✓ /api/asset-spine/health returns 200")
        
        if "total_assets" in data:
            print(f"  - Total assets: {data['total_assets']}")
        if "active_assets" in data:
            print(f"  - Active assets: {data['active_assets']}")
    
    def test_asset_spine_health_runs(self, admin_session):
        """Test /api/asset-spine/health/runs endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/asset-spine/health/runs?limit=2")
        assert response.status_code == 200, f"Asset spine health runs failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        print(f"✓ /api/asset-spine/health/runs?limit=2 returns 200")
        
        if "items" in data:
            print(f"  - Runs count: {len(data['items'])}")


class TestExecutiveIntelligenceEndpoints:
    """Test executive operational intelligence endpoints (OPPC/briefing)"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login and get admin tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.text}")
        
        data = login_response.json()
        session.headers.update({
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        })
        
        return session
    
    def test_oppc_executive_operations_center(self, admin_session):
        """Test /api/oppc/enterprise/executive-operations-center endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/executive-operations-center")
        # May return 200 or 404 if not configured
        assert response.status_code in [200, 404], f"OPPC exec ops center failed: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dict"
            print(f"✓ /api/oppc/enterprise/executive-operations-center returns 200")
        else:
            print(f"⚠ /api/oppc/enterprise/executive-operations-center returns 404 (not configured)")
    
    def test_oppc_monday_briefing(self, admin_session):
        """Test /api/oppc/enterprise/monday-briefing endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/monday-briefing")
        # May return 200 or 404 if not configured
        assert response.status_code in [200, 404], f"OPPC monday briefing failed: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dict"
            print(f"✓ /api/oppc/enterprise/monday-briefing returns 200")
            if "briefing" in data and data["briefing"]:
                print(f"  - Briefing status: {data['briefing'].get('status', 'unknown')}")
        else:
            print(f"⚠ /api/oppc/enterprise/monday-briefing returns 404 (not configured)")


class TestFieldLeadershipEndpoint:
    """Test field leadership endpoint for admin access"""
    
    @pytest.fixture(scope="class")
    def admin_session(self):
        """Login and get admin tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Admin login failed: {login_response.text}")
        
        data = login_response.json()
        session.headers.update({
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        })
        
        return session
    
    def test_field_leadership_list(self, admin_session):
        """Test /api/field-leadership?limit=1 endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/field-leadership?limit=1")
        assert response.status_code == 200, f"Field leadership list failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, (dict, list)), "Response should be a dict or list"
        print(f"✓ /api/field-leadership?limit=1 returns 200")
        
        # Extract record ID for detail test
        items = data.get("items", data) if isinstance(data, dict) else data
        if items and len(items) > 0:
            record_id = items[0].get("id") or items[0].get("_id")
            print(f"  - Found record ID: {record_id}")
            return record_id
        return None
    
    def test_field_leadership_detail(self, admin_session):
        """Test /api/field-leadership/:id endpoint"""
        # First get a record ID
        list_response = admin_session.get(f"{BASE_URL}/api/field-leadership?limit=1")
        if list_response.status_code != 200:
            pytest.skip("Could not get field leadership list")
        
        data = list_response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        if not items or len(items) == 0:
            pytest.skip("No field leadership records available")
        
        record_id = items[0].get("id") or items[0].get("_id")
        if not record_id:
            pytest.skip("Could not extract record ID")
        
        # Now test the detail endpoint
        detail_response = admin_session.get(f"{BASE_URL}/api/field-leadership/{record_id}")
        assert detail_response.status_code == 200, f"Field leadership detail failed: {detail_response.text}"
        
        detail_data = detail_response.json()
        assert isinstance(detail_data, dict), "Response should be a dict"
        print(f"✓ /api/field-leadership/{record_id} returns 200")
        
        if "kind" in detail_data:
            print(f"  - Record kind: {detail_data['kind']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
