"""
Test Daily Summary API endpoints for Phase 2 rebuild.
Tests: draft summary generation, deterministic fast-path, photo intelligence integration.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDailySummaryDraftEndpoint:
    """Tests for /api/daily-reports/summary/draft endpoint"""
    
    def test_draft_summary_returns_promptly(self):
        """Summary endpoint should return within 2 seconds (deterministic fast-path)"""
        payload = {
            "payload": {
                "project_number": "TEST-001",
                "project_name": "Test Project",
                "report_date": "2026-07-16",
                "prepared_by": "Test Supervisor",
                "location": "Test Location",
                "weather_summary": "Sunny, 75F",
                "masci_crews": [{"name": "John Doe", "trade": "Laborer", "hours": 8}],
                "production": [{"description": "Concrete pour", "quantity": 100, "unit": "CY"}],
                "photos": []
            },
            "form_key": "test-form-key-123",
            "language": "en"
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        elapsed = time.time() - start_time
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert elapsed < 2.0, f"Response took {elapsed:.2f}s, expected < 2s"
        
        data = response.json()
        assert data.get("ok") is True or data.get("ok") is False  # Should have ok field
        print(f"Draft summary returned in {elapsed:.3f}s")
    
    def test_draft_summary_deterministic_mode(self):
        """Summary should use deterministic fast-path mode"""
        payload = {
            "payload": {
                "project_number": "TEST-002",
                "report_date": "2026-07-16",
                "masci_crews": [{"name": "Worker A", "hours": 8}],
                "production": [{"description": "Excavation", "quantity": 200, "unit": "CY"}],
                "photos": []
            },
            "form_key": "test-form-key-456",
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # Should indicate deterministic mode
        assert "mode" in data or "reason_disabled" in data
        if "mode" in data:
            assert data["mode"] in ["deterministic_fallback", "deterministic", "llm"]
        print(f"Summary mode: {data.get('mode', 'N/A')}")
    
    def test_draft_summary_includes_summary_text(self):
        """Summary response should include summary_text field"""
        payload = {
            "payload": {
                "project_number": "TEST-003",
                "report_date": "2026-07-16",
                "masci_crews": [{"name": "Worker B", "hours": 10}],
                "production": [],
                "photos": []
            },
            "form_key": "test-form-key-789",
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "summary_text" in data
        assert isinstance(data["summary_text"], str)
        print(f"Summary text: {data['summary_text'][:100]}...")
    
    def test_draft_summary_includes_summary_input(self):
        """Summary response should include summary_input with labor/equipment/production data"""
        payload = {
            "payload": {
                "project_number": "TEST-004",
                "report_date": "2026-07-16",
                "masci_crews": [
                    {"name": "Worker A", "hours": 8, "trade": "Laborer"},
                    {"name": "Worker B", "hours": 6, "trade": "Operator"}
                ],
                "equipment": [
                    {"description": "Excavator", "hours_used": 4, "idle_hours": 1}
                ],
                "production": [
                    {"description": "Pipe install", "quantity": 50, "unit": "LF"}
                ],
                "photos": []
            },
            "form_key": "test-form-key-abc",
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "summary_input" in data
        
        summary_input = data["summary_input"]
        assert "labor" in summary_input
        assert "equipment" in summary_input
        assert "production" in summary_input
        assert "photos" in summary_input
        
        # Verify labor data
        labor = summary_input["labor"]
        assert labor["employee_count"] == 2
        assert labor["total_employee_hours"] == 14.0
        
        # Verify equipment data
        equipment = summary_input["equipment"]
        assert equipment["equipment_count"] == 1
        
        # Verify production data
        production = summary_input["production"]
        assert len(production["rows"]) == 1
        
        print(f"Summary input validated: {labor['employee_count']} employees, {equipment['equipment_count']} equipment")
    
    def test_draft_summary_photo_intelligence_field(self):
        """Summary response should include photo_intelligence field"""
        payload = {
            "payload": {
                "project_number": "TEST-005",
                "report_date": "2026-07-16",
                "masci_crews": [],
                "production": [],
                "photos": []
            },
            "form_key": "test-form-key-def",
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # photo_intelligence can be null or an object
        assert "photo_intelligence" in data
        print(f"Photo intelligence: {data.get('photo_intelligence')}")
    
    def test_draft_summary_empty_payload(self):
        """Summary should handle empty/minimal payload gracefully"""
        payload = {
            "payload": {},
            "form_key": "test-empty",
            "language": "en"
        }
        
        response = requests.post(f"{BASE_URL}/api/daily-reports/summary/draft", json=payload)
        # Should not crash - either 200 with minimal summary or 4xx with error
        assert response.status_code in [200, 400, 422]
        print(f"Empty payload response: {response.status_code}")


class TestDailyReportSubmitEndpoint:
    """Tests for /api/daily-reports POST endpoint (submit flow)"""
    
    def test_submit_endpoint_exists(self):
        """Submit endpoint should exist and require proper payload"""
        # Send minimal payload to check endpoint exists
        response = requests.post(f"{BASE_URL}/api/daily-reports", json={})
        # Should return 422 (validation error) not 404
        assert response.status_code in [401, 422, 400], f"Expected 401/422/400, got {response.status_code}"
        print(f"Submit endpoint exists, returned {response.status_code}")


class TestDailyReportDuplicateCheck:
    """Tests for /api/daily-reports/duplicate-check endpoint"""
    
    def test_duplicate_check_endpoint_exists(self):
        """Duplicate check endpoint should exist"""
        params = {
            "project_number": "TEST-001",
            "report_date": "2026-07-16"
        }
        response = requests.get(f"{BASE_URL}/api/daily-reports/duplicate-check", params=params)
        # Should return 200 with exists field
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "exists" in data
        print(f"Duplicate check: exists={data.get('exists')}")


class TestHealthEndpoint:
    """Basic health check"""
    
    def test_api_health(self):
        """API should be healthy"""
        response = requests.get(f"{BASE_URL}/api/version")
        assert response.status_code == 200
        print("API is healthy")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
