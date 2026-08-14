"""GD-0021 — canonical COMPLIANCE-RATE zero-denominator contract (Wave 5).

Owner rule: zero APPLICABLE population = NOT_APPLICABLE (value null), NOT 0%.
A legitimate zero numerator over a real population = 0%. Missing/undeterminable
denominator = UNKNOWN (never masquerades as N/A). Numeric typing preserved.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path("/app/backend")))
from lib.kpi_percent_complete import (  # noqa: E402
    compliance_rate, COMPLIANCE_STATE_OK, COMPLIANCE_STATE_NA, COMPLIANCE_STATE_UNKNOWN,
)


def test_zero_eligible_is_not_applicable_not_zero():
    val, state = compliance_rate(0, 0)
    assert val is None and state == COMPLIANCE_STATE_NA          # 0 eligible -> N/A (null), not 0%


def test_legit_zero_numerator_over_real_population_is_zero_percent():
    val, state = compliance_rate(0, 10)
    assert val == 0 and state == COMPLIANCE_STATE_OK             # 10 eligible / 0 compliant -> 0%


def test_full_compliance_is_hundred():
    val, state = compliance_rate(10, 10)
    assert val == 100 and state == COMPLIANCE_STATE_OK           # 10/10 -> 100%


def test_missing_or_broken_denominator_is_unknown_not_na():
    val, state = compliance_rate(5, None)
    assert val is None and state == COMPLIANCE_STATE_UNKNOWN     # undeterminable -> UNKNOWN, not N/A
    val2, state2 = compliance_rate(5, "oops")
    assert val2 is None and state2 == COMPLIANCE_STATE_UNKNOWN


def test_numeric_typing_preserved_never_string_na():
    for c, e in [(3, 4), (0, 5), (5, 5), (0, 0), (1, None)]:
        val, _ = compliance_rate(c, e)
        assert val is None or isinstance(val, (int, float))     # never the string "N/A"


def test_partial_and_rounding():
    val, state = compliance_rate(3, 4)
    assert val == 75 and state == COMPLIANCE_STATE_OK
    val2, _ = compliance_rate(1, 3, ndigits=1)
    assert val2 == 33.3


def test_na_is_distinct_from_unknown_and_from_zero():
    na = compliance_rate(0, 0)
    unk = compliance_rate(0, None)
    zero = compliance_rate(0, 5)
    assert na[1] != unk[1] != zero[1]
    assert na[0] is None and unk[0] is None and zero[0] == 0
