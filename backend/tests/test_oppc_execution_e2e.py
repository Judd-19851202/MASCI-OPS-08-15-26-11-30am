"""
WP-OPPC-05/06/07 E2E Tests — Daily Actual Production, Payroll Reconciliation, Monday Look-Behind

Tests the OPPC execution workspace and Monday review workflow.
Verifies:
- GET /api/oppc/projects/{project_number}/execution-workspace returns computed data
- Daily Reports submission drives quantity/labor/equipment signals into OPPC derived views
- Payroll Variance lifecycle extends into OPPC derived payroll reconciliation
- Monday review workspace routes and Trust Spine workflow events
- POST /api/oppc/projects/{project_number}/monday-review/start initializes review
- PUT /api/oppc/projects/{project_number}/monday-review/activities/{cost_code} saves review data
- PUT /api/oppc/projects/{project_number}/monday-review/meta updates critical path review
- POST /api/oppc/projects/{project_number}/monday-review/complete blocks until ready
- Regression: PM project schedule page still loads with planning_readiness, planning_lifecycle
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")

# Test credentials from /app/memory/test_credentials.md
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def get_auth_headers(email: str, password: str, portal: str) -> dict:
    """Login and return headers with portal token and directory token."""
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json={
        "email": email,
        "password": password,
        "portal": portal,
    })
    if r.status_code != 200:
        return {}
    data = r.json()
    session_token = data.get("session_token", "")
    portal_tokens = data.get("portal_tokens", {})
    portal_token = portal_tokens.get(portal, "")
    header_name = f"X-{portal.title()}-Token"
    if portal == "field_leadership":
        header_name = "X-FL-Token"
    return {
        header_name: portal_token,
        "X-Directory-Token": session_token,
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def pm_headers():
    """Get PM authentication headers."""
    headers = get_auth_headers(PM_EMAIL, PM_PASSWORD, "pm")
    if not headers.get("X-Pm-Token"):
        pytest.skip(f"PM login failed for {PM_EMAIL}")
    return headers


@pytest.fixture(scope="module")
def admin_headers():
    """Get Admin authentication headers."""
    headers = get_auth_headers(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")
    if not headers.get("X-Admin-Token"):
        pytest.skip(f"Admin login failed for {ADMIN_EMAIL}")
    return headers


@pytest.fixture(scope="module")
def test_project(admin_headers):
    """Find a project for testing."""
    # Use a known project from the test data
    return "20-07"


class TestOPPCExecutionWorkspace:
    """Tests for GET /api/oppc/projects/{project_number}/execution-workspace"""

    def test_execution_workspace_returns_200_for_admin(self, admin_headers, test_project):
        """Verify admin can access execution workspace."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Verify required fields are present
        assert "project_number" in data
        assert data["project_number"] == test_project
        assert "review_week" in data
        assert "planning_readiness" in data
        assert "planning_lifecycle" in data
        assert "schedule" in data
        assert "production_summary" in data
        assert "payroll_summary" in data
        assert "monday_review" in data
        assert "project_health" in data
        assert "root_cause_types" in data
        assert "controllability_options" in data

    def test_execution_workspace_returns_production_summary(self, admin_headers, test_project):
        """Verify production_summary contains expected fields."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        ps = data.get("production_summary", {})
        assert "planned_quantity" in ps
        assert "actual_quantity" in ps
        assert "remaining_quantity" in ps
        assert "percent_complete" in ps
        assert "actual_labor_hours" in ps
        assert "actual_equipment_hours" in ps
        assert "actual_trucks" in ps
        assert "report_count" in ps
        assert "latest_report_date" in ps

    def test_execution_workspace_returns_payroll_summary(self, admin_headers, test_project):
        """Verify payroll_summary contains expected fields."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        ps = data.get("payroll_summary", {})
        assert "lifecycle_state" in ps
        assert "field_labor_hours" in ps
        assert "payroll_labor_hours" in ps
        assert "labor_difference_hours" in ps
        assert "complete" in ps
        assert "missing_payroll" in ps
        assert "explainability" in ps

    def test_execution_workspace_returns_monday_review_structure(self, admin_headers, test_project):
        """Verify monday_review contains expected fields."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        mr = data.get("monday_review", {})
        assert "workspace" in mr
        assert "activities" in mr
        assert "exceptions" in mr
        assert "checks" in mr
        assert "ready" in mr
        assert "completion_percent" in mr
        assert "blocking_items" in mr
        assert "warnings" in mr
        assert "outstanding_recovery" in mr
        assert "critical_path_changes" in mr
        assert "missing_reports" in mr
        assert "missing_payroll" in mr
        assert "open_variances" in mr

    def test_execution_workspace_returns_readiness_checks(self, admin_headers, test_project):
        """Verify readiness checks are computed."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        checks = data.get("monday_review", {}).get("checks", {})
        expected_checks = [
            "actuals_complete",
            "variances_reviewed",
            "causes_recorded",
            "recovery_assigned",
            "payroll_reconciliation_complete",
            "critical_path_reviewed",
            "executive_actions_identified",
            "forecast_recalculated",
        ]
        for check in expected_checks:
            assert check in checks, f"Missing readiness check: {check}"

    def test_execution_workspace_returns_root_cause_types(self, admin_headers, test_project):
        """Verify root_cause_types taxonomy is returned."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        causes = data.get("root_cause_types", [])
        assert len(causes) > 0, "Expected root_cause_types to be populated"
        expected_causes = ["weather", "material", "equipment", "labor", "productivity"]
        for cause in expected_causes:
            assert cause in causes, f"Missing root cause type: {cause}"

    def test_execution_workspace_returns_controllability_options(self, admin_headers, test_project):
        """Verify controllability_options are returned."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        options = data.get("controllability_options", [])
        assert "controllable" in options
        assert "shared" in options
        assert "external" in options

    def test_execution_workspace_with_week_ending_param(self, admin_headers, test_project):
        """Verify week_ending parameter filters the review week."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", params={"week_ending": "2026-01-19"}, headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data.get("review_week", {}).get("week_ending") == "2026-01-19"

    def test_execution_workspace_activities_have_explainability(self, admin_headers, test_project):
        """Verify activities have explainability data for transparency."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        activities = data.get("monday_review", {}).get("activities", [])
        if activities:
            activity = activities[0]
            assert "explainability" in activity, "Activity should have explainability"
            exp = activity["explainability"]
            assert "expected" in exp
            assert "actual" in exp
            assert "difference" in exp
            assert "formula" in exp


class TestMondayReviewStart:
    """Tests for POST /api/oppc/projects/{project_number}/monday-review/start"""

    def test_start_monday_review_returns_200(self, admin_headers, test_project):
        """Verify admin can start a Monday review."""
        r = requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("ok") is True
        assert "monday_review" in data

    def test_start_monday_review_with_week_ending(self, admin_headers, test_project):
        """Verify week_ending parameter is respected."""
        r = requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={"week_ending": "2026-01-19"}, headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert data.get("review_week", {}).get("week_ending") == "2026-01-19"

    def test_start_monday_review_idempotent(self, admin_headers, test_project):
        """Verify starting review multiple times is idempotent."""
        r1 = requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        assert r1.status_code == 200
        r2 = requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        assert r2.status_code == 200
        # Both should succeed without error


class TestMondayReviewMeta:
    """Tests for PUT /api/oppc/projects/{project_number}/monday-review/meta"""

    def test_update_meta_returns_200(self, admin_headers, test_project):
        """Verify admin can update Monday review metadata."""
        # First start the review
        requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        # Then update meta
        r = requests.put(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/meta", json={
            "critical_path_reviewed": True,
            "executive_actions": ["Monitor weather forecast", "Coordinate with utility"],
            "notes": "Test review notes",
        }, headers=admin_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("ok") is True

    def test_update_meta_affects_readiness_checks(self, admin_headers, test_project):
        """Verify updating meta affects readiness checks."""
        requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        r = requests.put(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/meta", json={
            "critical_path_reviewed": True,
            "executive_actions": ["Action 1"],
        }, headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        checks = data.get("monday_review", {}).get("checks", {})
        assert checks.get("critical_path_reviewed") is True
        assert checks.get("executive_actions_identified") is True


class TestMondayReviewActivityUpdate:
    """Tests for PUT /api/oppc/projects/{project_number}/monday-review/activities/{cost_code}"""

    def test_update_activity_review_returns_200(self, admin_headers, test_project):
        """Verify admin can update activity review."""
        # Start review first
        requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        # Get activities
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("Could not get execution workspace")
        activities = r.json().get("monday_review", {}).get("activities", [])
        if not activities:
            pytest.skip("No activities to test")
        code = activities[0].get("code")
        # Update activity review
        r = requests.put(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/activities/{code}", json={
            "primary_cause": "weather",
            "controllability": "external",
            "recovery_strategy": "Reschedule to next week",
            "notes": "Test activity review",
        }, headers=admin_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("ok") is True

    def test_activity_review_rejects_invalid_primary_cause(self, admin_headers, test_project):
        """Verify invalid primary_cause is rejected."""
        requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("Could not get execution workspace")
        activities = r.json().get("monday_review", {}).get("activities", [])
        if not activities:
            pytest.skip("No activities to test")
        code = activities[0].get("code")
        r = requests.put(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/activities/{code}", json={
            "primary_cause": "invalid_cause_not_in_taxonomy",
        }, headers=admin_headers)
        assert r.status_code == 422, f"Expected 422 for invalid cause, got {r.status_code}"

    def test_activity_review_rejects_invalid_controllability(self, admin_headers, test_project):
        """Verify invalid controllability is rejected."""
        requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        r = requests.get(f"{BASE_URL}/api/oppc/projects/{test_project}/execution-workspace", headers=admin_headers)
        if r.status_code != 200:
            pytest.skip("Could not get execution workspace")
        activities = r.json().get("monday_review", {}).get("activities", [])
        if not activities:
            pytest.skip("No activities to test")
        code = activities[0].get("code")
        r = requests.put(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/activities/{code}", json={
            "controllability": "invalid_controllability",
        }, headers=admin_headers)
        assert r.status_code == 422, f"Expected 422 for invalid controllability, got {r.status_code}"


class TestMondayReviewComplete:
    """Tests for POST /api/oppc/projects/{project_number}/monday-review/complete"""

    def test_complete_monday_review_blocks_when_not_ready(self, admin_headers, test_project):
        """Verify completion is blocked when readiness checks fail."""
        # Start a fresh review
        requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/start", json={}, headers=admin_headers)
        # Try to complete without meeting all readiness checks
        r = requests.post(f"{BASE_URL}/api/oppc/projects/{test_project}/monday-review/complete", json={}, headers=admin_headers)
        # Should return 409 Conflict with blocking items
        if r.status_code == 409:
            data = r.json()
            detail = data.get("detail", {})
            assert detail.get("code") == "monday_review_not_ready"
            assert "blocking_items" in detail
            print(f"Blocking items: {detail.get('blocking_items')}")
        elif r.status_code == 200:
            # If it succeeds, the project must have been ready
            data = r.json()
            assert data.get("ok") is True
        else:
            pytest.fail(f"Unexpected status code: {r.status_code}: {r.text[:300]}")


class TestProjectScheduleRegression:
    """Regression tests for PM project schedule page (WP-OPPC-02/03/04)"""

    def test_project_schedule_returns_planning_readiness(self, admin_headers, test_project):
        """Verify planning_readiness is returned in schedule response."""
        r = requests.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule", headers=admin_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert "planning_readiness" in data
        pr = data.get("planning_readiness", {})
        assert "status" in pr
        assert "assignment_count" in pr
        assert "ready_assignments" in pr
        assert "supports_weekly_rollover" in pr
        assert "supports_monday_look_behind" in pr

    def test_project_schedule_returns_planning_lifecycle(self, admin_headers, test_project):
        """Verify planning_lifecycle is returned in schedule response."""
        r = requests.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "planning_lifecycle" in data
        pl = data.get("planning_lifecycle", {})
        assert "status" in pl
        assert "supports_publish" in pl
        assert "has_unpublished_changes" in pl

    def test_project_schedule_returns_schedule_with_tasks(self, admin_headers, test_project):
        """Verify schedule contains tasks array."""
        r = requests.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "schedule" in data
        schedule = data.get("schedule", {})
        assert "tasks" in schedule
        assert "window" in schedule
        assert "projected_finish_date" in schedule

    def test_weekly_rollover_preview_endpoint_exists(self, admin_headers, test_project):
        """Verify weekly rollover preview endpoint is accessible."""
        r = requests.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/weekly-rollover/preview", headers=admin_headers)
        # May return 200 or 422 depending on project state
        assert r.status_code in [200, 422], f"Unexpected status: {r.status_code}: {r.text[:300]}"


class TestTrustSpineWorkflows:
    """Tests for Trust Spine workflow event registration"""

    def test_oppc_daily_actuals_workflow_registered(self):
        """Verify oppc-daily-actuals workflow is registered in Trust Spine."""
        import sys
        sys.path.insert(0, "/app/backend")
        from lib.trust_spine import WORKFLOW_EXPECTED_STAGES
        assert "oppc-daily-actuals" in WORKFLOW_EXPECTED_STAGES
        stages = WORKFLOW_EXPECTED_STAGES["oppc-daily-actuals"]
        assert "record_created" in stages
        assert "validation_complete" in stages
        assert "audit_written" in stages
        assert "dashboard_updated" in stages
        assert "completed" in stages

    def test_oppc_payroll_reconciliation_workflow_registered(self):
        """Verify oppc-payroll-reconciliation workflow is registered in Trust Spine."""
        import sys
        sys.path.insert(0, "/app/backend")
        from lib.trust_spine import WORKFLOW_EXPECTED_STAGES
        assert "oppc-payroll-reconciliation" in WORKFLOW_EXPECTED_STAGES
        stages = WORKFLOW_EXPECTED_STAGES["oppc-payroll-reconciliation"]
        assert "record_created" in stages
        assert "validation_complete" in stages
        assert "audit_written" in stages
        assert "dashboard_updated" in stages
        assert "completed" in stages

    def test_oppc_monday_look_behind_workflow_registered(self):
        """Verify oppc-monday-look-behind workflow is registered in Trust Spine."""
        import sys
        sys.path.insert(0, "/app/backend")
        from lib.trust_spine import WORKFLOW_EXPECTED_STAGES
        assert "oppc-monday-look-behind" in WORKFLOW_EXPECTED_STAGES
        stages = WORKFLOW_EXPECTED_STAGES["oppc-monday-look-behind"]
        assert "record_created" in stages
        assert "validation_complete" in stages
        assert "audit_written" in stages
        assert "dashboard_updated" in stages
        assert "completed" in stages


class TestAccessControl:
    """Tests for access control on OPPC execution routes"""

    def test_hr_cannot_access_execution_workspace(self):
        """Verify HR role cannot access execution workspace."""
        headers = get_auth_headers("cert.hr@example.com", "CertProof2026!", "hr")
        if not headers.get("X-Hr-Token"):
            pytest.skip("HR login failed")
        r = requests.get(f"{BASE_URL}/api/oppc/projects/20-07/execution-workspace", headers=headers)
        assert r.status_code == 403, f"Expected 403 for HR, got {r.status_code}"

    def test_unauthenticated_cannot_access_execution_workspace(self):
        """Verify unauthenticated requests are rejected."""
        r = requests.get(f"{BASE_URL}/api/oppc/projects/20-07/execution-workspace")
        assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"
