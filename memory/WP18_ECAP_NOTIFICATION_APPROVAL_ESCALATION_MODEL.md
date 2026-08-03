# WP18 ECAP Notification, Approval, and Escalation Model

Date: 2026-08-03

## Final decision

**Decision label:** `APPROVED_CONSTITUTIONAL_DECISION`  
**Proof label:** `SOURCE_VERIFIED` + `DOCUMENTED_ONLY`

Notifications and approvals remain a shared governed system and are **not** to be rebuilt in WP-18C.

## Event classes

| Event class | Source | Approval needed? | Escalation rule |
|---|---|---|---|
| Daily reporting exception | Daily Reports / review queues | review only | PM → superintendent / ops leader if stale |
| Budget revision | budget subsystem | yes | PM / controls → finance/controller → executive by threshold |
| Commitment approval | procurement / finance | yes | approver chain by amount / scope |
| Forecast exception | forecast subsystem | threshold-based | PM → controls → finance / executive |
| EV exception | EV subsystem | review/certification by threshold | PM / controls → finance / executive |
| Safety / quality critical issue | safety / QA records | yes where closure impacts authority | escalate by severity and compliance policy |
| Qualification / eligibility block | HR / training | yes for override | manager → HR / safety / dispatch |

## Model rules

1. Notifications may inform action; they may not create authority.
2. Approval chains must follow the role decision matrix, not route-level convenience.
3. Escalation thresholds must be explicit for budget, commitment, forecast, EV, safety, and qualification events.
4. Every approval must leave an audit trail.

## Shared-system rule

The notification / approval / escalation framework is a protected shared system.  
WP-18C may only add new governed event bindings to it.