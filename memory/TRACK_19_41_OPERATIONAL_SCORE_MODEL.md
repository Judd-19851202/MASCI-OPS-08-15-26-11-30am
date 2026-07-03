# TRACK 19.41 · Operational Intelligence Score Model

**Status:** 🟢 LOCKED · single source of truth for every product score.

Module: `/app/backend/operational_intelligence/score_model.py`.

## Score contract

| Field | Type | Rules |
|---|---|---|
| `overall_score` | int 0–100 | Clamped. Never negative. |
| `attention_level` | `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` | Derived from score bands: ≥85 LOW · ≥65 MEDIUM · ≥40 HIGH · <40 CRITICAL. |
| `trend_direction` | `▲` / `▼` / `→` | Derived from `trend_percent` if provided. |
| `trend_percent` | Optional[float] | `None` when insufficient history exists (never fabricated). |
| `confidence` | `high`/`medium`/`low`/`insufficient_data` | Must be explicit. |
| `data_freshness` | str | Human-readable ("live", "2h", "1d", "insufficient_data"). |
| `top_positive_contributors` | list[Contributor] (0–5) | Positive movers with `impact ≥ 0`. |
| `top_negative_contributors` | list[Contributor] (0–5) | Negative movers with `impact < 0`. |
| `calculation_notes` | str | One-paragraph explanation of how the score was computed. |
| `generated_at` | ISO8601 UTC | Auto-populated if omitted. |

## Attention level bands

| Band | Range | Meaning |
|---|---|---|
| LOW | 85–100 | Green · nothing needs escalation |
| MEDIUM | 65–84 | Amber · monitor |
| HIGH | 40–64 | Orange · requires action this week |
| CRITICAL | 0–39 | Red · immediate attention required · **also the default when data is insufficient** |

## Golden rules

1. **Never fake confidence.** If the product can't compute a score with the data it has, call `insufficient_data_score()` — do NOT emit a 100.
2. **Never fake freshness.** Emit `"insufficient_data"` rather than `"live"` when the underlying data source is stale.
3. **Never divide by zero.** Trend math (`engine.compute_trend`) already handles prev=0 · curr=0 · missing values.
4. **Never score missing data as healthy.** `insufficient_data_score()` returns `overall_score=0` and `attention_level=CRITICAL`.
5. **Every score must list its contributors.** No silent black-box scoring.
6. **Deterministic.** Same inputs → same outputs. No randomness. No time-of-day drift beyond the timestamp.

## Helpers

```python
from operational_intelligence import (
    OperationalIntelligenceScore, Contributor,
    score_from_contributors, insufficient_data_score,
    ATTENTION_LOW, ATTENTION_MEDIUM, ATTENTION_HIGH, ATTENTION_CRITICAL,
    attention_from_score,
)

# Insufficient data
score = insufficient_data_score("PO history not yet populated")

# Contributor-driven score
score = score_from_contributors(
    baseline=100,
    positives=[Contributor(key="clean_slate", label="No open POs", impact=15)],
    negatives=[Contributor(key="overdue_capa", label="4 overdue CAPAs", impact=-25)],
    trend_percent=-8.0,
    confidence="high",
    data_freshness="live",
    calculation_notes="Composite of open volume and overdue CAPA count.",
)
```

## Lock test coverage

- Attention bands (5 assertions across score ranges).
- `insufficient_data_score()` is CRITICAL, score=0, no fabricated freshness/confidence.
- Clamp guarantees (positives cannot push above 100; negatives cannot drive below 0).
- Trend arrow derivation from `trend_percent` (up · down · flat · None).
- `to_dict()` produces all 10 required keys.

## Product adoption

- ✅ `po_weekly_digest` — uses `score_from_contributors` with dynamic contributors.
- 🟡 `safety_morning_digest` — Track 19.42 will retrofit the Score model onto its digest object without changing 19.39 payload shape.
- 🟡 `executive_operations_brief` — Track 19.42 retrofit.
- ❌ 8 contract-registered products — will emit `insufficient_data_score()` from their aggregators when they land.
