# TRACK 19.45B · Corporate Intelligence Score Model

Corporate Intelligence uses a **weighted rollup** on top of the universal
0-100 Operational Intelligence Score (Track 19.41). Every domain feeds
its own score in through a fixed weight table.

## Weight table (`CORPORATE_WEIGHTS`)
| Domain | Weight | Rationale |
|---|---:|---|
| `safety_morning_digest` | 20 | Safety carries top weight — life & OSHA exposure. |
| `project_intelligence` | 20 | Projects are the company's product. |
| `fleet_intelligence` | 12 | Fleet drives daily productivity. |
| `shop_intelligence` | 10 | Repair capacity gates fleet availability. |
| `transportation_intelligence` | 10 | DOT + driver risk. |
| `hr_intelligence` | 8 | Workforce currency. |
| `training_intelligence` | 8 | Certification exposure. |
| `po_weekly_digest` | 7 | Procurement throughput. |
| `executive_operations_brief` | 5 | Cross-check / context. |
| **Total** | **100** | |

## Formula
```
Let S = set of domains with confidence != insufficient_data
Let W_i = weight of domain i (from table above)
Let s_i = overall_score of domain i (0..100)

corporate_score = round( Σ (s_i × W_i)  /  Σ W_i )   for i in S
```

If `Σ W_i == 0` (every domain insufficient_data) → corporate emits
`insufficient_data` and refuses to score.

## Contributor overlay
On top of the weighted rollup, a small contributor pass runs so the
score section can list positive and negative drivers:

### Positive contributors
| Key | Trigger | Impact |
|---|---|---|
| `strong_domain` | Highest-scored domain ≥ 85 | +6 |
| `all_domains_healthy` | No scored domain < 65 | +10 |

### Negative contributors
| Key | Trigger | Impact |
|---|---|---|
| `high_crit_domains` | ≥1 scored domain < 65 | -min(30, count × 8) |
| `lowest_domain_critical` | Lowest scored domain < 40 | -15 |

The contributor overlay is displayed in the score card. The `overall_score`
returned to the executive summary is the **weighted rollup value**, not
the contributor-modified value — this keeps the corporate score honest
against the underlying domain average (contributors are shown for
transparency but do not override the arithmetic).

## Attention level
Universal thresholds (Track 19.41):
- ≥85 → LOW
- 65–84 → MEDIUM
- 40–64 → HIGH
- <40 → CRITICAL

## Confidence
- `high` when ≥6 domains scored.
- `medium` when 1–5 domains scored.
- `insufficient_data` when 0 domains scored.

## Trend
Uses the universal engine trend model. Engages once monthly history
rows accumulate.
