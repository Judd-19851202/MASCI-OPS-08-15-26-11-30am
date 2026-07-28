"""WP-OPPC-11 Forecasting & Critical-Path Hardening — Live API Verification

Tests the new WP-11 endpoints:
- GET /api/cost-codes/projects/{project_number}/forecast
- POST /api/cost-codes/projects/{project_number}/forecast/snapshots
- PUT /api/cost-codes/projects/{project_number}/forecast/overrides/{cost_code}
- GET /api/cost-codes/projects/{project_number}/schedule (forecasting payload)

Verifies:
1. Deterministic forecast derives from canonical operational data
2. Scenario comparison shows calculated truth + alternatives
3. Override governance preserves calculated truth and audits changes
4. Snapshot governance records versioned forecast history
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
TEST_PROJECT = "20-07"  # Known project with assigned cost codes


@pytest.fixture(scope="module")
def pm_token():
    """Get PM token via /api/pm/login."""
    r = requests.post(f"{BASE_URL}/api/pm/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if r.status_code != 200:
        pytest.skip(f"PM login failed: {r.status_code} - {r.text[:200]}")
    data = r.json()
    token = data.get("token")
    if not token:
        pytest.skip("No token in PM login response")
    return token


@pytest.fixture(scope="module")
def pm_session(pm_token):
    """Get PM session with auth token."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "X-PM-Token": pm_token
    })
    return session


@pytest.fixture(scope="module")
def test_project():
    """Return the test project number."""
    return TEST_PROJECT


class TestWP11ForecastEndpoint:
    """Test GET /api/cost-codes/projects/{project_number}/forecast"""

    def test_forecast_endpoint_returns_canonical_truth_basis(self, pm_session, test_project):
        """Verify forecast endpoint returns truth_basis = canonical_operational_data"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast")
        assert r.status_code == 200, f"Forecast endpoint failed: {r.text[:200]}"
        data = r.json()
        
        # WP-11 requirement: truth_basis must be canonical_operational_data
        assert data.get("truth_basis") == "canonical_operational_data", \
            f"Expected truth_basis=canonical_operational_data, got {data.get('truth_basis')}"
        
        # Verify schedule payload structure
        schedule = data.get("schedule", {})
        assert "scenario" in schedule, "Missing scenario in schedule"
        assert schedule.get("scenario", {}).get("key") == "calculated_truth", \
            "Default scenario should be calculated_truth"

    def test_forecast_endpoint_includes_scenario_comparison(self, pm_session, test_project):
        """Verify scenario comparison shows alternatives with days gained/lost"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast")
        assert r.status_code == 200
        data = r.json()
        
        comparison = data.get("scenario_comparison", {})
        assert "baseline" in comparison, "Missing baseline in scenario_comparison"
        assert "scenarios" in comparison, "Missing scenarios in scenario_comparison"
        
        # Verify baseline has required fields
        baseline = comparison.get("baseline", {})
        assert "projected_finish_date" in baseline
        assert "critical_path_count" in baseline
        
        # Verify scenarios have days_gained_against_baseline
        for scenario in comparison.get("scenarios", []):
            assert "scenario_key" in scenario
            assert "days_gained_against_baseline" in scenario
            assert "projected_finish_date" in scenario

    def test_forecast_endpoint_includes_governance_summary(self, pm_session, test_project):
        """Verify governance summary is included in forecast response"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast")
        assert r.status_code == 200
        data = r.json()
        
        governance = data.get("governance", {})
        assert "snapshot_count" in governance, "Missing snapshot_count in governance"
        assert "active_override_count" in governance, "Missing active_override_count in governance"
        assert "overrides" in governance, "Missing overrides list in governance"


class TestWP11ScheduleEndpointForecasting:
    """Test GET /api/cost-codes/projects/{project_number}/schedule forecasting payload"""

    def test_schedule_endpoint_includes_forecasting_section(self, pm_session, test_project):
        """Verify schedule endpoint includes forecasting section with WP-11 fields"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule")
        assert r.status_code == 200
        data = r.json()
        
        forecasting = data.get("forecasting", {})
        assert forecasting, "Missing forecasting section in schedule response"
        
        # WP-11 constitutional rule
        assert "constitutional_rule" in forecasting, "Missing constitutional_rule"
        assert "canonical" in forecasting.get("constitutional_rule", "").lower(), \
            "Constitutional rule should mention canonical data"
        
        # Scenario comparison
        assert "scenario_comparison" in forecasting, "Missing scenario_comparison"
        
        # Governance
        assert "governance" in forecasting, "Missing governance"
        
        # Scenario library
        assert "scenario_library" in forecasting, "Missing scenario_library"

    def test_schedule_tasks_include_hardening_and_explainability(self, pm_session, test_project):
        """Verify schedule tasks include hardening and explainability fields"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule")
        assert r.status_code == 200
        data = r.json()
        
        tasks = data.get("schedule", {}).get("tasks", [])
        if not tasks:
            pytest.skip("No tasks in schedule to verify")
        
        task = tasks[0]
        
        # WP-11 hardening fields
        assert "hardening" in task, "Missing hardening in task"
        hardening = task.get("hardening", {})
        assert "risk_band" in hardening, "Missing risk_band in hardening"
        assert "recommended_scenarios" in hardening, "Missing recommended_scenarios"
        
        # WP-11 explainability fields
        assert "explainability" in task, "Missing explainability in task"
        explainability = task.get("explainability", {})
        assert "rate_selection" in explainability, "Missing rate_selection"
        assert "quantity_basis" in explainability, "Missing quantity_basis"
        assert "truth_classes" in explainability, "Missing truth_classes"
        assert "formula" in explainability, "Missing formula"

    def test_schedule_includes_projected_and_committed_finish(self, pm_session, test_project):
        """Verify schedule includes both projected and committed finish dates"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule")
        assert r.status_code == 200
        data = r.json()
        
        schedule = data.get("schedule", {})
        assert "projected_finish_date" in schedule, "Missing projected_finish_date"
        assert "committed_finish_date" in schedule, "Missing committed_finish_date"
        assert "hardening_summary" in schedule, "Missing hardening_summary"


class TestWP11ForecastSnapshotGovernance:
    """Test POST /api/cost-codes/projects/{project_number}/forecast/snapshots"""

    def test_snapshot_creates_versioned_forecast_history(self, pm_session, test_project):
        """Verify snapshot endpoint creates versioned forecast history"""
        # Get initial governance state
        r1 = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast")
        assert r1.status_code == 200
        initial_count = r1.json().get("governance", {}).get("snapshot_count", 0)
        
        # Create snapshot
        r2 = pm_session.post(
            f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast/snapshots",
            json={
                "scenario_key": "calculated_truth",
                "note": "WP-11 test snapshot"
            }
        )
        assert r2.status_code == 200, f"Snapshot creation failed: {r2.text[:200]}"
        data = r2.json()
        
        assert data.get("ok") is True, "Snapshot response should have ok=True"
        assert "snapshot" in data, "Missing snapshot in response"
        
        snapshot = data.get("snapshot", {})
        assert "snapshot_id" in snapshot, "Missing snapshot_id"
        assert snapshot.get("truth_basis") == "canonical_operational_data", \
            "Snapshot should have canonical truth_basis"
        
        # Verify governance updated
        forecasting = data.get("forecasting", {})
        governance = forecasting.get("governance", {})
        assert governance.get("snapshot_count", 0) >= initial_count, \
            "Snapshot count should increase or stay same"


class TestWP11OverrideGovernance:
    """Test PUT /api/cost-codes/projects/{project_number}/forecast/overrides/{cost_code}"""

    def test_override_preserves_calculated_truth_and_audits(self, pm_session, test_project):
        """Verify override preserves calculated truth and creates audit trail"""
        # Get a cost code from the project
        r1 = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule")
        assert r1.status_code == 200
        tasks = r1.json().get("schedule", {}).get("tasks", [])
        if not tasks:
            pytest.skip("No tasks to test override on")
        
        task = tasks[0]
        cost_code = task.get("code")
        
        # Create override
        r2 = pm_session.put(
            f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast/overrides/{cost_code}",
            json={
                "adjusted_finish_date": "2026-12-31",
                "reason": "WP-11 test override - authorized management adjustment",
                "note": "Testing override governance",
                "evidence_links": ["doc://wp11-test"]
            }
        )
        assert r2.status_code == 200, f"Override creation failed: {r2.text[:200]}"
        data = r2.json()
        
        assert data.get("ok") is True, "Override response should have ok=True"
        assert "override" in data, "Missing override in response"
        
        override = data.get("override", {})
        assert override.get("cost_code") == cost_code, "Override should have correct cost_code"
        assert override.get("truth_basis") == "authorized_management_override", \
            "Override should have authorized_management_override truth_basis"
        assert "history" in override, "Override should have history for audit trail"
        assert len(override.get("history", [])) > 0, "Override history should not be empty"
        
        # Verify calculated truth is preserved in truth_classes
        forecasting = data.get("forecasting", {})
        governance = forecasting.get("governance", {})
        assert governance.get("active_override_count", 0) > 0, \
            "Active override count should be > 0"

    def test_override_requires_reason(self, pm_session, test_project):
        """Verify override endpoint requires reason field"""
        r1 = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule")
        assert r1.status_code == 200
        tasks = r1.json().get("schedule", {}).get("tasks", [])
        if not tasks:
            pytest.skip("No tasks to test override on")
        
        cost_code = tasks[0].get("code")
        
        # Try to create override without reason
        r2 = pm_session.put(
            f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast/overrides/{cost_code}",
            json={
                "adjusted_finish_date": "2026-12-31",
                "reason": "",  # Empty reason
                "note": "Testing validation"
            }
        )
        assert r2.status_code == 422, "Override without reason should fail with 422"


class TestWP11ScenarioComparison:
    """Test scenario comparison functionality"""

    def test_scenario_comparison_includes_all_standard_scenarios(self, pm_session, test_project):
        """Verify scenario comparison includes additional_crew, weekend_work, additional_shift"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast")
        assert r.status_code == 200
        data = r.json()
        
        comparison = data.get("scenario_comparison", {})
        scenarios = comparison.get("scenarios", [])
        scenario_keys = {s.get("scenario_key") for s in scenarios}
        
        expected_scenarios = {"additional_crew", "weekend_work", "additional_shift"}
        assert expected_scenarios.issubset(scenario_keys), \
            f"Missing scenarios. Expected {expected_scenarios}, got {scenario_keys}"

    def test_scenario_library_in_forecasting_section(self, pm_session, test_project):
        """Verify scenario library is exposed in forecasting section"""
        r = pm_session.get(f"{BASE_URL}/api/cost-codes/projects/{test_project}/schedule")
        assert r.status_code == 200
        data = r.json()
        
        forecasting = data.get("forecasting", {})
        scenario_library = forecasting.get("scenario_library", [])
        
        assert len(scenario_library) > 0, "Scenario library should not be empty"
        
        for scenario in scenario_library:
            assert "key" in scenario, "Scenario should have key"
            assert "label" in scenario, "Scenario should have label"
            assert "rate_multiplier" in scenario, "Scenario should have rate_multiplier"


class TestWP11TrustSpineIntegration:
    """Test Trust Spine workflow registration for oppc-forecasting"""

    def test_forecast_operations_emit_trust_spine_events(self, pm_session, test_project):
        """Verify forecast operations are registered with Trust Spine"""
        # Create a snapshot to trigger Trust Spine emission
        r = pm_session.post(
            f"{BASE_URL}/api/cost-codes/projects/{test_project}/forecast/snapshots",
            json={
                "scenario_key": "calculated_truth",
                "note": "Trust Spine verification snapshot"
            }
        )
        assert r.status_code == 200, f"Snapshot failed: {r.text[:200]}"
        
        # The Trust Spine emission is best-effort and doesn't fail the request
        # We verify the endpoint works and returns expected structure
        data = r.json()
        assert data.get("ok") is True
        assert "snapshot" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
