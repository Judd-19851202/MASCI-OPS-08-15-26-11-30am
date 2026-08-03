# WP18 ECAP Cost Code and Cost Trust Architecture

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

The existing cost-code architecture is preserved and extended into a final cost-trust model.

## Final cost-code architecture

| Layer | Proof label | Final rule |
|---|---|---|
| Enterprise cost-code library | `SOURCE_VERIFIED` | `cost_code_registry` remains the reusable enterprise definition source |
| Project-specific activation | `SOURCE_VERIFIED` | projects activate and map cost codes through `jobs_master.assigned_cost_codes` |
| Estimate-to-budget mapping | `DOCUMENTED_ONLY` | mapping layer attaches estimate packages and bid items to budget lines without replacing the cost-code library |
| Alias handling | `DOCUMENTED_ONLY` | aliases must map to one canonical enterprise cost code; no duplicate cost meaning |
| Cost transaction binding | `DOCUMENTED_ONLY` | every financial or operational transaction must carry project, cost code, date, quantity/unit where applicable, and source confidence |

## Cost categories

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

Every cost line and cost transaction must classify into one of:

- labor
- equipment
- material
- subcontract
- other direct cost
- indirect cost
- overhead
- revenue adjustment only where explicitly commercial

## Final trust-line bindings

| Relationship | Final rule |
|---|---|
| Cost code ↔ budget line | one canonical mapping, version-aware |
| Cost code ↔ schedule activity | optional but governed link through activity IDs |
| Cost code ↔ Daily Report quantity | required where production is quantity-based |
| Cost code ↔ payroll/time | labor transactions roll through cost-code and project context |
| Cost code ↔ PO | commitments map to cost code / phase / work package |
| Cost code ↔ equipment use | equipment deployment or utilization cost maps to cost code where applicable |
| Cost code ↔ QA/QC / Safety | only where the event has explicit financial or production consequence |

## Required transaction fields

**Proof label:** `DOCUMENTED_ONLY`

Every cost-related transaction record used by project controls must resolve:

- source system
- authoritative record id
- project
- contract / phase / work package where available
- cost code
- date
- quantity
- unit
- amount
- resource or actor (`employee`, `equipment`, `vendor`, `material line`)
- confidence
- reconciliation status
- adjustment history

## ForgedOps vs accounting / payroll / ERP

| Concept | ForgedOps owns | External accounting / payroll / ERP owns |
|---|---|---|
| operational cost-code model | yes | no |
| project planning and mapping | yes | no |
| field production quantities | yes | no |
| operational labor, equipment, material, and commitment linkage | yes | no |
| general ledger final posting | no | yes or future explicit authorization |
| payroll system of record | no | payroll / HR system of record |
| final collections ledger | no by default | accounting / ERP unless explicitly authorized |

## Constitutional result

The cost-code architecture is preserved; cost trust is extended by explicit transaction and ownership rules rather than by replacing current cost-code foundations.