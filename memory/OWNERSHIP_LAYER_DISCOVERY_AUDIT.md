# OMEGA · OWNERSHIP LAYER DISCOVERY AUDIT

**Date:** 2026-06-02 · Master document
**Mode:** READ-ONLY · zero code · zero implementation · zero estimates · zero authorization
**Governing doctrine:** Constitution Parts I–IV + Override + Amendment 001 + Build/Integrate/Ignore Doctrine
**Primary question:** How can ForgedOps automatically know who owns something · who should act · when action is required · when escalation occurs — without manual task assignment · acknowledgement workflows · acceptance workflows · ticket systems · Jira-style queues · Monday-style boards · excessive notifications?

---

## §0 · Discovery thesis

Ownership in ForgedOps is **not assigned · it is inferred**. The inference engine reads four signals already present in operational reality:

| Signal | Source |
|---|---|
| **S1 · Creator identity** | Who submitted the record (5-tier FSI ladder for public-gate · authenticated session for office-gate) |
| **S2 · Project membership** | `jobs_master.primary_pm` + project crew + project superintendent |
| **S3 · State-machine position** | Current lifecycle state's role gate (per `PHASE1A_ROLE_MATRIX.md`) |
| **S4 · Manager hierarchy** | `manager_employee_id` ladder + workflow-class default owner |

The intersection of these four signals determines a single accountable person at every moment of a workflow's life. No human types a name into an "Assignee" field. No human clicks "Accept". No human picks from a dropdown. **The platform reads the operational reality and tells the operator who owns this — period.**

This is the inverse of a Jira/Monday/ticket-system model. In those systems, work exists because someone created a task. In ForgedOps, **the operational record IS the task** — there is no parallel task object to assign. The DR exists because a foreman submitted one. The Incident exists because something happened. The Variance exists because hours diverged from a plan. None of these need an "assign" step; they need a "next-owner-inference" step.

---

## §1 · Universal 10-question framework (cross-cutting)

Before going workflow-by-workflow, the framework that governs each.

### Q1 · Who should automatically own the workflow?
Answer = `f(S1, S2, S3, S4)`. Each workflow class names which signals dominate. Default precedence: **S3 first (state's role gate) · S2 second (project owner) · S4 third (workflow-class default) · S1 last (creator)**. Why S1 last? Because the creator is often the *least* accountable party at most lifecycle states (they reported · they did not own).

### Q2 · Can ownership be inferred?
Yes · always. If inference returns NULL, the platform must surface that as an *operational defect*, not as an opportunity to add an "Assign" affordance. The dead-letter routing in iter452.5.1 Tier 5 (`safety@mascigc.com`) is the proof: even orphans go to a deterministic owner.

### Q3 · What event transfers ownership?
**State transition.** Only state transitions transfer ownership. There is no separate "Reassign" action. Reassignment is a side-effect of moving the record to a new state whose role gate names a different role.

### Q4 · What event closes ownership?
**Terminal-state transition with operational action.** Ownership ends when the workflow ends. Workflows end via Tier 1 work-performed evidence (Amendment 001), not via ack-click.

### Q5 · What event escalates ownership?
**Aging in state exceeds class SLA.** Escalation is not a notification fan-out — it is an **automatic ownership transfer up the `manager_employee_id` ladder** at SLA breach. The previous owner is informed, not re-assigned to.

### Q6 · What executive visibility is required?
**Action-Console portfolio rollup.** Executives see ownership concentrations (who owns the most overdue work) and SLA breach rates per role/project — never per-record. Each console row has a one-tap action affordance (reassign by transition · re-prioritize · escalate manually).

### Q7 · What should NEVER become a task?
**Information receipt.** "PM needs to know about X" → notification, not a task. Tasks exist only when an operational action is required. Rule 2 textbook.

### Q8 · What should NEVER require acknowledgement?
**Anything where Tier 1 evidence exists or can be captured.** Per Amendment 001. Acknowledgement is only acceptable when (a) legally mandated, (b) decision content is captured as data, or (c) a Tier-4 ride-along on a Tier-1 work artifact.

### Q9 · What should NEVER require assignment?
**Every lifecycle workflow on the platform.** Assignment dropdowns are forbidden. The state machine assigns; the operator never types a name.

### Q10 · What action actually changes the outcome?
**Operational action by the owner of the current state.** This is the only thing that moves the workflow forward. UI affordances exist only for operational actions; non-action UI (ack buttons, "Mark as Read", "Acknowledge Receipt") is anti-pattern.

---

## §2 · 10 workflows × 10 questions matrix

### §2.1 · Incidents (OC-001 · live)

| Q | Answer |
|---|---|
| Q1 Owner | OPEN→Submitter (FSI Tier 1-5) · UNDER_INVESTIGATION→Safety Manager (workflow-class default) · CORRECTIVE_ACTION_REQUIRED→PM (project owner via S2) · PENDING_CLOSURE→Safety Manager · CLOSED→none |
| Q2 Inferable | Yes — every state has a deterministic role gate; project linkage resolves to `jobs_master.primary_pm`; safety role is workflow-class default. |
| Q3 Transfers | State transitions (OPEN→UI · UI→CAR · CAR→PC · PC→CLOSED). Each transition automatically rotates ownership per role gate. |
| Q4 Closes | CLOSED transition · operational action = closure attestation + OSHA classification + (optional) corrective_action complete. |
| Q5 Escalates | CAR aging > SLA (default 5 business days) → manager_employee_id of PM. PENDING_CLOSURE > 3d → Safety Manager's manager. |
| Q6 Executive | "Incidents in CAR > SLA · by PM" Action Console row · one-tap actions: reassign-by-transition · escalate-now · request-update. |
| Q7 NOT a task | OSHA classification notification to executives · workers-comp claim status update from carrier (consumed event, not task). |
| Q8 NOT ack | OSHA recordable boolean is legally required (PASS Amendment 001). Everything else: no ack. |
| Q9 NOT assign | No "Assign Investigator" dropdown · state UNDER_INVESTIGATION's role gate IS the Safety Manager assignment. |
| Q10 Action that matters | CAPA creation (CAR) · CAPA completion (PC) · closure decision (CLOSED) — these change the record's state and the field outcome. |

### §2.2 · Daily Reports (OC-002 · live)

| Q | Answer |
|---|---|
| Q1 Owner | OPEN→Submitter (FSI ladder · field) · PENDING_REVIEW→PM (S2 · project owner) · REVIEWED→PM until CLOSED · CLOSED→none |
| Q2 Inferable | Yes — submitter from FSI ladder · PM from `jobs_master.primary_pm`. |
| Q3 Transfers | OPEN→PENDING_REVIEW (auto on submit) · PENDING_REVIEW→OPEN (kickback transfers ownership back to submitter via FSI revise token) · PENDING_REVIEW→REVIEWED · REVIEWED→CLOSED. |
| Q4 Closes | CLOSED · operational action = PM review attestation + optional kickback resolution. |
| Q5 Escalates | PENDING_REVIEW > 48h → PM's manager (manager_employee_id ladder). |
| Q6 Executive | "DRs in PENDING_REVIEW > 48h · by PM" Action Console row. |
| Q7 NOT a task | DR submission notification to PM is a notification (delivery-evidence event) · NOT a task. |
| Q8 NOT ack | iter445 "Has crew reviewed JHP?" FAIL-1 · already on IGNORE list. PM review modal captures decision content (PASS). |
| Q9 NOT assign | PM ownership inferred from project; no assignment UI. |
| Q10 Action that matters | PM kickback (with reason) · PM closure decision. Each is Tier 1 work-performed. |

### §2.3 · QA/QC (OC-003 · awaiting iter453 closure-action contract)

| Q | Answer |
|---|---|
| Q1 Owner | OPEN→Inspector (submitter) · DEFICIENCY_RAISED→PM (S2) for sub coordination · IN_REMEDIATION→PM · PENDING_RE_INSPECTION→Inspector · CLOSED→none |
| Q2 Inferable | Yes — inspector from session · PM from project. |
| Q3 Transfers | State transitions only. Sub remediation does not transfer ownership to sub — the **PM owns** sub-coordination as operational reality. |
| Q4 Closes | CLOSED · operational action = re-inspection passed (Tier 1) OR `corrective_actions` record completed. NOT "Mark Resolved" click (Amendment 001 REPLACE-5). |
| Q5 Escalates | IN_REMEDIATION > 10d → PM's manager. PENDING_RE_INSPECTION > 5d → Inspector's manager. |
| Q6 Executive | "Open deficiencies > SLA · by PM" + "Re-inspection backlog · by inspector". |
| Q7 NOT a task | Deficiency-raised notification to PM · sub-coordination email (those are PM's operational tools, not tasks). |
| Q8 NOT ack | "Mark Resolved" ack-click forbidden. Re-inspection record IS the resolution. |
| Q9 NOT assign | Inspector owns inspection; PM owns remediation; no "Assign to Sub" UI. |
| Q10 Action that matters | Corrective action completion + re-inspection submission. |

### §2.4 · Site Inspections (OC-004 · awaiting iter453 closure-action contract)

| Q | Answer |
|---|---|
| Q1 Owner | OPEN→Inspector · FINDINGS_RAISED→PM (S2) · IN_REMEDIATION→PM · PENDING_RE_INSPECTION→Inspector · CLOSED→none |
| Q2 Inferable | Yes — symmetrical to QA/QC. |
| Q3 Transfers | Same as QA/QC. |
| Q4 Closes | CLOSED · operational action = re-inspection passed OR documented exception · NOT "Acknowledge findings" (Amendment 001 REPLACE-4). |
| Q5 Escalates | Symmetrical to QA/QC. |
| Q6 Executive | "Open findings > SLA · by PM" rollup. |
| Q7 NOT a task | Findings notification · regulatory notification. |
| Q8 NOT ack | "Acknowledge findings" forbidden. |
| Q9 NOT assign | Same as QA/QC. |
| Q10 Action that matters | Re-inspection + corrective_action completion. |

### §2.5 · Payroll Variances (OC-007 · live)

| Q | Answer |
|---|---|
| Q1 Owner | OPEN→Foreman (creator of crew time) via S1 · UNDER_REVIEW→PM (S2 · project owner) for approval · APPROVED→Payroll · FINALIZED→none |
| Q2 Inferable | Yes — Foreman from crew composition · PM from project · Payroll is workflow-class default. |
| Q3 Transfers | OPEN→UR (auto on flag) · UR→APPROVED (PM decision) · APPROVED→FINALIZED (Payroll decision). |
| Q4 Closes | FINALIZED · operational action = Payroll's explicit finalize click capturing approval matrix (Tier 1 decision content). |
| Q5 Escalates | UR > 24h before payroll cut → PM's manager. APPROVED but un-finalized at cut time → Payroll Lead. |
| Q6 Executive | "Variances awaiting PM > 24h pre-cut" Action Console row. |
| Q7 NOT a task | Variance flag is a record · not a task. Foreman's view of own crew variances is operational reality, not a task list. |
| Q8 NOT ack | No "Foreman acknowledges variance" pattern. Decision = approve / reject with reason (Tier 1 decision content · PASS). |
| Q9 NOT assign | PM ownership inferred from project. |
| Q10 Action that matters | PM approve/reject + Payroll finalize. |

### §2.6 · Safety (Toolbox Talks · JHP · Training · per OC-005 re-scope decision)

| Q | Answer |
|---|---|
| Q1 Owner | Library content owner = Safety Manager · per-crew per-day delivery owner = Foreman (S1 conducting the talk) · per-employee training owner = `safety_training_records` consumer (employee's manager via S4 hierarchy) |
| Q2 Inferable | Yes — Foreman from crew · Safety Manager from workflow-class · employee manager from `manager_employee_id`. |
| Q3 Transfers | Toolbox Talk conducted → ownership shifts from Safety Manager (content) to attendance roster (Tier 2 evidence) · expiration approach → owner becomes `manager_employee_id` for renewal coordination. |
| Q4 Closes | Training expiration date passed (records terminate) · refresher recorded (cycle resets). |
| Q5 Escalates | Expiration imminent (< 14d) → manager_employee_id · expired → manager's manager. |
| Q6 Executive | "Training expirations next 30d · by manager" + "Crews with overdue Toolbox Talk · by foreman". |
| Q7 NOT a task | "Conduct a Toolbox Talk today" is operational reality (it's how the crew starts the day), not a task generated by the platform. |
| Q8 NOT ack | OC-005 JHP Acknowledgement Ledger as currently scoped FAIL per Amendment 001 CV-1 · re-scope per REPLACE-1 (Toolbox Talk Tier 1 + attendance Tier 2 + JHP download identity Tier 3). |
| Q9 NOT assign | Toolbox Talk doesn't need assigning — Foreman conducts it by virtue of being Foreman. |
| Q10 Action that matters | Toolbox Talk conducted (Tier 1) + attendance captured (Tier 2) + training renewed (Tier 1 record). |

### §2.7 · Equipment (Pre-Op · DVIR · Asset Master · Asset Transfers · live)

| Q | Answer |
|---|---|
| Q1 Owner | Asset register owner = Equipment Manager / Shop Foreman · per-asset deployed owner = currently-deployed-job's PM via Asset Transfer · per-record (Pre-Op) owner = Operator on shift (S1 via FL login) |
| Q2 Inferable | Yes — Asset Transfer states which job currently holds the asset · job resolves to PM. |
| Q3 Transfers | Asset Transfer transition (dispatched · returned) automatically rotates per-asset deployed ownership between Shop and Job-PM. |
| Q4 Closes | Pre-Op submitted (per-shift record) · Asset returned (transfer terminal state). |
| Q5 Escalates | Pre-Op fail not addressed > 24h → Shop Foreman → Equipment Manager. Missed PM cycle > 30d → Equipment Manager → executive. |
| Q6 Executive | "Equipment with open defects > 7d · by asset" + "Assets overdue on PM cycle · by Shop Foreman". |
| Q7 NOT a task | Pre-Op is operational reality (operator can't start the machine without one). Asset Transfer notification to receiving PM. |
| Q8 NOT ack | "Receiving PM acknowledges transfer" forbidden — transfer-receipt is a state transition (operational event), not an ack. |
| Q9 NOT assign | Operator owns Pre-Op by virtue of operating; no "Assign Pre-Op" UI. |
| Q10 Action that matters | Pre-Op submission · defect remediation · maintenance completion. |

### §2.8 · Fleet (Vehicles · DVIR · Fleet Defects · Driver Qualification · future DOT Dashboard)

| Q | Answer |
|---|---|
| Q1 Owner | Vehicle register owner = Fleet Manager · per-vehicle deployed owner = assigned driver (S1 via FL identity + Fleet assignment) · per-defect owner = Fleet Manager until remediated |
| Q2 Inferable | Yes — driver assignment from Fleet system · Fleet Manager from workflow-class · DQ-file owner = HR + Fleet Manager (jointly) |
| Q3 Transfers | DVIR submitted clean → no transfer · DVIR with defect → Fleet Manager owns defect remediation · DQ-file item expiring → Fleet Manager + driver's manager. |
| Q4 Closes | DVIR submitted (per-shift record) · defect remediated · DQ-file item renewed. |
| Q5 Escalates | Defect open > 7d → Fleet Manager's manager. DQ-file item expired → manager + Safety Manager (DOT exposure). |
| Q6 Executive | "Fleet defects > SLA · by driver" + "DQ-file expirations next 30d · by driver" + DOT Compliance Action Console. |
| Q7 NOT a task | DVIR is operational reality (driver can't dispatch without one) · DQ-file expiration notification. |
| Q8 NOT ack | "Driver acknowledges DOT policy" forbidden (V-10 · Amendment 001). |
| Q9 NOT assign | Driver assignment comes from Fleet assignment record, not from any "Assign Vehicle" UI inside Fleet workflow. |
| Q10 Action that matters | DVIR submission · defect remediation · DQ-file renewal. |

### §2.9 · HR (Onboarding · Offboarding · Time Off · Performance · per HRIS HYBRID split)

| Q | Answer |
|---|---|
| Q1 Owner | Employee record owner = HR (workflow-class default) · per-employee operational owner = `manager_employee_id` (direct manager) · workflow event owner = role-gated per state (Time Off Approver = manager; Onboarding Field-side = Safety + Shop; Offboarding Field-side = PM + Equipment Manager) |
| Q2 Inferable | Yes — manager via `manager_employee_id` (G1-11 BUILD) · HR is workflow-class default. |
| Q3 Transfers | State transitions per workflow (Time Off REQUESTED→APPROVED→TAKEN). |
| Q4 Closes | Workflow-specific terminal state (Time Off TAKEN · Onboarding all field-side steps Tier-1 evidenced · Offboarding all field-side steps Tier-1 evidenced). HR-side terminal states owned by HRIS integration. |
| Q5 Escalates | Time Off REQUESTED > 5d → manager's manager. Onboarding open > 14d → Safety Manager. Offboarding open > 14d → Equipment Manager + Safety Manager. |
| Q6 Executive | "Onboarding incomplete > 14d · by manager" + "Open Time Off requests > 5d · by approver". |
| Q7 NOT a task | "HR needs to file the I-9" — that's HRIS workflow, not ForgedOps task. HR-side notifications cross-system. |
| Q8 NOT ack | OC-013 orientation checkbox · OC-014 exit-interview checkbox · "Employee acknowledges handbook" · "Employee acknowledges review" — all FAIL per Amendment 001. Replace with `safety_training_records` (Tier 1) + interview notes as data (Tier 1) + handbook download identity (Tier 3). |
| Q9 NOT assign | Manager via `manager_employee_id` · no "Assign to PM" UI for Onboarding. |
| Q10 Action that matters | Field-side training completion · PPE issuance · access provisioning · PPE return · access revocation. |

### §2.10 · Project Operations (Submittal · RFI · CO · Pay-App · Sub-Mgmt · Meeting-Minutes · per BUILD Wave 4)

| Q | Answer |
|---|---|
| Q1 Owner | All workflows: per-project owner = `jobs_master.primary_pm` (S2) · per-state role gate (Submittal Reviewer = Engineer · RFI Responder = Designer/Owner · CO Approver = Owner Rep · Pay-App Approver = Owner Rep + Architect) · per-record creator = Subcontractor or PM (S1) |
| Q2 Inferable | Yes — PM from project · counterparties stored in sub/owner contact records · workflow role gates per state. |
| Q3 Transfers | State transitions per workflow (Submittal PENDING→APPROVED · RFI OPEN→ANSWERED · CO PROPOSED→APPROVED · Pay-App SUBMITTED→PAID). Counterparty ownership encoded as "external owner" state, not assignment. |
| Q4 Closes | Workflow-specific terminal state · operational action (approval decision · response posted · payment confirmed via accounting integration). |
| Q5 Escalates | Aging in counterparty-owned state → PM's manager (informs PM to escalate externally). Aging in PM-owned state → PM's manager. |
| Q6 Executive | "RFIs open > 14d · by project" + "Submittals overdue > 30d · by project" + "Change Orders unapproved > 21d" + "Pay-Apps awaiting payment > 30d". |
| Q7 NOT a task | Counterparty notifications · accounting integration events. |
| Q8 NOT ack | "Acknowledge Receipt" forbidden across all 6 PM workflows (V-1, V-2, V-4 · Amendment 001). "Acknowledged" intermediate status forbidden (V-2). |
| Q9 NOT assign | PM via project ownership · counterparty via record metadata · no assignment UI. |
| Q10 Action that matters | Decision capture (approve/reject with reason) · response post · payment integration event. |

---

## §3 · Cross-workflow ownership equation

All 10 workflows share the same inference logic, expressible as one equation:

```
Owner(record, t) =
    role_gate( current_state(record, t) )
    ∩ project_owner( record.project_number )  if S2 applies
    ∩ workflow_class_default                  if S3 unspecified
    ∩ manager_ladder( prior_owner )           if escalation_breached
    ∩ creator( record )                       only if all above NULL
```

The function returns a single human at every moment. There is no "Unassigned" state. There is no "Assignee" field. There is no dropdown. **There is only inference from operational reality.**

---

## §4 · The "Should it become a task" filter

For every candidate work item the platform surfaces, the operator should apply this 3-question filter (rule 2 textbook):

| Filter Q | If YES | If NO |
|---|---|---|
| Does completing this require an operational action? | Continue to filter 2 | NOT a task — it's information (notification only) |
| Does the action change a workflow's state? | Continue to filter 3 | NOT a task — it's a side-effect or report consumption |
| Is the action gated to a single accountable person derived from §3 equation? | Surface as Action Console row | NOT a task — fix the inference equation before surfacing |

If all three are YES, the work item becomes an **Action Console row** owned by the inferred person. That row has a one-tap action affordance that performs the operational action and transitions state. There is no "Mark Done" button — completion is a side-effect of doing the operational action.

---

## §5 · The Final Question

> *If ForgedOps became the operating system for heavy civil construction, what ownership model would allow the company to run without creating more work for the people using it?*

**Answer:** The model in which **the operational record IS the task**. No parallel task object exists. No "Assign" UI exists. No "Accept" UI exists. No "Acknowledge" UI exists.

For every workflow the platform manages:
* The state machine names the role gate at every state (Constitution Rule 3 + Rule 4)
* The role gate plus project linkage plus manager hierarchy resolves to **one person** (Constitution Rule 6 + Rule 7 + Amendment 001)
* That person sees their own record in their own Action Console with a one-tap operational-action affordance (Override anti-checklist clause)
* If the person doesn't act within SLA, ownership escalates up the manager ladder automatically (Rule 7)
* The record exits the Console when the operational action completes, transitioning to the next state's owner (Rule 4 · Tier 1 evidence)

The people using ForgedOps never create work for each other. **Operational reality creates work** (a DR submitted · an incident reported · a variance flagged · a defect logged · a finding raised). ForgedOps's job is to put each piece of work in front of exactly one accountable person at exactly the right moment, automatically, without a single click between the work appearing and the right person seeing it.

That is the ownership model.

---

## §6 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code written | ✅ |
| Zero implementation plans | ✅ |
| Zero estimates generated | ✅ |
| Zero authorizations issued | ✅ |
| All 10 workflows × 10 questions answered | ✅ |
| Universal inference equation surfaced | ✅ |
| "Should it become a task" filter rendered | ✅ |
| Final question answered Constitutionally | ✅ |
| Anti-checklist clause honored (Action Console pattern) | ✅ |
| Anti-assignment clause honored (no Assignee field) | ✅ |
| Amendment 001 honored (no ack-as-work) | ✅ |

🛑 **STOPPED.**
