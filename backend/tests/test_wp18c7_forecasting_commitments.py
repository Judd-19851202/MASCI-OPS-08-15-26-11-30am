"""
WP-18C7 Forecasting & Commitments Backend API Tests
====================================================
Tests the C7 governed forecast authority workspace for PM, Executive/Admin, 
and Field Leadership audiences.

Test Coverage:
- PM workspace GET
- PM commitment create/update
- Executive workspace GET
- Field Leadership workspace GET
- Verify forecasts/commitments data presence
- Verify audience/authority/versioning structures
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from test_credentials.md
PM_EMAIL = "pm.scope.forensic@example.com"
PM_PASSWORD = "ForensicPm2026!"
PM_PROJECT = "ZZ-FOR-ASSIGN-01"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
ADMIN_PROJECT = "ZZ-RUNTIME-CERT-2026"

FL_EMAIL = "cert.foreman@example.com"
FL_PASSWORD = "CertProof2026!"
FL_PROJECT = "ZZ-RUNTIME-CERT-2026"


class TestPmForecastingWorkspace:
    """PM Forecasting Workspace API Tests"""
    
    @pytest.fixture(scope="class")
    def pm_token(self):
        """Get PM authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        pytest.skip(f"PM login failed: {response.status_code} - {response.text}")
    
    def test_pm_forecasting_workspace_get(self, pm_token):
        """Test PM can GET forecasting workspace for scoped project"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/workspace",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions - validate response structure
        data = response.json()
        
        # Verify audience is set to PM
        assert data.get("audience") == "pm", f"Expected audience 'pm', got {data.get('audience')}"
        
        # Verify authority_boundaries structure exists
        assert "authority_boundaries" in data, "Missing authority_boundaries in response"
        boundaries = data["authority_boundaries"]
        assert "schedule_forecast_authority" in boundaries
        assert "production_authority" in boundaries
        assert "manual_commitment_authority" in boundaries
        
        # Verify versioning structure exists
        assert "versioning" in data, "Missing versioning in response"
        versioning = data["versioning"]
        assert "current_version_id" in versioning or "version_number" in versioning
        
        # Verify schedule structure
        assert "schedule" in data, "Missing schedule in response"
        
        # Verify production structure
        assert "production" in data, "Missing production in response"
        
        # Verify commitments structure
        assert "commitments" in data, "Missing commitments in response"
        commitments = data["commitments"]
        assert "lifecycle_counts" in commitments or "items" in commitments
        
        # Verify confidence structure
        assert "confidence" in data, "Missing confidence in response"
        
        print(f"PM workspace loaded successfully for project {PM_PROJECT}")
        print(f"  - Audience: {data.get('audience')}")
        print(f"  - Generated at: {data.get('generated_at')}")
        print(f"  - Schedule status: {data.get('schedule', {}).get('status')}")
        print(f"  - Production status: {data.get('production', {}).get('status')}")
    
    def test_pm_commitment_create(self, pm_token):
        """Test PM can create an operator commitment"""
        payload = {
            "family": "milestone_quantity",
            "status": "proposed",
            "title": "TEST_C7_Commitment_Create",
            "description": "Test commitment created by C7 testing agent",
            "due_date": "2026-12-31",
            "linked_unit": "LF",
            "target_quantity": 100.0,
            "target_hours": 0.0,
            "target_amount": 0.0,
            "confidence": "medium",
            "evidence_note": "Testing C7 commitment creation",
            "note": "Initial creation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/commitments",
            headers={"X-PM-Token": pm_token, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data.get("ok") is True, "Expected ok=True in response"
        assert "commitment" in data, "Missing commitment in response"
        
        commitment = data["commitment"]
        assert commitment.get("title") == payload["title"], f"Title mismatch"
        assert commitment.get("family") == payload["family"], f"Family mismatch"
        assert commitment.get("status") == payload["status"], f"Status mismatch"
        assert "commitment_id" in commitment, "Missing commitment_id"
        
        # Store commitment_id for update test
        self.__class__.created_commitment_id = commitment["commitment_id"]
        
        print(f"Commitment created successfully: {commitment['commitment_id']}")
        print(f"  - Title: {commitment.get('title')}")
        print(f"  - Status: {commitment.get('status')}")
        print(f"  - Family: {commitment.get('family')}")
    
    def test_pm_commitment_update(self, pm_token):
        """Test PM can update commitment lifecycle status and note"""
        commitment_id = getattr(self.__class__, "created_commitment_id", None)
        if not commitment_id:
            pytest.skip("No commitment_id from create test")
        
        payload = {
            "family": "milestone_quantity",
            "status": "committed",
            "title": "TEST_C7_Commitment_Create",
            "description": "Test commitment updated by C7 testing agent",
            "due_date": "2026-12-31",
            "linked_unit": "LF",
            "target_quantity": 100.0,
            "target_hours": 0.0,
            "target_amount": 0.0,
            "confidence": "high",
            "evidence_note": "Testing C7 commitment update",
            "note": "Status updated to committed"
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/commitments/{commitment_id}",
            headers={"X-PM-Token": pm_token, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data.get("ok") is True, "Expected ok=True in response"
        assert "commitment" in data, "Missing commitment in response"
        
        commitment = data["commitment"]
        assert commitment.get("status") == "committed", f"Expected status 'committed', got {commitment.get('status')}"
        assert commitment.get("confidence") == "high", f"Expected confidence 'high', got {commitment.get('confidence')}"
        
        # Verify history was updated
        history = commitment.get("history", [])
        assert len(history) > 0, "Expected history entries after update"
        
        print(f"Commitment updated successfully: {commitment_id}")
        print(f"  - New status: {commitment.get('status')}")
        print(f"  - New confidence: {commitment.get('confidence')}")
        print(f"  - History entries: {len(history)}")
    
    def test_pm_commitment_appears_in_register(self, pm_token):
        """Test that created commitment appears in the commitment register"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/workspace",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        commitments = data.get("commitments", {}).get("items", [])
        commitment_id = getattr(self.__class__, "created_commitment_id", None)
        
        if commitment_id:
            found = any(c.get("commitment_id") == commitment_id for c in commitments)
            assert found, f"Created commitment {commitment_id} not found in register"
            print(f"Commitment {commitment_id} found in register with {len(commitments)} total items")
    
    def test_pm_snapshot_capture(self, pm_token):
        """Test PM can capture a forecast version snapshot"""
        payload = {"note": "TEST_C7_Snapshot_Capture"}
        
        response = requests.post(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/snapshots",
            headers={"X-PM-Token": pm_token, "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "versioning" in data, "Missing versioning in response"
        
        versioning = data["versioning"]
        assert "current_version_id" in versioning or "version_number" in versioning
        
        print(f"Snapshot captured successfully")
        print(f"  - Version: {versioning.get('version_number')}")
        print(f"  - Persisted: {versioning.get('persisted')}")


class TestAdminForecastingWorkspace:
    """Executive/Admin Forecasting Workspace API Tests"""
    
    @pytest.fixture(scope="class")
    def admin_tokens(self):
        """Get Admin authentication tokens via multi-login"""
        # Step 1: Multi-login to get directory token
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip(f"Admin multi-login failed: {response.status_code} - {response.text}")
        
        data = response.json()
        directory_token = data.get("directory_token") or data.get("token")
        admin_token = data.get("admin_token") or data.get("token")
        
        if not directory_token:
            pytest.skip("No directory_token in multi-login response")
        
        return {"directory_token": directory_token, "admin_token": admin_token}
    
    def test_admin_forecasting_workspace_get(self, admin_tokens):
        """Test Executive/Admin can GET governed read-only workspace"""
        headers = {
            "X-Admin-Token": admin_tokens.get("admin_token", ""),
            "X-Directory-Token": admin_tokens.get("directory_token", "")
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{ADMIN_PROJECT}/forecasting/workspace",
            headers=headers,
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        
        # Verify audience is set to executive
        assert data.get("audience") == "executive", f"Expected audience 'executive', got {data.get('audience')}"
        
        # Verify authority_boundaries structure
        assert "authority_boundaries" in data, "Missing authority_boundaries"
        
        # Verify versioning structure
        assert "versioning" in data, "Missing versioning"
        
        # Verify schedule structure
        assert "schedule" in data, "Missing schedule"
        
        # Verify production structure
        assert "production" in data, "Missing production"
        
        # Verify commitments structure
        assert "commitments" in data, "Missing commitments"
        
        # Verify confidence structure
        assert "confidence" in data, "Missing confidence"
        
        print(f"Admin workspace loaded successfully for project {ADMIN_PROJECT}")
        print(f"  - Audience: {data.get('audience')}")
        print(f"  - Generated at: {data.get('generated_at')}")
    
    def test_admin_snapshot_capture(self, admin_tokens):
        """Test Admin can capture executive version snapshot"""
        headers = {
            "X-Admin-Token": admin_tokens.get("admin_token", ""),
            "X-Directory-Token": admin_tokens.get("directory_token", ""),
            "Content-Type": "application/json"
        }
        
        payload = {"note": "TEST_C7_Admin_Snapshot"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/project-controls/projects/{ADMIN_PROJECT}/forecasting/snapshots",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "versioning" in data, "Missing versioning in response"
        
        print(f"Admin snapshot captured successfully")


class TestFieldLeadershipForecastingWorkspace:
    """Field Leadership Forecasting Workspace API Tests"""
    
    @pytest.fixture(scope="class")
    def fl_token(self):
        """Get Field Leadership authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/field-leadership/portal/login",
            json={"email": FL_EMAIL, "password": FL_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token")
        pytest.skip(f"FL login failed: {response.status_code} - {response.text}")
    
    def test_fl_forecasting_workspace_get(self, fl_token):
        """Test Field Leadership can GET constrained read-only forecast surface"""
        response = requests.get(
            f"{BASE_URL}/api/field-leadership/portal/projects/{FL_PROJECT}/forecasting",
            headers={"X-FL-Token": fl_token},
            timeout=30
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert data.get("ok") is True, "Expected ok=True in response"
        assert data.get("project_number") == FL_PROJECT, f"Project number mismatch"
        
        # Verify workspace structure
        assert "workspace" in data, "Missing workspace in response"
        workspace = data["workspace"]
        
        # Verify field_summary exists (FL-specific)
        assert "field_summary" in workspace, "Missing field_summary in FL workspace"
        
        # Verify production structure
        assert "production" in workspace, "Missing production in FL workspace"
        
        # Verify commitments structure (constrained view)
        assert "commitments" in workspace, "Missing commitments in FL workspace"
        
        # Verify schedule structure
        assert "schedule" in workspace, "Missing schedule in FL workspace"
        
        # Verify drivers structure
        assert "drivers" in workspace, "Missing drivers in FL workspace"
        
        # Verify constraints structure
        assert "constraints" in workspace, "Missing constraints in FL workspace"
        
        # Verify confidence structure
        assert "confidence" in workspace, "Missing confidence in FL workspace"
        
        print(f"FL workspace loaded successfully for project {FL_PROJECT}")
        print(f"  - Project: {data.get('project_number')}")
        print(f"  - Field summary present: {bool(workspace.get('field_summary'))}")
        
        # Verify field_summary contents
        field_summary = workspace.get("field_summary", {})
        print(f"  - Next week quantity: {field_summary.get('next_week_quantity_total')}")
        print(f"  - At-risk commitments: {field_summary.get('at_risk_commitments')}")


class TestForecastingDataIntegrity:
    """Tests for data integrity and structure validation"""
    
    @pytest.fixture(scope="class")
    def pm_token(self):
        """Get PM authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/pm/login",
            json={"email": PM_EMAIL, "password": PM_PASSWORD},
            timeout=30
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"PM login failed: {response.status_code}")
    
    def test_workspace_has_required_sections(self, pm_token):
        """Verify workspace contains all required C7 sections"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/workspace",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Required top-level sections
        required_sections = [
            "project",
            "audience",
            "authority_boundaries",
            "generated_at",
            "schedule",
            "production",
            "resources",
            "cost",
            "constraints",
            "commitments",
            "forecast_vs_actual",
            "commitment_vs_actual",
            "work_block_lineage",
            "confidence",
            "drivers",
            "versioning"
        ]
        
        missing = [s for s in required_sections if s not in data]
        assert not missing, f"Missing required sections: {missing}"
        
        print(f"All {len(required_sections)} required sections present in workspace")
    
    def test_commitment_lifecycle_counts_structure(self, pm_token):
        """Verify commitment lifecycle counts structure"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/workspace",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        commitments = data.get("commitments", {})
        lifecycle_counts = commitments.get("lifecycle_counts", {})
        
        # Expected lifecycle statuses
        expected_statuses = ["proposed", "committed", "at_risk", "missed", "met", "revised", "cancelled"]
        
        for status in expected_statuses:
            assert status in lifecycle_counts, f"Missing lifecycle status: {status}"
            assert isinstance(lifecycle_counts[status], int), f"Lifecycle count for {status} should be int"
        
        print(f"Lifecycle counts structure valid: {lifecycle_counts}")
    
    def test_confidence_structure(self, pm_token):
        """Verify confidence report structure"""
        response = requests.get(
            f"{BASE_URL}/api/pm/project-controls/projects/{PM_PROJECT}/forecasting/workspace",
            headers={"X-PM-Token": pm_token},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        confidence = data.get("confidence", {})
        
        # Verify overall confidence
        assert "overall" in confidence, "Missing overall confidence"
        assert confidence["overall"] in ["high", "medium", "review_required"], f"Invalid overall confidence: {confidence['overall']}"
        
        # Verify production band counts
        assert "production_band_counts" in confidence, "Missing production_band_counts"
        
        # Verify lineage confidence
        assert "lineage_confidence" in confidence, "Missing lineage_confidence"
        
        print(f"Confidence structure valid: overall={confidence.get('overall')}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
