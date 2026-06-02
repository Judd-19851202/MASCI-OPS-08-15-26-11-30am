# OMEGA · CONSTITUTIONAL CONFLICT REGISTER

**Date:** 2026-06-02
**Mode:** READ-ONLY · evidence-only · zero code · zero re-scoring · zero redesign
**Governing doctrine:** `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md` (Part I + Part II)
**Method:** Cross-reference every recommendation, workflow, ownership model, escalation model, accountability model, future-roadmap item, Customer #2 / White-Label / Operations Center / ForgedOps v1 recommendation in the Phase-1A body of work against the 10 Friction Rules + Override.
**Findings preserved verbatim where cited. No prior audit modified.**

---

## §0 · Severity legend

| Code | Meaning |
|---|---|
| **P0 Constitutional Violation** | Recommendation directly violates one or more Rules and would produce checklist-software outcomes if built. Cannot be authorized as-currently-scoped. |
| **P1 High Risk** | Recommendation contains a click/notification/checklist component that violates a Rule. Salvageable with re-scope; would fail Constitution if built verbatim. |
| **P2 Moderate Risk** | Recommendation is Constitutionally compliant in intent but its current scoping language allows a non-compliant implementation. Requires explicit Constitutional guardrails before build. |
| **P3 Observation** | Recommendation does not violate the Constitution but should be re-evaluated under the 5 new audit axes before authorization. |

---

## §1 · Conflict register · 24 entries

### P0 · Constitutional Violations (4)

#### CV-1 · OC-005 "JHP Acknowledgement Ledger" — name and scope
* **Report:** `JHP_ACKNOWLEDGEMENT_GAP_REPORT.md` §4 (8 capability gaps), §7 (Options 1/2/3); `OPERATIONAL_COMPLETENESS_REGISTER.md` row OC-005; `OPERATIONAL_COMPLETENESS_EXECUTIVE_SUMMARY.md` §2 rank #8; `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §9 Top-10 #3
* **Recommendation:** Build a per-crew per-day acknowledgement ledger with capability 6 = "Acknowledgement UI (BilingualConsent + SignaturePad widget wired onto JhaPlansHub) — 'I have read this' affordance after download confirmation"
* **Rule(s) Impacted:** Rule 1 (Work Over Clicks) · Rule 2 (Information Is Not A Task) · Rule 5 (Public-Gate Simplicity)
* **Severity:** **P0 Constitutional Violation**
* **Rationale:** The literal name "Acknowledgement Ledger" and the proposed UI ("Click Acknowledge"/"Click Confirm I have read this") are the textbook examples Rule 1 forbids ("Bad: Click Acknowledge · Click Read · Click Confirm · Click Understood"). No corrective operational action is triggered by the acknowledgement; the ack EXISTS to document that the read occurred. This is "create work simply to document work" — the Core Principle's exact prohibition. Rule 5 also implicated: a Foreman would need to download PDF → return to app → tap consent → tap signature → tap submit just to register that they looked at the PDF.
* **Suggested Future Review:** Re-scope OC-005 from "acknowledgement ledger" to either (a) attendance-style record auto-derived from another operational event (e.g., JHP version pinned to a Toolbox Talk submission which IS work — Rule 7 compliant), or (b) eliminate the workflow if the OSHA/insurance question can be answered by the existing JHP upload + Toolbox Talk attendance pair, or (c) capture identity passively at the download endpoint (FSI Tier-1) without UI affordance and treat downloads as evidence — eliminating the click entirely. Operator decision required before any build authorization.

#### CV-2 · F-18 row 18 in Phase 1A Operational Certification Audit
* **Report:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §1 row 18 ("Acknowledge that I read the JHP" · 🔴 across Foreman/Super/PM/Safety)
* **Recommendation (implicit by listing as 🔴 gap):** Build acknowledge-JHP affordance to close 🔴 cells
* **Rule(s) Impacted:** Rule 1 · Rule 2
* **Severity:** **P0 Constitutional Violation**
* **Rationale:** Same defect class as CV-1. The "cannot complete" 🔴 indicator only signals a Constitutional violation if the missing affordance is a click. The Constitution says: if no action is required, no acknowledgement should be required. Building the affordance to turn 🔴 into 🟢 would violate Rule 1.
* **Suggested Future Review:** Do **not** count row 18 as a Phase-1A completion gap requiring an acknowledge UI. Either re-scope per CV-1 suggestions, or document that the row is Constitutionally exempt (acknowledgement is not required because no action follows).

#### CV-3 · Phase 1A Operational Certification Audit · Top-10 improvement #3
* **Report:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §9 Top-10 ranking #3 "OC-005 JHP Acknowledgement Ledger (Option 1 Minimum)"
* **Rule(s) Impacted:** Rule 1 · Rule 2 · supremacy clause
* **Severity:** **P0 Constitutional Violation**
* **Rationale:** Recommended for authorization in the top-10 list. Inherits CV-1's defect by reference.
* **Suggested Future Review:** Remove from Top-10 list pending operator re-scope decision per CV-1.

#### CV-4 · Vestigial JHA form field `stop_work_acknowledged`
* **Report:** `JHP_ACKNOWLEDGEMENT_GAP_REPORT.md` §1 ("grep returns ONLY `stop_work_acknowledged`"); `JHP_CODE_REALITY_AUDIT.md` (per `_INDEX.md` summary)
* **Recommendation:** OC-005 design proposes preserving the vestigial JHA system in this batch and addressing rename separately
* **Rule(s) Impacted:** Rule 1 · Rule 9 (Operator First — vestigial system that exists only for documentation)
* **Severity:** **P0 Constitutional Violation (existing surface)**
* **Rationale:** The `stop_work_acknowledged` boolean is a click-to-document field on a form that is itself vestigial. The audit notes 1 row in `db.jhas` (likely test data). Rule 1 violation by existence; Rule 9 violation because operations does not use it. This is identified here for the operator's awareness; remediation by code deletion is **not** authorized by this audit.
* **Suggested Future Review:** Operator may authorize a separate "vestigial-surface decommission" batch (out of scope here).

---

### P1 · High Risk (8)

#### HR-1 · ForgedOps Ownership v1 · Layer A (ownership primitive on lifecycle records)
* **Report:** `PHASE_1A_OPERATIONAL_OWNERSHIP_AUDIT.md` §7 Layer A
* **Recommendation:** Add 5 fields to every lifecycle record: `current_owner_user_id`, `current_owner_role`, `owner_assigned_at`, `owner_assigned_by`, `owner_due_at`
* **Rule(s) Impacted:** Rule 3 (One Owner — compliant) · Rule 6 (Minimize Human Decisions — at risk via `owner_assigned_by`) · Rule 7 (Accountability Must Be Automatic — at risk if assignment requires a manual UI)
* **Severity:** **P1 High Risk**
* **Rationale:** Layer A's intent — one named owner per workflow — aligns precisely with Rule 3. The field `owner_assigned_by` is concerning: if assignment is manual (a human picks the owner from a dropdown), Rule 6 (software decides routing/ownership) and Rule 7 (auto-accountability from workflow movement) are violated. The Constitution requires assignment to emerge from the workflow itself, not from a human decision at the time of assignment.
* **Suggested Future Review:** Re-scope Layer A so the assignment is ALWAYS derived (state-machine + role taxonomy + project_number → PM resolver) and `owner_assigned_by` records `system` or the state-machine transition that triggered the assignment, NEVER a human dropdown selection. Add explicit "no UI to manually assign" guardrail.

#### HR-2 · ForgedOps Ownership v1 · Layer C (escalation + reporting)
* **Report:** `PHASE_1A_OPERATIONAL_OWNERSHIP_AUDIT.md` §7 Layer C
* **Recommendation:** Nightly scheduler walks `current_owner_due_at`; first ping owner, then escalate to `manager_employee_id`, then escalate to executive aggregator. Plus an "Ownership Dashboard" surface.
* **Rule(s) Impacted:** Rule 8 (Reduce Operational Noise) · Rule 2 (Information Is Not A Task) · Rule 6 (Software decides escalation timing — compliant) · anti-checklist clause
* **Severity:** **P1 High Risk**
* **Rationale:** The escalation cascade is Constitutionally sound (Rule 7 + Rule 6) IF and ONLY IF Rule 8 is respected at every hop — i.e., the manager is notified ONLY when escalation triggers, NOT cc'd on every owner ping. The "Ownership Dashboard" risks the anti-checklist clause: a read-only list of open work that doesn't drive action becomes "audit software."
* **Suggested Future Review:** Add explicit Rule 8 routing discipline (single-recipient escalation hops, no department broadcasts) and replace "Ownership Dashboard" framing with "Action Console" (every list entry must have a one-tap operational affordance — close · reassign · request more info — never just a status pill).

#### HR-3 · OC-014 Employee Offboarding multi-step checklist
* **Report:** `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-014; `OPERATIONAL_COMPLETENESS_EXECUTIVE_SUMMARY.md` §2 rank #9
* **Recommendation:** "Multi-step lifecycles · checklist forcing PPE return + access deactivation + exit"
* **Rule(s) Impacted:** Rule 1 (Work Over Clicks — the term "checklist") · Rule 2 (Information Is Not A Task) · Rule 4 (Every Workflow Must End — compliant)
* **Severity:** **P1 High Risk**
* **Rationale:** A literal multi-step checklist is a Rule 1 violation if each "step" is a checkbox-style click rather than a discrete operational action. PPE return and access deactivation ARE operational actions (Rule 1 compliant); "exit interview" risks being a click-to-document step (Rule 2 violation).
* **Suggested Future Review:** Re-scope OC-014 so each step is an operational action with an external system consequence (return PPE → updates inventory; deactivate access → revokes IAM credentials; exit interview → captured as data with downstream HR use). If any step has no downstream consequence, remove it.

#### HR-4 · OC-018 Audit-trail uplift for 11 flag-only workflows
* **Report:** `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-018; `AUDIT_TRAIL_COVERAGE_REPORT.md` (per `_INDEX.md` summary)
* **Recommendation:** Add audit-trail collections to 11 workflows (CAPA · Asset Transfers · Fleet Defects · DVIR · Suppliers · Jobs · Equipment Master · Documents · Time Off · Document Expirations · Vendors)
* **Rule(s) Impacted:** Rule 2 (Information Is Not A Task) · anti-checklist clause · Rule 9 (Operator First)
* **Severity:** **P1 High Risk**
* **Rationale:** Audit-trail enrichment without a downstream operational consumer is pure documentation-of-documentation — the precise pattern Rule 2 + the anti-checklist clause forbid. The 11 workflows already function operationally; adding audit collections to satisfy "auditability" criteria without an operations consumer violates Rule 9 ("Audit Perfection vs Operational Practicality — Operational Practicality wins").
* **Suggested Future Review:** Re-scope OC-018 to enrich audit ONLY for those flag-only workflows whose audit data feeds an operational consequence (e.g., a CAPA audit trail that drives the Ownership Dashboard's "stuck CA" alert is Constitutionally compliant; an Asset Transfer audit trail that is only read in a periodic compliance review is not).

#### HR-5 · Site Inspection "Acknowledge findings" closure step (OC-004)
* **Report:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §1 row 13 ("Close Site Inspection · acknowledge findings" 🟠/🟡); `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-004
* **Recommendation (implicit):** iter453 OC-004 build would add an "acknowledge findings" affordance
* **Rule(s) Impacted:** Rule 1 (Work Over Clicks)
* **Severity:** **P1 High Risk**
* **Rationale:** If "acknowledge findings" is a click affordance, Rule 1 violation. If it is "PM/Safety records a remediation plan for each finding" then it is operational work (Rule 1 compliant).
* **Suggested Future Review:** Re-scope iter453 OC-004 so closure requires either (a) a remediation action recorded per finding, or (b) a resolved/dismissed disposition with operational consequence — NOT a checkbox click.

#### HR-6 · QA/QC Deficiency closure (OC-003) "Mark Resolved" pattern
* **Report:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §1 row 11; `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-003
* **Recommendation:** iter453 OC-003 would add per-deficiency status with resolve/re-inspect transitions
* **Rule(s) Impacted:** Rule 1 (Work Over Clicks) · Rule 4 (Every Workflow Must End — compliant)
* **Severity:** **P1 High Risk**
* **Rationale:** "Mark Resolved" is Constitutionally compliant if resolution is paired with an operational action (corrective work recorded, re-inspection performed). It is non-compliant if it is a status-pill change without operational consequence.
* **Suggested Future Review:** Re-scope iter453 OC-003 to require a corrective-action record OR a re-inspection event as the resolution trigger, not a standalone status flip.

#### HR-7 · iter445 added "Has crew reviewed the JHP today?" field on `NewDailyReport.jsx`
* **Report:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §2 F-1 ("optionally 'Has crew reviewed the JHP today?' type fields")
* **Recommendation (existing surface):** Field exists today
* **Rule(s) Impacted:** Rule 1 (Work Over Clicks) · Rule 2 (Information Is Not A Task)
* **Severity:** **P1 High Risk (existing surface)**
* **Rationale:** A Yes/No "Has crew reviewed the JHP today?" checkbox is the textbook Rule 1 violation. No action follows the answer. The answer cannot be verified. It IS a "click to document a click."
* **Suggested Future Review:** Operator may authorize a separate batch to either (a) remove the field, or (b) replace it with an operational derivation (e.g., crew member identity captured at JHP download).

#### HR-8 · "Auto-fan-out notifications" pattern from iter452 (DR PENDING_REVIEW → fan-out to PM + Safety + Admin)
* **Report:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §3 A-2/A-11; `_INDEX.md` iter452 entry "Notification fan-out on PENDING_REVIEW to PM/Safety/Admin"
* **Recommendation (existing surface):** Three roles notified per DR
* **Rule(s) Impacted:** Rule 8 (Reduce Operational Noise)
* **Severity:** **P1 High Risk (existing surface)**
* **Rationale:** Rule 8 explicitly says "Do not notify: entire departments · large groups · people with no required action." Notifying PM AND Safety AND Admin on every PENDING_REVIEW transition fans out to 3 recipients when (per Rule 3) only one of them owns the next action.
* **Suggested Future Review:** Re-scope notification dispatch so only the *current owner* receives the notification; others can observe via dashboard. Tied to HR-1 (Layer A current_owner field) — once one owner is identified per workflow, single-recipient notification is mechanically possible.

---

### P2 · Moderate Risk (7)

#### MR-1 · iter453 OC-003 + OC-004 BUILD (Phase 1A follow-up workflows)
* **Report:** `OPERATIONAL_COMPLETENESS_EXECUTIVE_SUMMARY.md` §5 Phase 1B; `_INDEX.md` iter452.5 entry
* **Recommendation:** Build OC-003 (QA/QC follow-up) and OC-004 (Site Inspection follow-up)
* **Rule(s) Impacted:** Rule 1 · Rule 4 · Rule 7 · new mandatory axis "User Friction"
* **Severity:** **P2 Moderate Risk**
* **Rationale:** Both are needed under Rule 4 (every workflow must end). Constitutional compliance depends entirely on whether closure requires operational action (compliant) or a click (non-compliant). Tied to HR-5 and HR-6.
* **Suggested Future Review:** Re-scope iter453 design to specify *what operational action* triggers closure, NOT a status-pill click. Add explicit "no Acknowledge button" guardrail.

#### MR-2 · OC-010 Status Vocabulary Canonicalization (Phase 1B)
* **Report:** `STATUS_VOCABULARY_AUDIT.md`; `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-010
* **Recommendation:** Canonicalize 18 status vocabularies into a single map
* **Rule(s) Impacted:** Rule 2 (Information Is Not A Task) · Rule 6 (Software decides status progression — compliant) · Rule 10 (Toy Airplane Frontend — compliant if status simplification reduces UX surface)
* **Severity:** **P2 Moderate Risk**
* **Rationale:** Canonicalization that REDUCES vocabulary count is Constitutionally aligned with Rule 10. Canonicalization that introduces MORE status labels per workflow (multi-step states) risks Rule 2 (status as information without action).
* **Suggested Future Review:** Re-scope to net-negative vocab change: every canonical status must trigger a downstream action, OR be removable.

#### MR-3 · iter455 + iter455.1 Phase 1A Integration Certification + Accountability Chain Projection
* **Report:** `PHASE1A_BUILD_PLAN.md` (per `_INDEX.md` summary); `ITER452_5_1_CERTIFICATION_REPORT.md`
* **Recommendation:** Bundle certification + chain projection in one batch
* **Rule(s) Impacted:** anti-checklist clause · new mandatory axis "Operational Practicality"
* **Severity:** **P2 Moderate Risk**
* **Rationale:** "Integration Certification" reports are documentation about documentation unless they have a forward-looking operational use (operator decision support · regression-prevention · onboarding). At risk of becoming "audit software."
* **Suggested Future Review:** Re-scope iter455 so its certification artifact is consumed by an operational surface (e.g., Action Console health pill), NOT only filed as evidence.

#### MR-4 · Operations Center build (forward-looking · current readiness 5/100)
* **Report:** `FORGEDOPS_OPERATIONS_READINESS.md` (per `_INDEX.md` summary); `OPERATIONAL_COMPLETENESS_EXECUTIVE_SUMMARY.md` §10
* **Recommendation:** Build customer-facing support portal · tickets · tenancy (~92-108 dev-days)
* **Rule(s) Impacted:** All Rules · anti-checklist clause · Rule 10
* **Severity:** **P2 Moderate Risk**
* **Rationale:** A support portal at risk of becoming "ticket-checklist software." Constitutional compliance requires every Ops Center surface to be an action surface (resolve · escalate · close), never a read-only ticket list.
* **Suggested Future Review:** Operator should mandate that the Operations Center MVP scope is constrained to Constitutional surfaces (every list entry has one-tap action affordance · zero acknowledgement steps · single-owner contract).

#### MR-5 · Customer #2 Tenant-Isolation Rebuild (`tenant_id` on every collection)
* **Report:** `CUSTOMER2_BLOCKER_MATRIX.md`; `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §5
* **Recommendation:** Add `tenant_id` propagation; rebuild query scoping
* **Rule(s) Impacted:** Rule 9 (Operator First) · neutral on most Rules
* **Severity:** **P2 Moderate Risk**
* **Rationale:** Constitutional neutrality on multi-tenancy itself. Risk is in Rule 9: if tenant rebuild forces existing operations through a slower or more complex UX, operations loses.
* **Suggested Future Review:** Mandate zero UX regression for MASCI users during tenant rebuild. Tenant rebuild must remain backend-only from the operator's perspective.

#### MR-6 · White-Label Brand-Config Layer (~5 weeks AFTER tenant isolation)
* **Report:** `WHITE_LABEL_BLOCKERS.md`; `PILLAR1_WHITE_LABEL_READINESS_REPORT.md`; `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §6
* **Recommendation:** Replace hard-coded MASCI literals with `BRAND.name` lookups; introduce logo/color/copy registries
* **Rule(s) Impacted:** Constitutionally neutral · observation: Rule 10 risk if introduces config UI for non-operators
* **Severity:** **P2 Moderate Risk**
* **Rationale:** Brand-config work doesn't violate the Constitution by itself but is at risk of producing an admin-config surface that operators must navigate.
* **Suggested Future Review:** Brand config should be a one-time-per-tenant operation, ideally set during tenant provisioning, never a recurring admin task.

#### MR-7 · OC-013 Employee Onboarding multi-step
* **Report:** `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-013
* **Recommendation:** Multi-step orientation/I-9/training-assign checklist
* **Rule(s) Impacted:** Rule 1 (Work Over Clicks · "checklist") · Rule 4 (compliant)
* **Severity:** **P2 Moderate Risk**
* **Rationale:** Same defect class as HR-3 OC-014. I-9 capture and training-assign are operational actions (Rule 1 compliant). "Orientation completed?" checkbox is not (Rule 1 violation).
* **Suggested Future Review:** Re-scope each step to operational action with downstream consequence.

---

### P3 · Observations (5)

#### O-1 · iter452.5.2 Resend Bounce Webhook (P1 pre-authorized)
* **Report:** `ITER452_5_1_CERTIFICATION_REPORT.md`; `_INDEX.md` iter452.5.1 entry
* **Recommendation:** Webhook auto-detects bounces, marks delivery-evidence event, retries via next tier of FSI ladder
* **Rule(s) Impacted:** Rule 7 (Accountability Must Be Automatic — strongly compliant)
* **Severity:** **P3 Observation · STRONG CONSTITUTIONAL ALIGNMENT**
* **Rationale:** Software auto-detects bounce → software escalates to next tier → zero human clicks. Textbook Rule 7.
* **Suggested Future Review:** None. Proceed as already authorized.

#### O-2 · ForgedOps Ownership v1 · Layer B (auto-task projection)
* **Report:** `PHASE_1A_OPERATIONAL_OWNERSHIP_AUDIT.md` §7 Layer B
* **Recommendation:** When lifecycle record enters a state with a defined owner-role, auto-create a row in `tasks`; auto-close on state advance
* **Rule(s) Impacted:** Rule 7 (compliant) · Rule 6 (compliant)
* **Severity:** **P3 Observation · STRONG CONSTITUTIONAL ALIGNMENT**
* **Rationale:** Tasks emerge from workflow movement, never from human clicks. Auto-close on state advance eliminates the "0/736 ever closed" pathology cited in the Ownership Audit.
* **Suggested Future Review:** None. Conceptually compliant; build scope review at authorization time per Rule 8 (single-recipient assignment).

#### O-3 · OC-009 Photo Delete / Orphan Janitor
* **Report:** `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-009
* **Recommendation:** Automated janitor cleans orphan rows; per-photo delete endpoint for admin
* **Rule(s) Impacted:** Rule 6 (Software makes the decision — compliant) · Rule 7 (compliant)
* **Severity:** **P3 Observation · STRONG CONSTITUTIONAL ALIGNMENT**
* **Rationale:** Janitor is software-only. Per-photo delete is operational action.
* **Suggested Future Review:** None.

#### O-4 · Continuity Events edit/close (OC-016)
* **Report:** `OPERATIONAL_COMPLETENESS_REGISTER.md` OC-016
* **Recommendation:** Add edit + close to Continuity Events
* **Rule(s) Impacted:** Rule 4 (compliant) · Rule 2 (potential violation if Continuity Events are purely informational)
* **Severity:** **P3 Observation**
* **Rationale:** Need to verify whether Continuity Events drive operational action or are informational. If informational, "edit/close" should be either removed (no action required) or only an admin-grade correction surface.
* **Suggested Future Review:** Operator clarification needed.

#### O-5 · F-21 / A-11 "Whole-department notifications" baseline
* **Report:** `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §3 A-11; `PUBLIC_GATE_WORKFLOW_ACCOUNTABILITY_REPORT.md`
* **Recommendation (existing surface):** Multi-recipient routing patterns exist across PM/Safety/Admin fan-outs
* **Rule(s) Impacted:** Rule 8 (Reduce Operational Noise)
* **Severity:** **P3 Observation**
* **Rationale:** A platform-wide audit pass under Rule 8 should be considered. Documented here as observation — remediation would be a separate authorized batch.

---

## §2 · Conflict tally

| Severity | Count |
|---:|---:|
| P0 Constitutional Violation | **4** |
| P1 High Risk | **8** |
| P2 Moderate Risk | **7** |
| P3 Observation | **5** |
| **TOTAL** | **24** |

---

## §3 · Constitutional-failure root-cause clustering

The 24 conflicts cluster into 5 root-cause patterns:

| Cluster | Conflicts | Root cause |
|---|---|---|
| **Acknowledgement-as-work** | CV-1, CV-2, CV-3, CV-4, HR-7 | Recommendation treats a click that documents "I saw this" as a tracked workflow step |
| **Checklist-as-workflow** | HR-3, HR-4, MR-2, MR-7 | Recommendation adds steps/states/labels that don't trigger operational action |
| **Multi-recipient notification** | HR-8, O-5 | Recommendation notifies > 1 role for events with a single owner |
| **Dashboard-as-deliverable** | HR-2 (Ownership Dashboard), MR-3, MR-4 | Recommendation produces a read-only list without action affordances |
| **Manual assignment risk** | HR-1, HR-5, HR-6 | Recommendation allows a human dropdown selection where software could derive |

Of the 24 conflicts, **0 are unresolvable.** All 24 are re-scopable inside Phase 1A/1B/2 envelopes by tightening the Rule 1/2/3/6/7/8 contract.

---

## §4 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero re-scoring of existing audits | ✅ |
| Zero recommendations rewritten | ✅ |
| Every conflict cites Report · Section · Rule · Severity · Rationale | ✅ |
| Every conflict has Suggested Future Review (NOT a design) | ✅ |
| 4 P0 violations explicit | ✅ |
| 24 total conflicts catalogued | ✅ |
| Findings preserved exactly as in source reports | ✅ |

🛑 **STOPPED.** Identify conflicts. Document conflicts. Stop.


---

## §5 · AMENDMENT 001 IMPACT NOTE (appended 2026-06-02)

Constitutional Amendment 001 ("Evidence Over Acknowledgement" · Rule 11 + 4-tier Evidence Hierarchy + Constitutional Test) was issued by the operator on 2026-06-02 and registered in `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md` Part IV. The Amendment strengthens but does NOT re-rank the existing 24 conflicts:

* **CV-1 OC-005 JHP Acknowledgement Ledger** — now also violates Rule 11; the Amendment's worked JHP Example matches CV-1 verbatim. Severity unchanged (P0).
* **CV-2 F-18 Acknowledge JHP** — now also violates Rule 11. Severity unchanged (P0).
* **CV-3 Top-10 Improvement #3 = OC-005 build** — now also violates Rule 11. Severity unchanged (P0).
* **CV-4 vestigial `stop_work_acknowledged`** — now also violates Rule 11. Severity unchanged (P0).
* **HR-7 iter445 DR "Has crew reviewed?" field** — now also violates Rule 11. Severity unchanged (P1).

**Constitutional Test ("What operational problem is solved by requiring this acknowledgement?") becomes a mandatory pre-build gate** for every future acknowledgement-workflow proposal. Items returning "None" shall not be built.

**Conflict count unchanged at 24.** Per OMEGA scope, this batch is forbidden from re-ranking. Companion validation sweep (`AMENDMENT001_VALIDATION_AUDIT.md` et al.) catalogues 18 acknowledgement concepts platform-wide (9 PASS · 2 FAIL · 7 REPLACE) without modifying this Register.

