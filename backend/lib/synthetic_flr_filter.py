"""TRACK 28.03 · Synthetic Field-Leadership record exclusion filter.

Same doctrine as ``synthetic_dr_filter`` (TRACK 24.9) but for the
``field_leadership_records`` collection. Certification /
smoke-test / TEST-prefixed FL records must never surface on any
user-facing operational screen (admin FL browser, mobile FL portal,
HR queues, PDF exports, CSV exports).

Sentinel fields checked (any match → exclude):
  • ``synthetic_record: true``          — explicit opt-in
  • ``hidden_from_operations: true``    — explicit opt-in
  • ``employee_name``                   — starts with TEST_ / TEST-
  • ``supervisor_name``                 — starts with TEST_ / TEST-
  • ``project_number``                  — same regex family as DR
  • ``project_name``                    — same regex family as DR
  • ``submitted_by_name``               — starts with TEST_ / TEST-

FL records don't always carry a project (some kinds like
``verbal_coaching`` are project-agnostic), so the primary
identity is the employee_name / supervisor_name — that is what
E2E fixtures prefix with ``TEST_28_03_``.
"""
from __future__ import annotations

from typing import Any, Dict, List


# Anchored so a real employee named "Testa" would NOT match.
_TEST_NAME_RE = (
    r"^("
    r"TEST[_\-]"
    r"|SMOKE[_\-]"
    r"|SYNTHETIC[_\-]"
    r"|CERT_TEST"
    r"|PARITY_"
    r")"
)

_TEST_PROJECT_RE = (
    r"^("
    r"TEST[_\-]"
    r"|0000-TEST"
    r"|SMOKE[_\-]"
    r"|SYNTHETIC[_\-]"
    r"|ITER[0-9]"
    r"|QA_SMOKE"
    r"|CERT_TEST"
    r"|RECERT"
    r"|PARITY"
    r")"
)


def synthetic_flr_exclusion_clauses() -> List[Dict[str, Any]]:
    """Return the mongo $and clauses that exclude synthetic FL records."""
    return [
        {"synthetic_record": {"$ne": True}},
        {"hidden_from_operations": {"$ne": True}},
        {"employee_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"supervisor_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"submitted_by_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"project_number": {"$not": {"$regex": _TEST_PROJECT_RE, "$options": "i"}}},
        {"project_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
    ]


def apply_synthetic_flr_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query for
    ``field_leadership_records``. Idempotent — calling twice yields
    the same effective query."""
    q = dict(query or {})
    extra = synthetic_flr_exclusion_clauses()
    existing = q.get("$and")
    if isinstance(existing, list):
        q["$and"] = existing + extra
    else:
        q["$and"] = extra
    return q


def is_synthetic_flr(doc: Dict[str, Any]) -> bool:
    """Python-side classifier used by cleanup + tests."""
    import re
    if not doc:
        return False
    if doc.get("synthetic_record") is True:
        return True
    if doc.get("hidden_from_operations") is True:
        return True
    for field in ("employee_name", "supervisor_name", "submitted_by_name", "project_name"):
        val = (doc.get(field) or "").strip()
        if val and re.match(_TEST_NAME_RE, val, re.IGNORECASE):
            return True
    pn = (doc.get("project_number") or "").strip()
    if pn and re.match(_TEST_PROJECT_RE, pn, re.IGNORECASE):
        return True
    return False


__all__ = [
    "synthetic_flr_exclusion_clauses",
    "apply_synthetic_flr_exclusion",
    "is_synthetic_flr",
]
