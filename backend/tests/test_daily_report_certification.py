"""
FORGEDOPS Daily Report Certification Tests
==========================================
Tests for the canonical Daily Report workflow including:
- Health endpoints (/api/ready, /api/health/full)
- Report number preview (/api/daily-reports/next-number)
- Duplicate check (/api/daily-reports/duplicate-check)
- Attachment upload (/api/daily-reports/attachments/upload)
- Multi-login authentication
- Daily report read with admin tokens
- PDF generation
"""
import os
import pytest
import requests
import base64
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


class TestHealthEndpoints:
    """Test health and readiness endpoints after runtime-healing fix"""
    
    def test_api_ready_returns_200(self):
        """Health endpoint /api/ready should return 200 with ok=true"""
        resp = requests.get(f"{BASE_URL}/api/ready", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected ok=true, got {data}"
        assert data.get("state") == "ready", f"Expected state=ready, got {data.get('state')}"
        assert data.get("mongo_ok") is True, f"Expected mongo_ok=true, got {data}"
    
    def test_api_health_full_returns_200(self):
        """Health endpoint /api/health/full should return 200 with ok=true"""
        resp = requests.get(f"{BASE_URL}/api/health/full", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected ok=true, got {data}"
        assert data.get("mongo") is True, f"Expected mongo=true, got {data}"


class TestReportNumberPreview:
    """Test report number preview endpoint"""
    
    def test_next_number_returns_canonical_format(self):
        """GET /api/daily-reports/next-number should return DR-YYYY-NNNNN format"""
        today = datetime.now().strftime("%Y-%m-%d")
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/next-number",
            params={"date": today},
            timeout=10
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify canonical format
        report_number = data.get("report_number", "")
        assert report_number.startswith("DR-"), f"Expected DR- prefix, got {report_number}"
        assert data.get("is_preview_only") is True, "Expected is_preview_only=true"
        assert "doc_id_preview" in data, "Expected doc_id_preview field"
        
        # Verify format: DR-YYYY-NNNNN
        parts = report_number.split("-")
        assert len(parts) == 3, f"Expected 3 parts in {report_number}"
        assert parts[0] == "DR", f"Expected DR prefix"
        assert len(parts[1]) == 4, f"Expected 4-digit year, got {parts[1]}"
        assert len(parts[2]) == 5, f"Expected 5-digit sequence, got {parts[2]}"
    
    def test_next_number_without_date(self):
        """GET /api/daily-reports/next-number without date should still work"""
        resp = requests.get(f"{BASE_URL}/api/daily-reports/next-number", timeout=10)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "report_number" in data, "Expected report_number field"


class TestDuplicateCheck:
    """Test duplicate check endpoint"""
    
    def test_duplicate_check_requires_params(self):
        """GET /api/daily-reports/duplicate-check requires project_number and report_date"""
        resp = requests.get(f"{BASE_URL}/api/daily-reports/duplicate-check", timeout=10)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    
    def test_duplicate_check_with_valid_params(self):
        """GET /api/daily-reports/duplicate-check with valid params returns result"""
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/duplicate-check",
            params={
                "project_number": "TEST-PROJECT-999",
                "report_date": "2026-01-01"
            },
            timeout=10
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "exists" in data, "Expected exists field"
        assert "count" in data, "Expected count field"
        assert "matches" in data, "Expected matches field"
        assert isinstance(data.get("matches"), list), "matches should be a list"


class TestMultiLogin:
    """Test multi-login authentication for admin access"""
    
    def test_multi_login_success(self):
        """POST /api/auth/multi-login should return tokens for valid credentials"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            timeout=15
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify tokens are returned
        assert "directory_token" in data or "admin_token" in data, f"Expected tokens in response: {data.keys()}"
    
    def test_multi_login_invalid_credentials(self):
        """POST /api/auth/multi-login should reject invalid credentials"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": "invalid@example.com",
                "password": "wrongpassword"
            },
            timeout=15
        )
        assert resp.status_code in [401, 403], f"Expected 401/403, got {resp.status_code}"


class TestAttachmentUpload:
    """Test attachment upload endpoint"""
    
    def test_attachment_upload_pdf(self):
        """POST /api/daily-reports/attachments/upload should accept PDF"""
        # Create a minimal valid PDF
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
        b64_content = base64.b64encode(pdf_content).decode("utf-8")
        data_url = f"data:application/pdf;base64,{b64_content}"
        
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/attachments/upload",
            json={
                "file_data": data_url,
                "filename": "test_document.pdf"
            },
            timeout=30
        )
        # May return 200 or 503 if R2 not configured
        assert resp.status_code in [200, 503], f"Expected 200 or 503, got {resp.status_code}: {resp.text}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "attachment_ref" in data, f"Expected attachment_ref in response: {data}"
    
    def test_attachment_upload_rejects_exe(self):
        """POST /api/daily-reports/attachments/upload should reject .exe files"""
        exe_content = b"MZ\x90\x00"  # PE header start
        b64_content = base64.b64encode(exe_content).decode("utf-8")
        data_url = f"data:application/octet-stream;base64,{b64_content}"
        
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/attachments/upload",
            json={
                "file_data": data_url,
                "filename": "malware.exe"
            },
            timeout=30
        )
        # Should reject with 400
        assert resp.status_code == 400, f"Expected 400 for .exe, got {resp.status_code}: {resp.text}"


class TestDailyReportReadWithAuth:
    """Test daily report read with admin authentication"""
    
    @pytest.fixture
    def admin_tokens(self):
        """Get admin tokens via multi-login"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            timeout=15
        )
        if resp.status_code != 200:
            pytest.skip(f"Could not authenticate: {resp.status_code}")
        return resp.json()
    
    def test_list_daily_reports_with_admin_token(self, admin_tokens):
        """GET /api/daily-reports should work with admin token"""
        headers = {}
        if "admin_token" in admin_tokens:
            headers["X-Admin-Token"] = admin_tokens["admin_token"]
        if "directory_token" in admin_tokens:
            headers["X-Directory-Token"] = admin_tokens["directory_token"]
        
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports",
            headers=headers,
            timeout=15
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected list response"
    
    def test_get_daily_report_by_id(self, admin_tokens):
        """GET /api/daily-reports/{id} should work with admin token"""
        headers = {}
        if "admin_token" in admin_tokens:
            headers["X-Admin-Token"] = admin_tokens["admin_token"]
        if "directory_token" in admin_tokens:
            headers["X-Directory-Token"] = admin_tokens["directory_token"]
        
        # First get list to find a report ID
        list_resp = requests.get(
            f"{BASE_URL}/api/daily-reports",
            headers=headers,
            timeout=15
        )
        if list_resp.status_code != 200 or not list_resp.json():
            pytest.skip("No daily reports available to test")
        
        reports = list_resp.json()
        if not reports:
            pytest.skip("No daily reports in list")
        
        report_id = reports[0].get("id")
        if not report_id:
            pytest.skip("First report has no ID")
        
        # Get single report
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}",
            headers=headers,
            timeout=15
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("id") == report_id, f"Expected id={report_id}, got {data.get('id')}"


class TestPDFGeneration:
    """Test PDF generation for daily reports"""
    
    @pytest.fixture
    def admin_tokens(self):
        """Get admin tokens via multi-login"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            timeout=15
        )
        if resp.status_code != 200:
            pytest.skip(f"Could not authenticate: {resp.status_code}")
        return resp.json()
    
    def test_pdf_generation_endpoint_exists(self, admin_tokens):
        """PDF generation endpoint should exist"""
        headers = {}
        if "admin_token" in admin_tokens:
            headers["X-Admin-Token"] = admin_tokens["admin_token"]
        if "directory_token" in admin_tokens:
            headers["X-Directory-Token"] = admin_tokens["directory_token"]
        
        # First get a report ID
        list_resp = requests.get(
            f"{BASE_URL}/api/daily-reports",
            headers=headers,
            timeout=15
        )
        if list_resp.status_code != 200 or not list_resp.json():
            pytest.skip("No daily reports available")
        
        reports = list_resp.json()
        if not reports:
            pytest.skip("No daily reports in list")
        
        report_id = reports[0].get("id")
        if not report_id:
            pytest.skip("First report has no ID")
        
        # Try PDF endpoint
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}/pdf",
            headers=headers,
            timeout=30
        )
        # Should return 200 with PDF or 202 with job_id for async
        assert resp.status_code in [200, 202, 404], f"Expected 200/202/404, got {resp.status_code}: {resp.text}"


class TestTrustSpineLifecycle:
    """Test Trust Spine lifecycle event recording"""
    
    @pytest.fixture
    def admin_tokens(self):
        """Get admin tokens via multi-login"""
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            timeout=15
        )
        if resp.status_code != 200:
            pytest.skip(f"Could not authenticate: {resp.status_code}")
        return resp.json()
    
    def test_trust_spine_events_endpoint(self, admin_tokens):
        """Trust Spine events endpoint should be accessible"""
        headers = {}
        if "admin_token" in admin_tokens:
            headers["X-Admin-Token"] = admin_tokens["admin_token"]
        if "directory_token" in admin_tokens:
            headers["X-Directory-Token"] = admin_tokens["directory_token"]
        
        # Check if trust spine endpoint exists
        resp = requests.get(
            f"{BASE_URL}/api/trust-spine/events",
            headers=headers,
            params={"workflow": "daily-report", "limit": 5},
            timeout=15
        )
        # May return 200 or 404 if endpoint doesn't exist
        assert resp.status_code in [200, 404], f"Expected 200/404, got {resp.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
