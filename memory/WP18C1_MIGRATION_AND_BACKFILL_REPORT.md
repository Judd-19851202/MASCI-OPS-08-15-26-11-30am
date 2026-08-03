# WP18C1 Migration and Backfill Report

Date: 2026-08-03

## Scope

WP-18C1 used additive migration only. No protected subsystem was replaced. No source record was overwritten.

## Existing sources inventoried

- `jobs_master`
- `project_team_assignments`
- `cost_code_registry` (preserved, not remapped yet)
- Asset Spine / `equipment_master`
- `operational_locations`
- `enterprise_governance_identity_projections`

## Backfill results

Latest governed backfill run:

- run id: `hierarchy_run_2511692ec7`
- company root: `company:masci`
- division root: `division:operations`
- projects bound: `33`
- facility bindings created: `123`
  - operational location references: `3`
  - equipment location bindings: `120`
- resource assignment foundation records: `81`
- unresolved review-queue items: `14`

## Current MASCI hierarchy established

- Company: `MASCI`
- Division: `Operations`
- Departments:
  - `Project Management`
  - `Field Operations`
  - `Shop Operations`
  - `Safety`
  - `Human Resources`
- Facilities:
  - `The Shop` (`shop`)
  - `MASCI Yard` (`yard`)
  - `23-04 - E59B7` (`yard`)
  - `Lauri` (`yard`)
- Projects bound from `jobs_master`: `33`

## Unresolved mappings preserved for review

The following were intentionally **not** guessed:

- `Preview Yard`
- `25-02 - E53F5 - CARR SR 5 YARD`
- `24-02 - E59B2 - S MYRTLE YARD - THEFT`
- `23-03 - T5791 - NEW HAVEN RD YARD - THEFT`
- `23-01 - T5767 - INDUSTRY RD YARD - THEFT`
- `23-09 - T5797 - CLEARLAKE YARD - THEFT`
- `23-02 - E54B1 - ISB YARD - THEFT`
- `T5736 - N CR 426 YARD - THEFT`
- `21-06 - T5736 - S CENTRAL AVE YARD - THEFT`
- `T5736 W BROADWAY YARD - THEFT`
- `T5749 DOLORES DR YARD - THEFT`
- `T5749 HAINES ST YARD - THEFT`
- `PLANT - THEFT PROTECTION`
- `SHOP-THEFT PROTECTION`

## Determinism and rollback

- Backfill is additive and idempotent.
- Equipment-location bindings use stable source identifiers.
- Ambiguous values are queued for review instead of merged silently.
- Test-created hierarchy nodes were archived after verification to preserve MASCI’s live hierarchy view.

## Result

Deterministic backfill is complete for current clear evidence, and unresolved mappings are explicitly queued rather than guessed.