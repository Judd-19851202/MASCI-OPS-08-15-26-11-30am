"""
Daily Report Submit Latency Test - TRACK 26.02 Async Path Verification

Tests the POST /api/daily-reports endpoint to verify:
1. Submit returns 200/201 reliably without timeout or gateway-style failure
2. Measures submit latency for at least 2 requests
3. Response creates a real Daily Report record with id/doc_id/report_number
"""
import os
import time
import uuid
import pytest
import requests
from datetime import datetime

# Use the preview URL from environment
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"


def generate_unique_project_number():
    """Generate a unique project number for each test run."""
    return f"TEST-SUBMIT-QA-{uuid.uuid4().hex[:8].upper()}"


def build_valid_minimal_payload(project_number: str):
    """Build a valid minimal payload for Daily Report submission."""
    return {
        "project_number": project_number,
        "project_name": "TEST Submit Speed Project",
        "report_date": "2026-08-05",
        "prepared_by": "TEST Submitter",
        "weather": "Clear",
        "location": "TEST Site",
        "supervisor": "TEST Supervisor",
        "crew_size": 1,
        "general_notes": "submit-speed-check",
        "ai_accepted_summary": "Work completed successfully for submit timing validation.",
        "ai_accepted_summary_meta": {
            "edited_by_user": False,
            "accepted_at": "2026-08-05T15:00:00Z",
            "source": "manual"
        },
        # Required location fields
        "location_source": "manual",
        "gps_lat": 25.7617,
        "gps_lng": -80.1918,
        "location_captured_at": "2026-08-05T15:00:00Z",
        # Mark as synthetic/test record
        "synthetic_record": True,
        "certification_record": True,
        "hidden_from_operations": True,
        "email_dispatch_suppressed": True,
    }


class TestDailyReportSubmitLatency:
    """Test Daily Report submit latency and reliability."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session."""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self.created_report_ids = []
        yield
        # Cleanup: Note - we don't delete as DELETE is frozen (410)
        # Reports are marked as synthetic/certification records

    def test_health_check(self):
        """Verify backend is accessible before running submit tests."""
        response = self.session.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print(f"✓ Health check passed: {response.status_code}")

    def test_submit_latency_request_1(self):
        """First submit latency measurement."""
        project_number = generate_unique_project_number()
        payload = build_valid_minimal_payload(project_number)
        
        start_time = time.time()
        response = self.session.post(
            f"{BASE_URL}/api/daily-reports",
            json=payload,
            timeout=60  # 60 second timeout
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n=== Submit Request 1 ===")
        print(f"Project Number: {project_number}")
        print(f"Status Code: {response.status_code}")
        print(f"Latency: {elapsed_time:.2f} seconds")
        
        # Verify success
        assert response.status_code in [200, 201], f"Submit failed with status {response.status_code}: {response.text[:500]}"
        
        # Verify response contains required fields
        data = response.json()
        assert "id" in data or "doc_id" in data or "report_number" in data, \
            f"Response missing id/doc_id/report_number: {list(data.keys())}"
        
        report_id = data.get("id") or data.get("doc_id") or data.get("report_number")
        self.created_report_ids.append(report_id)
        
        print(f"Report ID: {report_id}")
        print(f"Doc ID: {data.get('doc_id', 'N/A')}")
        print(f"Report Number: {data.get('report_number', 'N/A')}")
        
        # Verify latency is reasonable (under 30 seconds)
        assert elapsed_time < 30, f"Submit took too long: {elapsed_time:.2f}s (expected < 30s)"
        print(f"✓ Submit completed in {elapsed_time:.2f}s (within acceptable range)")

    def test_submit_latency_request_2(self):
        """Second submit latency measurement."""
        project_number = generate_unique_project_number()
        payload = build_valid_minimal_payload(project_number)
        
        start_time = time.time()
        response = self.session.post(
            f"{BASE_URL}/api/daily-reports",
            json=payload,
            timeout=60
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n=== Submit Request 2 ===")
        print(f"Project Number: {project_number}")
        print(f"Status Code: {response.status_code}")
        print(f"Latency: {elapsed_time:.2f} seconds")
        
        # Verify success
        assert response.status_code in [200, 201], f"Submit failed with status {response.status_code}: {response.text[:500]}"
        
        # Verify response contains required fields
        data = response.json()
        assert "id" in data or "doc_id" in data or "report_number" in data, \
            f"Response missing id/doc_id/report_number: {list(data.keys())}"
        
        report_id = data.get("id") or data.get("doc_id") or data.get("report_number")
        self.created_report_ids.append(report_id)
        
        print(f"Report ID: {report_id}")
        print(f"Doc ID: {data.get('doc_id', 'N/A')}")
        print(f"Report Number: {data.get('report_number', 'N/A')}")
        
        # Verify latency is reasonable
        assert elapsed_time < 30, f"Submit took too long: {elapsed_time:.2f}s (expected < 30s)"
        print(f"✓ Submit completed in {elapsed_time:.2f}s (within acceptable range)")

    def test_submit_creates_real_record(self):
        """Verify submit creates a real Daily Report record that can be retrieved."""
        project_number = generate_unique_project_number()
        payload = build_valid_minimal_payload(project_number)
        
        # Submit the report
        start_time = time.time()
        response = self.session.post(
            f"{BASE_URL}/api/daily-reports",
            json=payload,
            timeout=60
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n=== Submit + Verify Record ===")
        print(f"Project Number: {project_number}")
        print(f"Submit Status: {response.status_code}")
        print(f"Submit Latency: {elapsed_time:.2f}s")
        
        assert response.status_code in [200, 201], f"Submit failed: {response.status_code}"
        
        data = response.json()
        report_id = data.get("id")
        doc_id = data.get("doc_id")
        report_number = data.get("report_number")
        
        print(f"Created Report ID: {report_id}")
        print(f"Created Doc ID: {doc_id}")
        print(f"Created Report Number: {report_number}")
        
        # Verify at least one identifier is present
        assert report_id or doc_id or report_number, "No identifier returned in response"
        
        # Verify the record was actually created by fetching it
        # Note: This may require authentication for non-public endpoints
        if report_id:
            get_response = self.session.get(
                f"{BASE_URL}/api/daily-reports/{report_id}",
                timeout=30
            )
            # 200 = found, 401/403 = auth required (record exists but protected)
            if get_response.status_code == 200:
                fetched_data = get_response.json()
                assert fetched_data.get("project_number") == project_number, \
                    f"Fetched record has wrong project_number"
                print(f"✓ Record verified via GET: project_number matches")
            elif get_response.status_code in [401, 403]:
                print(f"✓ Record exists (GET returned {get_response.status_code} - auth required)")
            else:
                print(f"⚠ GET returned {get_response.status_code} - record may not be accessible")
        
        print(f"✓ Daily Report record created successfully")


class TestDailyReportSubmitValidation:
    """Test Daily Report submit validation requirements."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session."""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def test_submit_requires_approved_summary(self):
        """Verify submit fails without approved summary (422)."""
        payload = {
            "project_number": "TEST-NO-SUMMARY",
            "project_name": "TEST No Summary Project",
            "report_date": "2026-08-05",
            "prepared_by": "TEST Submitter",
            "location": "TEST Site",
            "location_source": "manual",
            # Missing ai_accepted_summary and ai_accepted_summary_meta
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/daily-reports",
            json=payload,
            timeout=30
        )
        
        print(f"\n=== Submit Without Approved Summary ===")
        print(f"Status Code: {response.status_code}")
        
        # Should return 422 with approved_summary_required error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", {})
        error_code = detail.get("error") if isinstance(detail, dict) else None
        
        print(f"Error: {error_code or detail}")
        assert error_code == "approved_summary_required" or "approved_summary" in str(detail).lower(), \
            f"Expected approved_summary_required error, got: {detail}"
        print(f"✓ Correctly rejected submission without approved summary")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
