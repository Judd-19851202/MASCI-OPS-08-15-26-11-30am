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

import re
from typing import Any, Dict, List, Optional

from lib.governed_fixture_evidence import is_governed_fixture
from lib.governed_record_classification import (
    apply_governed_visibility_exclusion,
    governed_visibility_exclusion_clauses,
)


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
    """Return the governed visibility clauses for operator-facing FL reads."""
    return governed_visibility_exclusion_clauses() + [
        _field_regex_not_test("employee_name", _TEST_NAME_RE),
        _field_regex_not_test("supervisor_name", _TEST_NAME_RE),
        _field_regex_not_test("project_number", _TEST_PROJECT_RE),
        _field_regex_not_test("project_name", _TEST_PROJECT_RE),
        _field_regex_not_test("submitted_by_name", _TEST_NAME_RE),
    ]


def _field_regex_not_test(field: str, pattern: str) -> Dict[str, Any]:
    return {
        "$or": [
            {field: {"$exists": False}},
            {field: None},
            {field: ""},
            {field: {"$not": {"$regex": pattern, "$options": "i"}}},
        ]
    }


def _apply_exclusion(query: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    q = dict(query or {})
    extra = synthetic_flr_exclusion_clauses()
    existing = q.get("$and")
    if isinstance(existing, list):
        q["$and"] = existing + extra
    else:
        q["$and"] = extra
    return q


def apply_synthetic_flr_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query for
    ``field_leadership_records``. Idempotent — calling twice yields
    the same effective query."""
    return _apply_exclusion(query)


def _matches_literal(doc: Dict[str, Any]) -> bool:
    def _hit(value: Any, pattern: str) -> bool:
        if not isinstance(value, str):
            return False
        return re.search(pattern, value.strip(), flags=re.I) is not None

    return any(
        _hit(doc.get(field), _TEST_NAME_RE)
        for field in ("employee_name", "supervisor_name", "submitted_by_name")
    ) or any(
        _hit(doc.get(field), _TEST_PROJECT_RE)
        for field in ("project_number", "project_name")
    )


def is_synthetic_flr(doc: Dict[str, Any]) -> bool:
    """Python-side classifier used by cleanup + tests."""
    return is_governed_fixture(doc, "field_leadership_records") or _matches_literal(doc)


__all__ = [
    "synthetic_flr_exclusion_clauses",
    "apply_synthetic_flr_exclusion",
    "is_synthetic_flr",
]
