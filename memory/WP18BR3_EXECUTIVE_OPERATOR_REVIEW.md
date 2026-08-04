# WP18BR3 Executive Operator Review

Date: 2026-08-03

## Purpose

Challenge the operator experience role by role and determine what helps, what slows each role down, what is unnecessary, and what is missing.

This review now also inherits the standing constitutional rule that every later feature must reduce operator work and improve downstream intelligence rather than create more paperwork.

That rule is codified in the **WP-18 Operational Intelligence Constitution**.

It is now complemented by the **WP-18 Operational Decision Engine Constitution**, including the rule that later packages must improve measurable operator and manager decisions rather than simply add more fields.

## Role review

| Role | What helps | What slows them down | What is unnecessary | What is missing |
|---|---|---|---|---|
| Executive | Executive overview, executive intelligence, operations center, ODS visibility surfaces already exist. `frontend/src/app/routing/AppRoutes.jsx:702-703,930-931,1369-1379` | Too many adjacent executive/read-side surfaces can create ambiguity. | Parallel legacy intelligence digest. | One authoritative executive reporting hierarchy with financial governance and EV. |
| Operations | Admin operations dashboard, operations control, dispatch, project health, and PM views already provide cross-domain visibility. `frontend/src/app/routing/AppRoutes.jsx:716-723,930-933` | Resource federation and reporting overlap make enterprise coordination harder than needed. | Extra overlapping dashboards telling similar stories. | One cross-domain operations view for resource/load/conflict decisions. |
| Project Manager | PM hub, command center, project schedule, Monday review, jobs, staffing, daily, incidents, photos, and safety drill-downs are already substantial. `frontend/src/app/routing/AppRoutes.jsx:878-977` | Finance and executive signal gaps force PMs to infer more than they should. | PM-facing duplicated read-only slices that do not change action. | Budget-aware but still PM-safe project controls view. |
| Superintendent | Daily report capture, field leadership, constraints, safety, trench-safety, and leadership records already reduce phone-call dependency. `frontend/src/app/routing/AppRoutes.jsx:549-575,624-675,1088-1093` | Constraints, equipment, and crew context still live across multiple surfaces. | None obviously redundant at field level. | One tighter field action queue across constraints, crew readiness, and equipment readiness. |
| Foreman | Public/field daily entry, calculators, safety forms, JHA, incidents, and leadership forms already support production capture. `frontend/src/app/routing/AppRoutes.jsx:528-575,624-648` | Split constraint and resource context makes next-best action less obvious. | None obvious. | More unified project-context feedback after submission. |
| Dispatcher | Dispatch hub, board, command map, fleet, haul ledger, and driver qualification are already strong operational surfaces. `frontend/src/app/routing/AppRoutes.jsx:1153-1192`; `frontend/src/pages/DispatchHubV2.jsx:9-20,166-184` | Resource and equipment semantics upstream are still not fully harmonized. | None inside dispatch itself; legacy duplicate launch points outside dispatch are unnecessary. | Cleaner upstream project/resource demand alignment. |
| HR | HR hub, time verification, payroll variance, time-off, training, qualifications, driver qualification, employees, safety records, and daily-report views are already mature. `frontend/src/app/routing/AppRoutes.jsx:1046-1080,1147,1270-1290` | Labor truth spans daily field capture and weekly reconciliation, so some answers still require cross-checking. | None clearly redundant. | Better enterprise labor rollups and finance-aware labor context. |
| Safety | Safety portal includes incidents, audits, documents, training, reports, employees, trench safety, inspections, and corrective actions. `frontend/src/app/routing/AppRoutes.jsx:1103-1147` | Executive reporting overlap can make safety summaries feel duplicated. | Legacy duplicated executive safety visibility lanes. | Cleaner enterprise escalation/rollup hierarchy. |
| Mechanic / Shop | Shop hub, asset care, queue, assignments, PM schedules, work orders, trench-safety repairs, and equipment views are highly specific and useful. `frontend/src/app/routing/AppRoutes.jsx:990-1030` | Asset identity is strong but external/provider edge seams still create context-switching risk. | None obvious in core shop workflow. | Even tighter equipment lifecycle continuity between field, dispatch, and shop. |
| Accounting | PO workflow, project P&L snapshot, approved amounts, and admin-only financial-adjacent surfaces exist. `backend/routes/po_requests.py:586-772`; `backend/server.py:6619-6754`; `frontend/src/app/routing/AppRoutes.jsx:813` | There is no authoritative budget, committed-cost, actual-cost, billing, revenue, cash-flow, or EV model. | Forcing accounting use through admin/PM-adjacent views long-term. | A real finance architecture with budget, actual cost, committed cost, billing/revenue, and EV. |

## BR3 operator conclusion

The platform already helps most operator roles more than it hurts them.  
The least complete operator experience belongs to:

1. executives, because reporting hierarchy is overlapping
2. accounting/finance, because finance authority is still incomplete

That is an argument for **targeted architectural amendments**, not a broad UX or platform rebuild.

It is also an argument that future packages must make operator capture lighter while making executive answers stronger.