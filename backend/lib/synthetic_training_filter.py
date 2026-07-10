"""TRACK 28.07 · Synthetic Training / Qualification exclusion filter.

Same doctrine as 28.02B/28.03/28.04/28.05/28.06. Certification test
fixtures using ``TEST_28_07_`` / ``SYNTHETIC_`` / ``ITER[0-9]``
prefixes on identity fields of Training + Qualification collections
must never surface on operator screens (HR training tab, Safety
credential registry, Executive compliance rollup, Dispatch driver-
qualification dashboard, Competent Person picker, public QR
verification, exports, PDFs).

Applies to reads on:
  * ``safety_training_records`` — canonical qualification / training / license / endorsement
  * ``qualification_attachments`` — evidence uploads
  * ``training_track_records``   — legacy training track history
  * ``training_guides``          — training video library
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

# Fields checked per collection.
QUALIFICATION_FIELDS = (
    "employee_name", "training_name", "qualification_type",
    "credential_number", "project_number", "instructor_name",
    "certifying_authority",
)
TRAINING_TRACK_FIELDS = ("employee_name", "training_name", "track_name")
QUAL_ATTACHMENT_FIELDS = ("filename", "uploaded_by")
TRAINING_GUIDE_FIELDS = ("title", "slug")


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


def apply_synthetic_qualification_exclusion(query): return _apply(query, QUALIFICATION_FIELDS)
def apply_synthetic_training_track_exclusion(query): return _apply(query, TRAINING_TRACK_FIELDS)
def apply_synthetic_qual_attachment_exclusion(query): return _apply(query, QUAL_ATTACHMENT_FIELDS)
def apply_synthetic_training_guide_exclusion(query): return _apply(query, TRAINING_GUIDE_FIELDS)


def is_synthetic_training_doc(doc: Dict[str, Any], fields: tuple[str, ...] = QUALIFICATION_FIELDS) -> bool:
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
    "apply_synthetic_qualification_exclusion",
    "apply_synthetic_training_track_exclusion",
    "apply_synthetic_qual_attachment_exclusion",
    "apply_synthetic_training_guide_exclusion",
    "is_synthetic_training_doc",
    "QUALIFICATION_FIELDS", "TRAINING_TRACK_FIELDS",
    "QUAL_ATTACHMENT_FIELDS", "TRAINING_GUIDE_FIELDS",
]
