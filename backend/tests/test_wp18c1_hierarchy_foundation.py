"""
WP-18C1 Enterprise Hierarchy Foundation - Backend API Tests
Tests the new hierarchy endpoints under /api/admin/governance/hierarchy/*
"""
import os
import uuid
from pathlib import Path
import pytest
import requests


BASE_URL = os.environ.get("LOCAL_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


class TestWP18C1HierarchyFoundation:
    """Tests for WP-18C1 Enterprise Hierarchy Foundation APIs"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin + directory authentication tokens via multi-login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={
                "X-Device-Id": f"wp18c1-{uuid.uuid4().hex[:8]}",
                "X-Test-Rate-Limit-Bypass": "1",
            },
            timeout=60,
        )
        if response.status_code == 200:
            data = response.json()
            portal_tokens = data.get("portal_tokens", {})
            admin_token = portal_tokens.get("admin")
            directory_token = data.get("session_token")
            if admin_token and directory_token:
                return {"admin": admin_token, "directory": directory_token}
        pytest.skip(f"Authentication failed on local backend: {response.status_code} - {response.text}")

    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with both required auth tokens"""
        return {
            "X-Admin-Token": auth_token["admin"],
            "X-Directory-Token": auth_token["directory"],
            "Content-Type": "application/json",
        }

    # ==================== HIERARCHY OVERVIEW ====================
    def test_hierarchy_overview_returns_valid_structure(self, auth_headers):
        """Test hierarchy overview API returns valid MASCI hierarchy foundation"""
        response = requests.get(f"{BASE_URL}/api/admin/governance/hierarchy/overview", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify summary exists
        assert "summary" in data, "Missing summary in overview"
        summary = data["summary"]
        assert "total_nodes" in summary, "Missing total_nodes in summary"
        assert "active_nodes" in summary, "Missing active_nodes in summary"
        assert "bindings_total" in summary, "Missing bindings_total in summary"
        assert "review_queue_total" in summary, "Missing review_queue_total in summary"
        assert "resource_assignments_total" in summary, "Missing resource_assignments_total in summary"
        
        # Verify current_masci_hierarchy exists
        assert "current_masci_hierarchy" in data, "Missing current_masci_hierarchy"
        hierarchy = data["current_masci_hierarchy"]
        assert "company" in hierarchy, "Missing company in hierarchy"
        assert "division" in hierarchy, "Missing division in hierarchy"
        assert "departments" in hierarchy, "Missing departments in hierarchy"
        assert "projects" in hierarchy, "Missing projects in hierarchy"
        assert "facilities" in hierarchy, "Missing facilities in hierarchy"
        
        # Verify company node
        company = hierarchy["company"]
        assert company is not None, "Company node is None"
        assert company.get("type") == "company", f"Company type mismatch: {company.get('type')}"
        
        print(f"✓ Overview: {summary['total_nodes']} nodes, {summary['bindings_total']} bindings, {summary['review_queue_total']} review items")

    # ==================== HIERARCHY NODES LIST ====================
    def test_hierarchy_nodes_list(self, auth_headers):
        """Test hierarchy nodes list API"""
        response = requests.get(f"{BASE_URL}/api/admin/governance/hierarchy/nodes", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data, "Missing count in response"
        assert "items" in data, "Missing items in response"
        assert isinstance(data["items"], list), "Items should be a list"
        
        # Verify node structure
        if data["items"]:
            node = data["items"][0]
            assert "id" in node, "Missing id in node"
            assert "name" in node, "Missing name in node"
            assert "type" in node, "Missing type in node"
            assert "code" in node, "Missing code in node"
        
        print(f"✓ Nodes list: {data['count']} nodes returned")

    def test_hierarchy_nodes_filter_by_type(self, auth_headers):
        """Test hierarchy nodes filtering by type"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            params={"node_type": "project"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # All returned nodes should be projects
        for node in data["items"]:
            assert node.get("type") == "project", f"Expected project type, got {node.get('type')}"
        
        print(f"✓ Project filter: {data['count']} projects returned")

    def test_hierarchy_nodes_search(self, auth_headers):
        """Test hierarchy nodes search functionality"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            params={"search": "MASCI"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"✓ Search 'MASCI': {data['count']} nodes matched")

    # ==================== NODE DETAIL ====================
    def test_hierarchy_node_detail(self, auth_headers):
        """Test fetching a specific node detail"""
        # First get the company node ID
        response = requests.get(f"{BASE_URL}/api/admin/governance/hierarchy/overview", headers=auth_headers)
        assert response.status_code == 200
        
        company = response.json().get("current_masci_hierarchy", {}).get("company")
        if not company:
            pytest.skip("No company node found")
        
        node_id = company["id"]
        
        # Fetch detail
        detail_response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes/{node_id}",
            headers=auth_headers
        )
        assert detail_response.status_code == 200, f"Expected 200, got {detail_response.status_code}: {detail_response.text}"
        
        data = detail_response.json()
        assert "node" in data, "Missing node in detail response"
        assert "children" in data, "Missing children in detail response"
        assert "ancestry" in data, "Missing ancestry in detail response"
        assert "bindings" in data, "Missing bindings in detail response"
        assert "resource_assignments" in data, "Missing resource_assignments in detail response"
        
        print(f"✓ Node detail: {data['node']['name']} with {len(data['children'])} children")

    def test_hierarchy_node_detail_not_found(self, auth_headers):
        """Test 404 for unknown node"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes/nonexistent-node-id",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Unknown node returns 404")

    def test_hierarchy_node_children(self, auth_headers):
        """Test fetching node children"""
        # Get company node
        response = requests.get(f"{BASE_URL}/api/admin/governance/hierarchy/overview", headers=auth_headers)
        company = response.json().get("current_masci_hierarchy", {}).get("company")
        if not company:
            pytest.skip("No company node found")
        
        children_response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes/{company['id']}/children",
            headers=auth_headers
        )
        assert children_response.status_code == 200, f"Expected 200, got {children_response.status_code}"
        
        data = children_response.json()
        assert "count" in data, "Missing count"
        assert "items" in data, "Missing items"
        print(f"✓ Company children: {data['count']} direct children")

    def test_hierarchy_node_ancestry(self, auth_headers):
        """Test fetching node ancestry"""
        # Get a project node
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            params={"node_type": "project"},
            headers=auth_headers
        )
        projects = response.json().get("items", [])
        if not projects:
            pytest.skip("No project nodes found")
        
        project = projects[0]
        ancestry_response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes/{project['id']}/ancestry",
            headers=auth_headers
        )
        assert ancestry_response.status_code == 200, f"Expected 200, got {ancestry_response.status_code}"
        
        data = ancestry_response.json()
        assert "count" in data, "Missing count"
        assert "items" in data, "Missing items"
        print(f"✓ Project ancestry: {data['count']} ancestors for {project['name']}")

    # ==================== REVIEW QUEUE ====================
    def test_hierarchy_review_queue(self, auth_headers):
        """Test review queue API for unresolved mappings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/review-queue",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data, "Missing count"
        assert "items" in data, "Missing items"
        
        # Verify review item structure if any exist
        if data["items"]:
            item = data["items"][0]
            assert "review_id" in item, "Missing review_id"
            assert "source_label" in item, "Missing source_label"
            assert "reason" in item, "Missing reason"
        
        print(f"✓ Review queue: {data['count']} unresolved items")

    # ==================== RESOURCE ASSIGNMENTS ====================
    def test_hierarchy_resource_assignments(self, auth_headers):
        """Test resource assignments API"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/resource-assignments",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data, "Missing count"
        assert "items" in data, "Missing items"
        
        # Verify assignment structure if any exist
        if data["items"]:
            item = data["items"][0]
            assert "assignment_id" in item, "Missing assignment_id"
            assert "resource_type" in item, "Missing resource_type"
            assert "assigned_node_id" in item, "Missing assigned_node_id"
        
        print(f"✓ Resource assignments: {data['count']} assignments")

    # ==================== SCOPE PREVIEW ====================
    def test_hierarchy_scope_preview(self, auth_headers):
        """Test scope preview API"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/scope",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data, "Missing count"
        assert "items" in data, "Missing items"
        
        # Verify scope preview structure if any exist
        if data["items"]:
            item = data["items"][0]
            assert "identity" in item, "Missing identity"
            assert "scope_preview" in item, "Missing scope_preview"
        
        print(f"✓ Scope preview: {data['count']} identity scopes")

    def test_hierarchy_scope_preview_with_email_filter(self, auth_headers):
        """Test scope preview with email filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/scope",
            params={"email": ADMIN_EMAIL},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ Scope preview with email filter works")

    # ==================== BINDINGS ====================
    def test_hierarchy_bindings(self, auth_headers):
        """Test hierarchy bindings API"""
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/bindings",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data, "Missing count"
        assert "items" in data, "Missing items"
        
        print(f"✓ Bindings: {data['count']} total bindings")

    # ==================== CREATE/UPDATE/STATE TRANSITIONS ====================
    def test_create_hierarchy_node(self, auth_headers):
        """Test creating a governed hierarchy item"""
        import uuid
        test_code = f"TEST-DEPT-{uuid.uuid4().hex[:6].upper()}"
        
        payload = {
            "code": test_code,
            "name": f"Test Department {test_code}",
            "type": "department",
            "parent_id": "division:operations",
            "description": "Test department created by WP-18C1 testing",
            "display_order": 999
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("ok") is True, "Expected ok=True"
        assert "node" in data, "Missing node in response"
        
        created_node = data["node"]
        assert created_node["code"] == test_code, "Code mismatch"
        assert created_node["type"] == "department", "Type mismatch"
        
        print(f"✓ Created node: {created_node['id']}")
        self.__class__.created_node = created_node

    def test_update_hierarchy_node(self, auth_headers):
        """Test updating a hierarchy node"""
        # First create a node
        import uuid
        test_code = f"TEST-UPD-{uuid.uuid4().hex[:6].upper()}"
        
        create_payload = {
            "code": test_code,
            "name": f"Original Name {test_code}",
            "type": "department",
            "parent_id": "division:operations",
            "description": "Original description"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=create_payload,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        node_id = create_response.json()["node"]["id"]
        
        # Update the node
        update_payload = {
            "name": f"Updated Name {test_code}",
            "description": "Updated description"
        }
        
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes/{node_id}",
            json=update_payload,
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        data = update_response.json()
        assert data.get("ok") is True, "Expected ok=True"
        assert data["node"]["name"] == f"Updated Name {test_code}", "Name not updated"
        
        print(f"✓ Updated node: {node_id}")

    def test_deactivate_hierarchy_node(self, auth_headers):
        """Test deactivating a hierarchy node"""
        # First create a node
        import uuid
        test_code = f"TEST-DEACT-{uuid.uuid4().hex[:6].upper()}"
        
        create_payload = {
            "code": test_code,
            "name": f"Deactivate Test {test_code}",
            "type": "department",
            "parent_id": "division:operations"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=create_payload,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        node_id = create_response.json()["node"]["id"]
        
        # Deactivate
        deactivate_response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes/{node_id}/deactivate",
            json={"reason": "Testing deactivation"},
            headers=auth_headers
        )
        assert deactivate_response.status_code == 200, f"Expected 200, got {deactivate_response.status_code}: {deactivate_response.text}"
        
        data = deactivate_response.json()
        assert data.get("ok") is True
        assert data["node"]["active_status"] is False, "Node should be inactive"
        
        print(f"✓ Deactivated node: {node_id}")

    def test_archive_hierarchy_node(self, auth_headers):
        """Test archiving a hierarchy node"""
        import uuid
        test_code = f"TEST-ARCH-{uuid.uuid4().hex[:6].upper()}"
        
        create_payload = {
            "code": test_code,
            "name": f"Archive Test {test_code}",
            "type": "department",
            "parent_id": "division:operations"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=create_payload,
            headers=auth_headers
        )
        assert create_response.status_code == 200
        node_id = create_response.json()["node"]["id"]
        
        # Archive
        archive_response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes/{node_id}/archive",
            json={"reason": "Testing archive"},
            headers=auth_headers
        )
        assert archive_response.status_code == 200, f"Expected 200, got {archive_response.status_code}: {archive_response.text}"
        
        data = archive_response.json()
        assert data.get("ok") is True
        assert data["node"]["archive_status"] is True, "Node should be archived"
        
        print(f"✓ Archived node: {node_id}")

    # ==================== BAD INPUT PROTECTION ====================
    def test_invalid_facility_subtype(self, auth_headers):
        """Test that invalid facility subtype returns error"""
        payload = {
            "code": "TEST-BAD-FAC",
            "name": "Bad Facility",
            "type": "facility",
            "subtype": "invalid_subtype",  # Invalid
            "parent_id": "company:masci"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid facility subtype returns 400")

    def test_missing_required_parent(self, auth_headers):
        """Test that missing required parent returns error"""
        payload = {
            "code": "TEST-NO-PARENT",
            "name": "No Parent Division",
            "type": "division",
            # Missing parent_id - division requires company parent
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Missing required parent returns 400")

    def test_duplicate_code(self, auth_headers):
        """Test that duplicate code returns error"""
        import uuid
        test_code = f"TEST-DUP-{uuid.uuid4().hex[:6].upper()}"
        
        payload = {
            "code": test_code,
            "name": f"First {test_code}",
            "type": "department",
            "parent_id": "division:operations"
        }
        
        # Create first
        response1 = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=payload,
            headers=auth_headers
        )
        assert response1.status_code == 200
        
        # Try to create duplicate
        payload["name"] = f"Duplicate {test_code}"
        response2 = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/nodes",
            json=payload,
            headers=auth_headers
        )
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}"
        print("✓ Duplicate code returns 400")

    # ==================== BACKFILL ====================
    def test_backfill_run(self, auth_headers):
        """Test running backfill"""
        response = requests.post(
            f"{BASE_URL}/api/admin/governance/hierarchy/backfill/run",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "run_id" in data or "run_at" in data, "Missing run info in response"
        print(f"✓ Backfill run completed")

    def test_backfill_latest(self):
        """Test getting latest backfill report"""
        # Fresh auth to avoid session timeout after backfill run
        login_response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": f"wp18c1-backfill-{uuid.uuid4().hex[:8]}", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=60,
        )
        if login_response.status_code != 200:
            pytest.skip(f"Fresh auth failed: {login_response.status_code}")
        data = login_response.json()
        fresh_headers = {
            "X-Admin-Token": data.get("portal_tokens", {}).get("admin"),
            "X-Directory-Token": data.get("session_token"),
        }
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/hierarchy/backfill/latest",
            headers=fresh_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Latest backfill report retrieved")

    # ==================== REGRESSION: EXISTING GOVERNANCE ====================
    def test_existing_governance_overview_still_works(self):
        """Regression: Existing governance overview should still work"""
        # Fresh auth to avoid session timeout after long test run
        login_response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": f"wp18c1-regression-{uuid.uuid4().hex[:8]}", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=60,
        )
        if login_response.status_code != 200:
            pytest.skip(f"Fresh auth failed: {login_response.status_code}")
        data = login_response.json()
        fresh_headers = {
            "X-Admin-Token": data.get("portal_tokens", {}).get("admin"),
            "X-Directory-Token": data.get("session_token"),
        }
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/overview",
            headers=fresh_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Existing governance overview still works")

    def test_existing_organization_endpoint_still_works(self):
        """Regression: Existing organization endpoint should still work"""
        # Fresh auth to avoid session timeout after long test run
        login_response = requests.post(
            f"{BASE_URL}/api/auth/multi-login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "portal": "admin"},
            headers={"X-Device-Id": f"wp18c1-org-{uuid.uuid4().hex[:8]}", "X-Test-Rate-Limit-Bypass": "1"},
            timeout=60,
        )
        if login_response.status_code != 200:
            pytest.skip(f"Fresh auth failed: {login_response.status_code}")
        data = login_response.json()
        fresh_headers = {
            "X-Admin-Token": data.get("portal_tokens", {}).get("admin"),
            "X-Directory-Token": data.get("session_token"),
        }
        response = requests.get(
            f"{BASE_URL}/api/admin/governance/organization",
            headers=fresh_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "count" in data, "Missing count"
        assert "items" in data, "Missing items"
        print(f"✓ Existing organization endpoint: {data['count']} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
