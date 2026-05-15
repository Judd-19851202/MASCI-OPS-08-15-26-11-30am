# Master Collection SOT Audit — Iter137 (Phase-1 Iter C-continued)

## Findings

✅ **Zero duplicates** in source-of-truth collections:
- `equipment_master`: 589 rows, no duplicate unit_numbers / VINs / serials
- `employees`: 240 rows, no duplicate emails / employee_ids

⚠️ **Cross-portal records store equipment/employee data without referencing master IDs.** Same-named items don't bind to the canonical record, so renames don't propagate and Search can't join cleanly.

## Coverage (before backfill)

| Collection | Total | With master ref | % |
|---|---|---|---|
| equipment_inspections | 23 | 0 | 0% |
| fire_extinguishers | 5 | 0 | 0% |
| incidents | 4 | 0 | 0% |
| corrective_actions | 1 | 0 | 0% |
| safety_training_records | 1 | 0 | 0% |

## Coverage (after iter137 backfill)

| Collection | Total | With master ref | % |
|---|---|---|---|
| equipment_inspections | 23 | **3** | **13%** |
| fire_extinguishers | 5 | 0 | 0% |
| incidents | 4 | 0 | 0% |
| corrective_actions | 1 | 0 | 0% |
| safety_training_records | 1 | **1** | **100%** |

## What was shipped (iter137)

- `backend/routes/master_lookup.py` NEW. Endpoints:
  - `GET /api/master-lookup/equipment?q=…` — typeahead (public read)
  - `GET /api/master-lookup/employees?q=…` — typeahead (public read; supports both 'name' single-field schema AND first/last split schema)
  - `POST /api/master-lookup/backfill/equipment?dry_run=true|false` — admin: scan cross-portal records, attach `equipment_master_id` where the freetext resolves
  - `POST /api/master-lookup/backfill/employees?dry_run=true|false` — admin: same for employees, matches by email → employee_id → full name
  - `GET /api/master-lookup/audit` — admin: returns current coverage %

## Schema observation

The `employees` collection uses a single `name` field (e.g., "Jaymn Judd"), not the standard `first_name`/`last_name` split assumed elsewhere. The lookup helper handles both schemas via $or query.

## Carryover work (next iter)

1. **Add foreign-key fields to model definitions**: Pydantic models for incidents, corrective_actions, fire_extinguishers should include optional `equipment_master_id` + `employee_master_id` fields so new submissions write the ref by default.
2. **Frontend typeahead wiring**: drop the lookup endpoints into the incident-create, CA-create, fire-ext-create forms so the freetext field becomes a search-and-pick.
3. **Resolution UI**: a "this CA has no master equipment link — pick one?" call-to-action in the Safety Portal so legacy records can be backfilled by a human.
4. **Mass-rename safety**: until coverage hits 100%, equipment master renames still won't propagate to history records that store freetext only.
