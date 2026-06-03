# WORKFLOW EXPLANATION LIBRARY
## OCEP · Training Completion Program (TCP)

**Date**: 2026-06-03
**Authority**: OMEGA · TCP
**Mode**: READ-ONLY content authoring · source-anchored (no fabrication)
**Purpose**: For each platform workflow, answer the 10 directive-mandated questions in a single canonical form. This file IS the training content. It is referenced by:
- `TRAINING_COMPLETION_MASTER_REGISTER.md` (per-workflow status)
- `WORKFLOW_KNOWLEDGE_MATRIX.md` (role × workflow grid)
- `TRAINING_GAP_REGISTER.md` (per-page 30-second failure register)

Source basis: existing `/app/backend/`, `/app/frontend/src/`, `/app/memory/` doctrine documents, and `tips.py` registry. Where doctrine is silent, the entry is marked `DOCTRINE-SILENT` and surfaces as a follow-up unknown.

---

## 1 · DAILY REPORT

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | The Daily Report is the legal record of work performed on a job site. It anchors hours, materials, equipment usage, weather, and narrative against `project_number` and `date`. Downstream: payroll, billing, schedule, claims defense. |
| 2 | **When to use it** | One Daily Report per crew per job per day. Submit by end-of-shift the day of work. Late submission triggers payroll variance and customer-billing delay. |
| 3 | **Who owns it** | Foreman (primary author) → escalates to Superintendent if blocked. |
| 4 | **Who receives it** | Office (Admin role) for review (`PENDING_REVIEW` → `REVIEWED` → `CLOSED`). PM read-side only at closure. |
| 5 | **What happens after submission** | DR enters `PENDING_REVIEW`. Office Admin reviews; either advances to `REVIEWED` or returns to field (`PENDING_REVIEW → OPEN` with reason ≥ 5 chars). Reason appears in the lifecycle History drawer. |
| 6 | **Common mistakes** | (a) Wrong hours (drives variance). (b) Missing materials. (c) Skipping the narrative. (d) Submitting before the shift ends. (e) Not reading the kickback reason and resubmitting blind. |
| 7 | **How to correct mistakes** | Before submission: edit the form. After `PENDING_REVIEW`: wait for office to kick back; office can also use Admin Universal Undo to revert any transition. |
| 8 | **How to reopen or recover** | Office kickback: `PENDING_REVIEW → OPEN` with reason. Universal Undo (admin-only, FOCP R2) reverses the last transition with mandatory reason. |
| 9 | **Related workflows** | Payroll Variance (consumes DR hours), Incident Report (DR may reference incident on shift), JHP (DR pre-shift hazard acknowledgement), Dispatch (DR confirms what dispatch assigned was actually worked). |
| 10 | **Success criteria** | DR closed on the schedule the Office expects. Zero stuck DRs > 72h. Zero kickbacks for missing required fields. |

---

## 2 · JOB HAZARD PLAN (JHP)

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | The JHP is the pre-shift safety briefing made permanent. It documents site hazards, PPE, and emergency response. Employee acknowledgement creates the legally-required attestation chain. |
| 2 | **When to use it** | Upload: as soon as a job is mobilized OR when conditions change (new hazard, weather, equipment). Acknowledge: before starting work on a job that day. |
| 3 | **Who owns it** | Author/upload: Safety or PM (admin token). Acknowledgement: each employee individually. Roster oversight: Foreman. Compliance: Safety + PM. |
| 4 | **Who receives it** | Field crew via `/jha`. Supervisors via `/admin/jha-acknowledgements` (post-FOCP R2). Audit twin in `workflow_state_events` with `workflow="jha_ack"`. |
| 5 | **What happens after submission** | (a) Upload → file lands in `db.job_hazard_files`, visible at `/jha`. (b) Acknowledgement → row in `db.jha_acknowledgements` + audit event. Re-acknowledging the same file version replaces the prior signature; the audit trail preserves both. |
| 6 | **Common mistakes** | (a) Signing on a stale version (operator should re-acknowledge the new version — original is preserved in audit). (b) Spanish-only crew member with no work email cannot acknowledge (email-as-identity-key, FOCP R2 § C2-0014). (c) Foreman trusting crew said they signed without verifying via `/admin/jha-acknowledgements`. |
| 7 | **How to correct mistakes** | Wrong version signed → simply acknowledge the new version. Prior row replaced, prior signature preserved in audit. Email-missing employee → use `employee_id` instead of email; admin can resolve. |
| 8 | **How to reopen or recover** | JHP acknowledgements are append-only in audit. No "unsign" — the operator-led correction is to acknowledge the correct version. Admin can review the entire trail at `/admin/jha-acknowledgements`. |
| 9 | **Related workflows** | Daily Report (DR submission implicitly assumes JHP was acknowledged), Incident Report (post-incident, JHP review for the affected job is mandatory), Safety Meeting (JHP content typically delivered in the meeting). |
| 10 | **Success criteria** | 100% acknowledgement coverage of every active job's current JHP version before shift. Zero ack gaps on mobilizing jobs. |

---

## 3 · SAFETY MEETING

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Recurring proactive safety briefing (weekly toolbox / pre-task / monthly all-hands). Creates roster proof, topic record, and discussion outcome. |
| 2 | **When to use it** | Per the company's safety calendar (typically weekly per crew) AND ad-hoc on serious incident or near-miss. |
| 3 | **Who owns it** | Foreman / Safety Coordinator (author + facilitator). Roster: signed by attendees. |
| 4 | **Who receives it** | Safety (visibility), PM (job-specific records), audit trail. |
| 5 | **What happens after submission** | Meeting record persists in `db.meetings`; attendee signatures attach. Visible to Safety and PM portal. |
| 6 | **Common mistakes** | (a) Signing for someone else. (b) Generic topic ("Be safe") instead of job-specific hazard. (c) Foreman holding meeting verbally without recording. |
| 7 | **How to correct mistakes** | Edit meeting record while still in open state; once closed, append a follow-up note. |
| 8 | **How to reopen or recover** | DOCTRINE-SILENT — meetings do not currently have a formal lifecycle reopen. If the meeting record is materially wrong, Safety creates a corrective note. |
| 9 | **Related workflows** | JHP (often the meeting's topic), Incident Report (incident may trigger an ad-hoc meeting), Corrective Action (meeting may surface CAPA items). |
| 10 | **Success criteria** | Per-crew weekly cadence preserved. Roster complete. Topic specific. Discussion outcomes captured. |

---

## 4 · INCIDENT REPORT

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Legal-record-quality intake of every injury, near-miss, property damage, or environmental release. Drives OSHA recordable determination, CAPA, and trend analysis. |
| 2 | **When to use it** | Immediately. First-on-scene reports within 15 minutes (`/incidents/new` is public). Late reports lose evidentiary weight. |
| 3 | **Who owns it** | Reporter: any role (often Foreman or Laborer). Triage + investigation: Safety. Closure: Safety + Admin (3-attestation gate). CAPA owner: assigned by Safety. |
| 4 | **Who receives it** | Safety (triage), PM (their job), Executive (auto-escalate on OSHA recordable per `OPERATOR_CONFIDENCE_LAYER_FINAL_SPEC §4.5`). |
| 5 | **What happens after submission** | `OPEN` → Safety transitions to `UNDER_INVESTIGATION` → `PENDING_CLOSURE` → `CLOSED` (3 attestations + OSHA ack). Audit twin in `workflow_state_events` workflow=`incident`. |
| 6 | **Common mistakes** | (a) Mis-classifying severity (routes to wrong queue). (b) Vague narrative ("hurt finger" vs "laceration to right index finger requiring sutures"). (c) Missing witnesses. (d) Closing too soon. |
| 7 | **How to correct mistakes** | Severity edit while in `OPEN`/`UNDER_INVESTIGATION`. Wrong closure → use Universal Undo (admin-only). All edits leave audit rows. |
| 8 | **How to reopen or recover** | Reopen: `CLOSED → UNDER_INVESTIGATION` with reason (admin / safety lane). Universal Undo (FOCP R2): reverses the last transition; original transition preserved as audit row. |
| 9 | **Related workflows** | CAPA (most incidents spawn ≥ 1 CAPA), JHP review (post-incident JHP update), Safety Meeting (incident-triggered briefing), Daily Report (DR notes incident occurred). |
| 10 | **Success criteria** | Every OSHA recordable closed with the 3-attestation gate plus OSHA ack. Zero recordables OPEN > 24h. Zero unauthorized closures (code-impossible per state machine). |

---

## 5 · QA/QC INSPECTION

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Pre-pour / pre-cover quality checkpoint. Captures deficiencies BEFORE the work is permanently buried. Defends against rework and warranty claims. |
| 2 | **When to use it** | Before every concrete pour, before every backfill, before every cover-up. Plus per project's QA/QC plan. |
| 3 | **Who owns it** | Inspector (PM or Safety) authors the deficiency. PM and Safety jointly drive closure. |
| 4 | **Who receives it** | PM (their project), Safety (cross-project), Foreman (must remediate). |
| 5 | **What happens after submission** | `OPEN/DEFICIENCY_RAISED` → `PENDING_RE_INSPECTION` → one of 3 closure paths (Amendment 001 REPLACE-5): **(A)** re-inspection passed · **(B)** corrective action documented ≥ 20 chars · **(C)** exception with PM + Safety dual sign-off + reason ≥ 10 chars. Audit twin `workflow=qaqc_inspection`. |
| 6 | **Common mistakes** | (a) Closing without re-inspection (code-blocks; doctrine intent). (b) Picking the wrong closure path. (c) Vague corrective-action text. (d) Skipping exception sign-off when path C is the correct choice. |
| 7 | **How to correct mistakes** | Wrong path chosen → Universal Undo (admin) reverses to the prior state; choose the right path. Vague text → re-open via undo and re-author. |
| 8 | **How to reopen or recover** | Reopen lane defined per state machine. Universal Undo (FOCP R2): reverses last transition; original preserved in audit. |
| 9 | **Related workflows** | Site Inspection (similar shape, different focus area), Corrective Action (QA/QC closure path B IS a CAPA), Daily Report (DR documents the inspected work). |
| 10 | **Success criteria** | Every deficiency reaches a path A/B/C closure. Zero deficiencies overdue per Amendment 001 thresholds. Zero unauthorized closures. |

---

## 6 · SITE INSPECTION

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | General safety / housekeeping / PPE / regulatory walk. Different from QA/QC (quality-of-work); same closure-contract shape. |
| 2 | **When to use it** | Per the site's inspection cadence (typically weekly) or in response to a complaint / external visit. |
| 3 | **Who owns it** | Safety primarily; PM may participate. |
| 4 | **Who receives it** | Safety, PM, Foreman (must remediate findings). |
| 5 | **What happens after submission** | `OPEN/FINDINGS_RAISED` → `PENDING_RE_INSPECTION` → closure paths A/B/C per Amendment 001 REPLACE-4 (parallel to QA/QC). Audit twin `workflow=site_inspection`. |
| 6 | **Common mistakes** | (a) Confusing `FINDINGS_RAISED` (Site) with `DEFICIENCY_RAISED` (QA/QC). (b) Same closure-path confusion as QA/QC. (c) Closing finding without owner assignment. |
| 7 | **How to correct mistakes** | Same as QA/QC: Undo + re-author. |
| 8 | **How to reopen or recover** | Per state machine reopen lane + Universal Undo. |
| 9 | **Related workflows** | QA/QC (parallel structure), CAPA, Safety Meeting. |
| 10 | **Success criteria** | Every finding has an owner. Every finding reaches closure path A/B/C. Zero overdue. |

---

## 7 · DISPATCH

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Daily assignment of drivers + trucks + equipment to jobs. The literal entry-point for every operating day. |
| 2 | **When to use it** | Daily (build tomorrow's board today). Plus mid-shift re-dispatch as needed. |
| 3 | **Who owns it** | Dispatch (primary). Shop informs (equipment available/offline). HR informs (driver qualifications). |
| 4 | **Who receives it** | Foremen + drivers (today's assignment); Super (cross-job view); HR (qualification cross-check); Shop (equipment claim). |
| 5 | **What happens after submission** | Board publishes; drivers receive shift-start via QR (post-iter393); Day-1 / Week-1 debrief lifecycle (post-iter392). |
| 6 | **Common mistakes** | (a) Assigning a driver whose CDL or medical expires before the shift. (b) Assigning equipment Shop has taken offline. (c) Not reading idle alerts / utilization signals. |
| 7 | **How to correct mistakes** | Reassign mid-shift; the board accepts changes with audit. |
| 8 | **How to reopen or recover** | Dispatch lifecycle (post-iter392) carries its own kickback / handoff verbs. Universal Undo (FOCP R2) admin-only for completed lifecycle transitions. |
| 9 | **Related workflows** | Driver Qualification (HR), Fleet Repair (Shop), Daily Report (DR confirms what was actually worked), Time-Off (driver unavailability). |
| 10 | **Success criteria** | Tomorrow's board ≥ 90% complete by 3pm today. Zero unqualified-driver assignments. Zero offline-equipment assignments. |

---

## 8 · FLEET (Repair / Visibility / Return-to-Service)

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Equipment lifecycle: defect intake → repair → return-to-service. The platform's most operationally consequential workflow (a wrongly-released truck kills people). |
| 2 | **When to use it** | Immediately on defect discovery (driver pre-shift, mechanic finding, post-incident inspection). |
| 3 | **Who owns it** | Shop (primary). Driver / Foreman (defect reporter). Dispatch (informed of offline). |
| 4 | **Who receives it** | Shop queue, Dispatch (offline notification), PM (job-impact). |
| 5 | **What happens after submission** | Severity-tiered intake (post-iter251) → repair lifecycle → RTS (Return-to-Service) checkpoint. |
| 6 | **Common mistakes** | (a) Mis-classifying severity (e.g., Yellow vs Red). (b) Releasing back to service without RTS verification. (c) Not communicating offline status to Dispatch. (d) **Phase 2 Pattern P3** flagged Shop/Fleet as platform's thinnest coaching surface — operators likely lack inline guidance. |
| 7 | **How to correct mistakes** | Reopen the repair; document the reason. Universal Undo if a lifecycle transition was wrong. |
| 8 | **How to reopen or recover** | Repair lifecycle reopen lane; Universal Undo (admin). |
| 9 | **Related workflows** | Equipment Inspection, Dispatch (cannot dispatch offline equipment), Daily Report (DR notes equipment used). |
| 10 | **Success criteria** | Zero units released to service with unresolved Red defects. Zero "same defect 2 weeks later" recurrences. RTS chain auditable. |

---

## 9 · EQUIPMENT (Inspection · Issuance · Training)

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Three related surfaces: (a) Inspection — pre-shift / periodic equipment check; (b) Issuance — equipment assigned to an employee with acknowledgement; (c) Training — operator certification per equipment class. |
| 2 | **When to use it** | (a) Pre-shift before equipment use. (b) When issuing equipment (PPE, tools, vehicles). (c) When new equipment requires operator certification. |
| 3 | **Who owns it** | Laborer / Operator (inspection + acknowledgement). Safety (issuance authorization). HR (training records). Shop (equipment readiness). |
| 4 | **Who receives it** | Safety + Shop (inspection results); HR (training records, signed issuance); Dispatch (current operator-equipment binding). |
| 5 | **What happens after submission** | Inspection: pre-shift defect → routes to Shop OR clears for use. Issuance: signed equipment-employee binding + acknowledgement (signature). Training: record persists with expiration. |
| 6 | **Common mistakes** | (a) Skipping pre-shift. (b) Issuing without acknowledgement signature. (c) Training without expiration tracking. |
| 7 | **How to correct mistakes** | Edit while in open state; once recorded, append correction note. |
| 8 | **How to reopen or recover** | Issuance acknowledgement is append-only; correction = new issuance with explanation. Inspection: re-inspect. |
| 9 | **Related workflows** | Fleet (vehicle equipment), Dispatch (operator-equipment binding), HR Training Records. |
| 10 | **Success criteria** | 100% pre-shift coverage on assigned equipment. 100% acknowledged issuance. Zero expired training in active use. |

---

## 10 · HR (Hub / Daily Reports view / Incidents view / Safety Records)

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | HR's command surface across employee data, payroll, safety records, training, time-off, and read-side views of operational data tied to people. |
| 2 | **When to use it** | Continuous: HR works the hub daily. |
| 3 | **Who owns it** | HR (primary), Admin (escalations). |
| 4 | **Who receives it** | HR-internal; surface-specific (e.g., Time-Off Queue serves PM approval downstream). |
| 5 | **What happens after submission** | Hub itself is read-only; each tile drills into a workflow with its own lifecycle (Employee Lifecycle, Time-Off, Payroll Variance, etc.). |
| 6 | **Common mistakes** | (a) Editing records directly (bypassing lifecycle). (b) Using parallel HRIS spreadsheet alongside platform. (c) Not reviewing the hub's weekly digest cadence. |
| 7 | **How to correct mistakes** | Use the underlying workflow's correction path. Avoid direct edits. |
| 8 | **How to reopen or recover** | Each underlying workflow has its own recovery; see Employee Lifecycle, Time-Off, Payroll Variance entries below. |
| 9 | **Related workflows** | Employee Lifecycle, Time-Off, Payroll Variance, Driver Qualification, Training Records, Safety Records. |
| 10 | **Success criteria** | HR Confidence Layer GREEN (per spec §4.7): last week's PV finalized, zero employee requests > 5d, zero training expiring < 7d. |

---

## 11 · TIME OFF

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Employee requests for paid/unpaid leave with audit trail and approval chain. |
| 2 | **When to use it** | Employee initiates as far in advance as possible; same-day for sickness. |
| 3 | **Who owns it** | Employee (request initiator); HR / Manager (approver). |
| 4 | **Who receives it** | HR queue + PM (the employee's manager). |
| 5 | **What happens after submission** | Request lands in HR Time-Off queue → approval/rejection → calendar / payroll impact. |
| 6 | **Common mistakes** | (a) Wrong leave type. (b) Missing duration. (c) Approver delay (Phase 2 §1.19 flagged approval-class FAIL). |
| 7 | **How to correct mistakes** | Edit while in open state; HR can adjust on behalf of employee with audit. |
| 8 | **How to reopen or recover** | DOCTRINE-SILENT for time-off-specific reopen. Standard recovery path: HR reverses via direct edit with audit comment. |
| 9 | **Related workflows** | Dispatch (driver unavailability), Daily Report (absent employee), Employee Lifecycle (separation events relate to PTO payout). |
| 10 | **Success criteria** | Zero requests > 5 days unanswered. Zero requests approved without payroll impact captured. |

---

## 12 · EMPLOYEE LIFECYCLE

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Single authoritative life-of-record for every employee: hire → active → leave/return → terminate → archive. Source of truth for payroll, training, dispatch, safety. |
| 2 | **When to use it** | On every employment status change. Reactivate vs Rehire is the most operationally consequential decision (preserves `original_hire_date`). |
| 3 | **Who owns it** | HR (primary). PM/Field Leadership inputs hire-recommendations. |
| 4 | **Who receives it** | HR, Dispatch, Safety, PM — all downstream. |
| 5 | **What happens after submission** | Status change writes to `db.employees.lifecycle_status` + audit row. Dispatch + Safety + Training reflect new status. |
| 6 | **Common mistakes** | (a) Rehiring instead of Reactivating (loses `original_hire_date` per Phase Alpha doctrine; HR Rehire tip is the only platform PASS on Phase 2 §1.7 — model for all other workflows). (b) Skipping termination cleanup. (c) Direct edit of `lifecycle_status` bypassing lifecycle. |
| 7 | **How to correct mistakes** | Restore archived employee via `/api/admin/employees/{id}/restore`. Reactivate path covers reversal of separation. |
| 8 | **How to reopen or recover** | Restore (admin) + Reactivate (HR canonical) + Universal Undo (admin). Phase Alpha doctrine governs original_hire_date preservation. |
| 9 | **Related workflows** | Time-Off, Payroll Variance, Driver Qualification (HR-side), Safety Training, Dispatch. |
| 10 | **Success criteria** | Zero direct-edits to `lifecycle_status` outside the lifecycle path. Zero rehire-when-should-be-reactivate errors. |

---

## 13 · ASSET TRANSFER

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Track physical asset movement between jobs / employees / locations with sender-receiver attestation. |
| 2 | **When to use it** | Any cross-job asset move; any asset issuance change between employees. |
| 3 | **Who owns it** | Sender (initiates); Receiver (accepts/rejects). |
| 4 | **Who receives it** | Receiver's queue (Field portal). Admin / PM read-side. |
| 5 | **What happens after submission** | Transfer becomes pending; receiver acknowledges or rejects with reason. |
| 6 | **Common mistakes** | (a) Receiver delays (Phase 2 §1.19 flagged approval-class FAIL). (b) Wrong recipient assigned. (c) Asset description vague. |
| 7 | **How to correct mistakes** | Sender can cancel while pending. Once accepted, reverse via new transfer. |
| 8 | **How to reopen or recover** | DOCTRINE-SILENT — no formal lifecycle. Recovery = new transfer in the opposite direction. |
| 9 | **Related workflows** | Equipment Issuance, Fleet (vehicle transfers), Dispatch. |
| 10 | **Success criteria** | Zero pending transfers > 5 days. Zero "asset lost" disputes. |

---

## 14 · PAYROLL VARIANCE

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Reconcile reported hours (from DR) against payroll system. Catch errors before they become paychecks. Drives operator-led decisions on every flagged row. |
| 2 | **When to use it** | Weekly (per iter452 doctrine — there is NO AUTO-FINALIZE; every batch is operator-led). |
| 3 | **Who owns it** | HR (review + approve). Admin (finalize). |
| 4 | **Who receives it** | HR queue; Admin finalize lane; Foremen if their DR is the source of variance. |
| 5 | **What happens after submission** | Batch enters lifecycle: `OPEN → UNDER_REVIEW → APPROVED → FINALIZED` (Admin only). 3 attestation flags required (`review_complete`, `approval_complete`, `variance_decisions_complete`). Audit twin `workflow=payroll_variance`. |
| 6 | **Common mistakes** | (a) Ticking the 3 attestations without truly reviewing (Phase 6 AR-0004 flagged). (b) Finalizing with a flagged row undecided. (c) Treating variance as automated when it is deliberately operator-led. |
| 7 | **How to correct mistakes** | Universal Undo (FOCP R2) reverses the most recent transition; original event preserved. Re-review with new attestations. |
| 8 | **How to reopen or recover** | Reopen lane: `FINALIZED → APPROVED` with reason. Universal Undo for any lifecycle slip. |
| 9 | **Related workflows** | Daily Report (source of hours), Employee Lifecycle (separation affects PTO payouts), Time-Off. |
| 10 | **Success criteria** | Weekly batch reaches FINALIZED on schedule. Zero flagged rows undecided at finalization. Zero auto-finalizations (doctrine). |

---

## 15 · CONSTRAINTS (Operational Constraint Foundation)

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Capture every operational blocker (weather, permit, design, materials, manpower, equipment) with chronology and resolution context. Defends against schedule claims. |
| 2 | **When to use it** | Whenever production is materially affected by a non-production factor. |
| 3 | **Who owns it** | PM (primary author). Super inputs. |
| 4 | **Who receives it** | PM portal, Super, Executive (financial exposure visibility). |
| 5 | **What happens after submission** | Constraint persists with chronology (`/api/operational-constraints/{id}/chronology`). Status patched (`PATCH /api/operational-constraints/{id}`) and resolved (`POST /api/operational-constraints/{id}/resolve`). |
| 6 | **Common mistakes** | (a) Chronology entries vague or missing. (b) Resolving without root-cause text. (c) Expecting a Reopen path — per TR-0007 doctrine, the platform deliberately does NOT expose constraint-reopen (product decision). |
| 7 | **How to correct mistakes** | Edit chronology (append-only). Re-PATCH status while not yet resolved. |
| 8 | **How to reopen or recover** | DOCTRINE EXEMPT: constraint reopen path is intentionally absent per `OPERATIONAL_CONSTRAINT_FOUNDATION.md`. If a resolved constraint must be revisited, create a new constraint referencing the prior. |
| 9 | **Related workflows** | Daily Report (DR notes constraint impact), Project Health (constraints feed into job health), Incident Report (some constraints originate as incidents). |
| 10 | **Success criteria** | Every constraint has chronology. Every resolved constraint has root-cause text. No improper reopen attempts. |

---

## 16 · SUBMITTALS

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | (Industry standard) PM-side packet management for submitting materials, shop drawings, RFIs to the customer/engineer for approval. |
| 2 | **When to use it** | Per project's submittal schedule. |
| 3 | **Who owns it** | PM (primary). |
| 4 | **Who receives it** | External (customer / engineer). PM tracks status internally. |
| 5 | **What happens after submission** | DOCTRINE-SILENT in current platform. |
| 6 | **Common mistakes** | N/A — surface not built. |
| 7 | **How to correct mistakes** | N/A. |
| 8 | **How to reopen or recover** | N/A. |
| 9 | **Related workflows** | Purchase Orders, Project Management, Vendor Management. |
| 10 | **Success criteria** | N/A — workflow not currently built. |

**Status**: **NOT-IMPLEMENTED** on the current platform (source survey 2026-06-03: only 1 file mentions "submittal" tangentially; no dedicated routes / pages / state machine). PMs likely run Submittals outside the platform today. Implementing is **out of scope** under FOCP Final Directive without 7-test + 4-proof clearance. Flagged in TRAINING_GAP_REGISTER.

---

## 17 · PURCHASE ORDERS

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | PM-initiated purchase request → approval chain → vendor commitment. Tracks job-cost commitments before invoice. |
| 2 | **When to use it** | When committing project funds to a vendor for materials / services. |
| 3 | **Who owns it** | PM (initiates). Admin / Executive (approver, depending on threshold). |
| 4 | **Who receives it** | PO Requests queue (Approvals class); accounting downstream. |
| 5 | **What happens after submission** | Request enters approval queue; on approval → vendor commitment; on rejection → returned with reason. |
| 6 | **Common mistakes** | Phase 2 §1.19 flagged the entire Approvals class as FAIL — no in-app coaching. Likely operator confusion: (a) wrong amount, (b) wrong vendor, (c) missing job-cost code. |
| 7 | **How to correct mistakes** | Cancel while pending; resubmit with corrections. Universal Undo (admin) on approved transitions. |
| 8 | **How to reopen or recover** | DOCTRINE-SILENT for PO-specific reopen. |
| 9 | **Related workflows** | Vendor Management, Project Management, Daily Report (materials traced to POs). |
| 10 | **Success criteria** | Zero pending POs > 7 days. Zero approved POs without commitment booked. |

---

## 18 · VENDOR MANAGEMENT (Sub / Supplier)

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | Track vendor/sub master records, qualification, performance, commitments. |
| 2 | **When to use it** | Onboard a new vendor; review existing performance; archive defunct vendors. |
| 3 | **Who owns it** | PM (operational); Admin (master record). |
| 4 | **Who receives it** | PM portal; Admin. |
| 5 | **What happens after submission** | Vendor record persists in `db.suppliers` with `lifecycle_state` and `is_active`. |
| 6 | **Common mistakes** | (a) Duplicates (vendor onboarded twice). (b) Active vendors that should be archived. **TR-0003 in the Truth Register specifically identifies that the platform has NO archive workflow for vendors / subs**. |
| 7 | **How to correct mistakes** | DOCTRINE-SILENT — no archive workflow per TR-0003. Recovery = direct admin edit with audit. |
| 8 | **How to reopen or recover** | DOCTRINE-SILENT pending TR-0003 resolution. |
| 9 | **Related workflows** | Purchase Orders, Submittals (if built), Daily Report (vendor sub-crew on site). |
| 10 | **Success criteria** | Master vendor list current. Zero duplicates. Active set reflects real engagement. |

**Status**: Vendor read/edit exists. Archive workflow MISSING per TR-0003 (Truth Register ACTIVE).

---

## 19 · PROJECT MANAGEMENT

| # | Field | Answer |
|---|---|---|
| 1 | **Why this exists** | The PM's command surface: job financial health, schedule, CAPAs, incidents, JHP compliance, sub commitments, P&L. |
| 2 | **When to use it** | Continuously throughout the day. PM Hub is the entry-point. |
| 3 | **Who owns it** | PM (primary). Super inputs. Executive read-side. |
| 4 | **Who receives it** | PM internally; Executive read-side via AdminCommandCenter; Safety + HR cross-referenced. |
| 5 | **What happens after submission** | Project Management is a hub of read-write surfaces; each underlying workflow has its own lifecycle (incidents, CAPAs, DRs, etc.). |
| 6 | **Common mistakes** | (a) PM only opening the platform when prompted by email. (b) PM not trusting data and re-pulling from Office. (c) PM bypassing platform for customer comms (intentional — platform is internal). |
| 7 | **How to correct mistakes** | Use the underlying workflow's correction path. |
| 8 | **How to reopen or recover** | Per-workflow recovery paths apply. |
| 9 | **Related workflows** | All operational workflows roll up into Project Management views. |
| 10 | **Success criteria** | PM Confidence Layer GREEN (per spec §4.4): zero CAPAs overdue, all DRs closing on schedule, JHP coverage ≥ 90% per project. |

---

## Doctrine references cited (no fabrication)

- FOCP Release 1 status canonicalization · `FOCP_COMPLETION_RELEASE_1_TR0005_BUNDLE.md`
- FOCP Release 2 JHP Acknowledgement Ledger + Universal Undo · `FOCP_COMPLETION_RELEASE_2_TR0001_BUNDLE.md`, `FOCP_COMPLETION_RELEASE_2_TR0002_BUNDLE.md`
- Amendment 001 QA/QC + Site Inspection closure contract · `workflow_state_machine.py` REPLACE-4/5
- iter452 Payroll Variance no-auto-finalize doctrine
- Phase Alpha Employee Lifecycle governance
- TR-0003 Sub/Vendor archive workflow ACTIVE
- TR-0007 Constraint reopen DOCTRINE-EXEMPT

---

**End of WORKFLOW EXPLANATION LIBRARY · TCP**
