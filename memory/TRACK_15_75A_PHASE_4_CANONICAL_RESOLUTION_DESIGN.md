# TRACK 15.75A · Phase 4 — Canonical PM / Co-PM Resolution Design

## Resolver contract (post-fix)

`pm_routing.resolve_pm_for_record_async(db, record)` returns
`Optional[(name, email)]`. Order of consultation:

```
1. jobs_master lookup by project_number (case-insensitive regex, then
   normalized prefix-match scan).
2. If job.pm_email present:                ─► return (name, pm_email)
3. Elif job.project_manager (name) present:─► project_managers.find_one(name)
4.                                          ─► PM_TABLE[name] (legacy)
5. NEW · project_team_assignments roster   ─► _resolve_roster_pm()
        Filter: assignment_role='pm',
                is_primary=true,
                active=true
        Resolution:
          a) inline `email`
          b) walk user_id → user_directory.email
          c) walk employee_id → employees.email
        Return (display_name|name, email)
6. PM_TABLE substring on project_name (legacy final fallback).
7. Else return None  ─► dead-letter (Track 15.74 truthful audit row).
```

## Co-PM contract (post-fix)

`pm_routing.recipients_for_record_async(db, record, kind)` builds
`co_pm_emails[]` as:

```
co_pm_emails = unique_union(
    jobs_master.co_pm_emails[],       # legacy
    _resolve_roster_co_pms(db, pn),   # NEW · roster rows with
                                       #  assignment_role='co_pm', active=true
)
```

Deduplication via case-insensitive `lower()` compare; the primary
PM email is excluded from the co-PM list.

## Failure-mode handling (every branch ends in a truthful audit row)

| Branch | Behavior | Audit row contents |
|---|---|---|
| Legacy `pm_email` resolves | Direct PM in To, co-PMs (legacy + roster) in CC | `status='resolved'`, recipients > 0 |
| Legacy name resolves via `project_managers` | same as above | same |
| Roster `is_primary` PM resolves with inline email | same | same |
| Roster `is_primary` PM resolves via `user_directory` walk | same | same |
| Roster `is_primary` PM resolves via `employees` walk | same | same |
| Roster PM exists but `active=false` | Ignored (silent-leak protection) | dead-letter audit row if no other PM resolves |
| Roster PM exists but `is_primary=false` | Ignored (backup PMs don't notify by default) | dead-letter audit row if no other PM resolves |
| Nothing resolves | Dead-letter | `status='routed_to_dead_letter'` (Track 15.74) carrying actual count |
| Nothing AND dead-letter unconfigured | Dead-letter audit | `status='dead_letter_unconfigured'` (Track 15.74) |

## What we deliberately did NOT do

* **Did not** migrate `jobs_master.pm_email` from the roster at startup.
  This would have been a write — out of scope of Track 15.75A (and risky
  if the operator wants the roster to be authoritative going forward).
* **Did not** flip OWNERSHIP_LOCK_ENABLED behavior. Track 15.75A
  consults the roster regardless of the flag; the flag only governs
  the `lib/team_routing.resolve_routing` in-app notification fanout.
* **Did not** introduce a V3 routing system. One resolver, three
  reads, all backward-compatible.

## Invariants the design preserves

1. Legacy `jobs_master.pm_email` ALWAYS wins when present.
   *(Regression: `test_legacy_pm_email_still_wins_when_present`.)*
2. Inactive roster rows never resolve as PM.
   *(Regression: `test_inactive_roster_pm_is_ignored`.)*
3. Non-primary roster rows never resolve as the primary PM.
   *(Regression: `test_non_primary_roster_pm_is_ignored`.)*
4. Legacy co-PMs are never dropped.
   *(Regression: `test_roster_co_pms_unioned_with_legacy`.)*
5. The dead-letter audit remains truthful per Track 15.74.
   *(Regression: `test_dead_letter_audit_*`.)*
