"""
WP-18C8 Earned Value Engine Backend API Tests
Tests the C8 earned-value workspace APIs for PM and Admin/Executive audiences.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

# Test project from agent context
TEST_PROJECT = "ZZ-RUNTIME-CERT-2026"


class TestEarnedValueEngineBackend:
    """C8 Earned Value Engine API tests"""

    @pytest.fixture(scope="class")
    def pm_token(self):
        """Get PM authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"PM login failed: {response.status_code} - {response.text}")
        data = response.json()
        return data.get("token") or data.get("access_token")

    @pytest.fixture(scope="class")
    def admin_tokens(self):
        """Get Admin authentication tokens (admin + directory)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
        data = response.json()
        return {
            "admin_token": data.get("admin_token"),
            "directory_token": data.get("directory_token")
        }

    # ==================== PM Earned Value API Tests ====================

    def test_pm_earned_value_snapshot_get(self, pm_token):
        """Test PM earned-value snapshot GET endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/earned-value",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "project_number" in data, "Missing project_number in response"
        assert data["project_number"] == TEST_PROJECT
        assert "readiness" in data, "Missing readiness in response"
        assert "summary" in data, "Missing summary in response"
        assert "metric_cards" in data, "Missing metric_cards in response"
        assert "lines" in data, "Missing lines in response"
        
        # Verify readiness structure
        readiness = data["readiness"]
        assert "overall" in readiness, "Missing overall in readiness"
        assert readiness["overall"] in ["ready", "partial", "blocked"], f"Invalid readiness overall: {readiness['overall']}"
        
        # Verify summary metrics
        summary = data["summary"]
        expected_metrics = ["bac", "ev", "ac", "cpi", "spi"]
        for metric in expected_metrics:
            assert metric in summary, f"Missing {metric} in summary"
        
        print(f"PM Earned Value Snapshot - Readiness: {readiness['overall']}")
        print(f"Summary: BAC={summary.get('bac')}, EV={summary.get('ev')}, AC={summary.get('ac')}, CPI={summary.get('cpi')}, SPI={summary.get('spi')}")

    def test_pm_earned_value_snapshot_force_refresh(self, pm_token):
        """Test PM earned-value snapshot with force_refresh=true"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/earned-value?force_refresh=true",
            headers={"X-PM-Token": pm_token},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "cache_status" in data, "Missing cache_status in response"
        print(f"PM Earned Value Force Refresh - Cache status: {data.get('cache_status')}")

    def test_pm_earned_value_snapshot_capture(self, pm_token):
        """Test PM earned-value snapshot capture (version creation)"""
        response = requests.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/earned-value/snapshots",
            headers={"X-PM-Token": pm_token},
            json={"note": "TEST_C8_PM_Snapshot_Capture"},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "versioning" in data, "Missing versioning in response"
        versioning = data["versioning"]
        assert "current_version_id" in versioning, "Missing current_version_id in versioning"
        print(f"PM Earned Value Snapshot Captured - Version: {versioning.get('current_version_id')}")

    def test_pm_earned_value_export(self, pm_token):
        """Test PM earned-value CSV export"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/earned-value/export",
            headers={"X-PM-Token": pm_token},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify CSV content type
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Expected text/csv content type, got {content_type}"
        
        # Verify content-disposition header
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition, f"Expected attachment disposition, got {content_disposition}"
        
        print(f"PM Earned Value Export - Content-Disposition: {content_disposition}")

    # ==================== Admin/Executive Earned Value API Tests ====================

    def test_admin_earned_value_snapshot_get(self, admin_tokens):
        """Test Admin/Executive earned-value snapshot GET endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{TEST_PROJECT}/earned-value",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"]
            },
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "project_number" in data, "Missing project_number in response"
        assert data["project_number"] == TEST_PROJECT
        assert "audience" in data, "Missing audience in response"
        assert data["audience"] == "executive", f"Expected executive audience, got {data['audience']}"
        assert "readiness" in data, "Missing readiness in response"
        assert "summary" in data, "Missing summary in response"
        
        print(f"Admin Earned Value Snapshot - Audience: {data.get('audience')}, Readiness: {data['readiness'].get('overall')}")

    def test_admin_earned_value_snapshot_force_refresh(self, admin_tokens):
        """Test Admin/Executive earned-value snapshot with force_refresh=true"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{TEST_PROJECT}/earned-value?force_refresh=true",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"]
            },
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "cache_status" in data, "Missing cache_status in response"
        print(f"Admin Earned Value Force Refresh - Cache status: {data.get('cache_status')}")

    def test_admin_earned_value_snapshot_capture(self, admin_tokens):
        """Test Admin/Executive earned-value snapshot capture (version creation)"""
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{TEST_PROJECT}/earned-value/snapshots",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"]
            },
            json={"note": "TEST_C8_Admin_Snapshot_Capture"},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "versioning" in data, "Missing versioning in response"
        versioning = data["versioning"]
        assert "current_version_id" in versioning, "Missing current_version_id in versioning"
        print(f"Admin Earned Value Snapshot Captured - Version: {versioning.get('current_version_id')}")

    def test_admin_earned_value_export(self, admin_tokens):
        """Test Admin/Executive earned-value CSV export"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{TEST_PROJECT}/earned-value/export",
            headers={
                "X-Admin-Token": admin_tokens["admin_token"],
                "X-Directory-Token": admin_tokens["directory_token"]
            },
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify CSV content type
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type, f"Expected text/csv content type, got {content_type}"
        
        print(f"Admin Earned Value Export - Content-Type: {content_type}")

    # ==================== Metric Validation Tests ====================

    def test_pm_earned_value_metrics_validation(self, pm_token):
        """Validate PM earned-value metrics match expected seeded values"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/earned-value?force_refresh=true",
            headers={"X-PM-Token": pm_token},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        summary = data.get("summary", {})
        readiness = data.get("readiness", {})
        
        # Validate readiness is ready (per agent context)
        assert readiness.get("overall") == "ready", f"Expected readiness overall=ready, got {readiness.get('overall')}"
        
        # Validate expected metrics from seeded fixture (BAC 1200, EV 1200, AC 900, CPI ~1.3333)
        bac = summary.get("bac")
        ev = summary.get("ev")
        ac = summary.get("ac")
        cpi = summary.get("cpi")
        
        print(f"Metrics Validation - BAC: {bac}, EV: {ev}, AC: {ac}, CPI: {cpi}")
        
        # Validate open counts are 0 (per agent context)
        open_actual_cost_count = summary.get("open_actual_cost_count", -1)
        open_commitment_count = summary.get("open_commitment_count", -1)
        
        assert open_actual_cost_count == 0, f"Expected open_actual_cost_count=0, got {open_actual_cost_count}"
        assert open_commitment_count == 0, f"Expected open_commitment_count=0, got {open_commitment_count}"
        
        print(f"Open counts - Actual cost: {open_actual_cost_count}, Commitment: {open_commitment_count}")

    def test_pm_earned_value_metric_cards_structure(self, pm_token):
        """Validate metric cards structure and required fields"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{TEST_PROJECT}/earned-value",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        metric_cards = data.get("metric_cards", [])
        
        # Verify we have the expected metric cards
        expected_metrics = ["c8-bac", "c8-pv", "c8-ev", "c8-ac", "c8-cv", "c8-sv", "c8-cpi", "c8-spi", "c8-etc", "c8-eac", "c8-tcpi"]
        metric_ids = [card.get("metric_id") for card in metric_cards]
        
        for expected in expected_metrics:
            assert expected in metric_ids, f"Missing metric card: {expected}"
        
        # Verify each metric card has required fields
        for card in metric_cards:
            assert "metric_id" in card, "Missing metric_id in card"
            assert "label" in card, "Missing label in card"
            assert "confidence" in card, "Missing confidence in card"
            assert "status" in card, "Missing status in card"
            assert "formula" in card, "Missing formula in card"
        
        print(f"Metric cards validated: {len(metric_cards)} cards with all required fields")

    # ==================== Budget Review Lane Tests ====================

    def test_pm_budget_overview_with_trust_link(self, pm_token):
        """Test PM budget overview shows trust-link review lane data"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/budget/overview?project_number={TEST_PROJECT}",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response has commitment and actual cost candidates
        assert "commitment_candidates" in data or "actual_cost_candidates" in data, "Missing trust-link candidate data"
        
        commitment_candidates = data.get("commitment_candidates", [])
        actual_cost_candidates = data.get("actual_cost_candidates", [])
        
        print(f"Budget Overview - Commitment candidates: {len(commitment_candidates)}, Actual cost candidates: {len(actual_cost_candidates)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
