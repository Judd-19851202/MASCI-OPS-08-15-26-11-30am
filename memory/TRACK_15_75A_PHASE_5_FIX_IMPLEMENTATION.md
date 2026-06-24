# TRACK 15.75A · Phase 5 — Fix Implementation

## Files changed

| File | Type of change | Lines (approx.) |
|---|---|---|
| `/app/backend/pm_routing.py` | feature — add roster fallback resolution | +130 |
| `/app/backend/routes/admin_pm_coverage.py` | feature — surface roster-resolved coverage on `/api/admin/pm-email-coverage` | +25 |
| `/app/backend/tests/test_track_15_75a_roster_pm_routing.py` | NEW — 6 regression tests | +220 |

## Workflows covered by a single resolver fix

The same `recipients_for_record_async` is the routing engine for
every project-linked workflow. So a single read-expansion in
`pm_routing.py` automatically restores routing for:

* Daily Reports (`schedule_auto_email("daily-report", …)` in `routes/daily_reports.py:383`)
* Safety Meetings (`schedule_auto_email("meeting", …)` in `routes/safety.py:638`)
* Equipment Pre-Ops (`schedule_auto_email("equipment-inspection", …)` in `routes/equipment.py:230`)
* Incidents (`schedule_auto_email("incident", …)` in `routes/safety.py:853`)
* QA/QC (`schedule_auto_email("qaqc", …)` in `routes/qaqc.py:218`)
* Inspections (`schedule_auto_email("inspection", …)` in `routes/safety.py:460`)
* JHA / JHP (`schedule_auto_email("jha", …)` in `routes/safety.py:742`)

This satisfies the Phase 5 mandate "do not patch only Daily Reports
if other workflows use the same broken source chain" — the broken
source chain is patched at its single root.

## Backward compatibility proof

`test_legacy_pm_email_still_wins_when_present` constructs a job
with BOTH `jobs_master.pm_email='pm.legacy@…'` AND a roster row
pointing at `pm.roster@…`. The resolver must return the legacy
value. Test PASSES.

## Co-PM union proof

`test_roster_co_pms_unioned_with_legacy` constructs a job with
BOTH a legacy co-PM in `jobs_master.co_pm_emails` AND a roster
co-PM. The resulting CC list must contain BOTH. Test PASSES.

## Silent-leak prevention proofs

* `test_inactive_roster_pm_is_ignored` — `active=false` roster row never resolves.
* `test_non_primary_roster_pm_is_ignored` — `is_primary=false` row never resolves as primary.

Both PASS.

## Live live-trace verification (synthetic prod-mirror)

```
  26-07    to=['jaymn.judd@mascigc.com']     cc=['davidjewett@mascigc.com']
  20-07    to=['davidjewett@mascigc.com']    cc=['pm.demo@mascigc.com']
  24-06    to=['davidjewett@mascigc.com']    cc=[]
  25-02    to=['ramonrodriguez@mascigc.com'] cc=[]
```

Outcomes match the operator's stated production assignments (with
the preview-only co-PM `pm.demo@mascigc.com` still surfaced on 20-07
because the preview fixture exists in `project_team_assignments`).

## No production writes

The fix is **read-only expansion**. It introduces no new write
path; it does not migrate any data; it does not change any
existing collection schema. The only DB writes during validation
were synthetic test fixtures using `TRACK-15-75A-TEST-*` project
numbers, all torn down on teardown.
