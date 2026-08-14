"""Wave 5 — CANONICAL % COMPLETE contract (shared calculator).

The label "% Complete" is used across MASCI OPS for FUNDAMENTALLY DIFFERENT business
concepts. Forcing them through one formula would itself be a truth defect. This
module defines the governed, explicitly-separated canonical calculators. Same
concept + same scope => same function here. Different concepts stay separate.

Governed concepts (see WAVE5_PERCENT_COMPLETE_CONTRACT.md for the full site map):

  PC-STORED      A user/import-entered progress value on a schedule activity or daily
                 report row. NOT a computed ratio — the canonical contract is: parse
                 to float, clamp to [0,100]. Missing/blank -> None (unknown), never 0.
                 -> clamp_stored_percent()

  PC-CHECKLIST   A computed ratio of completed items over an eligible item set
                 (onboarding steps, lifecycle tasks). numerator = completed eligible;
                 denominator = total eligible. Empty denominator -> 0.0 (nothing to do
                 == 0% work outstanding is represented as 0 complete-of-0; callers that
                 need "N/A" should check total==0 explicitly). Rounded to 1 dp.
                 -> checklist_percent()

  PC-SCHEDULE    Approved schedule progress rollup (max/avg of approved_percent_complete
                 across schedule rows for a scope). Uses clamp_stored_percent on each
                 input; aggregation mode (max or mean) MUST be chosen explicitly by the
                 caller. Empty set -> 0.0. Rounded to 2 dp.
                 -> schedule_rollup_percent(agg=SCHEDULE_MODE_MAX|MEAN)

  PC-COST        QUANTITY-based cost/progress: installed_or_actual_qty / authorized_or_planned
   (QUANTITY)    _qty. DISTINCT from the above: overrun MAY exceed 100% (no clamp by default);
                 zero/negative/missing denominator -> governed empty (default 0.0). Note: this
                 codebase has NO $-cost-burn, committed, earned-value-ratio, or billing %
                 concept among the % Complete sites — cost progress here is purely quantity.
                 -> quantity_progress_percent()

All calculators are pure and side-effect free.
"""
from __future__ import annotations

from typing import Iterable, Optional, Sequence


def _to_float(value, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp_stored_percent(value, *, missing=None) -> Optional[float]:
    """PC-STORED: parse a stored/entered progress value, clamp to [0,100].
    Blank/invalid -> `missing` (default None = unknown; NEVER silently 0)."""
    f = _to_float(value, None)
    if f is None:
        return missing
    return max(0.0, min(100.0, f))


def checklist_percent(
    completed: int, total: int, *, ndigits: int = 1, empty: Optional[float] = 0.0,
) -> Optional[float]:
    """PC-CHECKLIST: 100 * completed_eligible / total_eligible.

    `empty` GOVERNS the empty-denominator result and MUST be chosen explicitly by
    the caller per its business scope (no hidden default lie):
      * 0.0   -> nothing-of-nothing rendered as 0% (default, e.g. per-entity checklist).
      * 100.0 -> vacuously complete: no eligible items outstanding (e.g. fleet-wide
                 completeness where "0 records to fix" == fully compliant).
      * None  -> UNKNOWN (empty set is not a meaningful percent).
    Guards divide-by-zero; numerator floored at 0; result clamped to [0,100]."""
    if not total or int(total) <= 0:
        return empty
    pct = 100.0 * (max(0, int(completed)) / int(total))
    return round(max(0.0, min(100.0, pct)), ndigits)


def checklist_percent_from_flags(
    flags: Iterable[bool], *, ndigits: int = 1, empty: Optional[float] = 0.0,
) -> Optional[float]:
    """PC-CHECKLIST convenience: ratio of truthy flags to total flags."""
    flags = list(flags)
    return checklist_percent(sum(1 for f in flags if f), len(flags), ndigits=ndigits, empty=empty)


SCHEDULE_MODE_MAX = "max"
SCHEDULE_MODE_MEAN = "mean"
SCHEDULE_MODES = (SCHEDULE_MODE_MAX, SCHEDULE_MODE_MEAN)


def schedule_rollup_percent(values: Sequence, *, agg: str, ndigits: int = 2) -> float:
    """PC-SCHEDULE: aggregate approved_percent_complete across schedule rows.

    The caller MUST pass an explicit governed `agg` mode (no anonymous default):
      * SCHEDULE_MODE_MAX  ("max")  -> "current approved reading" = highest reading
                                        (activity/line current progress from candidate rows).
      * SCHEDULE_MODE_MEAN ("mean") -> unweighted average progress across the scope's rows
                                        (e.g. work-package activity average).
    A WEIGHTED rollup (EVM physical %) is a DIFFERENT governed concept owned by
    project_earned_value_engine._weighted_average and is intentionally NOT expressed here.
    Each input is clamped via PC-STORED semantics (missing treated as 0 in a rollup).
    Empty set -> 0.0. Rounded to `ndigits`."""
    if agg not in SCHEDULE_MODES:
        raise ValueError(
            "schedule_rollup_percent requires an explicit governed agg mode "
            f"({SCHEDULE_MODES}); got {agg!r}"
        )
    nums = [clamp_stored_percent(v, missing=0.0) or 0.0 for v in values]
    if not nums:
        return 0.0
    if agg == SCHEDULE_MODE_MEAN:
        return round(sum(nums) / len(nums), ndigits)
    return round(max(nums), ndigits)


COMPLIANCE_STATE_OK = "OK"
COMPLIANCE_STATE_NA = "NOT_APPLICABLE"
COMPLIANCE_STATE_UNKNOWN = "UNKNOWN"


def compliance_rate(compliant, eligible, *, ndigits: int = 0):
    """KPI-COMPLIANCE-RATE — governed zero-denominator semantics. Returns (value, state):
      * eligible None / non-numeric (population cannot be determined) -> (None, 'UNKNOWN').
      * eligible <= 0 (no applicable population)                       -> (None, 'NOT_APPLICABLE').
      * eligible  > 0  -> (round(100*compliant/eligible), 'OK'); a legitimate zero compliant
        count yields 0% (NOT N/A). Numeric typing preserved: value is a number or None
        (never the string 'N/A')."""
    if eligible is None:
        return None, COMPLIANCE_STATE_UNKNOWN
    try:
        e = int(eligible)
    except (TypeError, ValueError):
        return None, COMPLIANCE_STATE_UNKNOWN
    if e <= 0:
        return None, COMPLIANCE_STATE_NA
    val = round(100.0 * (max(0, int(compliant)) / e), ndigits)
    return (int(val) if ndigits == 0 else val), COMPLIANCE_STATE_OK



def quantity_progress_percent(
    numerator_qty, denominator_qty, *, ndigits: int = 2, empty: float = 0.0, clamp_max: Optional[float] = None,
) -> float:
    """PC-COST-QUANTITY: 100 * installed_or_actual_quantity / authorized_or_planned_quantity.

    This is the QUANTITY-based cost/progress concept (installed qty / authorized qty, or
    actual qty / planned qty). It is DISTINCT from PC-CHECKLIST and PC-SCHEDULE:
      * Cost/quantity progress MAY legitimately exceed 100% (overrun), so there is NO
        [0,100] clamp by default (clamp_max=None). Pass clamp_max=100.0 only if a caller's
        business rule explicitly caps it.
      * Zero / negative / missing denominator (no authorized quantity / no plan) -> `empty`
        (governed, default 0.0 — "no authorized scope yet" == 0% installed).
    `authorized_quantity` is expected to already reflect approved change orders (original +
    approved COs); this function does not re-derive change-order math. Rounded to `ndigits`."""
    den = _to_float(denominator_qty, 0.0) or 0.0
    if den <= 0:
        return empty
    pct = 100.0 * ((_to_float(numerator_qty, 0.0) or 0.0) / den)
    if clamp_max is not None:
        pct = min(pct, clamp_max)
    return round(pct, ndigits)


def utilization_percent(
    used, available, *, ndigits: int = 1, empty: Optional[float] = 0.0, clamp_max: Optional[float] = 100.0,
) -> Optional[float]:
    """KPI-UTILIZATION: 100 * used / available.

    Covers capacity-style utilization where `used` is a subset of `available`:
      * equipment run utilization  -> run_hours / (run_hours + idle_hours)
      * storage capacity           -> used_bytes / total_bytes
    Capacity-bounded, so clamped to `clamp_max` (default 100.0 — you cannot exceed 100%
    of available capacity). Zero / negative / missing `available` -> `empty` (governed,
    default 0.0 == "no available capacity/time observed -> 0% utilized"; pass empty=None
    for UNKNOWN when no observation should read as no-data rather than zero).
    NOTE: distinct utilization CONCEPTS (equipment vs storage vs fleet-status vs labor)
    are NOT interchangeable — each concept keeps its own governed caller/denominator; this
    helper only unifies the used/available ratio MATH + zero-denominator + clamp rules."""
    den = _to_float(available, 0.0) or 0.0
    if den <= 0:
        return empty
    pct = 100.0 * ((_to_float(used, 0.0) or 0.0) / den)
    if clamp_max is not None:
        pct = min(pct, clamp_max)
    return round(pct, ndigits)
