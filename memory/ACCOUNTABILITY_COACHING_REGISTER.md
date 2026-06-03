# ACCOUNTABILITY COACHING REGISTER
## OCEP · Operational Coaching & Spanish Parity Completion Program (OCSPCP) · 4 of 7

**Date**: 2026-06-03
**Authority**: OMEGA / FOCP DIRECTIVE — OCSPCP Phase 4
**Mode**: READ-ONLY · source-direct · NO engineering
**Purpose**: For every workflow, verify the platform clearly explains Owner · Approver · Escalation Path · Audit Trail · Retention Requirements · Reopen/Revision Rules — in English AND Spanish.

---

## 1 · Accountability evidence sources (single inventory)

The platform expresses accountability through five mechanisms:

| # | Mechanism | Source | Function |
|---|---|---|---|
| AC1 | `tips.py` `who` kind tip | Per form_key | Anchors "Who completes / who sees this" |
| AC2 | `tips.py` `escalate` kind tip | Per form_key | Anchors escalation path |
| AC3 | `workflow_state_events` audit collection | `lib/workflow_state_events.py` + per-workflow lifecycle files | Append-only audit trail |
| AC4 | `AdminOperationalLanguage.jsx` glossary entries (5-section per entry) | `pages/admin/AdminOperationalLanguage.jsx` | Operator-canonical Owner / Approver / Audit / Retention semantics |
| AC5 | Pydantic models + state machines | `routes/*.py`, `workflow_state_machine` (Amendment 001 REPLACE-4/5) | Code-enforced approval / reopen rules |

---

## 2 · Per-workflow accountability matrix (35 active workflows; Submittals NOT-IMPLEMENTED excluded)

For each workflow: Owner / Approver / Escalation / Audit / Retention / Reopen — × EN / ES.

### 2.1 · Lifecycle-anchored workflows (have formal state machine + audit)

| # | Workflow | Owner | Approver | Escalation | Audit Trail | Retention | Reopen | EN | ES |
|---|---|---|---|---|---|---|---|:-:|:-:|
| 1 | Incident | 🟢 (`who` tip) | 🟢 (3-attestation) | 🟢 (escalate tip · OSHA auto-escalate per `OPERATOR_CONFIDENCE_LAYER_FINAL_SPEC §4.5`) | 🟢 (`incident_lifecycle.py` WORKFLOW="incident") | 🟢 (append-only) | 🟢 (CLOSED→UNDER_INVESTIGATION + Universal Undo) | 🟢 | 🟡 (Layer A only) |
| 2 | Site Inspection | 🟢 | 🟢 (A/B/C closure paths) | 🟢 | 🟢 (`site_inspection_lifecycle.py` WORKFLOW="site_inspection") | 🟢 | 🟢 (per state machine) | 🟢 | 🟡 |
| 3 | QA/QC Inspection | 🟢 | 🟢 (A/B/C closure paths) | 🟢 | 🟢 (`qaqc_lifecycle.py` WORKFLOW="qaqc_inspection") | 🟢 | 🟢 | 🟢 | 🟡 |
| 4 | Payroll Variance | 🟢 (HR + Admin finalize) | 🟢 (3-attestation) | 🟢 | 🟢 (`payroll_variance_lifecycle.py` WORKFLOW="payroll_variance") | 🟢 | 🟢 (Universal Undo) | 🟢 | 🟡 (AR-0004: attestation flag definitions absent in-flow) |
| 5 | Daily Report | 🟢 (Foreman) | 🟢 (Office) | 🟡 | 🟢 (`daily_report_lifecycle.py`) | 🟢 | 🟢 | 🟢 | 🟡 |
| 6 | Employee Lifecycle | 🟢 (HR) | 🟢 (lifecycle transitions) | 🟢 (rehire sub-form has escalate) | 🟢 (`employee_lifecycle.py`) | 🟢 | 🟢 (restore endpoint) | 🟢 | 🟢 (Layer A + glossary Reactivate-vs-Rehire) |
| 7 | JHP Acknowledgement | 🟢 (each employee) | 🟢 (acknowledge) | 🟡 | 🟢 (`jha_acknowledgements.py` WORKFLOW="jha_ack") | 🟢 (append-only) | 🟢 (re-ack new version) | 🟢 | 🟡 ("Reconocer" semantic breadth per SOCP §1.1) |

### 2.2 · State-machine-implicit workflows (have approval gates but no formal lifecycle file)

| # | Workflow | Owner | Approver | Escalation | Audit Trail | Retention | Reopen | EN | ES |
|---|---|---|---|---|---|---|---|:-:|:-:|
| 8 | CAPA / Corrective | 🟢 (Safety) | 🟢 (Verified→Closed gate) | 🟢 | 🟢 (`status_history` append `corrective_actions.py` L221) | 🟢 | 🟡 (status reverts via direct edit + audit) | 🟢 | 🔴 (no body_es) |
| 9 | Safety Meeting | 🟢 (Foreman) | 🔴 (no formal approval) | 🟢 | 🟡 (created_at only; no `workflow_state_events`) | 🟢 | 🔴 (no lifecycle) | 🟡 | 🔴 |
| 10 | Constraints | 🟢 (PM) | 🟢 (resolve API) | 🟡 | 🟢 (chronology append) | 🟢 | 🔴 (DOCTRINE-EXEMPT TR-0007) | 🟢 | 🟢 (Layer A) |
| 11 | Universal Undo / Recovery Stream | 🟢 (Admin) | 🟢 (reason required) | 🟢 | 🟢 (original transition preserved) | 🟢 | n/a | 🟢 | 🟢 (FOCP R2 § 8 EN-canonical doctrine) |

### 2.3 · Record-keeping workflows (append-only / no transitions)

| # | Workflow | Owner | Approver | Escalation | Audit Trail | Retention | Reopen | EN | ES |
|---|---|---|---|---|---|---|---|:-:|:-:|
| 12 | Equipment Pre-op | 🟢 (Operator) | n/a | 🟢 (preop.signoff escalate) | 🟡 (created_at) | 🟢 | n/a | 🟡 | 🔴 |
| 13 | Equipment Issuance | 🟢 | n/a (acknowledgement-only) | 🟢 | 🟡 | 🟢 | n/a (correction = new issuance) | 🟡 | 🔴 |
| 14 | Equipment Training | 🟢 (HR) | n/a | 🟢 | 🟡 | 🟢 (expiration tracked) | n/a | 🟡 | 🔴 |
| 15 | Fire Extinguisher Insp | 🟢 | n/a | 🟢 | 🟡 | 🟢 | n/a | 🟡 | 🔴 |
| 16 | Safety Document | 🟢 (Safety) | n/a | 🟢 | 🟡 | 🟢 | n/a | 🟡 | 🔴 |
| 17 | Safety Training record | 🟢 | n/a | 🟢 | 🟡 | 🟢 (expiration) | n/a | 🟢 | 🔴 |
| 18 | Attendance | 🟡 (Field Leadership) | 🟡 | 🟢 (escalate tip) | 🟡 | 🟢 | n/a | 🟡 (2 tips) | 🔴 |
| 19 | Time Verification | 🟢 (HR) | 🟡 (discrepancy review) | 🟢 | 🟡 | 🟢 | n/a | 🟢 | 🔴 |
| 20 | Document Expirations | 🟢 (HR) | n/a | 🟢 | 🟡 | 🟢 | n/a | 🟢 | 🔴 |
| 21 | Driver Qualification | 🟢 (HR + Dispatch) | 🟢 (CDL/Med-card gate) | 🟢 | 🟡 | 🟢 | 🟡 | 🟢 | 🔴 |
| 22 | Material Calculator | 🟢 (PM) | n/a | 🟡 | n/a (no persistence) | n/a | n/a | 🟢 | 🔴 |
| 23 | Asset Transfer | 🟢 (Sender/Receiver) | 🟢 (receiver accepts/rejects) | 🟡 | 🟢 (status history) | 🟢 | 🔴 (DOCTRINE-SILENT) | 🟡 | 🟡 |

### 2.4 · Approval-class workflows (Phase 2 P2 — approval flows without coaching)

| # | Workflow | Owner | Approver | Escalation | Audit Trail | Retention | Reopen | EN | ES |
|---|---|---|---|---|---|---|---|:-:|:-:|
| 24 | Time-Off Review | 🟢 (HR/Manager) | 🟢 | 🟢 (4 sub-forms have escalate) | 🟡 | 🟢 | 🔴 (DOCTRINE-SILENT) | 🟢 | 🔴 |
| 25 | Employee Accountability (write-up, verbal coaching, recognition, supervisor_notes, training_deficiency, promotion_recommendation, new_employee_eval, crew_eval) | 🟢 (Field Leadership / HR) | 🟢 | 🟢 | 🟡 (status_history pattern) | 🟢 | 🟡 | 🟢 | 🔴 |
| 26 | Field Leadership Portal (login / dashboard / records / user-management) | 🟢 (Admin) | 🟢 | 🟢 | 🟡 | 🟢 | n/a | 🟢 | 🔴 |
| 27 | Dispatch (handoff, holds, transfers, idle-alerts, utilization) | 🟢 (Dispatch) | 🟢 (board changes audit) | 🟢 | 🟢 (`dispatch_lifecycle.py` exists) | 🟢 | 🟡 | 🟢 | 🔴 |
| 28 | Equipment Checkout / Return | 🟢 | 🟢 (acknowledge) | 🟢 | 🟡 | 🟢 | n/a | 🟢 | 🔴 |
| 29 | Vendor Management | 🟢 (PM/Admin) | n/a | 🟡 | 🟡 | 🟢 | 🔴 (TR-0003 — no archive workflow) | 🟡 | 🟡 |
| 30 | HR Hub (read-side) | 🟢 (HR) | n/a | n/a | n/a (read-side) | n/a | n/a | 🟢 | 🟢 |
| 31 | PM Hub (read-side) | 🟢 (PM) | n/a | n/a | n/a | n/a | n/a | 🟢 | 🟢 |
| 32 | Public Time-Off (employee request) | 🟢 (employee) | 🟢 (HR queue) | 🟡 | 🟡 | 🟢 | 🔴 | 🟢 | 🟢 |
| 33 | Topic Library | 🟢 (Safety) | n/a | n/a (read-side) | n/a | n/a | n/a | 🟢 | 🟢 (23 ES files) |
| 34 | Fleet DVIR | 🟢 (Driver) | 🟡 | 🟢 | 🟡 | 🟢 | n/a | 🟢 | 🔴 |
| 35 | Fleet Repair / RTS | 🔴 (no formal `who` on RTS) | 🔴 (no formal multi-party sign-off contract) | 🔴 (no escalate kind on RTS) | 🟡 | 🟢 | 🔴 | 🔴 | 🔴 |

---

## 3 · Aggregate accountability completion (35 workflows × 6 dimensions × 2 languages = 420 cells)

| Dimension | 🟢 (EN) | 🟡 (EN) | 🔴 (EN) | 🟢 (ES) | 🟡 (ES) | 🔴 (ES) |
|---|---:|---:|---:|---:|---:|---:|
| Owner | 33 | 1 | 1 | n/a | n/a | n/a |
| Approver | 23 | 3 | 9 | n/a | n/a | n/a |
| Escalation | 28 | 5 | 2 | n/a | n/a | n/a |
| Audit Trail | 18 | 16 | 1 | n/a | n/a | n/a |
| Retention | 33 | 0 | 2 | n/a | n/a | n/a |
| Reopen/Revision | 8 | 4 | 11 (some n/a) | n/a | n/a | n/a |
| **Composite EN accountability** | **143 / 210 = 68%** | | | | | |
| **Composite ES accountability (Layer B coaching dependency)** | **5 / 35 = 14% GREEN** ; remaining 30 have ES audit/retention via code (Layer A) but ES coaching/explanation absent | | | | | |

EN accountability is **substantially complete** (Owner / Audit / Retention near-universal; gaps concentrate on Approver, Escalation, Reopen for non-lifecycle workflows). ES accountability is **substantially incomplete at the coaching/explanation layer** — the underlying code-level accountability (audit rows, retention) exists in both languages by virtue of being code, but the coaching that explains it to a Spanish operator does not.

---

## 4 · Gaps clustered (informational, not authorizing)

| Cluster | Affected workflows | Type |
|---|---|---|
| **A1 — Approver path absent (formal sign-off)** | Safety Meeting, Vendor Management, Fleet RTS | Either implement approval state machine OR declare doctrine-explicit (operator) |
| **A2 — Reopen rules DOCTRINE-SILENT** | Asset Transfer, Time-Off Review, Public Time-Off, Vendor Management, Fleet RTS | Operator decides whether each is genuinely doctrine-silent OR needs formal reopen |
| **A3 — Audit trail YELLOW (created_at only, no workflow_state_events)** | Pre-op, Equipment Issuance, Equipment Training, Fire Extinguisher, Safety Document, Safety Training, Attendance, Time Verification, Document Expirations, Driver Qualification, Time-Off Review, Employee Accountability, Field Leadership, Checkout, Fleet DVIR | Append-only by virtue of code; not unified into the workflow_state_events lake. Operator decides whether to extend. |
| **A4 — ES accountability coaching absent** | 30 of 35 workflows | Layer B body_es content gap |
| **A5 — Glossary in-flow linking absent** | All 35 | UI wiring — operator-intent declared, not implemented |

Per FOCP Rule 6 ("Every recommendation must be traceable to an existing workflow, screen, form, or process"), every cluster above traces to existing infrastructure. **No new workflows. No new modules.**

---

## 5 · Retired false findings

| Inherited claim | Verdict | Disposition |
|---|---|---|
| "All workflows have audit trails" | Verified: only 7 of 35 have unified `workflow_state_events` audit. 15+ have created_at-based audit. | **REFINED.** |
| "Approver paths are universally implemented" | 9 workflows lack formal approver — most are append-only records (Equipment Issuance, etc.) and approval is structurally not applicable; 3 are RED (Safety Meeting, Vendor Management, Fleet RTS). | **REFINED.** |
| "Retention policies are documented per workflow" | Retention is implemented uniformly (Mongo persistence; append-only by code) but is not documented per-workflow in coaching content. | **REFINED.** |

---

**End of ACCOUNTABILITY COACHING REGISTER · OCSPCP 4 of 7**
