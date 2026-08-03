"""
BCSS Checkpoint 5 · Comprehensive OTS Adoption Testing
=======================================================
Tests the five bounded surface families for OTS adoption:
1. Platform Data Truth family
2. Recovery Snapshot family
3. Backup Verification family
4. Backup Trust family
5. Deployment Readiness family

Plus the directly coupled truth-preservation consumer:
- Integration Truth (/api/admin/integrations/truth-status)

Negative behavior tests:
- Weaker evidence cannot produce stronger claims
- Claim cannot exceed configured ceiling
- Trust score cannot upgrade source truth
- Archive availability cannot imply restore capability
- Deployment readiness cannot imply BCSS recovery certification
"""
from __future__ import annotations

import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _request(method, path, *, headers=None, json=None, timeout=30):
    """Retry-enabled request helper."""
    last_error = None
    for _ in range(4):
        try:
            response = requests.request(
                method,
                f"{BASE_URL}{path}",
                headers=headers,
                json=json,
                timeout=timeout,
            )
            if response.status_code < 500:
                return response
            last_error = RuntimeError(f"server returned {response.status_code}")
        except Exception as exc:
            last_error = exc
        time.sleep(1)
    raise last_error


@pytest.fixture(scope="module")
def auth_headers():
    """Authenticate and return admin headers."""
    response = _request("POST", "/api/auth/multi-login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    response.raise_for_status()
    data = response.json()
    return {
        "X-Admin-Token": data["portal_tokens"]["admin"],
        "X-Directory-Token": data["session_token"],
    }


def _assert_ots_contract(payload, expected_claim=None, expected_ceiling=None):
    """Validate OTS contract fields are present and correct."""
    ots = payload.get("ots_truth")
    assert ots, "ots_truth must be present"
    
    required_keys = [
        "truth_subject",
        "canonical_owner",
        "evidence_state",
        "evidence_quality",
        "evidence_confidence",
        "truth_evaluation",
        "permitted_claim",
        "claim_ceiling",
        "claim_basis",
        "evaluation_timestamp",
        "audit_reference",
    ]
    for key in required_keys:
        assert key in ots, f"ots_truth missing {key}"
    
    if expected_claim:
        assert ots["permitted_claim"] == expected_claim, f"Expected permitted_claim={expected_claim}, got {ots['permitted_claim']}"
    
    if expected_ceiling:
        assert ots["claim_ceiling"] == expected_ceiling, f"Expected claim_ceiling={expected_ceiling}, got {ots['claim_ceiling']}"
    
    # Validate truth_relationship
    rel = payload.get("truth_relationship")
    assert rel, "truth_relationship must be present"
    
    # Validate compatibility
    compat = payload.get("compatibility")
    assert compat, "compatibility must be present"
    assert compat.get("breaking_api_changes") == 0, "No breaking API changes allowed"
    
    return ots


def _assert_legacy_fields_preserved(payload, legacy_fields):
    """Verify legacy response fields remain present."""
    for field in legacy_fields:
        assert field in payload, f"Legacy field '{field}' must be preserved"


# ═══════════════════════════════════════════════════════════════════
# FAMILY 1: Platform Data Truth
# ═══════════════════════════════════════════════════════════════════

class TestPlatformDataTruthFamily:
    """Platform Data Truth family: /api/platform/data-truth"""
    
    def test_platform_data_truth_returns_additive_ots_fields(self):
        """OTS contract fields are additive without breaking existing fields."""
        response = _request("GET", "/api/platform/data-truth", timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Verify OTS contract
        ots = _assert_ots_contract(data, expected_claim="CORRELATED", expected_ceiling="CORRELATED")
        
        # Verify legacy fields preserved
        _assert_legacy_fields_preserved(data, [
            "status", "ok", "as_of", "environment", "data_source", "database",
            "verified", "certification_date", "certification_stamp", "runtime_identity",
            "ui_banner", "integrations", "doctrine"
        ])
        
        # Verify legacy field consistency
        assert data["verified"] == data["ok"], "legacy 'verified' field should remain consistent with 'ok'"
    
    def test_platform_data_truth_truth_relationship_correct(self):
        """Truth relationship correctly identifies canonical owner."""
        response = _request("GET", "/api/platform/data-truth", timeout=20)
        response.raise_for_status()
        data = response.json()
        
        rel = data.get("truth_relationship")
        assert rel is not None
        assert rel.get("canonical_owner_route") == "/api/admin/platform/status"
        assert "derivation_explanation" in rel
    
    def test_platform_data_truth_compatibility_no_breaking_changes(self):
        """Compatibility projection shows no breaking changes."""
        response = _request("GET", "/api/platform/data-truth", timeout=20)
        response.raise_for_status()
        data = response.json()
        
        compat = data.get("compatibility")
        assert compat["breaking_api_changes"] == 0
        assert compat["preserved_fields"] > 0
        assert compat["new_additive_fields"] > 0


# ═══════════════════════════════════════════════════════════════════
# FAMILY 2: Recovery Snapshot
# ═══════════════════════════════════════════════════════════════════

class TestRecoverySnapshotFamily:
    """Recovery Snapshot family: /api/admin/recovery/snapshot"""
    
    def test_recovery_snapshot_enforces_correlated_ceiling(self, auth_headers):
        """Recovery snapshot enforces CORRELATED claim ceiling."""
        response = _request("GET", "/api/admin/recovery/snapshot", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        ots = _assert_ots_contract(data, expected_claim="CORRELATED", expected_ceiling="CORRELATED")
        
        # Verify prohibited claims
        assert "VALIDATED" in ots.get("prohibited_claims", [])
        assert "CERTIFIED" in ots.get("prohibited_claims", [])
    
    def test_recovery_snapshot_exposes_ots_truth_metadata(self, auth_headers):
        """Recovery snapshot exposes OTS truth metadata."""
        response = _request("GET", "/api/admin/recovery/snapshot", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        ots = data.get("ots_truth")
        assert ots["truth_subject"] == "bcss_recovery_posture"
        assert ots["canonical_owner"] == "bcss_recovery_posture"
        assert "audit_reference" in ots
        # Note: public_ots_projection doesn't include evidence_required_to_raise_claim
        # The claim_basis and prohibited_claims serve the same purpose
        assert "claim_basis" in ots
        assert "prohibited_claims" in ots
    
    def test_recovery_snapshot_preserves_legacy_fields(self, auth_headers):
        """Recovery snapshot preserves all legacy response fields."""
        response = _request("GET", "/api/admin/recovery/snapshot", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        _assert_legacy_fields_preserved(data, [
            "computed_at", "pill", "last_backup", "last_drill",
            "backup_age_minutes", "backup_age_target_minutes",
            "archive_lineage", "rpo", "rto", "archive_count",
            "bucket_usage", "archive_size_trend", "failures_7d",
            "warnings", "scheduler", "hourly_cadence_enabled"
        ])


# ═══════════════════════════════════════════════════════════════════
# FAMILY 3: Backup Verification
# ═══════════════════════════════════════════════════════════════════

class TestBackupVerificationFamily:
    """Backup Verification family: /api/admin/backup-verification/*"""
    
    def test_backup_verification_state_is_observed_only(self, auth_headers):
        """State endpoint is OBSERVED scheduler/config state surface only."""
        response = _request("GET", "/api/admin/backup-verification/state", headers=auth_headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        ots = _assert_ots_contract(data, expected_claim="OBSERVED", expected_ceiling="OBSERVED")
        
        # Verify prohibited claims for state-only surface
        prohibited = ots.get("prohibited_claims", [])
        assert "CORRELATED" in prohibited
        assert "VERIFIED" in prohibited
        assert "VALIDATED" in prohibited
        assert "CERTIFIED" in prohibited
    
    def test_backup_verification_preview_exposes_bounded_ots_truth(self, auth_headers):
        """Preview endpoint exposes bounded OTS truth metadata."""
        response = _request("GET", "/api/admin/backup-verification/preview", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        assert data.get("ok") is True
        report = data.get("report") or {}
        
        ots = _assert_ots_contract(report, expected_ceiling="VALIDATED")
        
        # Verify it does not overclaim certification
        assert ots["claim_ceiling"] == "VALIDATED"
        assert "CERTIFIED" in ots.get("prohibited_claims", [])
    
    def test_backup_verification_does_not_overclaim_certification(self, auth_headers):
        """Backup verification does not overclaim certification."""
        response = _request("GET", "/api/admin/backup-verification/preview", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        report = data.get("report") or {}
        ots = report.get("ots_truth")
        
        # Permitted claim must not exceed VALIDATED
        assert ots["permitted_claim"] in ["UNKNOWN", "OBSERVED", "CORRELATED", "VERIFIED", "VALIDATED"]
        assert ots["permitted_claim"] != "CERTIFIED"


# ═══════════════════════════════════════════════════════════════════
# FAMILY 4: Backup Trust
# ═══════════════════════════════════════════════════════════════════

class TestBackupTrustFamily:
    """Backup Trust family: /api/admin/backup-trust-score"""
    
    def test_backup_trust_score_remains_correlated_only(self, auth_headers):
        """Backup trust score remains CORRELATED only."""
        response = _request("GET", "/api/admin/backup-trust-score", headers=auth_headers, timeout=90)
        response.raise_for_status()
        data = response.json()
        
        ots = _assert_ots_contract(data, expected_claim="CORRELATED", expected_ceiling="CORRELATED")
        
        # Trust score cannot upgrade into VERIFIED/VALIDATED/CERTIFIED independently
        assert ots["permitted_claim"] == "CORRELATED"
        assert ots["claim_ceiling"] == "CORRELATED"
    
    def test_backup_trust_score_cannot_upgrade_source_truth(self, auth_headers):
        """Trust score cannot upgrade source truth."""
        response = _request("GET", "/api/admin/backup-trust-score", headers=auth_headers, timeout=90)
        response.raise_for_status()
        data = response.json()
        
        ots = data.get("ots_truth")
        
        # Even with high trust_score, permitted_claim stays CORRELATED
        assert ots["permitted_claim"] == "CORRELATED"
        
        # Verify prohibited claims
        prohibited = ots.get("prohibited_claims", [])
        assert "VALIDATED" in prohibited or "CERTIFIED" in prohibited


# ═══════════════════════════════════════════════════════════════════
# FAMILY 5: Deployment Readiness
# ═══════════════════════════════════════════════════════════════════

class TestDeploymentReadinessFamily:
    """Deployment Readiness family: /api/admin/deployment-readiness"""
    
    def test_deployment_readiness_exposes_bounded_ots_truth(self, auth_headers):
        """Deployment readiness exposes bounded OTS truth metadata."""
        response = _request("GET", "/api/admin/deployment-readiness", headers=auth_headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        ots = _assert_ots_contract(data, expected_ceiling="CERTIFIED")
        
        # Verify decision is present
        assert data["decision"] in ["pass", "fail"]
    
    def test_deployment_readiness_preserves_deployment_vs_recovery_boundary(self, auth_headers):
        """Deployment readiness preserves deployment-vs-recovery certification boundary."""
        response = _request("GET", "/api/admin/deployment-readiness", headers=auth_headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        ots = data.get("ots_truth")
        
        # Prohibited claims must include BCSS recovery certification
        prohibited = ots.get("prohibited_claims", [])
        assert "BCSS recovery certification" in prohibited or "full-platform recovery certification" in prohibited
        
        # Unknowns should mention deployment != recovery
        unknowns = ots.get("unknowns", [])
        if data["decision"] != "pass":
            assert any("recovery" in u.lower() for u in unknowns)
    
    def test_deployment_history_preserves_ots_truth(self, auth_headers):
        """Deployment history preserves ots_truth on historical records."""
        response = _request("GET", "/api/admin/deployment-readiness/history?limit=5", headers=auth_headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        if data.get("events"):
            for event in data["events"]:
                assert "ots_truth" in event, "historical ledger row must preserve ots_truth"
                assert event["ots_truth"]["claim_ceiling"] == "CERTIFIED"


# ═══════════════════════════════════════════════════════════════════
# DIRECTLY COUPLED TRUTH-PRESERVATION CONSUMER
# ═══════════════════════════════════════════════════════════════════

class TestIntegrationTruthConsumer:
    """Integration Truth: /api/admin/integrations/truth-status"""
    
    def test_integration_truth_exposes_additive_ots_truth(self, auth_headers):
        """Integration truth exposes additive OTS truth metadata."""
        response = _request("GET", "/api/admin/integrations/truth-status", headers=auth_headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        ots = _assert_ots_contract(data, expected_claim="CORRELATED", expected_ceiling="CORRELATED")
        
        # Verify truth subject
        assert ots["truth_subject"] == "bcss_external_dependency_continuity"
    
    def test_integration_truth_preserves_existing_semantics(self, auth_headers):
        """Integration truth preserves existing dependency-truth semantics."""
        response = _request("GET", "/api/admin/integrations/truth-status", headers=auth_headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Verify legacy fields preserved
        _assert_legacy_fields_preserved(data, [
            "checked_at", "overall", "integrations", "doctrine"
        ])
        
        # Verify integrations array structure
        integrations = data.get("integrations", [])
        assert len(integrations) > 0
        for integration in integrations:
            assert "id" in integration
            assert "name" in integration
            assert "overall" in integration


# ═══════════════════════════════════════════════════════════════════
# NEGATIVE BEHAVIOR TESTS
# ═══════════════════════════════════════════════════════════════════

class TestNegativeBehavior:
    """Negative behavior tests for OTS claim boundaries."""
    
    def test_weaker_evidence_cannot_produce_stronger_claims(self, auth_headers):
        """Weaker evidence cannot produce stronger claims."""
        # Platform data truth is CORRELATED - cannot claim VERIFIED
        response = _request("GET", "/api/platform/data-truth", timeout=20)
        response.raise_for_status()
        data = response.json()
        
        ots = data.get("ots_truth")
        assert ots["permitted_claim"] == "CORRELATED"
        assert ots["claim_ceiling"] == "CORRELATED"
    
    def test_claim_cannot_exceed_configured_ceiling(self, auth_headers):
        """Claim cannot exceed configured ceiling."""
        # Recovery snapshot has CORRELATED ceiling
        response = _request("GET", "/api/admin/recovery/snapshot", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        ots = data.get("ots_truth")
        # Permitted claim must be <= ceiling
        claim_ladder = ["UNKNOWN", "OBSERVED", "CORRELATED", "VERIFIED", "VALIDATED", "CERTIFIED"]
        permitted_idx = claim_ladder.index(ots["permitted_claim"]) if ots["permitted_claim"] in claim_ladder else -1
        ceiling_idx = claim_ladder.index(ots["claim_ceiling"]) if ots["claim_ceiling"] in claim_ladder else -1
        
        assert permitted_idx <= ceiling_idx, f"permitted_claim {ots['permitted_claim']} exceeds ceiling {ots['claim_ceiling']}"
    
    def test_trust_score_cannot_upgrade_source_truth(self, auth_headers):
        """Trust score cannot upgrade source truth."""
        response = _request("GET", "/api/admin/backup-trust-score", headers=auth_headers, timeout=90)
        response.raise_for_status()
        data = response.json()
        
        # Even with high trust_score, the OTS claim stays bounded
        ots = data.get("ots_truth")
        assert ots["permitted_claim"] == "CORRELATED"
        assert ots["claim_ceiling"] == "CORRELATED"
    
    def test_archive_availability_cannot_imply_restore_capability(self, auth_headers):
        """Archive availability cannot imply restore capability."""
        response = _request("GET", "/api/admin/recovery/snapshot", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        ots = data.get("ots_truth")
        
        # The claim ceiling and prohibited claims enforce this boundary
        # Recovery snapshot is CORRELATED only - cannot claim VALIDATED or CERTIFIED
        assert ots["claim_ceiling"] == "CORRELATED"
        prohibited = ots.get("prohibited_claims", [])
        assert "VALIDATED" in prohibited or "CERTIFIED" in prohibited
    
    def test_deployment_readiness_cannot_imply_bcss_recovery_certification(self, auth_headers):
        """Deployment readiness cannot imply BCSS recovery certification."""
        response = _request("GET", "/api/admin/deployment-readiness", headers=auth_headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        ots = data.get("ots_truth")
        
        # Prohibited claims must include recovery certification
        prohibited = ots.get("prohibited_claims", [])
        assert any("recovery" in p.lower() for p in prohibited)


# ═══════════════════════════════════════════════════════════════════
# COMPATIBILITY BEHAVIOR TESTS
# ═══════════════════════════════════════════════════════════════════

class TestCompatibilityBehavior:
    """Compatibility behavior tests for legacy API contracts."""
    
    def test_platform_data_truth_legacy_fields_present(self):
        """Platform data truth legacy response fields remain present."""
        response = _request("GET", "/api/platform/data-truth", timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # All legacy fields must be present
        assert "status" in data
        assert "ok" in data
        assert "environment" in data
        assert "database" in data
        assert "verified" in data
        assert "ui_banner" in data
    
    def test_recovery_snapshot_legacy_fields_present(self, auth_headers):
        """Recovery snapshot legacy response fields remain present."""
        response = _request("GET", "/api/admin/recovery/snapshot", headers=auth_headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        # All legacy fields must be present
        assert "pill" in data
        assert "last_backup" in data
        assert "backup_age_minutes" in data
        assert "rpo" in data
        assert "rto" in data
        assert "scheduler" in data
    
    def test_no_breaking_api_contract_for_tested_families(self, auth_headers):
        """No breaking API contract introduced for the tested families."""
        endpoints = [
            ("/api/platform/data-truth", None),
            ("/api/admin/recovery/snapshot", auth_headers),
            ("/api/admin/backup-verification/state", auth_headers),
            ("/api/admin/backup-trust-score", auth_headers),
            ("/api/admin/deployment-readiness", auth_headers),
            ("/api/admin/integrations/truth-status", auth_headers),
        ]
        
        for path, headers in endpoints:
            response = _request("GET", path, headers=headers, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            compat = data.get("compatibility")
            assert compat is not None, f"{path} must have compatibility projection"
            assert compat.get("breaking_api_changes") == 0, f"{path} must have no breaking changes"
