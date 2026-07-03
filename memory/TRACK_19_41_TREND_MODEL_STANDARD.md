# TRACK 19.41 · Trend Model Standardization

**Status:** 🟢 LOCKED.

## Single trend engine

- Module: `/app/backend/operational_intelligence/engine.py::compute_trend`.
- **No** product may implement its own trend math.
- **No** duplicate trend helper allowed.

## Contract

```python
compute_trend(current: float, previous: float) -> {
    "current":     float,
    "previous":    float,
    "delta":       float,       # current - previous
    "pct_change":  Optional[float],  # None when both = 0
    "arrow":       "▲" | "▼" | "→",
    "tone":        "up" | "down" | "flat",
}
```

## Edge cases (all locked by test)

| Case | Input | Output |
|---|---|---|
| Increase | current=120, previous=100 | ▲ · +20 · +20.0% |
| Decrease | current=80, previous=100 | ▼ · -20 · -20.0% |
| Stable | current=50, previous=50 | → · 0 · 0.0% |
| prev=0 · curr>0 | current=5, previous=0 | ▲ · +5 · 100.0% |
| prev=0 · curr=0 | current=0, previous=0 | → · 0 · **None** |
| None-safe | current=None, previous=None | → · 0 · None |

## Metric semantics (owner-defined, not platform-defined)

The trend engine is **direction-agnostic**. Whether an ▲ is *good* or
*bad* depends on the metric owner:

| Metric | ▲ meaning |
|---|---|
| Open high-attention cases | ❌ Bad |
| Overdue CAPAs | ❌ Bad |
| Open POs | ❌ Bad |
| Training completion % | ✅ Good |
| Fleet availability | ✅ Good |
| Days-since-recordable | ✅ Good |
| Executive readiness % | ✅ Good |

Products encode this semantic by:
- placing the metric in either `top_wins` (good movement) or `needs_immediate_attention` (bad movement),
- setting the Score `Contributor.impact` sign (positive = good · negative = bad),
- letting the Trend section render the raw arrow (context comes from placement).

The trend engine itself remains context-free. This is intentional — one engine, one truth.

## Insufficient-data state

When the prior period is empty (first-run rollout of a product), `pct_change=None`. The renderer displays "—" instead of a fake percent. The Score model surfaces `confidence="insufficient_data"` alongside.

## Adoption

- ✅ `executive_operations_brief` — trend engine ready (currently seeded on portfolio counts).
- ✅ `po_weekly_digest` — trend engaged from Track 19.42 onward (once history rows accumulate).
- ✅ `safety_morning_digest` — trend engine referenced via 19.38 aggregator.
- ❌ 8 contract-registered products — will consume `compute_trend` when their aggregators land.

## Lock test coverage

- Track 19.40 lock test: `test_trend_up_down_flat` · `test_trend_division_by_zero_edge_cases`.
- Track 19.41 lock test: `test_trend_arrow_derived_from_percent`.
