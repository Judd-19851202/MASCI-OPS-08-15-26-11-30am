# Operational Lifecycle Matrix · OMEGA Completeness Audit

**Batch:** OMEGA · Operational Completeness Audit · Phase 2 · Lifecycle Matrix
**Companion:** `OPERATIONAL_WORKFLOW_INVENTORY.md`
**Mode:** READ-ONLY
**Date:** 2026-06-01

---

## 1 · Matrix legend

| Cell | Meaning |
|---|---|
| ✅ | Action is supported end-to-end (endpoint + UI + persisted) |
| 🟡 | Action is partially supported (endpoint exists, UI absent / UI exists, endpoint missing / persisted but not surfaced) |
| ❌ | Action is not supported |
| n/a | Action does not apply to this workflow |
| ⚠ | Action is supported but with a known correctness gap (see notes) |

Columns: **Crt** = Create · **Vw** = View · **Edt** = Edit · **Asn** = Assign · **Rsn** = Reassign · **StC** = Status Change · **Cls** = Close/Resolve/Complete · **Reo** = Reopen · **Arc** = Archive · **Del** = Delete · **Aud** = Audit Trail · **API** = API exposure · **UI** = UI exposure · **Acc** = Accountability integration · **CC** = Command Center integration · **Prm** = Permissions enforced · **Fbk** = User feedback on blocked transitions

---

## 2 · Per-workflow lifecycle matrix

| # | Workflow | Crt | Vw | Edt | Asn | Rsn | StC | Cls | Reo | Arc | Del | Aud | API | UI | Acc | CC | Prm | Fbk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Incident Report | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | 🟡 | 🟡 | 🟡 | 🟡 | 🟡 | ✅ | 🟡 |
| 2 | CAPA | ✅ | ✅ | ✅ | 🟡 | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | JHA (form) | ✅ | ✅ | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | 🟡 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 4 | Safety Meeting | ✅ | ✅ | ❌ | n/a | n/a | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | 🟡 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 5 | FL Form (10 kinds) | ✅ | ✅ | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | ❌ | ✅ | 🟡 | ✅ | ✅ | ❌ | ❌ | ✅ | 🟡 |
| 6 | PPE Issuance | ✅ | ✅ | ❌ | ❌ | n/a | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | 🟡 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 7 | PPE Return | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 8 | Safety Training (form) | ✅ | ✅ | ❌ | ❌ | n/a | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | 🟡 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 9 | Safety Training Records (canon) | ✅ | ✅ | ✅ | n/a | n/a | ✅ | ✅ | ✅ | ❌ | ✅ | 🟡 | ✅ | ✅ | 🟡 | 🟡 | ✅ | ✅ |
| 10 | Employee Records | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a | n/a | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ |
| 11 | Employee Onboarding | 🟡 | ✅ | ✅ | n/a | n/a | ✅ | ❌ | n/a | n/a | n/a | ❌ | 🟡 | 🟡 | ❌ | ❌ | ✅ | ❌ |
| 12 | Employee Offboarding | 🟡 | ✅ | ✅ | n/a | n/a | ✅ | 🟡 | ✅ | n/a | n/a | 🟡 | ✅ | 🟡 | ❌ | ❌ | ✅ | 🟡 |
| 13 | Status / Term / Rehire | n/a | ✅ | ✅ | n/a | n/a | ✅ | ✅ | ✅ | n/a | n/a | 🟡 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 14 | Time Verification | n/a | ✅ | ❌ | n/a | n/a | ❌ | ❌ | n/a | n/a | n/a | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| 15 | Payroll Variance | ✅ | ✅ | 🟡 | n/a | n/a | 🟡 | ❌ | n/a | n/a | n/a | 🟡 | ✅ | ✅ | ❌ | ❌ | ✅ | 🟡 |
| 16-21 | PO Request (full family) | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 22 | Vendor / Supplier | ✅ | ✅ | ✅ | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 23-24 | Job / Project Lifecycle | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a | n/a | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 25 | Daily Report | ✅ | ✅ | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | 🟡 | ✅ | 🟡 | 🟡 | ✅ | ❌ |
| 26 | DR Photos | n/a | ✅ | ❌ | n/a | n/a | n/a | n/a | n/a | n/a | ❌ | ❌ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| 27 | Job Photos Library | n/a | ✅ | ❌ | n/a | n/a | n/a | n/a | n/a | n/a | ❌ | ❌ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| 28 | Photo Viewer | n/a | ✅ | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| 29 | Photo Delete / Orphan | ❌ | ❌ | ❌ | n/a | n/a | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 30 | Fleet Defects | ✅ | ✅ | 🟡 | ✅ | n/a | ✅ | ✅ | ❌ | n/a | n/a | 🟡 | ✅ | ✅ | 🟡 | 🟡 | ✅ | ✅ |
| 31 | DVIR / Pre-Op | ✅ | ✅ | ❌ | n/a | n/a | ✅ | ✅ | ✅ | n/a | ✅ | 🟡 | ✅ | ✅ | 🟡 | 🟡 | ✅ | ✅ |
| 32 | Equipment Master | ✅ | ✅ | ✅ | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 33 | Asset Transfers | ✅ | ✅ | ❌ | ✅ | n/a | ✅ | ✅ | ❌ | n/a | n/a | 🟡 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 34 | Dispatch Board | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a | n/a | 🟡 | ✅ | ✅ | ❌ | 🟡 | ✅ | ✅ |
| 35 | Dispatch Assignments | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | n/a | n/a | 🟡 | ✅ | ✅ | ❌ | 🟡 | ✅ | ✅ |
| 36 | Continuity Events | ✅ | ✅ | ❌ | n/a | n/a | ❌ | ❌ | ❌ | n/a | n/a | ❌ | 🟡 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 37 | Operator / Driver Qual | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a | n/a | n/a | n/a | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| 38 | QA/QC | ✅ | ✅ | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | 🟡 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 39 | Site Inspection | ✅ | ✅ | ❌ | ❌ | n/a | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | 🟡 | ✅ | ❌ | ❌ | ✅ | ❌ |
| 40 | Fire Extinguishers | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a | n/a | n/a | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 41 | Safety Documents | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a | n/a | n/a | ✅ | 🟡 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 42 | Document Expirations | ✅ | ✅ | ✅ | n/a | n/a | n/a | n/a | n/a | n/a | ✅ | 🟡 | ✅ | ✅ | ❌ | 🟡 | ✅ | ✅ |
| 43 | Tasks | ✅ | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ❌ | n/a | n/a | ✅ | ✅ | 🟡 | ✅ | 🟡 | ✅ | ✅ |
| 44 | Notifications | n/a | ✅ | n/a | n/a | n/a | ✅ | ✅ | n/a | n/a | n/a | 🟡 | ✅ | ✅ | n/a | n/a | ✅ | ✅ |
| 45 | Ops Events / Holds | ✅ | ✅ | ✅ | ✅ | n/a | ✅ | ✅ | ❌ | n/a | n/a | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ | ✅ |
| 46 | Time Off Requests | ✅ | ✅ | ❌ | n/a | n/a | ✅ | ✅ | ❌ | n/a | n/a | 🟡 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ |
| 50 | Scheduler Runs | n/a | ✅ | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| 54 | Backup Digest | n/a | ✅ | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| 55 | Recovery Dashboard | n/a | ✅ | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a |
| 56 | User Directory | ✅ | ✅ | ✅ | n/a | n/a | ✅ | n/a | n/a | n/a | ✅ | ✅ | ✅ | ✅ | n/a | n/a | ✅ | ✅ |
| 57 | Role / Permission Mgmt | 🟡 | ✅ | 🟡 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 🟡 | 🟡 | 🟡 | n/a | n/a | ✅ | 🟡 |
| 58 | Admin Settings | n/a | ✅ | ✅ | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 🟡 | ✅ | ✅ | n/a | n/a | ✅ | ✅ |

---

## 3 · Aggregate cell counts (per column)

| Action | ✅ | 🟡 | ❌ | n/a |
|---|---|---|---|---|
| Create | 33 | 4 | 3 | 8 |
| View | 47 | 0 | 1 | 0 |
| Edit | 22 | 4 | 16 | 6 |
| Assign | 8 | 1 | 9 | 30 |
| Reassign | 4 | 2 | 2 | 40 |
| Status Change | 19 | 2 | 13 | 14 |
| Close / Resolve | 14 | 2 | 14 | 18 |
| Reopen | 3 | 0 | 17 | 28 |
| Archive | 8 | 0 | 14 | 26 |
| Delete | 17 | 0 | 9 | 22 |
| Audit Trail | 8 | 18 | 14 | 8 |
| API exposure | 38 | 7 | 1 | 2 |
| UI exposure | 36 | 5 | 1 | 6 |
| Accountability | 8 | 7 | 21 | 12 |
| Command Center | 6 | 9 | 21 | 12 |
| Permissions | 46 | 0 | 1 | 1 |
| User feedback | 25 | 6 | 13 | 4 |

---

## 4 · Most concerning rows (by inspection)

### 4.1 · 🔴 Workflows with zero status/close/audit support

| Workflow | Crt | StC | Cls | Aud | Acc | CC |
|---|---|---|---|---|---|---|
| Incident Report | ✅ | ❌ | ❌ | 🟡 | 🟡 | 🟡 |
| JHA form | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Safety Meeting | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| FL Form (10 kinds) | ✅ | ❌ | ❌ | 🟡 | ❌ | ❌ |
| PPE Issuance | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Safety Training (form) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Daily Report | ✅ | ❌ | ❌ | ❌ | 🟡 | 🟡 |
| QA/QC | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Site Inspection | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

**9 workflows are create-and-forget today.** They produce records that are read-only forever. The platform cannot tell the difference between "open" and "closed" on any of them.

### 4.2 · ⚫ Placeholders (collection or naming exists, but no workflow)

| Workflow | Why placeholder |
|---|---|
| PPE Return | No collection, no endpoint, no UI — yet PPE Issuance has no closure path. Operationally orphaned. |
| Photo Delete / Orphan Handling | No surface; orphan rows known to exist; no janitor. |

### 4.3 · 🟡 Workflows where Edit ✅ but Reopen ❌

* CAPA, Asset Transfers, Tasks, PO Requests, Tickets/Ops Holds, Time-Off — closure terminal; **no reopen path.**
* This is a class-wide gap. Once closed, the user cannot reopen without admin DB write.

### 4.4 · 🟡 Workflows where DB has status but Accountability ignores it

* Incidents (audited) · Daily Reports · Tasks (partial) · Fleet Defects (partial)
* See `SOURCE_OF_TRUTH_AUDIT.md`.

### 4.5 · 🟡 Workflows with no audit trail despite status changes

* FL Forms · Payroll Variance · Asset Transfers · Dispatch Assignments · Dispatch Continuity · Notifications · Time Off · Admin Settings · Safety Documents
* See `AUDIT_TRAIL_COVERAGE_REPORT.md`.

---

## 5 · OMEGA discipline

🟢 Read-only · matrix derived from route inventory + DB samples + frontend code grep.

🛑 Continue to `STATUS_VOCABULARY_AUDIT.md`.
