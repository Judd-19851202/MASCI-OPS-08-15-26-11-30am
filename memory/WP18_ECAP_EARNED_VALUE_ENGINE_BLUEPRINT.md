# WP18 ECAP Earned Value Engine Blueprint

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `NOT_FOUND` + `INFERENCE`

Earned Value is the second and final justified `BUILD_NEW` subsystem.

## EV engine law

EV may not be claimed where the platform only has budget-versus-actual reporting.  
EV becomes active only where inputs meet the data-quality rules below.

## Core formulas

| Metric | Formula | Proof label |
|---|---|---|
| BAC | approved current budget at the selected grain | `DOCUMENTED_ONLY` |
| PV | time-phased approved budget planned to be earned by status date | `DOCUMENTED_ONLY` |
| EV | approved percent complete × BAC or approved earned quantity × budget unit value | `DOCUMENTED_ONLY` |
| AC | actual recognized cost at same grain / cutoff | `DOCUMENTED_ONLY` |
| CV | EV - AC | `DOCUMENTED_ONLY` |
| SV | EV - PV | `DOCUMENTED_ONLY` |
| CPI | EV / AC | `DOCUMENTED_ONLY` |
| SPI | EV / PV | `DOCUMENTED_ONLY` |
| ETC | EAC - AC or approved remaining-work forecast | `DOCUMENTED_ONLY` |
| EAC | approved forecast completion cost | `DOCUMENTED_ONLY` |
| TCPI | (BAC - EV) / (BAC - AC) or approved target variant | `DOCUMENTED_ONLY` |

## Final EV method hierarchy

| Method | Use rule |
|---|---|
| Quantity-based EV | primary where a cost code or work package has governed planned and accepted quantity |
| Production-based EV | use where output quantity and production conversion are the best operational truth |
| Schedule-based EV | fallback where quantity is unavailable but approved physical percent complete exists |
| Cost-code-level EV | minimum required controllable grain |
| Phase-level EV | derived rollup only |
| Project-level EV | derived rollup only |
| Portfolio-level EV | derived rollup only |

## Input architecture

| Input | Final source |
|---|---|
| Planned Value seed | Budget Hierarchy + time-phased schedule baseline |
| Earned quantity / percent complete | approved production / quantity / schedule progress model |
| Actual Cost | budget actual-cost layer with payroll / procurement / other reconciled inputs |
| Progress approval | PM / superintendent / project controls governance |
| Schedule baseline and forecast dates | schedule architecture |

## Data-quality and confidence rules

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

1. EV must publish a confidence state by grain.
2. If quantity is missing, EV must fall back only to an approved schedule/physical-percent rule.
3. If AC is incomplete, EV must show partial or blocked confidence, not fake precision.
4. Corrected Daily Reports, cost adjustments, or schedule revisions must recalculate EV through a versioned event trail.

## Daily Reports contribution rule

Daily Reports contribute:

- installed quantity
- labor hours
- equipment hours
- delays / constraints
- candidate actual start / finish evidence

Daily Reports do **not** directly certify EV.  
They feed the approved quantity, progress, and actual-cost layers that certify EV.

## Exception handling

| Situation | Engine response |
|---|---|
| incomplete actual cost | publish EV with constrained confidence or block affected CPI outputs |
| revised budget | preserve prior snapshots and recalculate using the active approved budget version |
| corrected quantity | preserve correction history and recalculate EV from corrected accepted quantity |
| schedule revision | preserve baseline and current/forecast states separately |

## Final EV determination

Earned Value is fully decided for WP-18C authorization and remains gated by Budget Hierarchy completion in sequence.