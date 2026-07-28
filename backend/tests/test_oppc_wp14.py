"""
WP-OPPC-14 Operations Control Plane Testing
============================================
Tests for:
- Operational Registry / Event Catalog
- Daily Report -> OPPC proof chain
- Communication intents and acknowledgements
- Baseline snapshots
- Readiness evidence packages
- Escalation endpoint accessibility
"""
import os
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "http://localhost:8001"

# Test credentials from test_credentials.md
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PASSWORD = "Maddix123!"


class TestOPPCAuthentication:
    """Authentication setup for OPPC tests"""
    
    @pytest.fixture(scope="class")
    def admin_tokens(self):
        """Get admin and directory tokens via multi-login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        assert response.status_code == 200, f"Multi-login failed: {response.text}"
        data = response.json()
        
        admin_token = data.get("portal_tokens", {}).get("admin")
        # session_token is used as directory_token for session binding
        session_token = data.get("session_token")
        pm_token = data.get("portal_tokens", {}).get("pm")
        
        assert admin_token, "Admin token not found in multi-login response"
        assert session_token, "Session token not found in multi-login response"
        
        return {
            "admin_token": admin_token,
            "directory_token": session_token,  # session_token is the directory token
            "pm_token": pm_token
        }
    
    @pytest.fixture(scope="class")
    def auth_headers(self, admin_tokens):
        """Build auth headers for admin requests"""
        return {
            "X-Admin-Token": admin_tokens["admin_token"],
            "X-Directory-Token": admin_tokens["directory_token"],
            "Content-Type": "application/json"
        }


class TestOPPCRegistry(TestOPPCAuthentication):
    """Tests for GET /api/admin/operations-control/registry"""
    
    def test_registry_endpoint_returns_200(self, auth_headers):
        """Registry endpoint should return 200 with valid auth"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/registry",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Registry endpoint failed: {response.text}"
        print("PASS: Registry endpoint returns 200")
    
    def test_registry_contains_principles(self, auth_headers):
        """Registry should contain constitutional principles"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/registry",
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        registry = data.get("registry", {})
        
        # Check for principles
        principles = registry.get("principles", [])
        assert len(principles) >= 4, f"Expected at least 4 principles, got {len(principles)}"
        
        # Verify required principles exist
        principle_ids = [p.get("id") for p in principles]
        assert "transport_independence" in principle_ids, "Missing transport_independence principle"
        assert "operational_intent" in principle_ids, "Missing operational_intent principle"
        print(f"PASS: Registry contains {len(principles)} principles including transport_independence and operational_intent")
    
    def test_registry_contains_workflows(self, auth_headers):
        """Registry should contain registered workflows"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/registry",
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        registry = data.get("registry", {})
        
        counts = registry.get("counts", {})
        assert counts.get("workflows", 0) >= 1, "Expected at least 1 workflow"
        
        workflow_ids = registry.get("workflow_ids", [])
        assert "oppc.daily_report_to_oppc" in workflow_ids, "Missing oppc.daily_report_to_oppc workflow"
        print(f"PASS: Registry contains {counts.get('workflows')} workflows including oppc.daily_report_to_oppc")
    
    def test_registry_contains_events(self, auth_headers):
        """Registry should contain registered event IDs"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/registry",
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        registry = data.get("registry", {})
        
        counts = registry.get("counts", {})
        assert counts.get("events", 0) >= 3, "Expected at least 3 events"
        
        event_ids = registry.get("event_ids", [])
        assert "oppc.daily_report.submitted" in event_ids, "Missing oppc.daily_report.submitted event"
        print(f"PASS: Registry contains {counts.get('events')} events including oppc.daily_report.submitted")
    
    def test_registry_contains_communication_intents(self, auth_headers):
        """Registry should contain communication intents"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/registry",
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        registry = data.get("registry", {})
        
        counts = registry.get("counts", {})
        assert counts.get("communication_intents", 0) >= 1, "Expected at least 1 communication intent"
        
        intent_ids = registry.get("communication_intent_ids", [])
        assert "oppc.daily_report.notify_project_team" in intent_ids, "Missing oppc.daily_report.notify_project_team intent"
        print(f"PASS: Registry contains {counts.get('communication_intents')} communication intents")
    
    def test_registry_contains_transports(self, auth_headers):
        """Registry should contain transport providers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/registry",
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        registry = data.get("registry", {})
        
        counts = registry.get("counts", {})
        assert counts.get("transports", 0) >= 2, "Expected at least 2 transports"
        
        transport_ids = registry.get("transport_ids", [])
        assert "in_app.notification_feed" in transport_ids, "Missing in_app.notification_feed transport"
        assert "email.resend" in transport_ids, "Missing email.resend transport"
        print(f"PASS: Registry contains {counts.get('transports')} transports")
    
    def test_registry_has_hash(self, auth_headers):
        """Registry should have a registry hash"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/registry",
            headers=auth_headers,
            timeout=30
        )
        data = response.json()
        registry = data.get("registry", {})
        
        registry_hash = registry.get("registry_hash")
        assert registry_hash, "Registry hash is missing"
        assert len(registry_hash) >= 8, "Registry hash seems too short"
        print(f"PASS: Registry has hash: {registry_hash}")


class TestOPPCBaselines(TestOPPCAuthentication):
    """Tests for baseline snapshot endpoints"""
    
    def test_create_baseline_snapshot(self, auth_headers):
        """POST /api/admin/operations-control/baselines should create a baseline"""
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/baselines",
            json={"baseline_name": "Operations Control Plane v1"},
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Create baseline failed: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        
        baseline = data.get("baseline", {})
        assert baseline.get("id"), "Baseline should have an id"
        assert baseline.get("baseline_name") == "Operations Control Plane v1", "Baseline name mismatch"
        assert baseline.get("registry_hash"), "Baseline should have registry_hash"
        assert baseline.get("created_at"), "Baseline should have created_at"
        assert baseline.get("status") == "captured", "Baseline status should be captured"
        print(f"PASS: Created baseline snapshot with id: {baseline.get('id')}")
        return baseline.get("id")
    
    def test_list_baselines(self, auth_headers):
        """GET /api/admin/operations-control/baselines should list baselines"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/baselines",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"List baselines failed: {response.text}"
        
        data = response.json()
        assert "baselines" in data, "Response should have baselines array"
        assert "count" in data, "Response should have count"
        
        baselines = data.get("baselines", [])
        if baselines:
            baseline = baselines[0]
            assert baseline.get("id"), "Baseline should have id"
            assert baseline.get("baseline_name"), "Baseline should have baseline_name"
            print(f"PASS: Listed {len(baselines)} baselines")
        else:
            print("PASS: Baselines endpoint works (no baselines yet)")


class TestOPPCEvidence(TestOPPCAuthentication):
    """Tests for readiness evidence package endpoints"""
    
    def test_create_evidence_package(self, auth_headers):
        """POST /api/admin/operations-control/evidence should create evidence package"""
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/evidence",
            json={"workflow_id": "oppc.daily_report_to_oppc"},
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Create evidence failed: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        
        evidence = data.get("evidence", {})
        assert evidence.get("id"), "Evidence should have an id"
        assert evidence.get("workflow_id") == "oppc.daily_report_to_oppc", "Workflow ID mismatch"
        assert evidence.get("registry_hash"), "Evidence should have registry_hash"
        assert evidence.get("created_at"), "Evidence should have created_at"
        assert evidence.get("status") == "captured", "Evidence status should be captured"
        print(f"PASS: Created evidence package with id: {evidence.get('id')}")
        return evidence.get("id")
    
    def test_list_evidence_packages(self, auth_headers):
        """GET /api/admin/operations-control/evidence should list evidence packages"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/evidence",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"List evidence failed: {response.text}"
        
        data = response.json()
        assert "evidence" in data, "Response should have evidence array"
        assert "count" in data, "Response should have count"
        
        evidence_list = data.get("evidence", [])
        if evidence_list:
            evidence = evidence_list[0]
            assert evidence.get("id"), "Evidence should have id"
            assert evidence.get("workflow_id"), "Evidence should have workflow_id"
            print(f"PASS: Listed {len(evidence_list)} evidence packages")
        else:
            print("PASS: Evidence endpoint works (no evidence yet)")


class TestOPPCEscalations(TestOPPCAuthentication):
    """Tests for escalation endpoint"""
    
    def test_escalations_run_endpoint_accessible(self, auth_headers):
        """POST /api/admin/operations-control/escalations/run should be accessible"""
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/escalations/run",
            headers=auth_headers,
            timeout=30
        )
        # Should return 200, not 404
        assert response.status_code == 200, f"Escalations run endpoint returned {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Response should have ok=True"
        assert "checked_at" in data, "Response should have checked_at"
        assert "escalated_count" in data, "Response should have escalated_count"
        print(f"PASS: Escalations run endpoint accessible, escalated_count: {data.get('escalated_count')}")


class TestOPPCEvents(TestOPPCAuthentication):
    """Tests for control plane events endpoint"""
    
    def test_list_events(self, auth_headers):
        """GET /api/admin/operations-control/events should list events"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/events",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"List events failed: {response.text}"
        
        data = response.json()
        assert "events" in data, "Response should have events array"
        assert "count" in data, "Response should have count"
        print(f"PASS: Listed {data.get('count')} control plane events")


class TestOPPCCommunications(TestOPPCAuthentication):
    """Tests for control plane communications endpoint"""
    
    def test_list_communications(self, auth_headers):
        """GET /api/admin/operations-control/communications should list communications"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/communications",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"List communications failed: {response.text}"
        
        data = response.json()
        assert "communications" in data, "Response should have communications array"
        assert "count" in data, "Response should have count"
        print(f"PASS: Listed {data.get('count')} control plane communications")


class TestOPPCOverview(TestOPPCAuthentication):
    """Tests for operations control overview endpoint"""
    
    def test_overview_endpoint(self, auth_headers):
        """GET /api/admin/operations-control/overview should return operations"""
        response = requests.get(
            f"{BASE_URL}/api/admin/operations-control/overview",
            headers=auth_headers,
            timeout=60  # Overview can be slow
        )
        assert response.status_code == 200, f"Overview failed: {response.text}"
        
        data = response.json()
        assert "operations" in data, "Response should have operations array"
        assert "count" in data, "Response should have count"
        assert data.get("count", 0) > 0, "Should have at least one operation"
        print(f"PASS: Overview returned {data.get('count')} operations")


class TestNotificationAcknowledgement(TestOPPCAuthentication):
    """Tests for notification acknowledgement bridging to communication"""
    
    def test_notification_acknowledge_endpoint_exists(self, auth_headers):
        """POST /api/notifications/{id}/acknowledge should exist"""
        # Use a fake notification ID - we just want to verify the endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/notifications/fake-notif-id/acknowledge",
            headers=auth_headers,
            timeout=30
        )
        # Should return 404 (not found) not 405 (method not allowed) or 500
        assert response.status_code in [200, 404], f"Acknowledge endpoint returned unexpected status: {response.status_code}"
        print(f"PASS: Notification acknowledge endpoint exists (returned {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
