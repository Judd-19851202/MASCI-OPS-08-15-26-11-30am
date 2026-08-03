# WP18C3 Financial Trust-Line Evidence

Date: 2026-08-03

## Trust-line matrix

| Concept | Canonical store / truth line | C3 behavior | Explicitly not overloaded with |
|---|---|---|---|
| Enterprise work type | `enterprise_work_type_registry` | Classification suggestion + PM-approved linkage | customer numbering, budget totals |
| Customer pay item / customer cost code | `project_pay_item_registry` | Contractual/project truth referenced by budget lines | enterprise work type identity |
| Budget version | `project_budget_versions` | Planning authority with historical version preservation | commitments, accounting actuals |
| Budget line | `project_budget_lines` | Planning line with future-ready references | operational work ledger, GL transactions |
| Commitment | `po_requests` → `project_budget_commitment_candidates` | Review-only linkage foundation | budget overwrite, accounting actuals |
| Actual cost candidate | `project_budget_actual_cost_candidates` | Review-only candidate foundation | booked accounting truth |
| Operational work | `project_controls_work_ledger` | Read-only downstream reference | budget or cost truth |
| Revenue / billing / collections | reserved fields on line + future modules | structurally separated, left at zero in C3 | budget / commitments / actual cost |

## Runtime API evidence

PM overview response for `ZZ-RUNTIME-CERT-2026` returned:
- `customer_pay_item_truth = project_pay_item_registry`
- `enterprise_work_type_truth = enterprise_work_type_registry`
- `budget_version_truth = project_budget_versions`
- `budget_line_truth = project_budget_lines`
- `commitment_truth = po_requests`
- `actual_cost_truth = external_accounting_or_governed_receipt_review`
- `operational_work_truth = project_controls_work_ledger`
- `ai_role = advisory_only`

## Guardrails displayed to operators

Both PM and admin surfaces show explicit guardrail text that:
- imports never activate automatically;
- PM approval is required;
- ambiguous rows remain in governed review;
- commitments and actuals are separate trust lines.

Testing agent report `/app/test_reports/iteration_112.json` verified this language on both surfaces.
