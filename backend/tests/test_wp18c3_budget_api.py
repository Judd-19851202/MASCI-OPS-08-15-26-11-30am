"""
WP-18C3 Project Budget Authority API Tests
Tests the budget hierarchy, import workflow, and governed activation endpoints.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("LOCAL_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")

# Test credentials from test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"


class TestWP18C3BudgetAPIs:
    """WP-18C3 Budget Authority API tests"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get admin session tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Canonical multi-login admin session
        response = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, headers={"X-Device-Id": f"wp18c3-admin-{uuid.uuid4().hex[:8]}"})
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code}")
        
        data = response.json()
        admin_token = (data.get("portal_tokens") or {}).get("admin") or data.get("admin_token") or data.get("token")
        directory_token = data.get("session_token") or data.get("directory_token") or ""
        
        session.headers.update({
            "X-Admin-Token": admin_token,
            "X-Directory-Token": directory_token
        })
        return session

    @pytest.fixture(scope="class")
    def pm_session(self):
        """Get PM session tokens"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": PM_EMAIL,
            "password": PM_PASSWORD
        }, headers={"X-Device-Id": f"wp18c3-pm-{uuid.uuid4().hex[:8]}"})
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code}")
        
        data = response.json()
        pm_token = (data.get("portal_tokens") or {}).get("pm") or data.get("token") or data.get("pm_token")
        directory_token = data.get("session_token") or ""
        
        session.headers.update({"X-PM-Token": pm_token, "X-Directory-Token": directory_token})
        return session

    # ==================== Admin Budget Endpoints ====================

    def test_admin_budget_overview_returns_200(self, admin_session):
        """Admin budget overview endpoint should return 200"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/project-controls/budget/overview")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "summary" in data, "Response should contain summary"
        assert "versions" in data, "Response should contain versions"
        assert "imports" in data, "Response should contain imports"
        assert "review_queue" in data, "Response should contain review_queue"
        assert "event_contracts" in data, "Response should contain event_contracts"
        assert "backfill" in data, "Response should contain backfill status"

    def test_admin_budget_overview_with_project_filter(self, admin_session):
        """Admin budget overview with project filter should return 200"""
        response = admin_session.get(
            f"{BASE_URL}/api/admin/governance/project-controls/budget/overview",
            params={"project_number": TEST_PROJECT}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_admin_budget_review_queue_returns_200(self, admin_session):
        """Admin budget review queue endpoint should return 200"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/project-controls/budget/review-queue")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "count" in data, "Response should contain count"
        assert "items" in data, "Response should contain items"

    def test_admin_budget_backfill_queues_work(self, admin_session):
        """Admin budget backfill should queue work (not block)"""
        response = admin_session.post(f"{BASE_URL}/api/admin/governance/project-controls/budget/backfill/run")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("ok") == True, "Backfill should return ok=True"
        assert data.get("status") == "queued", "Backfill should be queued, not blocking"

    # ==================== PM Budget Endpoints ====================

    def test_pm_budget_overview_returns_200(self, pm_session):
        """PM budget overview endpoint should return 200"""
        response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/budget/overview"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "project" in data, "Response should contain project info"
        assert "authority_boundaries" in data, "Response should contain authority_boundaries"
        assert "counts" in data, "Response should contain counts"
        assert "event_contracts" in data, "Response should contain event_contracts"

    def test_pm_budget_versions_returns_200(self, pm_session):
        """PM budget versions endpoint should return 200"""
        response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/budget/versions"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "count" in data, "Response should contain count"
        assert "items" in data, "Response should contain items"

    def test_pm_budget_review_queue_returns_200(self, pm_session):
        """PM budget review queue endpoint should return 200"""
        response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/budget/review-queue"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "count" in data, "Response should contain count"
        assert "items" in data, "Response should contain items"

    def test_pm_budget_imports_returns_200(self, pm_session):
        """PM budget imports endpoint should return 200"""
        response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/budget/imports"
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "count" in data, "Response should contain count"
        assert "items" in data, "Response should contain items"

    # ==================== Trust Line Separation ====================

    def test_budget_authority_boundaries_are_separate(self, pm_session):
        """Budget authority boundaries should keep concepts separate"""
        response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/budget/overview"
        )
        assert response.status_code == 200
        
        data = response.json()
        boundaries = data.get("authority_boundaries", {})
        
        # Verify trust lines are separate
        assert boundaries.get("customer_pay_item_truth") == "project_pay_item_registry"
        assert boundaries.get("enterprise_work_type_truth") == "enterprise_work_type_registry"
        assert boundaries.get("commitment_truth") == "po_requests"
        assert boundaries.get("actual_cost_truth") == "external_accounting_or_governed_receipt_review"
        assert boundaries.get("ai_role") == "advisory_only"

    # ==================== Regression: Existing Routes ====================

    def test_pm_project_controls_still_loads(self, pm_session):
        """Regression: PM Project Controls route should still work"""
        response = pm_session.get(
            f"{BASE_URL}/api/pm/project-controls/overview",
            params={"project_number": TEST_PROJECT}
        )
        assert response.status_code == 200, f"PM Project Controls regression failed: {response.status_code}"

    def test_admin_project_controls_still_loads(self, admin_session):
        """Regression: Admin Project Controls route should still work"""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/project-controls/overview")
        assert response.status_code == 200, f"Admin Project Controls regression failed: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
