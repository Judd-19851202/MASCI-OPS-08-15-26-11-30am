"""
TRACK Voice-to-Report, Watchdog Conflict Detection, and Async Job Polling Tests

Tests for:
1. POST /api/transcribe - Voice transcription endpoint
2. POST /api/daily-reports - Watchdog conflict detection on submit
3. GET /api/daily-reports.csv - Async job polling pattern (202 + job_id)
4. Photo intelligence status in draft responses
"""
import os
import pytest
import requests
import io
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")

# ── Test credentials ──
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
        timeout=60,
    )
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code}")
    data = resp.json()
    token = data.get("portal_tokens", {}).get("admin") or data.get("token")
    if not token:
        pytest.skip("No admin token in response")
    return token


class TestTranscribeEndpoint:
    """Tests for POST /api/transcribe voice transcription endpoint."""

    def test_transcribe_endpoint_exists(self):
        """Verify /api/transcribe endpoint exists and rejects empty requests."""
        # Send empty request - should get 422 (validation error) not 404
        resp = requests.post(f"{BASE_URL}/api/transcribe", timeout=30)
        # 422 = endpoint exists but validation failed (no audio file)
        # 400 = bad request
        # 404 = endpoint doesn't exist
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"
        print(f"Transcribe endpoint exists, returns {resp.status_code} for empty request")
        
        # Verify error mentions audio field
        data = resp.json()
        assert "detail" in data, "Response missing detail field"
        detail_str = str(data["detail"])
        assert "audio" in detail_str.lower(), f"Error should mention 'audio' field: {detail_str}"

    def test_transcribe_requires_audio_file(self):
        """Verify /api/transcribe requires audio file upload."""
        # Send form data without audio file
        resp = requests.post(
            f"{BASE_URL}/api/transcribe",
            data={"field_hint": "work_performed", "language_hint": "auto"},
            timeout=30,
        )
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        print(f"Transcribe correctly requires audio file: {resp.status_code}")


class TestDailyReportWatchdog:
    """Tests for Watchdog Conflict Detection on Daily Report submit."""

    def test_daily_report_submit_includes_watchdog(self, admin_token):
        """Verify POST /api/daily-reports returns conflict_watchdog metadata."""
        # Create a minimal valid daily report payload
        payload = {
            "project_name": "Test Project for Watchdog",
            "project_number": "TEST-WATCHDOG-001",
            "location": "Test Location",
            "report_date": "2026-07-17",
            "prepared_by": "Test Supervisor",
            "superintendent": "Test Super",
            "weather_summary": "Clear skies",
            "masci_crews": [{"name": "Test Worker", "trade": "Laborer", "hours": 8}],
            "activities": [{"description": "Test activity for watchdog testing"}],
            "production": [{"description": "Test production", "quantity": 100, "unit": "LF"}],
            "photos": [],
            "ai_accepted_summary": "Test summary for watchdog verification.",
            "ai_accepted_summary_meta": {
                "source": "manual",
                "accepted_at": "2026-07-17T12:00:00Z",
            },
            "narrative_sections": {
                "work_completed": "Test work completed",
                "tomorrow_plan": "Test tomorrow plan",
            },
            "certification_record": True,  # Mark as test record
            "synthetic_record": True,
        }
        
        headers = {"X-Admin-Token": admin_token}
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports",
            json=payload,
            headers=headers,
            timeout=60,
        )
        
        # Should succeed
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify conflict_watchdog is present
        assert "conflict_watchdog" in data, "Response missing conflict_watchdog field"
        watchdog = data["conflict_watchdog"]
        
        # Verify watchdog structure
        assert "has_conflicts" in watchdog, "Watchdog missing has_conflicts"
        assert "requires_pm_review" in watchdog, "Watchdog missing requires_pm_review"
        assert "schedule_source" in watchdog, "Watchdog missing schedule_source"
        assert "yesterday_report" in watchdog, "Watchdog missing yesterday_report"
        assert "conflicts" in watchdog, "Watchdog missing conflicts"
        assert "checked_at" in watchdog, "Watchdog missing checked_at"
        
        print(f"Watchdog metadata present: has_conflicts={watchdog['has_conflicts']}, conflicts={len(watchdog['conflicts'])}")


class TestAsyncJobPolling:
    """Tests for async HTTP 202 job polling pattern."""

    def test_daily_reports_csv_returns_202(self, admin_token):
        """Verify GET /api/daily-reports.csv returns 202 with job_id."""
        headers = {"X-Admin-Token": admin_token}
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports.csv",
            headers=headers,
            timeout=30,
        )
        
        # Should return 202 Accepted with job envelope
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify job envelope structure
        assert "job_id" in data, "Response missing job_id"
        assert "status" in data, "Response missing status"
        assert "status_url" in data, "Response missing status_url"
        
        job_id = data["job_id"]
        status = data["status"]
        
        print(f"CSV export job created: job_id={job_id}, status={status}")
        
        # Verify status is queued or processing
        assert status in ("queued", "processing", "completed"), f"Unexpected status: {status}"

    def test_job_status_polling(self, admin_token):
        """Verify job status polling endpoint works."""
        headers = {"X-Admin-Token": admin_token}
        
        # First create a job
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports.csv",
            headers=headers,
            timeout=30,
        )
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]
        
        # Poll for status
        max_polls = 10
        poll_interval = 1.5
        final_status = None
        
        for i in range(max_polls):
            status_resp = requests.get(
                f"{BASE_URL}/api/jobs/{job_id}/status",
                headers=headers,
                timeout=30,
            )
            assert status_resp.status_code == 200, f"Status poll failed: {status_resp.status_code}"
            status_data = status_resp.json()
            final_status = status_data.get("status")
            
            print(f"Poll {i+1}: status={final_status}")
            
            if final_status == "completed":
                # Verify completed response has download_url
                result = status_data.get("result", {})
                assert "download_url" in result, "Completed job missing download_url in result"
                print(f"Job completed! download_url present")
                break
            elif final_status == "failed":
                print(f"Job failed: {status_data.get('error')}")
                break
            
            time.sleep(poll_interval)
        
        assert final_status in ("completed", "failed"), f"Job did not complete in time: {final_status}"

    def test_job_status_404_for_nonexistent(self, admin_token):
        """Verify job status returns 404 for nonexistent job."""
        headers = {"X-Admin-Token": admin_token}
        resp = requests.get(
            f"{BASE_URL}/api/jobs/nonexistent-job-id-12345/status",
            headers=headers,
            timeout=30,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("Job status correctly returns 404 for nonexistent job")


class TestPhotoIntelligenceStatus:
    """Tests for per-photo status in draft responses."""

    def test_photo_intelligence_draft_endpoint(self, admin_token):
        """Verify photo intelligence draft endpoint exists and returns status."""
        headers = {"X-Admin-Token": admin_token}
        
        # Test with empty payload
        payload = {
            "form_key": "test-form-key-12345",
            "payload": {
                "photos": [],
                "project_number": "TEST-001",
            },
            "force": False,
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/photo-intelligence/draft",
            json=payload,
            headers=headers,
            timeout=30,
        )
        
        # Should succeed
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert "status" in data or "lifecycle_status" in data, "Response missing status field"
        assert "photo_count" in data, "Response missing photo_count"
        assert "photo_statuses" in data, "Response missing photo_statuses array"
        
        status = data.get("status") or data.get("lifecycle_status")
        print(f"Photo intelligence draft status: {status}, photo_count: {data.get('photo_count')}")
        
        # With no photos, should be "no_photos"
        assert status == "no_photos", f"Expected 'no_photos' status, got: {status}"


class TestDailySummaryDraftAsync:
    """Tests for async daily summary draft endpoint."""

    def test_summary_draft_returns_job_or_result(self, admin_token):
        """Verify summary draft endpoint returns job_id or direct result."""
        headers = {"X-Admin-Token": admin_token}
        
        payload = {
            "payload": {
                "project_name": "Test Project",
                "project_number": "TEST-001",
                "report_date": "2026-07-17",
                "prepared_by": "Test Supervisor",
                "weather_summary": "Clear",
                "masci_crews": [{"name": "Worker", "trade": "Laborer", "hours": 8}],
                "activities": [{"description": "Test activity"}],
            },
            "form_key": "test-summary-draft-key",
            "force": False,
        }
        
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json=payload,
            headers=headers,
            timeout=60,
        )
        
        # Should succeed with 200 (direct result) or 202 (job created)
        assert resp.status_code in (200, 202), f"Expected 200/202, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        if "job_id" in data:
            # Async job pattern
            assert "status" in data, "Job response missing status"
            print(f"Summary draft returned async job: {data.get('job_id')}, status={data.get('status')}")
        else:
            # Direct result
            print(f"Summary draft returned direct result: keys={list(data.keys())}")
            # Should have summary_text or enabled flag
            assert "summary_text" in data or "enabled" in data, "Response missing expected fields"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
