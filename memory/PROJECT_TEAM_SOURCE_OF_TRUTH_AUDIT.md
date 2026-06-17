# PROJECT TEAM SOURCE-OF-TRUTH AUDIT (TRACK 15.10)

**Scope:** every role surfaced on the Project Team page. **Goal:** confirm there is exactly ONE source-of-truth collection per role and that the page consumes it without inventing a parallel identity store.

## Single canonical model
- **People** live in `user_directory` (`{ id, email, name, employee_id, portals[], disabled, must_change_password, password_hash, last_login_at }`).
- **Assignments** live in `project_team_assignments` (`{ project_number, user_id, employee_id, email, display_name, assignment_role, active, is_primary, … }`).
- **Project leadership cascade** lives on `jobs_master` (`pm_email`, `co_pm_emails[]`) — backfilled idempotently into `project_team_assignments` and JIT-lifted by Track 15.10 if the backfill hasn't run for a given project.
- **No new collection introduced in Track 15.10.** Asserted by `test_no_new_collections_introduced`.

## Per-role inventory

| # | Role | Assignment role key | Source roster (people) | Source roster field used by picker | Assignable by |
|---|---|---|---|---|---|
| 1 | Project Manager | `pm` | `jobs_master.pm_email` → `user_directory` | `user_directory.email/name` | **Admin only** |
| 2 | Co-PM | `co_pm` | `jobs_master.co_pm_emails[]` → `user_directory` | `user_directory.email/name` | **Admin only** |
| 3 | Executive Oversight | `executive_oversight` | `user_directory` (portal=admin) | `user_directory.email/name` | **Admin only** |
| 4 | Superintendent | `superintendent` | `user_directory` (portal=field-leadership or pm) | `user_directory.email/name` | PM-assignable |
| 5 | Assistant Superintendent | `assistant_superintendent` | `user_directory` (portal=field-leadership) | same | PM-assignable |
| 6 | Foreman | `foreman` | `user_directory` (portal=field-leadership) | same | PM-assignable |
| 7 | Project Engineer | `project_engineer` | `user_directory` (portal=pm) | same | PM-assignable |
| 8 | Project Administrator | `project_administrator` | `user_directory` (portal=pm) | same | PM-assignable |
| 9 | Project Coordinator | `project_coordinator` | `user_directory` (portal=pm) | same | PM-assignable |
| 10 | Safety Representative | `safety_rep` | `user_directory` (portal=safety) | same | PM-assignable |
| 11 | QA/QC Representative | `qaqc_rep` | `user_directory` (portal=safety / pm) | same | PM-assignable |
| 12 | HR Representative | `hr_rep` | `user_directory` (portal=hr) | same | PM-assignable |
| 13 | Dispatch Representative | `dispatch_rep` | `user_directory` (portal=dispatch) | same | PM-assignable |
| 14 | Equipment Manager | `equipment_manager` | `user_directory` (portal=shop) | same | PM-assignable |
| 15 | Shop Representative | `shop_rep` | `user_directory` (portal=shop) | same | PM-assignable |
| 16 | Survey Representative | `survey_rep` | `user_directory` (portal=field-leadership or pm) | same | PM-assignable |
| 17 | Accounting Representative | `accounting_rep` | `user_directory` (portal=admin / pm) | same | PM-assignable |

`user_directory.portals[]` is the existing per-user portal-access multi-value field — Track 15.10 does not add a new field, it just reads it.

## Identity / login fields consumed (read-only)

| Field | Used for |
|---|---|
| `id` | Assignment user_id binding |
| `email` | Identity match (case-insensitive) |
| `name` | Display name, fallback rank 3 |
| `employee_id` | Cross-link to HR `employees` collection |
| `disabled` | Login status → `disabled` |
| `must_change_password` | Login status → `invite_pending` |
| `password_hash` | Login status → `active` (if present) |
| `last_login_at` | Login status → `active` (if present) |
| `portals[]` | Optional filter for the PM picker |

## Known data gaps (carry-forward, NOT deferral of Track 15.10 items)

| # | Gap | Impact | Recommended fix | Owner |
|---|---|---|---|---|
| A | `accounting_rep` and `survey_rep` portals are not consistently stamped on legacy directory rows. | Pickers for these roles may show a smaller candidate list than expected. | Admin: assign `portals: ["pm"]` or `["admin"]` to relevant directory rows; or operator can call `/api/pm/directory/users` without the portal filter to see all. | Admin |
| B | Legacy DR docs may have `superintendent: "(unnamed)"` strings already in the database (not in `project_team_assignments` — in old `daily_reports` docs). | Track 15.10's panel-side fix prevents `(unnamed)` from being rendered going forward; legacy DR doc content is a separate cleanup. | Optional data sweep on `daily_reports` collection. | Operator |
| C | `assistant_superintendent` was added late; not all field leadership users have it as a portal value. | Same as A — picker still works via name search. | Same as A. | Admin |

These gaps DO NOT block Track 15.10 closure — the operational workflow works correctly regardless. They are documented for future cleanup.
