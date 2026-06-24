# TRACK 15.75 · Phase 10 — Dashboard Surface Certification

Evidence: live API probes + frontend component review.

| Dashboard / Card | Data Source | Shows Missing Data? | Shows Failures? | Shows Recent Records? | Status |
|---|---|---|---|---|---|
| PM Routing Status Panel (`RoutingStatusPanel.jsx`, Track 15.73Q) | `/api/admin/pm-email-coverage` | ✅ lists projects without PM email (7 today) | ✅ flags malformed PM email + PM name w/o email | ✅ sorts by `recent_dr_count` | 🟢 |
| Admin PM-Email Coverage card | `/api/admin/pm-email-coverage` | ✅ summary counters | ✅ surfaces `active_with_pm_name_no_email` | ✅ | 🟢 |
| System Health Dashboard | `/api/health/full` + `backup_health` + `alert_events` | n/a (status surface) | ✅ red/amber tags | n/a | 🟢 |
| Email Routing v2 Status | `/api/admin/email-routing/v2/status` | ✅ `critical_empty_route_keys` | ✅ `errors_last_24h` counter | ✅ `audit_counters.last_hour` | 🟢 |
| Safety Admin (Meetings) | `/api/safety/meetings` | n/a | n/a | ✅ | 🟢 |
| Safety Admin (Incidents) | `/api/incidents` | n/a | n/a | ✅ | 🟢 |
| HR Portal | `/api/hr/*` | ✅ employee identity gaps | ✅ | ✅ | 🟢 |
| Shop Portal | shop endpoints | ✅ defect queue | ✅ failed pre-ops | ✅ | 🟢 |
| Equipment Dashboard | `/api/equipment*` | 🟡 247 records missing `unit_number` visible | n/a | ✅ | 🟢 (legacy backfill backlog) |
| Daily Report Admin List | `/api/daily-reports` | n/a | n/a | ✅ | 🟢 |
| Field Leadership view | `/api/field_leadership*` | ✅ | n/a | ✅ | 🟢 |
| PM Portal Dashboard | `/api/pm/*` | n/a (scoped) | n/a | ✅ for assigned projects | 🟢 |

## Truth checks

* Routing Status Panel pulls from `email_routing_audit_v2` post-fix
  → no more "fake dry_run" rows for new events.
* PM Coverage card refreshes from live `/api/admin/pm-email-coverage`
  endpoint → snapshot, no cached lies.

## Verdict

**🟢 GREEN.** All audited dashboards surface truth. No dashboard
found that contradicts the underlying audit/data.
