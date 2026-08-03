"""DR-03 Gate 5 E2E Tests - Live API verification.

Tests the Gate 5 repair items against the live preview API:
1. Summary draft endpoint returns canonical totals
2. No [object Object] in error responses
3. Manual summary fallback works
4. Daily Report viewer deep links resolve
5. Certification records excluded from dispatch
6. Photo-intelligence status is truthful
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    return data.get("portal_tokens", {}).get("admin", "")


@pytest.fixture(scope="module")
def dispatch_token():
    """Get dispatch token via multi-login."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        timeout=30,
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    data = resp.json()
    return data.get("portal_tokens", {}).get("dispatch", "")


class TestSummaryDraftEndpoint:
    """Test /api/daily-reports/summary/draft endpoint."""

    def test_returns_canonical_totals_for_live_fixture(self):
        """Verify summary_input totals match expected values."""
        payload = {
            "project_name": "D Curb Test",
            "project_number": "27-DR03",
            "report_date": "2026-07-15",
            "prepared_by": "Jaymn Judd",
            "masci_crews": [{
                "employee_id": "E-1",
                "name": "Crew One",
                "trade": "Concrete",
                "start_time": "06:00",
                "stop_time": "17:45",
                "lunch_minutes": 30,
            }],
            "subcontractors": [{"company": "Acme Concrete", "count": 1, "hours": 11}],
            "equipment": [{"description": "Skid Steer", "hours_used": 4, "idle_hours": 6}],
            "production": [{"description": "D curb", "quantity": 875, "unit": "LF", "percent_complete": 65}],
            "photos": ["a", "b", "c", "d", "e", "f"],
        }
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json={"payload": payload},
            timeout=30,
        )
        assert resp.status_code == 200, f"Draft failed: {resp.text}"
        data = resp.json()
        
        # Verify canonical totals
        summary_input = data.get("summary_input", {})
        assert summary_input["labor"]["employee_count"] == 1
        assert summary_input["labor"]["total_employee_hours"] == 11.25
        assert summary_input["subcontractors"]["subcontractor_count"] == 1
        assert summary_input["subcontractors"]["total_hours"] == 11.0
        assert summary_input["equipment"]["equipment_count"] == 1
        assert summary_input["equipment"]["total_run_hours"] == 4.0
        assert summary_input["equipment"]["total_idle_hours"] == 6.0
        assert summary_input["photos"]["photo_count"] == 6

    def test_no_object_object_in_response(self):
        """Verify no [object Object] in any response field."""
        payload = {"project_name": "Test", "masci_crews": [{"name": "Test"}]}
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json={"payload": payload},
            timeout=30,
        )
        assert resp.status_code == 200
        text = resp.text
        assert "[object Object]" not in text, "Found [object Object] in response"

    def test_ai_disabled_returns_reason_not_500(self):
        """When AI is disabled, endpoint returns reason_disabled, not 500."""
        payload = {"project_name": "Test"}
        resp = requests.post(
            f"{BASE_URL}/api/daily-reports/summary/draft",
            json={"payload": payload},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("ok") is True
        # AI is disabled in preview, so enabled should be False
        if not data.get("enabled"):
            assert data.get("reason_disabled"), "Missing reason_disabled when AI disabled"


class TestPhotoIntelligenceStatus:
    """Test photo-intelligence read behavior."""

    def test_no_photos_returns_no_photos_status(self):
        """When no photos, status should be 'no_photos'."""
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/nonexistent-id/photo-intelligence",
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") in ("no_photos", "not_requested"), f"Unexpected status: {data.get('status')}"

    def test_status_is_distinguishable(self):
        """Status should be a clear string, not empty or ambiguous."""
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/test-id/photo-intelligence",
            timeout=30,
        )
        assert resp.status_code == 200
        data = resp.json()
        status = data.get("status")
        assert status, "Status should not be empty"
        assert isinstance(status, str), "Status should be a string"
        assert status in ("no_photos", "not_requested", "pending", "complete_zero_observations", "complete_with_observations", "suppressed")


class TestDailyReportViewerDeepLink:
    """Test Daily Report viewer deep link resolution."""

    def test_resolve_endpoint_returns_governed_viewer_route(self, admin_token):
        """Verify /api/operational-records/resolve returns governed viewer route."""
        resp = requests.get(
            f"{BASE_URL}/api/operational-records/resolve/DR-2026-00001",
            headers={"X-Admin-Token": admin_token},
            timeout=30,
        )
        assert resp.status_code == 200, f"Resolve failed: {resp.text}"
        data = resp.json()
        assert data.get("record_kind") == "legacy_daily_report"
        assert data.get("viewer_route", "").startswith("/daily-reports/")


class TestCertificationRecordIsolation:
    """Test certification/synthetic record exclusion."""

    def test_dispatch_daily_reports_excludes_certification_records(self, dispatch_token):
        """Verify dispatch list excludes certification_record=true docs."""
        resp = requests.get(
            f"{BASE_URL}/api/dispatch/daily-reports?limit=100",
            headers={"X-Dispatch-Token": dispatch_token},
            timeout=30,
        )
        assert resp.status_code == 200, f"Dispatch list failed: {resp.text}"
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        
        # Check no certification records leaked through
        cert_records = [i for i in items if i.get("certification_record") is True]
        assert len(cert_records) == 0, f"Found {len(cert_records)} certification records in dispatch list"
        
        # Check no synthetic records leaked through
        synth_records = [i for i in items if i.get("synthetic_record") is True]
        assert len(synth_records) == 0, f"Found {len(synth_records)} synthetic records in dispatch list"


class TestReleaseIdentity:
    """Test release identity parity."""

    def test_frontend_backend_release_match(self):
        """Verify frontend and backend release hashes match."""
        resp = requests.get(f"{BASE_URL}/api/version", timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("frontend_backend_release_match") is True, "Release identity mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
