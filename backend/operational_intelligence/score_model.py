"""Operational Intelligence Score model — the ONE universal score
used by every intelligence product.

Range: 0–100.
Attention levels: LOW · MEDIUM · HIGH · CRITICAL.
Trend arrows: ▲ up (improving OR worsening depending on metric semantics) ·
▼ down · → flat.

Design rules
------------
- Never fake confidence or freshness.
- Never divide by zero.
- Never score missing data as healthy — emit "insufficient_data".
- Every score MUST list its top positive and top negative contributors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


ATTENTION_LOW = "LOW"
ATTENTION_MEDIUM = "MEDIUM"
ATTENTION_HIGH = "HIGH"
ATTENTION_CRITICAL = "CRITICAL"

ATTENTION_LEVELS = (ATTENTION_LOW, ATTENTION_MEDIUM,
                    ATTENTION_HIGH, ATTENTION_CRITICAL)


def attention_from_score(score: int) -> str:
    """Map 0–100 score → attention level. Clamp out-of-range values."""
    s = max(0, min(100, int(score or 0)))
    if s >= 85:
        return ATTENTION_LOW
    if s >= 65:
        return ATTENTION_MEDIUM
    if s >= 40:
        return ATTENTION_HIGH
    return ATTENTION_CRITICAL


@dataclass
class Contributor:
    key: str
    label: str
    impact: int   # signed; -N drags the score down · +N pulls it up
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "label": self.label,
                "impact": int(self.impact), "detail": self.detail}


@dataclass
class OperationalIntelligenceScore:
    overall_score: int                  # 0..100
    attention_level: str                # LOW|MEDIUM|HIGH|CRITICAL
    trend_direction: str                # "▲" | "▼" | "→"
    trend_percent: Optional[float]      # None when insufficient data
    confidence: str                     # "high" | "medium" | "low" | "insufficient_data"
    data_freshness: str                 # e.g. "2h" · "1d" · "insufficient_data"
    top_positive_contributors: List[Contributor] = field(default_factory=list)
    top_negative_contributors: List[Contributor] = field(default_factory=list)
    calculation_notes: str = ""
    generated_at: str = ""

    def __post_init__(self):
        # Clamp + defensive defaults · never let the model emit garbage.
        self.overall_score = max(0, min(100, int(self.overall_score or 0)))
        if self.attention_level not in ATTENTION_LEVELS:
            self.attention_level = attention_from_score(self.overall_score)
        if self.trend_direction not in ("▲", "▼", "→"):
            self.trend_direction = "→"
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "attention_level": self.attention_level,
            "trend_direction": self.trend_direction,
            "trend_percent": self.trend_percent,
            "confidence": self.confidence,
            "data_freshness": self.data_freshness,
            "top_positive_contributors":
                [c.to_dict() for c in self.top_positive_contributors[:5]],
            "top_negative_contributors":
                [c.to_dict() for c in self.top_negative_contributors[:5]],
            "calculation_notes": self.calculation_notes,
            "generated_at": self.generated_at,
        }


def insufficient_data_score(notes: str = "") -> OperationalIntelligenceScore:
    """Canonical 'insufficient data' score — never scored as healthy."""
    return OperationalIntelligenceScore(
        overall_score=0,
        attention_level=ATTENTION_CRITICAL,
        trend_direction="→",
        trend_percent=None,
        confidence="insufficient_data",
        data_freshness="insufficient_data",
        calculation_notes=notes or (
            "Insufficient data to compute an Operational Intelligence Score. "
            "Attention level defaulted to CRITICAL — never score missing data as healthy."
        ),
    )


def score_from_contributors(
    *,
    baseline: int = 100,
    positives: Optional[List[Contributor]] = None,
    negatives: Optional[List[Contributor]] = None,
    trend_percent: Optional[float] = None,
    confidence: str = "medium",
    data_freshness: str = "",
    calculation_notes: str = "",
) -> OperationalIntelligenceScore:
    """Deterministic contributor → score reducer.

    baseline + sum(positives.impact) - sum(abs(negatives.impact)) clamped
    to 0..100. Trend direction is derived from trend_percent (None →
    stable arrow but insufficient_data trend_percent).
    """
    positives = positives or []
    negatives = negatives or []
    raw = int(baseline)
    for c in positives:
        raw += max(0, int(c.impact))
    for c in negatives:
        raw -= abs(int(c.impact))
    score = max(0, min(100, raw))

    if trend_percent is None:
        arrow = "→"
    elif trend_percent > 0.5:
        arrow = "▲"
    elif trend_percent < -0.5:
        arrow = "▼"
    else:
        arrow = "→"

    return OperationalIntelligenceScore(
        overall_score=score,
        attention_level=attention_from_score(score),
        trend_direction=arrow,
        trend_percent=trend_percent,
        confidence=confidence,
        data_freshness=data_freshness or "unknown",
        top_positive_contributors=sorted(positives, key=lambda c: -c.impact)[:5],
        top_negative_contributors=sorted(negatives, key=lambda c: c.impact)[:5],
        calculation_notes=calculation_notes,
    )


__all__ = [
    "ATTENTION_LOW", "ATTENTION_MEDIUM", "ATTENTION_HIGH", "ATTENTION_CRITICAL",
    "ATTENTION_LEVELS",
    "attention_from_score",
    "Contributor", "OperationalIntelligenceScore",
    "insufficient_data_score", "score_from_contributors",
]
