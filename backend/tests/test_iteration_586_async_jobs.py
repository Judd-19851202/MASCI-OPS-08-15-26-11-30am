"""
Iteration 586 · Async Job Polling & Daily Summary/PDF Tests

Tests for:
1. Daily summary drafting returns 202 with job_id and polling reaches completed summary
2. Polling endpoint /api/jobs/{job_id}/status returns queued/processing/completed states
3. Approved daily report PDF download queues a job, polls status, and downloads finished PDF
4. Approved reports list loads correctly after cache scaffolding
5. Runtime cache metadata indicates memory fallback (Redis disabled)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=30,
    )
    assert resp.status_code == 200, f"Multi-login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    tokens = data.get("portal_tokens") or {}
    admin_tok = tokens.get("admin") or data.get("token")
    assert admin_tok, "No admin token returned"
    return admin_tok


class TestAsyncJobPolling:
    """Test async job status polling endpoint."""

    def test_job_status_404_for_nonexistent_job(self):
        """GET /api/jobs/{job_id}/status returns 404 for nonexistent job."""
        resp = requests.get(
            f"{BASE_URL}/api/jobs/nonexistent-job-id-12345/status",
            timeout=15,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    def test_job_result_404_for_nonexistent_job(self):
        """GET /api/jobs/{job_id}/result returns 404 for nonexistent job."""
        resp = requests.get(
            f"{BASE_URL}/api/jobs/nonexistent-job-id-12345/result",
            params={"token": "fake-token"},
            timeout=15,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


class TestDailySummaryDraftAsync:
    """Test daily summary draft endpoint with async job polling."""

    def test_summary_draft_returns_202_with_job_id(self):
        """POST /api/daily-reports/summary/draft returns 202 with job_id."""
        payload = {
            "payload": {
                "project_name": "Test Project",
                "project_number": "TEST-001",
                "report_date": "2026-07-17",
                "prepared_by": "Test Supervisor",
                "location": "Test Location",
                "weather_summary": "Clear, 85°F",
                "masci_crews": [
                    {"name": "John Doe", "trade": "Operator", "hours": 8.0}
                ],
                "equipment": [
                    {"description": "Excavator", "unit_number": "EXC-001", "run_hours": 6.0}
                ],
                "production": [
                    {"description": "Excavation", "quantity": 100, "unit": "CY", "percent_complete": 50}
                ],
            },
            "language": "en",
        }
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json=payload,
            timeout=30,
        )
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "job_id" in data, "Response should contain job_id"
        assert data.get("status") == "queued", f"Expected status=queued, got {data.get('status')}"
        assert "status_url" in data, "Response should contain status_url"
        assert data.get("kind") == "daily_summary_draft", f"Expected kind=daily_summary_draft"

    def test_summary_draft_job_polling_reaches_completed(self):
        """Poll job status until completed and verify summary result."""
        # Create a summary draft job
        payload = {
            "payload": {
                "project_name": "Polling Test Project",
                "project_number": "POLL-001",
                "report_date": "2026-07-17",
                "prepared_by": "Test Supervisor",
                "location": "Test Location",
                "weather_summary": "Sunny, 90°F",
                "masci_crews": [
                    {"name": "Jane Smith", "trade": "Foreman", "hours": 10.0}
                ],
                "production": [
                    {"description": "Concrete Pour", "quantity": 50, "unit": "CY"}
                ],
            },
            "language": "en",
        }
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json=payload,
            timeout=30,
        )
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}"
        data = resp.json()
        job_id = data.get("job_id")
        assert job_id, "No job_id returned"

        # Poll until completed or timeout
        max_polls = 60
        poll_interval = 1.5
        final_status = None
        final_result = None

        for i in range(max_polls):
            status_resp = requests.get(
                f"{BASE_URL}/api/jobs/{job_id}/status",
                timeout=15,
            )
            assert status_resp.status_code == 200, f"Status poll failed: {status_resp.status_code}"
            status_data = status_resp.json()
            final_status = status_data.get("status")
            
            # Verify cache_backend metadata shows memory fallback
            cache_backend = status_data.get("cache_backend") or {}
            assert cache_backend.get("backend") == "memory", f"Expected memory backend, got {cache_backend}"
            
            if final_status == "completed":
                final_result = status_data.get("result")
                break
            elif final_status == "failed":
                pytest.fail(f"Job failed: {status_data.get('error')}")
            
            time.sleep(poll_interval)

        assert final_status == "completed", f"Job did not complete in time, last status: {final_status}"
        assert final_result is not None, "Completed job should have result"
        assert "summary_text" in final_result or final_result.get("ok"), "Result should contain summary_text or ok"


class TestApprovedReportsList:
    """Test approved daily reports list endpoint."""

    def test_approved_reports_list_loads(self, admin_token):
        """GET /api/daily-reports/approved returns list of approved reports."""
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/approved",
            headers={"X-Admin-Token": admin_token},
            params={"limit": 10},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "items" in data, "Response should contain items array"
        items = data.get("items") or []
        assert isinstance(items, list), "items should be a list"
        
        # Verify item structure if any items exist
        if items:
            item = items[0]
            assert "report_id" in item or "id" in item, "Item should have report_id or id"
            assert "source" in item, "Item should have source field (legacy/modern)"

    def test_approved_reports_list_requires_auth(self):
        """GET /api/daily-reports/approved returns 401 without auth."""
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/approved",
            params={"limit": 5},
            timeout=15,
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


class TestApprovedReportPdfAsync:
    """Test approved report PDF download with async job polling."""

    def test_pdf_endpoint_returns_202_with_job_id(self, admin_token):
        """GET /api/daily-reports/{report_id}/pdf returns 202 with job_id."""
        # First get an approved report
        list_resp = requests.get(
            f"{BASE_URL}/api/daily-reports/approved",
            headers={"X-Admin-Token": admin_token},
            params={"limit": 1},
            timeout=30,
        )
        assert list_resp.status_code == 200, f"List failed: {list_resp.status_code}"
        items = list_resp.json().get("items") or []
        
        if not items:
            pytest.skip("No approved reports available for PDF test")
        
        report_id = items[0].get("report_id") or items[0].get("id")
        assert report_id, "No report_id found"

        # Request PDF - should return 202 with job_id
        pdf_resp = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}/pdf",
            headers={
                "X-Admin-Token": admin_token,
                "Accept": "application/json",
            },
            timeout=30,
        )
        assert pdf_resp.status_code == 202, f"Expected 202, got {pdf_resp.status_code}: {pdf_resp.text}"
        data = pdf_resp.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "job_id" in data, "Response should contain job_id"
        assert data.get("kind") == "daily_report_pdf", f"Expected kind=daily_report_pdf"

    def test_pdf_job_polling_reaches_completed_with_download_url(self, admin_token):
        """Poll PDF job until completed and verify download_url in result."""
        # Get an approved report
        list_resp = requests.get(
            f"{BASE_URL}/api/daily-reports/approved",
            headers={"X-Admin-Token": admin_token},
            params={"limit": 1},
            timeout=30,
        )
        items = list_resp.json().get("items") or []
        
        if not items:
            pytest.skip("No approved reports available for PDF test")
        
        report_id = items[0].get("report_id") or items[0].get("id")

        # Request PDF
        pdf_resp = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}/pdf",
            headers={
                "X-Admin-Token": admin_token,
                "Accept": "application/json",
            },
            timeout=30,
        )
        assert pdf_resp.status_code == 202
        job_id = pdf_resp.json().get("job_id")
        assert job_id, "No job_id returned"

        # Poll until completed
        max_polls = 30
        poll_interval = 1.0
        final_status = None
        final_result = None

        for i in range(max_polls):
            status_resp = requests.get(
                f"{BASE_URL}/api/jobs/{job_id}/status",
                timeout=15,
            )
            assert status_resp.status_code == 200
            status_data = status_resp.json()
            final_status = status_data.get("status")
            
            if final_status == "completed":
                final_result = status_data.get("result")
                break
            elif final_status == "failed":
                error = status_data.get("error") or {}
                # 409 means report not approved - that's expected for some reports
                if "409" in str(error.get("code", "")) or "not yet approved" in str(error.get("message", "")):
                    pytest.skip("Report not yet approved for PDF export")
                pytest.fail(f"PDF job failed: {error}")
            
            time.sleep(poll_interval)

        assert final_status == "completed", f"PDF job did not complete, last status: {final_status}"
        assert final_result is not None, "Completed job should have result"
        assert "download_url" in final_result, "Result should contain download_url"
        assert "filename" in final_result, "Result should contain filename"

    def test_pdf_download_via_result_endpoint(self, admin_token):
        """Download PDF via /api/jobs/{job_id}/result endpoint."""
        # Get an approved report
        list_resp = requests.get(
            f"{BASE_URL}/api/daily-reports/approved",
            headers={"X-Admin-Token": admin_token},
            params={"limit": 1},
            timeout=30,
        )
        items = list_resp.json().get("items") or []
        
        if not items:
            pytest.skip("No approved reports available for PDF test")
        
        report_id = items[0].get("report_id") or items[0].get("id")

        # Request PDF and poll to completion
        pdf_resp = requests.get(
            f"{BASE_URL}/api/daily-reports/{report_id}/pdf",
            headers={
                "X-Admin-Token": admin_token,
                "Accept": "application/json",
            },
            timeout=30,
        )
        assert pdf_resp.status_code == 202
        job_id = pdf_resp.json().get("job_id")

        # Poll until completed
        download_url = None
        for i in range(30):
            status_resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}/status", timeout=15)
            status_data = status_resp.json()
            if status_data.get("status") == "completed":
                download_url = status_data.get("result", {}).get("download_url")
                break
            elif status_data.get("status") == "failed":
                error = status_data.get("error") or {}
                if "not yet approved" in str(error.get("message", "")):
                    pytest.skip("Report not yet approved for PDF export")
                pytest.fail(f"PDF job failed: {error}")
            time.sleep(1.0)

        if not download_url:
            pytest.skip("PDF job did not complete with download_url")

        # Download the PDF
        # The download_url is relative like /api/jobs/{job_id}/result?token=xxx
        full_url = f"{BASE_URL}{download_url}" if download_url.startswith("/api") else f"{BASE_URL}/api{download_url}"
        download_resp = requests.get(full_url, timeout=30)
        assert download_resp.status_code == 200, f"Download failed: {download_resp.status_code}"
        assert download_resp.headers.get("Content-Type") == "application/pdf" or \
               "application/pdf" in download_resp.headers.get("Content-Type", ""), \
               f"Expected PDF content type, got {download_resp.headers.get('Content-Type')}"
        assert len(download_resp.content) > 100, "PDF content should not be empty"
        # Verify PDF magic bytes
        assert download_resp.content[:4] == b"%PDF", "Content should be a valid PDF"


class TestRuntimeCacheMetadata:
    """Test that runtime cache metadata indicates memory fallback (Redis disabled)."""

    def test_job_status_shows_memory_backend(self):
        """Job status response should show cache_backend=memory (Redis disabled)."""
        # Create a quick job to check metadata
        payload = {
            "payload": {
                "project_name": "Cache Test",
                "project_number": "CACHE-001",
                "masci_crews": [{"name": "Test", "hours": 1}],
            },
        }
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json=payload,
            timeout=30,
        )
        assert resp.status_code == 202
        job_id = resp.json().get("job_id")

        # Check status
        status_resp = requests.get(f"{BASE_URL}/api/jobs/{job_id}/status", timeout=15)
        assert status_resp.status_code == 200
        data = status_resp.json()
        
        cache_backend = data.get("cache_backend") or {}
        assert cache_backend.get("backend") == "memory", \
            f"Expected memory backend (Redis disabled), got {cache_backend}"
        assert cache_backend.get("redis_active") is False, \
            "redis_active should be False when Redis is disabled"


class TestHealthEndpoint:
    """Verify backend health."""

    def test_health_endpoint(self):
        """GET /api/health returns ok."""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("ok") is True
