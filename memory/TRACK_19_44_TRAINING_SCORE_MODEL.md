# TRACK 19.44 · Training Intelligence Score Model

## Positive contributors

| Key | Trigger | Impact |
|---|---|---|
| `completion_activity` | Completions > 0 in period | +8 |
| `no_expired` | Active employees > 0 · no expired | +15 |
| `meeting_attendance` | Meetings > 0 in period | +6 |

## Negative contributors

| Key | Trigger | Impact |
|---|---|---|
| `expired_certs` | Expired count > 0 | `-min(35, count*8)` |
| `expiring_30d` | Expiring in 30d > 0 | `-min(20, count*3)` |
| `expiring_60d` | Expiring in 60d > 0 (only if 30d = 0) | `-min(10, count*2)` |
| `missing_records` | Missing/pending records > 0 | `-min(15, count*3)` |
| `approval_backlog` | Pending approvals > 5 | `-min(12, count/2)` |

## Confidence

- `insufficient_data` when no training signals populated.
- `medium` when signals present but active employees < 20 or total records < 10.
- `high` when active employees ≥ 20 AND total records ≥ 10.

## No-auto-decision

Platform does NOT determine discipline · employment eligibility · OSHA recordability · legal compliance. Every contributor labels a signal, never a decision.
