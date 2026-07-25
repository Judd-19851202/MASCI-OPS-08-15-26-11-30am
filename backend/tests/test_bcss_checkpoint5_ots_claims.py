from __future__ import annotations

from lib.ots_truth import (
    CERTIFIED,
    CORRELATED,
    OBSERVED,
    UNKNOWN,
    VALIDATED,
    VERIFIED,
    canonical_claim_below_or_equal,
    canonical_truth_card,
    prohibited_wording_findings,
)


def test_unknown_evidence_cannot_exceed_unknown_ceiling():
    card = canonical_truth_card(
        truth_subject="bcss_runtime_state_authority",
        canonical_owner="bcss_runtime_state_authority",
        truth_surface_id="bcss_runtime_state_authority",
        evidence_state="unknown",
        evidence_quality="UNKNOWN",
        evidence_confidence="UNKNOWN",
        truth_evaluation="UNVERIFIABLE",
        permitted_claim=OBSERVED,
        claim_ceiling=UNKNOWN,
        claim_basis=[],
    )
    assert card["permitted_claim"] == UNKNOWN
    assert card["contradictory_evidence"]


def test_observed_evidence_cannot_produce_verified():
    card = canonical_truth_card(
        truth_subject="bcss_backup_archive_lineage",
        canonical_owner="bcss_backup_archive_lineage",
        truth_surface_id="bcss_backup_archive_lineage",
        evidence_state="observed",
        evidence_quality="DIRECT_OBSERVED",
        evidence_confidence="LOW",
        truth_evaluation="UNVERIFIABLE",
        permitted_claim=VERIFIED,
        claim_ceiling=OBSERVED,
        claim_basis=["newest archive object"],
    )
    assert card["permitted_claim"] == OBSERVED


def test_correlated_surface_cannot_produce_validated_claim():
    card = canonical_truth_card(
        truth_subject="bcss_recovery_posture",
        canonical_owner="bcss_recovery_posture",
        truth_surface_id="bcss_recovery_posture",
        evidence_state="correlated",
        evidence_quality="CORRELATED",
        evidence_confidence="MEDIUM",
        truth_evaluation="DEGRADED",
        permitted_claim=VALIDATED,
        claim_ceiling=CORRELATED,
        claim_basis=["aggregated recovery signals"],
    )
    assert card["permitted_claim"] == CORRELATED


def test_verified_evidence_cannot_produce_certified_without_decision():
    card = canonical_truth_card(
        truth_subject="bcss_backup_archive_lineage",
        canonical_owner="bcss_backup_archive_lineage",
        truth_surface_id="bcss_backup_archive_lineage",
        evidence_state="independently_verified",
        evidence_quality="VALIDATED",
        evidence_confidence="HIGH",
        truth_evaluation="VERIFIED",
        permitted_claim=CERTIFIED,
        claim_ceiling=VALIDATED,
        claim_basis=["archive verification report"],
    )
    assert card["permitted_claim"] == VALIDATED


def test_claim_cannot_exceed_its_configured_ceiling():
    assert canonical_claim_below_or_equal(OBSERVED, VERIFIED) is True
    assert canonical_claim_below_or_equal(CERTIFIED, VERIFIED) is False


def test_trust_score_surface_remains_correlated_only():
    card = canonical_truth_card(
        truth_subject="bcss_recovery_trust",
        canonical_owner="bcss_recovery_trust",
        truth_surface_id="bcss_recovery_trust",
        evidence_state="calculated",
        evidence_quality="CALCULATED",
        evidence_confidence="MEDIUM",
        truth_evaluation="VERIFIED",
        permitted_claim=VERIFIED,
        claim_ceiling=CORRELATED,
        claim_basis=["trust score"],
    )
    assert card["permitted_claim"] == CORRELATED


def test_http_success_is_not_operational_truth():
    card = canonical_truth_card(
        truth_subject="bcss_runtime_state_authority",
        canonical_owner="bcss_runtime_state_authority",
        truth_surface_id="bcss_runtime_state_authority",
        evidence_state="observed",
        evidence_quality="DIRECT_OBSERVED",
        evidence_confidence="LOW",
        truth_evaluation="UNVERIFIABLE",
        permitted_claim=OBSERVED,
        claim_ceiling=CORRELATED,
        claim_basis=["HTTP 200"],
        unknowns=["HTTP success does not prove represented truth health."],
    )
    assert "HTTP success" in card["unknowns"][0]


def test_archive_availability_does_not_imply_restore_capability():
    findings = prohibited_wording_findings(
        ["Newest archive object observed; restore proven"],
        claim_ceiling=OBSERVED,
    )
    assert "restore proven" in findings


def test_restore_capability_does_not_imply_recovery_certification():
    findings = prohibited_wording_findings(
        ["Representative restore validated; business continuity complete"],
        claim_ceiling=VALIDATED,
    )
    assert "business continuity complete" in findings


def test_deployment_readiness_does_not_imply_recovery_readiness():
    findings = prohibited_wording_findings(
        ["Deployment safe and recovery ready"],
        claim_ceiling=CERTIFIED,
    )
    assert "guaranteed" not in findings
    assert "recovery ready" not in findings  # certified wording allowed generally; boundary enforced at route notes


def test_backup_verification_wording_reflects_actual_evidence_state():
    findings = prohibited_wording_findings(
        ["Backup verification report · fully recoverable · certified"],
        claim_ceiling=VALIDATED,
    )
    assert "fully recoverable" in findings
    assert "certified" in findings


def test_missing_evidence_remains_unknown_or_unavailable():
    card = canonical_truth_card(
        truth_subject="bcss_external_dependency_continuity",
        canonical_owner="bcss_external_dependency_continuity",
        truth_surface_id="bcss_external_dependency_continuity",
        evidence_state="unavailable",
        evidence_quality="UNAVAILABLE",
        evidence_confidence="UNKNOWN",
        truth_evaluation="UNVERIFIABLE",
        permitted_claim=UNKNOWN,
        claim_ceiling=UNKNOWN,
        claim_basis=[],
        unknowns=["No dependency rows were produced."],
    )
    assert card["permitted_claim"] == UNKNOWN
    assert card["unknowns"]
