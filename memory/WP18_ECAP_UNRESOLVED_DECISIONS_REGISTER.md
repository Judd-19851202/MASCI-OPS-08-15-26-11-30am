# WP18 ECAP Unresolved Decisions Register

Date: 2026-08-03

## Register purpose

**Proof label:** `DOCUMENTED_ONLY`

This register captures only decisions that remain legitimately deferred or conditionally required.

## Register

| Decision ID | Proof label | Decision | Status | Why not blocking now | When it becomes active |
|---|---|---|---|---|---|
| U01 | `EXECUTIVE_DECISION_REQUIRED` | whether MASCI needs a future holding-company level | `DEFER` | not required for current validated operating scope or WP-18C dependency order | only if acquisitions or corporate structure require it |
| U02 | `EXECUTIVE_DECISION_REQUIRED` | whether legal entity becomes a first-class hierarchy object instead of company metadata | `DEFER` | current ECAP can proceed with company root and finance boundaries already decided | only if accounting/ERP integration proves legal-entity separation is required |
| U03 | `EXECUTIVE_DECISION_REQUIRED` | exact external accounting/ERP connector implementation path | `DEFER` | source-of-truth boundary is already decided without naming a specific connector | becomes active before financial cutover if current accounting source cannot satisfy required exports |

## Register result

No unresolved decision currently blocks WP-18C authorization.