# OMEGA · OWNERSHIP TRANSFER MATRIX

**Date:** 2026-06-02 · Companion to `OWNERSHIP_LAYER_DISCOVERY_AUDIT.md` and `OWNERSHIP_INFERENCE_MATRIX.md`
**Mode:** READ-ONLY · zero code · zero design · zero estimates
**Purpose:** Enumerate the events that transfer ownership and the events that close ownership. **Transfer is never an action — it is a side-effect of a state transition.** Closure is never a click — it is a side-effect of an operational action that completes a Tier 1 work artifact.

---

## §0 · Foundational rule (Constitution Rule 3 + Rule 4 + Rule 7)

> Ownership transfers ONLY when the state machine transitions. Ownership closes ONLY when the workflow reaches a terminal state via Tier 1 work-performed evidence. There are no exceptions. "Reassign" UI is forbidden. "Mark as Owner" UI is forbidden. "Acknowledge Ownership" UI is forbidden.

---

## §1 · Transfer events × 10 workflows

Each row names the **state transition** that triggers the transfer and the **operational event** that drives that transition. The transition is the cause; the transfer is the effect.

### §1.1 · Incidents (OC-001)

| From state | To state | Triggering operational event | Owner rotates from → to |
|---|---|---|---|
| (none) | OPEN | Incident submitted (form / public gate) | (none) → Submitter |
| OPEN | UNDER_INVESTIGATION | Safety Manager starts investigation (Tier 1: opens incident in admin UI · sets initial classification) | Submitter → Safety Manager |
| UNDER_INVESTIGATION | CORRECTIVE_ACTION_REQUIRED | CAPA created (Tier 1 work artifact) | Safety Manager → PM (project owner) |
| CORRECTIVE_ACTION_REQUIRED | PENDING_CLOSURE | CAPA completed (Tier 1) | PM → Safety Manager |
| PENDING_CLOSURE | CLOSED | Closure attestation + OSHA classification (Tier 1 decision content) | Safety Manager → (none · terminal) |
| Any state | REOPEN | Reopen with reason (Tier 1 decision content) | (any) → most recent owner before closure |

### §1.2 · Daily Reports (OC-002)

| From state | To state | Triggering operational event | Owner rotates |
|---|---|---|---|
| (none) | OPEN | DR submitted | (none) → Submitter |
| OPEN | PENDING_REVIEW | DR auto-submit on save | Submitter → PM |
| PENDING_REVIEW | OPEN | PM kickback with reason (Tier 1) | PM → Submitter (via FSI revise token) |
| PENDING_REVIEW | REVIEWED | PM review attestation (Tier 1 decision content) | PM → PM (no-op rotation; PM still owns) |
| REVIEWED | CLOSED | Closure decision (Tier 1) | PM → (none) |

### §1.3 · QA/QC (OC-003)

| From state | To state | Triggering operational event | Owner rotates |
|---|---|---|---|
| (none) | OPEN | Inspection submitted | (none) → Inspector |
| OPEN | DEFICIENCY_RAISED | Deficiency captured (Tier 1) | Inspector → PM |
| DEFICIENCY_RAISED | IN_REMEDIATION | PM accepts work scope (Tier 1: opens corrective_action OR assigns sub coordination) | PM → PM (no rotation; state semantic change) |
| IN_REMEDIATION | PENDING_RE_INSPECTION | Corrective_action completed (Tier 1) | PM → Inspector |
| PENDING_RE_INSPECTION | CLOSED | Re-inspection passed (Tier 1: new inspection record OR explicit re-inspection event) | Inspector → (none) |

### §1.4 · Site Inspections (OC-004)

Symmetrical to §1.3 — state names FINDINGS_RAISED instead of DEFICIENCY_RAISED.

### §1.5 · Payroll Variances (OC-007)

| From state | To state | Triggering operational event | Owner rotates |
|---|---|---|---|
| (none) | OPEN | Variance flagged (auto from time-verification reconciliation) | (none) → Foreman |
| OPEN | UNDER_REVIEW | Foreman submits explanation (Tier 1 decision content) | Foreman → PM |
| UNDER_REVIEW | OPEN | PM reject with reason (Tier 1) | PM → Foreman |
| UNDER_REVIEW | APPROVED | PM approve with reason (Tier 1 decision content) | PM → Payroll |
| APPROVED | FINALIZED | Payroll finalize per-row decision (Tier 1) | Payroll → (none) |

### §1.6 · Safety (Toolbox Talks · JHP · Training)

| From state | To state | Triggering operational event | Owner rotates |
|---|---|---|---|
| n/a | RECORDED | Toolbox Talk conducted with attendance (Tier 1 + Tier 2 evidence) | (no transfer · the event IS the ownership) |
| n/a | DOWNLOADED | JHP downloaded (Tier 3 identity capture) | Library owner (Safety Manager) retains; download is event-evidence, not ownership transfer |
| ACTIVE | EXPIRING_SOON | < 14d to renewal (auto by date) | Workflow-class default → Direct manager (escalation-style transfer) |
| EXPIRING_SOON | EXPIRED | Renewal date passed (auto) | Direct manager → Manager's manager + Safety Manager |
| EXPIRED | RENEWED | Training renewed (Tier 1: new safety_training_records row) | (escalated owners) → Direct manager + employee |

### §1.7 · Equipment

| From state | To state | Triggering operational event | Owner rotates |
|---|---|---|---|
| n/a | RECORDED (Pre-Op) | Operator submits Pre-Op | (no transfer · per-shift Tier 1 record) |
| RECORDED clean | (no further state) | — | — |
| RECORDED defect | OPEN_DEFECT | Defect flagged | Operator → Shop Foreman |
| OPEN_DEFECT | REMEDIATED | Maintenance work performed (Tier 1: maintenance_records row OR MaintainX integration event) | Shop Foreman → (none) |
| n/a | IN_TRANSIT | Asset Transfer record created | Equipment Manager owns until receipt |
| IN_TRANSIT | DEPLOYED | Receipt at jobsite (Tier 1: receiving operator submits first Pre-Op on-site OR transfer ACK by sign-on-glass) | Equipment Manager → Receiving job's PM |
| DEPLOYED | RETURNED | Return transfer | Receiving PM → Shop Foreman |
| n/a | PM_DUE | Calendar-derived | Equipment Manager owns |
| PM_DUE | PM_OVERDUE | Past-due (auto by date) | Equipment Manager → Equipment Manager's manager |
| PM_OVERDUE | RESOLVED | Maintenance completed (Tier 1) | (escalated) → Equipment Manager |

### §1.8 · Fleet

| From state | To state | Triggering operational event | Owner rotates |
|---|---|---|---|
| n/a | RECORDED (DVIR) | Driver submits DVIR | (no transfer · per-shift Tier 1 record) |
| RECORDED defect | OPEN_DEFECT | Defect flagged | Driver → Fleet Manager |
| OPEN_DEFECT | REMEDIATED | Repair completed (Tier 1) | Fleet Manager → (none) |
| n/a | DQ_VALID | All DQ-file items current | Fleet Manager + Driver's manager |
| DQ_VALID | DQ_EXPIRING_SOON | < 30d to expiration (auto) | Same owners with elevated priority |
| DQ_EXPIRING_SOON | DQ_EXPIRED | Past-due (auto) | + Manager's manager + Safety Manager (DOT exposure) |
| DQ_EXPIRED | DQ_VALID | Renewal recorded (Tier 1 OR EX-6 drug-test integration event OR MVR refresh) | (escalated) → Fleet Manager + Direct manager |

### §1.9 · HR

| Sub-workflow | Transfer event | Owner rotates |
|---|---|---|
| Time Off REQUESTED → APPROVED | Manager approval (Tier 1 decision content) | Manager → Employee (self-service downstream) |
| Time Off REQUESTED → DENIED | Manager denial with reason (Tier 1) | Manager → Employee |
| Time Off APPROVED → TAKEN | Date passes (auto) | Employee → (none) |
| Onboarding step (Safety training) DONE | safety_training_records row written (Tier 1) | (per step) Safety Manager → next step's owner |
| Onboarding step (PPE issuance) DONE | PPE_issuance row written (Tier 1) | Shop Foreman → next step's owner |
| Onboarding step (access provisioning) DONE | access_records row written (Tier 1) | IT → next step's owner |
| Offboarding step (PPE return) DONE | PPE_return row written (Tier 1) | Shop Foreman → next step's owner |
| Offboarding step (access revoke) DONE | access_revocation row written (Tier 1) | IT → next step's owner |
| All Onboarding/Offboarding steps DONE | Workflow terminal | Final-step owner → (none) |
| Performance review (HRIS-side) | INTEGRATE only | HRIS owns transfer |

### §1.10 · Project Operations

| Workflow | Transfer event | Owner rotates |
|---|---|---|
| Submittal PENDING → UNDER_REVIEW (external) | PM dispatches to Engineer of record | PM → counterparty (pseudo-state) |
| Submittal UNDER_REVIEW → APPROVED / REJECTED | Counterparty response received and PM logs disposition (Tier 1) | counterparty → PM |
| RFI OPEN → AWAITING_RESPONSE | PM dispatches to Designer / Owner | PM → counterparty |
| RFI AWAITING_RESPONSE → ANSWERED | Response posted (Tier 1 content) | counterparty → PM |
| CO PROPOSED → UNDER_OWNER_REVIEW | PM submits to Owner Rep | PM → counterparty |
| CO UNDER_OWNER_REVIEW → APPROVED | Owner approval received (Tier 1: signed CO document OR EX-1 accounting event) | counterparty → PM + Accounting (HYBRID) |
| Pay-App SUBMITTED → APPROVED | Owner / Architect approval (Tier 1: signed Pay-App OR EX-1 event) | counterparty → PM + Accounting (HYBRID) |
| Pay-App APPROVED → PAID | EX-1 accounting payment event | PM + Accounting → (none) |
| Sub-Mgmt ONBOARDING → ACTIVE | Contract executed + insurance verified (Tier 1) | PM → PM (state semantic) |
| Sub-Mgmt ACTIVE → INSURANCE_EXPIRING | Auto by date | PM → PM + manager_employee_id of PM |
| Sub-Mgmt INSURANCE_EXPIRING → ACTIVE | New COI uploaded (Tier 1) | (escalated) → PM |
| Meeting-Minutes RECORDED | Minutes submitted (Tier 1) | (no transfer · record-of-fact) |

---

## §2 · Closure events × 10 workflows

Closure events are the subset of transfer events that move the record to a **terminal state**. All closures share the same property: Tier 1 work-performed evidence is the trigger — never a click.

| Workflow | Terminal state | Required Tier 1 evidence | Forbidden closure pattern |
|---|---|---|---|
| Incidents | CLOSED | Closure attestation + OSHA classification + (optional) CAPA complete | "Mark as Resolved" click without attestation |
| Daily Reports | CLOSED | PM review attestation | Auto-close on aging |
| QA/QC | CLOSED | Re-inspection record OR `corrective_actions` complete | "Acknowledge findings" click (Amendment 001 REPLACE-5) |
| Site Inspections | CLOSED | Re-inspection record OR `corrective_actions` complete | "Acknowledge findings" click (REPLACE-4) |
| Payroll Variances | FINALIZED | Payroll per-row finalize decision | Bulk auto-finalize · Variance auto-approve on aging |
| Safety / Training | RENEWED | New `safety_training_records` row | Mass "Acknowledge handbook" click (V-14) |
| Equipment defect | REMEDIATED | Maintenance record OR MaintainX event | "Mark Fixed" click without record |
| Fleet defect | REMEDIATED | Repair record | "Mark Fixed" click |
| HR Onboarding | COMPLETE | All field-side steps Tier 1 evidenced (no checkbox steps remaining) | Multi-step checkbox checklist (REPLACE-7) |
| HR Offboarding | COMPLETE | All field-side steps Tier 1 evidenced | Multi-step checklist (REPLACE-6) |
| Project Ops · Submittal | APPROVED/REJECTED | Counterparty disposition recorded | "Acknowledged" intermediate status (V-1) |
| Project Ops · RFI | ANSWERED | Response posted | "Acknowledged" status (V-2) |
| Project Ops · CO | APPROVED | Owner signature + EX-1 financial sync | Ack-only approval flow (V-3) |
| Project Ops · Pay-App | PAID | EX-1 payment event | "Marked Paid" without integration evidence (V-4) |
| Sub-Mgmt | TERMINATED | Final accounting reconciliation + access revoke | "Marked Inactive" without operational evidence |

---

## §3 · Anti-transfer events (NEVER trigger transfer)

The following operational events do NOT transfer ownership, despite often being mistaken for transfer-worthy:

| Anti-event | Why it doesn't transfer |
|---|---|
| Notification delivered to PM | Information is not ownership — Rule 2 |
| Sub-contractor receives RFI | Sub is counterparty, not owner — RFI owner remains PM throughout |
| Operator submits a Pre-Op | Pre-Op is per-shift Tier 1 record, not a workflow with transferable ownership |
| Field-leader downloads JHP | Download = Tier 3 identity evidence; library owner remains Safety Manager |
| Executive views portfolio rollup | Executive surfaces are Action Consoles — viewing is not ownership |
| User opens Action Console | Console view ≠ ownership transfer |
| Admin reads a workflow record | Read action ≠ ownership |
| Cron job sweeps stale records | Sweeps may trigger escalation events but do NOT directly transfer (escalation handled per `ESCALATION_DISCOVERY_REPORT.md`) |

---

## §4 · Anti-closure events (NEVER trigger closure)

| Anti-event | Why it doesn't close |
|---|---|
| Aging beyond SLA | Triggers escalation, not closure — Rule 4 (Every Workflow Must End requires action, not patience) |
| Manager "approves" without operational evidence | Approval-as-ack pattern · Amendment 001 violation |
| Bulk "Mark all as resolved" | Always violates Rule 6 (Minimize Human Decisions to operational decisions) |
| User dismisses the record from their console | Console dismissal ≠ closure (dismissal is a UX affordance, not an operational action) |
| Workflow imported from external system (data migration) | Migration must preserve original closure evidence or mark as `legacy_closed_unevidenced=True` for forensic visibility |

---

## §5 · Cross-workflow ownership chain (lifecycle example)

To prove the transfer model holds at composite scale, here is a single field-event traced from start to closure across 4 workflows:

**Event:** Foreman submits Daily Report including hazard sighting that becomes an Incident.

| t | Workflow | State | Owner | Transfer driver |
|---|---|---|---|---|
| 1 | DR | OPEN | Foreman | initial submit |
| 2 | DR | PENDING_REVIEW | PM | auto on submit |
| 3 | Incident (spawned) | OPEN | Foreman (incident submitter) | spawn record · creator |
| 4 | Incident | UNDER_INVESTIGATION | Safety Manager | Safety opens investigation |
| 5 | DR | REVIEWED | PM | PM review |
| 6 | DR | CLOSED | (none) | PM closure decision |
| 7 | Incident | CORRECTIVE_ACTION_REQUIRED | PM (project owner) | CAPA created |
| 8 | QA/QC (spawned by CAPA · QC inspection scheduled) | OPEN | Inspector | inspection submitted |
| 9 | QA/QC | DEFICIENCY_RAISED | PM | finding raised on hazard |
| 10 | QA/QC | IN_REMEDIATION | PM | corrective_action opened |
| 11 | Incident | PENDING_CLOSURE | Safety Manager | CAPA completed |
| 12 | Incident | CLOSED | (none) | closure attestation + OSHA |
| 13 | QA/QC | PENDING_RE_INSPECTION | Inspector | corrective_action complete |
| 14 | QA/QC | CLOSED | (none) | re-inspection passed |

**Total human assignments performed during this chain: ZERO.** Total acknowledgement clicks: ZERO. Total ownership transfers: 9 (each driven by a state transition, each transition driven by a Tier 1 operational action).

This is what "the operating system for heavy civil construction" looks like.

---

## §6 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code | ✅ |
| Zero design | ✅ |
| Transfer events documented per workflow with Tier 1 evidence per transition | ✅ |
| Closure events documented with forbidden patterns called out | ✅ |
| Anti-transfer + anti-closure events catalogued | ✅ |
| Cross-workflow lifecycle example demonstrates zero-assignment chain | ✅ |
| Rule 3 + Rule 4 + Rule 7 + Amendment 001 honored throughout | ✅ |

🛑 **STOPPED.**
