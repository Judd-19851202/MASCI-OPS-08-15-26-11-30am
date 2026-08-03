# WP18 ECAP Cross-System Interaction Map

Date: 2026-08-03

## Interaction law

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

No cross-domain event may produce uncontrolled side effects.

Every major event must define:

- producer
- authoritative event record
- consumers
- records updated
- approvals
- notifications
- KPI / financial / schedule impact
- retry and idempotency behavior

Authoritative event ledger: `WP18_ECAP_EVENT_AND_DATA_FLOW_REGISTER.csv`

## Final map by domain

| Producer domain | Primary authoritative record | Main consumers | Guardrail |
|---|---|---|---|
| Daily field reporting | `daily_reports` | schedule, payroll variance, production, Project Controls, executive readers | Daily Reports feed truth; they do not silently overwrite schedule or budget |
| Procurement / PO | `po_requests` | commitments, Project Health, budget, executive reporting | procurement feeds commitment truth; it does not become budget authority |
| Governance / approvals | governance ledgers | permissions, notifications, audit, admin readers | approval audit remains authoritative |
| Shop / equipment | Asset Spine + shop records | dispatch, maintenance, executive reporting | provider-local mapping never outranks registry identity |
| Safety / QA | domain records | project controls, executive reporting, operator alerts | only explicit financial/schedule consequences may cross into controls |
| Forecast / EV | budget + schedule + production + actual-cost layers | PM, controls, executive readers | derived models may summarize truth; they do not replace upstream owners |

## Interaction result

Cross-system interaction is fully decided for WP-18C.  
Implementation must conform to the authoritative event register.