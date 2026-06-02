# OMEGA · AMENDMENT 001 REPLACEMENT CANDIDATES

**Date:** 2026-06-02
**Mode:** READ-ONLY · zero code · zero redesign · zero implementation planning
**Governing doctrine:** `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md` Part IV Amendment 001
**Companions:** `AMENDMENT001_VALIDATION_AUDIT.md` · `AMENDMENT001_EVIDENCE_HIERARCHY_MATRIX.md`

---

## §0 · Replacement principle (verbatim from Amendment 001)

> "ForgedOps shall never require acknowledgements when objective operational evidence already exists."
>
> "The system should capture evidence naturally from work being performed."

**This document identifies what stronger evidence is already captured today for each REPLACE-classified item.** It does NOT design a replacement workflow. It does NOT propose code. It does NOT recommend which option to authorize. Operator-decision authority is preserved.

---

## §1 · Replacement candidates · 7 items classified REPLACE

### REPLACE-1 · OC-005 JHP Acknowledgement Ledger

* **Current acknowledgement:** Per-crew per-day per-JHP "I have read this" checkbox + signature pad (proposed in `JHP_ACKNOWLEDGEMENT_GAP_REPORT.md` §4 capability 6)
* **Operational purpose claimed:** Prove crew was briefed on JHP for OSHA/insurance/contract record
* **Existing evidence available without new ack infrastructure:**
   * **Tier 1 (Work Performed):** Toolbox Talk submission for same day + project_number captures crew briefing on the JHP. Live primitive: `routes/safety.py` toolbox talk endpoint · 1 row in `tasks` tagged `safety.meeting`. The crew **performing** the Toolbox Talk IS the evidence of briefing.
   * **Tier 2 (Participation):** Toolbox Talk attendance roster (if captured per meeting) provides crew-level participation evidence.
   * **Tier 3 (Access):** `GET /api/job-hazard-files/{file_id}/download` can be wrapped with FSI Tier-1 identity capture (per `JHP_ACKNOWLEDGEMENT_GAP_REPORT.md` §4 capability 1) — passive, no UI affordance, no click.
* **Operator-decision options (NOT recommendations):**
   * (a) Eliminate OC-005 entirely; rely on existing Tier 1 Toolbox Talk + Tier 3 JHP download evidence
   * (b) Re-scope OC-005 to capability 1 ONLY (identity at download endpoint) — passive Tier 3 capture, no ack UI
   * (c) If OSHA/insurance counsel mandates Tier 4 ack specifically, build OC-005 as scoped — operator must answer the Constitutional Test affirmatively before authorization
   * (d) Tie JHP review to existing Toolbox Talk submission as a required link (Tier 1 + cross-workflow binding)

### REPLACE-2 · F-18 row 18 Acknowledge JHP

* **Current acknowledgement:** Same as REPLACE-1 (would be the affordance built to close 🔴 cells)
* **Operational purpose claimed:** Same as REPLACE-1
* **Existing evidence:** Same as REPLACE-1
* **Operator-decision options:** Same as REPLACE-1. Closing the 🔴 cells in `PHASE_1A_OPERATIONAL_CERTIFICATION_AUDIT.md` §1 row 18 does NOT require building the ack — option (a) or (b) above would mark row 18 as "Constitutionally exempt" rather than "completion gap."

### REPLACE-3 · Site Inspection "Acknowledge findings" (OC-004 future scope)

* **Current acknowledgement:** Status-pill click "Acknowledge findings"
* **Operational purpose claimed:** Document that PM/Safety read the findings before closing the inspection
* **Existing evidence available:**
   * **Tier 1 (Work Performed):** Corrective-action record per finding (existing `corrective_actions` collection · 9 rows today · schema `assigned_to_name` · `due_date` · `closed_by_name`)
   * **Tier 1 (Work Performed alternative):** Re-inspection submission (new state event on the inspection record)
* **Operator-decision options:**
   * (a) Closure requires at least one corrective-action record per finding
   * (b) Closure requires a "dismissed-with-rationale" disposition per finding (text field captures rationale = Tier 1 operational data)
   * (c) Closure allowed only after re-inspection submission

### REPLACE-4 · QA/QC "Mark Resolved" status-pill (OC-003 future scope)

* **Current acknowledgement:** Status-pill click per deficiency
* **Operational purpose claimed:** Document deficiency is no longer open
* **Existing evidence available:**
   * **Tier 1 (Work Performed):** Corrective-action record (existing `corrective_actions` collection)
   * **Tier 1 (Work Performed alternative):** Re-inspection submission triggered by deficiency
* **Operator-decision options:**
   * (a) "Resolved" requires linked corrective-action record
   * (b) "Resolved" requires re-inspection submission
   * (c) "Resolved" requires either (a) or (b) operator's choice

### REPLACE-5 · OC-014 Offboarding "exit interview" checkbox step

* **Current acknowledgement:** "I conducted the exit interview" checkbox
* **Operational purpose claimed:** Document HR performed exit interview
* **Existing evidence available:**
   * **Tier 1 (Work Performed):** Interview notes captured as free-text data (would require a notes field, not a checkbox)
   * **Tier 2 (Participation):** Interview attendance recorded (employee + HR present)
* **Operator-decision options:**
   * (a) Re-scope step to require interview notes (Tier 1 data capture)
   * (b) Eliminate step if no downstream consumer reads the interview record
   * (c) Replace with Tier 2 attendance/timestamp pair

### REPLACE-6 · OC-013 Onboarding "orientation completed" checkbox step

* **Current acknowledgement:** "Orientation completed" checkbox
* **Operational purpose claimed:** Document new employee received orientation
* **Existing evidence available:**
   * **Tier 1 (Work Performed):** Post-orientation training completion record in `safety_training_records` (existing collection)
   * **Tier 2 (Participation):** Orientation attendance roster (live primitive — `safety_training_records` already tracks `completed_at` + `instructor`)
* **Operator-decision options:**
   * (a) Eliminate checkbox; consume `safety_training_records` row as completion evidence
   * (b) Replace with attendance roster requirement

### REPLACE-7 · BilingualConsent + SignaturePad on JHP (proposed in JHP gap report Pattern D)

* **Current acknowledgement:** Same workflow as REPLACE-1; specifically the proposed reuse of `BilingualConsent.jsx` + `SignaturePad.jsx` for the JHP ack UI
* **Operational purpose claimed:** Same as REPLACE-1
* **Existing evidence:** Same as REPLACE-1
* **Operator-decision options:** Same as REPLACE-1 — pattern reuse does not justify pattern existence

---

## §2 · Items where NO existing evidence substitute is identifiable

For two items, the audit identifies the acknowledgement as a FAIL with no existing evidence substitute — meaning the field has no operational consumer and elimination (not replacement) is the Constitutional answer.

### FAIL-1 · iter445 `NewDailyReport.jsx` "Has crew reviewed the JHP today?" Yes/No (LIVE)

* **Why no substitute identifiable:** The field exists today on the DR form, but the audit of all consumers of `daily_reports` shows no downstream workflow reads the value. The field is pure self-attestation telemetry without an operational consumer. There is no replacement workflow to identify because there is no workflow consuming it.
* **Constitutional answer:** Eliminate the field. (Requires separate operator-authorized code change · not authorized by this audit.)
* **Alternative evidence available:** If JHP-briefing evidence is operationally required, the JHP family Tier 1 + Tier 2 + Tier 3 stack from REPLACE-1 satisfies the need without the self-attestation field.

### FAIL-2 · Vestigial `stop_work_acknowledged` boolean on `db.jhas` (LIVE · 1 row · likely test data)

* **Why no substitute identifiable:** The workflow itself is vestigial (operator confirmed MASCI does not use JHA forms). There is no operational consumer of the field because there is no operational consumer of the workflow.
* **Constitutional answer:** Decommission the vestigial JHA system. (Requires separate operator-authorized batch.)
* **Alternative evidence available:** N/A — workflow is dormant; field would not be retained even in a re-scope.

---

## §3 · Cross-cutting replacement summary

| Replacement source | How many REPLACE items it covers | Pre-existing infrastructure used |
|---|---:|---|
| **Toolbox Talk submission** (Tier 1 work) | 2 (REPLACE-1, REPLACE-2) | `tasks` `source_module="safety.meeting"` · existing route |
| **Toolbox Talk attendance roster** (Tier 2) | 2 (REPLACE-1, REPLACE-2) | Capturable at meeting submit; not yet implemented but no new collection needed if added |
| **JHP download identity capture** (Tier 3) | 3 (REPLACE-1, REPLACE-2, REPLACE-7) | Existing `GET /api/job-hazard-files/{file_id}/download` endpoint + FSI Tier-1 wrapper |
| **`corrective_actions` collection** (Tier 1) | 2 (REPLACE-3, REPLACE-4) | Live collection · 9 rows · schema already supports per-source linkage |
| **Re-inspection submission** (Tier 1) | 2 (REPLACE-3, REPLACE-4) | New state event on existing collections; no new collection needed |
| **Interview notes data capture** (Tier 1) | 1 (REPLACE-5) | Free-text field on existing offboarding record · no new collection |
| **`safety_training_records`** (Tier 1 + Tier 2) | 1 (REPLACE-6) | Live collection · 6 rows · schema already supports completion + attendance |

**No new collections required to satisfy any REPLACE classification.** All seven items can be addressed using existing platform primitives.

---

## §4 · What this audit does NOT do

| Constraint | Status |
|---|---|
| Does not design the replacement workflow | ✅ |
| Does not recommend which operator-decision option to authorize | ✅ |
| Does not estimate code effort | ✅ |
| Does not propose schema changes | ✅ |
| Does not recompute existing audit scores | ✅ |
| Does not modify existing audits | ✅ |
| Does not authorize any build | ✅ |

The audit identifies that **stronger evidence already exists today** for each REPLACE item and surfaces **operator-decision options** at high level. Selection of an option for any item requires explicit operator authorization in a separate batch.

---

## §5 · Discipline scorecard

| Check | Status |
|---|---|
| Zero code changed | ✅ |
| Zero solutions designed | ✅ |
| Zero implementation plans produced | ✅ |
| Every REPLACE item identifies existing evidence sources | ✅ |
| Every REPLACE item preserves operator-decision authority | ✅ |
| FAIL items (no substitute) explicitly distinguished from REPLACE items | ✅ |
| 7 REPLACE + 2 FAIL items catalogued | ✅ |

🛑 **STOPPED.** Replacement candidates identified. Documentation only.
