# WP18 ECAP Project Controls Operating Model

Date: 2026-08-03

## Final operating model decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Project Controls in ForgedOps is one operating model connecting:

- estimate
- budget
- cost codes
- CPM / schedule activity
- lookahead
- Daily Reports
- quantities
- labor / equipment / materials
- commitments
- QA/QC and safety constraints
- project constraints
- forecasts
- earned value
- executive reporting

It is not approved to become a larger data-entry burden.
Every later Project Controls package must reduce operator effort while increasing operational understanding.
Work Blocks and governed metrics should progressively become the digital heart and governed metric engine for later control decisions.

This requirement is carried by the **WP-18 Operational Decision Engine Constitution**.

## Weekly cadence

| Day / step | Owner | Required actions | Approval / output |
|---|---|---|---|
| Daily field close | foreman / superintendent | submit Daily Reports, quantities, delays, crew/equipment, field constraints | PM review queue updated |
| Daily controls sync | PM / project engineer | review Daily Report exceptions, candidate progress, missing cost-code mappings | schedule/quantity review queue updated |
| Weekly labor reconciliation | HR / payroll / PM | review payroll variance and unresolved labor anomalies | approved or escalated labor exception state |
| Weekly commitment review | PM / procurement / finance | review approved/unapproved commitments and receipt gaps | commitment ledger updated |
| Weekly production / progress review | PM / superintendent / controls | certify accepted quantity, percent complete, schedule progress, standing constraints | forecast/EV candidate update allowed |
| Weekly forecast review | PM / controls / finance | update ETC/EAC assumptions and forecast snapshots | reviewed forecast state |
| Monday review | PM / ops / executive audience | review budget, schedule, production, constraints, commitments, forecast, EV exceptions | executive actions / escalations / return path |

## Operating law

1. Daily Reports originate field truth.
2. PM / controls certify what becomes schedule, forecast, and EV truth.
3. Finance / controller certify budget and actual-cost truth.
4. Executive readers summarize; they do not change authority.

## Locking and roll-forward rules

| Object | Lock / roll-forward rule |
|---|---|
| original budget | never overwritten |
| approved budget revision | additive version with effective date |
| weekly lookahead | versioned by week and linked to current schedule state |
| Daily Report | immutable submitted record plus governed corrections |
| accepted quantity | correction history retained; no silent overwrite |
| forecast snapshot | time-stamped and preserved |
| EV snapshot | time-stamped and preserved |

## Operator reality rule

**Proof label:** `DOCUMENTED_ONLY`

The operating model is approved only because it works for:

- a superintendent completing field updates
- a PM reviewing progress and commitments
- finance validating cost truth
- executive leadership seeing one governed outcome

Anything that adds operator burden without improving trust violates ECAP.

Anything that captures data without creating downstream operational or executive value violates the Operational Intelligence Constitution.