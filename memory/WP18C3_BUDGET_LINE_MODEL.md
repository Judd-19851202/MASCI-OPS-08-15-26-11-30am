# WP18C3 Budget Line Model

Date: 2026-08-03

## Purpose

WP-18C3 introduces an additive `project_budget_lines` authority that is future-ready for later work packages without redesigning the schema. The line model is intentionally **not** an accounting ledger, **not** Earned Value, and **not** a forecasting engine. It is the governed financial-planning layer sitting between contractual customer pay items and later operational / reconciliation workflows.

## Constitutional invariants

1. **Customer Pay Item remains customer truth** and stays distinct from MASCI enterprise work type.
2. **Budget Line remains planning truth** and does not become the accounting ledger.
3. **Operational Work Ledger remains execution fact truth** and is only referenced from the budget line.
4. **No silent population**: future-ready relationships exist structurally, but only approved evidence may populate them.
5. **No original-budget overwrite**: budget versions preserve historical truth; line rows are version-bound.

## Canonical shape

### Identity and lineage
- `budget_line_id`
- `project_number`
- `version_id`
- `status`
- `source_import_id`
- `source_row_id`
- `source_document_hash`
- `source_lineage.pm_approved_at`
- `source_lineage.pm_approved_by`

### Contractual / classification references
- `customer_pay_item_id`
- `customer_pay_item_number`
- `description`
- `enterprise_work_type_id`
- `project_cost_code`
- `phase_id`
- `work_package_id`
- `schedule_activity_id`
- `schedule_activity_name`
- `line_kind` (`direct_cost`, `allowance`, `contingency`, `management_reserve`)

### Future-ready operational references
- `daily_report_work_block_ids[]`
- `crew_ids[]`
- `employee_ids[]`
- `equipment_ids[]`
- `material_refs[]`
- `vendor_refs[]`
- `subcontractor_refs[]`
- `commitment_refs[]`
- `actual_cost_refs[]`
- `forecast_refs[]`

### Financial separation fields
- `quantity`
- `unit`
- `unit_budget_amount`
- `budget_amount`
- `commitment_amount`
- `actual_cost_amount`
- `forecast_amount`
- `remaining_amount`
- `revenue_amount`
- `billing_amount`
- `collections_amount`

### Crew-cost / production readiness fields
- `labor_cost_budget_amount`
- `equipment_cost_budget_amount`
- `material_cost_budget_amount`
- `subcontract_cost_budget_amount`
- `vendor_cost_budget_amount`
- `production_quantity_rollup`

### Trust-line metadata
- `trust_lines.budget = project_budget_lines`
- `trust_lines.commitment = po_requests`
- `trust_lines.actual_cost = external_accounting_or_governed_receipt_review`
- `trust_lines.revenue = customer_contract_or_future_billing_module`
- `trust_lines.billing = future_billing_module`
- `trust_lines.collections = future_collections_module`

## What C3 populates now

Runtime-certified fields populated in the active certification line:
- project / version identity
- customer pay item reference
- enterprise work type reference
- project cost code reference
- phase / work package / schedule activity foundation
- quantity / unit / budget / forecast / remaining
- source lineage and PM approval metadata

## What C3 intentionally leaves as empty-but-supported arrays

The following remain structurally present but unpopulated until later authorized work packages provide evidence-backed bindings:
- Daily Report work blocks
- crews / employees
- equipment
- material movements
- vendors / subcontractors
- commitment refs
- actual-cost refs
- forecast refs

## Certified runtime example

Active certified row (`ZZ-RUNTIME-CERT-2026`):
- `budget_line_id`: `budget-line:ZZ-RUNTIME-CERT-2026:...:a178785e:...`
- `customer_pay_item_number`: `CERT-001`
- `enterprise_work_type_id`: `work-type:asphalt`
- `project_cost_code`: `C3-CERT-1785798640`
- `phase_id`: `PHASE-A`
- `work_package_id`: `WP-C3`
- `schedule_activity_id`: `ACT-C3-2`
- `budget_amount`: `1200.0`
- `forecast_amount`: `1200.0`
- `remaining_amount`: `1200.0`

## Architectural result

The model satisfies the C3 amendments:
- dual cost-code architecture preserved;
- future linkage to C4–C10 is structurally possible without schema redesign;
- no accounting duplication was introduced;
- ambiguous data remains queued instead of guessed.
