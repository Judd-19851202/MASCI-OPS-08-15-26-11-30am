"""WAVE 5 — Canonical VARIANCE-PERCENT authority (KPI-VARIANCE-PERCENT).

One governed owner for percentage variance so that the SAME variance concept
at the SAME scope produces the SAME number, with an EXPLICIT, provable sign
convention and favorable/unfavorable interpretation per concept.

SIGN CONVENTION (canonical, single source of truth):
    variance_percent = (actual - baseline) / baseline * 100
  => POSITIVE means actual EXCEEDS baseline; NEGATIVE means actual is BELOW baseline.
  This is a mathematical fact about the number. Whether "above baseline" is GOOD
  or BAD depends on the concept and is governed separately by ``variance_favorable``.

ZERO / UNKNOWN BASELINE (explicit governed modes — never silently pick one):
  - mode="honest_unknown" (financial / payroll truth): baseline<=0 -> None (UNKNOWN;
      a variance percentage is genuinely undefined with no baseline). Used where the
      surface renders "—"/UNKNOWN for a missing denominator (payroll variance).
  - mode="unplanned_is_full" (planning/production): baseline<=0 -> 0.0 when actual<=0
      (nothing planned, nothing done = no variance) else 100.0 (everything done was
      unplanned = 100% over plan). This preserves the governed operational meaning used
      by the OPPC variance-intelligence engine.

FAVORABLE / UNFAVORABLE (per concept — NO generic "positive=green"):
  Governed by concept semantics. Cost/labor/spend OVER baseline is UNFAVORABLE;
  production/quantity/schedule-progress OVER baseline is FAVORABLE; schedule-slip
  (duration/days over baseline) is UNFAVORABLE. Zero variance is NEUTRAL.
"""
from __future__ import annotations

from typing import Optional

# Concepts where a POSITIVE variance (actual above baseline) is FAVORABLE (good).
_POSITIVE_IS_FAVORABLE = {
    "production",   # produced more than planned
    "quantity",     # installed more than planned
    "crew_productivity",
    "productivity",  # efficiency above 100 baseline
    "earned_value",
}
# Concepts where a POSITIVE variance (actual above baseline) is UNFAVORABLE (bad).
_POSITIVE_IS_UNFAVORABLE = {
    "cost",
    "labor",        # more labor hours than budgeted
    "payroll",
    "schedule",     # more days/duration than baseline = slip
    "duration",
    "forecast_overrun",
    "spend",
}


def variance_percent(
    actual: Optional[float],
    baseline: Optional[float],
    *,
    mode: str = "honest_unknown",
    ndigits: int = 2,
) -> Optional[float]:
    """Canonical variance percentage. See module docstring for modes/sign."""
    try:
        a = float(actual) if actual is not None else None
        b = float(baseline) if baseline is not None else None
    except (TypeError, ValueError):
        return None
    if a is None or b is None:
        return None
    if b <= 0:
        if mode == "unplanned_is_full":
            return 0.0 if a <= 0 else 100.0
        # honest_unknown
        return None
    return round(((a - b) / b) * 100.0, ndigits)


def variance_favorable(concept: str, variance_pct: Optional[float]) -> str:
    """Return 'favorable' | 'unfavorable' | 'neutral' | 'unknown' for the given
    concept. Never assume positive=good. UI color MUST derive from this, not sign."""
    if variance_pct is None:
        return "unknown"
    key = (concept or "").strip().lower()
    if abs(variance_pct) < 1e-9:
        return "neutral"
    positive = variance_pct > 0
    if key in _POSITIVE_IS_FAVORABLE:
        return "favorable" if positive else "unfavorable"
    if key in _POSITIVE_IS_UNFAVORABLE:
        return "unfavorable" if positive else "favorable"
    return "unknown"


__all__ = ["variance_percent", "variance_favorable"]
