# SAFETY COACHING COMPLETION REGISTER
## OCEP · Operational Coaching & Spanish Parity Completion Program (OCSPCP) · 3 of 7

**Date**: 2026-06-03
**Authority**: OMEGA / FOCP DIRECTIVE — OCSPCP Phase 3
**Mode**: READ-ONLY · source-direct · NO new safety workflows
**Note**: This register intentionally consolidates and references existing source-direct evidence in:
- `SAFETY_TRAINING_COMPLETION_REGISTER.md` (STCP 1 of 5)
- `SAFETY_COACHING_GAP_REGISTER.md` (STCP 2 of 5)
- `SAFETY_SPANISH_GAP_REGISTER.md` (STCP 3 of 5)
- `SAFETY_HELP_CONTENT_REGISTER.md` (STCP 4 of 5)
- `SAFETY_CERTIFICATION_READINESS_REPORT.md` (STCP 5 of 5)
- `SAFETY_OPERATIONAL_TRAINING_CERTIFICATION.md` (STCP final)

It does **not** re-derive evidence already audited under STCP. It adds the additional safety workflows the directive lists (Near Miss, Heat Illness, Excavation, Utility Exposure, PPE) and verifies them against source.

---

## 1 · Directive's safety workflow list — verification against source

| # | Directive-named workflow | Source-direct status |
|---|---|---|
| 1 | Incident | ✅ EXISTS — `routes/safety.py` /incidents + `incident_lifecycle.py` (STCP §1) |
| 2 | Near Miss | 🟡 **CLASSIFIED AS INCIDENT SUB-TYPE** — `i18n.js` incident.severity includes "Near-Miss / Cuasi-accidente" (SOCP §4 #6). Not a distinct workflow; rolls up to Incident lifecycle. **No new workflow needed.** |
| 3 | JHP | ✅ EXISTS — JHP + acknowledgement (STCP §1) |
| 4 | Safety Meeting | ✅ EXISTS (STCP §1) |
| 5 | Site Inspection | ✅ EXISTS (STCP §1) |
| 6 | QA/QC Hold | 🟡 **CLASSIFIED AS QA/QC LIFECYCLE STATE** — QA/QC Inspection lifecycle (`qaqc_lifecycle.py`) handles deficiency-raised / pending-re-inspection / closure A/B/C states. "Hold" is the operational name for `PENDING_RE_INSPECTION`. **No new workflow needed.** |
| 7 | Equipment Training | ✅ EXISTS (STCP §1) |
| 8 | Equipment Issuance | ✅ EXISTS (STCP §1) |
| 9 | Fleet DVIR | ✅ EXISTS — `tips.py` fleet.dvir (4 tips, has mistake). Daily Vehicle Inspection Report = pre-trip; closely related to preop. |
| 10 | Fleet Return To Service | ✅ EXISTS — `tips.py` fleet.rts (2 tips). **Highest single-decision risk per SOCP §8.2 + STCP §5.** |
| 11 | Heat Illness | 🟡 **TOPIC-LIBRARY-LEVEL COVERAGE** — source survey: `frontend/src/lib/topics/wellness.es.js` contains wellness-related topics including heat illness; no dedicated workflow / route / state machine. Operationally surfaces inside Safety Meeting topic library, not as a standalone workflow. **No new workflow needed; topic-library coverage suffices.** |
| 12 | Excavation | 🟡 **TOPIC-LIBRARY-LEVEL COVERAGE** — `frontend/src/lib/topics/excavation.es.js` (4 trade-specific topics: trenching_shoring, soil_classification, excavation_potholing_daylight, excavation_spoil_placement). Sample-verified decision-grade prose (SOCP §2, §6, §7). Operationally surfaces inside JHP + Safety Meeting. **No new workflow needed.** |
| 13 | Utility Exposure | 🟡 **TOPIC-LIBRARY-LEVEL COVERAGE** — `excavation.es.js` `excavation_potholing_daylight.incident_pattern` covers 811 / locate / fiber / gas main / energized line strikes. **No new workflow needed.** |
| 14 | PPE | 🟡 **TIP-LEVEL + INSPECTION SUB-FORM** — `tips.py` inspection.ppe has 3 tips (escalate / mistake / why). Surfaces as a Site Inspection sub-form. **No new workflow needed.** |

**Per directive Rule 1 ("Do not build new safety workflows unless a workflow genuinely does not exist"):** All 14 directive-listed safety workflows are accounted for. **Zero new workflows recommended.** Items 2 (Near Miss), 6 (QA/QC Hold), 11 (Heat Illness), 12 (Excavation), 13 (Utility Exposure), 14 (PPE) are sub-states or topic-library items inside existing workflows.

---

## 2 · Per-safety-workflow coaching completeness (consolidated from STCP)

For each directive-recognized safety workflow:

| # | Workflow | EN coaching | ES coaching | Common Mistakes | Escalation guidance | Lifecycle guidance | Source-direct verdict |
|---|---|:-:|:-:|:-:|:-:|:-:|---|
| 1 | Incident Report (incl. Near Miss) | 🟢 | 🔴 | 🟡 (5 of 6 sub-forms) | 🟢 (escalate kind on 4 sub-forms; OSHA auto-escalate per spec) | 🟢 (`incident_lifecycle.py`) | 🟡 |
| 2 | JHP + Ack | 🟢 | 🔴 | 🟡 (parent missing) | 🟢 (jha + jha.poster have escalate) | 🔴 (no LifecycleGuide for JHP) | 🟡 |
| 3 | Safety Meeting | 🟢 | 🔴 | 🟢 (5 of 6 sub-forms) | 🟢 (4 forms have escalate) | 🔴 (no lifecycle file) | 🟡 |
| 4 | Site Inspection | 🟢 | 🔴 | 🟢 (4 of 5 sub-forms) | 🟢 (3 forms have escalate) | 🟢 (`site_inspection_lifecycle.py`) | 🟡 |
| 5 | QA/QC Inspection (incl. QA/QC Hold) | 🟢 | 🔴 | 🟢 (4 of 6 sub-forms) | 🟢 (3 forms have escalate) | 🟢 (`qaqc_lifecycle.py`) | 🟡 |
| 6 | Equipment Training | 🟢 | 🔴 | 🟡 (1 of 4 sub-forms — acknowledgment) | 🟢 (3 forms have escalate) | 🔴 (no lifecycle) | 🟡 |
| 7 | Equipment Issuance | 🟢 | 🔴 | 🟡 (1 of 5 sub-forms) | 🟢 | 🔴 | 🟡 |
| 8 | Fleet DVIR | 🟢 | 🔴 | 🟢 (4 tips inc. mistake) | 🟢 (4 tips inc. escalate) | 🟡 (no LifecycleGuide; severity tier internal) | 🟡 |
| 9 | **Fleet Return to Service (RTS)** | 🔴 (2 tips) | 🔴 | 🟡 (mistake present) | 🔴 (no escalate kind) | 🔴 | 🔴 |
| 10 | Heat Illness (topic) | 🟢 (via wellness.es.js + meetings tips) | 🟢 (topic file is ES-native) | 🟡 (within topic content) | 🟡 (topic action_items) | n/a | 🟢 (topic-library) |
| 11 | Excavation (topic) | 🟢 (via excavation.es.js + jha + meeting tips) | 🟢 (4 ES topics, decision-grade) | 🟢 (each topic has incident_pattern) | 🟡 | n/a | 🟢 |
| 12 | Utility Exposure (topic) | 🟢 (excavation_potholing_daylight) | 🟢 | 🟢 (decision-grade ES content) | 🟢 ("Llame al 911 y al servicio") | n/a | 🟢 |
| 13 | PPE (inspection.ppe sub-form) | 🟢 (3 tips) | 🔴 (Layer B) | 🟢 (mistake present) | 🟢 (escalate present) | n/a | 🟡 |
| 14 | CAPA / Corrective | 🟢 | 🔴 | 🟢 (3 of 3 sub-forms) | 🟢 | 🟡 (status_history append only; no LifecycleGuide) | 🟡 |

**Verdict counts**: 🟢 3 (topic-library workflows: Heat Illness, Excavation, Utility Exposure — Spanish-native via topic files) · 🟡 10 · 🔴 1 (Fleet RTS).

---

## 3 · Fleet RTS — highest-priority safety coaching gap (per directive)

**Per directive: "Fleet Return To Service receives highest priority."**

### 3.1 · Current state (source-direct)

| Attribute | Current | Evidence |
|---|---|---|
| Tip count on `fleet.rts` | 2 | `tips.py` AST walk |
| Kinds present | `why`, `mistake` | Confirmed |
| Kinds missing | `who`, `next`, `escalate` | Confirmed |
| body_es coverage | 0 of 2 | Confirmed |
| LifecycleGuide wired | No | No fleet lifecycle file with WORKFLOW="fleet" found |
| workflow_state_events audit | No | No `workflow="fleet"` writes in routes |
| Glossary entry "Return to Service" | Likely (Layer D); not in-flow linked from fleet pages | AdminOperationalLanguage admin-route-only |
| Spanish parity | 🔴 | Layer B body_es = 0 |
| Field reviewer attention assigned | Yes (SOCP Phase 4 packet §3.8 highest priority) | Confirmed in SOCP packet |

### 3.2 · Source-direct closure path (no engineering authorized, informational only)

| Step | Scope | Type |
|---|---|---|
| 1 | Author EN `who` tip on `fleet.rts` (who can authorize RTS; mechanic / supervisor / contract gate) | Content addition to existing form_key |
| 2 | Author EN `next` tip on `fleet.rts` (dispatch notification, board update, etc.) | Content |
| 3 | Author EN `escalate` tip on `fleet.rts` (when RTS must NOT be granted) | Content |
| 4 | Author `body_es` on all 5 fleet tips (existing 2 + new 3) | Content (ES) |
| 5 | Wire LifecycleGuide for fleet repair pipeline | Reuse existing LifecycleGuide component |
| 6 | Add glossary in-flow tooltip on RTS button surface | UI wire (no new component) |

**No new workflow. No new module.** All reuse existing infrastructure. Operator decides FOCP authorization.

---

## 4 · Aggregate safety coaching completion

| Metric | Value |
|---|---:|
| Directive-recognized safety workflows | 14 |
| Already 🟢 GREEN (topic-library workflows with native ES content) | 3 |
| 🟡 YELLOW (EN coverage exists; ES Layer B gap) | 10 |
| 🔴 RED (insufficient coverage on a high-stakes surface) | 1 (Fleet RTS) |
| Aggregate safety coaching completion % | **3 / 14 = 21% GREEN (composite, ES-inclusive)** · **13 / 14 = 93% GREEN (EN-only)** |

The 21% / 93% split is the headline finding: **safety coaching is largely complete in English, almost entirely uncovered in Spanish at the tip-body layer.**

---

## 5 · Retired false findings (safety coaching scope)

| Inherited claim | Verdict | Disposition |
|---|---|---|
| "Near Miss is a separate workflow" | Verified: handled as Incident severity. | **CORRECTED.** |
| "Heat Illness needs its own workflow" | Topic-library handles it. | **NO NEW WORKFLOW.** |
| "PPE needs its own workflow" | Site Inspection ppe sub-form covers it. | **NO NEW WORKFLOW.** |
| "Excavation needs its own workflow" | JHP + Safety Meeting + 4 excavation.es.js topics cover it. | **NO NEW WORKFLOW.** |
| "Utility Exposure needs its own workflow" | Same as Excavation. | **NO NEW WORKFLOW.** |
| "QA/QC Hold is a separate workflow" | It's the PENDING_RE_INSPECTION state of QA/QC. | **NO NEW WORKFLOW.** |
| "Fleet RTS is YELLOW" (STCP) | **CORRECTED at OCSPCP scope to 🔴** — only 2 tips, no `who/next/escalate`, no lifecycle, no body_es. | **REFINED.** |

---

**End of SAFETY COACHING COMPLETION REGISTER · OCSPCP 3 of 7**
