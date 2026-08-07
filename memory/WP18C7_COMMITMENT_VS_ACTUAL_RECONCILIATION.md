# WP18C7 Commitment vs Actual Reconciliation

## Comparison rules
- Quantity commitments compare to accepted production by linked unit.
- Hour-based support compares to resource hours observed where available.
- Amount-based commitments compare to actual amount / reviewed receipt amount.
- Due-date proximity can move a commitment to `at_risk`.
- Past-due unmet commitments move to `missed`.

## Runtime proof
- PM commitment create/update flow PASS.
- Commitment register returned updated item and lifecycle counts.
- Evidence: `/app/test_reports/iteration_155.json`
