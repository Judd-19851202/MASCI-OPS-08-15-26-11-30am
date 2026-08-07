# WP18C9 Portfolio Data Contract

Date: 2026-08-07  
Status: PASS

## Snapshot Identity
- Collection: `portfolio_intelligence_snapshots`
- Key: `scope_key`
- Schema version: `WP18C9/v1`
- Cache role: bounded delivery surface only
- Fresh-cache TTL: 10 minutes

## Top-Level Response Shape
| Field | Type | Meaning |
|---|---|---|
| `snapshot_id` | string | Portfolio update identifier |
| `scope_key` | string | Global or scoped actor view key |
| `audience` | string | `executive` or `pm` |
| `generated_at` | ISO datetime | When the portfolio view was last assembled |
| `scope` | object | Mode, project count, visible project numbers |
| `portfolio_summary` | object | Rollups for counts, financials, schedule, commitments, constraints, production, resource pressure, freshness |
| `projects` | array | Per-project explainable portfolio cards with drill-back paths |
| `change_report` | object | Published changes and attention movement |
| `comparability_standard` | object | Rules for mathematically valid aggregation |
| `decision_rules` | array | Deterministic attention rules |
| `blocked_dependencies` | object | C9-specific blocker count and items |
| `refresh_errors` | array | Isolated project refresh failures, if any |
| `performance_profile` | object | Query, refresh, build timings |
| `cache_status` | string | `reused`, `rebuilt`, or `stale_last_good` |

## Per-Project Contract
Each `projects[]` row contains:
- project identifiers and operator-safe labels
- `priority_band` and `priority_label`
- `why_it_matters`
- `recommended_action`
- `change_summary`
- `freshness` across project performance, forecast, and Earned Value
- `financial`, `cost_forecast`, `schedule`, `commitments`, `constraints`, `production`, `resource_pressure`
- drill-back paths into project pages
- supporting-record timestamps for project performance, forecast, and Earned Value

## Truth Rules in the Contract
1. Portfolio financial rollups are aggregate-money rollups only.
2. PM responses are scope-filtered before delivery.
3. Refresh reuses existing upstream services and preserves last-good delivery if a refresh fails.
4. Older or missing project updates remain visible as insufficient evidence.
