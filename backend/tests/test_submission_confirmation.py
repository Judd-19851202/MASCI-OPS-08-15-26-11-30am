"""
Test submission confirmation flows and governed numbering
Tests for DVIR, Daily Reports, Near Miss, PO Requests, Safety Forms, ODR
"""
import pytest
import requests
import os
import time

BASE_URL = "http://localhost:8001"

class TestHealthAndBasicEndpoints:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test backend health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") == True
        print(f"Health check passed: {data}")
    
    def test_ready_endpoint(self):
        """Test backend ready endpoint"""
        response = requests.get(f"{BASE_URL}/api/ready", timeout=10)
        assert response.status_code == 200
        print("Ready endpoint passed")


class TestPublicNearMissSubmission:
    """Test public near-miss submission flow with governed numbering"""
    
    def test_submit_near_miss_returns_case_number(self):
        """Test that near-miss submission returns a governed case number"""
        payload = {
            "what_almost_happened": "Test near miss - forklift almost struck a worker during testing",
            "location_label": "Test Site - Building A"
        }
        response = requests.post(
            f"{BASE_URL}/api/public/near-miss",
            json=payload,
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify governed case number is returned
        assert "case_number" in data, "Response should contain case_number"
        case_number = data.get("case_number")
        assert case_number, "case_number should not be empty"
        print(f"Near miss submitted with case number: {case_number}")
        
        # Verify case structure
        assert "case" in data, "Response should contain case object"
        case = data.get("case", {})
        assert case.get("state") == "FIELD_SUBMITTED", f"Expected FIELD_SUBMITTED state, got {case.get('state')}"
        
        # Verify field_block contains submitted data
        field_block = case.get("field_block", {})
        assert field_block.get("incident_type") == "near_miss"
        assert field_block.get("location_label") == "Test Site - Building A"
        print(f"Near miss case structure verified: {case.get('id')}")


class TestFleetDVIREndpoints:
    """Test DVIR-related endpoints"""
    
    def test_dvir_trucks_list(self):
        """Test that trucks list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/fleet/trucks", timeout=10)
        # May require auth, so 401 is acceptable
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"Trucks list returned {len(data.get('items', data))} items")
    
    def test_dvir_eligible_trucks(self):
        """Test eligible trucks endpoint"""
        response = requests.get(f"{BASE_URL}/api/dispatch/transportation/eligible-trucks", timeout=10)
        # May require auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            print("Eligible trucks endpoint working")


class TestPORequestEndpoints:
    """Test PO Request endpoints"""
    
    def test_po_requests_list(self):
        """Test PO requests list endpoint"""
        response = requests.get(f"{BASE_URL}/api/po-requests", timeout=10)
        # Requires auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"PO requests list returned {len(data.get('items', []))} items")
    
    def test_po_summary(self):
        """Test PO summary endpoint"""
        response = requests.get(f"{BASE_URL}/api/po-requests/summary", timeout=10)
        # Requires auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"PO summary: {data}")


class TestSafetyFormsEndpoints:
    """Test Safety Forms endpoints"""
    
    def test_safety_forms_issuances_list(self):
        """Test safety equipment issuances list"""
        response = requests.get(f"{BASE_URL}/api/safety-forms/equipment-issuances", timeout=10)
        # Requires auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"Safety issuances list returned {len(data.get('items', []))} items")


class TestDailyReportEndpoints:
    """Test Daily Report endpoints"""
    
    def test_daily_reports_list(self):
        """Test daily reports list endpoint"""
        response = requests.get(f"{BASE_URL}/api/daily-reports", timeout=10)
        # Requires auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"Daily reports list returned {len(data.get('items', []))} items")
    
    def test_daily_reports_next_number(self):
        """Test daily reports next number endpoint"""
        today = time.strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/daily-reports/next-number?report_date={today}", timeout=10)
        # May require auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"Next daily report number: {data}")


class TestODREndpoints:
    """Test ODR endpoints"""
    
    def test_odr_list(self):
        """Test ODR list endpoint"""
        response = requests.get(f"{BASE_URL}/api/odr", timeout=10)
        # Requires auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"ODR list returned {len(data.get('items', []))} items")


class TestTrenchSafetyEndpoints:
    """Test Trench Safety endpoints"""
    
    def test_excavations_list(self):
        """Test excavations list endpoint"""
        response = requests.get(f"{BASE_URL}/api/trench-safety/excavations", timeout=10)
        # Requires auth
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            print(f"Excavations list returned {len(data.get('items', []))} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
