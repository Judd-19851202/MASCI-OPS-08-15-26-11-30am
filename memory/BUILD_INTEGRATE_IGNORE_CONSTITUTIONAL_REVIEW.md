# OMEGA · BUILD / INTEGRATE / IGNORE — CONSTITUTIONAL REVIEW

**Date:** 2026-06-02 · Companion to `BUILD_INTEGRATE_IGNORE_MASTER_REGISTER.md`
**Mode:** READ-ONLY · zero code · zero redesign · zero implementation plan · zero estimates
**Method:** Audit every classification in the BUILD / INTEGRATE / HYBRID / IGNORE master register against the binding governance set — Constitution Parts I–IV (10 Friction Rules + Amendment 001 Rule 11) + Constitutional Override (Supremacy + 5 mandatory audit axes + 3-criterion success test + anti-checklist clause). Mark each item PASS / REVIEW REQUIRED / CONSTITUTIONAL CONFLICT. Surface latent conflicts only — do NOT resolve.

---

## §0 · Verdict legend

| Code | Meaning |
|---|---|
| ✅ **PASS** | Classification is Constitutionally clean as stated · no operator review required |
| 🟡 **REVIEW REQUIRED** | Classification is sound but scope/posture needs an operator decision before any future build/integrate authorization |
| 🔴 **CONSTITUTIONAL CONFLICT** | Classification as currently stated would violate Constitution or Amendment 001 if executed · must be re-scoped or eliminated |

---

## §1 · 48-gap classification review

### G0 · Day-to-day blockers (12 items)

| # | Gap | Class | Verdict | Constitutional grounding / latent conflict |
|---|---|---|---|---|
| G0-1 | Job costing not in ForgedOps | 🔗 INTEGRATE | ✅ PASS | Rule 9 (Operator First · don't rebuild) · Build/Integrate/Ignore Doctrine textbook |
| G0-2 | Master schedule not in ForgedOps | 🔗 INTEGRATE | ✅ PASS | Rule 9 · Doctrine textbook |
| G0-3 | Submittal workflow absent | 🔨 BUILD | 🟡 REVIEW REQUIRED | Constitutional-clean ONLY if the workflow does NOT include "Acknowledge Receipt" steps (V-1) · Amendment 001 must gate scoping |
| G0-4 | RFI workflow absent | 🔨 BUILD | 🟡 REVIEW REQUIRED | Same as G0-3 · "Acknowledged" intermediate status (V-2) is a Rule 11 violation if built |
| G0-5 | Change-order workflow absent | 🔨🔗 HYBRID | 🟡 REVIEW REQUIRED | Multi-step approval ack chains (V-3) violate Rule 8; approval decisions are Tier 1 if data captured · scope must split decision-content from ack-click |
| G0-6 | Pay-application workflow absent | 🔨🔗 HYBRID | 🟡 REVIEW REQUIRED | Same posture as G0-5 · approval decision content = PASS; "I acknowledge" ride-along = FAIL |
| G0-7 | Field clock-in/out per employee | 🔨 BUILD | ✅ PASS | Rule 7 (Accountability Must Be Automatic) · Tier 1 work-performed evidence by construction · GPS replaces "I am at the correct jobsite" attestation (V-6) |
| G0-8 | Production tracking by activity | 🔨 BUILD | ✅ PASS | Rule 7 · Tier 1 production data · zero ack workflow |
| G0-9 | Subcontractor management | 🔨🔗 HYBRID | 🟡 REVIEW REQUIRED | "Sub acknowledges scope" (V-12) violates Rule 11 · contract execution = PASS · ack click = FAIL |
| G0-10 | Three parallel Corrective-Action systems | 🔨 BUILD (canonicalize) | ✅ PASS | Rule 3 (One Owner) · Rule 6 (Minimize Human Decisions) · canonicalization is anti-fragmentation |
| G0-11 | 0/736 user-level task assignment | 🔨 BUILD | ✅ PASS | Rule 7 + Rule 6 · Layer A+B is auto-derived from state machine · no manual-assign UI (Layer A risk per Conflict Register P1) must remain prohibited |
| G0-12 | iter445 "Has crew reviewed JHP?" Yes/No | 🚫 IGNORE | ✅ PASS | Amendment 001 FAIL-1 textbook · Rule 1 + Rule 11 · eliminate |

### G1 · Scalability / Executive visibility (14 items)

| # | Gap | Class | Verdict | Constitutional grounding / latent conflict |
|---|---|---|---|---|
| G1-1 | Executive role + portfolio | 🔨 BUILD | 🟡 REVIEW REQUIRED | Must be **Action Console** (Override anti-checklist clause), NOT read-only dashboard. Every executive entry needs one-tap action affordance. Latent risk: "Executive acknowledges weekly KPIs" (V-13) is Rule 1 + Rule 2 + anti-checklist violation. |
| G1-2 | Per-PM accountability scorecard | 🔨 BUILD | ✅ PASS | Rule 7 · accountability_projection consumer · Action Console pattern |
| G1-3 | Portfolio rollup | 🔨 BUILD | 🟡 REVIEW REQUIRED | Same posture as G1-1 — must be Action Console not Dashboard |
| G1-4 | Backlog / bid pipeline | 🔗 INTEGRATE | ✅ PASS | Rule 9 · CRM owns · out of mission |
| G1-5 | WIP / forecast-to-complete | 🔗 INTEGRATE | ✅ PASS | Rule 9 · Accounting owns · ForgedOps surfaces |
| G1-6 | OSHA 300/301/300A generator | 🔨 BUILD | ✅ PASS | Rule 7 (regulatory artifact auto-generated) · 300A signature is the only legally-required Tier 4 ride-along · permitted |
| G1-7 | Driver Qualification File | 🔨 BUILD | 🟡 REVIEW REQUIRED | "Driver acknowledges DOT policy" annual click (V-10) is Rule 11 violation if scoped. DQ-file scope must be document-management + expiration tracking, NOT annual ack ritual. |
| G1-8 | DOT compliance dashboard | 🔨 BUILD | 🟡 REVIEW REQUIRED | Must be Action Console (anti-checklist) · expirations + violations + missing docs each tied to one-tap remediation action |
| G1-9 | Performance review | 🔗 INTEGRATE | ✅ PASS | Rule 9 · HRIS owns · "Employee acknowledges review" (V-8) would be Rule 11 violation anyway |
| G1-10 | Discipline tracking | 🔨🔗 HYBRID | 🟡 REVIEW REQUIRED | Safety-incident-tied discipline chain is Tier 1 operational decision content (PASS). Pure HR discipline → HRIS (PASS). Boundary line is the operator's call. |
| G1-11 | `manager_employee_id` | 🔨 BUILD | ✅ PASS | Rule 8 routing foundation · Rule 3 enforcement primitive |
| G1-12 | `tenant_id` propagation | 🔨 BUILD | ✅ PASS | Architectural foundation · Rule 9 (build the platform, not the workflow) |
| G1-13 | Multi-tenant auth / SSO | 🔨🔗 HYBRID | ✅ PASS | Auth provider INTEGRATE (Rule 9) · tenant boundary BUILD (architectural) |
| G1-14 | "What's mine across the platform" view | 🔨 BUILD | ✅ PASS | Rule 3 (One Owner) · Rule 4 (Every Workflow Must End) · highest-named friction in operator audit |

### G2 · Adoption / Operational clarity (15 items)

| # | Gap | Class | Verdict | Constitutional grounding / latent conflict |
|---|---|---|---|---|
| G2-1 | OC-003 QA/QC follow-up | 🔨 BUILD | 🟡 REVIEW REQUIRED | Amendment 001 REPLACE-5: closure must require operational action (`corrective_actions` OR re-inspection) · NOT "Mark Resolved" ack click. Re-scope before build. |
| G2-2 | OC-004 Site Inspection follow-up | 🔨 BUILD | 🟡 REVIEW REQUIRED | Amendment 001 REPLACE-4: closure must require operational action · NOT "Acknowledge findings" ack |
| G2-3 | OC-008 PPE Return | 🔨 BUILD | ✅ PASS | Rule 7 · operational action · Tier 1 evidence by construction |
| G2-4 | Maintenance work-order | 🔗 INTEGRATE | ✅ PASS | Rule 9 · MaintainX owns · operator explicitly named |
| G2-5 | Equipment utilization-by-job | 🔨 BUILD | ✅ PASS | Rule 7 · consumer of existing Tier 1 primitives · zero ack pattern |
| G2-6 | Fuel-card integration | 🔗 INTEGRATE | ✅ PASS | Rule 9 · fuel vendor owns · out of mission |
| G2-7 | OC-013 Onboarding multi-step | 🔨🔗 HYBRID | 🟡 REVIEW REQUIRED | Amendment 001 REPLACE-7: orientation checkbox must be replaced by `safety_training_records` (Tier 1) OR attendance roster (Tier 2) · NOT click. HR-side (I-9/benefits) → HRIS. |
| G2-8 | OC-014 Offboarding multi-step | 🔨🔗 HYBRID | 🟡 REVIEW REQUIRED | Amendment 001 REPLACE-6: exit-interview checkbox → notes captured as Tier 1 data. Field-side PPE return/access revoke = PASS. HR-side (final-pay/COBRA) → HRIS. |
| G2-9 | Benefits administration | 🔗 INTEGRATE | ✅ PASS | Rule 9 · HRIS / benefits broker owns |
| G2-10 | ATS / recruiting | 🔗 INTEGRATE | ✅ PASS | Rule 9 · ATS owns |
| G2-11 | MSDS / SDS library | 🔗 INTEGRATE | ✅ PASS | Rule 9 · Velocity/KHA/3E owns |
| G2-12 | Drug-test pool | 🔗 INTEGRATE | ✅ PASS | Rule 9 · HIPAA-bounded · vendor owns chain-of-custody |
| G2-13 | Workers comp claim | 🔗 INTEGRATE | ✅ PASS | Rule 9 · carrier owns · ForgedOps links incident→claim ID |
| G2-14 | Lien-waiver tracking | 🔨🔗 HYBRID | ✅ PASS | Document tracking is Tier 1 · financial linkage to accounting |
| G2-15 | Meeting-minutes capture | 🔨 BUILD | 🟡 REVIEW REQUIRED | "Read and Acknowledged" on minutes (V-5) is Rule 11 violation. Scope must be minutes-as-data, NOT minutes-as-ack-target. |

### G3 · Cosmetic / convenience (7 items)

| # | Gap | Class | Verdict | Constitutional grounding |
|---|---|---|---|---|
| G3-1 | OC-006 Safety Meeting amend | 🔨 BUILD | ✅ PASS | Existing primitive completion · zero new ack pattern |
| G3-2 | OC-016 Continuity Events edit/close | 🔨 BUILD | ✅ PASS | Existing primitive completion |
| G3-3 | OC-017 Safety digest fire relocation | 🔨 BUILD | ✅ PASS | Rule 9 (Operator First) · surface relocation |
| G3-4 | OC-019 Casing normalization | 🚫 IGNORE | ✅ PASS | Cosmetic · no operational consequence · IGNORE is correct |
| G3-5 | OC-022 Reopen actions across 14 workflows | 🔨 BUILD | ✅ PASS | Rule 4 (Every Workflow Must End) extension · audited reopen-with-reason already proven in iter451/iter452 |
| G3-6 | OC-009 Photo Janitor | 🔨 BUILD | ✅ PASS | Rule 6/7 strong alignment · listed as Constitutional exemplar in Compliance Sweep |
| G3-7 | Closure-attestation modal | 🔨 KEEP | ✅ PASS | Already PASS per Amendment 001 §10 · preserve |

---

## §2 · 11 external dependency strategy review

| # | Dependency | Strategy | Verdict | Constitutional grounding |
|---|---|---|---|---|
| EX-1 | Accounting / ERP | INTEGRATE — BLOCKING | ✅ PASS | Rule 9 textbook · Doctrine textbook · blocking flag itself is informational |
| EX-2 | Payroll processor | INTEGRATE — REQUIRED | ✅ PASS | Rule 9 · variance reconciliation already partially live |
| EX-3 | Project scheduling (P6/HCSS) | INTEGRATE — RECOMMENDED | ✅ PASS | Rule 9 |
| EX-4 | ELD / Telematics (Motive) | INTEGRATE — REQUIRED | ✅ PASS | Rule 9 · hardware/regulatory non-negotiable |
| EX-5 | IFTA | INTEGRATE — OPTIONAL | ✅ PASS | ELD-bundled · no Constitutional posture |
| EX-6 | Drug-test pool | INTEGRATE — RECOMMENDED | ✅ PASS | Rule 9 · HIPAA-bounded |
| EX-7 | Workers comp carrier | INTEGRATE — RECOMMENDED | ✅ PASS | Rule 9 · litigation-sensitive |
| EX-8 | OSHA portal | INTEGRATE — REGULATORY | ✅ PASS | Rule 9 · government system |
| EX-9 | Benefits administration | INTEGRATE — OPTIONAL | ✅ PASS | Rule 9 · ACA-regulated |
| EX-10 | ATS / recruiting | INTEGRATE — OPTIONAL | ✅ PASS | Rule 9 |
| EX-11 | MSDS / SDS library | INTEGRATE — RECOMMENDED | ✅ PASS | Rule 9 · subscription product |

All 11 strategy classifications PASS. The Build/Integrate/Ignore Doctrine is an extension of Rule 9 (Operator First — integrate, don't rebuild), and every INTEGRATE assignment honors that rule.

---

## §3 · Top 10 capabilities review

| Rank | Capability | Class | Verdict | Constitutional grounding |
|---:|---|---|---|---|
| 1 | Universal Ownership Layer (A+B) | 🔨 BUILD | ✅ PASS | Rule 3 + Rule 6 + Rule 7 textbook · explicit prohibition of manual-assign UI must remain enforced |
| 2 | Field Clock-in/out | 🔨 BUILD | ✅ PASS | Rule 7 · Tier 1 by construction · zero ack |
| 3 | Production Tracking by Activity | 🔨 BUILD | ✅ PASS | Rule 7 · Tier 1 production data |
| 4 | Executive Role + Action Console | 🔨 BUILD | 🟡 REVIEW REQUIRED | Must remain Action Console pattern (anti-checklist clause) · no "weekly KPI ack" ride-along (V-13) |
| 5 | iter453 OC-003 + OC-004 Closure-Action | 🔨 BUILD | 🟡 REVIEW REQUIRED | Amendment 001 REPLACE-4 + REPLACE-5 unresolved · closure-action contract must be operator-decided before build |
| 6 | OSHA 300/301/300A Generator | 🔨 BUILD | ✅ PASS | Rule 7 · 300A signature legally required Tier 4 ride-along |
| 7 | DOT Compliance + DQ-File | 🔨 BUILD | 🟡 REVIEW REQUIRED | "Driver acknowledges DOT policy" (V-10) annual-ack ritual must be excluded from scope |
| 8 | OC-005 JHP Evidence (re-scoped) | 🔨 BUILD (re-scope) | 🟡 REVIEW REQUIRED | Amendment 001 P0 CV-1 · operator must select one of 8 options in `AMENDMENT001_EXECUTIVE_SUMMARY.md §5` before any build |
| 9 | Subcontractor Management | 🔨🔗 HYBRID | 🟡 REVIEW REQUIRED | "Sub acknowledges scope" (V-12) must be excluded · contract execution is the Tier 1 evidence |
| 10 | Notification Routing per Rule 8 + iter452.5.2 | 🔨 BUILD | ✅ PASS | Rule 8 textbook · already pre-authorized · strongest Constitutional alignment per Compliance Sweep |

---

## §4 · Top 5 greenfield capabilities review

| Rank | Greenfield | Class | Verdict | Constitutional grounding |
|---:|---|---|---|---|
| 1 | Field Clock-in/out (B-8) | 🔨 BUILD | ✅ PASS | Same as Top 10 #2 |
| 2 | Production Tracking by Activity (B-9) | 🔨 BUILD | ✅ PASS | Same as Top 10 #3 |
| 3 | Executive Role + Action Console (B-11 + B-12) | 🔨 BUILD | 🟡 REVIEW REQUIRED | Same as Top 10 #4 |
| 4 | OSHA 300/301/300A Generator (B-15) | 🔨 BUILD | ✅ PASS | Same as Top 10 #6 |
| 5 | DQ-File + DOT Dashboard (B-23 + B-24) | 🔨 BUILD | 🟡 REVIEW REQUIRED | Same as Top 10 #7 |

---

## §5 · IGNORE list review

The 48 items on the IGNORE list (`FORGEDOPS_IGNORE_LIST.md`) are reviewed in aggregate rather than per-line, because each item already includes its doctrine citation.

| IGNORE category | Items | Verdict | Constitutional grounding |
|---|---:|---|---|
| Amendment 001 acknowledgement-as-work violations | 18 | ✅ PASS | Rule 11 textbook · every item answers "What operational problem does this acknowledgement solve?" with NONE |
| Mature-system replacement avoidance | 22 | ✅ PASS | Rule 9 + Build/Integrate/Ignore Doctrine textbook |
| Architectural / UX anti-patterns | 8 | ✅ PASS | Override anti-checklist clause + Rule 1 + Rule 7 + Rule 8 |

All 48 IGNORE items PASS. The IGNORE list is Constitutionally airtight as scoped.

---

## §6 · Aggregate verdict tally

| Verdict | Count | % |
|---|---:|---:|
| ✅ PASS | **36** | 75 % |
| 🟡 REVIEW REQUIRED | **12** | 25 % |
| 🔴 CONSTITUTIONAL CONFLICT | **0** | 0 % |
| **TOTAL items reviewed** | **48** (gaps) + **11** (external) + **10** (Top 10) + **5** (Top 5 greenfield) = **74 line-items** plus aggregate IGNORE-list review | |

Zero items currently classified as outright CONSTITUTIONAL CONFLICT because the prior batches (Compliance Sweep + Amendment 001 Validation Sweep) already absorbed the worst offenders into the IGNORE list and the REPLACE candidates set. The 12 REVIEW REQUIRED items are the **remaining latent risks** — they pass classification but require operator-level scoping decisions before they can be authorized for build.

---

## §7 · REVIEW REQUIRED roll-up

The 12 REVIEW REQUIRED items cluster into 4 forward-binding doctrines that any future operator authorization must honor:

### Cluster A · "Anti-checklist clause must be enforced at scoping" (4 items)
* G1-1 Executive role
* G1-3 Portfolio rollup
* G1-8 DOT compliance dashboard
* G2-15 Meeting-minutes capture

**Forward rule:** Every executive/dashboard/notebook surface in ForgedOps must be an **Action Console** — every row has a one-tap action affordance. Read-only surfaces are forbidden by the Override.

### Cluster B · "Closure-action contract must replace closure-as-click" (3 items)
* G2-1 OC-003 QA/QC follow-up
* G2-2 OC-004 Site Inspection follow-up
* Top-10 #5 iter453 BUILD

**Forward rule:** Closure of any 🔴 finding requires an operational action (corrective_action OR re-inspection OR documented exception). "Mark Resolved" / "Acknowledge findings" ack-clicks are forbidden by Amendment 001 REPLACE-4 + REPLACE-5.

### Cluster C · "Multi-step lifecycles must be evidence-per-step, not checklist-per-step" (2 items)
* G2-7 OC-013 Onboarding multi-step
* G2-8 OC-014 Offboarding multi-step

**Forward rule:** Every step that exists in OC-013 / OC-014 must be backed by Tier 1 work-performed data (training record / PPE issuance / attendance / device de-provision event) — not a checkbox click. Amendment 001 REPLACE-6 + REPLACE-7 binding.

### Cluster D · "Workflow build must exclude acknowledgement ride-alongs" (5 items)
* G0-3 Submittal · G0-4 RFI · G0-5 CO · G0-6 Pay-App · G0-9 Sub Management · Top-10 #9 Subcontractor

**Forward rule:** When scoping these PM workflows, the operator must explicitly exclude "Acknowledge Receipt" / "Acknowledged status" / "Sub acknowledges scope" / "Approver acknowledges" patterns. Approval **decisions** are Tier 1 PASS; approval **ack ride-alongs** are Rule 11 FAIL.

### Cross-cluster · "DQ-file + Executive ack rituals must be excluded" (2 items)
* G1-7 DQ-File (V-10 annual DOT-policy ack)
* G1-10 Discipline tracking (HR vs Safety boundary)
* Top-10 #4 / #7 — already grouped above

---

## §8 · CONSTITUTIONAL CONFLICT items

**None.**

The Compliance Sweep + Amendment 001 Validation Sweep have already absorbed every active 🔴 conflict into IGNORE-class or REPLACE-candidate status. The remaining 12 REVIEW REQUIRED items are latent risks **forward-binding** future scoping conversations, not active violations of the current classification.

Note: 4 P0 Constitutional Violations from the Compliance Sweep remain unresolved at the operator-decision layer (CV-1 through CV-4 in `CONSTITUTIONAL_CONFLICT_REGISTER.md`). Those decisions sit outside the scope of this review — they were captured in the prior batch and remain awaiting operator selection among the 8 options in `AMENDMENT001_EXECUTIVE_SUMMARY.md §5`.

---

## §9 · Override audit-axes posture

The Constitutional Override added 5 mandatory audit axes. This review explicitly assesses the classification register against all 5:

| Override audit axis | Posture across 48 classifications |
|---|---|
| User Friction | BUILD items consistently address known frictions (clock-in, "what's mine", closure-action). INTEGRATE items remove the largest friction source (accounting reconciliation). |
| Click Burden | Zero classifications introduce new click rituals · IGNORE list explicitly forbids them |
| Workflow Simplicity | HYBRID class introduced to preserve simplicity (workflow stays in ForgedOps · financial layer stays in accounting) |
| Operational Practicality | EX-1 BLOCKING flag signals practicality gap if accounting integration is deferred |
| Field Adoption Probability | Top 10 selection biases toward high-field-value items (clock-in #2, production #3) · low-field-value items deferred |

All 5 axes PASS.

---

## §10 · 3-criterion success-test posture

The Override requires every classification to satisfy:

| Success criterion | Posture |
|---|---|
| Operationally Complete | BUILD items close the operational mission · INTEGRATE items close external boundaries · HYBRID items honor both |
| Operationally Accountable | Ownership Layer (Top 10 #1) is the explicit completeness primitive · `manager_employee_id` (G1-11) is the routing primitive |
| Operationally Simple | IGNORE list (48 items) removes complexity sources · HYBRID class avoids accounting/ERP rebuild |

All 3 criteria PASS at the classification level. Per-item success-test posture remains operator-authorized at scoping time.

---

## §11 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code written | ✅ |
| Zero solutions designed | ✅ |
| Zero implementation plans | ✅ |
| Zero estimates generated | ✅ |
| Every BUILD/INTEGRATE/HYBRID/IGNORE item reviewed against Constitution Parts I–IV + Override + Amendment 001 | ✅ |
| PASS / REVIEW REQUIRED / CONSTITUTIONAL CONFLICT verdict per item | ✅ |
| 0 outright CONSTITUTIONAL CONFLICT items (prior batches absorbed them) | ✅ |
| 12 REVIEW REQUIRED items clustered into 4 forward-binding doctrines | ✅ |
| 4 unresolved P0 Constitutional Violations from Compliance Sweep cross-cited (not re-scored) | ✅ |

🛑 **STOPPED.**
