# TRACK 15.75A · Phase 2 — Routing Resolver Trace (Before / After)

## Resolver entry point

`pm_routing.resolve_pm_for_record_async(db, record)` returns `(name, email)` or `None`.
`pm_routing.recipients_for_record_async(db, record, kind)` returns `{to[], cc[], all[]}`.

## BEFORE Track 15.75A — read order

1. `jobs_master.find_one({project_number: …})` (case-insensitive regex; fallback to normalized prefix scan).
2. If `job.pm_email`: lookup `project_managers.find_one({email})` → return that PM, else return raw `pm_email`.
3. If only `job.project_manager` (name): lookup `project_managers.find_one({name})`, then `PM_TABLE[name]` legacy fallback.
4. Final fallback: legacy `PM_TABLE` by `project_name` substring match.
5. Else return `None` → routing escalates to `ADMIN_DEAD_LETTER_TO`.

**Defect:** the new Team Roster surface (`project_team_assignments`) was never consulted, so projects whose PM was assigned via that UI dead-lettered.

## AFTER Track 15.75A — read order (additive)

1. `jobs_master.find_one(...)` *(unchanged)*
2. If `job.pm_email`: same as before *(unchanged — legacy ALWAYS wins when present)*
3. If only `job.project_manager` name: same as before *(unchanged)*
4. **NEW** — `_resolve_roster_pm(db, project_number)`:
   * find `project_team_assignments` row where `assignment_role='pm' AND is_primary=true AND active=true`;
   * if `email` inline → return it;
   * else walk `user_id` → `user_directory`, `employee_id` → `employees` to resolve email.
5. Legacy `PM_TABLE` by `project_name` substring *(unchanged)*
6. Else return `None` → dead-letter *(unchanged)*

Co-PMs in `recipients_for_record_async`:
* Continue reading `jobs_master.co_pm_emails[]` *(unchanged)*
* **NEW** — union with `_resolve_roster_co_pms(db, project_number)`: every `project_team_assignments` row with `assignment_role='co_pm' AND active=true`.

## Per-project trace

| Project | DR count | Roster PM seeded (synthetic prod-mirror) | BEFORE — To | BEFORE — Reason | AFTER — To | AFTER — CC | Failure point fixed? |
|---|---|---|---|---|---|---|---|
| 20-07 | 53 | David Jewett (`davidjewett@mascigc.com`) | `safety@mascigc.com` (DEAD_LETTER) | `jobs_master.pm_email` blank · resolver returned None | `davidjewett@mascigc.com` | `pm.demo@mascigc.com` | ✅ |
| 26-07 | 16 | Jaymn Judd (`jaymn.judd@mascigc.com`) + co-PM David Jewett | `safety@mascigc.com` (DEAD_LETTER) | same | `jaymn.judd@mascigc.com` | `davidjewett@mascigc.com` | ✅ |
| 24-06 | 0 | David Jewett (also has `jobs_master.pm_email=davidjewett@…`) | `davidjewett@mascigc.com` (DIRECT_PM) | OK already | `davidjewett@mascigc.com` | `[]` | n/a — backward compatible |
| 25-02 | 0 | (no roster) — `jobs_master.pm_email=ramonrodriguez@…` | `ramonrodriguez@mascigc.com` (DIRECT_PM) | OK already | `ramonrodriguez@mascigc.com` | `[]` | n/a — backward compatible |

Live trace evidence: `/tmp/t1575a_live_roster_proof.py` output captured in §4 of the FINAL_CERTIFICATION.

## Exact line references (current code state)

* `pm_routing.py` lines 109–189 — `resolve_pm_for_record_async` (extended).
* `pm_routing.py` lines 192–276 — NEW `_resolve_roster_pm` + `_resolve_roster_co_pms` helpers.
* `pm_routing.py` lines 318–376 — `recipients_for_record_async` co-PM union block (extended).
