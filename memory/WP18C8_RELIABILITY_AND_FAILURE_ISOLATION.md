# WP-18C8 Reliability and Failure Isolation

Date: 2026-08-07
Result: PASS

## Failure-isolation behaviors delivered

- Snapshot cache isolates the operator-facing read path from always forcing a full recomputation.
- Fingerprinted versioning prevents duplicate version churn when nothing materially changed.
- Missing data becomes `blocked`, `partial`, or `review_required` instead of throwing a user-facing crash.
- Receipt/accounting uncertainty is preserved as a trust note instead of being promoted to final truth.
- C8 writes only additive snapshot/version records plus governed budget candidate review updates.

## Runtime incidents found during implementation and final disposition

1. **Snapshot upsert missing `project_number`**
   - Symptom: duplicate-key failure on snapshot collection after first write.
   - Repair: added top-level `project_number` and cleaned legacy null-key rows.
   - Result: closed.

2. **Budget candidate sync could erase approved linkage**
   - Symptom: overview refresh could reset approved review state.
   - Repair: preserved allocations/review fields and only downgrade on source-amount mismatch.
   - Result: closed.

3. **Commitment candidate disappeared after receipt-status advance**
   - Symptom: approved PO dropped out of commitment sync once receipt was uploaded.
   - Repair: expanded eligible PO statuses through the commitment lifecycle.
   - Result: closed.

4. **First route visit could need manual refresh**
   - Symptom: PM/Admin C8 pages could stay on first-load waiting state.
   - Repair: added a one-shot retry on initial mount.
   - Result: closed.

5. **Quantity lineage could miss active budget line when activity IDs drifted**
   - Symptom: approved actuals existed, but EV stayed blocked on the active line.
   - Repair: added planned-link fallback by cost code + work package + pay item lineage.
   - Result: closed.

## Restart / reload result

- Backend hot reload and supervisor restart both recovered successfully during implementation.
- C8 failures did not require database rollback or cross-package rework.

## Final result

No open C8 reliability blocker remained at closeout.