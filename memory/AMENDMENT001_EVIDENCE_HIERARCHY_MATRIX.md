# OMEGA · AMENDMENT 001 EVIDENCE HIERARCHY MATRIX

**Date:** 2026-06-02
**Mode:** READ-ONLY · zero code · zero redesign
**Governing doctrine:** `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md` Part IV Amendment 001
**Companion to:** `AMENDMENT001_VALIDATION_AUDIT.md`

---

## §0 · Hierarchy reference (verbatim from Amendment 001)

| Tier | Strength | Examples |
|---:|---|---|
| **Tier 1 — Work Performed** | **Strongest** | DR submitted · QA/QC correction completed · Site Inspection deficiency corrected · Payroll variance resolved · Incident investigation completed · Equipment inspection submitted · Safety meeting conducted · Training completed · Production entered · Revision submitted |
| **Tier 2 — Participation Evidence** | Acceptable | Safety Meeting attendance · Toolbox Talk attendance · Sign-in roster · Training attendance · QR attendance scan · Device attendance capture |
| **Tier 3 — Access Evidence** | Conditional | JHP opened · PDF downloaded · Revision viewed · Correction notice opened · Notification consumed |
| **Tier 4 — Acknowledgement Evidence** | **Weakest** | I Agree · I Understand · I Have Read This · I Acknowledge · Confirm |

> "Acknowledgement alone is not proof of understanding. Acknowledgement alone is not proof of compliance. Acknowledgement alone is not proof of work. ForgedOps should treat acknowledgement as a last resort."

---

## §1 · Matrix · each acknowledgement × evidence already captured today

For each acknowledgement concept from `AMENDMENT001_VALIDATION_AUDIT.md`, identify which Tiers of evidence are **already captured** (or **capturable without new infrastructure**) using existing platform primitives. The Matrix answers: *"How much stronger evidence already exists in the platform?"*

Legend per cell: ✅ already captured · ✅* capturable with existing primitives (no new infra) · 🔴 not captured · n/a not applicable

### 1.1 · Proposed acknowledgement workflows

| # | Acknowledgement | Tier 1 (Work) | Tier 2 (Participation) | Tier 3 (Access) | Tier 4 (Ack) | Net evidence position today |
|---:|---|:---:|:---:|:---:|:---:|---|
| 1 | OC-005 JHP Ack Ledger | ✅* Toolbox Talk submission for same date + project_number captures crew briefing on the JHP | ✅* meeting attendance roster | ✅* `GET /api/job-hazard-files/{file_id}/download` + FSI Tier-1 identity capture (per JHP gap report §4 capability 1) | 🔴 (proposed only) | **Tiers 1+2+3 all available today via existing primitives.** Tier 4 ack would be additive but not necessary. |
| 2 | F-18 Acknowledge JHP | Same as #1 | Same as #1 | Same as #1 | 🔴 | Same as #1 |
| 3 | Site Inspection acknowledge findings | ✅* corrective-action record per finding | n/a | n/a | 🔴 | **Tier 1 available** via existing `corrective_actions` collection or new per-finding state tracking |
| 4 | QA/QC Mark Resolved | ✅* corrective-action record OR re-inspection submission | n/a | n/a | 🔴 | **Tier 1 available** via existing `corrective_actions` + new `qaqc_inspections` re-inspection record |
| 5 | OC-014 exit-interview checkbox | ✅* interview notes captured as data | n/a | n/a | 🔴 | **Tier 1 capturable** if step is rescoped to require notes/data |
| 6 | OC-013 orientation checkbox | ✅* post-orientation training completion record | ✅* orientation attendance roster | n/a | 🔴 | **Tiers 1+2 capturable** via existing primitives |
| 7 | BilingualConsent+SignaturePad on JHP | Same as #1 | Same as #1 | Same as #1 | 🔴 | Same as #1 |

### 1.2 · Existing live acknowledgement-style fields

| # | Acknowledgement | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Net evidence position today |
|---:|---|:---:|:---:|:---:|:---:|---|
| 8 | iter445 DR "Has crew reviewed JHP?" Yes/No | ✅* Toolbox Talk submission for same day + project | ✅* attendance roster | ✅* JHP download identity capture (if FSI Tier-1 enabled at download endpoint) | ✅ field exists but consumer absent | **Tiers 1+2+3 available; Tier 4 field has no downstream consumer.** |
| 9 | Vestigial `stop_work_acknowledged` | ✅* Toolbox Talk content (if stop-work covered) | ✅* attendance | n/a | ✅ field exists on vestigial form | **Field has no operational consumer; system itself is vestigial.** |
| 10 | BilingualConsent on Daily Report | ✅ DR submission IS Tier 1 | n/a | n/a | ✅ consent text version stamped | **Tier 1 dominates; consent is Tier-4 ride-along · legally necessary** |
| 11 | BilingualConsent on Incident submission | ✅ incident submission IS Tier 1 | n/a | n/a | ✅ consent version stamped | Same as #10 |
| 12 | DR closure attestation modal | ✅ state transition + notes are Tier 1 | n/a | n/a | ✅ modal confirms intent | **Tier 1 dominates; modal captures decision content** |
| 13 | Incident closure + OSHA ack | ✅ closure transition + OSHA recordable data are Tier 1 | n/a | n/a | ✅ OSHA ack legally required | **Tier 1 dominates; OSHA ack is the legally required Tier-4 artifact** |
| 14 | Reopen-with-reason modal | ✅ reason text IS Tier 1 operational decision content | n/a | n/a | n/a (not an ack — text capture) | **Pure Tier 1 — not an acknowledgement** |
| 15 | `consent_text_version` stamping | ✅ rides on Tier 1 work submission | n/a | n/a | ✅ version retention | **Tier 1 + Tier 4 ride-along · legally necessary** |

### 1.3 · Adjacent evidence-capture patterns (already compliant)

| # | Pattern | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Net evidence position |
|---:|---|:---:|:---:|:---:|:---:|---|
| 16 | `safety_training_records` credentialing | ✅ training completion IS Tier 1 | ✅ attendance recorded | n/a | n/a | **Pure Tiers 1+2 — credential record, not acknowledgement** |
| 17 | `training_hits` HelpTip telemetry | n/a | n/a | ✅ view captures Tier 3 access | n/a | **Pure Tier 3 telemetry for UX analytics** |
| 18 | Approval decisions (Time Off, PO, PV) | ✅ approve/reject IS Tier 1 operational judgment | n/a | n/a | n/a | **Pure Tier 1 — Rule 6 explicit exception** |

---

## §2 · Cross-cutting findings

### 2.1 · The JHP ack pattern is the dominant Constitutional liability

Items 1, 2, 7 (proposed) and items 8, 9 (live) all attack the same operational problem: "prove crew was briefed on the JHP." All five can be solved with combinations of existing Tier 1 + Tier 2 + Tier 3 evidence already captured (or trivially capturable) elsewhere in the platform. **Zero new acknowledgement infrastructure is required to satisfy the operational problem.** Operator-decision required on whether OSHA/insurance language demands a Tier 4 artifact in addition; if not, all five items can be eliminated.

### 2.2 · Closure-as-click pattern (items 3, 4) is replaceable by existing primitives

The `corrective_actions` collection already exists. Closure of QA/QC and Site Inspection workflows can require a corrective-action record (Tier 1) instead of a status-pill click (Tier 4). This is a Constitutional re-scope, not a new feature.

### 2.3 · Multi-step checklist pattern (items 5, 6) is replaceable per-step

Each step in OC-013/OC-014 can be re-scoped to either capture operational data (Tier 1) or rely on an attendance/roster artifact (Tier 2). Constitutional re-scope at design time eliminates the checkbox pattern.

### 2.4 · Self-attestation Yes/No fields (items 8, 9) are pure FAIL

These fields exist today with no operational consumer. They are the textbook "evidence of clicking" pattern Amendment 001 forbids. Removal would be a code change requiring operator authorization (not requested in this audit).

### 2.5 · 6 patterns are already Constitutionally aligned (items 12, 13, 14, 16, 17, 18)

The platform's closure attestation, reopen-reason, credentialing, telemetry, and approval-decision patterns all use Tier 1 work + (where applicable) legally necessary Tier 4 ride-along. These should NOT be modified.

### 2.6 · 3 consent ride-alongs (items 10, 11, 15) are operator-decision

The public-gate Daily Report and Incident submissions include BilingualConsent + `consent_text_version` stamping. The Tier 1 submission itself is the work-performed evidence. The consent is a Tier 4 ride-along that is **legally appropriate** for non-authenticated submitters. For FSI Tier-1 authenticated submitters (FL-token holders), the consent could arguably be dropped — operator-decision territory.

---

## §3 · Aggregate evidence sufficiency

| Acknowledgement family | Tier 1 evidence already available? | Tier 2? | Tier 3? | Net classification |
|---|:---:|:---:|:---:|---|
| JHP ack family (items 1, 2, 7, 8, 9) | ✅ Toolbox Talk submission | ✅ attendance | ✅ JHP download + FSI identity | **Replaceable without new ack infrastructure** |
| Closure-as-click (items 3, 4) | ✅ corrective_actions OR re-inspection | n/a | n/a | **Replaceable via existing collection** |
| Multi-step checklists (items 5, 6) | ✅ if step captures data | ✅ if attendance roster | n/a | **Replaceable per-step Constitutional re-scope** |
| Self-attestation (items 8, 9 LIVE) | ✅ Tier 1 alternative exists | ✅ alternative exists | ✅ alternative exists | **Eliminable; no operational dependency** |
| Closure attestation rides Tier 1 (items 12, 13, 14) | ✅ state transition IS Tier 1 | n/a | n/a | **Already compliant** |
| Consent ride-alongs (items 10, 11, 15) | ✅ submission IS Tier 1 | n/a | n/a | **Already compliant · operator-decision optional** |
| Credential/telemetry/approval (items 16, 17, 18) | ✅ Tier 1/2/3 by design | ✅ where applicable | ✅ where applicable | **Already compliant** |

---

## §4 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero reports modified | ✅ |
| Zero scores recomputed | ✅ |
| Every concept mapped to all 4 Tiers | ✅ |
| Evidence sufficiency rendered per cluster | ✅ |
| Cross-cutting findings preserve operator decision authority | ✅ |

🛑 **STOPPED.** Hierarchy matrix complete. Documentation only.
