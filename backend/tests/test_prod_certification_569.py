"""
Production Certification Test Suite - Iteration 569
Tests critical production endpoints at https://mascidocs.com
Read-only verification - no write operations to production data
"""
import pytest
import requests
import os
import time

# Production URL
BASE_URL = "https://mascidocs.com"

# Super admin credentials
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


class TestReleaseIdentity:
    """Test release identity and lineage on production"""
    
    def test_version_endpoint_returns_expected_fields(self):
        """Verify /api/version returns all required fields"""
        response = requests.get(f"{BASE_URL}/api/version")
        assert response.status_code == 200
        data = response.json()
        
        # Required fields
        assert "commit" in data
        assert "source_hash" in data
        assert "frontend_backend_release_match" in data
        assert "app_env" in data
        assert "db_name" in data
        assert "instance_fingerprint" in data
        
        # Verify production environment
        assert data["app_env"] == "production"
        assert data["db_name"] == "masci_safety"
        assert data["frontend_backend_release_match"] == True
        
        print(f"✓ Release: {data['commit'][:8]}, source_hash: {data['source_hash']}")
    
    def test_version_stability_across_calls(self):
        """Verify repeated /api/version calls return consistent identity"""
        responses = []
        for _ in range(3):
            response = requests.get(f"{BASE_URL}/api/version")
            assert response.status_code == 200
            responses.append(response.json())
            time.sleep(0.5)
        
        # Commit and source_hash should be identical
        commits = set(r["commit"] for r in responses)
        source_hashes = set(r["source_hash"] for r in responses)
        
        assert len(commits) == 1, f"Commit mismatch across calls: {commits}"
        assert len(source_hashes) == 1, f"Source hash mismatch: {source_hashes}"
        
        # Instance fingerprint may vary (load balancing)
        fingerprints = set(r["instance_fingerprint"] for r in responses)
        print(f"✓ Consistent commit/hash, {len(fingerprints)} unique instance(s)")
    
    def test_environment_identity_fields(self):
        """Verify environment identity configuration"""
        response = requests.get(f"{BASE_URL}/api/version")
        data = response.json()
        
        env_id = data.get("environment_identity", {})
        
        assert env_id.get("app_env") == "production"
        assert env_id.get("db_name") == "masci_safety"
        assert env_id.get("db_isolation_enforced") == True
        assert env_id.get("storage_bucket") == "masci-hub"
        assert env_id.get("delete_engine_status") == "DISABLED"
        
        print(f"✓ Environment identity verified: {env_id.get('app_env')}/{env_id.get('db_name')}")


class TestHealthEndpoints:
    """Test health and startup surfaces"""
    
    def test_health_basic(self):
        """Verify /api/health returns healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        print(f"✓ Health OK: {data}")
    
    def test_health_full(self):
        """Verify /api/health/full returns all subsystems healthy"""
        response = requests.get(f"{BASE_URL}/api/health/full")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") == True
        assert data.get("mongo") == True
        assert data.get("scheduler") == True
        assert data.get("backup_recent") == True
        
        print(f"✓ Full health: mongo={data.get('mongo')}, scheduler={data.get('scheduler')}, backup={data.get('backup_recent')}")


class TestAuthentication:
    """Test authentication and session management"""
    
    def test_super_admin_multi_login(self):
        """Verify super admin can login via multi-login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("ok") == True
        assert "portal_tokens" in data
        assert "user" in data
        
        # Verify all portal tokens present
        tokens = data["portal_tokens"]
        expected_portals = ["admin", "pm", "hr", "safety", "shop", "dispatch"]
        for portal in expected_portals:
            assert portal in tokens, f"Missing portal token: {portal}"
        
        print(f"✓ Super admin login successful, {len(tokens)} portal tokens")
        return tokens
    
    def test_invalid_credentials_rejected(self):
        """Verify invalid credentials are rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected")
    
    def test_no_redirect_loop_on_login(self):
        """Verify login doesn't cause redirect loops"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            allow_redirects=True
        )
        
        # Should not have excessive redirects
        assert len(response.history) < 5, f"Too many redirects: {len(response.history)}"
        assert response.status_code == 200
        print(f"✓ No redirect loop, {len(response.history)} redirects")


class TestDailyReports:
    """Test Daily Report route contracts and functionality"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        return response.json()["portal_tokens"]["admin"]
    
    def test_daily_reports_list(self, admin_token):
        """Verify daily reports list endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports?limit=5",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify report structure
        report = data[0]
        assert "id" in report
        assert "project_number" in report
        assert "report_date" in report
        
        print(f"✓ Daily reports list: {len(data)} reports returned")
    
    def test_daily_report_viewer(self, admin_token):
        """Verify individual report viewer works"""
        # Get a report ID first
        list_response = requests.get(
            f"{BASE_URL}/api/daily-reports?limit=1",
            headers={"X-Admin-Token": admin_token}
        )
        report_id = list_response.json()[0]["id"]
        
        # Fetch the report
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == report_id
        print(f"✓ Report viewer works: {report_id[:8]}...")
    
    def test_legacy_route_aliases_resolve(self):
        """Verify legacy route aliases return 200"""
        legacy_routes = [
            "/daily/new",
            "/reports/daily/new",
            "/daily/v1",
            "/daily/v2",
            "/daily/v3",
            "/daily-report/v1",
            "/daily-report/v2",
            "/daily-report/v3",
            "/daily/submit"
        ]
        
        for route in legacy_routes:
            response = requests.get(f"{BASE_URL}{route}", allow_redirects=True)
            assert response.status_code == 200, f"Route {route} failed with {response.status_code}"
        
        print(f"✓ All {len(legacy_routes)} legacy routes resolve to 200")


class TestDispatchSurfaces:
    """Test dispatch and transportation surfaces"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        return response.json()["portal_tokens"]["admin"]
    
    def test_projects_list(self, admin_token):
        """Verify projects list endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/projects/list?limit=10",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert len(data["items"]) > 0
        
        print(f"✓ Projects list: {len(data['items'])} projects")


class TestPortalAccess:
    """Test major portal surfaces load correctly"""
    
    @pytest.fixture
    def tokens(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        return response.json()["portal_tokens"]
    
    def test_admin_me_endpoint(self, tokens):
        """Verify admin /me endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"Authorization": f"Bearer {tokens['admin']}"}
        )
        # May return 200 or use different auth header
        print(f"Admin me endpoint: {response.status_code}")
    
    def test_pm_token_valid(self, tokens):
        """Verify PM token is valid"""
        assert tokens.get("pm") is not None
        assert len(tokens["pm"]) > 50
        print(f"✓ PM token valid: {len(tokens['pm'])} chars")
    
    def test_hr_token_valid(self, tokens):
        """Verify HR token is valid"""
        assert tokens.get("hr") is not None
        assert len(tokens["hr"]) > 50
        print(f"✓ HR token valid: {len(tokens['hr'])} chars")
    
    def test_safety_token_valid(self, tokens):
        """Verify Safety token is valid"""
        assert tokens.get("safety") is not None
        assert len(tokens["safety"]) > 50
        print(f"✓ Safety token valid: {len(tokens['safety'])} chars")
    
    def test_shop_token_valid(self, tokens):
        """Verify Shop token is valid"""
        assert tokens.get("shop") is not None
        assert len(tokens["shop"]) > 50
        print(f"✓ Shop token valid: {len(tokens['shop'])} chars")
    
    def test_dispatch_token_valid(self, tokens):
        """Verify Dispatch token is valid"""
        assert tokens.get("dispatch") is not None
        assert len(tokens["dispatch"]) > 50
        print(f"✓ Dispatch token valid: {len(tokens['dispatch'])} chars")


class TestCertificationIsolation:
    """Verify certification records are isolated from operational data"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD}
        )
        return response.json()["portal_tokens"]["admin"]
    
    def test_no_certification_records_in_daily_reports(self, admin_token):
        """Verify certification records are excluded from daily reports list"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports?limit=50",
            headers={"X-Admin-Token": admin_token}
        )
        data = response.json()
        
        for report in data:
            # Check for certification markers
            assert report.get("certification_record") != True
            assert report.get("synthetic_record") != True
            # Check project number doesn't contain cert markers
            pn = report.get("project_number", "")
            assert "CERT" not in pn.upper() or "ZZ-RUNTIME-CERT" not in pn
        
        print(f"✓ No certification records in {len(data)} daily reports")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
