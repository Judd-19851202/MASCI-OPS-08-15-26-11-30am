# TRACK 19.44 · Project Intelligence Score Model

## Positive contributors

| Key | Trigger | Impact |
|---|---|---|
| `strong_daily_report_coverage` | Reports 7d ≥ active_projects × 3 | +10 |
| `photo_activity` | Photos 7d > 0 | +5 |
| `no_incidents` | 0 project incidents (7d) · active projects > 0 | +10 |
| `no_high_attention` | 0 HIGH-attention cases | +8 |

## Negative contributors

| Key | Trigger | Impact |
|---|---|---|
| `high_attention_project_cases` | HIGH cases > 0 | `-min(30, count*10)` |
| `missing_reports` | Missing/overdue DRs > 0 | `-min(20, count*3)` |
| `aging_constraints` | Constraints open > 30 days > 0 | `-min(15, count*3)` |
| `constraint_load` | Open constraints > 5 (when no aging) | `-min(10, count/2)` |
| `po_bottleneck` | Portfolio open POs > 30 · active projects > 0 | `-min(15, count/10)` |
| `project_incidents` | Project incidents (7d) > 0 | `-min(20, count*6)` |

## Confidence

- `insufficient_data` when no project signals populated.
- `medium` when signals present but active projects < 5 or reports < 5.
- `high` when active projects ≥ 5 AND reports ≥ 5.

## No-auto-decision

Platform does NOT declare projects on-time or off-track · assign blame · determine fault · infer financial overrun. Every contributor labels a signal.
