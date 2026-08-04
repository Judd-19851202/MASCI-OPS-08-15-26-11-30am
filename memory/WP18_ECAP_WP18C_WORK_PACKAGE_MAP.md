# WP18 ECAP WP-18C Work Package Map

Date: 2026-08-03

## Final work-package contract

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `DOCUMENTED_ONLY`

Every work package in this map inherits the WP-17 Product Constitution, the WP-18 ECAP, and the WP-18 Operational Intelligence Constitution. Compliance is mandatory.

No package in this map is complete if it only captures or stores data without creating downstream operational reuse, intelligence value, reduced operator burden where applicable, or increased executive visibility where applicable.

### WP-18C1 — Enterprise Hierarchy Foundation
- objective: propagate the accepted hierarchy and inheritance model
- preserved systems: governance registry, portals, permissions
- changed systems: hierarchy consumption points only
- exclusions: no finance logic, no EV
- rollback: revert to prior scope resolution and mappings

### WP-18C2 — Authority and Source-of-Truth Enforcement
- objective: lock truth owners, resource federation, approvals, notifications, escalation rules
- preserved systems: governance / approvals / current portals
- exclusions: no budget math yet
- rollback: prior authority mapping and event bindings

### WP-18C3 — Budget Hierarchy Foundation
- objective: original/current/revised budget, commitments, actual-cost trust, revenue/billing/collection structure
- preserved systems: cost-code library, Daily Reports, PO workflow, P&L inputs
- exclusions: no EV yet
- rollback: additive disable of new budget layers

### WP-18C4 — Cost-Code and Estimate Mapping
- objective: connect estimate/bid/budget/cost-code mappings cleanly
- preserved systems: existing cost-code architecture
- exclusions: no shell redesign
- rollback: disable mapping layer and retain current planning state

### WP-18C5 — Project Controls Schedule / Actuals Spine
- objective: govern Daily Report → quantity/progress → schedule/constraint flow
- preserved systems: schedule engine, Daily Reports, lookahead paths
- exclusions: no standalone new schedule engine
- rollback: restore prior progress synchronization path

### WP-18C6 — Production and Quantity Intelligence
- objective: accepted quantity, productivity, cost-per-unit, approved production truth
- preserved systems: Daily Reports, QA/QC, PM shell
- exclusions: no duplicate production system
- rollback: disable accepted-quantity layer and derived readers

### WP-18C7 — Forecasting and Commitments
- objective: ETC/EAC, commitments, forecast rollups
- preserved systems: PO workflow, forecast lineage, PM reviews
- exclusions: no EV before ready
- rollback: disable new forecast/commitment derived views

### WP-18C8 — Earned Value Engine
- objective: implement approved EV formulas and exception handling
- preserved systems: budget, schedule, quantity, actual-cost layers
- exclusions: no independent EV data-entry workflow
- rollback: disable EV outputs and preserve source systems

### WP-18C9 — Executive and Portfolio Intelligence
- objective: final reporting hierarchy, KPI dictionary, executive rollups, legacy digest retirement
- preserved systems: ODS, Project Health, KPI patterns, shells
- exclusions: no new hidden reader stack
- rollback: retain existing read surfaces while disabling new hierarchy outputs

### WP-18C10 — Migration, Backfill, Reconciliation, and Certification
- objective: backfill, shadow comparisons, cutover, acceptance, rollback proof
- preserved systems: all authoritative historical records
- exclusions: no destructive historical rewrite
- rollback: full reversion to pre-cutover behavior and readers