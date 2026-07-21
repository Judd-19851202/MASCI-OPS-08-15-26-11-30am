"""
C2 Checkpoint Tests - Canonical Truth Architecture, KPI Provenance, Status Integrity

Tests verify:
1. Platform status returns canonical_truth with owners
2. Trust spine returns canonical_status + truth_surface
3. Integration truth returns truth_surface owner metadata
4. OCC health endpoint returns structured data
5. Auth continuity for admin-protected routes
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login"""
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert data.get("ok") is True, "Login response not ok"
    token = data.get("portal_tokens", {}).get("admin")
    assert token, "No admin token in response"
    return token


class TestC2CanonicalTruthArchitecture:
    """C2 canonical runtime attestation tests"""
    
    def test_platform_status_returns_canonical_truth(self, admin_token):
        """C2: Platform status includes canonical_truth with owners"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/status",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200, f"Platform status failed: {response.text}"
        
        data = response.json()
        
        # Verify canonical_truth is present
        assert "canonical_truth" in data, "canonical_truth missing from platform status"
        canonical_truth = data["canonical_truth"]
        
        # Verify checkpoint is C2
        assert canonical_truth.get("checkpoint") == "C2", "Checkpoint should be C2"
        
        # Verify status is VERIFIED
        assert canonical_truth.get("status") == "VERIFIED", "Status should be VERIFIED"
        
        # Verify owners are present
        assert "owners" in canonical_truth, "owners missing from canonical_truth"
        owners = canonical_truth["owners"]
        
        # Verify expected owner surfaces
        expected_surfaces = [
            "platform_attestation",
            "trust_spine",
            "integration_truth",
            "shared_auth_session",
            "shared_admin_shell"
        ]
        for surface in expected_surfaces:
            assert surface in owners, f"Owner surface '{surface}' missing"
            owner = owners[surface]
            assert "surface_id" in owner, f"surface_id missing for {surface}"
            assert "owner_endpoint" in owner, f"owner_endpoint missing for {surface}"
            assert "owner_module" in owner, f"owner_module missing for {surface}"
            assert "contract" in owner, f"contract missing for {surface}"
    
    def test_platform_status_no_ambiguous_ownership(self, admin_token):
        """C2: Each surface has exactly one authoritative owner"""
        response = requests.get(
            f"{BASE_URL}/api/admin/platform/status",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        
        data = response.json()
        owners = data.get("canonical_truth", {}).get("owners", {})
        
        for surface_id, owner in owners.items():
            # Each owner should have owner_type = "authoritative"
            assert owner.get("owner_type") == "authoritative", \
                f"Surface {surface_id} should have authoritative owner_type"


class TestC2TrustSpineContract:
    """C2 trust spine contract tests"""
    
    def test_trust_spine_returns_canonical_status(self, admin_token):
        """C2: Trust spine returns canonical_status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/trust-spine",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200, f"Trust spine failed: {response.text}"
        
        data = response.json()
        
        # Verify canonical_status is present
        assert "canonical_status" in data, "canonical_status missing from trust spine"
        
        # Verify canonical_status is a valid value
        valid_statuses = ["VERIFIED", "MISMATCH", "DEGRADED", "UNVERIFIABLE", "NOT_APPLICABLE"]
        assert data["canonical_status"] in valid_statuses, \
            f"Invalid canonical_status: {data['canonical_status']}"
    
    def test_trust_spine_returns_truth_surface(self, admin_token):
        """C2: Trust spine returns truth_surface owner metadata"""
        response = requests.get(
            f"{BASE_URL}/api/admin/trust-spine",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify truth_surface is present
        assert "truth_surface" in data, "truth_surface missing from trust spine"
        truth_surface = data["truth_surface"]
        
        # Verify truth_surface has required fields
        assert truth_surface.get("surface_id") == "trust_spine", \
            "truth_surface should have surface_id = trust_spine"
        assert truth_surface.get("owner_endpoint") == "/api/admin/trust-spine", \
            "truth_surface should have correct owner_endpoint"
        assert "owner_module" in truth_surface, "owner_module missing"
        assert "contract" in truth_surface, "contract missing"
    
    def test_trust_spine_workflow_drilldown(self, admin_token):
        """C2: Trust spine workflow drilldown works"""
        # First get the list of workflows
        response = requests.get(
            f"{BASE_URL}/api/admin/trust-spine",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        
        data = response.json()
        workflows = data.get("workflows", [])
        
        if workflows:
            # Test drilldown for first workflow
            workflow_name = workflows[0].get("workflow")
            drilldown_response = requests.get(
                f"{BASE_URL}/api/admin/trust-spine/workflow/{workflow_name}?limit=10",
                headers={"X-Admin-Token": admin_token}
            )
            assert drilldown_response.status_code == 200, \
                f"Workflow drilldown failed: {drilldown_response.text}"
            
            drilldown_data = drilldown_response.json()
            assert "workflow" in drilldown_data
            assert "events" in drilldown_data


class TestC2IntegrationTruthContract:
    """C2 integration truth contract tests"""
    
    def test_integration_truth_returns_truth_surface(self, admin_token):
        """C2: Integration truth returns truth_surface owner metadata"""
        response = requests.get(
            f"{BASE_URL}/api/admin/integrations/truth-status",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200, f"Integration truth failed: {response.text}"
        
        data = response.json()
        
        # Verify truth_surface is present
        assert "truth_surface" in data, "truth_surface missing from integration truth"
        truth_surface = data["truth_surface"]
        
        # Verify truth_surface has required fields
        assert truth_surface.get("surface_id") == "integration_truth", \
            "truth_surface should have surface_id = integration_truth"
        assert truth_surface.get("owner_endpoint") == "/api/admin/integrations/truth-status", \
            "truth_surface should have correct owner_endpoint"
        assert "owner_module" in truth_surface, "owner_module missing"
        assert "contract" in truth_surface, "contract missing"
    
    def test_integration_truth_returns_overall_status(self, admin_token):
        """C2: Integration truth returns overall canonical status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/integrations/truth-status",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify overall status is present
        assert "overall" in data, "overall status missing"
        
        # Verify it's a valid canonical status
        valid_statuses = ["VERIFIED", "MISMATCH", "DEGRADED", "UNVERIFIABLE", "NOT_APPLICABLE"]
        assert data["overall"] in valid_statuses, \
            f"Invalid overall status: {data['overall']}"
    
    def test_integration_truth_returns_integrations_list(self, admin_token):
        """C2: Integration truth returns list of integrations with three-state model"""
        response = requests.get(
            f"{BASE_URL}/api/admin/integrations/truth-status",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify integrations list is present
        assert "integrations" in data, "integrations list missing"
        integrations = data["integrations"]
        assert len(integrations) > 0, "integrations list is empty"
        
        # Verify each integration has three-state model
        for integration in integrations:
            assert "id" in integration, "integration missing id"
            assert "name" in integration, "integration missing name"
            assert "config_status" in integration, "integration missing config_status"
            assert "connectivity_status" in integration, "integration missing connectivity_status"
            assert "operational_status" in integration, "integration missing operational_status"
            assert "overall" in integration, "integration missing overall"


class TestC2OCCHealth:
    """C2 Operations Control Center health tests"""
    
    def test_occ_health_returns_data(self, admin_token):
        """C2: OCC health endpoint returns structured data"""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200, f"OCC health failed: {response.text}"
        
        data = response.json()
        
        # Verify required fields
        assert "overall_status" in data, "overall_status missing"
        assert "counts" in data, "counts missing"
        assert "sections" in data, "sections missing"
    
    def test_occ_health_sections_have_cards(self, admin_token):
        """C2: OCC health sections contain cards with evidence"""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        
        data = response.json()
        sections = data.get("sections", [])
        
        assert len(sections) > 0, "No sections in OCC health"
        
        for section in sections:
            assert "id" in section, "section missing id"
            assert "label" in section, "section missing label"
            assert "cards" in section, "section missing cards"


class TestC2AuthContinuity:
    """C2 auth continuity for admin-protected routes"""
    
    def test_admin_routes_require_auth(self):
        """C2: Admin routes return 401/403 without token"""
        protected_routes = [
            "/api/admin/platform/status",
            "/api/admin/trust-spine",
            "/api/admin/integrations/truth-status",
            "/api/admin/occ/health"
        ]
        
        for route in protected_routes:
            response = requests.get(f"{BASE_URL}{route}")
            assert response.status_code in [401, 403], \
                f"Route {route} should require auth, got {response.status_code}"
    
    def test_admin_routes_accessible_with_token(self, admin_token):
        """C2: Admin routes accessible with valid admin token"""
        protected_routes = [
            "/api/admin/platform/status",
            "/api/admin/trust-spine",
            "/api/admin/integrations/truth-status",
            "/api/admin/occ/health"
        ]
        
        for route in protected_routes:
            response = requests.get(
                f"{BASE_URL}{route}",
                headers={"X-Admin-Token": admin_token}
            )
            assert response.status_code == 200, \
                f"Route {route} should be accessible with admin token, got {response.status_code}"
    
    def test_ai_keys_status_accessible(self, admin_token):
        """C2: AI keys status endpoint accessible"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ai/keys/status",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200, f"AI keys status failed: {response.text}"
        
        data = response.json()
        assert "providers" in data, "providers missing from AI keys status"
    
    def test_dr_v2_alias_telemetry_accessible(self, admin_token):
        """C2: DR-V2 alias telemetry endpoint accessible"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dr-v2-alias-telemetry",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200, f"DR-V2 alias telemetry failed: {response.text}"
        
        data = response.json()
        assert "truth_surface" in data, "truth_surface missing from alias telemetry"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
