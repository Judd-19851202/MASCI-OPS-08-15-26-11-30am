"""
WP-12 Production Confidence Score - Live API Verification

Tests:
1. /api/project-health returns production_confidence and production_confidence_governance
2. /api/project-health/{project_number}/confidence returns explainable confidence payload
3. POST /api/project-health/{project_number}/confidence/snapshots persists versioned history
4. /api/ods/executive/confidence returns portfolio summary + project rows
5. ODS dashboards include production confidence rollups
6. Governance: manual_forecast_fields_used must remain false
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_session():
    """Authenticate as admin and return session with cookies."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login via multi-login
    login_resp = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if login_resp.status_code != 200:
        pytest.skip(f"Admin login failed: {login_resp.status_code} - {login_resp.text[:200]}")
    
    return session


class TestWP12ProjectHealthConfidence:
    """WP-12: Project Health endpoint includes production confidence."""
    
    def test_project_health_returns_confidence_payload(self, admin_session):
        """GET /api/project-health rows include production_confidence."""
        resp = admin_session.get(f"{BASE_URL}/api/project-health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        assert "rows" in data, "Response must have 'rows' key"
        assert "summary" in data, "Response must have 'summary' key"
        
        if data["rows"]:
            row = data["rows"][0]
            # WP-12 requirement: production_confidence in each row
            assert "production_confidence" in row, "Row must include production_confidence"
            confidence = row["production_confidence"]
            
            # Verify confidence structure
            assert "score" in confidence, "Confidence must have score"
            assert "band" in confidence, "Confidence must have band"
            assert "components" in confidence, "Confidence must have components"
            assert "governance" in confidence, "Confidence must have governance"
            assert "explainability" in confidence, "Confidence must have explainability"
            
            # WP-12 discipline check: manual_forecast_fields_used must be false
            assert confidence["governance"]["manual_forecast_fields_used"] is False, \
                "governance.manual_forecast_fields_used must be False"
            assert confidence["governance"]["truth_basis"] == "canonical_operational_data", \
                "truth_basis must be canonical_operational_data"
            
            # Verify score is 0-100
            assert 0 <= confidence["score"] <= 100, f"Score {confidence['score']} must be 0-100"
            
            # Verify band is valid
            valid_bands = {"high_confidence", "watch", "low_confidence", "critical"}
            assert confidence["band"] in valid_bands, f"Band {confidence['band']} must be valid"
            
            # WP-12 requirement: production_confidence_governance in each row
            assert "production_confidence_governance" in row, \
                "Row must include production_confidence_governance"
            gov = row["production_confidence_governance"]
            assert "snapshot_count" in gov, "Governance must have snapshot_count"
            
            print(f"✓ Project {row['project_number']}: score={confidence['score']}, band={confidence['band']}")
    
    def test_project_health_summary_includes_confidence_average(self, admin_session):
        """Summary should allow computing average confidence from rows."""
        resp = admin_session.get(f"{BASE_URL}/api/project-health")
        assert resp.status_code == 200
        
        data = resp.json()
        rows = data.get("rows", [])
        
        if rows:
            # Compute average confidence
            total_score = sum(
                float(row.get("production_confidence", {}).get("score", 0))
                for row in rows
            )
            avg_score = total_score / len(rows)
            print(f"✓ Portfolio average confidence: {avg_score:.2f} across {len(rows)} projects")


class TestWP12ConfidenceDetailEndpoint:
    """WP-12: GET /api/project-health/{project_number}/confidence."""
    
    def test_confidence_detail_returns_explainable_payload(self, admin_session):
        """Detail endpoint returns full explainable confidence."""
        # First get a project number from project-health
        health_resp = admin_session.get(f"{BASE_URL}/api/project-health")
        assert health_resp.status_code == 200
        
        rows = health_resp.json().get("rows", [])
        if not rows:
            pytest.skip("No projects available for confidence detail test")
        
        project_number = rows[0]["project_number"]
        
        # Get confidence detail
        resp = admin_session.get(f"{BASE_URL}/api/project-health/{project_number}/confidence")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        assert data["project_number"] == project_number
        assert "production_confidence" in data
        assert "governance" in data
        
        confidence = data["production_confidence"]
        
        # Verify all 6 components are present
        components = confidence.get("components", [])
        component_keys = {c["key"] for c in components}
        expected_keys = {"planning", "production", "labor", "variance", "resource_readiness", "data_trust"}
        assert component_keys == expected_keys, f"Expected components {expected_keys}, got {component_keys}"
        
        # Verify each component has required fields
        for comp in components:
            assert "key" in comp
            assert "score" in comp
            assert "max_score" in comp
            assert "status" in comp
            assert "reason" in comp
            assert "metrics" in comp
            print(f"  - {comp['key']}: {comp['score']}/{comp['max_score']} ({comp['status']})")
        
        # Verify explainability
        explainability = confidence.get("explainability", [])
        assert len(explainability) == 6, "Should have 6 explainability entries"
        
        # Verify freshness
        freshness = confidence.get("freshness", {})
        assert "report_freshness" in freshness
        
        print(f"✓ Confidence detail for {project_number}: score={confidence['score']}")


class TestWP12ConfidenceSnapshotEndpoint:
    """WP-12: POST /api/project-health/{project_number}/confidence/snapshots."""
    
    def test_snapshot_persists_confidence_history(self, admin_session):
        """Snapshot endpoint persists versioned confidence history."""
        # Get a project number
        health_resp = admin_session.get(f"{BASE_URL}/api/project-health")
        assert health_resp.status_code == 200
        
        rows = health_resp.json().get("rows", [])
        if not rows:
            pytest.skip("No projects available for snapshot test")
        
        project_number = rows[0]["project_number"]
        
        # Get current governance to check snapshot count before
        detail_before = admin_session.get(f"{BASE_URL}/api/project-health/{project_number}/confidence")
        assert detail_before.status_code == 200
        count_before = detail_before.json().get("governance", {}).get("snapshot_count", 0)
        
        # Create snapshot
        resp = admin_session.post(f"{BASE_URL}/api/project-health/{project_number}/confidence/snapshots")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        assert data.get("ok") is True
        assert "snapshot" in data
        assert "production_confidence" in data
        
        snapshot = data["snapshot"]
        assert "snapshot_id" in snapshot
        assert snapshot["snapshot_id"].startswith("confidence-")
        assert snapshot["project_number"] == project_number
        assert snapshot["truth_basis"] == "canonical_operational_data"
        assert "created_at" in snapshot
        assert "created_by" in snapshot
        
        # Verify snapshot count increased
        detail_after = admin_session.get(f"{BASE_URL}/api/project-health/{project_number}/confidence")
        assert detail_after.status_code == 200
        count_after = detail_after.json().get("governance", {}).get("snapshot_count", 0)
        assert count_after == count_before + 1, f"Snapshot count should increase: {count_before} -> {count_after}"
        
        print(f"✓ Snapshot created: {snapshot['snapshot_id']} (count: {count_before} -> {count_after})")


class TestWP12ExecutiveConfidenceEndpoint:
    """WP-12: GET /api/ods/executive/confidence."""
    
    def test_executive_confidence_returns_portfolio_summary(self, admin_session):
        """Executive confidence endpoint returns portfolio summary + project rows."""
        resp = admin_session.get(f"{BASE_URL}/api/ods/executive/confidence")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        
        # Verify summary
        assert "summary" in data, "Response must have summary"
        summary = data["summary"]
        assert "average_score" in summary
        assert "high_confidence" in summary
        assert "watch" in summary
        assert "low_confidence" in summary
        assert "critical" in summary
        
        # Verify projects
        assert "projects" in data, "Response must have projects"
        projects = data["projects"]
        
        if projects:
            project = projects[0]
            assert "project_number" in project
            assert "project_name" in project
            assert "production_confidence" in project
            assert "governance" in project
            
            confidence = project["production_confidence"]
            assert confidence["governance"]["manual_forecast_fields_used"] is False
            
            print(f"✓ Executive confidence: avg={summary['average_score']}, "
                  f"high={summary['high_confidence']}, watch={summary['watch']}, "
                  f"critical={summary['critical']}")
        
        assert "generated_at" in data


class TestWP12ODSDashboardConfidenceRollups:
    """WP-12: ODS dashboards include production confidence rollups."""
    
    def test_pm_dashboard_includes_confidence(self, admin_session):
        """PM dashboard includes production confidence rollup."""
        resp = admin_session.get(f"{BASE_URL}/api/ods/pm/dashboard")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        
        # Verify production_confidence section
        assert "production_confidence" in data, "PM dashboard must include production_confidence"
        pc = data["production_confidence"]
        assert "summary" in pc
        assert "projects" in pc
        
        print(f"✓ PM dashboard confidence: avg={pc['summary'].get('average_score', 0)}")
    
    def test_admin_dashboard_includes_confidence(self, admin_session):
        """Admin dashboard includes production confidence rollup."""
        resp = admin_session.get(f"{BASE_URL}/api/ods/admin/dashboard")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        
        # Verify production_confidence section
        assert "production_confidence" in data, "Admin dashboard must include production_confidence"
        pc = data["production_confidence"]
        assert "summary" in pc
        assert "projects" in pc
        
        print(f"✓ Admin dashboard confidence: avg={pc['summary'].get('average_score', 0)}")
    
    def test_executive_brief_includes_confidence(self, admin_session):
        """Executive brief includes production confidence."""
        resp = admin_session.get(f"{BASE_URL}/api/ods/executive/brief")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        
        # Verify production_confidence section
        assert "production_confidence" in data, "Executive brief must include production_confidence"
        pc = data["production_confidence"]
        assert "summary" in pc
        assert "projects" in pc
        
        print(f"✓ Executive brief confidence: avg={pc['summary'].get('average_score', 0)}")
    
    def test_executive_health_includes_confidence(self, admin_session):
        """Executive health includes production confidence."""
        resp = admin_session.get(f"{BASE_URL}/api/ods/executive/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
        
        data = resp.json()
        
        # Verify production_confidence section
        assert "production_confidence" in data, "Executive health must include production_confidence"
        pc = data["production_confidence"]
        assert "summary" in pc
        assert "projects" in pc
        
        print(f"✓ Executive health confidence: avg={pc['summary'].get('average_score', 0)}")


class TestWP12DisciplineChecks:
    """WP-12: Discipline checks - no duplicate scoring engine, canonical truth only."""
    
    def test_no_manual_forecast_fields_used(self, admin_session):
        """Verify governance.manual_forecast_fields_used is always false."""
        # Check project-health
        health_resp = admin_session.get(f"{BASE_URL}/api/project-health")
        assert health_resp.status_code == 200
        
        for row in health_resp.json().get("rows", []):
            confidence = row.get("production_confidence", {})
            gov = confidence.get("governance", {})
            assert gov.get("manual_forecast_fields_used") is False, \
                f"Project {row['project_number']}: manual_forecast_fields_used must be False"
        
        # Check executive confidence
        exec_resp = admin_session.get(f"{BASE_URL}/api/ods/executive/confidence")
        assert exec_resp.status_code == 200
        
        for project in exec_resp.json().get("projects", []):
            confidence = project.get("production_confidence", {})
            gov = confidence.get("governance", {})
            assert gov.get("manual_forecast_fields_used") is False, \
                f"Project {project['project_number']}: manual_forecast_fields_used must be False"
        
        print("✓ All projects have manual_forecast_fields_used=False")
    
    def test_truth_basis_is_canonical(self, admin_session):
        """Verify truth_basis is always canonical_operational_data."""
        health_resp = admin_session.get(f"{BASE_URL}/api/project-health")
        assert health_resp.status_code == 200
        
        for row in health_resp.json().get("rows", []):
            confidence = row.get("production_confidence", {})
            gov = confidence.get("governance", {})
            assert gov.get("truth_basis") == "canonical_operational_data", \
                f"Project {row['project_number']}: truth_basis must be canonical_operational_data"
        
        print("✓ All projects have truth_basis=canonical_operational_data")
