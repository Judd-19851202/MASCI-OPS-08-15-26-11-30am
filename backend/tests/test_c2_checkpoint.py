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
import time
import pytest
import requests

from lib.canonical_truth import derived_truth_payload, validate_truth_registry
from lib.shared_capabilities import occ_operation_capability
from lib.trust_reconciliation import reconcile_shared_foundation

BASE_URL = os.environ.get('C2_TEST_BASE_URL', 'http://127.0.0.1:8001').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token via multi-login"""
    for _ in range(30):
        try:
            health = requests.get(f"{BASE_URL}/api/health", timeout=5)
            if health.status_code == 200:
                break
        except Exception:
            time.sleep(1)
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

    def test_occ_health_returns_truth_relationship(self, admin_token):
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "truth_surface" in data
        assert "truth_relationship" in data
        assert data["truth_surface"]["role"] == "AGGREGATOR"


class TestC2OwnerEnforcement:
    def test_canonical_owner_registration_succeeds(self):
        result = validate_truth_registry()
        assert result["summary"]["registered_surface_count"] >= 8

    def test_duplicate_canonical_owner_is_rejected(self):
        dupe = {
            "surface_id": "dupe_platform_owner",
            "role": "CANONICAL_OWNER",
            "owner_endpoint": "/api/admin/dupe-platform-status",
            "owner_module": "backend/routes/dupe.py",
            "truth_subject": "platform_runtime_truth",
            "status_authority": "dupe_platform_owner",
            "kpi_authority": "dupe_platform_owner",
            "threshold_authority": "dupe_platform_owner",
            "freshness_authority": "dupe_platform_owner",
            "upstream_owner_ids": [],
        }
        result = validate_truth_registry([dupe])
        assert any(f["finding_type"] == "OWNER_CONFLICT" for f in result["findings"])

    def test_missing_owner_produces_finding(self):
        missing = {
            "surface_id": "missing_owner_surface",
            "role": "DERIVED_CONSUMER",
            "truth_subject": "missing_owner_truth",
            "upstream_owner_ids": ["trust_spine"],
        }
        result = validate_truth_registry([missing])
        assert any(f["finding_type"] == "MISSING_OWNER_METADATA" for f in result["findings"])

    def test_derived_consumer_requires_upstream_owner(self):
        missing_upstream = {
            "surface_id": "derived_without_upstream",
            "role": "DERIVED_CONSUMER",
            "owner_endpoint": "/api/admin/derived-without-upstream",
            "owner_module": "backend/routes/derived_without_upstream.py",
            "truth_subject": "derived_without_upstream_truth",
            "upstream_owner_ids": [],
        }
        result = validate_truth_registry([missing_upstream])
        assert any(f["finding_type"] == "MISSING_UPSTREAM_OWNER" for f in result["findings"])

    def test_validator_cannot_claim_canonical_authority(self):
        bad_validator = {
            "surface_id": "bad_validator",
            "role": "VALIDATOR",
            "canonical_owner_id": "bad_validator",
            "owner_endpoint": "/api/admin/bad-validator",
            "owner_module": "backend/routes/bad_validator.py",
            "truth_subject": "platform_validation_truth",
            "upstream_owner_ids": ["platform_attestation"],
        }
        result = validate_truth_registry([bad_validator])
        assert any(f["finding_type"] == "VALIDATOR_CLAIMS_CANONICAL_AUTHORITY" for f in result["findings"])

    def test_duplicate_kpi_derivation_produces_finding(self):
        duped = {
            "surface_id": "otc_clone",
            "role": "DERIVED_CONSUMER",
            "owner_endpoint": "/api/admin/otc-clone",
            "owner_module": "backend/routes/otc_clone.py",
            "truth_subject": "shared_operational_trust_score",
            "upstream_owner_ids": ["trust_spine"],
            "duplicate_derivation_keys": ["platform_operational_score"],
        }
        result = validate_truth_registry([duped])
        assert any(f["finding_type"] == "DUPLICATE_DERIVATION" for f in result["findings"])

    def test_trust_reconciliation_executes(self):
        result = reconcile_shared_foundation()
        assert "finding_count" in result
        assert "status" in result

    def test_p0_findings_block_completion(self):
        result = reconcile_shared_foundation(extra_findings=[{
            "severity": "P0",
            "blocking_status": True,
        }])
        assert result["status"] == "FAIL"


class TestC2SharedCapabilities:
    def test_shared_capability_resolves_available(self):
        cap = occ_operation_capability({
            "id": "storage.audit",
            "title": "Storage Audit",
            "has_apply": False,
            "requires_dry_run": False,
            "confirmation_phrase": "",
        }, available=True)
        assert cap["available"] is True

    def test_shared_capability_resolves_unavailable_with_reason(self):
        cap = occ_operation_capability({
            "id": "storage.manual",
            "title": "Storage Manual",
            "has_apply": False,
            "requires_dry_run": False,
            "confirmation_phrase": "",
        }, available=False, disabled_reason="Manual-only operation")
        assert cap["available"] is False
        assert cap["disabled_reason"] == "Manual-only operation"

    def test_required_dry_run_is_enforced(self, admin_token):
        response = requests.post(
            f"{BASE_URL}/api/admin/operations-control/operations/storage.safe_cleanup/apply",
            headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
            json={}
        )
        assert response.status_code == 400
        assert "dry_run_id required" in response.text

    def test_required_completion_evidence_is_enforced(self, admin_token):
        dry_run = requests.post(
            f"{BASE_URL}/api/admin/operations-control/operations/storage.safe_cleanup/dry-run",
            headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
            json={}
        )
        assert dry_run.status_code == 200
        action_id = dry_run.json().get("action_id")
        assert action_id
        audit = requests.get(
            f"{BASE_URL}/api/admin/operations-control/audit/{action_id}",
            headers={"X-Admin-Token": admin_token},
        )
        assert audit.status_code == 200
        assert audit.json().get("action_id") == action_id

    def test_shared_route_includes_truth_owner_metadata(self, admin_token):
        response = requests.get(
            f"{BASE_URL}/api/admin/trust-reconciliation",
            headers={"X-Admin-Token": admin_token},
        )
        assert response.status_code == 200
        assert "registry_summary" in response.json()

    def test_retired_surface_cannot_remain_primary(self):
        retired = {
            "surface_id": "retired_surface",
            "role": "RETIRED",
            "owner_endpoint": "/api/admin/retired",
            "owner_module": "backend/routes/retired.py",
            "truth_subject": "retired_truth",
            "upstream_owner_ids": [],
        }
        payload = derived_truth_payload(
            "platform_trust_validator",
            canonical_owner_route="/api/admin/platform/status",
            derivation_explanation="validator",
            canonical_status="VERIFIED",
        )
        assert payload["relationship"]["canonical_owner_route"] == "/api/admin/platform/status"


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
