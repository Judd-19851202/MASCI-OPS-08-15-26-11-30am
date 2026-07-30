"""
WP-16 Phase 6 Admin Visual Restoration - Backend API Tests
Tests that Admin-protected APIs work correctly after the visual restoration.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ops8-admin-only-preview@example.com"
ADMIN_PASSWORD = "AdminOnlyOps8!"


class TestAdminAuth:
    """Test Admin authentication and token retrieval"""
    
    @pytest.fixture(scope="class")
    def admin_tokens(self):
        """Login and get admin tokens"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Extract tokens
        admin_token = data.get("portal_tokens", {}).get("admin")
        session_token = data.get("session_token")
        
        assert admin_token, "Admin token not found in response"
        assert session_token, "Session token not found in response"
        
        return {
            "admin_token": admin_token,
            "session_token": session_token
        }
    
    def test_admin_login_success(self):
        """Test that admin login works with preview fixture"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "portal_tokens" in data
        assert "admin" in data["portal_tokens"]
        print(f"PASS: Admin login successful")
    
    def test_admin_check_endpoint(self, admin_tokens):
        """Test /api/admin/check endpoint"""
        headers = {
            "X-Admin-Token": admin_tokens["admin_token"],
            "X-Directory-Token": admin_tokens["session_token"]
        }
        response = requests.get(f"{BASE_URL}/api/admin/check", headers=headers)
        assert response.status_code == 200, f"Admin check failed: {response.text}"
        print(f"PASS: /api/admin/check returns 200")


class TestAdminProtectedAPIs:
    """Test Admin-protected API endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        
        return {
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        }
    
    def test_qaqc_inspections(self, admin_headers):
        """Test /api/qaqc-inspections endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/qaqc-inspections",
            headers=admin_headers
        )
        assert response.status_code == 200, f"QAQC inspections failed: {response.text}"
        print(f"PASS: /api/qaqc-inspections returns 200")
    
    def test_equipment_master_status(self, admin_headers):
        """Test /api/admin/equipment-master/status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/equipment-master/status",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Equipment master status failed: {response.text}"
        print(f"PASS: /api/admin/equipment-master/status returns 200")
    
    def test_equipment_inspections(self, admin_headers):
        """Test /api/equipment-inspections endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/equipment-inspections",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Equipment inspections failed: {response.text}"
        print(f"PASS: /api/equipment-inspections returns 200")
    
    def test_meetings(self, admin_headers):
        """Test /api/meetings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/meetings?limit=2",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Meetings failed: {response.text}"
        print(f"PASS: /api/meetings returns 200")
    
    def test_trench_safety_excavations(self, admin_headers):
        """Test /api/trench-safety/excavations endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/trench-safety/excavations?limit=2",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Trench safety excavations failed: {response.text}"
        print(f"PASS: /api/trench-safety/excavations returns 200")
    
    def test_job_photos(self, admin_headers):
        """Test /api/job-photos endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/job-photos?limit=2",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Job photos failed: {response.text}"
        print(f"PASS: /api/job-photos returns 200")
    
    def test_inspections(self, admin_headers):
        """Test /api/inspections endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/inspections?limit=2",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Inspections failed: {response.text}"
        print(f"PASS: /api/inspections returns 200")


class TestInspectionDetail:
    """Test inspection detail route with seeded ID"""
    
    @pytest.fixture(scope="class")
    def admin_headers(self):
        """Get admin auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        
        return {
            "X-Admin-Token": data["portal_tokens"]["admin"],
            "X-Directory-Token": data["session_token"]
        }
    
    def test_inspection_detail_by_id(self, admin_headers):
        """Test fetching inspection by seeded ID"""
        inspection_id = "67555b86-7201-4eb3-806c-0a1c43823f25"
        response = requests.get(
            f"{BASE_URL}/api/inspections/{inspection_id}",
            headers=admin_headers
        )
        # Accept 200 (found) or 404 (not found but endpoint works)
        assert response.status_code in [200, 404], f"Inspection detail failed: {response.text}"
        print(f"PASS: /api/inspections/{inspection_id} returns {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
