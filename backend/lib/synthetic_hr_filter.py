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

from lib.governed_fixture_evidence import is_governed_fixture
from lib.governed_record_classification import (
    apply_governed_visibility_exclusion,
    governed_visibility_exclusion_clauses,
)


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
    """Return the governed visibility clauses for operator-facing employee reads."""
    return governed_visibility_exclusion_clauses()


def apply_synthetic_hr_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query for the ``employees``
    collection. Idempotent — calling twice yields the same effective
    query."""
    return apply_governed_visibility_exclusion(query)


def is_synthetic_hr(doc: Dict[str, Any]) -> bool:
    """Python-side classifier used by cleanup + tests."""
    return is_governed_fixture(doc, "employees")


__all__ = [
    "synthetic_hr_exclusion_clauses",
    "apply_synthetic_hr_exclusion",
    "is_synthetic_hr",
]
