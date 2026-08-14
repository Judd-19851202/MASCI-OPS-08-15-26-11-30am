"""GD-0017 — canonical % Complete contract guard (Wave 5, KPI-PERCENT-COMPLETE).

Locks the governed semantics of the shared calculators in lib.kpi_percent_complete
BEFORE consumers are migrated. Distinct concepts stay distinct; empty-denominator,
rounding and clamp behaviour are pinned.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path("/app/backend")))
from lib.kpi_percent_complete import (  # noqa: E402
    clamp_stored_percent, checklist_percent, checklist_percent_from_flags, schedule_rollup_percent,
)


def test_stored_clamps_and_missing_is_none_not_zero():
    assert clamp_stored_percent(50) == 50.0
    assert clamp_stored_percent(150) == 100.0
    assert clamp_stored_percent(-5) == 0.0
    assert clamp_stored_percent("") is None          # missing = unknown, NEVER silently 0
    assert clamp_stored_percent(None) is None
    assert clamp_stored_percent("abc") is None
    assert clamp_stored_percent(None, missing=0.0) == 0.0


def test_checklist_ratio_and_empty_denominator():
    assert checklist_percent(0, 0) == 0.0             # empty denominator -> 0, no ZeroDivisionError
    assert checklist_percent(3, 4) == 75.0
    assert checklist_percent(4, 4) == 100.0
    assert checklist_percent(9, 4) == 100.0           # clamped
    assert checklist_percent(-1, 4) == 0.0
    assert checklist_percent_from_flags([True, True, False, False]) == 50.0
    assert checklist_percent_from_flags([]) == 0.0


def test_schedule_rollup_max_mean_and_empty():
    assert schedule_rollup_percent([10, 90, 40]) == 90.0            # default max
    assert schedule_rollup_percent([10, 90, 40], agg="mean") == 46.67
    assert schedule_rollup_percent([]) == 0.0                       # empty scope -> 0
    assert schedule_rollup_percent([None, 50, ""]) == 50.0          # missing treated as 0 in rollup


def test_concepts_are_distinct_not_one_formula():
    # A stored 0-entered value (known 0%) must NOT be conflated with an empty checklist.
    assert clamp_stored_percent(0) == 0.0
    assert clamp_stored_percent("") is None
    # checklist 0/0 (nothing to complete) vs stored unknown are different truths.
    assert checklist_percent(0, 0) == 0.0
    assert clamp_stored_percent(None) is None
