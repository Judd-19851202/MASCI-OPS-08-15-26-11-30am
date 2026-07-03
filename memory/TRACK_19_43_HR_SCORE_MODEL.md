# TRACK 19.43 · HR Intelligence Score Model

## Positive contributors

| Key | Trigger | Impact |
|---|---|---|
| `all_current` | Active employees > 0 · no expired quals | +15 |
| `training_activity` | Training activities in the period > 0 | +6 |
| `net_growth` | New hires > 0 · exits = 0 | +5 |

## Negative contributors

| Key | Trigger | Impact |
|---|---|---|
| `expired_quals` | Expired qualifications > 0 | `-min(35, count*8)` |
| `expiring_30d` | Qualifications expiring in 30d > 0 | `-min(15, count*2)` |
| `net_churn` | Exits > new hires + 1 | -8 |

## Confidence

- `insufficient_data` when no HR signals populated.
- `medium` when signals present but active employee count < 20.
- `high` when active employees ≥ 20.

## No-auto-decision

HR + Safety own investigation, classification, and disposition. Platform does NOT determine:
- termination cause
- discipline
- performance rating
- eligibility for rehire
- legal liability

Every contributor labels a signal — never a decision.
