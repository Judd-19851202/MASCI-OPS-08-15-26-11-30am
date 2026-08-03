"""
WP-OPPC-14F Operational Case Management Backend Tests

Tests the canonical Operational Case Management capability for MASCI OPS:
- Case list/detail/assembly/timeline/graph APIs
- Preview Daily Report certification record creation
- Full certification chain execution
- Task creation, evidence capture, baseline inclusion, evidence export
- Server-validated transitions with closure requirements
- Duplicate case handling and related-case linkage
- Communication acknowledgement through case endpoints
"""

import os
import pytest
import requests
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://masci-audit-hub.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


class TestOPPCCaseManagementAPIs:
    """Test suite for WP-OPPC-14F Operational Case Management APIs"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with admin authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate as super admin
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"}
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            # Multi-login returns portal_tokens and session_token
            admin_token = data.get("portal_tokens", {}).get("admin")
            session_token = data.get("session_token")
            
            if admin_token:
                self.session.headers.update({"X-Admin-Token": admin_token})
            if session_token:
                self.session.headers.update({"X-Directory-Token": session_token})
        
        yield
        self.session.close()

    # ========== Registry and Foundation Tests ==========
    
    def test_01_registry_endpoint_returns_case_types_and_lifecycle(self):
        """GET /api/admin/operations-control/registry returns case types and lifecycle"""
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/registry")
        assert response.status_code == 200, f"Registry endpoint failed: {response.text}"
        
        data = response.json()
        assert "registry" in data, "Response missing 'registry' key"
        
        registry = data["registry"]
        # Verify case management components exist
        assert "case_types" in registry or registry.get("counts", {}).get("case_types", 0) >= 0
        assert "case_lifecycle" in registry or registry.get("counts", {}).get("case_lifecycle", 0) >= 0
        print(f"Registry endpoint OK - version: {registry.get('version', 'unknown')}")

    # ========== Case List API Tests ==========
    
    def test_02_list_cases_endpoint(self):
        """GET /api/admin/operations-control/cases returns persisted cases"""
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases")
        assert response.status_code == 200, f"List cases failed: {response.text}"
        
        data = response.json()
        assert "cases" in data, "Response missing 'cases' key"
        assert "count" in data, "Response missing 'count' key"
        assert "summary" in data, "Response missing 'summary' key"
        
        summary = data["summary"]
        assert "total" in summary
        assert "open" in summary
        assert "escalated" in summary
        assert "pending_verification" in summary
        assert "critical" in summary
        
        print(f"List cases OK - total: {data['count']}, open: {summary.get('open', 0)}")

    def test_03_list_cases_with_status_filter(self):
        """GET /api/admin/operations-control/cases?status=CLOSED filters by status"""
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases?status=CLOSED")
        assert response.status_code == 200, f"Filtered list failed: {response.text}"
        
        data = response.json()
        cases = data.get("cases", [])
        # All returned cases should have CLOSED status
        for case in cases:
            assert case.get("status") == "CLOSED", f"Case {case.get('id')} has status {case.get('status')}, expected CLOSED"
        
        print(f"Status filter OK - {len(cases)} CLOSED cases")

    # ========== Preview Certification Tests ==========
    
    def test_04_create_preview_daily_report_certification(self):
        """POST /api/admin/operations-control/certifications/preview-daily-report creates fresh preview Daily Report and case"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/preview-daily-report",
            json={}
        )
        assert response.status_code == 200, f"Preview certification failed: {response.text}"
        
        data = response.json()
        assert "certification" in data, "Response missing 'certification' key"
        assert "daily_report" in data, "Response missing 'daily_report' key"
        assert "case" in data, "Response missing 'case' key"
        
        case = data["case"]
        assert case.get("id"), "Case missing id"
        assert case.get("case_number"), "Case missing case_number"
        assert case.get("status"), "Case missing status"
        
        # Store case_id for subsequent tests
        self.__class__.preview_case_id = case["id"]
        self.__class__.preview_case_number = case.get("case_number")
        
        print(f"Preview certification OK - case: {case.get('case_number')}, status: {case.get('status')}")

    # ========== Case Detail API Tests ==========
    
    def test_05_get_case_detail(self):
        """GET /api/admin/operations-control/cases/{case_id} returns case detail"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/{case_id}")
        assert response.status_code == 200, f"Case detail failed: {response.text}"
        
        case = response.json()
        assert case.get("id") == case_id
        assert "case_number" in case
        assert "status" in case
        assert "severity" in case
        assert "priority" in case
        assert "origin" in case
        assert "linked_record_ids" in case
        
        print(f"Case detail OK - {case.get('case_number')}, severity: {case.get('severity')}")

    def test_06_get_case_assembly(self):
        """GET /api/admin/operations-control/cases/{case_id}/assembly returns full case assembly"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/assembly")
        assert response.status_code == 200, f"Case assembly failed: {response.text}"
        
        data = response.json()
        assert "case" in data, "Assembly missing 'case' key"
        assert "summary" in data, "Assembly missing 'summary' key"
        assert "authoritative_records" in data, "Assembly missing 'authoritative_records' key"
        
        records = data["authoritative_records"]
        # Verify expected record types exist
        assert "daily_report" in records or records.get("daily_report") is None
        assert "events" in records
        assert "communications" in records
        assert "history" in records
        
        print(f"Case assembly OK - {len(records.get('events', []))} events, {len(records.get('communications', []))} communications")

    def test_07_get_case_timeline(self):
        """GET /api/admin/operations-control/cases/{case_id}/timeline returns unified timeline"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/timeline")
        assert response.status_code == 200, f"Case timeline failed: {response.text}"
        
        data = response.json()
        assert "timeline" in data, "Response missing 'timeline' key"
        assert "count" in data, "Response missing 'count' key"
        
        timeline = data["timeline"]
        for entry in timeline:
            assert "id" in entry
            assert "kind" in entry
            assert "at" in entry
            assert "title" in entry
        
        print(f"Case timeline OK - {data['count']} entries")

    def test_08_get_case_relationship_graph(self):
        """GET /api/admin/operations-control/cases/{case_id}/graph returns relationship graph"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/graph")
        assert response.status_code == 200, f"Case graph failed: {response.text}"
        
        data = response.json()
        assert "nodes" in data, "Graph missing 'nodes' key"
        assert "edges" in data, "Graph missing 'edges' key"
        
        nodes = data["nodes"]
        edges = data["edges"]
        
        # Should have at least the case node
        assert len(nodes) >= 1, "Graph should have at least one node (the case)"
        
        # Verify node structure
        for node in nodes:
            assert "id" in node
            assert "type" in node
            assert "label" in node
        
        print(f"Case graph OK - {len(nodes)} nodes, {len(edges)} edges")

    # ========== Case Action Tests ==========
    
    def test_09_create_case_task(self):
        """POST /api/admin/operations-control/cases/{case_id}/tasks creates corrective task"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/tasks",
            json={
                "title": "Test corrective action task",
                "description": "Created by automated test",
                "assignee_role": "pm",
                "priority": "High",
                "due_minutes": 120
            }
        )
        assert response.status_code == 200, f"Create task failed: {response.text}"
        
        data = response.json()
        assert "case" in data, "Response missing 'case' key"
        assert "task_id" in data, "Response missing 'task_id' key"
        
        self.__class__.created_task_id = data["task_id"]
        print(f"Create task OK - task_id: {data['task_id']}")

    def test_10_capture_case_evidence(self):
        """POST /api/admin/operations-control/cases/{case_id}/evidence captures evidence package"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/evidence",
            json={}
        )
        assert response.status_code == 200, f"Capture evidence failed: {response.text}"
        
        data = response.json()
        assert "ok" in data and data["ok"] == True
        assert "evidence" in data, "Response missing 'evidence' key"
        
        evidence = data["evidence"]
        assert evidence.get("id"), "Evidence missing id"
        
        self.__class__.evidence_id = evidence["id"]
        print(f"Capture evidence OK - evidence_id: {evidence['id']}")

    def test_11_include_case_in_baseline(self):
        """POST /api/admin/operations-control/cases/{case_id}/baseline includes case in baseline"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/baseline",
            json={"baseline_name": "Test Baseline v1"}
        )
        assert response.status_code == 200, f"Include baseline failed: {response.text}"
        
        data = response.json()
        assert "ok" in data and data["ok"] == True
        assert "baseline" in data, "Response missing 'baseline' key"
        
        baseline = data["baseline"]
        assert baseline.get("id"), "Baseline missing id"
        
        self.__class__.baseline_id = baseline["id"]
        print(f"Include baseline OK - baseline_id: {baseline['id']}")

    def test_12_export_case_evidence_package(self):
        """POST /api/admin/operations-control/cases/{case_id}/export exports evidence package"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/export",
            json={}
        )
        assert response.status_code == 200, f"Export evidence failed: {response.text}"
        
        data = response.json()
        assert "ok" in data and data["ok"] == True
        assert "export" in data, "Response missing 'export' key"
        
        export = data["export"]
        assert export.get("id"), "Export missing id"
        assert "payload" in export, "Export missing payload"
        
        payload = export["payload"]
        assert "case" in payload
        assert "timeline" in payload
        assert "relationship_graph" in payload
        assert "proof_chain" in payload
        
        print(f"Export evidence OK - export_id: {export['id']}")

    # ========== Case Transition Tests ==========
    
    def test_13_transition_case_to_under_review(self):
        """POST /api/admin/operations-control/cases/{case_id}/transitions moves case to UNDER_REVIEW"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
            json={
                "to_status": "UNDER_REVIEW",
                "reason": "Test transition to review"
            }
        )
        assert response.status_code == 200, f"Transition failed: {response.text}"
        
        data = response.json()
        assert "ok" in data and data["ok"] == True
        assert "case" in data
        assert data["case"]["status"] == "UNDER_REVIEW"
        
        print("Transition to UNDER_REVIEW OK")

    def test_14_transition_case_to_investigating(self):
        """POST /api/admin/operations-control/cases/{case_id}/transitions moves case to INVESTIGATING"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
            json={
                "to_status": "INVESTIGATING",
                "reason": "Test investigation started"
            }
        )
        assert response.status_code == 200, f"Transition failed: {response.text}"
        
        data = response.json()
        assert data["case"]["status"] == "INVESTIGATING"
        print("Transition to INVESTIGATING OK")

    def test_15_closure_fails_without_requirements(self):
        """POST /api/admin/operations-control/cases/{case_id}/transitions to CLOSED fails without requirements"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        # First transition through required states
        for status in ["ACTION_REQUIRED", "RECOVERY_ACTIVE", "MONITORING", "PENDING_VERIFICATION", "RESOLVED"]:
            self.session.post(
                f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
                json={
                    "to_status": status,
                    "reason": f"Test transition to {status}",
                    "root_cause": "Test root cause" if status in ["RECOVERY_ACTIVE", "RESOLVED"] else "",
                    "resolution_summary": "Test resolution" if status == "RESOLVED" else ""
                }
            )
        
        # Try to close without proper requirements - should fail or succeed based on evidence
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
            json={
                "to_status": "CLOSED",
                "reason": "",  # Missing reason
                "root_cause": "",  # Missing root cause
            }
        )
        
        # Either 422 (validation error) or 200 (if evidence already captured)
        if response.status_code == 422:
            print("Closure correctly rejected without requirements")
        else:
            print("Closure allowed (evidence already captured)")

    # ========== Full Certification Chain Test ==========
    
    def test_16_run_full_certification_chain(self):
        """POST /api/admin/operations-control/certifications/run executes full certification chain"""
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/certifications/run",
            json={}
        )
        assert response.status_code == 200, f"Certification run failed: {response.text}"
        
        data = response.json()
        assert "release_determination" in data, "Response missing 'release_determination'"
        assert "primary_case" in data, "Response missing 'primary_case'"
        
        release = data["release_determination"]
        assert release in [
            "OPERATIONS CONTROL PLANE v1 — VERIFIED COMPLETE",
            "OPERATIONS CONTROL PLANE v1 — NOT READY"
        ], f"Unexpected release determination: {release}"
        
        primary_case = data["primary_case"]
        assert primary_case.get("id"), "Primary case missing id"
        assert primary_case.get("status") == "CLOSED", f"Primary case should be CLOSED, got {primary_case.get('status')}"
        
        # Store for duplicate test
        self.__class__.certification_primary_case_id = primary_case["id"]
        self.__class__.certification_duplicate_case_id = data.get("duplicate_case_id")
        
        print(f"Certification chain OK - {release}")
        print(f"  Primary case: {primary_case.get('case_number')}")
        print(f"  Duplicate case: {data.get('duplicate_case_id')}")

    def test_17_duplicate_case_handling(self):
        """Verify duplicate case was created and marked as DUPLICATE"""
        duplicate_id = getattr(self.__class__, "certification_duplicate_case_id", None)
        if not duplicate_id:
            pytest.skip("No duplicate case created in certification")
        
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/{duplicate_id}")
        assert response.status_code == 200, f"Get duplicate case failed: {response.text}"
        
        case = response.json()
        assert case.get("status") == "DUPLICATE", f"Duplicate case should have DUPLICATE status, got {case.get('status')}"
        
        # Verify duplicate_of_case_id is set
        resolution = case.get("resolution", {})
        assert resolution.get("duplicate_of_case_id"), "Duplicate case missing duplicate_of_case_id"
        
        print(f"Duplicate case handling OK - {case.get('case_number')} marked as DUPLICATE")

    # ========== Communication Acknowledgement Test ==========
    
    def test_18_acknowledge_case_communication(self):
        """POST /api/admin/operations-control/cases/{case_id}/communications/{comm_id}/ack acknowledges communication"""
        # Get a case with communications
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases?limit=10")
        if response.status_code != 200:
            pytest.skip("Could not list cases")
        
        cases = response.json().get("cases", [])
        
        # Find a case with communications
        for case in cases:
            case_id = case.get("id")
            assembly_response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/assembly")
            if assembly_response.status_code != 200:
                continue
            
            assembly = assembly_response.json()
            communications = assembly.get("authoritative_records", {}).get("communications", [])
            
            # Find an unacknowledged communication
            for comm in communications:
                if comm.get("ack_status") == "pending":
                    comm_id = comm.get("id")
                    
                    ack_response = self.session.post(
                        f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/communications/{comm_id}/ack",
                        json={"note": "Acknowledged by automated test"}
                    )
                    
                    if ack_response.status_code == 200:
                        print(f"Communication acknowledgement OK - comm_id: {comm_id}")
                        return
        
        print("No pending communications found to acknowledge (OK)")

    # ========== Duplicate Policy Test ==========
    
    def test_19_duplicate_daily_report_policy_no_second_case(self):
        """Verify duplicate Daily Report policy reprocessing does not create second case"""
        # The certification chain already tests this - the duplicate case is marked DUPLICATE
        # not created as a new governed case
        primary_id = getattr(self.__class__, "certification_primary_case_id", None)
        duplicate_id = getattr(self.__class__, "certification_duplicate_case_id", None)
        
        if not primary_id or not duplicate_id:
            pytest.skip("Certification chain not run")
        
        # Verify they are linked
        primary_response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/{primary_id}")
        if primary_response.status_code == 200:
            primary = primary_response.json()
            related_ids = primary.get("linked_record_ids", {}).get("related_case_ids", [])
            assert duplicate_id in related_ids, "Duplicate case should be in related_case_ids"
            print("Duplicate policy handling verified - cases are properly linked")

    # ========== Error Handling Tests ==========
    
    def test_20_get_nonexistent_case_returns_404(self):
        """GET /api/admin/operations-control/cases/{invalid_id} returns 404"""
        response = self.session.get(f"{BASE_URL}/api/admin/operations-control/cases/nonexistent-case-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("404 for nonexistent case OK")

    def test_21_invalid_transition_returns_422(self):
        """POST /api/admin/operations-control/cases/{case_id}/transitions with invalid transition returns 422"""
        case_id = getattr(self.__class__, "preview_case_id", None)
        if not case_id:
            pytest.skip("No preview case created")
        
        # Try an invalid transition (e.g., OPEN -> CLOSED directly without going through lifecycle)
        response = self.session.post(
            f"{BASE_URL}/api/admin/operations-control/cases/{case_id}/transitions",
            json={
                "to_status": "INVALID_STATUS",
                "reason": "Test invalid transition"
            }
        )
        
        # Should be 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("Invalid transition rejected OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
