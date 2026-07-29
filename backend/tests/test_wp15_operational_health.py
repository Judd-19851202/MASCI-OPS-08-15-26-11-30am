"""
WP-15 Operational Health Dashboard Backend Tests
Tests the Enterprise Governance module on the shared Operational Health Dashboard framework.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    BASE_URL = "https://backup-forensics.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_session():
    """Authenticate as admin and return session with cookies."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login
    response = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    
    data = response.json()
    # Set admin token header from portal_tokens
    portal_tokens = data.get("portal_tokens", {})
    admin_token = portal_tokens.get("admin")
    if admin_token:
        session.headers.update({"X-Admin-Token": admin_token})
    
    # Also set directory token if available
    session_token = data.get("session_token")
    if session_token:
        session.headers.update({"X-Directory-Token": session_token})
    
    return session


class TestHealthEndpoint:
    """Basic health check tests."""
    
    def test_health_endpoint_returns_ok(self):
        """Health endpoint should return ok status."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True


class TestOperationalHealthModules:
    """Tests for /api/admin/operational-health/modules endpoint."""
    
    def test_modules_list_requires_auth(self):
        """Modules list should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/operational-health/modules")
        assert response.status_code in [401, 403]
    
    def test_modules_list_returns_framework(self, admin_session):
        """Modules list should return the framework catalog."""
        response = admin_session.get(f"{BASE_URL}/api/admin/operational-health/modules")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("framework_id") == "operational-health-dashboard"
        assert data.get("framework_label") == "Operational Health Dashboard"
        assert "modules" in data
        
        # Verify enterprise-governance is in the catalog
        modules = data.get("modules", [])
        eg_module = next((m for m in modules if m.get("id") == "enterprise-governance"), None)
        assert eg_module is not None
        assert eg_module.get("availability") == "live"
        assert eg_module.get("route") == "/admin/governance"


class TestEnterpriseGovernanceModule:
    """Tests for /api/admin/operational-health/modules/enterprise-governance endpoint."""
    
    def test_module_requires_auth(self):
        """Enterprise governance module should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/operational-health/modules/enterprise-governance")
        assert response.status_code in [401, 403]
    
    def test_module_returns_full_payload(self, admin_session):
        """Enterprise governance module should return complete payload."""
        response = admin_session.get(f"{BASE_URL}/api/admin/operational-health/modules/enterprise-governance")
        assert response.status_code == 200
        
        data = response.json()
        
        # Framework metadata
        assert data.get("framework_id") == "operational-health-dashboard"
        assert data.get("framework_label") == "Operational Health Dashboard"
        assert data.get("framework_version") == "1.0"
        assert "generated_at" in data
        
        # Module metadata
        module = data.get("module", {})
        assert module.get("id") == "enterprise-governance"
        assert module.get("label") == "Enterprise Governance"
        assert module.get("route") == "/admin/governance"
        assert "authority_statement" in module
        assert "future_modules" in module
        assert "quick_links" in module
        
        # Overall status and counts
        assert data.get("overall_status") in ["green", "yellow", "red", "unknown"]
        counts = data.get("counts", {})
        assert "green" in counts
        assert "yellow" in counts
        assert "red" in counts
        assert "unknown" in counts
        
        # Truth surface
        assert "truth_surface" in data
        assert "truth_relationship" in data
        
        # Sections
        sections = data.get("sections", [])
        assert len(sections) == 8, f"Expected 8 sections, got {len(sections)}"
        
        section_ids = [s.get("id") for s in sections]
        expected_sections = [
            "constitutional-status",
            "governance-drift",
            "certification-health",
            "trust-spine-integrity",
            "identity-health",
            "authorization-health",
            "operator-experience",
            "constitutional-exemptions",
        ]
        for expected in expected_sections:
            assert expected in section_ids, f"Missing section: {expected}"
    
    def test_module_cards_have_drilldown_metadata(self, admin_session):
        """Every KPI card should have required drill-down metadata."""
        response = admin_session.get(f"{BASE_URL}/api/admin/operational-health/modules/enterprise-governance")
        assert response.status_code == 200
        
        data = response.json()
        sections = data.get("sections", [])
        
        required_fields = [
            "id", "title", "status", "summary", "root_cause_explanation",
            "endpoint", "evidence_source_label", "producer",
            "checked_at", "last_successful_refresh", "affected_assets",
            "recommended_action", "evidence"
        ]
        
        for section in sections:
            for card in section.get("cards", []):
                for field in required_fields:
                    assert field in card, f"Card {card.get('id')} missing field: {field}"
                
                # Status must be valid
                assert card.get("status") in ["green", "yellow", "red", "unknown"], \
                    f"Card {card.get('id')} has invalid status: {card.get('status')}"
                
                # Affected assets must have structure
                affected = card.get("affected_assets", {})
                assert "files" in affected or "modules" in affected or "workflows" in affected
    
    def test_module_does_not_invent_green(self, admin_session):
        """Dashboard must not invent GREEN statuses without evidence."""
        response = admin_session.get(f"{BASE_URL}/api/admin/operational-health/modules/enterprise-governance")
        assert response.status_code == 200
        
        data = response.json()
        sections = data.get("sections", [])
        
        for section in sections:
            for card in section.get("cards", []):
                if card.get("status") == "green":
                    # Green cards must have evidence
                    evidence = card.get("evidence", {})
                    assert evidence, f"Green card {card.get('id')} has no evidence"
                    
                    # Green cards should have checked_at or last_successful_refresh
                    has_timestamp = card.get("checked_at") or card.get("last_successful_refresh")
                    assert has_timestamp, f"Green card {card.get('id')} has no timestamp evidence"
    
    def test_module_404_for_unknown_module(self, admin_session):
        """Unknown module ID should return 404."""
        response = admin_session.get(f"{BASE_URL}/api/admin/operational-health/modules/unknown-module")
        assert response.status_code == 404


class TestGovernanceVersionsEndpoint:
    """Tests for /api/admin/governance/versions endpoint."""
    
    def test_versions_requires_auth(self):
        """Versions endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/governance/versions")
        assert response.status_code in [401, 403]
    
    def test_versions_returns_wp15_frozen_status(self, admin_session):
        """Versions should report wp15-architecture-frozen status."""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/versions")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "wp15-architecture-frozen"
        assert "architecture_freeze_reference" in data
        assert "constitutional_standard_reference" in data
        assert data.get("operational_health_dashboard_route") == "/admin/governance"


class TestGovernanceRegistryEndpoint:
    """Tests for /api/admin/governance/registry endpoint."""
    
    def test_registry_requires_auth(self):
        """Registry endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/governance/registry")
        assert response.status_code in [401, 403]
    
    def test_registry_returns_constitutional_principles(self, admin_session):
        """Registry should include constitutional principles."""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/registry")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data
        assert "constitutional_principles" in data
        principles = data.get("constitutional_principles", [])
        assert "enterprise_governance_principle" in principles


class TestTrustSpineEndpoint:
    """Tests for /api/admin/trust-spine endpoint."""
    
    def test_trust_spine_requires_auth(self):
        """Trust spine endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/trust-spine")
        assert response.status_code in [401, 403]
    
    def test_trust_spine_returns_platform_band(self, admin_session):
        """Trust spine should return platform band status."""
        response = admin_session.get(f"{BASE_URL}/api/admin/trust-spine")
        assert response.status_code == 200
        
        data = response.json()
        assert "platform_band" in data
        assert data.get("platform_band") in ["green", "yellow", "red", "unknown", None]
        assert "workflows" in data


class TestProductionCertificationEndpoint:
    """Tests for /api/admin/production-certification endpoint."""
    
    def test_certification_requires_auth(self):
        """Production certification endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/production-certification")
        assert response.status_code in [401, 403]
    
    def test_certification_returns_platform_band(self, admin_session):
        """Production certification should return platform band."""
        response = admin_session.get(f"{BASE_URL}/api/admin/production-certification")
        assert response.status_code == 200
        
        data = response.json()
        assert "platform_band" in data
        assert "workflows" in data


class TestOccTrustEventsEndpoint:
    """Tests for /api/admin/occ/trust-events endpoint."""
    
    def test_trust_events_requires_auth(self):
        """Trust events endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/occ/trust-events")
        assert response.status_code in [401, 403]
    
    def test_trust_events_returns_blockers(self, admin_session):
        """Trust events should return unresolved blockers."""
        response = admin_session.get(f"{BASE_URL}/api/admin/occ/trust-events?limit=25")
        assert response.status_code == 200
        
        data = response.json()
        assert "counts" in data
        assert "unresolved_blockers" in data


class TestSessionsEndpoint:
    """Tests for /api/admin/sessions/recent endpoint."""
    
    def test_sessions_requires_auth(self):
        """Sessions endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/sessions/recent")
        assert response.status_code in [401, 403]
    
    def test_sessions_returns_timeout_config(self, admin_session):
        """Sessions should return timeout configuration."""
        response = admin_session.get(f"{BASE_URL}/api/admin/sessions/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert "timeouts_enabled" in data
        assert "tiers" in data


class TestGovernanceIdentitiesEndpoint:
    """Tests for /api/admin/governance/identities endpoint."""
    
    def test_identities_requires_auth(self):
        """Identities endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/governance/identities")
        assert response.status_code in [401, 403]
    
    def test_identities_returns_projections(self, admin_session):
        """Identities should return identity projections."""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/identities")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "items" in data


class TestGovernanceDecisionsEndpoint:
    """Tests for /api/admin/governance/decisions endpoint."""
    
    def test_decisions_requires_auth(self):
        """Decisions endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/governance/decisions")
        assert response.status_code in [401, 403]
    
    def test_decisions_returns_items(self, admin_session):
        """Decisions should return decision items."""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/decisions")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "items" in data


class TestGovernanceOverridesEndpoint:
    """Tests for /api/admin/governance/emergency-overrides endpoint."""
    
    def test_overrides_requires_auth(self):
        """Overrides endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/governance/emergency-overrides")
        assert response.status_code in [401, 403]
    
    def test_overrides_returns_items(self, admin_session):
        """Overrides should return override items."""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/emergency-overrides")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "items" in data


class TestGovernanceApprovalFlowsEndpoint:
    """Tests for /api/admin/governance/approval-flows endpoint."""
    
    def test_approval_flows_requires_auth(self):
        """Approval flows endpoint should require admin authentication."""
        response = requests.get(f"{BASE_URL}/api/admin/governance/approval-flows")
        assert response.status_code in [401, 403]
    
    def test_approval_flows_returns_items(self, admin_session):
        """Approval flows should return items and requests."""
        response = admin_session.get(f"{BASE_URL}/api/admin/governance/approval-flows")
        assert response.status_code == 200
        
        data = response.json()
        assert "count" in data
        assert "items" in data
        assert "requests" in data


class TestDrillDownContractCompleteness:
    """Tests that the drill-down contract is complete for all KPIs."""
    
    def test_drilldown_contract_card_is_green(self, admin_session):
        """The drilldown-contract card should be green if all cards have metadata."""
        response = admin_session.get(f"{BASE_URL}/api/admin/operational-health/modules/enterprise-governance")
        assert response.status_code == 200
        
        data = response.json()
        sections = data.get("sections", [])
        
        # Find the drilldown-contract card in operator-experience section
        drilldown_card = None
        for section in sections:
            if section.get("id") == "operator-experience":
                for card in section.get("cards", []):
                    if card.get("id") == "drilldown-contract":
                        drilldown_card = card
                        break
        
        assert drilldown_card is not None, "drilldown-contract card not found"
        
        # Check the evidence for missing fields
        evidence = drilldown_card.get("evidence", {})
        missing_by_card = evidence.get("missing_by_card", [])
        
        # If there are missing fields, the status should not be green
        if missing_by_card:
            assert drilldown_card.get("status") != "green", \
                f"drilldown-contract is green but has missing fields: {missing_by_card}"
        else:
            assert drilldown_card.get("status") == "green", \
                "drilldown-contract should be green when all cards have required metadata"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
