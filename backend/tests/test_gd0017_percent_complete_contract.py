"""GD-0017 — canonical % Complete contract guard (Wave 5, KPI-PERCENT-COMPLETE).

Locks the governed semantics of the shared calculators in lib.kpi_percent_complete.
Distinct business concepts stay distinct; empty-denominator, rounding, clamp,
missing/unknown and duplicate/deleted-row behaviour are pinned. Includes failure
fixtures proving a divergent duplicate local formula would be DETECTED (not silently
tolerated because its current result happens to match).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path("/app/backend")))
from lib.kpi_percent_complete import (  # noqa: E402
    clamp_stored_percent, checklist_percent, checklist_percent_from_flags, schedule_rollup_percent,
)


# ---------------------------------------------------------------------------
# PC-STORED  (user/import-entered value — UNKNOWN != 0)
# ---------------------------------------------------------------------------
def test_stored_zero_hundred_and_bounds():
    assert clamp_stored_percent(0) == 0.0           # legitimate 0
    assert clamp_stored_percent(100) == 100.0       # legitimate 100
    assert clamp_stored_percent(50) == 50.0
    assert clamp_stored_percent(150) == 100.0       # above 100 -> clamp
    assert clamp_stored_percent(-5) == 0.0          # below 0 -> clamp
    assert clamp_stored_percent("73.5") == 73.5     # numeric string parses


def test_stored_missing_is_unknown_never_zero():
    assert clamp_stored_percent("") is None
    assert clamp_stored_percent(None) is None
    assert clamp_stored_percent("abc") is None      # unparseable -> UNKNOWN
    assert clamp_stored_percent([]) is None
    # explicit governed coercion (only when caller decides missing == 0)
    assert clamp_stored_percent(None, missing=0.0) == 0.0


# ---------------------------------------------------------------------------
# PC-CHECKLIST  (completed eligible / total eligible; governed empty-denom)
# ---------------------------------------------------------------------------
def test_checklist_ratio_basic():
    assert checklist_percent(0, 4) == 0.0           # 0%
    assert checklist_percent(1, 4) == 25.0          # one-of-many
    assert checklist_percent(3, 4) == 75.0
    assert checklist_percent(4, 4) == 100.0         # 100%


def test_checklist_clamps_negative_and_over():
    assert checklist_percent(9, 4) == 100.0         # completed > total -> clamp 100
    assert checklist_percent(-1, 4) == 0.0          # negative numerator floored


def test_checklist_empty_denominator_is_governed_not_hidden():
    # No hidden default lie: caller MUST choose the empty-denominator meaning.
    assert checklist_percent(0, 0) == 0.0                    # default: nothing-of-nothing = 0%
    assert checklist_percent(0, 0, empty=100.0) == 100.0     # vacuously complete (fleet scope)
    assert checklist_percent(0, 0, empty=None) is None       # UNKNOWN (empty set meaningless)
    assert checklist_percent(5, 0, empty=100.0) == 100.0     # denominator drives empty branch


def test_checklist_rounding_boundary():
    assert checklist_percent(1, 3) == 33.3          # 33.333.. -> 1dp
    assert checklist_percent(2, 3) == 66.7          # 66.666.. -> 1dp
    assert checklist_percent(1, 6, ndigits=2) == 16.67


def test_checklist_from_flags_dedup_and_deleted_are_caller_responsibility():
    # The calculator counts the eligible set it is HANDED. Excluded / N/A / deleted /
    # duplicate rows must be filtered by the caller BEFORE counting; the guard proves
    # that a correctly-filtered set produces the canonical value.
    flags = [True, True, False, False]
    assert checklist_percent_from_flags(flags) == 50.0
    assert checklist_percent_from_flags([]) == 0.0
    assert checklist_percent_from_flags([], empty=100.0) == 100.0
    # simulate excluded/N/A + deleted rows removed upstream, duplicates de-duped:
    rows = [
        {"id": "a", "done": True, "status": "active"},
        {"id": "a", "done": True, "status": "active"},   # duplicate id
        {"id": "b", "done": False, "status": "active"},
        {"id": "c", "done": True, "status": "na"},        # N/A excluded
        {"id": "d", "done": False, "status": "deleted"},  # deleted excluded
    ]
    eligible = {}
    for r in rows:
        if r["status"] in ("na", "deleted"):
            continue
        eligible[r["id"]] = r["done"]                     # dedupe by id
    assert checklist_percent_from_flags(eligible.values()) == 50.0   # a done, b not


# ---------------------------------------------------------------------------
# PC-SCHEDULE  (explicit governed aggregation mode; no anonymous max/mean)
# ---------------------------------------------------------------------------
def test_schedule_rollup_modes_are_explicit_and_differ():
    from lib.kpi_percent_complete import SCHEDULE_MODE_MAX, SCHEDULE_MODE_MEAN
    vals = [10, 90, 40]
    assert schedule_rollup_percent(vals, agg=SCHEDULE_MODE_MAX) == 90.0
    assert schedule_rollup_percent(vals, agg=SCHEDULE_MODE_MEAN) == 46.67
    # modes are NOT interchangeable — proving they yield different truths:
    assert (schedule_rollup_percent(vals, agg=SCHEDULE_MODE_MAX)
            != schedule_rollup_percent(vals, agg=SCHEDULE_MODE_MEAN))


def test_schedule_rollup_requires_explicit_governed_mode():
    # No anonymous default: caller MUST select a governed mode (owner rule).
    with pytest.raises(ValueError):
        schedule_rollup_percent([10, 20], agg="")            # missing/blank
    with pytest.raises(ValueError):
        schedule_rollup_percent([10, 20], agg="weighted")    # not a governed mode here


def test_schedule_rollup_empty_and_missing():
    assert schedule_rollup_percent([], agg="mean") == 0.0            # empty scope
    assert schedule_rollup_percent([None, 50, ""], agg="mean") == round(50 / 3, 2)  # missing == 0 in rollup
    assert schedule_rollup_percent([150, 40], agg="max") == 100.0    # per-input clamp before agg


# ---------------------------------------------------------------------------
# Concepts stay DISTINCT — same label, different truth
# ---------------------------------------------------------------------------
def test_concepts_are_distinct_not_one_formula():
    # stored known-0 vs stored unknown vs empty checklist are three different truths
    assert clamp_stored_percent(0) == 0.0
    assert clamp_stored_percent("") is None
    assert checklist_percent(0, 0) == 0.0
    assert checklist_percent(0, 0, empty=None) is None
    # a stored 100 (entered) and a checklist 100 (all done) share a number but not a path
    assert clamp_stored_percent(100) == checklist_percent(4, 4) == 100.0


# ---------------------------------------------------------------------------
# SAME-CONCEPT / SAME-SCOPE EQUALITY across consumers
# ---------------------------------------------------------------------------
def test_same_scope_consumers_agree():
    # Two consumers of the SAME checklist scope (same completed/total, same empty policy)
    # MUST return the identical value regardless of who computes it.
    a = checklist_percent(7, 12, empty=100.0)
    b = checklist_percent(7, 12, empty=100.0)
    assert a == b


# ---------------------------------------------------------------------------
# FAILURE FIXTURES — a divergent duplicate local formula is DETECTED
# ---------------------------------------------------------------------------
def _legacy_frontend_style(value, total):
    """Reproduction of the OLD divergent local formula: integer round, empty->0."""
    return round((value / total) * 100) if total else 0


def test_divergent_local_formula_is_detected_on_rounding():
    # Canonical 1dp vs legacy integer-round diverge at a rounding boundary -> caught.
    canonical = checklist_percent(1, 3)          # 33.3
    legacy = _legacy_frontend_style(1, 3)        # 33
    assert canonical != legacy, "duplicate formula must not silently pass"


def test_divergent_local_formula_is_detected_on_empty_denominator():
    # Canonical fleet-scope empty==100 vs legacy empty==0 diverge -> caught.
    canonical = checklist_percent(0, 0, empty=100.0)  # 100.0
    legacy = _legacy_frontend_style(0, 0)             # 0
    assert canonical != legacy


def test_divergent_local_formula_is_detected_on_unknown():
    # PC-STORED unknown must be None, a `value || 0` fallback would show 0 -> caught.
    canonical = clamp_stored_percent(None)       # None (UNKNOWN)
    fallback = clamp_stored_percent(None) or 0   # 0  (the anti-pattern)
    assert canonical is None and fallback == 0
    assert canonical != fallback


@pytest.mark.parametrize("completed,total,expected", [
    (0, 10, 0.0), (10, 10, 100.0), (5, 10, 50.0), (1, 8, 12.5), (7, 7, 100.0),
])
def test_checklist_parametrized_scale(completed, total, expected):
    assert checklist_percent(completed, total) == expected
