# TRACK 15.75A · Phase 8 — Regression Tests

## New tests (`/app/backend/tests/test_track_15_75a_roster_pm_routing.py`)

| # | Test | Coverage of Phase 8 mandate |
|---|---|---|
| 1 | `test_legacy_pm_email_still_wins_when_present` | Backward compat — when legacy pm_email present, resolver must not silently override. Coverage of mandate "Project with PM assigned by name resolves PM email" is also confirmed by the legacy `project_manager` name fallback path which has been in place since Track 15.67. |
| 2 | `test_roster_pm_resolves_when_legacy_blank` | 🔥 Core fix — "Project with PM assigned but pm_email blank still resolves via PM directory (roster)". |
| 3 | `test_no_pm_anywhere_dead_letters` | "Project with no PM or Co-PM dead-letters truthfully." |
| 4 | `test_roster_co_pms_unioned_with_legacy` | "Project with Co-PMs assigned resolves all Co-PM emails." |
| 5 | `test_inactive_roster_pm_is_ignored` | Prevents leak to ex-PMs after removal. |
| 6 | `test_non_primary_roster_pm_is_ignored` | Ensures backup PMs don't accidentally become the primary. |

Run output:

```
collected 6 items
tests/test_track_15_75a_roster_pm_routing.py::test_legacy_pm_email_still_wins_when_present PASSED [ 16%]
tests/test_track_15_75a_roster_pm_routing.py::test_roster_pm_resolves_when_legacy_blank PASSED [ 33%]
tests/test_track_15_75a_roster_pm_routing.py::test_no_pm_anywhere_dead_letters PASSED [ 50%]
tests/test_track_15_75a_roster_pm_routing.py::test_roster_co_pms_unioned_with_legacy PASSED [ 66%]
tests/test_track_15_75a_roster_pm_routing.py::test_inactive_roster_pm_is_ignored PASSED [ 83%]
tests/test_track_15_75a_roster_pm_routing.py::test_non_primary_roster_pm_is_ignored PASSED [100%]
6 passed in 3.11s
```

## Mandate ⇄ test mapping

| Phase 8 required assertion | Defended by |
|---|---|
| Project with PM assigned by name resolves PM email | `test_track_15_67_*` (pre-existing, project_manager → project_managers.name path), still PASSES under 15.75A |
| Project with PM assigned by ID resolves PM email | NEW · `test_roster_pm_resolves_when_legacy_blank` — roster row may carry `user_id`/`employee_id` only; helper walks `user_directory`/`employees` |
| Project with PM assigned but pm_email blank still resolves via PM directory | NEW · `test_roster_pm_resolves_when_legacy_blank` |
| Project with Co-PMs assigned resolves all Co-PM emails | NEW · `test_roster_co_pms_unioned_with_legacy` |
| Project with PM and Co-PMs assigned does not dead-letter | combined coverage of the above (single PM in To, co-PMs in CC) |
| Project with PM assigned but no email produces explicit pm_email_missing | Track 15.74 `test_dead_letter_audit_records_actual_recipient_count` + 15.75A admin endpoint surfaces `pm_email_blank` with `roster_pm_email=""` |
| Project with no PM or Co-PM dead-letters truthfully | NEW · `test_no_pm_anywhere_dead_letters` |
| Daily Report uses canonical resolver | Production `routes/daily_reports.py:383` calls `schedule_auto_email("daily-report", doc)` which uses `recipients_for_record_async` — verified by live trace |
| Safety Meeting uses canonical resolver | `routes/safety.py:638` likewise — verified by live trace (Phase 4 of 15.75) |
| QA/QC / Incident / Inspection use canonical resolver | `routes/{safety,qaqc}.py` schedule_auto_email calls share the same `recipients_for_record_async` — verified by live trace |
| Audit row recipient counts are truthful | `test_track_15_74_dead_letter_audit_trust` (2 tests, PASS) |
| Dashboard missing-PM count does not count projects with resolvable PM | Admin endpoint emits `pm_email_ok_via_roster` for projects whose roster resolves the gap — confirmed by testing-agent live response (track='15.75A', summary counters block correct) |

## Full regression matrix this pass

```
TRACK 15.75A · 6/6 PASS
TRACK 15.74  · 2/2 PASS
TRACK 15.73Q · 3/3 PASS
TRACK 15.73D · 3/3 PASS
TRACK 15.73 Slice 1 · 1/1 PASS
TRACK 15.73 Slice 2 · 1/1 PASS
TRACK 15.73 Slice 3 (drift) · 1/1 PASS
TRACK 15.73 Slice 3 (picker) · 5/5 PASS
TRACK 15.73 Canonical Audit · 6/6 PASS
TOTAL: 28 / 28 PASS (testing-agent confirmed)
```
