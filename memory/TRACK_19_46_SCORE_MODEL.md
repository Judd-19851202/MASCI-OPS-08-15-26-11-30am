# TRACK 19.46 · Weekly Operations Score Model

Weekly Operations uses the universal 0-100 Operational Intelligence
Score model (Track 19.41) with a WoW-delta-first contributor mix.

## Baseline
`baseline = round(mean(current domain scores))`

If no domain has a real score, the aggregator emits
`insufficient_data` (never scored as healthy).

## Positive contributors
| Key | Trigger | Impact |
|---|---|---|
| `domains_improving` | ≥1 domain improved WoW | +min(12, improvers × 3) |
| `no_domains_in_high_or_critical` | 0 domains < 65 | +10 |

## Negative contributors
| Key | Trigger | Impact |
|---|---|---|
| `domains_declining` | ≥1 domain declined WoW | -min(20, decliners × 5) |
| `domains_in_high_or_critical` | ≥1 domain < 65 now | -min(25, high_crit × 8) |

## Trend
- `trend_percent = round(((mean_current - mean_prior) / mean_prior) × 100, 1)`
  computed only across domains that have BOTH a current score and a
  prior history row.
- If no domains have prior history rows, `trend_percent` is `None`
  and the trend arrow renders as `→` (never faked).

## Confidence
- `high` — ≥6 domains scored AND at least one WoW delta computed.
- `medium` — 3–5 domains scored.
- `low` — 1–2 domains scored.
- `insufficient_data` — 0 domains scored.

## Attention level thresholds (universal)
- ≥85 → LOW
- 65–84 → MEDIUM
- 40–64 → HIGH
- <40 → CRITICAL

## Why this math and not a weighted rollup?
Weekly Operations is a **change** report, not a snapshot. Corporate
Intelligence already delivers the weighted snapshot. Weekly Operations
optimises for "what shifted vs last week" — arithmetic mean gives every
domain equal voice in the WoW signal.
