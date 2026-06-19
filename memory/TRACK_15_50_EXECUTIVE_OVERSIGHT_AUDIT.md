# TRACK 15.50 · Executive Oversight Audit (Phase 8)

**Status:** ✅ AUDIT + SMALLEST-ADDITIVE FIX DELIVERED.

## Pre-15.50 executive visibility into retraining
Zero. Training records existed in `safety_training_records` but no aggregate or summary surfaced anywhere on the Executive Overview.

## What 15.50 added (smallest additive solution)
THREE counts on the existing safety tile · NO new tile · NO new endpoint · NO new collection:
- **`training_required`** = count of incident-triggered training records that exist (have `source_incident_id` set)
- **`training_completed`** = same, filtered by `status` ∈ {Completed, Verified}
- **`training_overdue`** = count of `incident.aftercare.training_14d` tasks past their `due_at` and not Closed/Completed

## Verdict integration
- Any incident-triggered training overdue → forces verdict to RED + adds a verdict_reasons bullet ("N incident-triggered training assignment(s) overdue").
- Foundation version bumped to **v15.50.1**.

## Live evidence
- `GET /api/admin/executive/overview` returns:
  - `foundation_version: 15.50.1`
  - `tiles.safety.training_required: 0`
  - `tiles.safety.training_completed: 0`
  - `tiles.safety.training_overdue: 0`
  - `source_modules` now includes `safety_training_records`

## Frontend tile · ExecutiveOverview.jsx
Three new lines on the safety tile with `data-testid`:
- `tile-safety-training-required` · "N incident-triggered retraining required"
- `tile-safety-training-completed` · "N retraining completed"
- `tile-safety-training-overdue` · "N retraining overdue" · red emphasis when > 0

Tile color tone also reflects overdue training: red when `training_overdue > 0`.

## Five-question scorecard from Phase 8
| Question | Answer | Where |
|---|:---:|---|
| How many WV incidents occurred? | ✅ | `safety.wv_incidents_90d` (Track 15.48) |
| How many employees retrained? | ✅ | `safety.training_completed` (NEW 15.50) |
| Outstanding retraining requirements? | ✅ | `safety.training_required` (NEW 15.50) |
| Overdue retraining? | ✅ | `safety.training_overdue` (NEW 15.50) + RED verdict |
| Repeat incidents? | 🟡 PARTIAL | Derivable from `safety.public_interaction_30d` but no project-or-employee-grouped "repeat" tile. Backlog Track 15.51 candidate. |

## Sign-off
GREEN. Four of five executive visibility questions are answered directly. The fifth (repeat-incidents) requires a project/employee grouping query — documented as Track 15.51 candidate.
