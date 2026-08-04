# WP-18C5 Constraint Authority Evidence

## Preserved rule

C5 references governed constraints but does not create a parallel constraint notes store.

## Evidence lines

- Existing constraint truth remains in the operational constraints authority:
  - `backend/routes/operational_constraints.py`
- Existing schedule review queue remains the governed review-item surface:
  - `project_schedule_review_queue`
- C5 candidate review items are written into the same governed review queue via:
  - `backend/services/project_schedule_actuals_spine.py::_upsert_review_item`

## What C5 does

- carries forward work-block `constraint_entries`
- opens governed review items when actual mapping / registry resolution / material classification remains ambiguous
- preserves provenance instead of auto-normalizing the constraint relationship

## What C5 does not do

- no independent constraint-master writes
- no duplicate constraint ledger
- no AI auto-closure of constraints

## Governing decision

**PASS** — C5 stays inside the existing constraint authority and uses governed review items for unresolved actuals/constraint links.
