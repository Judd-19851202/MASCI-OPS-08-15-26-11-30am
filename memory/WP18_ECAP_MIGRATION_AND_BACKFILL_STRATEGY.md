# WP18 ECAP Migration and Backfill Strategy

Date: 2026-08-03

## Final migration law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

No big-bang rewrite. No destructive migration without recovery evidence.

## Strategy

1. **Additive schema strategy** — new budget and EV structures are additive first.
2. **Backward compatibility** — current readers and workflows continue during staged rollout.
3. **Shadow calculations** — budget, forecast, and EV run in parallel until reconciled.
4. **Dual-read periods** — executive and PM readers may compare legacy and new governed outputs during controlled transition.
5. **Deterministic backfill** — historical budget/actual/quantity mappings must be reproducible from preserved sources and versioned assumptions.
6. **Exception queues** — ambiguous historical mappings go to review, never silent defaults.
7. **Rollback** — every WP-18C package must define rollback to prior governed state.

## Historical truth protection

Daily Reports, payroll variance, PO approvals, cost-code planning history, and schedule revisions must retain historical records.  
No silent recalculation of historical financial truth is allowed.

## Final result

Migration/backfill strategy is fully decided and supports WP-18C authorization.