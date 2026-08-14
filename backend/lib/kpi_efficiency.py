"""WAVE 5 — Canonical EFFICIENCY-PERCENT authority (KPI-EFFICIENCY-PERCENT).

Efficiency percent is NOT one concept. The governed distinct concepts are:

  RATE_EFFICIENCY   = actual_rate / target_rate * 100
      (production efficiency: how fast we actually produced vs the budget rate)
  RESOURCE_EFFICIENCY = earned_budget / consumed_actual * 100
      (labor efficiency: budgeted-hours-earned-for-work-done vs actual hours burned;
       >100 = beat the budget, <100 = over-burned)
  OUTPUT_RATIO      = actual_output / planned_output * 100
      (crew/production ratio of quantities — a progress-style ratio, distinct from rate)

These MUST NOT be forced into one equation; the numerator/denominator differ.
This module supplies ONE governed calculator so every consumer of the SAME concept
at the SAME scope gets the SAME number with the SAME zero/unknown handling.

ZERO / UNKNOWN DENOMINATOR (explicit governed modes):
  - mode="zero" (legacy OPPC PM-workspace convention): denom<=0 -> 0.0. Kept for the
    internal execution workspace whose consumers render numeric floats. 0.0 here means
    "no measurable efficiency yet" in that governed operational surface.
  - mode="unknown": denom<=0 -> None (a percentage is genuinely undefined with no
    consumed resource / no target). Use for any surface that can render UNKNOWN/"—".

100 semantics: 100% = exactly on budget. >100 is LEGITIMATE (beat budget / over-produced)
and must NOT be clamped. Negative inputs are not expected; treated as their float value.
"""
from __future__ import annotations

from typing import Optional


def efficiency_percent(
    numerator: Optional[float],
    denominator: Optional[float],
    *,
    mode: str = "zero",
    ndigits: int = 2,
) -> Optional[float]:
    """Canonical efficiency = numerator/denominator*100. Not clamped at 100."""
    try:
        n = float(numerator) if numerator is not None else None
        d = float(denominator) if denominator is not None else None
    except (TypeError, ValueError):
        return None
    if n is None or d is None:
        return None
    if d <= 0:
        return 0.0 if mode == "zero" else None
    return round((n / d) * 100.0, ndigits)


__all__ = ["efficiency_percent"]
