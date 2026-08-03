# WP18C2 · Operational Work Ledger Contract

## Purpose

WP-18C2 implemented an **additive operational work ledger** in `project_controls_work_ledger`.

This ledger does **not** replace Daily Reports. It connects Daily Report evidence into a governed, queryable operational contract for PM project controls and future connected reporting.

## Authority Boundary

- **Source-of-truth owner for actual field input:** `daily_reports`
- **Additive ledger substrate:** `project_controls_work_ledger`
- **Schedule truth remains separate:** existing schedule engine / PM authority
- **Budget truth remains future:** not implemented in WP-18C2
- **EV truth remains future:** not implemented in WP-18C2

## Implemented Ledger Row Shape

Each row stores:

- `ledger_id`
- `source_report_id`
- `source_report_number`
- `project_number`
- `project_name`
- `report_date`
- `work_block_id`
- `title`
- `authority_owner = daily_reports`
- `ledger_contract_version = wp18c2.v1`
- `cost_code`
- `pay_item_id`
- `customer_pay_item_number`
- `primary_work_type_id`
- `work_type_ids[]`
- `schedule_activity_id`
- `schedule_actual_proposal_status`
- `installed_quantity`
- `unit`
- `resource_counts { labor, equipment, materials, subcontractors, constraints }`
- `block { ...normalized governed work block snapshot... }`
- `created_at`

## Linkage Contract Implemented

The normalized work block / ledger row supports linkage to:

- Project
- Contract (when known)
- Phase (when known)
- Work package (when known)
- Project pay item (when known)
- Cost code (when known)
- Schedule activity (when known)
- Labor rows
- Equipment rows
- Material rows
- Subcontractor rows
- Constraint rows
- Photo refs
- Attachment refs
- QA/QC refs (structure present)
- Safety refs (structure present)

## Runtime Evidence

- Current ledger row count: **178**
- Ledger contract version in use: **`wp18c2.v1`**
- PM runtime verification confirmed ledger visibility on `/pm/project-controls`

Sample historical ledger evidence observed at runtime:

- `source_report_number = DR-2099-00006`
- `title = General Field Work`
- `resource_counts = labor:1, materials:1`
- `schedule_actual_proposal_status = proposed_only`

## Non-authority Guardrails

- The ledger never overrides the Daily Report.
- The ledger never overwrites the schedule.
- The ledger does not implement budget hierarchy or earned value.
- The ledger is not an accounting general ledger.
