# WP18C3 Commitment and Actual-Cost Foundation

Date: 2026-08-03

## Constitutional result

WP-18C3 establishes commitment and actual-cost foundations **without** turning ForgedOps into the accounting ledger.

## Implemented stores

### Commitment candidates
- collection: `project_budget_commitment_candidates`
- source truth: `po_requests`
- rule: approved/closed PO Requests may generate review-only commitment candidates
- prohibition: no guessed linkage to budget lines

### Actual-cost candidates
- collection: `project_budget_actual_cost_candidates`
- source truth posture: `external_accounting_or_governed_receipt_review`
- rule: candidate receipt rows are preserved for review
- prohibition: no candidate row becomes accounting truth automatically

## Runtime evidence

### Systemwide counts at certification snapshot
- commitment candidates: `32`
- actual-cost candidates: `8`

### Certified project counts (`ZZ-RUNTIME-CERT-2026`)
- approved PO Requests: `0`
- commitment candidates visible in PM overview: `0`
- actual-cost candidates visible in PM overview: `0`

This is expected for the certification project. The foundation exists, the trust lines are separate, and no fake costs were created simply to satisfy a test.

## Why this satisfies the watch-outs

1. **No duplicate accounting**: actual cost stays external / review-governed.
2. **No financial guessing**: unresolved commitments remain queued.
3. **Future crew economics ready**: budget lines already carry labor/equipment/material/subcontract/vendor rollup fields.
4. **Materials / subcontractors / vendors stay referential**: arrays exist on the line model but were not silently backfilled.

## Open future-ready hooks retained for later authorized work

- `commitment_refs[]`
- `actual_cost_refs[]`
- `material_refs[]`
- `vendor_refs[]`
- `subcontractor_refs[]`
- later reconciliation against ERP/AP and payroll trust lines

## Non-goals still respected

- no accounting GL duplication
- no forecasting engine
- no Earned Value implementation
- no PO lifecycle replacement
