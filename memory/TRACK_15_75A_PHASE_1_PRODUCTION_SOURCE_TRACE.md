# TRACK 15.75A · Phase 1 — Production Source-of-Truth Trace

## Findings

Two parallel collections persist project assignments in this platform:

| Source | Collection | Fields | Written by |
|---|---|---|---|
| **Legacy** | `jobs_master` | `pm_email`, `project_manager` (name), `co_pm_emails[]` | `POST /api/admin/jobs` (`server.py:3351`, `jobs_master.upsert_job`); `PATCH /api/admin/jobs/{job_id}/co-pms` (`server.py:3802`) |
| **Team Roster (new)** | `project_team_assignments` | `project_number`, `assignment_role` (`pm` / `co_pm` / `foreman` / `safety_rep` / `hr_rep` / …), `is_primary`, `active`, `email`, `display_name`, `user_id`, `employee_id` | `POST /api/admin/jobs/{project_number}/team` (`routes/project_team_assignments.py:936`) — this is the new UI surface the operator showed in screenshots |

## Per-project trace (preview snapshot)

| Project | UI PM shown (operator screenshot) | UI Co-PMs shown | `jobs_master.pm_email` (preview) | `jobs_master.project_manager` (name) | `jobs_master.co_pm_emails` | `project_team_assignments` active rows |
|---|---|---|---|---|---|---|
| **20-07** | David Jewett | Leo Masci · Vincenza Massaro | _(empty)_ | _(empty)_ | _(empty)_ | 1 active co_pm (`pm.demo@mascigc.com` — preview fixture) · 1 active foreman · 1 active safety_rep · **NO active pm row in preview** |
| **26-07** | Jaymn Judd | Vincenza Massaro · David Jewett | _(empty)_ | _(empty)_ | _(empty)_ | **0 rows** in preview |
| **24-06** | David Jewett | — | `davidjewett@mascigc.com` ✅ | _(empty)_ | _(empty)_ | 1 active pm (`davidjewett@mascigc.com`, `source='backfill_pm_email'`) |
| **24-08** | Chris Wright | — | `davidjewett@mascigc.com` (preview drift) | _(empty)_ | _(empty)_ | _(none observed)_ |
| **25-02** | Ramon Rodriguez | — | `ramonrodriguez@mascigc.com` ✅ | _(empty)_ | _(empty)_ | _(none observed)_ |

> **Key:** Preview DB is a snapshot — production carries the live roster data shown in operator screenshots. The fix works against **whatever data is in the roster collection**, so once production already has PM=David Jewett for 20-07 in `project_team_assignments`, the fixed resolver will route to him.

## API endpoint feeding the Job Master "Team Roster" screen

* `GET /api/admin/jobs/{project_number}/team` — returns the merged view of legacy + roster rows via `resolve_team_for_project(db, project_number)`. This is what the screenshot UI renders.
* Writes go to `POST /api/admin/jobs/{project_number}/team` → inserts into `project_team_assignments` (NEVER touches `jobs_master.pm_email` / `co_pm_emails`).
* The legacy PM cell on Active Jobs Master goes through `POST /api/admin/jobs` → `jobs_master.upsert_job` → writes to `jobs_master.pm_email` / `project_manager`.

## Conclusion

The screen the operator sees as "PM cell" is the **Team Roster** screen, which writes to `project_team_assignments`. The routing resolver was reading **only** `jobs_master.pm_email`. The two surfaces never spoke to each other before the Track 15.75A fix.
