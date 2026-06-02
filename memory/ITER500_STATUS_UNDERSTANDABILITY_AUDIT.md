# ITER500 · STATUS UNDERSTANDABILITY AUDIT

**Date**: 2026-06-02T19:30 UTC
**Mode**: READ-ONLY

---

## Status taxonomy across workflows

| Workflow | Statuses in use | Confusion risk |
|---|---|:-:|
| HR Employee Lifecycle | Active · Inactive · Leave of Absence · Suspended · Resigned · Terminated · Retired · Pending Hire | 🟡 8 statuses · 5 are "not currently working" |
| Incident | open · in_review · revision · pending_closure · closed · reopened | 🟡 6 lifecycle states |
| QA/QC | open · in_review · revision · pending_closure · closed · reopened | 🟢 mirrors Incident (iter453 standardized) |
| Site Inspection | open · in_review · revision · pending_closure · closed · reopened | 🟢 mirrors above |
| Constraint | open · in-progress · resolved · closed · reopened | 🟡 distinct vocabulary vs lifecycle |
| Daily Report | draft · submitted · approved · locked | 🟡 "approved" without operator-visible step |
| JHA | draft · submitted · posted · expired · archived | 🟡 |
| Equipment Inspection | passed · pass_with_defects · failed · expired | 🟡 dual-axis status (result + freshness) |
| FleetDVIR | passed · failed | 🟢 binary |
| HR Queue Request | pending · approved · rejected · withdrawn | 🟢 |
| PO Request | draft · submitted · approved · rejected · fulfilled | 🟡 "fulfilled" not explicit in UI |
| Asset Transfer | initiated · in_transit · received · cancelled | 🟡 |
| Time-Off | requested · approved · denied · cancelled · taken | 🟡 "taken" not always set |

---

## Cross-workflow status-name overlaps causing tribal-knowledge gaps

* **"Closed"** appears across QA/QC · Inspection · Incident · Constraint · Asset Transfer (`cancelled`) — but semantically distinct.
* **"Approved"** appears across PO · Time-Off · Training records · Daily Reports (with shop-approval) · HR Queue Request — but with different actors and consequences.
* **"Reopened"** is universal across QA/QC · Inspection · Incident · Constraint — and is correctly normalized; this is one of the cleaner taxonomy choices.
* **"Expired"** vs **"Out of Date"** vs **"Stale"** — three terms across Equipment Inspection · Training Records · Driver Qualification · Site Inspection due-dates.
* **"Pending"** appears in HR Queue (pending review) · PO Request (pending approval) · Time-Off (pending) · Asset Transfer (pending receipt) — overloaded.

---

## Status visibility audit per workflow

| Workflow | Status visible in list? | Status visible in detail? | Status next-action visible? |
|---|:-:|:-:|:-:|
| HR Employee | 🟢 (badge in row + drawer header) | 🟢 | 🟢 (iter453.7+iter453.9) |
| Incident | 🟢 | 🟢 | 🟡 (next-state hinted via lifecycle panel) |
| QA/QC | 🟢 | 🟢 | 🟢 (OC-003 lifecycle panel) |
| Site Inspection | 🟢 | 🟢 | 🟢 (OC-004) |
| Constraint | 🟢 | 🟡 (no lifecycle panel · uses inline buttons) | 🟡 |
| Daily Report | 🟢 | 🟢 | 🟡 (lock vs share vs export — three CTAs without primacy) |
| JHA | 🟢 | 🟡 (poster status separate from submission status) | 🟡 |
| Equipment Inspection | 🟢 | 🟢 | 🟡 (re-inspection link via tooltip) |
| FleetDVIR | 🟢 | 🟡 | 🟡 |
| HR Queue Request | 🟢 | 🟢 (approve/reject buttons visible) | 🟢 |
| PO Request | 🟢 | 🟡 (reject reason optional) | 🟡 |
| Asset Transfer | 🟢 | 🟡 (receive ack is subtle) | 🟡 |
| Time-Off | 🟡 (table-only · no badge) | 🟡 | 🟡 |

---

## STOP
