"""TRACK 27.10 · Daily Report Operational Excellence + PDF Certification
E2E API tests for the Hard Submission Gate and PDF generation.

Tests:
1. POST /api/daily-reports rejects payload missing approved summary (422)
2. POST /api/daily-reports accepts payload with approved summary metadata
3. GET /api/daily-reports/{id}/pdf returns valid PDF with single summary
4. GET /api/daily-reports/{id}/audit-footer returns audit envelope
"""
from __future__ import annotations

import os
import sys
import uuid

import pytest
import requests

sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

ONE_PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkAAIA"
    "AAoAAv/lxKUAAAAASUVORK5CYII="
)


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login."""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30,
        )
    except requests.RequestException as exc:
        pytest.skip(f"Admin login unavailable: {exc}")
    if resp.status_code != 200:
        pytest.skip(f"Admin login failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    token = data.get("portal_tokens", {}).get("admin")
    if not token:
        pytest.skip("No admin token in multi-login response")
    return token


@pytest.fixture(scope="module")
def api_client(admin_token):
    """Session with admin auth header."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-Admin-Token": admin_token,
        "X-Test-Rate-Limit-Bypass": "1",
    })
    return session


class TestDailyReportSummaryGate:
    """Test the Hard Submission Gate for Daily Reports."""

    def test_post_rejects_missing_approved_summary(self, api_client):
        """POST /api/daily-reports returns 422 when ai_accepted_summary is missing."""
        payload = {
            "project_name": "TEST_Track27_10_NoSummary",
            "project_number": "TEST-27-10-001",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Clear",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            # Missing ai_accepted_summary and ai_accepted_summary_meta
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "approved_summary_required", f"Unexpected error: {detail}"

    def test_post_rejects_missing_accepted_at(self, api_client):
        """POST /api/daily-reports returns 422 when accepted_at is missing from meta."""
        payload = {
            "project_name": "TEST_Track27_10_NoAcceptedAt",
            "project_number": "TEST-27-10-002",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Clear",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            "ai_accepted_summary": "Test summary text",
            "ai_accepted_summary_meta": {
                "source": "ai",
                "approved_by": "Test Supervisor",
                # Missing accepted_at
            },
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "approved_summary_metadata_required", f"Unexpected error: {detail}"

    def test_post_rejects_invalid_source(self, api_client):
        """POST /api/daily-reports returns 422 when source is invalid."""
        payload = {
            "project_name": "TEST_Track27_10_InvalidSource",
            "project_number": "TEST-27-10-003",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Clear",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            "ai_accepted_summary": "Test summary text",
            "ai_accepted_summary_meta": {
                "source": "invalid_source",  # Invalid
                "approved_by": "Test Supervisor",
                "accepted_at": "2026-01-15T19:00:00Z",
            },
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        detail = data.get("detail", {})
        assert detail.get("error") == "approved_summary_source_invalid", f"Unexpected error: {detail}"

    def test_post_accepts_ai_summary_with_valid_metadata(self, api_client):
        """POST /api/daily-reports succeeds with valid AI summary metadata."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "project_name": f"TEST_Track27_10_ValidAI_{unique_id}",
            "project_number": f"TEST-27-10-AI-{unique_id}",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Clear skies, 75°F",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            "ai_accepted_summary": "Crews completed curb prep and staging. No delays.",
            "ai_accepted_summary_meta": {
                "source": "ai",
                "approved_by": "Test Supervisor",
                "accepted_at": "2026-01-15T19:00:00Z",
            },
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        assert "id" in data, "Response should contain id"
        assert data.get("ai_accepted_summary") == payload["ai_accepted_summary"]
        # Store for cleanup
        self.__class__.created_ai_report_id = data.get("id")

    def test_post_accepts_manual_summary_with_valid_metadata(self, api_client):
        """POST /api/daily-reports succeeds with valid manual summary metadata."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "project_name": f"TEST_Track27_10_ValidManual_{unique_id}",
            "project_number": f"TEST-27-10-MAN-{unique_id}",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Partly cloudy, 72°F",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            "ai_accepted_summary": "Supervisor-written summary: Work completed as planned.",
            "ai_accepted_summary_meta": {
                "source": "manual",
                "approved_by": "Test Supervisor",
                "accepted_at": "2026-01-15T19:30:00Z",
            },
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        assert "id" in data, "Response should contain id"
        assert data.get("ai_accepted_summary") == payload["ai_accepted_summary"]
        # Store for PDF test
        self.__class__.created_manual_report_id = data.get("id")

    def test_post_accepts_edited_summary_with_valid_metadata(self, api_client):
        """POST /api/daily-reports succeeds with valid edited summary metadata."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "project_name": f"TEST_Track27_10_ValidEdited_{unique_id}",
            "project_number": f"TEST-27-10-EDT-{unique_id}",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Overcast, 68°F",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            "ai_accepted_summary": "AI-generated then edited: Work completed with minor adjustments.",
            "ai_accepted_summary_meta": {
                "source": "edited",
                "approved_by": "Test Supervisor",
                "accepted_at": "2026-01-15T20:00:00Z",
                "edited_by_supervisor": True,
            },
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        assert "id" in data, "Response should contain id"
        self.__class__.created_edited_report_id = data.get("id")

    def test_post_accepts_fallback_summary_with_valid_metadata(self, api_client):
        """POST /api/daily-reports succeeds with valid fallback summary metadata."""
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "project_name": f"TEST_Track27_10_ValidFallback_{unique_id}",
            "project_number": f"TEST-27-10-FB-{unique_id}",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Rain, 65°F",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            "ai_accepted_summary": "Fallback summary: Daily activity recorded.",
            "ai_accepted_summary_meta": {
                "source": "fallback",
                "approved_by": "Test Supervisor",
                "accepted_at": "2026-01-15T20:30:00Z",
            },
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        assert "id" in data, "Response should contain id"
        self.__class__.created_fallback_report_id = data.get("id")

    def test_post_persists_units_and_equipment_run_idle_fields(self, api_client):
        unique_id = str(uuid.uuid4())[:8]
        payload = {
            "project_name": f"TEST_Track27_10_Parity_{unique_id}",
            "project_number": f"TEST-27-10-PAR-{unique_id}",
            "location": "Test Location",
            "report_date": "2026-01-15",
            "prepared_by": "Test Supervisor",
            "weather_summary": "Clear skies, 75°F",
            "photos": [ONE_PX] * 6,
            "prepared_by_signature": ONE_PX,
            "ai_accepted_summary": "Parity test summary.",
            "ai_accepted_summary_meta": {
                "source": "manual",
                "approved_by": "Test Supervisor",
                "accepted_at": "2026-01-15T21:00:00Z",
            },
            "production": [{
                "description": "Curb",
                "quantity": 67,
                "unit": "LF",
                "unit_snapshot": "Linear Feet",
            }],
            "materials": [{
                "description": "Stone",
                "quantity": 12,
                "unit": "TON",
                "unit_snapshot": "Tons",
            }],
            "outbound_materials": [{
                "material": "Spoils",
                "quantity": 4,
                "unit": "OTHER",
                "unit_snapshot": "Loads",
            }],
            "equipment": [{
                "description": "CAT 320",
                "run_time": 6.5,
                "idle_time": 1.25,
            }],
        }
        resp = api_client.post(f"{BASE_URL}/api/daily-reports", json=payload, timeout=30)
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text[:500]}"
        data = resp.json()
        assert data["production"][0]["unit"] == "LF"
        assert data["production"][0].get("custom_unit_label") == "Linear Feet"
        assert data["materials"][0]["unit"] == "TON"
        assert data["materials"][0].get("custom_unit_label") == "Tons"
        assert data["outbound_materials"][0]["unit"] == "OTHER"
        assert data["outbound_materials"][0].get("custom_unit_label") == "Loads"
        assert data["equipment"][0].get("hours_used") == 6.5
        assert data["equipment"][0].get("idle_hours") == 1.25
        assert data["equipment"][0].get("run_time") == 6.5
        assert data["equipment"][0].get("idle_time") == 1.25


class TestDailyReportPDF:
    """Test PDF generation for Daily Reports."""

    def test_pdf_endpoint_returns_valid_pdf(self, api_client):
        """GET /api/daily-reports/{id}/pdf returns a valid PDF."""
        # First, get a list of daily reports to find one with an ID
        resp = api_client.get(f"{BASE_URL}/api/daily-reports", timeout=15)
        assert resp.status_code == 200, f"Failed to list daily reports: {resp.status_code}"
        reports = resp.json()
        if not reports:
            pytest.skip("No daily reports available for PDF test")
        
        report_id = reports[0].get("id")
        if not report_id:
            pytest.skip("First report has no id")
        
        # Fetch the PDF
        pdf_resp = api_client.get(f"{BASE_URL}/api/daily-reports/{report_id}/pdf", timeout=30)
        assert pdf_resp.status_code == 200, f"PDF fetch failed: {pdf_resp.status_code} {pdf_resp.text[:200]}"
        
        # Verify it's a PDF
        content = pdf_resp.content
        assert content[:4] == b"%PDF", "Response should start with %PDF magic bytes"
        
        # Check content type
        content_type = pdf_resp.headers.get("Content-Type", "")
        assert "pdf" in content_type.lower(), f"Content-Type should be PDF, got: {content_type}"

    def test_audit_footer_endpoint_returns_envelope(self, api_client):
        """GET /api/daily-reports/{id}/audit-footer returns audit envelope."""
        # Get a report ID
        resp = api_client.get(f"{BASE_URL}/api/daily-reports", timeout=15)
        assert resp.status_code == 200
        reports = resp.json()
        if not reports:
            pytest.skip("No daily reports available")
        
        report_id = reports[0].get("id")
        
        # Fetch audit footer
        footer_resp = api_client.get(f"{BASE_URL}/api/daily-reports/{report_id}/audit-footer", timeout=15)
        assert footer_resp.status_code == 200, f"Audit footer failed: {footer_resp.status_code}"
        
        data = footer_resp.json()
        assert "sha256" in data, "Audit footer should contain sha256"
        assert "doc_id" in data, "Audit footer should contain doc_id"
        assert "rendered_at_utc" in data, "Audit footer should contain rendered_at_utc"
        assert "footer_text" in data, "Audit footer should contain footer_text"


class TestDailyReportList:
    """Test Daily Report listing and retrieval."""

    def test_list_daily_reports(self, api_client):
        """GET /api/daily-reports returns a list."""
        resp = api_client.get(f"{BASE_URL}/api/daily-reports", timeout=15)
        assert resp.status_code == 200, f"List failed: {resp.status_code}"
        data = resp.json()
        assert isinstance(data, list), "Response should be a list"

    def test_get_single_daily_report(self, api_client):
        """GET /api/daily-reports/{id} returns a single report."""
        # Get a report ID first
        resp = api_client.get(f"{BASE_URL}/api/daily-reports", timeout=15)
        assert resp.status_code == 200
        reports = resp.json()
        if not reports:
            pytest.skip("No daily reports available")
        
        report_id = reports[0].get("id")
        
        # Fetch single report
        detail_resp = api_client.get(f"{BASE_URL}/api/daily-reports/{report_id}", timeout=15)
        assert detail_resp.status_code == 200, f"Detail fetch failed: {detail_resp.status_code}"
        
        data = detail_resp.json()
        assert data.get("id") == report_id, "Returned report should match requested ID"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
