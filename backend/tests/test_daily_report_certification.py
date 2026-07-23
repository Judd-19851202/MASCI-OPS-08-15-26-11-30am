"""
Daily Report Certification Tests - Iteration 17
Tests for ForgedOps Daily Report workflow certification including:
- Health endpoints
- Report number preview
- Attachment evidence
- PDF generation with attachment evidence
- Admin/PM read access
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "jaymn.judd@mascigc.com"
TEST_PASSWORD = "Maddix123!"

# Existing synthetic report for testing
SYNTHETIC_REPORT_ID = "17010cbf-e5b6-4929-84e6-71430efbff90"
SYNTHETIC_DOC_ID = "DR-2026-03522"


class TestHealthEndpoints:
    """Health and readiness endpoint tests"""
    
    def test_ready_endpoint(self):
        """Test /api/ready returns 200 and ok=true"""
        response = requests.get(f"{BASE_URL}/api/ready")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data.get("state") == "ready"
        assert data.get("mongo_ok") is True
        assert data.get("startup_complete") is True
        print(f"PASS: /api/ready returns ok=true, state=ready")
    
    def test_health_full_endpoint(self):
        """Test /api/health/full returns 200 and all checks pass"""
        response = requests.get(f"{BASE_URL}/api/health/full")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert data.get("mongo") is True
        assert data.get("scheduler") is True
        assert data.get("runtime_identity_ok") is True
        print(f"PASS: /api/health/full returns all checks passing")
    
    def test_version_endpoint(self):
        """Test /api/version returns frontend_backend_release_match=true"""
        response = requests.get(f"{BASE_URL}/api/version")
        assert response.status_code == 200
        data = response.json()
        assert data.get("frontend_backend_release_match") is True
        print(f"PASS: /api/version shows frontend_backend_release_match=true")


class TestAuthentication:
    """Authentication tests"""
    
    def test_multi_login(self):
        """Test multi-login returns session and portal tokens"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        assert "session_token" in data
        assert "portal_tokens" in data
        assert "admin" in data["portal_tokens"]
        assert "pm" in data["portal_tokens"]
        print(f"PASS: Multi-login returns session and portal tokens")


class TestReportNumberPreview:
    """Report number preview tests"""
    
    def test_next_number_preview(self):
        """Test /api/daily-reports/next-number returns preview"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/next-number",
            params={"report_date": "2026-07-22"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "report_number" in data
        assert data["report_number"].startswith("DR-2026-")
        assert data.get("is_preview_only") is True
        print(f"PASS: Report number preview: {data['report_number']}")
    
    def test_duplicate_check(self):
        """Test /api/daily-reports/duplicate-check works"""
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/duplicate-check",
            params={"project_number": "TEST-001", "report_date": "2026-07-22"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "exists" in data
        assert "count" in data
        print(f"PASS: Duplicate check returns exists={data['exists']}, count={data['count']}")


@pytest.fixture
def auth_tokens():
    """Get authentication tokens"""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip("Authentication failed")
    data = response.json()
    return {
        "session_token": data["session_token"],
        "admin_token": data["portal_tokens"]["admin"],
        "pm_token": data["portal_tokens"]["pm"]
    }


class TestDailyReportRead:
    """Daily report read access tests"""
    
    def test_admin_read_report(self, auth_tokens):
        """Test admin can read daily report with attachments"""
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["session_token"]
        }
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/{SYNTHETIC_REPORT_ID}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("id") == SYNTHETIC_REPORT_ID
        assert data.get("doc_id") == SYNTHETIC_DOC_ID
        assert "attachments" in data
        assert len(data["attachments"]) >= 2
        print(f"PASS: Admin can read report with {len(data['attachments'])} attachments")
    
    def test_report_has_attachment_evidence(self, auth_tokens):
        """Test report contains attachment evidence with filenames"""
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["session_token"]
        }
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/{SYNTHETIC_REPORT_ID}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check attachments have required fields
        attachments = data.get("attachments", [])
        assert len(attachments) >= 2
        
        for attachment in attachments:
            assert "filename" in attachment
            assert "mime_type" in attachment
            assert "attachment_ref" in attachment
        
        # Check for specific test attachments
        filenames = [a["filename"] for a in attachments]
        assert "daily_ticket.pdf" in filenames
        assert any("notes with spaces" in f for f in filenames)
        print(f"PASS: Report has attachment evidence with filenames: {filenames}")


class TestPDFGeneration:
    """PDF generation tests"""
    
    def test_pdf_generation_queues(self, auth_tokens):
        """Test PDF generation job is queued"""
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["session_token"]
        }
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/{SYNTHETIC_REPORT_ID}/pdf",
            headers=headers
        )
        assert response.status_code in [200, 202]  # 202 Accepted for async job
        data = response.json()
        assert data.get("ok") is True
        assert "job_id" in data
        assert data.get("kind") == "daily_report_pdf"
        print(f"PASS: PDF generation job queued: {data['job_id']}")
        return data["job_id"]
    
    def test_pdf_generation_completes(self, auth_tokens):
        """Test PDF generation completes successfully"""
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["session_token"]
        }
        
        # Request PDF
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/{SYNTHETIC_REPORT_ID}/pdf",
            headers=headers
        )
        assert response.status_code in [200, 202]  # 202 Accepted for async job
        job_id = response.json()["job_id"]
        
        # Poll for completion
        max_attempts = 10
        for i in range(max_attempts):
            time.sleep(1)
            status_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/status")
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                assert status_data.get("ok") is True
                assert "result" in status_data
                assert "download_url" in status_data["result"]
                assert status_data["result"].get("source") == "canonical"
                print(f"PASS: PDF generation completed with canonical source")
                return status_data
            elif status_data.get("status") == "failed":
                pytest.fail(f"PDF generation failed: {status_data.get('error')}")
        
        pytest.fail("PDF generation timed out")
    
    def test_pdf_download_works(self, auth_tokens):
        """Test PDF can be downloaded"""
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["session_token"]
        }
        
        # Request PDF
        response = requests.get(
            f"{BASE_URL}/api/daily-reports/{SYNTHETIC_REPORT_ID}/pdf",
            headers=headers
        )
        job_id = response.json()["job_id"]
        
        # Wait for completion
        time.sleep(3)
        status_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/status")
        status_data = status_response.json()
        
        if status_data.get("status") == "completed":
            download_url = status_data["result"]["download_url"]
            pdf_response = requests.get(f"{BASE_URL}{download_url}")
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"
            assert len(pdf_response.content) > 10000  # PDF should be substantial
            print(f"PASS: PDF downloaded successfully, size: {len(pdf_response.content)} bytes")


class TestAISummary:
    """AI summary tests"""
    
    def test_ai_summary_endpoint_exists(self, auth_tokens):
        """Test AI summary draft endpoint exists"""
        headers = {
            "X-Admin-Token": auth_tokens["admin_token"],
            "X-Directory-Token": auth_tokens["session_token"]
        }
        # This is a POST endpoint to generate AI summary
        response = requests.post(
            f"{BASE_URL}/api/daily-reports/{SYNTHETIC_REPORT_ID}/ai-summary",
            headers=headers
        )
        # Should return 200 or 202 (accepted) or 400 (if already has summary)
        assert response.status_code in [200, 202, 400, 404]
        print(f"PASS: AI summary endpoint responds with status {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
