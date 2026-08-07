# WP18C7 Material & Vendor Commitment Evidence

## Authority
- `project_budget_authority` commitment candidates
- `project_budget_authority` actual-cost candidates

## C7 behavior
- PO-derived commitments are surfaced as read-only `vendor_subcontractor` commitment rows.
- Review status and trust line are preserved.
- Actual amount comparison uses reviewed receipt candidate evidence when present.

## Guardrail
- No PO-derived row is rewritten into the manual operator collection.

## Runtime proof
- Admin/PM workspace payload includes commitment exposure and commitment item lanes.
