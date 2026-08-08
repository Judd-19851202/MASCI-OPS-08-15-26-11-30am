from __future__ import annotations

from typing import Any, Dict, List, Optional


LIVE_OPERATIONAL_CLASSIFICATION = "live_operational"
PREVIEW_CERTIFICATION_CLASSIFICATION = "preview_certification"
SYNTHETIC_TEST_CLASSIFICATION = "synthetic_test"
LEGACY_HIDDEN_BACKFILL_CLASSIFICATION = "legacy_hidden_backfill"

LIVE_OPERATIONS_SCOPE = "live_operations"
TECHNICAL_AUDIT_ONLY_SCOPE = "technical_audit_only"

GOVERNED_HIDDEN_SOURCE_KIND_TO_CLASSIFICATION = {
    "preview_certification": PREVIEW_CERTIFICATION_CLASSIFICATION,
    "synthetic_test": SYNTHETIC_TEST_CLASSIFICATION,
}

HIDDEN_CLASSIFICATIONS = {
    PREVIEW_CERTIFICATION_CLASSIFICATION,
    SYNTHETIC_TEST_CLASSIFICATION,
    LEGACY_HIDDEN_BACKFILL_CLASSIFICATION,
}

_EXPLICIT_MARKERS = ["synthetic_record", "hidden_from_operations", "certification_record"]


def hidden_corrective_action_classification_for_source_kind(source_kind: Optional[str]) -> Optional[str]:
    kind = (source_kind or "").strip().lower()
    return GOVERNED_HIDDEN_SOURCE_KIND_TO_CLASSIFICATION.get(kind)


def synthetic_corrective_action_exclusion_clauses() -> List[Dict[str, Any]]:
    return [
        {"technical_record_classification": {"$nin": sorted(HIDDEN_CLASSIFICATIONS)}},
        {"truth_visibility_scope": {"$ne": TECHNICAL_AUDIT_ONLY_SCOPE}},
        {"synthetic_record": {"$ne": True}},
        {"hidden_from_operations": {"$ne": True}},
        {"certification_record": {"$ne": True}},
    ]


def apply_synthetic_corrective_action_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    q = dict(query or {})
    extra = synthetic_corrective_action_exclusion_clauses()
    existing = q.get("$and")
    if isinstance(existing, list):
        q["$and"] = existing + extra
    else:
        q["$and"] = extra
    return q


def is_hidden_corrective_action(doc: Dict[str, Any]) -> bool:
    if not doc:
        return False
    classification = str(doc.get("technical_record_classification") or "").strip().lower()
    if classification in HIDDEN_CLASSIFICATIONS:
        return True
    if doc.get("truth_visibility_scope") == TECHNICAL_AUDIT_ONLY_SCOPE:
        return True
    for marker in _EXPLICIT_MARKERS:
        if doc.get(marker) is True:
            return True
    return False


def is_synthetic_corrective_action(doc: Dict[str, Any]) -> bool:
    return is_hidden_corrective_action(doc)


def synthetic_corrective_action_markers(doc: Dict[str, Any], *, preserve_existing: bool = False) -> Dict[str, Any]:
    existing_classification = str(doc.get("technical_record_classification") or "").strip().lower()
    classification = hidden_corrective_action_classification_for_source_kind(doc.get("source_kind"))
    if not classification and preserve_existing and existing_classification:
        classification = existing_classification

    if classification in HIDDEN_CLASSIFICATIONS:
        reason = {
            PREVIEW_CERTIFICATION_CLASSIFICATION: "preview_certification_record",
            SYNTHETIC_TEST_CLASSIFICATION: "synthetic_test_record",
            LEGACY_HIDDEN_BACKFILL_CLASSIFICATION: "legacy_hidden_backfill",
        }.get(classification, "technical_hidden_record")
        return {
            "technical_record_classification": classification,
            "truth_visibility_scope": TECHNICAL_AUDIT_ONLY_SCOPE,
            "governed_classification_reason": reason,
            "governed_classification_source": f"source_kind:{(doc.get('source_kind') or '').strip().lower() or 'preserved'}",
            "synthetic_record": True,
            "hidden_from_operations": True,
            "certification_record": classification == PREVIEW_CERTIFICATION_CLASSIFICATION or bool(doc.get("certification_record")),
        }

    return {
        "technical_record_classification": LIVE_OPERATIONAL_CLASSIFICATION,
        "truth_visibility_scope": LIVE_OPERATIONS_SCOPE,
        "governed_classification_reason": "live_operational_default",
        "governed_classification_source": "source_kind:operational",
        "synthetic_record": False,
        "hidden_from_operations": False,
        "certification_record": False,
    }


__all__ = [
    "GOVERNED_HIDDEN_SOURCE_KIND_TO_CLASSIFICATION",
    "HIDDEN_CLASSIFICATIONS",
    "LEGACY_HIDDEN_BACKFILL_CLASSIFICATION",
    "LIVE_OPERATIONAL_CLASSIFICATION",
    "LIVE_OPERATIONS_SCOPE",
    "PREVIEW_CERTIFICATION_CLASSIFICATION",
    "SYNTHETIC_TEST_CLASSIFICATION",
    "TECHNICAL_AUDIT_ONLY_SCOPE",
    "apply_synthetic_corrective_action_exclusion",
    "hidden_corrective_action_classification_for_source_kind",
    "is_hidden_corrective_action",
    "is_synthetic_corrective_action",
    "synthetic_corrective_action_exclusion_clauses",
    "synthetic_corrective_action_markers",
]