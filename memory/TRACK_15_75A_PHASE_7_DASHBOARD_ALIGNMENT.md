# TRACK 15.75A · Phase 7 — Dashboard Alignment

## `/api/admin/pm-email-coverage` — updated

Endpoint version bumped to `track='15.75A'` and now pre-builds a roster
index (`roster_pm_by_pn`, `roster_co_pm_by_pn`) from
`project_team_assignments` before iterating `jobs_master`. Each row
in the response now carries two **new fields**:

* `roster_pm_email` — the resolved primary-PM email from the
  roster, or `""` if no active primary PM row.
* `roster_co_pm_emails` — list of all active co-PM emails from the
  roster.

And a **new status flag** can appear in the `status[]` list:

* `pm_email_ok_via_roster` — emitted when `jobs_master.pm_email`
  is blank but the roster carried a usable primary-PM email. These
  projects are counted as `active_with_pm_email` (i.e., they are
  NOT counted as missing) — exactly the operator's requirement
  that "if Job Master shows PM/Co-PM assigned, the routing health
  card must not claim missing PM unless email resolution truly failed."

If neither legacy nor roster resolves a primary PM, the row carries
`pm_email_blank` AND the new `roster_pm_email` / `roster_co_pm_emails`
fields surface the assignment source so the operator knows where
to look (Team Roster vs Active Jobs Master).

## Updated remediation note

Now reads:

> _TRACK 15.75A · The resolver now consults the Job Master Team Roster
> (`project_team_assignments`) when `jobs_master.pm_email` is blank.
> Projects whose roster carries an active primary PM are marked
> `pm_email_ok_via_roster` and route directly to that PM. Rows still
> listed here lack both a roster PM and a legacy pm_email — operator
> should assign a PM via /admin → 'Team Roster' for the project.
> Until backfilled, those projects' notifications fall through to
> ADMIN_DEAD_LETTER_TO (no silent failure)._

## Routing Status Panel (`RoutingStatusPanel.jsx`)

The component already pulls live from `/api/admin/pm-email-coverage`,
so it automatically picks up:
* the new shape (`track`, `summary`, `missing_rows_top_25`)
* the new per-row fields (`roster_pm_email`, `roster_co_pm_emails`)
* the new status flag (`pm_email_ok_via_roster`).

No frontend code change required for the missing-PM count to drop
the moment a Team Roster PM is assigned for an active project — the
backend already resolves it.

## Other dashboards

| Dashboard | Already truthful? | Why |
|---|---|---|
| Active Jobs Master | ✅ | Continues to render `jobs_master.pm_email` directly |
| Team Roster screen | ✅ | Direct render of `project_team_assignments` |
| PM Portal | ✅ | PM scope still works (uses team_routing for in-app notifications, independent surface) |
| Safety Admin | ✅ | Reads `meetings` / `incidents` directly |
| System Health / Email Routing v2 Status | ✅ | Inherits Track 15.74 audit truth |

## Live verification of new shape (from testing agent run)

```
GET /api/admin/pm-email-coverage (admin)  → 200
  track = "15.75A"
  summary.active_total = 30
  summary.active_with_pm_email = 23
  every row carries roster_pm_email / roster_co_pm_emails fields
  401 returned for missing X-Admin-Token
```
