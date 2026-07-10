"""TRACK 28.04 · Synthetic / Test HR Employee exclusion filter.

Same doctrine as ``synthetic_dr_filter`` (TRACK 24.9) and
``synthetic_flr_filter`` (TRACK 28.03) but for the ``employees``
collection. Certification / smoke-test / TEST-prefixed employee
records must never surface on any user-facing operational screen
(HR roster, HR filter facets, HR completeness snapshot, HR
accountability timeline, HR time-verification, HR training
records, employee pickers on Daily Report / Field Leadership /
Safety / Dispatch / Fleet / Shop, admin employee list, admin
employee CSV export, global search Cmd+K).

Sentinel fields checked (any match → exclude):
  • ``synthetic_record: true``          — explicit opt-in
  • ``hidden_from_operations: true``    — explicit opt-in
  • ``name``                            — starts with TEST_ / TEST-
  • ``preferred_name``                  — starts with TEST_ / TEST-
  • ``legal_first_name``                — starts with TEST_ / TEST-
  • ``legal_last_name``                 — starts with TEST_ / TEST-
  • ``email``                           — starts with test_28_04_ / test-28-04 (both prefix + literal `+` variants tolerated)
  • ``employee_id``                     — starts with TEST_ / TEST-

Anchored regexes preserve real employees (e.g. someone legally
named "Testa" starts with 'Testa', which does not match TEST_ or
TEST- because of the required trailing sentinel character).
"""
from __future__ import annotations

from typing import Any, Dict, List


# Anchored so a real employee named "Testa" would NOT match. Same
# regex family as synthetic_flr_filter.
_TEST_NAME_RE = (
    r"^("
    r"TEST[_\-]"
    r"|SMOKE[_\-]"
    r"|SYNTHETIC[_\-]"
    r"|CERT_TEST"
    r"|PARITY_"
    r"|ITER[0-9]"
    r")"
)

# Email pattern — lowercased and matches both `test_28_04_...` and
# `test-28-04...` at start-of-string. Also matches the +-tag pattern
# some fixtures use: `hrmanager+test_28_04@…`.
_TEST_EMAIL_RE = (
    r"("
    r"^test[_\-]28[_\-]04"
    r"|^synthetic[_\-]"
    r"|^smoke[_\-]"
    r"|^iter[0-9]"
    r"|\+test[_\-]28[_\-]04"
    r"|\+synthetic[_\-]"
    r")"
)


def synthetic_hr_exclusion_clauses() -> List[Dict[str, Any]]:
    """Return the mongo $and clauses that exclude synthetic employees."""
    return [
        {"synthetic_record": {"$ne": True}},
        {"hidden_from_operations": {"$ne": True}},
        {"name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"preferred_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"legal_first_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"legal_last_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"employee_id": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
        {"email": {"$not": {"$regex": _TEST_EMAIL_RE, "$options": "i"}}},
    ]


def apply_synthetic_hr_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query for the ``employees``
    collection. Idempotent — calling twice yields the same effective
    query."""
    q = dict(query or {})
    extra = synthetic_hr_exclusion_clauses()
    existing = q.get("$and")
    if isinstance(existing, list):
        q["$and"] = existing + extra
    else:
        q["$and"] = extra
    return q


def is_synthetic_hr(doc: Dict[str, Any]) -> bool:
    """Python-side classifier used by cleanup + tests."""
    import re
    if not doc:
        return False
    if doc.get("synthetic_record") is True:
        return True
    if doc.get("hidden_from_operations") is True:
        return True
    for field in (
        "name", "preferred_name", "legal_first_name", "legal_last_name",
        "employee_id",
    ):
        val = (doc.get(field) or "").strip() if isinstance(doc.get(field), str) else ""
        if val and re.match(_TEST_NAME_RE, val, re.IGNORECASE):
            return True
    email = (doc.get("email") or "").strip().lower() if isinstance(doc.get("email"), str) else ""
    if email and re.search(_TEST_EMAIL_RE, email, re.IGNORECASE):
        return True
    return False


__all__ = [
    "synthetic_hr_exclusion_clauses",
    "apply_synthetic_hr_exclusion",
    "is_synthetic_hr",
]
