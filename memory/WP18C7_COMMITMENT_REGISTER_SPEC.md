# WP18C7 Commitment Register Spec

## Register lanes
- **Manual operator commitments**: persisted in `project_forecast_commitments`
- **PO-derived commitment exposure**: read-only derived from `project_budget_commitment_candidates`

## Core fields
- `commitment_id`
- `project_number`
- `family`
- `status`
- `title`
- `due_date`
- `linked_unit`
- `target_quantity`
- `target_hours`
- `target_amount`
- `confidence`
- `history[]`

## Comparison fields
- `actual_quantity`
- `actual_hours`
- `actual_amount`
- `derived_status`
- `drivers[]`

## UI surfaces
- PM editable register in the Commitments tab
- Executive read-only register in the same workspace
- FL receives constrained at-risk commitment visibility only
