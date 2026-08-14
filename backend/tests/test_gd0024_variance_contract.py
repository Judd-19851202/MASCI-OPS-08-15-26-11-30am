"""GD-0024 — KPI-VARIANCE-PERCENT canonical contract + failure injection.

Falsifiable: each test asserts the governed sign convention, zero/negative
baseline handling, and per-concept favorable/unfavorable interpretation. A test
FAILS if the old ungoverned behavior (generic positive=good, silent zero-mask,
or wrong sign) is reintroduced.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.kpi_variance import variance_percent, variance_favorable


def test_sign_convention_actual_minus_baseline():
    # actual above baseline -> positive
    assert variance_percent(120, 100, mode="honest_unknown") == 20.0
    # actual below baseline -> negative
    assert variance_percent(80, 100, mode="honest_unknown") == -20.0
    # equal -> 0
    assert variance_percent(100, 100, mode="honest_unknown") == 0.0


def test_zero_baseline_honest_unknown_is_none():
    # A percentage with no baseline is UNKNOWN, never a silent 0.
    assert variance_percent(50, 0, mode="honest_unknown") is None
    assert variance_percent(0, 0, mode="honest_unknown") is None
    assert variance_percent(50, -5, mode="honest_unknown") is None


def test_zero_baseline_unplanned_is_full():
    # planning/production: nothing planned + nothing done -> 0; unplanned work -> 100
    assert variance_percent(0, 0, mode="unplanned_is_full") == 0.0
    assert variance_percent(12, 0, mode="unplanned_is_full") == 100.0
    assert variance_percent(12, -3, mode="unplanned_is_full") == 100.0


def test_none_and_nonnumeric_inputs_are_unknown():
    assert variance_percent(None, 100) is None
    assert variance_percent(100, None) is None
    assert variance_percent("x", 100) is None


def test_favorable_is_per_concept_not_generic_sign():
    # cost/labor OVER baseline (positive) is UNFAVORABLE
    assert variance_favorable("cost", 15.0) == "unfavorable"
    assert variance_favorable("labor", -10.0) == "favorable"
    # production/quantity OVER baseline (positive) is FAVORABLE
    assert variance_favorable("production", 15.0) == "favorable"
    assert variance_favorable("quantity", -10.0) == "unfavorable"
    # schedule slip (more days) is UNFAVORABLE
    assert variance_favorable("schedule", 5.0) == "unfavorable"


def test_favorable_neutral_and_unknown_states():
    assert variance_favorable("cost", 0.0) == "neutral"
    assert variance_favorable("cost", None) == "unknown"
    # unrecognised concept must NOT be guessed as good/bad
    assert variance_favorable("mystery_concept", 20.0) == "unknown"


def test_extreme_and_over_100_not_clamped():
    assert variance_percent(300, 100, mode="honest_unknown") == 200.0
    assert variance_percent(1000, 1, mode="honest_unknown") == 99900.0


def test_oppc_intelligence_uses_canonical_owner():
    # Blast-radius: the OPPC variance-intelligence engine must delegate, not
    # re-implement, so schedule/production/labor/productivity all agree.
    from services.cost_codes import oppc_intelligence as oi
    assert oi._variance_percent(100.0, 120.0) == 20.0     # planned=100 actual=120
    assert oi._variance_percent(0.0, 0.0) == 0.0
    assert oi._variance_percent(0.0, 5.0) == 100.0


def test_four_quadrant_favorable_render_semantics():
    # The UI color/state MUST come from these four governed quadrants, not raw sign.
    # positive favorable: produced MORE than planned (good)
    assert variance_favorable("production", 12.0) == "favorable"
    # positive unfavorable: burned MORE labor than budget (bad)
    assert variance_favorable("labor", 12.0) == "unfavorable"
    # negative favorable: used LESS cost than baseline (good)
    assert variance_favorable("cost", -12.0) == "favorable"
    # negative unfavorable: produced LESS than planned (bad)
    assert variance_favorable("production", -12.0) == "unfavorable"


def test_oppc_intelligence_emits_governed_favorable_field():
    # The variance payload must carry the governed favorable direction so the UI
    # never has to guess from sign.
    import inspect
    from services.cost_codes import oppc_intelligence as oi
    src = inspect.getsource(oi.build_project_variance_intelligence)
    assert '"favorable": variance_favorable(' in src, "variance payload must emit governed favorable"

