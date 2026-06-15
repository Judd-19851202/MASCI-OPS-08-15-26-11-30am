# NOTIFICATION_ROUTING_MATRIX.md · Track 14.0-PM-STAFFING-RUNTIME-CERTIFICATION

**Generated**: 2026-02-14 · **Source**: `backend/lib/event_fanout.py` + `lib/team_routing.py` static analysis.
**Honest scope note**: code-derived. Live event emission per role-bucket has spot-test coverage in `test_event_fanout.py` and the staffing tests; full 17-role × N-event runtime cert is **not** done in this session.

## Event × Recipient Routing

| Event Class | Routed To (by role assignment on project) | Fallback (no assignment) |
|---|---|---|
| Daily Report submitted | `pm` + `co_pm` + `superintendent` | `pm` from `jobs_master.pm_id` |
| Daily Report revision request | `pm` + `co_pm` | `pm` |
| Incident filed | `safety_rep` + `pm` + `co_pm` + `superintendent` | Safety bell-bucket |
| Safety form submitted | `safety_rep` + `pm` | Safety bell-bucket |
| QA/QC inspection filed | `qaqc_rep` + `project_engineer` + `pm` | PM bell-bucket |
| Equipment pre-op FAIL | `equipment_manager` + `shop_rep` + `safety_rep` + `pm` | Shop bell-bucket |
| Equipment return | `equipment_manager` + `shop_rep` | Shop bell-bucket |
| Asset transfer | `pm` (from) + `pm` (to) + `equipment_manager` | Admin |
| PO request | `pm` + `project_administrator` + `accounting_rep` | PM |
| Time-off request | `hr_rep` + `superintendent` + `pm` | HR bell-bucket |
| Time verification flag | `hr_rep` + `pm` + `accounting_rep` | HR |
| Document expiration | `hr_rep` (HR docs) · `safety_rep` (safety certs) · `equipment_manager` (equipment) | Per category bell-bucket |
| Training completion | `safety_rep` + `hr_rep` + `pm` | HR |
| Dispatch broadcast | `dispatch_rep` + `pm` + `superintendent` | Dispatch |
| Survey completion | `survey_rep` + `project_engineer` + `pm` | PM |
| Project assignment change | the assigned user + `pm` + `co_pm` | n/a |
| Approval (employee request) | originating supervisor + `hr_rep` + `pm` | HR |

**Mechanism**: `emit_task_and_notification(kind, project_number, …)` calls `team_routing.recipients_for(kind, project_number)` which reads the project's `team_snapshot` for the active assignments per role, normalises legacy aliases through `_canonical_role()`, and falls back to portal bell-buckets when the project has no assignments for the relevant role.

**Identity-aware**: every email + bell payload runs through the canonical identity helper (UXS-11G) so recipients see "James Fisher (Jimmy)" in subject lines and body labels.

**What needs runtime cert**: trigger each event class with a seeded preview project + assigned test users; capture inbox / bell receipts.
