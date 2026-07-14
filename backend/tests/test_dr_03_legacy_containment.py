"""DR-03 Legacy Containment and Downstream Parity Tests.

Tests verify:
1. Legacy V2 write endpoints return 410 (retired)
2. Compatibility reads remain available
3. Canonical /api/daily-reports endpoint works
4. /api/dr-v2/meta returns read_only_compatibility: true
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestDR03LegacyWriteContainment:
    """Verify legacy V2 write endpoints are blocked with 410."""

    def test_dr_v2_drafts_post_returns_410(self):
        """POST /api/dr-v2/drafts should return 410 legacy retired."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/drafts",
            json={"report_id": "test-draft-123", "project_number": "TEST-001"},
            timeout=30,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail.get("error") == "legacy_daily_report_runtime_retired"
        assert detail.get("compat_mode") == "read_only"
        assert detail.get("canonical_route") == "/daily/submit"
        print("PASS: POST /api/dr-v2/drafts returns 410 with retirement message")

    def test_dr_v2_ai_synthesize_post_returns_410(self):
        """POST /api/dr-v2/ai/synthesize should return 410 legacy retired."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/ai/synthesize",
            json={"report_id": "test-draft-123"},
            timeout=30,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["detail"]["error"] == "legacy_daily_report_runtime_retired"
        print("PASS: POST /api/dr-v2/ai/synthesize returns 410")

    def test_dr_v2_ai_approve_post_returns_410(self):
        """POST /api/dr-v2/ai/approve should return 410 legacy retired."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/ai/approve",
            json={"report_id": "test-draft-123", "action": "accept"},
            timeout=15,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["detail"]["error"] == "legacy_daily_report_runtime_retired"
        print("PASS: POST /api/dr-v2/ai/approve returns 410")

    def test_dr_v2_canonicalize_post_returns_410(self):
        """POST /api/dr-v2/reports/{report_id}/canonicalize should return 410."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/reports/test-report-123/canonicalize",
            json={"draft": {}, "field_language": "es"},
            timeout=15,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["detail"]["error"] == "legacy_daily_report_runtime_retired"
        print("PASS: POST /api/dr-v2/reports/{id}/canonicalize returns 410")

    def test_dr_v2_photos_analyze_post_returns_410(self):
        """POST /api/dr-v2/photos/{photo_id}/analyze should return 410."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/photos/test-photo-123/analyze",
            json={"photo_id": "test-photo-123"},
            timeout=15,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["detail"]["error"] == "legacy_daily_report_runtime_retired"
        print("PASS: POST /api/dr-v2/photos/{id}/analyze returns 410")

    def test_dr_v2_photos_link_accept_returns_410(self):
        """POST /api/dr-v2/photos/{photo_id}/links/{link_id}/accept should return 410."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/photos/test-photo-123/links/link-456/accept",
            json={},
            timeout=15,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["detail"]["error"] == "legacy_daily_report_runtime_retired"
        print("PASS: POST /api/dr-v2/photos/{id}/links/{id}/accept returns 410")

    def test_dr_v2_photos_link_dismiss_returns_410(self):
        """POST /api/dr-v2/photos/{photo_id}/links/{link_id}/dismiss should return 410."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/photos/test-photo-123/links/link-456/dismiss",
            json={},
            timeout=15,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["detail"]["error"] == "legacy_daily_report_runtime_retired"
        print("PASS: POST /api/dr-v2/photos/{id}/links/{id}/dismiss returns 410")

    def test_dr_v2_photos_question_resolve_returns_410(self):
        """POST /api/dr-v2/photos/{photo_id}/questions/{question_id}/resolve should return 410."""
        resp = requests.post(
            f"{BASE_URL}/api/dr-v2/photos/test-photo-123/questions/q-789/resolve",
            json={"resolution": "test"},
            timeout=15,
        )
        assert resp.status_code == 410, f"Expected 410, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["detail"]["error"] == "legacy_daily_report_runtime_retired"
        print("PASS: POST /api/dr-v2/photos/{id}/questions/{id}/resolve returns 410")


class TestDR03CompatibilityReads:
    """Verify compatibility read endpoints remain available."""

    def test_dr_v2_meta_returns_read_only_compat(self):
        """GET /api/dr-v2/meta should return read_only_compatibility: true."""
        resp = requests.get(f"{BASE_URL}/api/dr-v2/meta", timeout=15)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("read_only_compatibility") is True
        assert data.get("legacy_writes_blocked") is True
        assert data.get("canonical_route") == "/daily/submit"
        assert data.get("canonical_api") == "/api/daily-reports"
        print(f"PASS: GET /api/dr-v2/meta returns read_only_compatibility=true, provider={data.get('provider')}")

    def test_dr_v2_drafts_get_returns_404_for_missing(self):
        """GET /api/dr-v2/drafts/{report_id} should return 404 for non-existent draft (not 410)."""
        resp = requests.get(f"{BASE_URL}/api/dr-v2/drafts/nonexistent-draft-xyz", timeout=15)
        # 404 means the read endpoint is still available, just no data
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
        print("PASS: GET /api/dr-v2/drafts/{id} returns 404 for missing (read still works)")

    def test_dr_v2_ai_audit_get_returns_empty_for_missing(self):
        """GET /api/dr-v2/ai/audit/{report_id} should return empty log for non-existent report."""
        resp = requests.get(f"{BASE_URL}/api/dr-v2/ai/audit/nonexistent-report-xyz", timeout=15)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("log") == []
        assert data.get("last_action") is None
        print("PASS: GET /api/dr-v2/ai/audit/{id} returns empty log for missing (read still works)")

    def test_dr_v2_photos_intelligence_get_returns_null_for_missing(self):
        """GET /api/dr-v2/photos/{photo_id}/intelligence should return null intel for missing."""
        resp = requests.get(f"{BASE_URL}/api/dr-v2/photos/nonexistent-photo-xyz/intelligence", timeout=15)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("intel") is None
        print("PASS: GET /api/dr-v2/photos/{id}/intelligence returns null for missing (read still works)")


class TestDR03CanonicalDailyReportsAPI:
    """Verify canonical /api/daily-reports endpoint works."""

    def test_daily_reports_list_endpoint_requires_auth(self):
        """GET /api/daily-reports requires auth (401 without token)."""
        resp = requests.get(f"{BASE_URL}/api/daily-reports?limit=1", timeout=15)
        # 401 is expected - endpoint requires admin or PM auth
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        print("PASS: GET /api/daily-reports returns 401 (auth required as expected)")

    def test_daily_reports_next_number_endpoint_available(self):
        """GET /api/daily-reports/next-number should return doc_id_preview."""
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/next-number?report_date=2026-07-14",
            timeout=15,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        # The endpoint returns doc_id_preview (not next_number)
        assert "doc_id_preview" in data or "next_number" in data
        preview = data.get("doc_id_preview") or data.get("next_number")
        print(f"PASS: GET /api/daily-reports/next-number returns preview={preview}")

    def test_daily_reports_duplicate_check_endpoint_available(self):
        """GET /api/daily-reports/duplicate-check should work."""
        resp = requests.get(
            f"{BASE_URL}/api/daily-reports/duplicate-check?project_number=TEST-001&report_date=2026-07-14",
            timeout=15,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "exists" in data
        print(f"PASS: GET /api/daily-reports/duplicate-check returns exists={data.get('exists')}")


class TestDR03DownstreamParity:
    """Verify downstream surfaces remain intact."""

    def test_jobs_recent_context_endpoint_available(self):
        """GET /api/jobs/{project_number}/recent-context should work (smart prefill)."""
        # This endpoint is used by the V3 shell for smart prefill
        resp = requests.get(
            f"{BASE_URL}/api/jobs/TEST-001/recent-context",
            timeout=15,
        )
        # 200 or 404 (no prior reports) are both valid - endpoint is available
        assert resp.status_code in (200, 404), f"Expected 200 or 404, got {resp.status_code}: {resp.text}"
        print(f"PASS: GET /api/jobs/{'{project}'}/recent-context returns {resp.status_code}")

    def test_cost_codes_for_project_endpoint_available(self):
        """GET /api/cost-codes/for-project should work."""
        resp = requests.get(
            f"{BASE_URL}/api/cost-codes/for-project?project_number=TEST-001",
            timeout=15,
        )
        # 200 is expected (may return empty codes list)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "codes" in data
        print(f"PASS: GET /api/cost-codes/for-project returns {len(data.get('codes', []))} codes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
