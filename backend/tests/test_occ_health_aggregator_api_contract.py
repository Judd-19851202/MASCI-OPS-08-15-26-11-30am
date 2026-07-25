"""MASCI OPS BCSS Release 2 Program 2 Wave 3 Family 1 - OCC Health Aggregator API Contract Tests.

Tests the bounded repair for the OCC Health Aggregator:
1. OCC family remains role=AGGREGATOR (not converted to canonical owner)
2. truth_subject=shared_operational_posture
3. canonical_owner_id=platform_attestation
4. canonical_owner_route=/api/admin/platform/status (not /api/admin/occ/health)
5. No duplicate owner/truth engine introduced
6. Honest unknown/unverifiable handling
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from test_credentials.md
TEST_EMAIL = "jaymn.judd@mascigc.com"
TEST_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for authenticated requests."""
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("portal_tokens", {}).get("admin") or data.get("token")
    if not token:
        pytest.skip("No admin token in login response")
    
    return token


class TestOCCHealthAggregatorContract:
    """Tests for OCC Health Aggregator API contract after bounded repair."""
    
    def test_occ_health_endpoint_requires_auth(self):
        """OCC health endpoint should require admin authentication."""
        if not BASE_URL:
            pytest.skip("REACT_APP_BACKEND_URL not set")
        
        response = requests.get(f"{BASE_URL}/api/admin/occ/health", timeout=30)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_occ_health_returns_aggregator_role(self, admin_token):
        """OCC health should return role=AGGREGATOR, not CANONICAL_OWNER."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Check truth_surface
        truth_surface = data.get("truth_surface", {})
        assert truth_surface.get("role") == "AGGREGATOR", \
            f"Expected role=AGGREGATOR, got {truth_surface.get('role')}"
        
        # Check truth_relationship
        truth_relationship = data.get("truth_relationship", {})
        assert truth_relationship.get("role") == "AGGREGATOR", \
            f"Expected relationship role=AGGREGATOR, got {truth_relationship.get('role')}"
    
    def test_occ_health_truth_subject_is_shared_operational_posture(self, admin_token):
        """OCC health should have truth_subject=shared_operational_posture."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        truth_surface = data.get("truth_surface", {})
        assert truth_surface.get("truth_subject") == "shared_operational_posture", \
            f"Expected truth_subject=shared_operational_posture, got {truth_surface.get('truth_subject')}"
    
    def test_occ_health_canonical_owner_is_platform_attestation(self, admin_token):
        """OCC health should have canonical_owner_id=platform_attestation."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check truth_surface
        truth_surface = data.get("truth_surface", {})
        assert truth_surface.get("canonical_owner_id") == "platform_attestation", \
            f"Expected canonical_owner_id=platform_attestation, got {truth_surface.get('canonical_owner_id')}"
        
        # Check truth_relationship
        truth_relationship = data.get("truth_relationship", {})
        assert truth_relationship.get("canonical_owner_id") == "platform_attestation", \
            f"Expected relationship canonical_owner_id=platform_attestation, got {truth_relationship.get('canonical_owner_id')}"
    
    def test_occ_health_canonical_owner_route_is_platform_status(self, admin_token):
        """OCC health canonical_owner_route should be /api/admin/platform/status, NOT /api/admin/occ/health."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        truth_relationship = data.get("truth_relationship", {})
        canonical_owner_route = truth_relationship.get("canonical_owner_route")
        
        # The bounded repair: canonical_owner_route should point to the upstream canonical owner
        # NOT to the OCC aggregator's own endpoint
        assert canonical_owner_route == "/api/admin/platform/status", \
            f"Expected canonical_owner_route=/api/admin/platform/status, got {canonical_owner_route}"
        
        # Verify it's NOT pointing to itself
        assert canonical_owner_route != "/api/admin/occ/health", \
            "canonical_owner_route should NOT point to OCC's own endpoint"
    
    def test_occ_health_has_required_sections(self, admin_token):
        """OCC health should have all 8 required sections."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        sections = data.get("sections", [])
        section_ids = {s.get("id") for s in sections}
        
        required_sections = {
            "platform_runtime",
            "storage_recovery",
            "queues_workers",
            "communications",
            "ai_operations",
            "daily_reports",
            "identity_security",
            "integrations",
        }
        
        missing = required_sections - section_ids
        assert not missing, f"Missing required sections: {missing}"
    
    def test_occ_health_has_canonical_counts(self, admin_token):
        """OCC health should have canonical_counts for honest status mapping."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        canonical_counts = data.get("canonical_counts", {})
        
        # Should have all canonical status counts
        assert "verified" in canonical_counts, "Missing verified count"
        assert "degraded" in canonical_counts, "Missing degraded count"
        assert "mismatch" in canonical_counts, "Missing mismatch count"
        assert "unverifiable" in canonical_counts, "Missing unverifiable count"
        assert "not_applicable" in canonical_counts, "Missing not_applicable count"
    
    def test_occ_health_honest_unknown_handling(self, admin_token):
        """OCC health should honestly report unverifiable/unknown cards, not fake healthy."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check that overall_status reflects actual state
        overall_status = data.get("overall_status")
        overall_canonical = data.get("overall_canonical")
        
        # Both should be present
        assert overall_status is not None, "Missing overall_status"
        assert overall_canonical is not None, "Missing overall_canonical"
        
        # Check canonical_counts
        canonical_counts = data.get("canonical_counts", {})
        unverifiable = canonical_counts.get("unverifiable", 0)
        
        # If there are unverifiable cards, overall should NOT be VERIFIED
        if unverifiable > 0:
            assert overall_canonical != "VERIFIED", \
                f"Overall should not be VERIFIED when {unverifiable} cards are unverifiable"
    
    def test_occ_health_no_duplicate_truth_engine(self, admin_token):
        """OCC health should NOT claim to be a canonical owner or introduce duplicate truth."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        truth_relationship = data.get("truth_relationship", {})
        
        # is_canonical should be False for an aggregator
        is_canonical = truth_relationship.get("is_canonical")
        assert is_canonical is False, \
            f"Aggregator should have is_canonical=False, got {is_canonical}"
        
        # Role should be AGGREGATOR, not CANONICAL_OWNER
        role = truth_relationship.get("role")
        assert role == "AGGREGATOR", f"Expected role=AGGREGATOR, got {role}"
        assert role != "CANONICAL_OWNER", "OCC should NOT be a CANONICAL_OWNER"
    
    def test_occ_health_derivation_explanation_present(self, admin_token):
        """OCC health should have a derivation explanation for transparency."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        truth_relationship = data.get("truth_relationship", {})
        
        derivation_explanation = truth_relationship.get("derivation_explanation")
        assert derivation_explanation, "Missing derivation_explanation"
        assert "aggregator" in derivation_explanation.lower() or "derived" in derivation_explanation.lower(), \
            f"Derivation explanation should mention aggregator/derived nature: {derivation_explanation}"


class TestOCCHealthAggregatorNoRegressions:
    """Tests to verify no regressions after bounded repair."""
    
    def test_occ_health_returns_generated_at(self, admin_token):
        """OCC health should return generated_at timestamp."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "generated_at" in data, "Missing generated_at"
        assert data["generated_at"], "generated_at should not be empty"
    
    def test_occ_health_returns_total_cards(self, admin_token):
        """OCC health should return total_cards count."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_cards" in data, "Missing total_cards"
        assert data["total_cards"] > 0, "total_cards should be > 0"
    
    def test_occ_health_cards_have_required_fields(self, admin_token):
        """Each card should have required fields for UI rendering."""
        response = requests.get(
            f"{BASE_URL}/api/admin/occ/health",
            headers={"X-Admin-Token": admin_token},
            timeout=60
        )
        assert response.status_code == 200
        
        data = response.json()
        sections = data.get("sections", [])
        
        required_card_fields = {"id", "title", "status", "summary", "endpoint", "drilldown"}
        
        for section in sections:
            for card in section.get("cards", []):
                missing = required_card_fields - set(card.keys())
                assert not missing, f"Card {card.get('id')} missing fields: {missing}"
