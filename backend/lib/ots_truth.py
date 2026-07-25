from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from lib.canonical_truth import canonical_truth_surface

UNKNOWN = "UNKNOWN"
OBSERVED = "OBSERVED"
CORRELATED = "CORRELATED"
VERIFIED = "VERIFIED"
VALIDATED = "VALIDATED"
CERTIFIED = "CERTIFIED"

CLAIM_LADDER = [UNKNOWN, OBSERVED, CORRELATED, VERIFIED, VALIDATED, CERTIFIED]
_CLAIM_RANK = {name: idx for idx, name in enumerate(CLAIM_LADDER)}

DEFAULT_PROHIBITED_WORDING = {
    UNKNOWN: ["certified", "guaranteed", "fully recoverable", "recovery ready", "disaster recovery complete", "business continuity complete", "restore proven", "production safe", "deployment safe", "fully protected", "compliant", "validated", "verified"],
    OBSERVED: ["certified", "guaranteed", "fully recoverable", "recovery ready", "disaster recovery complete", "business continuity complete", "restore proven", "production safe", "deployment safe", "fully protected", "compliant", "validated", "verified"],
    CORRELATED: ["certified", "guaranteed", "fully recoverable", "recovery ready", "disaster recovery complete", "business continuity complete", "restore proven", "production safe", "deployment safe", "fully protected", "compliant", "validated"],
    VERIFIED: ["certified", "guaranteed", "fully recoverable", "recovery ready", "disaster recovery complete", "business continuity complete"],
    VALIDATED: ["certified", "guaranteed", "fully recoverable", "recovery ready", "disaster recovery complete", "business continuity complete", "restore proven", "production safe", "deployment safe", "fully protected", "compliant"],
    CERTIFIED: ["guaranteed"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def claim_rank(claim: Optional[str]) -> int:
    return _CLAIM_RANK.get(str(claim or "").upper(), -1)


def canonical_claim_below_or_equal(claim: str, ceiling: str) -> bool:
    return claim_rank(claim) <= claim_rank(ceiling)


def canonical_truth_card(
    *,
    truth_subject: str,
    canonical_owner: str,
    truth_surface_id: str,
    evidence_state: str,
    evidence_quality: str,
    evidence_confidence: str,
    truth_evaluation: str,
    permitted_claim: str,
    claim_ceiling: str,
    claim_basis: Iterable[str] | None,
    prohibited_claims: Iterable[str] | None = None,
    degradation_reasons: Iterable[str] | None = None,
    unknowns: Iterable[str] | None = None,
    contradictory_evidence: Iterable[str] | None = None,
    evidence_timestamp: Optional[str] = None,
    evaluation_timestamp: Optional[str] = None,
    source_version: Optional[str] = None,
    audit_reference: Optional[str] = None,
    evidence_required_to_raise_claim: Iterable[str] | None = None,
    notes: Iterable[str] | None = None,
) -> Dict[str, Any]:
    permitted = str(permitted_claim or UNKNOWN).upper()
    ceiling = str(claim_ceiling or UNKNOWN).upper()
    contradictions = list(contradictory_evidence or [])
    if not canonical_claim_below_or_equal(permitted, ceiling):
        contradictions.append("Requested permitted claim exceeded the configured ceiling and was clamped.")
        permitted = ceiling

    return {
        "truth_subject": truth_subject,
        "canonical_owner": canonical_owner,
        "truth_surface": canonical_truth_surface(truth_surface_id),
        "evidence_state": str(evidence_state or "unknown"),
        "evidence_quality": str(evidence_quality or "UNKNOWN"),
        "evidence_confidence": str(evidence_confidence or "UNKNOWN").upper(),
        "truth_evaluation": str(truth_evaluation or UNKNOWN),
        "permitted_claim": permitted,
        "claim_ceiling": ceiling,
        "claim_basis": list(claim_basis or []),
        "prohibited_claims": list(prohibited_claims or []),
        "degradation_reasons": list(degradation_reasons or []),
        "unknowns": list(unknowns or []),
        "contradictory_evidence": contradictions,
        "evidence_timestamp": evidence_timestamp,
        "evaluation_timestamp": evaluation_timestamp or _now_iso(),
        "source_version": source_version or "OTS-C5.1",
        "audit_reference": audit_reference,
        "evidence_required_to_raise_claim": list(evidence_required_to_raise_claim or []),
        "notes": list(notes or []),
    }


def truth_card_projection(card: Mapping[str, Any], *, fields: Iterable[str]) -> Dict[str, Any]:
    return {field: deepcopy(card.get(field)) for field in fields if field in card}


def public_ots_projection(card: Mapping[str, Any]) -> Dict[str, Any]:
    return truth_card_projection(
        card,
        fields=[
            "truth_subject",
            "canonical_owner",
            "truth_surface",
            "evidence_state",
            "evidence_quality",
            "evidence_confidence",
            "truth_evaluation",
            "permitted_claim",
            "claim_ceiling",
            "claim_basis",
            "prohibited_claims",
            "degradation_reasons",
            "unknowns",
            "contradictory_evidence",
            "evidence_timestamp",
            "evaluation_timestamp",
            "source_version",
            "audit_reference",
        ],
    )


def compatibility_projection(*, preserved_fields: int, deprecated_fields: int, new_fields: int, alias_fields: Iterable[str], breaking_changes: int = 0) -> Dict[str, Any]:
    return {
        "preserved_fields": int(preserved_fields),
        "deprecated_fields": int(deprecated_fields),
        "new_additive_fields": int(new_fields),
        "legacy_aliases_retained": list(alias_fields),
        "breaking_api_changes": int(breaking_changes),
    }


def projected_truth_relationship(*, surface_id: str, card: Mapping[str, Any], derivation_explanation: str, canonical_owner_route: Optional[str], derived_status: Optional[str] = None) -> Dict[str, Any]:
    surface = canonical_truth_surface(surface_id)
    return {
        "is_canonical": surface.get("role") in {"CANONICAL_OWNER", "DOMAIN_OWNER"},
        "role": surface.get("role"),
        "canonical_owner_id": surface.get("canonical_owner_id"),
        "canonical_owner_route": canonical_owner_route or surface.get("owner_endpoint"),
        "upstream_owner_ids": surface.get("upstream_owner_ids") or [],
        "canonical_status": card.get("truth_evaluation") or "UNVERIFIABLE",
        "derived_status": derived_status or card.get("truth_evaluation") or "UNVERIFIABLE",
        "derivation_explanation": derivation_explanation,
        "conflicts": list(card.get("contradictory_evidence") or []),
        "has_conflict": bool(card.get("contradictory_evidence")),
        "evidence_age_source": card.get("evidence_timestamp") or card.get("evaluation_timestamp"),
        "stale_evidence": any("stale" in str(reason).lower() for reason in (card.get("degradation_reasons") or [])),
    }


def prohibited_wording_findings(texts: Iterable[str], *, claim_ceiling: str) -> List[str]:
    forbidden = DEFAULT_PROHIBITED_WORDING.get(str(claim_ceiling or UNKNOWN).upper(), [])
    findings: List[str] = []
    for text in texts:
        lowered = str(text or "").lower()
        for phrase in forbidden:
            if phrase in lowered:
                findings.append(phrase)
    return sorted(set(findings))


def assert_no_prohibited_wording(texts: Iterable[str], *, claim_ceiling: str) -> None:
    findings = prohibited_wording_findings(texts, claim_ceiling=claim_ceiling)
    if findings:
        raise ValueError(f"Prohibited wording for claim ceiling {claim_ceiling}: {', '.join(findings)}")


__all__ = [
    "CERTIFIED",
    "CLAIM_LADDER",
    "CORRELATED",
    "OBSERVED",
    "UNKNOWN",
    "VALIDATED",
    "VERIFIED",
    "assert_no_prohibited_wording",
    "canonical_claim_below_or_equal",
    "canonical_truth_card",
    "claim_rank",
    "compatibility_projection",
    "projected_truth_relationship",
    "prohibited_wording_findings",
    "public_ots_projection",
    "truth_card_projection",
]
