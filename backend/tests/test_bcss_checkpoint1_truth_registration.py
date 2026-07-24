from lib.canonical_truth import (
    AGGREGATOR,
    CANONICAL_OWNER,
    DERIVED_CONSUMER,
    canonical_truth_registry,
    validate_truth_registry,
)


BCSS_SURFACES = {
    "bcss_runtime_state_authority": {"truth_subject": "bcss_runtime_state_authority", "role": CANONICAL_OWNER},
    "bcss_backup_slot_execution": {"truth_subject": "bcss_backup_slot_execution", "role": CANONICAL_OWNER},
    "bcss_backup_job_execution": {"truth_subject": "bcss_backup_job_execution", "role": CANONICAL_OWNER},
    "bcss_backup_archive_lineage": {"truth_subject": "bcss_backup_archive_lineage", "role": CANONICAL_OWNER},
    "bcss_restore_execution": {"truth_subject": "bcss_restore_execution", "role": CANONICAL_OWNER},
    "bcss_restore_drill_evidence": {"truth_subject": "bcss_restore_drill_evidence", "role": CANONICAL_OWNER},
    "bcss_recovery_posture": {"truth_subject": "bcss_recovery_posture", "role": AGGREGATOR},
    "bcss_recovery_trust": {"truth_subject": "bcss_recovery_trust", "role": DERIVED_CONSUMER},
    "bcss_recovery_certification": {"truth_subject": "bcss_recovery_certification", "role": CANONICAL_OWNER},
    "bcss_external_dependency_continuity": {"truth_subject": "bcss_external_dependency_continuity", "role": AGGREGATOR},
}


def test_bcss_truth_subjects_are_formally_registered():
    registry = canonical_truth_registry()

    assert len(BCSS_SURFACES) == 10

    for surface_id, expected in BCSS_SURFACES.items():
        assert surface_id in registry, f"Missing BCSS surface registration: {surface_id}"
        surface = registry[surface_id]
        assert surface["truth_subject"] == expected["truth_subject"]
        assert surface["role"] == expected["role"]
        assert surface["owner_endpoint"]
        assert surface["owner_module"]


def test_bcss_registration_has_no_owner_conflicts_or_missing_upstreams():
    findings = validate_truth_registry()["findings"]
    bcss_findings = [
        finding
        for finding in findings
        if str(finding.get("surface_id") or "").startswith("bcss_")
        or str(finding.get("subject") or "").startswith("bcss_")
    ]

    assert bcss_findings == []


def test_bcss_posture_and_trust_roles_are_separated():
    registry = canonical_truth_registry()

    posture = registry["bcss_recovery_posture"]
    trust = registry["bcss_recovery_trust"]

    assert posture["role"] == AGGREGATOR
    assert trust["role"] == DERIVED_CONSUMER
    assert trust["canonical_owner_id"] == "bcss_recovery_posture"
    assert "bcss_recovery_posture" in trust["upstream_owner_ids"]
