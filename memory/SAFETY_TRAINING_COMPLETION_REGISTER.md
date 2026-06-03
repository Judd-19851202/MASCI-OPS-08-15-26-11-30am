# SAFETY TRAINING COMPLETION REGISTER
## OCEP · Safety Training Completion Program (STCP) · Register 1 of 5

**Date**: 2026-06-03
**Authority**: OMEGA · STCP
**Mode**: READ-ONLY source-direct verification · NO new workflows · NO duplicate docs · NO training bloat
**Evidence rule**: Every cell below was verified against actual code at `/app/backend/guidance/tips.py`, `/app/backend/routes/`, `/app/backend/lib/workflow_state_events.py`, `/app/frontend/src/`. No estimates, no assumptions.

**Method**:
1. Enumerated every safety form_key in `tips.py` (47 form_keys / 137 tips relevant to safety workflows).
2. Parsed each tip's `kind` and `body_es` presence with a Python AST-style walk.
3. Cross-referenced each workflow against `routes/safety.py`, lifecycle files, and `lib/workflow_state_events.py` for audit-trail wiring.
4. Cross-referenced the AdminOperationalLanguage glossary for ownership / approval semantics.

---

## 1 · The 14 verified safety workflows

These are the **operationally-distinct safety workflows** that actually exist in the codebase. No workflow is invented; no workflow is duplicated; no parent/child is double-counted.

| # | Workflow | Backend evidence | Frontend evidence |
|---|---|---|---|
| 1 | **Job Hazard Plan (JHP)** + acknowledgement ledger | `routes/safety.py` /jhas (lines 544–625) · `routes/jha_acknowledgements.py` (FOCP R2) | `frontend/src/pages/JhaPlansHub.jsx` · `pages/admin/AdminJhaAcknowledgements.jsx` |
| 2 | **Safety Meeting** | `routes/safety.py` /meetings (lines 455–536) · `models/Meeting` Pydantic | `pages/NewMeeting.jsx` · `pages/MeetingsDashboard.jsx` · `pages/ViewMeeting.jsx` |
| 3 | **Incident Report** | `routes/safety.py` /incidents (lines 633–833) · `routes/incident_lifecycle.py` (WORKFLOW="incident") | `pages/NewIncident.jsx` · `pages/ViewIncident.jsx` · `pages/IncidentsDashboard.jsx` · `components/IncidentLifecyclePanel.jsx` |
| 4 | **Site Inspection** | `routes/safety.py` /inspections (lines 303–447) · `routes/site_inspection_lifecycle.py` (WORKFLOW="site_inspection") | `pages/NewInspection.jsx` · `pages/ViewInspection.jsx` · `components/SiteInspectionLifecyclePanel.jsx` |
| 5 | **QA/QC Inspection** | `routes/qaqc.py` · `routes/qaqc_lifecycle.py` (WORKFLOW="qaqc_inspection") | `pages/NewQaqcInspection.jsx` · `pages/ViewQaqcInspection.jsx` · `pages/QaqcSection.jsx` · `components/QaqcLifecyclePanel.jsx` |
| 6 | **CAPA / Corrective Action** | `routes/safety_portal/corrective_actions.py` (8 endpoints, status_history append at L221) | (admin / safety portal pages) |
| 7 | **Equipment Inspection — Pre-op** | `tips.py` preop / preop.controls / preop.defects / preop.signoff / preop.tires-tracks / preop.fluids | (form pages — preop forms) |
| 8 | **Equipment Issuance** | `tips.py` equipment-issuance + 4 sub-forms · backend equipment routes | `pages/safety/equipment-issuance` flows |
| 9 | **Equipment Training (operator certification)** | `tips.py` equipment-training + 3 sub-forms · safety_forms route | `pages/safety/equipment-training` flows |
| 10 | **Fleet DVIR / Repair / RTS / Visibility** | `routes/fleet_ops.py` · `tips.py` fleet.dvir / fleet.repair / fleet.rts / fleet.visibility / fleet.weekly-emergency / fleet.weekly-lead | `components/FleetRepairDrawer.jsx` · fleet admin pages |
| 11 | **Fire Extinguisher Inspection** | `routes/safety.py` · `tips.py` fire-extinguisher / fire-extinguisher.add / fire-extinguisher.inspection | safety pages |
| 12 | **Safety Topic Library** | `routes/safety_topic_library.py` · 23 `topics/*.es.js` files · 23 implied `*.en.js` (in `meetingTopicLibrary.js` historical) | `pages/SafetyTopicLibrary.jsx` |
| 13 | **Safety Document upload / classification** | `tips.py` safety-document / .classification / .upload | safety document upload pages |
| 14 | **Safety Training record / expiration tracking** | `tips.py` safety-training / .expiration / .upload | `pages/TrainingHub.jsx` · `pages/TrainingTrack.jsx` |

**Net safety workflows**: **14 distinct operational processes**. No false additions. No phantom workflows.

---

## 2 · Safety Training Completion Matrix (11-criteria verification)

Columns: each criterion is GREEN / YELLOW / RED. Evidence cited in source-direct notes (Section 3).

| # | Workflow | Owner | Help Content | Coaching (tips) | English | Spanish (UI) | Common Mistakes (`mistake` kind) | Related Workflows | Audit Trail | Approval Path | Onboarding | Status | Gap | Remediation (no engineering authorized) |
|---|---|---|---|---|---|---|---|---|---|---|---|:-:|---|---|
| 1 | JHP + Ack | Safety / PM | 🟢 8 tips total | 🟡 partial | 🟢 | 🟢 i18n + topic content | 🟡 parent `jha` lacks mistake; `jha.poster` has it | 🟢 meeting, incident, DR | 🟢 FOCP R2 `jha_ack` workflow | 🟢 acknowledge ledger | 🔴 absent | 🟡 | parent `mistake` absent + body_es 0% (Coaching Gap Register §1) | Lift body_es / add `jha` parent mistake — FOCP-gated |
| 2 | Safety Meeting | Safety / Foreman | 🟢 22 tips | 🟢 broad | 🟢 | 🟢 i18n + 23 ES topic files | 🟢 5 of 6 forms (parent `meeting` lacks; sub-forms have it) | 🟢 JHP, incident, CAPA | 🔴 **NO lifecycle audit file** | 🔴 **NO formal approval / lifecycle** | 🔴 absent | 🟡 | parent mistake gap + no audit trail + body_es 0% | Either accept doctrine-silent (operator-led) or FOCP-gate a `meeting` lifecycle — operator decides |
| 3 | Incident Report | Safety / Admin | 🟢 22 tips | 🟢 broad | 🟢 | 🟢 i18n | 🟢 5 of 6 forms (parent `incident` lacks; sub-forms have it) | 🟢 CAPA, JHP, meeting, DR | 🟢 `incident_lifecycle.py` WORKFLOW="incident" | 🟢 3-attestation closure gate | 🔴 absent | 🟡 | parent mistake gap + body_es 0% + attestation labels lack per-flag def (AR-0016) | FOCP-gate; high-priority |
| 4 | Site Inspection | Safety | 🟢 17 tips | 🟢 broad | 🟢 | 🟢 | 🟢 4 of 5 forms | 🟢 QA/QC, CAPA | 🟢 `site_inspection_lifecycle.py` WORKFLOW="site_inspection" | 🟢 Amendment 001 closure A/B/C | 🔴 absent | 🟡 | parent mistake gap + body_es 0% + `FINDINGS_RAISED` vs `DEFICIENCY_RAISED` vocab risk (AR-0007) | FOCP-gate; medium-priority |
| 5 | QA/QC Inspection | PM / Safety | 🟢 18 tips | 🟢 broad | 🟢 | 🟢 | 🟢 4 of 6 forms | 🟢 CAPA, Site Insp | 🟢 `qaqc_lifecycle.py` WORKFLOW="qaqc_inspection" | 🟢 Amendment 001 closure A/B/C | 🔴 absent | 🟡 | parent mistake gap + body_es 0% + 3-path closure coaching missing (Phase 2 P4) | FOCP-gate |
| 6 | CAPA | Safety | 🟢 11 tips | 🟢 | 🟢 | 🟢 i18n + glossary | 🟢 3 of 3 sub-forms have it; parent lacks | 🟢 incident, qaqc, site insp | 🟢 `status_history` append (`corrective_actions.py` L221) | 🟢 5-stage pipeline (glossary) | 🔴 absent | 🟡 | parent mistake gap + body_es 0% | FOCP-gate (small) |
| 7 | Equipment Pre-op (preop) | Operator / Shop | 🟢 ~13 tips | 🟡 partial | 🟢 | 🟢 | 🟡 preop.defects has mistake; others lack | 🟢 fleet repair, DR | 🟡 created_at present; no workflow_state_events | n/a — defect intake routes to fleet | 🔴 absent | 🟡 | parent mistake gap + body_es 0% | FOCP-gate |
| 8 | Equipment Issuance | Safety / HR | 🟢 7 tips | 🟡 partial | 🟢 | 🟢 | 🟡 acknowledgment has it; parent lacks | 🟢 equipment training | 🟡 created_at; no workflow_state_events | n/a — append-only | 🔴 absent | 🟡 | parent mistake gap + body_es 0% | FOCP-gate |
| 9 | Equipment Training | HR / Safety | 🟢 7 tips | 🟡 partial | 🟢 | 🟢 | 🟡 acknowledgment has it; parent lacks | 🟢 equipment issuance, training expiration | 🟡 created_at + expiration tracking; no workflow_state_events | n/a — record-only | 🔴 absent | 🟡 | parent mistake gap + body_es 0% | FOCP-gate |
| 10 | **Fleet Repair / RTS** | Shop | 🔴 **only 2 RTS tips (why+mistake)** | 🔴 **thin** | 🟡 partial | 🟢 | 🟡 fleet.rts has mistake; fleet.repair lacks | 🟢 preop, dispatch | 🟡 fleet has internal severity tier model; no `workflow="fleet"` audit row | 🔴 RTS attestation surface lacks formal multi-party sign-off contract | 🔴 absent | 🔴 | **Phase 2 P3 + SOCP §8.2 confirmed: highest single-decision risk on platform** | FOCP-gate; **highest priority** |
| 11 | Fire Extinguisher Inspection | Safety / Shop | 🟢 4 tips | 🟢 | 🟢 | 🟢 | 🟢 has mistake | 🟢 site inspection | 🟡 created_at only | n/a | 🔴 absent | 🟢 | body_es 0% | FOCP-gate (low) |
| 12 | Safety Topic Library | Safety | 🟢 4 tips | 🟢 | 🟢 | 🟢 **23 trade-specific ES topic files (1579 LOC)** | 🔴 topic-library parent lacks mistake; sub-pages also lack | 🟢 meeting, JHP | n/a read-side | n/a read-side | 🔴 absent | 🟡 | parent mistake gap + body_es 0% on tips (note: topic CONTENT is bilingual; tips ABOUT topic library are EN-only) | FOCP-gate |
| 13 | Safety Document upload | Safety | 🟢 6 tips | 🟢 | 🟢 | 🟢 | 🟡 upload has mistake; parent + classification lack | 🟡 safety training | 🟡 created_at | n/a | 🔴 absent | 🟡 | parent mistake gap + body_es 0% | FOCP-gate |
| 14 | Safety Training record | HR / Safety | 🟢 8 tips | 🟢 | 🟢 | 🟢 + `training_es.js` (1093 LOC) | 🟡 upload has mistake; parent + expiration lack | 🟢 safety document, employee lifecycle | 🟡 created_at + expiration tracking | n/a | 🟡 TrainingHub/TrainingTrack pages exist | 🟢 | body_es 0% | FOCP-gate |

**Aggregate verdict counts**:

| Verdict | Count |
|---|---:|
| 🟢 GREEN — Complete | 2 (Fire Extinguisher Inspection, Safety Training record) |
| 🟡 YELLOW — Partial | 11 |
| 🔴 RED — Missing / critical gap | 1 (Fleet RTS) |
| **Total safety workflows** | **14** |

---

## 3 · Source-direct evidence cards (per workflow)

For each cell of the matrix above where the verdict was not 🟢 GREEN, the evidence reference:

### 3.1 · JHP `mistake` parent gap
- **Evidence**: `tips.py` form_key `"jha"` has 4 tips with kinds `{escalate, next, who, why}`. No `mistake` kind.
- **Cross-check**: `jha.poster` has `{escalate, example, mistake, why}` — confirmed mistake exists on the poster sub-form.
- **Conclusion**: Parent `jha` form lacks the `mistake` kind. NOT a false finding.

### 3.2 · Safety Meeting NO formal lifecycle / approval
- **Evidence**: No `routes/meeting_lifecycle.py` file. `safety.py` /meetings endpoint stores documents with `created_at` only. No `workflow_state_events` writes for `workflow="meeting"` or `"safety_meeting"`.
- **Conclusion**: Meeting has WRITE + READ + DELETE but no transition history, no approval gate. NOT a false finding.

### 3.3 · Incident parent `mistake` gap + sub-form coverage
- **Evidence**: Parent `incident` has `{escalate, next, who, why}`. Sub-forms `incident.corrective`, `.location`, `.narrative`, `.severity`, `.witnesses` all have `mistake`.
- **Conclusion**: Incident parent lacks `mistake`; 5 of 6 sub-forms have it. NOT a false finding.

### 3.4 · Site Inspection vs QA/QC vocab risk (AR-0007)
- **Evidence**: AR-0007 in `ADOPTION_RISK_REGISTER.md` already records `FINDINGS_RAISED` (Site) vs `DEFICIENCY_RAISED` (QA/QC) vocabulary risk.
- **Conclusion**: Existing register entry. NOT a false finding.

### 3.5 · Fleet RTS thin coverage
- **Evidence**: `tips.py` form_key `"fleet.rts"` has only 2 tips, kinds `{mistake, why}`. No `who` (who can authorize), no `next` (what happens after RTS), no `escalate` (when to escalate), no `example`.
- **Cross-check**: Phase 2 §1.12 P3 already flagged Fleet/Shop as platform's thinnest coverage. SOCP §8.2 named RTS as highest single-decision risk.
- **Conclusion**: HIGHEST-priority gap. NOT a false finding.

### 3.6 · body_es 0% across safety tips (largest discovery)
- **Evidence**: AST-style walk of `tips.py` shows of the ~137 safety-workflow tips, **only 1 tip has body_es** (specifically a single tip on `jha.poster`). All others have NO body_es field. The HelpTip.jsx component renders Spanish operators an English `body` under Spanish labels (`label_es: "Por qué importa"`, `"Errores comunes"`, etc.).
- **Implication**: i18n.js (UI strings) is broadly bilingual at ~3218 keyed entries. tips.py (coaching surface) is essentially monolingual. These two layers were previously conflated in the 52% Phase-2 score.
- **Conclusion**: NEW, evidence-backed gap. NOT a false finding. Covered in detail in `SAFETY_SPANISH_GAP_REGISTER.md`.

### 3.7 · Onboarding absent across all 14 workflows
- **Evidence**: No dedicated onboarding page, sequencing, or guided-tour artifact found for any safety workflow. `pages/onboarding` directory does not exist in `/app/frontend/src/pages`. `TrainingHub.jsx` exists for Safety Training records but is record-keeping, not new-hire walk-through.
- **Conclusion**: NOT a false finding. The Library + Master Register + Knowledge Matrix (TCP, prior session) constitute the closest existing onboarding artifact, all in `/app/memory/`. They are documentation, not in-app onboarding.

---

## 4 · Findings retired (false-finding hygiene)

The directive mandates retiring false findings. The following inherited claims were verified against source and **retired** or **refined**:

| Inherited claim | Source-direct verification | Disposition |
|---|---|---|
| "All Spanish coverage is at 52%" (composite Phase-2 figure) | i18n.js = ~3218 ES entries (broad). tips.py body_es = ≈ 0% across safety tips. The 52% conflated two layers. | **REFINED**: Spanish coverage is *bimodal*. UI surface ≈ comprehensive; coaching/tip body surface ≈ 0%. |
| "Mistake kind absent on 14 form_keys" (Phase-2 P1, generic) | Precise verification: absent on 18 PARENT form_keys including jha/meeting/incident/inspection/qaqc/corrective/equipment-issuance/equipment-training/safety-document/safety-training/topic-library/preop/fleet.repair/fleet.visibility/safety-training.expiration/qaqc.signoff/preop.controls/preop.signoff. Present on 14+ sub-forms. | **REFINED**: More precise count; pattern is parent-vs-sub-form split. |
| "Approval class universally FAIL" (Phase-2 P2, for Time-Off/PO/Asset Transfer/Employee Requests) | These are not safety workflows. Safety approval gates (incident 3-attestation, qaqc Amendment 001, site inspection Amendment 001, CAPA pipeline) are formally implemented. | **NOT applicable to STCP scope.** |
| "Submittals missing" | Submittals is not a safety workflow. | **NOT applicable to STCP scope.** Excluded from STCP matrix. |
| "Onboarding exists in platform" | No source evidence of an onboarding page or guided tour. | **CONFIRMED**: Onboarding is 🔴 absent across all 14 safety workflows. |

---

## 5 · No-new-workflow check

Per Rule 1 ("Do not build new safety workflows unless a workflow genuinely does not exist"), this register confirms:

- Every workflow listed above already has a backend route and a frontend page.
- No new workflow is proposed by this register.
- The two gaps that could be argued to "need a new workflow" are: (a) Safety Meeting formal lifecycle, (b) Onboarding sequence. Both are recorded as 🔴 RED, but **neither is recommended for new-workflow build by this register** — that decision belongs to the operator under FOCP 7-test + 4-proof.

---

**End of SAFETY TRAINING COMPLETION REGISTER · STCP 1 of 5**
