"""TRACK 24.9 · Synthetic / Test Daily Report exclusion filter.

Production PM screens (Command Center latest, Approved Daily
Reports export, Recent Photos, PM KPIs, Safety KPIs) were
surfacing synthetic smoke/certification records such as:
  * TEST_247B_EMAIL_RECERT
  * TEST_DR_V3_EMAIL_PARITY_ES
  * TEST_DR_V3_EMAIL_PARITY_EN
  * TEST_DR_*   / TEST-*      · iter79, iter250, iter452 harness fixtures
  * TEST_QA / TEST_Numbering / TEST_SAFETY_ESC_ROUNDTRIP · early QA fixtures
  * 0000-TEST / TEST-25-XX / TEST-45XX / TEST-PHOTO-* project number stubs

These must never appear on user-facing operational screens.

Doctrine:
  * Never hard-delete a Daily Report. Audit history stays intact.
  * User-facing queries add `apply_synthetic_dr_exclusion(query)`
    which mixes an $and clause excluding synthetic docs.
  * Explicit markers win: `synthetic_record=true` OR
    `hidden_from_operations=true` → excluded unconditionally.
  * Heuristic markers cover legacy fixtures that pre-date the
    explicit flags: project_number regex against `_TEST_PROJECT_RE`
    catches `TEST_*`, `TEST-*`, `0000-TEST`, `SMOKE-*`, etc.
  * The heuristic is intentionally conservative — real projects
    with names containing "test" (rare in construction) are
    preserved by anchoring the regex at the START of the field.
"""
from __future__ import annotations

from typing import Any, Dict, List

# Regex applied to `project_number` (and `doc_id` as a safety net)
# to catch legacy synthetic fixtures. Anchored so it only matches
# strings that START with a known synthetic sentinel — a real
# project like "SR-TESTING-4" would NOT match.
#
# Sentinels:
#   TEST_       · iter79/iter250/iter452 harness pattern
#   TEST-       · TEST-25-23 / TEST-4525 / TEST-PHOTO fixtures
#   0000-TEST   · doc-id smoke fixtures
#   SMOKE       · smoke test fixtures
#   SYNTHETIC   · explicit synthetic fixtures
#   ITER        · iter### harness fixtures
#   QA_SMOKE / CERT_TEST / RECERT / PARITY  · certification fixtures
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

# Also match project NAME sentinels — some legacy fixtures set a
# clean project_number but a "TEST_" project_name. Kept separate
# from the project_number regex so a legitimate project can never
# be caught by the name heuristic alone if it has a real
# project_number.
_TEST_NAME_RE = (
    r"^("
    r"TEST_"
    r"|TEST-"
    r"|SMOKE_"
    r"|SYNTHETIC_"
    r"|iter[0-9]"
    r"|QA_SMOKE"
    r"|CERT_TEST"
    r")"
)

# Explicit markers that unconditionally hide a record from user-
# facing screens. These are set by the Track 24.9 cleanup script
# and by future synthetic submissions that opt into the hidden
# lane. Never remove them from the exclusion set.
_EXPLICIT_MARKERS = ["synthetic_record", "hidden_from_operations"]


def synthetic_exclusion_clauses() -> List[Dict[str, Any]]:
    """Return the mongo $and clauses that exclude synthetic DRs."""
    return [
        {"synthetic_record": {"$ne": True}},
        {"hidden_from_operations": {"$ne": True}},
        {"project_number": {"$not": {"$regex": _TEST_PROJECT_RE, "$options": "i"}}},
        {"project_name": {"$not": {"$regex": _TEST_NAME_RE, "$options": "i"}}},
    ]


def apply_synthetic_dr_exclusion(query: Dict[str, Any]) -> Dict[str, Any]:
    """Mix synthetic exclusion into a mongo query.

    Idempotent — calling twice yields the same effective query.
    The clauses are appended to `$and` so callers with existing
    `$or` / equality clauses remain intact.
    """
    q = dict(query or {})
    extra = synthetic_exclusion_clauses()
    existing = q.get("$and")
    if isinstance(existing, list):
        q["$and"] = existing + extra
    else:
        q["$and"] = extra
    return q


def is_synthetic_dr(doc: Dict[str, Any]) -> bool:
    """Python-side classifier used by the cleanup script + tests."""
    import re
    if not doc:
        return False
    if doc.get("synthetic_record") is True:
        return True
    if doc.get("hidden_from_operations") is True:
        return True
    pn = (doc.get("project_number") or "").strip()
    if pn and re.match(_TEST_PROJECT_RE, pn, re.IGNORECASE):
        return True
    name = (doc.get("project_name") or "").strip()
    if name and re.match(_TEST_NAME_RE, name, re.IGNORECASE):
        return True
    return False


__all__ = [
    "synthetic_exclusion_clauses",
    "apply_synthetic_dr_exclusion",
    "is_synthetic_dr",
]
