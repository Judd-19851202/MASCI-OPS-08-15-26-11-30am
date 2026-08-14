"""GD-0023 — KPI-EFFICIENCY-PERCENT canonical contract + failure injection.

Falsifiable: asserts distinct efficiency concepts share ONE governed divide/zero
handler, 100 is not clamped, and zero-denominator uses the governed mode (0.0 for
the numeric PM-workspace surface, None where UNKNOWN can render).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.kpi_efficiency import efficiency_percent


def test_basic_ratio():
    assert efficiency_percent(80, 100) == 80.0
    assert efficiency_percent(100, 100) == 100.0


def test_over_100_is_legitimate_not_clamped():
    # beating the budget / producing faster than target is real, must not clamp
    assert efficiency_percent(130, 100) == 130.0
    assert efficiency_percent(250, 100) == 250.0


def test_zero_denominator_zero_mode():
    # numeric PM-workspace surface: no consumed resource -> 0.0 (governed)
    assert efficiency_percent(50, 0, mode="zero") == 0.0
    assert efficiency_percent(50, -3, mode="zero") == 0.0


def test_zero_denominator_unknown_mode():
    # a surface that can render UNKNOWN must not fabricate 0% efficiency
    assert efficiency_percent(50, 0, mode="unknown") is None
    assert efficiency_percent(0, 0, mode="unknown") is None


def test_none_and_nonnumeric_are_unknown():
    assert efficiency_percent(None, 100) is None
    assert efficiency_percent(100, None) is None
    assert efficiency_percent("x", 100) is None


def test_rounding():
    assert efficiency_percent(1, 3) == 33.33


def test_oppc_execution_routes_through_canonical():
    # Blast-radius: activity labor/production efficiency must delegate.
    import inspect
    from services.cost_codes import oppc_execution as oe
    src = inspect.getsource(oe.build_project_execution_workspace)
    assert "_canon_efficiency(" in src, "efficiency must route through canonical owner"
    # the old inline 'else 0.0' ternary efficiency formula must be gone
    assert "actual_labor_hours_week\"]) * 100.0, 2) if slot" not in src
