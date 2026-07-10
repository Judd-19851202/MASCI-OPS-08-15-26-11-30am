"""TRACK 28.06 · Synthetic Safety exclusion filter.

Same doctrine as 28.02B/28.03/28.04/28.05. Certification / smoke-test
fixtures using ``TEST_28_06_``, ``SYNTHETIC_``, ``ITER[0-9]`` prefixes
on the identity fields of Safety collections must never surface on
operator-facing screens (Safety inbox, HR safety-record picker,
Field Leadership safety dashboard, executive safety rollup, global
search Safety group, exports, PDFs).

Applies to reads on:
  * ``incidents``               — incident records
  * ``jhas``                    — job-hazard analyses
  * ``inspections``             — safety inspections
  * ``meetings``                — safety / toolbox meetings
  * ``safety_documents``        — safety documents / policies
  * ``safety_equipment_issuances`` — issuance records
  * ``safety_training_records`` — training / certification
"""
from __future__ import annotations

import re
from typing import Any, Dict, List


_TEST_SENTINEL_RE = (
    r"^("
    r"TEST[_\-]"
    r"|SMOKE[_\-]"
    r"|SYNTHETIC[_\-]"
    r"|CERT_TEST"
    r"|PARITY_"
    r"|ITER[0-9]"
    r")"
)

# Fields checked per collection (identity + free-text where a
# TEST_28_06_ prefix would land during E2E runs).
INCIDENT_FIELDS = ("project_name", "project_number", "location", "reported_by", "doc_id")
JHA_FIELDS = ("project_name", "project_number", "task", "doc_id")
INSPECTION_FIELDS = ("project_name", "project_number", "inspector_name", "doc_id")
MEETING_FIELDS = ("project_name", "project_number", "topic", "presenter_name", "doc_id")
SAFETY_DOC_FIELDS = ("title", "project_number")
SAFETY_TRAINING_FIELDS = ("employee_name", "training_name", "project_number")
SAFETY_ISSUANCE_FIELDS = ("employee_name", "equipment_name")


def _clauses(fields: tuple[str, ...]) -> List[Dict[str, Any]]:
    return (
        [{"synthetic_record": {"$ne": True}}, {"hidden_from_operations": {"$ne": True}}]
        + [{f: {"$not": {"$regex": _TEST_SENTINEL_RE, "$options": "i"}}} for f in fields]
    )


def _apply(query: Dict[str, Any], fields: tuple[str, ...]) -> Dict[str, Any]:
    q = dict(query or {})
    extras = _clauses(fields)
    if isinstance(q.get("$and"), list):
        q["$and"] = q["$and"] + extras
    else:
        q["$and"] = extras
    return q


def apply_synthetic_incident_exclusion(query): return _apply(query, INCIDENT_FIELDS)
def apply_synthetic_jha_exclusion(query): return _apply(query, JHA_FIELDS)
def apply_synthetic_inspection_exclusion(query): return _apply(query, INSPECTION_FIELDS)
def apply_synthetic_meeting_exclusion(query): return _apply(query, MEETING_FIELDS)
def apply_synthetic_safety_doc_exclusion(query): return _apply(query, SAFETY_DOC_FIELDS)
def apply_synthetic_safety_training_exclusion(query): return _apply(query, SAFETY_TRAINING_FIELDS)
def apply_synthetic_safety_issuance_exclusion(query): return _apply(query, SAFETY_ISSUANCE_FIELDS)


def is_synthetic_safety_doc(doc: Dict[str, Any], fields: tuple[str, ...] = INCIDENT_FIELDS) -> bool:
    if not doc:
        return False
    if doc.get("synthetic_record") is True or doc.get("hidden_from_operations") is True:
        return True
    for f in fields:
        v = doc.get(f)
        if isinstance(v, str) and re.match(_TEST_SENTINEL_RE, v.strip(), re.IGNORECASE):
            return True
    return False


__all__ = [
    "apply_synthetic_incident_exclusion",
    "apply_synthetic_jha_exclusion",
    "apply_synthetic_inspection_exclusion",
    "apply_synthetic_meeting_exclusion",
    "apply_synthetic_safety_doc_exclusion",
    "apply_synthetic_safety_training_exclusion",
    "apply_synthetic_safety_issuance_exclusion",
    "is_synthetic_safety_doc",
    "INCIDENT_FIELDS", "JHA_FIELDS", "INSPECTION_FIELDS", "MEETING_FIELDS",
    "SAFETY_DOC_FIELDS", "SAFETY_TRAINING_FIELDS", "SAFETY_ISSUANCE_FIELDS",
]
