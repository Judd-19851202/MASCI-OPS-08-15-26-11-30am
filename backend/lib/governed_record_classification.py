from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional


LIVE_OPERATIONAL_CLASSIFICATION = "live_operational"
SYNTHETIC_TEST_CLASSIFICATION = "synthetic_test"
PREVIEW_CERTIFICATION_CLASSIFICATION = "preview_certification"
TECHNICAL_RECORD_CLASSIFICATION = "technical"
LEGACY_MIGRATION_CLASSIFICATION = "legacy_migration"
REVIEW_REQUIRED_CLASSIFICATION = "review_required"

LIVE_OPERATIONS_SCOPE = "live_operations"
TECHNICAL_AUDIT_ONLY_SCOPE = "technical_audit_only"
REVIEW_REQUIRED_SCOPE = "review_required"

HIDDEN_CLASSIFICATIONS = {
    SYNTHETIC_TEST_CLASSIFICATION,
    PREVIEW_CERTIFICATION_CLASSIFICATION,
    TECHNICAL_RECORD_CLASSIFICATION,
    LEGACY_MIGRATION_CLASSIFICATION,
}


def governed_visibility_exclusion_clauses() -> List[Dict[str, Any]]:
    return [
        {"synthetic_record": {"$ne": True}},
        {"hidden_from_operations": {"$ne": True}},
        {"certification_record": {"$ne": True}},
        {
            "technical_record_classification": {
                "$nin": sorted(HIDDEN_CLASSIFICATIONS),
            }
        },
        {"truth_visibility_scope": {"$ne": TECHNICAL_AUDIT_ONLY_SCOPE}},
    ]


def apply_governed_visibility_exclusion(query: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    q = dict(query or {})
    extra = governed_visibility_exclusion_clauses()
    existing = q.get("$and")
    if isinstance(existing, list):
        q["$and"] = existing + extra
    else:
        q["$and"] = extra
    return q


def is_hidden_from_live_operations(doc: Optional[Dict[str, Any]]) -> bool:
    if not doc:
        return False
    if doc.get("synthetic_record") is True:
        return True
    if doc.get("hidden_from_operations") is True:
        return True
    if doc.get("certification_record") is True:
        return True
    if doc.get("truth_visibility_scope") == TECHNICAL_AUDIT_ONLY_SCOPE:
        return True
    return (doc.get("technical_record_classification") or "") in HIDDEN_CLASSIFICATIONS


def governed_hidden_markers(
    *,
    classification: str,
    evidence_source: str,
    reason: str,
    evidence_fields: Optional[Iterable[str]] = None,
    source_kind: Optional[str] = None,
    certification_record: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "synthetic_record": classification == SYNTHETIC_TEST_CLASSIFICATION,
        "hidden_from_operations": True,
        "certification_record": bool(certification_record),
        "technical_record_classification": classification,
        "truth_visibility_scope": TECHNICAL_AUDIT_ONLY_SCOPE,
        "governed_classification_source": evidence_source,
        "governed_classification_reason": reason,
        "governed_classification_fields": list(evidence_fields or []),
    }
    if source_kind:
        payload["source_kind"] = source_kind
    if extra:
        payload.update(deepcopy(extra))
    return payload


def governed_live_markers(
    *,
    evidence_source: str,
    reason: str,
    evidence_fields: Optional[Iterable[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "synthetic_record": False,
        "hidden_from_operations": False,
        "certification_record": False,
        "technical_record_classification": LIVE_OPERATIONAL_CLASSIFICATION,
        "truth_visibility_scope": LIVE_OPERATIONS_SCOPE,
        "governed_classification_source": evidence_source,
        "governed_classification_reason": reason,
        "governed_classification_fields": list(evidence_fields or []),
    }
    if extra:
        payload.update(deepcopy(extra))
    return payload


def governed_review_markers(
    *,
    evidence_source: str,
    reason: str,
    evidence_fields: Optional[Iterable[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "synthetic_record": False,
        "hidden_from_operations": False,
        "certification_record": False,
        "technical_record_classification": REVIEW_REQUIRED_CLASSIFICATION,
        "truth_visibility_scope": REVIEW_REQUIRED_SCOPE,
        "governed_classification_source": evidence_source,
        "governed_classification_reason": reason,
        "governed_classification_fields": list(evidence_fields or []),
    }
    if extra:
        payload.update(deepcopy(extra))
    return payload


__all__ = [
    "LIVE_OPERATIONAL_CLASSIFICATION",
    "SYNTHETIC_TEST_CLASSIFICATION",
    "PREVIEW_CERTIFICATION_CLASSIFICATION",
    "TECHNICAL_RECORD_CLASSIFICATION",
    "LEGACY_MIGRATION_CLASSIFICATION",
    "REVIEW_REQUIRED_CLASSIFICATION",
    "LIVE_OPERATIONS_SCOPE",
    "TECHNICAL_AUDIT_ONLY_SCOPE",
    "REVIEW_REQUIRED_SCOPE",
    "HIDDEN_CLASSIFICATIONS",
    "governed_visibility_exclusion_clauses",
    "apply_governed_visibility_exclusion",
    "is_hidden_from_live_operations",
    "governed_hidden_markers",
    "governed_live_markers",
    "governed_review_markers",
]