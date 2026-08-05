"""
Test Suite: Master Data Dropdown Population
============================================
Tests for the bug fix: crews see empty master-data dropdowns in production.

Verifies that the following public/anonymous endpoints return non-empty item arrays:
- GET /api/hr/employee-roster/public (anonymous employee picker)
- GET /api/jobs (public job picker)
- GET /api/equipment-master (public equipment picker)
- GET /api/suppliers (public supplier picker)

Also verifies PM-authenticated endpoint:
- GET /api/hr/employee-roster (with X-PM-Token)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")

# Test credentials from test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"


class TestPublicMasterDataEndpoints:
    """Test public/anonymous master data endpoints return populated data."""

    def test_public_employee_roster_returns_items(self):
        """GET /api/hr/employee-roster/public should return non-empty employee list."""
        response = requests.get(f"{BASE_URL}/api/hr/employee-roster/public", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "'items' should be a list"
        
        # Critical: items should NOT be empty
        assert len(data["items"]) > 0, "Employee roster should NOT be empty - this is the bug we're fixing!"
        
        # Verify item structure (public projection)
        if data["items"]:
            item = data["items"][0]
            # Public projection should have these fields
            assert "name" in item, "Employee should have 'name' field"
            # Should NOT have PII fields
            assert "email" not in item or item.get("email") is None, "Public roster should NOT expose email"
            assert "phone" not in item or item.get("phone") is None, "Public roster should NOT expose phone"
            assert "ssn" not in item or item.get("ssn") is None, "Public roster should NOT expose SSN"
        
        print(f"✓ /api/hr/employee-roster/public: returned {len(data['items'])} employees")

    def test_public_jobs_returns_items(self):
        """GET /api/jobs should return non-empty job list."""
        response = requests.get(f"{BASE_URL}/api/jobs", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "'items' should be a list"
        
        # Critical: items should NOT be empty
        assert len(data["items"]) > 0, "Jobs list should NOT be empty - this is the bug we're fixing!"
        
        # Verify item structure
        if data["items"]:
            item = data["items"][0]
            assert "project_number" in item or "project_name" in item, "Job should have project identifier"
        
        print(f"✓ /api/jobs: returned {len(data['items'])} jobs")

    def test_public_equipment_master_returns_items(self):
        """GET /api/equipment-master should return non-empty equipment list."""
        response = requests.get(f"{BASE_URL}/api/equipment-master", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "'items' should be a list"
        
        # Critical: items should NOT be empty
        assert len(data["items"]) > 0, "Equipment master should NOT be empty - this is the bug we're fixing!"
        
        # Verify item structure
        if data["items"]:
            item = data["items"][0]
            # Equipment should have identifying fields
            assert "unit_number" in item or "make_model" in item or "category" in item, \
                "Equipment should have identifying fields"
        
        print(f"✓ /api/equipment-master: returned {len(data['items'])} equipment items")

    def test_public_suppliers_returns_items(self):
        """GET /api/suppliers should return non-empty supplier list."""
        response = requests.get(f"{BASE_URL}/api/suppliers", timeout=30)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "'items' should be a list"
        
        # Critical: items should NOT be empty
        assert len(data["items"]) > 0, "Suppliers list should NOT be empty - this is the bug we're fixing!"
        
        # Verify item structure
        if data["items"]:
            item = data["items"][0]
            assert "name" in item, "Supplier should have 'name' field"
        
        print(f"✓ /api/suppliers: returned {len(data['items'])} suppliers")


class TestPMAuthenticatedEndpoints:
    """Test PM-authenticated master data endpoints."""

    @pytest.fixture(scope="class")
    def pm_token(self):
        """Get PM authentication token."""
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=30
        )
        
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        token = data.get("token")
        if not token:
            pytest.skip("PM login did not return a token")
        
        print(f"✓ PM login successful for {PM_EMAIL}")
        return token

    def test_pm_authenticated_employee_roster(self, pm_token):
        """GET /api/hr/employee-roster with X-PM-Token should return non-empty list."""
        response = requests.get(
            f"{BASE_URL}/api/hr/employee-roster",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert isinstance(data["items"], list), "'items' should be a list"
        
        # Critical: items should NOT be empty
        assert len(data["items"]) > 0, "Authenticated employee roster should NOT be empty!"
        
        print(f"✓ /api/hr/employee-roster (PM auth): returned {len(data['items'])} employees")


class TestSupplierCacheRegression:
    """Test that supplier dropdown doesn't become sticky-empty."""

    def test_supplier_multiple_loads_not_sticky_empty(self):
        """Supplier dropdown should not cache empty results permanently."""
        # First load
        response1 = requests.get(f"{BASE_URL}/api/suppliers", timeout=30)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Second load (should not be sticky-empty if first was empty)
        response2 = requests.get(f"{BASE_URL}/api/suppliers", timeout=30)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Third load
        response3 = requests.get(f"{BASE_URL}/api/suppliers", timeout=30)
        assert response3.status_code == 200
        data3 = response3.json()
        
        # All should return the same count (no sticky-empty behavior)
        count1 = len(data1.get("items", []))
        count2 = len(data2.get("items", []))
        count3 = len(data3.get("items", []))
        
        assert count1 == count2 == count3, \
            f"Supplier counts should be consistent: {count1}, {count2}, {count3}"
        
        # And should not be empty
        assert count1 > 0, "Suppliers should not be empty across multiple loads"
        
        print(f"✓ Supplier cache regression test passed: {count1} suppliers across 3 loads")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
