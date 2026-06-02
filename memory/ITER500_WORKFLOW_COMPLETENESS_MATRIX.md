# ITER500 · WORKFLOW COMPLETENESS MATRIX

**Date**: 2026-06-02T19:30 UTC
**Scope**: 147 pages · 254 routes · 12 functional domains · 12 personas
**Mode**: READ-ONLY · code-path scan + prior-audit synthesis

---

## Domain coverage matrix

| Domain | Routes/Pages | Persona owner | Workflow status | Notable risk |
|---|---:|---|:-:|---|
| HR (lifecycle, queue, accountability) | 19 / 14 | HR Manager | 🟢 | iter453.7/.9 just fixed save UX (this audit cycle) |
| Safety (incidents, JHA, meetings) | 18 / 11 | Safety Lead / Foreman | 🟡 | Lifecycle "Reopen" path discoverable only on detail page |
| Operations (Dispatch, Fleet, Equipment) | 25 / 14 | Dispatch / PM | 🟡 | Dispatch board approvals lack explicit OLD→NEW confirmation |
| Payroll (variance, time verification, time off) | 5 / 4 | HR Payroll | 🟡 | Time-off approval is a checkbox table with no explicit "Approve" verb |
| Fleet (DVIR, weekly emergency/lead) | 8 / 3 | Driver / Dispatch | 🟡 | DVIR submission confirmation page bare-minimum text |
| Equipment (inspections, transfers) | 9 / 5 | Shop / Field | 🟢 | New inspection wizard has clear Save with success toast |
| Shop (equipment maintenance) | 6 / 3 | Shop Foreman | 🟡 | Asset-transfer "received" acknowledgement uses subtle checkbox |
| Training (records, videos, ops-training) | 8 / 6 | HR / Safety | 🟢 | Training-record edit forms have save buttons in standard dialogs |
| JHP (plans, posters) | 5 / 3 | Safety / Field | 🔴 | OC-005 acknowledgement ledger is NOT YET BUILT (iter454 backlog) |
| QA/QC + Site Inspections | 14 / 8 | PM / QC | 🟢 | iter453 OC-003/OC-004 lifecycle panels live + audit drawer wired |
| Daily Reports | 8 / 5 | Foreman / PM | 🟢 | New daily report wizard has clear Submit + share/lock flow |
| Incidents | 8 / 5 | Safety / HR | 🟡 | Incident closure has lifecycle panel but "Reopen reason" still hidden under collapsed card on some viewports |
| Constraints | 4 / 3 | PM | 🟢 | NewConstraint has Save · detail page has lifecycle controls |
| Field Leadership Portal | 9 / 6 | Foreman | 🟢 | Portal-specific forms each have Submit with confirmation page |
| Sub/Vendor Management | 3 / 2 | PM | 🟡 | Supplier list has add-new but no closure / archive workflow |
| Project Management (PO requests, project health) | 8 / 5 | PM / Exec | 🟡 | PO-requests has approve/reject but reject reason is not required-by-default |
| Accountability / Command Center | 5 / 3 | Admin / Exec | 🟡 | Accountability timeline is read-only; "drill down" via tooltip not obvious |
| Admin (governance, audit, system health) | 70+ / 35+ | Admin only | 🟢 | Admin pages are super-user surfaces; tribal-knowledge by design |

---

## Operational completeness by phase

| Phase | Status |
|---|:-:|
| Find — can user locate the workflow entry? | 🟡 (Hub.jsx has 587 lines · many tiles; some flows deep-nested) |
| Understand — is the verb/label clear? | 🟡 (some "Submit" vs "Save" vs "Create" inconsistencies) |
| Start — can user begin the workflow? | 🟢 (every "New X" page wires to a clear form) |
| Complete — can user reach a success state? | 🟢 (post-iter453.9 for HR; other domains varied) |
| Confirm — can user tell it succeeded? | 🟡 (HR now 🟢; Dispatch, Fleet, Payroll still bottom-right toast only) |
| Reopen — can user revert/correct? | 🟡 (Incident reopen exists but discoverability poor; HR reactivate has separate dialog — UX surprise) |
| Recover — can user undo a mistake? | 🔴 (most workflows have no undo · status_history audit trail exists but no in-app undo button) |

---

## Workflow-completion percentage estimate

Out of approximately **84 distinct workflows** across the 12 domains, the inventory rates:

| Tier | Count | Examples |
|---:|---|---|
| 🟢 Operationally complete (all 6 stages green) | ~ 46 | HR lifecycle (post-iter453.9), QA/QC lifecycle, Site Inspection lifecycle, Daily Report submit, Equipment inspection submit, JHA submit |
| 🟡 Operationally functional with friction | ~ 28 | Dispatch board approvals, Payroll time-off, PO-requests approval, Asset-transfer receive, Incident reopen, Sub/Vendor management |
| 🔴 Operationally incomplete | ~ 10 | OC-005 JHP ack ledger (not built), undo paths universally, FleetDVIR "post-submit can I edit?", several admin batch operations |

**Workflow Completion %** = 46 / 84 ≈ **55 %** fully complete · 28 / 84 ≈ **33 %** functional-with-friction · 10 / 84 ≈ **12 %** incomplete

---

## STOP
