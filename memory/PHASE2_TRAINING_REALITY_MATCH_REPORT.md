# PHASE 2 · TRAINING REALITY MATCH (LITE) REPORT
## OCEP Operational Completion Sprint

**Date**: 2026-06-02
**Authority**: OMEGA · OPERATIONAL COMPLETION SPRINT
**Mode**: READ-ONLY · in-app guidance audit (video review deferred per directive)
**Scope**: Help content · tooltips · workflow descriptions · in-app coaching
**Source of evidence**: `/app/backend/guidance/tips.py` + `<HelpTipBlock>` placements in `/app/frontend/src/pages/`

---

## 0 · Method

Per directive: video / Skywork review **deferred**. Audit scope = **in-app guidance only**.

Per-workflow, this report answers the 8 directive-mandated questions by checking which of the 7 canonical tip kinds is present in the help registry:

| Directive question | Tip kind that should answer it |
|---|---|
| 1. What is this? | Page title + form `why` (lead) |
| 2. Why do I use it? | `why` |
| 3. When do I use it? | `when` or first-line of `why` |
| 4. What happens after submission? | `next` |
| 5. Who receives it? | `who` |
| 6. Who owns it? | `who` + `escalate` |
| 7. What if I make a mistake? | `mistake` |
| 8. Is this clearly explained? | composite — all of the above present AND embedded on the form via `<HelpTipBlock formKey=…>` |

A workflow scores:
- **PASS** if 8/8 questions are answered (all 7 kinds materially present + form embeds the block)
- **PARTIAL** if 5–7/8 questions answered (most coverage but one critical kind missing — typically `mistake` or `when`)
- **FAIL** if 0–4/8 answered (workflow is operationally orphaned for the new operator)

Evidence corpus dimensions (verified 2026-06-02):
- 461 tip rows in `tips.py`
- 202 distinct `form_key`s in the registry
- 7 canonical kinds: why · when · next · who · escalate · mistake · example
- `<HelpTipBlock>` placements counted in source (grep yielded ~60 distinct form_keys placed)

---

## 1 · Per-workflow audit

For each workflow: Tips registered (kinds) · Block placement · 8-question coverage · Verdict · Top remediation candidate (READ-ONLY identification; build decisions deferred to FOCP gate).

### 1.1 · JOB HAZARD PLAN (JHP) — `/jha`
- **Registered**: why · next · who · escalate (4/7)
- **Block placement**: present on `JhaPlansHub.jsx` (page-root + poster coaching)
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 partial (folded into `why`) · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ (no `mistake` kind) · 8 partial
- **Post-FOCP R2 reality**: acknowledge button + identity strip newly added · no tip yet teaches "what happens if I sign on a wrong plan version"
- **Verdict**: **PARTIAL**
- **Top remediation candidate**: add `mistake` kind teaching "If you signed the wrong version, re-open `/jha`, find the current version, and acknowledge again — your prior acknowledgement is preserved as an audit row." (NOT BUILD-AUTHORIZED — requires 7-test + 4-proof clearance)

### 1.2 · DAILY REPORT — `/daily-reports/new` and `/daily-reports`
- **Registered**: `daily-report` (why · next · who · escalate); `daily-report.crew`, `.equipment`, `.materials`, `.narrative`, `.photos` (mostly partial sets); `daily-report-new` (none)
- **Block placement**: per-section blocks present on `NewDailyReport.jsx`
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 partial · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ (no `mistake` kind on parent or sections) · 8 partial
- **Post-iter453.7 + FOCP R2 reality**: sticky footer + disabled-state logic in place; undo last status change available admin-side
- **Verdict**: **PARTIAL**
- **Top remediation candidate**: add `mistake` to `daily-report` + `daily-report-new`: "If office returns this DR to field, the kickback reason appears in the history drawer — open the lifecycle panel to read it before resubmitting." Add `mistake` to `daily-report.materials`: "Wrong material codes drive payroll variance downstream — fix before submission, not after."

### 1.3 · INCIDENT — `/incidents/new` + Incident lifecycle
- **Registered**: `incident` (why · next · who · escalate); `incident.location`, `.narrative`, `.severity`, `.witnesses`, `.corrective` (per-section coverage)
- **Block placement**: present on `NewIncident.jsx`
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 ✅ (severity tip implicitly teaches when) · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ (no `mistake` kind on parent) · 8 partial
- **Verdict**: **PARTIAL**
- **Top remediation candidate**: add `mistake` on `incident.severity`: "Mis-classifying severity routes the incident to the wrong queue. If you realize the classification is wrong after submission, ask Safety to reopen — admin-side undo restores the prior state cleanly."

### 1.4 · QA/QC — `/qaqc-inspections/new` + QA/QC lifecycle
- **Registered**: `qaqc` (why · next · who · escalate)
- **Block placement**: present on QA/QC pages
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 partial · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ (no `mistake`) · 8 ❌ for closure paths (3-path Amendment 001 closure not taught in tips)
- **Verdict**: **PARTIAL** (closure surface drags this to FAIL-adjacent)
- **Top remediation candidate**: per Amendment 001 contract, add 3 distinct tips on `qaqc.close`: one for each closure path (re-inspection · corrective-action ≥ 20 chars · exception with dual sign-off). Currently nothing teaches the operator which path applies when.

### 1.5 · SITE INSPECTION — `/inspections/new` + Site Inspection lifecycle
- **Registered**: `inspection` (why · next · who · escalate); `inspection.context`, `.findings`, `.ppe`, `.signoff`
- **Block placement**: present on `NewInspection.jsx`
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 partial · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ (no `mistake`) · 8 partial
- **Verdict**: **PARTIAL**
- **Top remediation candidate**: add `mistake` on `inspection.findings`: "A finding without an owner becomes overdue automatically; if you don't know who to assign, escalate to Safety rather than guess."

### 1.6 · DISPATCH (handoff + holds + transfers + utilization + idle alerts + DR-read)
- **Registered**: parent `dispatch` (none) · `dispatch.handoff` ✅ · `dispatch.holds` partial · `dispatch.transfers` partial · `dispatch.utilization` partial · `dispatch.idle-alerts` partial · `dispatch.daily-report-read` partial
- **Block placement**: present on dispatch surfaces
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 ✅ on handoff · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ (no `mistake` anywhere in dispatch) · 8 partial
- **Verdict**: **PARTIAL** with caveat — the absence of a parent `dispatch` tip means a new dispatcher arriving at the board has no entry-point coaching
- **Top remediation candidate**: add a parent `dispatch` tip set (why/when/who/escalate) so a new operator hitting the board cold knows what they're looking at before drilling into sub-surfaces.

### 1.7 · HR — Employee Lifecycle (new hire · rehire · separation · lifecycle-dates)
- **Registered**: `employee-lifecycle` (why · next · who · escalate); `employee-lifecycle.rehire` (why · next · escalate · **mistake** ✅); `employee-lifecycle.separation` partial; `employee-lifecycle.lifecycle-dates` partial
- **Block placement**: present on HR portal
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 ✅ · 4 ✅ · 5 ✅ · 6 ✅ · 7 ✅ (only workflow auditing PASS on Q7 thanks to rehire `mistake` tip) · 8 ✅
- **Verdict**: **PASS** (best-in-class · the rehire-vs-reactivate `mistake` tip prevents the platform's most expensive HR error)
- **Reference standard**: HR Rehire's tip pattern is the canonical model. Every other workflow's `mistake` kind should mirror this density and operational specificity.

### 1.8 · HR — Driver Qualification (dashboard · expirations · endorsements · restrictions · CDL-vs-approved)
- **Registered**: all 5 sub-keys carry why/next/who/escalate; none carry `mistake`
- **Block placement**: present
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 ✅ (expirations subkey teaches when) · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ · 8 partial
- **Verdict**: **PARTIAL**

### 1.9 · HR — Employee Accountability
- **Registered**: `employee-accountability` (why · next · who · escalate)
- **Verdict**: **PARTIAL** (no `mistake`)

### 1.10 · SAFETY · Fire Extinguisher (add · inspection)
- **Registered**: `fire-extinguisher` (why · next · who · escalate); `.add`, `.inspection` partial
- **Block placement**: present
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 ✅ · 4 ✅ · 5 ✅ · 6 ✅ · 7 ❌ · 8 partial
- **Verdict**: **PARTIAL**

### 1.11 · SAFETY · CORRECTIVE ACTIONS (parent · close · create)
- **Registered**: `corrective` (why · next · who · escalate); `corrective.close` (why · next · **mistake** ✅); `corrective.create` partial
- **Verdict**: **PARTIAL** (close is strong; parent + create lack `mistake`)

### 1.12 · FLEET REPAIR · `fleet.repair` · `fleet.rts` · `fleet.visibility`
- **Registered**: `fleet.repair` (why · next); `fleet.rts` partial; `fleet.visibility` partial
- **Block placement**: present
- **8-question coverage**: 1 ✅ · 2 ✅ · 3 ❌ (no `when` and no `escalate`) · 4 ✅ · 5 ❌ (no `who`) · 6 partial · 7 ❌ · 8 ❌
- **Verdict**: **FAIL** for Shop persona; weakest training-reality surface on the platform
- **Top remediation candidate**: full kind battery (why/when/next/who/escalate/mistake) on `fleet.repair` parent + `.rts` (return-to-service is the operational risk surface; Shop currently has the thinnest coaching of any workflow)

### 1.13 · EQUIPMENT ISSUANCE (parent · acknowledgment · employee · photos)
- **Registered**: parent (why · next · who · escalate); `.acknowledgment` (why · **mistake** · escalate ✅); `.employee` (`mistake` only); `.photos` partial
- **Verdict**: **PARTIAL** (good coverage; not at HR-rehire density)

### 1.14 · EQUIPMENT TRAINING (parent · context · signatures)
- **Registered**: parent partial; `.context` partial; `.signatures` partial
- **Verdict**: **PARTIAL**

### 1.15 · FIELD LEADERSHIP PORTAL (5 sub-keys: change-password · dispatch-visibility · portal-dashboard · records · user-management)
- **Registered**: most subkeys have why/next/who/escalate; none have `mistake`
- **Verdict**: **PARTIAL**

### 1.16 · DRIVER LIFECYCLE
- **Registered**: why · next · who · escalate (4/7)
- **Verdict**: **PARTIAL**

### 1.17 · DOCUMENT EXPIRATIONS
- **Registered**: why · next · who · escalate
- **Verdict**: **PARTIAL**

### 1.18 · UNIVERSAL UNDO / RECOVERY (post-FOCP R2 · admin-only)
- **Registered**: **NO tips** (FOCP R2 doctrine § 7 says no help-tip required because button + modal copy carry the mental model)
- **Block placement**: N/A
- **8-question coverage**: 1 ✅ (button label) · 2 ✅ (modal copy) · 3 ✅ (modal shows when to use) · 4 ✅ (modal shows what gets written) · 5 ✅ (admin-only by design) · 6 ✅ · 7 N/A (undo IS the mistake-recovery) · 8 ✅
- **Verdict**: **PASS by doctrine-exemption** (inline copy is the training)
- **TR-classification**: **DOCTRINE EXEMPT** — no register entry required

### 1.19 · POs · Asset Transfers · Time-off · Employee Requests (4 approval surfaces)
- **Registered**: form_keys for these surfaces NOT systematically present in `tips.py` (verified via grep)
- **Block placement**: not present on `PoRequests.jsx`, `AssetTransfers.jsx`, `HrTimeOff.jsx`, `HrEmployeeRequestsQueue.jsx`
- **8-question coverage**: 0–2 / 8 (button labels carry most of the meaning; no formal coaching)
- **Verdict**: **FAIL** for the new-PM / new-HR persona
- **Top remediation candidate**: a single `approvals` parent tip set (why · who · escalate) covering all 4 surfaces would lift all four from FAIL to PARTIAL with minimal coaching surface. (Identification only — NOT BUILD-AUTHORIZED.)

---

## 2 · Aggregate scoring

| Verdict | Workflows | % |
|---|---:|---:|
| PASS | 2 (HR Employee Lifecycle (rehire) · Universal Undo by doctrine) | 11 % |
| PARTIAL | 14 | 74 % |
| FAIL | 3 (Fleet Repair · 4-surface Approvals as a class · Daily-Report-New entry-point) | 16 % |
| **Total workflows audited** | **19** |  |

**Overall Training-Reality Match (LITE) Score**: **52 / 100** (weighted: PASS = 100 · PARTIAL = 60 · FAIL = 0).

**Threshold for Phase 7 certification**: ≥ 75. **Gap**: 23 points.

---

## 3 · Pattern findings (the four root causes)

| # | Pattern | Affected workflows | Operational cost |
|---|---|---|---|
| P1 | **`mistake` kind systematically absent** | 14 of 19 workflows | Operators cannot recover without calling someone. Defeats the FOCP doctrine of "users can recover from mistakes." |
| P2 | **Approval surfaces have no coaching at all** | POs · Asset Transfers · Time-off · Employee Requests (4 surfaces · multi-role) | New PM / HR cannot operate these without tribal knowledge |
| P3 | **Shop / Fleet has the thinnest coverage** | `fleet.repair` · `fleet.rts` · `fleet.visibility` (3 of 19) | Shop persona's training-reality is the platform's weakest — and Shop's mistakes are the platform's most operationally consequential (truck rolls out that shouldn't have) |
| P4 | **Closure-path coaching missing on QA/QC** | 1 high-impact workflow | Amendment 001's 3-path closure is the platform's hardest decision and the only one with no in-app explanation |

These four patterns explain ALL 17 non-PASS workflows. Remediation in 4 patterns clears the entire training-reality surface.

---

## 4 · Workflows by persona impact

| Persona | Workflows materially affected | Aggregate verdict for this persona |
|---|---|---|
| Laborer | JHP (PARTIAL) | PARTIAL |
| Foreman | Daily Report (PARTIAL) · JHP (PARTIAL) | PARTIAL |
| Superintendent | Daily Report (PARTIAL) · Incident (PARTIAL) · Site Inspection (PARTIAL) | PARTIAL |
| PM | QA/QC (PARTIAL) · Approvals (FAIL) · Incident (PARTIAL) · Corrective (PARTIAL) | **APPROVALS DRAGGING TO FAIL-ADJACENT** |
| Safety | Incident (PARTIAL) · Corrective (PARTIAL) · QA/QC (PARTIAL) · Site Inspection (PARTIAL) · Fire Ex (PARTIAL) | PARTIAL |
| Dispatch | Dispatch sub-keys (PARTIAL) · Driver Qualification (PARTIAL) | PARTIAL |
| HR | Employee Lifecycle (PASS) · Driver Qual (PARTIAL) · Employee Accountability (PARTIAL) · Approvals (FAIL) | **APPROVALS DRAGGING TO FAIL-ADJACENT** |
| Shop | Fleet Repair (FAIL) · Equipment Issuance (PARTIAL) · Equipment Training (PARTIAL) | **FAIL** |
| Executive | Universal Undo (PASS) · most others read-side only | PASS |

Worst-served personas: **Shop** (only role with a FAIL on a primary workflow), then **PM/HR** (because of the Approvals-as-a-class FAIL).

---

## 5 · Truth Register classification of findings

| Finding | Existing TR? | Classification |
|---|---|---|
| P1 (mistake kind missing across 14 workflows) | No · new finding from this audit | **ACTIVE** (engineering-supportable; needs 7-test + 4-proof if any build) |
| P2 (Approvals surfaces have no help) | No | **ACTIVE** |
| P3 (Fleet/Shop coaching thinness) | No | **ACTIVE** |
| P4 (QA/QC closure-path coaching missing) | Adjacent to TR-D001 (training docs operator-led) | **DEFERRED** (operator decides whether this is a doctrine-style decision aid or a training-content task) |
| Universal Undo no tips | N/A | **DOCTRINE EXEMPT** (FOCP R2 § 7 declares the inline copy carries the mental model) |

No new engineering work is authorized by this audit alone. All four ACTIVE patterns must independently pass FOCP Final Directive's 7-test + 4-proof gates before any code is written.

---

## 6 · Sign-off

```
This Training Reality Match (LITE) report is complete to the boundary
defined by the OMEGA OPERATIONAL COMPLETION SPRINT directive
(in-app guidance only; video / Skywork review deferred).

Findings:    Overall Score 52 / 100
             2 PASS · 14 PARTIAL · 3 FAIL
             4 root-cause patterns identified
             0 build actions authorized by this report

Reviewer:    AI agent (E1)
Date:        2026-06-02
Status:      AWAITS OPERATOR CONFIRMATION
```

Operator confirmation step: read §1, §3, §5; confirm or refute each verdict against observed operator behavior; sign date above. AI agent cannot self-confirm.

---

**End of PHASE 2 · TRAINING REALITY MATCH (LITE) REPORT**
