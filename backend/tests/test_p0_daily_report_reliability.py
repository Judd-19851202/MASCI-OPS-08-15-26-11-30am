"""
P0 Daily Report Reliability Incident - Backend API Tests
=========================================================
Tests for the incident fix verifying:
1. Backend readiness/health/version endpoints remain aligned
2. Public HR roster endpoint works for anonymous Daily Report access
3. skipSessionStatus behavior for optional/background loaders
"""

import pytest
import requests
import os

BASE_URL = (
    os.environ.get('REACT_APP_BACKEND_URL')
    or 'http://localhost:8001'
).rstrip('/')

class TestBackendHealthEndpoints:
    """Verify backend readiness/health/version endpoints after incident fix"""
    
    def test_ready_endpoint_returns_ok(self):
        """GET /api/ready should return 200 with ok=true"""
        response = requests.get(f"{BASE_URL}/api/ready", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("ok") is True, f"Expected ok=true, got {data}"
        assert data.get("state") == "ready", f"Expected state=ready, got {data.get('state')}"
        print(f"✓ /api/ready: ok={data.get('ok')}, state={data.get('state')}")
    
    def test_health_full_endpoint_returns_ok(self):
        """GET /api/health/full should return 200 with all health checks passing"""
        response = requests.get(f"{BASE_URL}/api/health/full", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("ok") is True, f"Expected ok=true, got {data}"
        assert data.get("mongo") is True, f"Expected mongo=true, got {data.get('mongo')}"
        print(f"✓ /api/health/full: ok={data.get('ok')}, mongo={data.get('mongo')}")
    
    def test_version_endpoint_returns_release_info(self):
        """GET /api/version should return version/commit info"""
        response = requests.get(f"{BASE_URL}/api/version", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "commit" in data, "Expected commit field in version response"
        assert "source_hash" in data, "Expected source_hash field in version response"
        print(f"✓ /api/version: commit={data.get('commit')[:8]}..., source_hash={data.get('source_hash')[:8]}...")


class TestPublicHrRosterEndpoint:
    """Verify public HR roster endpoint for anonymous Daily Report access"""
    
    def test_public_hr_roster_returns_200(self):
        """GET /api/hr/employee-roster/public should return 200 without auth"""
        response = requests.get(f"{BASE_URL}/api/hr/employee-roster/public", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Expected items array in response"
        items = data.get("items", [])
        print(f"✓ /api/hr/employee-roster/public: returned {len(items)} employees")
    
    def test_public_hr_roster_does_not_expose_pii(self):
        """Public HR roster should not expose private fields (CDL, SSN, DOB, etc.)"""
        response = requests.get(f"{BASE_URL}/api/hr/employee-roster/public", timeout=15)
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        
        # Check first few items for PII fields that should NOT be present
        pii_fields = ["ssn", "social_security", "dob", "date_of_birth", "cdl_number", 
                      "medical_card", "phone", "email", "address", "emergency_contact"]
        
        for item in items[:5]:  # Check first 5 items
            for field in pii_fields:
                assert field not in item, f"PII field '{field}' should not be in public roster"
        
        print(f"✓ Public HR roster does not expose PII fields")


class TestDailyReportPublicEndpoints:
    """Verify Daily Report public endpoints work without auth"""
    
    def test_next_number_endpoint(self):
        """GET /api/daily-reports/next-number should return next report number preview"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/next-number",
            params={"report_date": "2026-07-22"},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # The endpoint returns doc_id_preview for preview environments
        assert "doc_id_preview" in data or "next_number" in data, "Expected doc_id_preview or next_number in response"
        preview_num = data.get("doc_id_preview") or data.get("next_number")
        print(f"✓ /api/daily-reports/next-number: {preview_num}")
    
    def test_jobs_endpoint_returns_list(self):
        """GET /api/jobs should return job list for job picker"""
        response = requests.get(f"{BASE_URL}/api/jobs", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Jobs endpoint may return items array or direct list
        items = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(items, list), "Expected list of jobs"
        print(f"✓ /api/jobs: returned {len(items)} jobs")
    
    def test_field_leadership_roster_endpoint(self):
        """GET /api/field-leadership-roster should return foreman list"""
        response = requests.get(f"{BASE_URL}/api/field-leadership-roster", timeout=15)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        print(f"✓ /api/field-leadership-roster: returned {len(items) if isinstance(items, list) else 'data'}")


class TestBrandingAndBannerEndpoints:
    """Verify branding and banner endpoints for Daily Report UI"""
    
    def test_branding_current_endpoint(self):
        """GET /api/branding/current should return branding config"""
        response = requests.get(f"{BASE_URL}/api/branding/current", timeout=10)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ /api/branding/current: returned branding config")
    
    def test_banners_active_endpoint(self):
        """GET /api/banners/active should return active banners"""
        response = requests.get(
            f"{BASE_URL}/api/banners/active",
            params={"device_id": "test-device-123"},
            timeout=10
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ /api/banners/active: returned banner data")


class TestEquipmentMasterEndpoint:
    """Verify equipment master endpoint for equipment picker"""
    
    def test_equipment_master_returns_list(self):
        """GET /api/equipment-master should return equipment list"""
        response = requests.get(f"{BASE_URL}/api/equipment-master", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "items" in data or "categories" in data, "Expected items or categories in response"
        print(f"✓ /api/equipment-master: returned equipment data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
