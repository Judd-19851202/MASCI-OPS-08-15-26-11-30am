# WP18 ECAP Forecasting, Commitment, and Actuals Model

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Forecasting must be built from three distinct layers:

1. commitments
2. actuals
3. remaining-work forecast

## Final model

| Layer | Final rule |
|---|---|
| Commitment | approved/issued cost obligation not yet actualized |
| Actual | recognized cost already incurred |
| Remaining work | approved expected cost to finish unperformed work |
| Forecast / ETC | commitment outlook + remaining work view where not yet actualized |
| EAC | actual cost + ETC or current approved forecast finish |

## Sources

| Input | Source owner |
|---|---|
| Commitment | PO workflow + future subcontract commitment path under budget subsystem |
| Actual labor / field cost signal | Daily Reports + payroll reconciliation + finance reconciliation |
| Actual procurement cost signal | PO receipt / invoice / accounting reconciliation path |
| Remaining work | PM / controls / finance forecast snapshot |
| Forecast history | existing forecast lineage + new budget/actual layers |

## Trust-line rules

1. Commitment does not equal actual.
2. Actual does not equal billed.
3. Forecast does not overwrite original or current approved budget.
4. Forecast snapshots are versioned and attributable.

## Executive reporting rule

Any executive forecast number must state whether it is primarily driven by:

- approved commitments
- actual recognized cost
- remaining work forecast assumptions

That explanation is mandatory in drill-down views.