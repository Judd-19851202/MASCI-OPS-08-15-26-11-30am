# TRACK 19.42 · Transportation Intelligence · Score Model

## Baseline & clamp

- `baseline=100`; score clamped to `[0, 100]`.
- Uses `score_from_contributors(...)` from `operational_intelligence.score_model`.
- Attention bands: ≥85 LOW · ≥65 MEDIUM · ≥40 HIGH · <40 CRITICAL.

## Positive contributors

| Key | Trigger | Impact | Rationale |
|---|---|---|---|
| `dvir_no_defects` | DVIRs submitted last 7d > 0 · zero open defects | +10 | Clean inspection pass |
| `qualifications_current` | Active drivers > 0 · zero expired | +12 | No lapsed credentials |
| `full_availability` | Fleet total > 0 · zero OOS | +10 | Fleet fully available |
| `no_accidents` | Zero vehicle incidents in the period | +8 | Clean-safety period |

## Negative contributors

| Key | Trigger | Impact | Rationale |
|---|---|---|---|
| `expired_qualifications` | Any expired driver qualification | `-min(30, count*8)` | Safety-critical · immediate action |
| `expiring_soon` | Qualifications expiring within 30 days | `-min(15, count*3)` | Renewal window approaching |
| `open_dvir_defects` | DVIRs with `has_open_defects=True` | `-min(20, count*4)` | Open defects raised via inspection |
| `oos_units` | OOS unit count | `-min(25, count*3)` | Weighted by count with cap |
| `vehicle_incidents` | Vehicle-accident case count (7d) | `-min(35, count*12)` | Safety-critical · highest weight |
| `transport_backlog` | Open transportation action items > 5 | `-min(15, count//2)` | Aggregate backlog |

## Confidence policy

- **`insufficient_data`** — no transportation collections populated at all.
- **`medium`** — signals present but data volume < threshold (DVIR ≤10 OR active drivers ≤5).
- **`high`** — DVIR total > 10 AND active drivers > 5.

## Data freshness

- `insufficient_data` when no signals present.
- `live` otherwise.

## Trend

- `trend_percent=None` for the first-run rollout — history rows accumulate from Track 19.42 onward via `engine.write_history`. Real week-over-week trend engages Track 19.43+ once ≥ 2 history rows exist per product.
- Trend arrow currently displays `→ flat` for headline metric.

## No-auto-decision safeguards

- Score surfaces attention. It does **NOT** determine:
  - DOT recordability
  - Preventability
  - Fault
  - Driver discipline
  - Insurance liability
  - CSA basic weighting

Every contributor labels a **signal**, never a **decision**.
