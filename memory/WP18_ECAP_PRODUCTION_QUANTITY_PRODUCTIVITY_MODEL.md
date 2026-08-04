# WP18 ECAP Production, Quantity, and Productivity Model

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Production and quantity truth remains rooted in Daily Reports and approved downstream certification.

Production capture is constitutionally justified only when it creates downstream operational intelligence, automation, or executive understanding.

This requirement is carried by the **WP-18 Operational Intelligence Constitution**.

It is also carried by the **WP-18 Operational Decision Engine Constitution**, which requires one governed metric engine rather than competing productivity or production calculations.

## Canonical terms

| Term | Final meaning |
|---|---|
| Planned quantity | quantity planned for a budget line / work package / activity |
| Installed quantity | field-reported quantity placed or completed |
| Accepted quantity | quantity accepted for project-controls, billing, and EV use |
| Rejected quantity | quantity not accepted due to QA/QC or error |
| Rework quantity | quantity requiring rework or non-credit redo |
| Crew hours | labor hours attached to production context |
| Equipment hours | equipment effort attached to production context |
| Production rate | quantity per labor/equipment/time unit |
| Productivity | actual rate relative to target rate or budgeted production assumption |
| Cost per unit | actual or forecast cost divided by accepted quantity |
| Earned quantity | accepted quantity eligible for EV conversion |
| Remaining quantity | planned minus accepted quantity |

## Source and approval rules

| Concept | Source | Approval rule |
|---|---|---|
| Installed quantity | Daily Reports | field-originated, PM/controls reviewed |
| Accepted quantity | Daily Reports + QA/QC + PM/controls | must be certified before budget/EV rollups |
| Rejected / rework quantity | QA/QC and PM governance | retained separately; never silently netted out |
| Rate and productivity | derived from quantity plus hours / cost | calculated, not manually invented |

## Duplicate prevention rules

**Proof label:** `DOCUMENTED_ONLY`

1. One accepted quantity record path per cost-code / activity / date grain.
2. Rework is stored explicitly, not hidden in revised totals.
3. Billing and EV consume only accepted quantity, not raw installed quantity unless explicitly approved.

## Relationship rules

| Relationship | Final rule |
|---|---|
| Daily Reports ↔ production truth | Daily Reports originate candidate production facts |
| QA/QC ↔ accepted quantity | QA/QC may confirm, reject, or condition acceptance |
| Production ↔ schedule progress | approved quantity informs activity progress |
| Production ↔ billing | only accepted billable quantity feeds billing logic |
| Production ↔ EV | only accepted earned quantity feeds quantity-based EV |

## Productivity law

Productivity must always be explainable from:

- quantity
- hours and/or cost basis
- target rate or budget assumption
- confidence state

No unexplained productivity number is allowed.

No production-capture feature is complete until it creates downstream value beyond storing quantity rows.