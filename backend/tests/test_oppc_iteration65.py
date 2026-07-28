"""
OPPC WP-OPPC-08/09/10 Live API Tests
Tests for:
- GET /api/oppc/enterprise/resource-coordination (Admin only)
- GET /api/oppc/enterprise/executive-operations-center (Admin only)
- GET /api/oppc/projects/{project_number}/variance-intelligence (PM scoped)
- PUT /api/oppc/projects/{project_number}/variances/{variance_key} (PM scoped)
- Execution workspace variance_intelligence embedding
- Regression: Monday review activity flow
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
PM_FORENSIC_EMAIL = "pm.scope.forensic@example.com"
PM_FORENSIC_PASSWORD = "ForensicPm2026!"


class TestOPPCEnterpriseRoutes:
    """Tests for enterprise-level OPPC routes (Admin only)"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get admin session tokens"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "portal": "admin"
        })
        if r.status_code != 200:
            pytest.skip(f"Admin login failed: {r.status_code} - {r.text[:200]}")
        data = r.json()
        portal_tokens = data.get("portal_tokens", {})
        session.headers.update({
            "X-Admin-Token": portal_tokens.get("admin") or portal_tokens.get("admin") or data.get("admin_token") or data.get("token") or "",
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        })
        return session

    def test_enterprise_resource_coordination_returns_200_for_admin(self, admin_session):
        """Admin can access GET /api/oppc/enterprise/resource-coordination"""
        r = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Verify canonical structure
        assert "planning_cycle" in data
        assert "window" in data
        assert "projects" in data
        assert "conflicts" in data
        assert "recommendations" in data
        assert "recovery_plans" in data
        assert "summary" in data
        # Verify summary fields
        summary = data["summary"]
        assert "active_projects" in summary
        assert "resource_conflicts" in summary
        assert "overdue_recovery_plans" in summary
        print(f"Enterprise resource coordination: {summary['active_projects']} projects, {summary['resource_conflicts']} conflicts")

    def test_executive_operations_center_returns_200_for_admin(self, admin_session):
        """Admin can access GET /api/oppc/enterprise/executive-operations-center"""
        r = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/executive-operations-center")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Verify canonical structure
        assert "generated_at" in data
        assert "planning_cycle" in data
        assert "summary" in data
        assert "what_is_happening_today" in data
        assert "what_is_at_risk" in data
        assert "resource_conflicts" in data
        assert "recovery_overdue" in data
        assert "projects_slipping" in data
        assert "leadership_required" in data
        assert "recommendations" in data
        # Verify summary fields
        summary = data["summary"]
        assert "open_variances" in summary
        assert "critical_variances" in summary
        assert "leadership_projects" in summary
        print(f"Executive operations center: {summary['open_variances']} open variances, {summary['leadership_projects']} leadership projects")

    def test_enterprise_routes_require_admin(self):
        """Non-admin users should get 403 on enterprise routes"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": PM_EMAIL,
            "password": PM_PASSWORD,
            "portal": "pm"
        })
        if r.status_code != 200:
            pytest.skip(f"PM login failed: {r.status_code}")
        data = r.json()
        portal_tokens = data.get("portal_tokens", {})
        session.headers.update({
            "X-Pm-Token": portal_tokens.get("pm") or portal_tokens.get("pm") or data.get("pm_token") or data.get("token") or "",
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        })
        # Try enterprise resource coordination
        r = session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        assert r.status_code == 403, f"Expected 403 for PM on enterprise route, got {r.status_code}"
        # Try executive operations center
        r = session.get(f"{BASE_URL}/api/oppc/enterprise/executive-operations-center")
        assert r.status_code == 403, f"Expected 403 for PM on executive route, got {r.status_code}"
        print("Enterprise routes correctly require admin access")


class TestOPPCVarianceIntelligence:
    """Tests for variance intelligence routes"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get admin session tokens"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "portal": "admin"
        })
        if r.status_code != 200:
            pytest.skip(f"Admin login failed: {r.status_code}")
        data = r.json()
        portal_tokens = data.get("portal_tokens", {})
        session.headers.update({
            "X-Admin-Token": portal_tokens.get("admin") or data.get("admin_token") or data.get("token") or "",
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        })
        return session

    @pytest.fixture(scope="class")
    def pm_forensic_session(self):
        """Get PM forensic session tokens (has scoped projects)"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": PM_FORENSIC_EMAIL,
            "password": PM_FORENSIC_PASSWORD,
            "portal": "pm"
        })
        if r.status_code != 200:
            pytest.skip(f"PM forensic login failed: {r.status_code}")
        data = r.json()
        portal_tokens = data.get("portal_tokens", {})
        session.headers.update({
            "X-Pm-Token": portal_tokens.get("pm") or data.get("pm_token") or data.get("token") or "",
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        })
        return session

    def test_variance_intelligence_returns_canonical_taxonomy(self, admin_session):
        """GET /api/oppc/projects/{project_number}/variance-intelligence returns taxonomy"""
        # Use admin to find a project with data
        coord = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        if coord.status_code != 200:
            pytest.skip("Could not get enterprise coordination")
        projects = coord.json().get("projects", [])
        if not projects:
            pytest.skip("No projects in enterprise coordination")
        project_number = projects[0].get("project_number")
        
        r = admin_session.get(f"{BASE_URL}/api/oppc/projects/{project_number}/variance-intelligence")
        if r.status_code == 403:
            pytest.skip(f"Admin does not have scope for project {project_number}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Verify canonical structure
        assert "project_number" in data
        assert "planning_cycle" in data
        assert "week_window" in data
        assert "summary" in data
        assert "taxonomy" in data
        assert "variances" in data
        # Verify taxonomy
        taxonomy = data["taxonomy"]
        assert "variance_types" in taxonomy
        assert "root_causes" in taxonomy
        assert "severities" in taxonomy
        assert "controllability" in taxonomy
        assert "statuses" in taxonomy
        print(f"Variance intelligence for {project_number}: {data['summary'].get('total_variances', 0)} variances")

    def test_execution_workspace_embeds_variance_intelligence(self, admin_session):
        """GET /api/oppc/projects/{project_number}/execution-workspace includes variance_intelligence"""
        coord = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        if coord.status_code != 200:
            pytest.skip("Could not get enterprise coordination")
        projects = coord.json().get("projects", [])
        if not projects:
            pytest.skip("No projects in enterprise coordination")
        project_number = projects[0].get("project_number")
        
        r = admin_session.get(f"{BASE_URL}/api/oppc/projects/{project_number}/execution-workspace")
        if r.status_code == 403:
            pytest.skip(f"Admin does not have scope for project {project_number}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Verify variance_intelligence is embedded
        assert "variance_intelligence" in data, "variance_intelligence should be embedded in execution workspace"
        vi = data["variance_intelligence"]
        assert "summary" in vi
        assert "variances" in vi
        assert "taxonomy" in vi
        print(f"Execution workspace for {project_number} embeds variance_intelligence with {vi['summary'].get('total_variances', 0)} variances")


class TestOPPCVarianceReview:
    """Tests for variance review PUT endpoint"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get admin session tokens"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "portal": "admin"
        })
        if r.status_code != 200:
            pytest.skip(f"Admin login failed: {r.status_code}")
        data = r.json()
        portal_tokens = data.get("portal_tokens", {})
        session.headers.update({
            "X-Admin-Token": portal_tokens.get("admin") or data.get("admin_token") or data.get("token") or "",
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        })
        return session

    def test_variance_review_validates_taxonomy(self, admin_session):
        """PUT /api/oppc/projects/{project_number}/variances/{variance_key} validates taxonomy"""
        coord = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        if coord.status_code != 200:
            pytest.skip("Could not get enterprise coordination")
        projects = coord.json().get("projects", [])
        if not projects:
            pytest.skip("No projects in enterprise coordination")
        project_number = projects[0].get("project_number")
        
        # Get variance intelligence to find a variance key
        vi = admin_session.get(f"{BASE_URL}/api/oppc/projects/{project_number}/variance-intelligence")
        if vi.status_code == 403:
            pytest.skip(f"Admin does not have scope for project {project_number}")
        if vi.status_code != 200:
            pytest.skip(f"Could not get variance intelligence: {vi.status_code}")
        variances = vi.json().get("variances", [])
        if not variances:
            pytest.skip("No variances found for testing")
        variance_key = variances[0].get("variance_key")
        
        # Test invalid status
        r = admin_session.put(f"{BASE_URL}/api/oppc/projects/{project_number}/variances/{variance_key}", json={
            "status": "invalid_status"
        })
        assert r.status_code == 422, f"Expected 422 for invalid status, got {r.status_code}"
        
        # Test invalid primary_cause
        r = admin_session.put(f"{BASE_URL}/api/oppc/projects/{project_number}/variances/{variance_key}", json={
            "status": "under_review",
            "primary_cause": "invalid_cause"
        })
        assert r.status_code == 422, f"Expected 422 for invalid primary_cause, got {r.status_code}"
        
        # Test invalid controllability
        r = admin_session.put(f"{BASE_URL}/api/oppc/projects/{project_number}/variances/{variance_key}", json={
            "status": "under_review",
            "controllability": "invalid_controllability"
        })
        assert r.status_code == 422, f"Expected 422 for invalid controllability, got {r.status_code}"
        
        print(f"Variance review taxonomy validation working for {variance_key}")

    def test_variance_review_saves_and_returns_workspace(self, admin_session):
        """PUT /api/oppc/projects/{project_number}/variances/{variance_key} saves review and returns workspace"""
        coord = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        if coord.status_code != 200:
            pytest.skip("Could not get enterprise coordination")
        projects = coord.json().get("projects", [])
        if not projects:
            pytest.skip("No projects in enterprise coordination")
        project_number = projects[0].get("project_number")
        
        vi = admin_session.get(f"{BASE_URL}/api/oppc/projects/{project_number}/variance-intelligence")
        if vi.status_code == 403:
            pytest.skip(f"Admin does not have scope for project {project_number}")
        if vi.status_code != 200:
            pytest.skip(f"Could not get variance intelligence: {vi.status_code}")
        variances = vi.json().get("variances", [])
        if not variances:
            pytest.skip("No variances found for testing")
        variance_key = variances[0].get("variance_key")
        
        # Save a valid variance review
        r = admin_session.put(f"{BASE_URL}/api/oppc/projects/{project_number}/variances/{variance_key}", json={
            "status": "under_review",
            "primary_cause": "weather",
            "contributing_causes": ["planning"],
            "controllability": "not_preventable",
            "cause_notes": "TEST: Rain delay during paving window",
            "recovery_strategy": "weekend_work",
            "recovery_priority": "high",
            "recovery_owner_role": "pm",
            "requires_executive_review": False,
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("ok") is True
        assert "review" in data
        assert "workspace" in data
        assert "variance_intelligence" in data
        print(f"Variance review saved for {variance_key}")


class TestOPPCMondayReviewRegression:
    """Regression tests for Monday review flow after variance intelligence changes"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get admin session tokens"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "portal": "admin"
        })
        if r.status_code != 200:
            pytest.skip(f"Admin login failed: {r.status_code}")
        data = r.json()
        portal_tokens = data.get("portal_tokens", {})
        session.headers.update({
            "X-Admin-Token": portal_tokens.get("admin") or data.get("admin_token") or data.get("token") or "",
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        })
        return session

    def test_monday_review_start_still_works(self, admin_session):
        """POST /api/oppc/projects/{project_number}/monday-review/start still works"""
        coord = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        if coord.status_code != 200:
            pytest.skip("Could not get enterprise coordination")
        projects = coord.json().get("projects", [])
        if not projects:
            pytest.skip("No projects in enterprise coordination")
        project_number = projects[0].get("project_number")
        
        r = admin_session.post(f"{BASE_URL}/api/oppc/projects/{project_number}/monday-review/start", json={})
        if r.status_code == 403:
            pytest.skip(f"Admin does not have scope for project {project_number}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("ok") is True
        assert "monday_review" in data
        assert "variance_intelligence" in data
        print(f"Monday review start works for {project_number}")

    def test_activity_review_update_still_works(self, admin_session):
        """PUT /api/oppc/projects/{project_number}/monday-review/activities/{cost_code} still works"""
        coord = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        if coord.status_code != 200:
            pytest.skip("Could not get enterprise coordination")
        projects = coord.json().get("projects", [])
        if not projects:
            pytest.skip("No projects in enterprise coordination")
        project_number = projects[0].get("project_number")
        
        # Get execution workspace to find an activity
        ws = admin_session.get(f"{BASE_URL}/api/oppc/projects/{project_number}/execution-workspace")
        if ws.status_code == 403:
            pytest.skip(f"Admin does not have scope for project {project_number}")
        if ws.status_code != 200:
            pytest.skip(f"Could not get execution workspace: {ws.status_code}")
        activities = ws.json().get("monday_review", {}).get("activities", [])
        if not activities:
            pytest.skip("No activities found for testing")
        cost_code = activities[0].get("code")
        
        # Update activity review
        r = admin_session.put(f"{BASE_URL}/api/oppc/projects/{project_number}/monday-review/activities/{cost_code}", json={
            "primary_cause": "weather",
            "controllability": "external",
            "recovery_strategy": "TEST: Add weekend shift",
            "recovery_owner_role": "pm",
            "forecast_impact": "No slip after recovery",
        })
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:300]}"
        data = r.json()
        assert data.get("ok") is True
        assert "monday_review" in data
        print(f"Activity review update works for {project_number}/{cost_code}")


class TestOPPCResourceConflicts:
    """Tests for enterprise resource conflict detection"""

    @pytest.fixture(scope="class")
    def admin_session(self):
        """Get admin session tokens"""
        session = requests.Session()
        r = session.post(f"{BASE_URL}/api/auth/multi-login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "portal": "admin"
        })
        if r.status_code != 200:
            pytest.skip(f"Admin login failed: {r.status_code}")
        data = r.json()
        portal_tokens = data.get("portal_tokens", {})
        session.headers.update({
            "X-Admin-Token": portal_tokens.get("admin") or data.get("admin_token") or data.get("token") or "",
            "X-Directory-Token": data.get("session_token") or data.get("directory_token") or "",
        })
        return session

    def test_resource_conflicts_have_canonical_structure(self, admin_session):
        """Resource conflicts have canonical structure with conflict_type, severity, why, recommendation"""
        r = admin_session.get(f"{BASE_URL}/api/oppc/enterprise/resource-coordination")
        assert r.status_code == 200
        data = r.json()
        conflicts = data.get("conflicts", [])
        if not conflicts:
            print("No resource conflicts found in preview data - this is expected if no shared resources")
            return
        
        for conflict in conflicts[:5]:
            assert "conflict_type" in conflict, "conflict should have conflict_type"
            assert "severity" in conflict, "conflict should have severity"
            assert "resource_key" in conflict, "conflict should have resource_key"
            assert "why" in conflict, "conflict should have why explanation"
            assert "recommendation" in conflict, "conflict should have recommendation"
            assert conflict["conflict_type"] in [
                "crew_conflict", "superintendent_overload", "equipment_conflict", "truck_conflict"
            ], f"Unknown conflict type: {conflict['conflict_type']}"
            assert conflict["severity"] in ["low", "medium", "high", "critical"], f"Unknown severity: {conflict['severity']}"
        
        print(f"Found {len(conflicts)} resource conflicts with canonical structure")
        for conflict in conflicts[:3]:
            print(f"  - {conflict['conflict_type']}: {conflict['resource_key']} ({conflict['severity']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
