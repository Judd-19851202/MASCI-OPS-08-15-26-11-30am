# WP18 ECAP Budget Hierarchy Constitution

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `PARTIAL_EVIDENCE` + `INFERENCE`

Budget Hierarchy is a justified `BUILD_NEW` subsystem.  
It is built **on top of** preserved upstream truth and does not replace cost codes, Daily Reports, PO workflow, or schedule.

## Core budget law

No single field named `budget` may represent multiple concepts.

The system must distinguish:

1. what was estimated
2. what was awarded
3. what was originally budgeted
4. what is currently approved
5. what is committed
6. what has actually cost
7. what has been earned
8. what remains to spend
9. what is forecast at completion
10. what is billed
11. what is collected

## Final hierarchy

| Layer | Proof label | Owner | Purpose | Notes |
|---|---|---|---|---|
| Estimate package | `PARTIAL_EVIDENCE` | estimating / precon | what was bid | source may originate outside final budget subsystem |
| Awarded contract value | `DOCUMENTED_ONLY` | executive / finance | contract award baseline | commercial cap for budget governance |
| Original budget version | `DOCUMENTED_ONLY` | project controls + finance | first approved operational budget | immutable baseline once approved |
| Current approved budget | `DOCUMENTED_ONLY` | finance / project controls | active working budget | only one current approved version |
| Pending budget revision | `DOCUMENTED_ONLY` | finance / project controls | proposed but not approved changes | not used in official rollups until approved |
| Management reserve / contingency / allowance | `DOCUMENTED_ONLY` | executive / finance | protected controlled variance pools | must not be merged into one generic field |
| Budget line | `DOCUMENTED_ONLY` | project controls | cost-code/phase/work-package level budget unit | ties to quantity, unit, resource type, and responsible scope |
| Commitment ledger | `DOCUMENTED_ONLY` | procurement + finance | committed cost tracking | fed by PO and subcontract commitments |
| Actual-cost ledger | `DOCUMENTED_ONLY` | finance/accounting | operational actual-cost truth for project controls | not a general ledger replacement |
| Forecast ledger | `DOCUMENTED_ONLY` | PM + project controls + finance | ETC/EAC and forecast changes | must reference current budget, commitments, and actuals |
| Revenue / billing / collections ledger | `DOCUMENTED_ONLY` | finance/accounting | commercial outcome tracking | may consume external accounting/ERP mirror where applicable |

## Required dimensions on every budget line

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

- company
- division
- region
- project
- contract
- phase
- work package
- cost code
- optional activity link
- cost type (`labor`, `equipment`, `material`, `subcontract`, `other_direct`, `indirect`, `overhead`)
- quantity
- unit
- responsible role
- effective date
- version / revision reference

## Ownership and locking rules

| Concept | Final owner | Approval | Locking rule | Revision rule |
|---|---|---|---|---|
| Original budget | project controls + finance | finance approver | locks at first approval | never overwritten |
| Current approved budget | finance / controller | formal approval required | exactly one active approved version | replaced only by approved revision |
| Contingency / reserve | executive + finance | executive-controlled | separate locked pools | releases tracked explicitly |
| Commitment | procurement + finance | approver workflow | locked when approved/issued | changes create adjustment history |
| Actual cost | finance/accounting | reconciliation policy | no silent overwrite | corrections are adjustments |
| Forecast | PM + controls + finance | review/approval rules by threshold | time-stamped snapshot | every change preserved |
| Revenue / billing / collection | finance/accounting | finance policy | locked by accounting events | adjustments preserved with source reference |

## Operator workflow rules

**Proof label:** `DOCUMENTED_ONLY`

1. Estimating may seed budget candidates, but does not automatically create approved budget authority.
2. PM / controls may prepare working budget mappings.
3. Finance / controller approves the official budget version.
4. PO approvals feed commitments; they do not directly rewrite budget.
5. Daily Reports feed production and operational actuals; they do not directly rewrite approved budget.
6. Forecast changes create snapshots; they do not overwrite original budget.

## Rollups

| Rollup | Final rule |
|---|---|
| Project rollup | sum by budget line across cost code / phase / work package with revision-aware effective dating |
| Division / region rollup | only from approved project budget, commitment, actual, and forecast layers |
| Portfolio rollup | only from approved/current layers plus time-stamped forecast snapshots |

## ForgedOps ownership boundary

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

ForgedOps owns:

- operational budget structure
- cost-code/project controls budget mapping
- commitments for project-controls use
- operational actual-cost model for controls and executive reporting
- forecast, EAC, and EV inputs

ForgedOps does **not** become the accounting general ledger unless separately authorized.

## Final budget distinction table

| Concept | Meaning |
|---|---|
| Bid | what was priced before award |
| Budget | approved internal cost plan |
| Commitment | obligated future spend |
| Actual | incurred recognized spend in project-controls view |
| Earned | value of approved progress performed |
| Remaining | budget or forecast left to spend / produce |
| Forecast | expected final outcome based on actuals + remaining work |
| Billed | customer invoiced value |
| Collected | cash received |

## Constitutional result

Budget Hierarchy is fully decided for WP-18C authorization.