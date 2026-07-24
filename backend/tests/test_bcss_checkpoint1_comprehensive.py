"""
BCSS Checkpoint 1 Comprehensive Verification Tests
===================================================
Verifies BCSS-R01 and BCSS-R03 requirements from the BCSS Master Implementation Program.

Tests:
1. All 10 BCSS truth subjects are registered in canonical truth registry
2. No BCSS-scoped owner conflicts or missing upstream references
3. Recovery posture and recovery trust roles are formally separated
4. Registry extension does not break existing canonical truth surfaces
5. BCSS surfaces have correct owner metadata (endpoint, module)
"""

import pytest
from lib.canonical_truth import (
    AGGREGATOR,
    CANONICAL_OWNER,
    DERIVED_CONSUMER,
    VALIDATOR,
    canonical_truth_registry,
    validate_truth_registry,
    owner_role_counts,
    canonical_truth_contract,
)


# Constitution Section 18 defines exactly 10 BCSS truth subjects
BCSS_TRUTH_SUBJECTS = {
    "bcss_runtime_state_authority": {
        "truth_subject": "bcss_runtime_state_authority",
        "role": CANONICAL_OWNER,
        "layer": "AUTHORITY",
    },
    "bcss_backup_slot_execution": {
        "truth_subject": "bcss_backup_slot_execution",
        "role": CANONICAL_OWNER,
        "layer": "EXECUTION",
    },
    "bcss_backup_job_execution": {
        "truth_subject": "bcss_backup_job_execution",
        "role": CANONICAL_OWNER,
        "layer": "EXECUTION",
    },
    "bcss_backup_archive_lineage": {
        "truth_subject": "bcss_backup_archive_lineage",
        "role": CANONICAL_OWNER,
        "layer": "EVIDENCE",
    },
    "bcss_restore_execution": {
        "truth_subject": "bcss_restore_execution",
        "role": CANONICAL_OWNER,
        "layer": "EXECUTION",
    },
    "bcss_restore_drill_evidence": {
        "truth_subject": "bcss_restore_drill_evidence",
        "role": CANONICAL_OWNER,
        "layer": "EVIDENCE",
    },
    "bcss_recovery_posture": {
        "truth_subject": "bcss_recovery_posture",
        "role": AGGREGATOR,
        "layer": "INTELLIGENCE",
    },
    "bcss_recovery_trust": {
        "truth_subject": "bcss_recovery_trust",
        "role": DERIVED_CONSUMER,
        "layer": "TRUST",
    },
    "bcss_recovery_certification": {
        "truth_subject": "bcss_recovery_certification",
        "role": CANONICAL_OWNER,
        "layer": "CERTIFICATION",
    },
    "bcss_external_dependency_continuity": {
        "truth_subject": "bcss_external_dependency_continuity",
        "role": AGGREGATOR,
        "layer": "INTELLIGENCE",
    },
}


class TestBCSSCheckpoint1Registration:
    """BCSS-R01: Verify all 10 BCSS truth subjects are registered"""

    def test_exactly_10_bcss_surfaces_registered(self):
        """Verify exactly 10 BCSS surfaces exist in registry"""
        registry = canonical_truth_registry()
        bcss_surfaces = {k: v for k, v in registry.items() if k.startswith("bcss_")}
        assert len(bcss_surfaces) == 10, f"Expected 10 BCSS surfaces, found {len(bcss_surfaces)}"

    def test_all_bcss_truth_subjects_present(self):
        """Verify all 10 constitutional BCSS truth subjects are registered"""
        registry = canonical_truth_registry()
        for surface_id in BCSS_TRUTH_SUBJECTS:
            assert surface_id in registry, f"Missing BCSS surface: {surface_id}"

    def test_bcss_truth_subjects_match_constitution(self):
        """Verify each BCSS surface has correct truth_subject binding"""
        registry = canonical_truth_registry()
        for surface_id, expected in BCSS_TRUTH_SUBJECTS.items():
            surface = registry[surface_id]
            assert surface["truth_subject"] == expected["truth_subject"], (
                f"{surface_id}: truth_subject mismatch"
            )

    def test_bcss_roles_match_constitution(self):
        """Verify each BCSS surface has correct role per constitution"""
        registry = canonical_truth_registry()
        for surface_id, expected in BCSS_TRUTH_SUBJECTS.items():
            surface = registry[surface_id]
            assert surface["role"] == expected["role"], (
                f"{surface_id}: role mismatch (expected {expected['role']}, got {surface['role']})"
            )

    def test_bcss_surfaces_have_owner_endpoint(self):
        """Verify all BCSS surfaces have owner_endpoint metadata"""
        registry = canonical_truth_registry()
        for surface_id in BCSS_TRUTH_SUBJECTS:
            surface = registry[surface_id]
            assert surface.get("owner_endpoint"), f"{surface_id}: missing owner_endpoint"

    def test_bcss_surfaces_have_owner_module(self):
        """Verify all BCSS surfaces have owner_module metadata"""
        registry = canonical_truth_registry()
        for surface_id in BCSS_TRUTH_SUBJECTS:
            surface = registry[surface_id]
            assert surface.get("owner_module"), f"{surface_id}: missing owner_module"


class TestBCSSCheckpoint1Validation:
    """BCSS-R01: Verify no owner conflicts or missing upstream references"""

    def test_no_bcss_scoped_findings(self):
        """Verify validation produces zero BCSS-scoped findings"""
        validation = validate_truth_registry()
        bcss_findings = [
            f for f in validation["findings"]
            if str(f.get("surface_id", "")).startswith("bcss_")
            or str(f.get("subject", "")).startswith("bcss_")
        ]
        assert bcss_findings == [], f"BCSS findings found: {bcss_findings}"

    def test_no_owner_conflicts_in_bcss(self):
        """Verify no OWNER_CONFLICT findings for BCSS surfaces"""
        validation = validate_truth_registry()
        owner_conflicts = [
            f for f in validation["findings"]
            if f["finding_type"] == "OWNER_CONFLICT"
            and (
                str(f.get("surface_id", "")).startswith("bcss_")
                or str(f.get("subject", "")).startswith("bcss_")
            )
        ]
        assert owner_conflicts == [], f"BCSS owner conflicts: {owner_conflicts}"

    def test_no_missing_upstream_in_bcss(self):
        """Verify no MISSING_UPSTREAM_OWNER findings for BCSS surfaces"""
        validation = validate_truth_registry()
        missing_upstream = [
            f for f in validation["findings"]
            if f["finding_type"] == "MISSING_UPSTREAM_OWNER"
            and str(f.get("surface_id", "")).startswith("bcss_")
        ]
        assert missing_upstream == [], f"BCSS missing upstream: {missing_upstream}"

    def test_no_missing_owner_metadata_in_bcss(self):
        """Verify no MISSING_OWNER_METADATA findings for BCSS surfaces"""
        validation = validate_truth_registry()
        missing_metadata = [
            f for f in validation["findings"]
            if f["finding_type"] == "MISSING_OWNER_METADATA"
            and str(f.get("surface_id", "")).startswith("bcss_")
        ]
        assert missing_metadata == [], f"BCSS missing metadata: {missing_metadata}"


class TestBCSSCheckpoint1RoleSeparation:
    """BCSS-R03: Verify recovery posture and trust roles are formally separated"""

    def test_recovery_posture_is_aggregator(self):
        """Verify bcss_recovery_posture has AGGREGATOR role"""
        registry = canonical_truth_registry()
        posture = registry["bcss_recovery_posture"]
        assert posture["role"] == AGGREGATOR, (
            f"bcss_recovery_posture should be AGGREGATOR, got {posture['role']}"
        )

    def test_recovery_trust_is_derived_consumer(self):
        """Verify bcss_recovery_trust has DERIVED_CONSUMER role"""
        registry = canonical_truth_registry()
        trust = registry["bcss_recovery_trust"]
        assert trust["role"] == DERIVED_CONSUMER, (
            f"bcss_recovery_trust should be DERIVED_CONSUMER, got {trust['role']}"
        )

    def test_trust_points_upstream_to_posture(self):
        """Verify bcss_recovery_trust has bcss_recovery_posture as canonical_owner_id"""
        registry = canonical_truth_registry()
        trust = registry["bcss_recovery_trust"]
        assert trust["canonical_owner_id"] == "bcss_recovery_posture", (
            f"bcss_recovery_trust canonical_owner_id should be bcss_recovery_posture"
        )

    def test_trust_has_posture_in_upstream_ids(self):
        """Verify bcss_recovery_trust includes bcss_recovery_posture in upstream_owner_ids"""
        registry = canonical_truth_registry()
        trust = registry["bcss_recovery_trust"]
        assert "bcss_recovery_posture" in trust["upstream_owner_ids"], (
            "bcss_recovery_posture should be in bcss_recovery_trust upstream_owner_ids"
        )

    def test_posture_and_trust_are_distinct_surfaces(self):
        """Verify posture and trust are separate surfaces with different truth subjects"""
        registry = canonical_truth_registry()
        posture = registry["bcss_recovery_posture"]
        trust = registry["bcss_recovery_trust"]
        assert posture["truth_subject"] != trust["truth_subject"], (
            "Posture and trust should have distinct truth subjects"
        )


class TestBCSSCheckpoint1NoBreakage:
    """Verify registry extension does not break existing canonical truth"""

    def test_existing_canonical_owners_preserved(self):
        """Verify pre-existing canonical owners still exist"""
        registry = canonical_truth_registry()
        pre_existing = [
            "platform_attestation",
            "trust_spine",
            "integration_truth",
            "shared_auth_session",
            "shared_admin_shell",
        ]
        for surface_id in pre_existing:
            assert surface_id in registry, f"Pre-existing surface missing: {surface_id}"
            assert registry[surface_id]["role"] == CANONICAL_OWNER, (
                f"{surface_id} should still be CANONICAL_OWNER"
            )

    def test_existing_aggregators_preserved(self):
        """Verify pre-existing aggregators still exist"""
        registry = canonical_truth_registry()
        assert "occ_health_aggregator" in registry
        assert registry["occ_health_aggregator"]["role"] == AGGREGATOR

    def test_existing_derived_consumers_preserved(self):
        """Verify pre-existing derived consumers still exist"""
        registry = canonical_truth_registry()
        assert "operations_trust_center" in registry
        assert registry["operations_trust_center"]["role"] == DERIVED_CONSUMER

    def test_existing_validators_preserved(self):
        """Verify pre-existing validators still exist"""
        registry = canonical_truth_registry()
        assert "platform_trust_validator" in registry
        assert registry["platform_trust_validator"]["role"] == VALIDATOR

    def test_contract_status_verified(self):
        """Verify canonical truth contract status is VERIFIED"""
        contract = canonical_truth_contract()
        assert contract["status"] == "VERIFIED"

    def test_role_counts_include_bcss(self):
        """Verify role counts reflect BCSS additions"""
        counts = owner_role_counts()
        # 7 BCSS canonical owners + 5 pre-existing = 12
        assert counts[CANONICAL_OWNER] >= 12, f"Expected at least 12 canonical owners"
        # 2 BCSS aggregators + 1 pre-existing = 3
        assert counts[AGGREGATOR] >= 3, f"Expected at least 3 aggregators"
        # 1 BCSS derived consumer + 1 pre-existing = 2
        assert counts[DERIVED_CONSUMER] >= 2, f"Expected at least 2 derived consumers"
