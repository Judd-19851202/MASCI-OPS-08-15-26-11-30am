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
                 input; aggregation (max or mean) is chosen by the caller's governed
                 scope. Empty set -> 0.0. Rounded to 2 dp.
                 -> schedule_rollup_percent()

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


def checklist_percent(completed: int, total: int, *, ndigits: int = 1) -> float:
    """PC-CHECKLIST: 100 * completed_eligible / total_eligible.
    Empty denominator -> 0.0. Guards against divide-by-zero and clamps to [0,100]."""
    if not total or total <= 0:
        return 0.0
    pct = 100.0 * (max(0, int(completed)) / int(total))
    return round(max(0.0, min(100.0, pct)), ndigits)


def checklist_percent_from_flags(flags: Iterable[bool], *, ndigits: int = 1) -> float:
    """PC-CHECKLIST convenience: ratio of truthy flags to total flags."""
    flags = list(flags)
    return checklist_percent(sum(1 for f in flags if f), len(flags), ndigits=ndigits)


def schedule_rollup_percent(values: Sequence, *, agg: str = "max", ndigits: int = 2) -> float:
    """PC-SCHEDULE: aggregate approved_percent_complete across schedule rows.
    Each input is clamped via PC-STORED semantics (missing treated as 0 for rollup).
    agg='max' (default) or 'mean'. Empty set -> 0.0."""
    nums = [clamp_stored_percent(v, missing=0.0) or 0.0 for v in values]
    if not nums:
        return 0.0
    if agg == "mean":
        return round(sum(nums) / len(nums), ndigits)
    return round(max(nums), ndigits)
