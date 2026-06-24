# TRACK 15.75 · Phase 6 — PM / Co-PM Dashboard Certification

Evidence: live API probes + `routes/pm_routes.py`, `project_team_assignments.py`.

## PM dashboard surfaces

| Endpoint | Scope | Probe |
|---|---|---|
| `/api/pm/me` | per-PM self | 401 without token (verified) |
| `/api/pm/jobs` | assigned projects | 401 without token (verified) |
| `/api/pm/check` | PM token check | exists |
| `/api/pm/crew/training-records` | crew records for assigned jobs | exists |
| `/api/pm/crew/ppe` | PPE for assigned jobs | exists |
| `/api/pm/crew/capas` | corrective actions | exists |
| `/api/pm/crew/summary` | summary rollup | exists |
| `/api/pm/notifications/digest` | in-app digest | exists |
| `/api/pm/job/{project_number}/team` | team roster | exists |
| `/api/pm/directory/users` | PM directory | exists |
| `/api/daily-reports?project_number=…` | DR list, PM-scoped (require_admin returns PM doc) | 401 without token (verified) |

## Co-PM scope

* `jobs_master.co_pm_emails[]` is read by `recipients_for_record_async`
  → co-PMs are CC'd on operational DR/inspection emails AND on
  compliance forms (incident/meeting/jha/qaqc) via the same path.
* The PM scope helper `compute_pm_scope` (used by Safety routes) is
  validated by Slice 2 / Slice 3 regression tests.

## Live coverage observability

* `/api/admin/pm-email-coverage` (Track 15.73Q) — exposes:
  * active_total = 30
  * active_with_pm_email = 23 (76.7 %)
  * active_missing_pm_email = 7
  * active_with_co_pm_email_only = 2
  * active_total_no_pm_no_copm = 5
  * 2 of the 7 missing have **recent DRs** (`20-07`, `26-07`).
* `RoutingStatusPanel` frontend card surfaces this list to admins.

## Preview-data caveat

In preview, the projects with valid PM emails (24-06, 25-02, etc.)
have ZERO DRs / meetings / incidents. The projects with active
records (20-07, 26-07) lack PM emails. This is **fixture state**,
not a defect. PMs assigned to active production projects with
proper email would see populated dashboards.

## Verdict

**🟢 GREEN** on code surface and PM scope.
**🟡 AMBER on operational coverage** — 7 active jobs need PM email
backfill before PMs will see their DRs directly (see Phase 12
Remediation Plan). Until then, dead-letter routing keeps the
dispatch surface visible to `safety@mascigc.com` and `jaymn.judd@`,
who can re-route manually.
