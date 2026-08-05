"""
WP-18C6 Operational Intelligence E2E API Tests
Tests PM and Admin C6 endpoints for operational intelligence:
- PM snapshot endpoint with full governance contract fields
- PM export endpoint returns CSV
- Admin overview returns snapshot
- Admin backfill route returns queued and subsequent overview returns backfill status
- Auth regression: PM login with X-PM-Token and Admin login with X-Admin-Token + X-Directory-Token
"""
import os
import time
import uuid
from pathlib import Path

import pytest
import requests


def _load_base_url() -> str:
    env_value = (os.environ.get("REACT_APP_BACKEND_URL") or "").strip().rstrip("/")
    if env_value:
        return env_value
    env_file = Path("/app/frontend/.env")
    if not env_file.exists():
        return ""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().strip('"').strip("'").rstrip("/")
    return ""


BASE_URL = _load_base_url()
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"


def _request_with_retry(method: str, url: str, **kwargs):
    attempts = int(kwargs.pop("attempts", 4))
    backoff_seconds = float(kwargs.pop("backoff_seconds", 2.0))
    last_response = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.request(method, url, **kwargs)
        except requests.RequestException:
            if attempt < attempts:
                time.sleep(backoff_seconds * attempt)
                continue
            raise
        last_response = response
        if response.status_code not in {502, 503, 504}:
            return response
        if attempt < attempts:
            time.sleep(backoff_seconds * attempt)
    return last_response


class TestWP18C6AuthRegression:
    """Regression tests for auth/session flow on C6 routes"""

    def test_pm_login_returns_token(self):
        """PM login via /api/pm/login returns a valid token"""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not configured")
        response = _request_with_retry(
            "POST",
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            headers={"X-Device-Id": f"wp18c6-pm-auth-{uuid.uuid4().hex[:8]}"},
            timeout=30,
        )
        assert response.status_code == 200, f"PM login failed: {response.text}"
        data = response.json()
        token = data.get("token") or data.get("pm_token")
        assert token, "PM login did not return a token"
        assert len(token) > 10, "PM token appears invalid"

    def test_admin_multi_login_returns_session_token(self):
        """Admin login via /api/auth/multi-login returns session_token for X-Directory-Token"""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not configured")
        response = _request_with_retry(
            "POST",
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": f"wp18c6-admin-auth-{uuid.uuid4().hex[:8]}"},
            timeout=30,
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        session_token = data.get("session_token") or data.get("directory_token")
        assert session_token, "Admin login did not return session_token"
        admin_token = (data.get("portal_tokens") or {}).get("admin") or data.get("admin_token") or data.get("token")
        assert admin_token, "Admin login did not return admin portal token"


class TestWP18C6PMOperationalIntelligence:
    """PM Operational Intelligence C6 endpoint tests"""

    @pytest.fixture(scope="class")
    def pm_headers(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not configured")
        response = _request_with_retry(
            "POST",
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            headers={"X-Device-Id": f"wp18c6-pm-headers-{uuid.uuid4().hex[:8]}"},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code}")
        token = response.json().get("token") or response.json().get("pm_token")
        return {"X-PM-Token": token}

    def test_pm_snapshot_returns_governed_payload(self, pm_headers):
        """PM snapshot endpoint returns governed snapshot with all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"PM snapshot failed: {response.text}"
        payload = response.json()
        
        # Verify top-level governance contract
        assert payload.get("metric_engine_authority") == "Governed Metric Engine"
        assert payload.get("operator_surface_label") == "Operational Intelligence"
        assert payload.get("engine_label") == "Production Intelligence Engine"
        assert payload.get("calculation_version") == "wp18c6.v1"
        
        # Verify authority contract
        authority = payload.get("authority_contract", {})
        assert authority.get("operators_see") == "Operational Intelligence"
        assert authority.get("architects_build") == "Production Intelligence Engine"
        assert authority.get("all_calculations_from") == "Governed Metric Engine"
        
        # Verify summary fields
        summary = payload.get("summary", {})
        assert "approved_events" in summary
        assert "review_queue_open" in summary
        assert "open_recommendations" in summary
        assert "orphan_events" in summary
        assert summary.get("manual_reporting_entries_added") == 0

    def test_pm_snapshot_metric_cards_have_full_governance_fields(self, pm_headers):
        """PM snapshot metric cards expose all governance contract fields"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200
        payload = response.json()
        
        metric_cards = payload.get("metric_cards", [])
        assert len(metric_cards) > 0, "No metric cards returned"
        
        # Check first metric card has all required governance fields
        metric = metric_cards[0]
        required_fields = [
            "metric_id", "label", "definition", "formula", "owner",
            "version", "value", "unit_label", "confidence",
            "calculation_timestamp", "freshness", "limitations",
            "source_records", "work_block_lineage", "supporting_evidence",
            "audit_trail", "lineage", "drilldown_path"
        ]
        for field in required_fields:
            assert field in metric, f"Metric card missing required field: {field}"
        
        # Verify freshness structure
        freshness = metric.get("freshness", {})
        assert "last_updated_at" in freshness
        assert "status" in freshness
        assert "calculation_version" in freshness
        
        # Verify audit trail structure
        audit = metric.get("audit_trail", {})
        assert audit.get("authority_collection") == "project_operational_intelligence_snapshots"

    def test_pm_snapshot_has_resource_productivity_tabs(self, pm_headers):
        """PM snapshot includes resource productivity for all resource types"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200
        payload = response.json()
        
        resources = payload.get("resource_productivity", {})
        expected_tabs = ["crews", "employees", "equipment", "materials", "vendors", "subcontractors"]
        for tab in expected_tabs:
            assert tab in resources, f"Missing resource tab: {tab}"

    def test_pm_snapshot_has_recommendations_and_review_queue(self, pm_headers):
        """PM snapshot includes recommendations and review queue sections"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200
        payload = response.json()
        
        assert "recommendations" in payload
        assert "review_queue" in payload
        assert isinstance(payload["recommendations"], list)
        assert isinstance(payload["review_queue"], list)

    def test_pm_export_returns_csv(self, pm_headers):
        """PM export endpoint returns CSV with correct headers"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence/export",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"PM export failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        
        lines = response.text.strip().split("\n")
        assert len(lines) > 0, "CSV is empty"
        header = lines[0].strip()
        assert header == "section,metric_id,label,value,unit,confidence,notes"

    def test_pm_snapshot_force_refresh_works(self, pm_headers):
        """PM snapshot with force_refresh=true rebuilds the snapshot"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence?force_refresh=true",
            headers=pm_headers,
            timeout=60,
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload.get("cache_status") == "rebuilt"


class TestWP18C6AdminOperationalIntelligence:
    """Admin Operational Intelligence C6 endpoint tests"""

    @pytest.fixture(scope="class")
    def admin_headers(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not configured")
        response = _request_with_retry(
            "POST",
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": f"wp18c6-admin-headers-{uuid.uuid4().hex[:8]}"},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        data = response.json()
        return {
            "X-Admin-Token": ((data.get("portal_tokens") or {}).get("admin") or data.get("admin_token") or data.get("token")),
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        }

    def test_admin_overview_without_project_returns_summary(self, admin_headers):
        """Admin overview without project_number returns summary and snapshots list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/overview",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"Admin overview failed: {response.text}"
        payload = response.json()
        
        # Verify summary structure
        summary = payload.get("summary", {})
        assert "projects_with_snapshots" in summary
        assert "open_review_items" in summary
        assert "open_recommendations" in summary
        assert "orphan_events" in summary
        
        # Verify backfill status is present
        assert "backfill" in payload
        backfill = payload.get("backfill", {})
        assert "status" in backfill

    def test_admin_overview_with_project_returns_snapshot(self, admin_headers):
        """Admin overview with project_number returns full governed snapshot"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/overview?project_number={TEST_PROJECT}",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"Admin overview with project failed: {response.text}"
        payload = response.json()
        
        # Verify snapshot is included
        assert "snapshot" in payload
        snapshot = payload.get("snapshot", {})
        assert snapshot.get("metric_engine_authority") == "Governed Metric Engine"
        assert snapshot.get("project_number") == TEST_PROJECT

    def test_admin_overview_force_refresh_rebuilds_snapshot(self, admin_headers):
        """Admin overview with force_refresh=true rebuilds the snapshot"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/overview?project_number={TEST_PROJECT}&force_refresh=true",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200
        payload = response.json()
        snapshot = payload.get("snapshot", {})
        assert snapshot.get("cache_status") == "rebuilt"

    def test_admin_backfill_returns_queued(self, admin_headers):
        """Admin backfill endpoint returns queued status immediately"""
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/backfill/run?force=true",
            headers=admin_headers,
            timeout=30,
        )
        assert response.status_code == 200, f"Admin backfill failed: {response.text}"
        payload = response.json()
        assert payload.get("ok") is True
        assert payload.get("status") == "queued"
        assert "wp18c6" in payload.get("message", "").lower()

    def test_admin_backfill_status_updates_in_overview(self, admin_headers):
        """After backfill is queued, overview shows running or completed status"""
        # Queue the backfill
        queue_response = requests.post(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/backfill/run?force=true",
            headers=admin_headers,
            timeout=30,
        )
        assert queue_response.status_code == 200
        
        # Wait a bit for backfill to start
        time.sleep(3)
        
        # Check overview for backfill status
        overview_response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/overview",
            headers=admin_headers,
            timeout=60,
        )
        assert overview_response.status_code == 200
        payload = overview_response.json()
        backfill = payload.get("backfill", {})
        assert backfill.get("status") in {"running", "completed", "pending_manual_run"}

    def test_admin_export_returns_csv(self, admin_headers):
        """Admin export endpoint returns CSV for a project"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/operational-intelligence/projects/{TEST_PROJECT}/export",
            headers=admin_headers,
            timeout=60,
        )
        assert response.status_code == 200, f"Admin export failed: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "")
        
        lines = response.text.strip().split("\n")
        assert len(lines) > 0
        assert lines[0].strip() == "section,metric_id,label,value,unit,confidence,notes"


class TestWP18C6OverrideFlow:
    """Tests for recommendation override flow"""

    @pytest.fixture(scope="class")
    def pm_headers(self):
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not configured")
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=30,
        )
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code}")
        token = response.json().get("token") or response.json().get("pm_token")
        return {"X-PM-Token": token}

    def test_pm_override_endpoint_exists(self, pm_headers):
        """PM override endpoint is accessible (may return 200 or error based on recommendation existence)"""
        # First get snapshot to check if there are any recommendations
        snapshot_response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence",
            headers=pm_headers,
            timeout=60,
        )
        assert snapshot_response.status_code == 200
        snapshot = snapshot_response.json()
        recommendations = snapshot.get("recommendations", [])
        
        if not recommendations:
            # No recommendations to override, but endpoint should still be accessible
            # Try with a fake recommendation ID - should return 200 (override is recorded regardless)
            response = requests.post(
                f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence/recommendations/test-recommendation-id/override",
                headers=pm_headers,
                json={"action": "override", "note": "Test override note"},
                timeout=30,
            )
            # The endpoint should accept the override even if recommendation doesn't exist
            assert response.status_code == 200, f"Override endpoint failed: {response.text}"
        else:
            # Override the first open recommendation
            open_recs = [r for r in recommendations if r.get("status") == "open"]
            if open_recs:
                rec_id = open_recs[0].get("recommendation_id")
                response = requests.post(
                    f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/operational-intelligence/recommendations/{rec_id}/override",
                    headers=pm_headers,
                    json={"action": "override", "note": "Test override from e2e test"},
                    timeout=30,
                )
                assert response.status_code == 200, f"Override failed: {response.text}"
                payload = response.json()
                assert payload.get("ok") is True
                assert "override" in payload


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
