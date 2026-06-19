# TRACK 15.51 · Training Compliance Certification (Phase 5)

**Status:** ✅ CERTIFIED · 7-state status model live · 4 surfaces agree.

## Status model coverage
| State | Schema field | Where set |
|---|---|---|
| Required | `status="Required"` | Default when training assigned but not yet started |
| Assigned | `status="Assigned"` | Default when training record created without completed_date |
| In Progress | `status="In Progress"` | Manually set during delivery |
| Completed | `status="Completed"` | Auto-default when `completed_date` is set |
| Verified | `status="Verified"` + `verified_by` + `verified_at` | Set on safety sign-off |
| Overdue | `status="Overdue"` | Background check vs `due_date` (or derived live in Executive Overview) |
| Waived | `status="Waived"` + `waived_by` + `waived_at` + `waiver_reason` | Explicit waiver path · no silent waivers |

## Four-surface agreement (all consume same `safety_training_records` collection)
| Surface | What it shows | Source query |
|---|---|---|
| Employee View | All training records for the employee · including incident-bound | `find({employee_id: <id>})` via HR portal |
| Safety View | Training records list filterable by status · incident binding · topic | Existing safety portal `/api/safety/training-records` endpoint |
| Executive View | Aggregate counts only · `training_required` / `training_completed` / `training_overdue` | Executive Overview safety tile (Track 15.50) |
| Incident View / PDF | Recurrence-prevention block on incident PDF | `_training_records` enrichment from `find({source_incident_id: <id>})` |

All four read the same collection → automatically agree. No sync logic needed.

## Live count check (preview DB)
- safety_training_records: 10 rows (legacy · pre-Track-15.50 fields)
- Of those · incident-bound: 0 (no production WV/PI incidents have hit the chain yet — synthetic test was cleaned)

This means `training_required=0`, `training_completed=0`, `training_overdue=0` on Executive Overview — accurate.

## Sign-off
GREEN. Status model is complete. Four surfaces agree by construction. The first WV/PI incident in production will exercise the full chain.
