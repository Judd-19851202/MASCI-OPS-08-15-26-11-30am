# QA · Live Performance Audit (iter147)

_Generated 2026-05-15 19:14 UTC_
_Window: last 1h · Source: db.usage_events (iter146 telemetry)_

**Thresholds**:
- Flag if `max_ms > 1000` (worst-case latency)
- Flag if `avg_ms > 250` (sustained slowness)
- Flag if `error_pct > 5.0%`
- Below 10 calls = treated as noise (not flagged)

## Flagged Routes — Priority Order

| Route | Calls | Avg ms | Worst ms | Err% | Reason | Collection Hint | Live max ms |
|---|---|---|---|---|---|---|---|
| `/api/incidents` | 18 | 7 | 74 | 11.1% | err=11.1% | hits `incidents` · profile with scripts/qa_audit.py | — |
| `/api/daily-reports` | 18 | 15 | 109 | 11.1% | err=11.1% | hits `daily_reports` · profile with scripts/qa_audit.py | — |
| `/api/inspections` | 18 | 18 | 113 | 11.1% | err=11.1% | hits `equipment_inspections` · profile with scripts/qa_audit.py | — |
| `/api/meetings` | 18 | 15 | 90 | 11.1% | err=11.1% | — | — |
| `/api/auth/multi-login` | 17 | 135 | 234 | 41.2% | err=41.2% | — | — |
| `/api/jhas` | 12 | 13 | 79 | 16.7% | err=16.7% | — | — |
| `/api/auth/issue-portal-token` | 11 | 2 | 6 | 100.0% | err=100.0% | — | — |

## All Top Routes (by call count)

| Route | Calls | Avg ms | Worst ms | Errors |
|---|---|---|---|---|
| `/api/banners/active` | 133 | 2 | 77 | 0 |
| `/api/incidents` | 18 | 7 | 74 | 2 |
| `/api/daily-reports` | 18 | 15 | 109 | 2 |
| `/api/inspections` | 18 | 18 | 113 | 2 |
| `/api/meetings` | 18 | 15 | 90 | 2 |
| `/api/auth/multi-login` | 17 | 135 | 234 | 7 |
| `/api/version` | 12 | 12 | 47 | 0 |
| `/api/jhas` | 12 | 13 | 79 | 2 |
| `/api/suppliers` | 12 | 31 | 113 | 0 |
| `/api/equipment-types` | 12 | 3 | 12 | 0 |
| `/api/equipment-master` | 12 | 53 | 125 | 0 |
| `/api/employees` | 12 | 24 | 123 | 0 |
| `/api/auth/issue-portal-token` | 11 | 2 | 6 | 11 |
| `/api/master-lookup/equipment/:id/where-used` | 9 | 1 | 4 | 9 |
| `/api/qaqc-inspections` | 6 | 10 | 46 | 0 |
| `/api/trench-boxes` | 6 | 4 | 18 | 0 |
| `/api/job-hazard-plans` | 6 | 6 | 18 | 0 |
| `/api/equipment-inspections` | 6 | 15 | 55 | 0 |
| `/api/integrations/health` | 6 | 28 | 150 | 0 |
| `/api/admin/login` | 6 | 0 | 0 | 0 |
| `/api/field-leadership` | 4 | 50 | 122 | 0 |
| `/api/hr/me` | 4 | 25 | 63 | 0 |
| `/api/job-photos` | 4 | 6 | 18 | 0 |
| `/api/shop/check` | 4 | 56 | 95 | 0 |
| `/api/admin/check` | 4 | 38 | 73 | 0 |
| `/api/pm/check` | 4 | 32 | 95 | 0 |
| `/api/admin/jobs` | 3 | 0 | 2 | 3 |
| `/api/hr/login` | 3 | 224 | 224 | 0 |
| `/api/field-leadership/time-off/stats` | 2 | 2 | 2 | 0 |
| `/api/integrations/motive/events` | 2 | 3 | 5 | 0 |

