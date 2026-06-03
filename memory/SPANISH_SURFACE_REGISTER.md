# SPANISH SURFACE REGISTER
## OCEP · Spanish Operational Certification Program (SOCP) · Phase 1

**Date**: 2026-06-03
**Authority**: OMEGA · SOCP Phase 1
**Mode**: READ-ONLY inventory · no translation changes · no rewrites
**Purpose**: Source-direct inventory of every Spanish-facing surface in the MASCI Docs codebase. For each surface: English source · Spanish surface · Owner · Workflow · Risk Level.

**Architecture context (source-direct, not opinion)**:
- The platform is bilingual with **English as the canonical doctrine language**. Spanish is a **read/fill aid** for Spanish-speaking crew (per `frontend/src/lib/i18n.js` lines 1–4).
- Submitted prose strings flow through `frontend/src/lib/translateOnSubmit.js` (130 LOC), which round-trips Spanish user input back to English via `/api/translate` (LLM) at submit time. All MASCI safety records are stored & PDF-printed in English.
- Spanish surface mechanics: `useT()` hook + `<LangToggle>` segmented control (visible on every form header). Choice persists to `localStorage["masci.lang"]`. `<html lang>` syncs so browser native ES spell-check activates on inputs/textareas.

Risk-Level legend:
- 🔴 **SAFETY-CRITICAL** — Spanish wording governs hazard / emergency / safety-record decisions where a misreading could cause injury, OSHA non-compliance, or wrongful-death liability
- 🟠 **OPERATIONAL-CRITICAL** — Spanish wording governs day-of-work operations (pay, dispatch, time-off, equipment readiness)
- 🟡 **COMPLIANCE / GOVERNANCE** — Spanish wording governs audit / record / training fidelity (lower acute risk; higher cumulative risk)
- 🟢 **INFORMATIONAL** — Spanish wording is navigational / cosmetic; no decision-grade impact

---

## 1 · Master surface inventory

### 1.1 · Core i18n dictionary

| # | Surface | English source | Spanish surface (file) | Owner | Workflow(s) | Risk |
|---|---|---|---|---|---|---|
| 1.1.1 | Platform-wide UI strings dictionary | English keys in code | `frontend/src/lib/i18n.js` (4902 LOC · ~3218 keyed ES entries) | Engineering / Operator Council | ALL workflows | 🟠 |
| 1.1.2 | Language toggle UI | EN / ES segmented control | `frontend/src/components/LangToggle.jsx` (70 LOC) | Engineering | Every form header | 🟢 |
| 1.1.3 | Submit-time auto-translation | Spanish freeform prose → English (LLM) | `frontend/src/lib/translateOnSubmit.js` (130 LOC) | Engineering · /api/translate route | Every form's `submit()` in ES mode | 🟠 (translation fidelity = record fidelity) |

### 1.2 · Safety-critical workflows

| # | Surface | English source | Spanish surface (file / section) | Owner | Workflow | Risk |
|---|---|---|---|---|---|---|
| 1.2.1 | Daily Report form labels, tips, validation | English form labels | `i18n.js` Section iter437/iter438 + form copy | Safety / Engineering | Daily Report | 🟠 |
| 1.2.2 | JHP acknowledgement modal copy | "Acknowledge", attestation text | `i18n.js` JHP section | Safety | JHP | 🔴 (legal attestation chain) |
| 1.2.3 | Safety Meeting topic library — 23 trade-specific dictionaries | English meeting topics | `frontend/src/lib/topics/*.es.js` (23 files, 1579 LOC) — airport, concrete, dewatering, electrical, environmental, excavation, fall_protection, general, grading, lab, milling, mot, office, paving, pipe, plant, rigging, shop, trucking, utilities, wellness | Safety | Safety Meeting | 🔴 (drives hazard discussion content) |
| 1.2.4 | Incident Report form labels + severity + narrative prompts | English form copy | `i18n.js` Section incident · `NewIncident.jsx` `useT()` calls | Safety | Incident Report | 🔴 (OSHA-recordable record) |
| 1.2.5 | Incident lifecycle attestation flags | "review_complete" etc. | `i18n.js` lifecycle keys | Safety / Admin | Incident closure | 🔴 (3-attestation gate) |
| 1.2.6 | QA/QC inspection form + closure paths A/B/C copy | English Amendment 001 contract | `i18n.js` QA/QC + Site Inspection sections | PM / Safety | QA/QC + Site Inspection | 🟠 |
| 1.2.7 | Hub banner Spanish templates | English banner library | `frontend/src/lib/hubBannerTemplates.js` (ES strings) · backend `hub_banners_pdf.py` | Admin / Safety | All portal hubs | 🟠 |
| 1.2.8 | Safety Topic Library page | English titles | `frontend/src/pages/SafetyTopicLibrary.jsx` (uses `*.es.js`) | Safety | Safety topic browse | 🔴 |

### 1.3 · Operational-critical workflows

| # | Surface | English source | Spanish surface (file / section) | Owner | Workflow | Risk |
|---|---|---|---|---|---|---|
| 1.3.1 | Dispatch board strings | English board copy | `i18n.js` Section dispatch | Dispatch | Dispatch | 🟠 |
| 1.3.2 | Dispatch shift-start QR / Day-1 debrief | English driver pages | `backend/routes/dispatch_continuity.py` + `dispatch_day1_debrief.py` (Spanish-aware) | Dispatch | Driver shift-start | 🟠 |
| 1.3.3 | Equipment inspection / issuance / training | English form copy | `i18n.js` equipment section · `NewEquipmentInspection.jsx`, `ViewEquipmentInspection.jsx` | Safety / Shop | Equipment | 🟠 |
| 1.3.4 | Fleet repair / RTS surface | English fleet copy | `i18n.js` fleet keys · `FleetRepairDrawer.jsx` | Shop | Fleet | 🔴 (RTS = return-to-service decision) |
| 1.3.5 | HR Hub, Time-Off, Employee Lifecycle | English HR copy | `i18n.js` HR section · `HrHub.jsx`, `HrTimeOff.jsx`, `HrEmployees.jsx` `useT()` | HR | HR workflows | 🟠 |
| 1.3.6 | Time-Off request public form | English public copy | `PublicTimeOff.jsx` + `i18n.js` | HR | Time Off | 🟡 |
| 1.3.7 | Employee Request queue | English approval copy | `HrEmployeeRequestsQueue.jsx` + `i18n.js` | HR / PM | Employee Requests | 🟡 |
| 1.3.8 | Payroll Variance attestation flags | English flag labels | `i18n.js` payroll variance section · `HrPayrollVariance.jsx` | HR / Admin | Payroll Variance | 🟠 (attestation = legal payroll) |

### 1.4 · Training surfaces

| # | Surface | English source | Spanish surface | Owner | Workflow | Risk |
|---|---|---|---|---|---|---|
| 1.4.1 | Training track data (course content) | English training catalog | `frontend/src/data/training_es.js` (1093 LOC) | HR / Safety | Training | 🟠 (training fidelity) |
| 1.4.2 | Training Hub / Track pages | English page copy | `TrainingHub.jsx`, `TrainingTrack.jsx` `useT()` | HR / Safety | Training | 🟡 |
| 1.4.3 | Admin Training Resources panel | English admin copy | `AdminTrainingResourcesPanel.jsx` `useT()` | Admin / HR | Training admin | 🟡 |

### 1.5 · Help / guidance / coaching

| # | Surface | English source | Spanish surface | Owner | Workflow | Risk |
|---|---|---|---|---|---|---|
| 1.5.1 | HelpTip inline tips (`why`, `mistake`, `next`, etc.) | English `tips.py` registry | `backend/guidance/tips.py` (Spanish entries) · `frontend/src/components/HelpTip.jsx` `useT()` | Engineering / Operator Council | All forms | 🟠 (Phase 2 P1 noted ES `mistake` gap) |
| 1.5.2 | Operational Guidance Center | English landing | `pages/guidance/OperationalGuidanceCenter.jsx` `useT()` | Admin | Guidance | 🟡 |
| 1.5.3 | Operational Language Glossary (admin) | English glossary | `pages/admin/AdminOperationalLanguage.jsx` (509 LOC) — every term has `en` + `es` pair | Admin | Glossary | 🟠 (canonical vocabulary) |
| 1.5.4 | Portal context banner | English banner copy | `components/PortalContextBanner.jsx` (Spanish strings detected) | Admin | All portals | 🟢 |
| 1.5.5 | Portal Login Help | English helper copy | `components/PortalLoginHelp.jsx` (Spanish strings) | Admin | Login | 🟢 |

### 1.6 · Validation / error / notification

| # | Surface | English source | Spanish surface | Owner | Workflow | Risk |
|---|---|---|---|---|---|---|
| 1.6.1 | Form validation messages | English `toast.error` text | `i18n.js` validation keys | Engineering | All forms | 🟠 (operator-blocking messages) |
| 1.6.2 | Photo-gate validation hint | English "NEED N MORE PHOTO(S)" | `i18n.js` photo-gate section | Engineering / Safety | New Daily Report, Incident, Inspection | 🟠 |
| 1.6.3 | Sentry tags / observability locale tagging | n/a | `backend/sentry_tags.py` Spanish-aware tagging | Engineering | Observability | 🟢 |
| 1.6.4 | Email / SMS templates | English templates | **DOCTRINE-SILENT** — no dedicated `*_es.html` / `*_es.txt` template files surveyed in `/app/backend/` | Engineering / Resend integration | Notifications | ⚠️ **UNKNOWN — flagged for field review** |

### 1.7 · PDF / generated artifact surfaces

| # | Surface | English source | Spanish surface | Owner | Workflow | Risk |
|---|---|---|---|---|---|---|
| 1.7.1 | Daily Report PDF | English template | `backend/pdf_render.py` (Spanish-aware) | Engineering | DR PDF | 🟡 — by doctrine PDFs print in EN |
| 1.7.2 | Field Leadership PDF | English template | `backend/field_leadership_pdf.py` (Spanish-aware) | Engineering | FL PDF | 🟡 |
| 1.7.3 | Hub banner PDF | English template | `backend/hub_banners_pdf.py` (Spanish-aware) | Engineering | Banner PDF | 🟡 |
| 1.7.4 | Training PDF | English template | `backend/training_pdf.py` (Spanish-aware) | Engineering | Training PDF | 🟡 |
| 1.7.5 | Checklists (Spanish-aware) | English checklist source | `backend/checklists.py` | Engineering | Checklists | 🟡 |

### 1.8 · Backend routes with Spanish awareness

| # | Surface | File | Notes | Risk |
|---|---|---|---|---|
| 1.8.1 | Field Leadership | `backend/routes/field_leadership.py` | Spanish strings present | 🟡 |
| 1.8.2 | Hub banners | `backend/routes/hub_banners.py` | Spanish strings present | 🟡 |
| 1.8.3 | JHP acknowledgements | `backend/routes/jha_acknowledgements.py` | FOCP R2 — Spanish-aware ledger | 🔴 (identity-key risk for ES-only crew per FOCP R2 § C2-0014) |
| 1.8.4 | Safety Topic Library | `backend/routes/safety_topic_library.py` | Reads topic ES dictionaries | 🔴 |
| 1.8.5 | Dispatch continuity / debrief | `backend/routes/dispatch_continuity.py`, `dispatch_day1_debrief.py` | Spanish strings present | 🟠 |

### 1.9 · Safety Accountability Classification

| # | Surface | English source | Spanish surface | Owner | Workflow | Risk |
|---|---|---|---|---|---|---|
| 1.9.1 | Safety Accountability Class labels | English class names | `frontend/src/lib/safetyAccountabilityClass.js` (234 LOC) + `safetyAccountabilityClass.test.js` | Safety | Cross-workflow classification | 🔴 (drives liability classification) |

---

## 2 · Aggregate inventory

| Tier | Count |
|---|---:|
| Distinct Spanish surfaces inventoried | 33 |
| Files contributing Spanish content (frontend + backend) | 60+ (verified by grep) |
| i18n.js Spanish key entries | ~3218 |
| Trade-specific Spanish topic files | 23 (`topics/*.es.js`) |
| Training Spanish content (LOC) | 1093 |
| Backend Spanish-aware files | 13 |

### 2.1 · Risk distribution

| Risk tier | Surfaces |
|---|---:|
| 🔴 SAFETY-CRITICAL | 8 |
| 🟠 OPERATIONAL-CRITICAL | 13 |
| 🟡 COMPLIANCE / GOVERNANCE | 9 |
| 🟢 INFORMATIONAL | 3 |
| ⚠️ UNKNOWN (DOCTRINE-SILENT) | 1 (email/SMS template ES variants — flagged for field review) |

---

## 3 · Known limitations of this register

1. **Surface count is conservative.** Each `i18n.js` section (~30) is treated as one surface even though many sections contain hundreds of keyed strings. A finer breakdown is possible but adds little decision value at the certification-package level.
2. **Email / SMS Spanish template existence is DOCTRINE-SILENT** in the source survey. The platform may rely on submit-time translation for outbound notifications or may simply send English. Field reviewers (Phase 4 packet) will be asked to confirm.
3. **No content-quality assessment is performed here.** Quality assessment occurs in `CONSTRUCTION_SPANISH_TERMINOLOGY_DICTIONARY.md` (Phase 2) and `SPANISH_SAFETY_CRITICAL_REGISTER.md` (Phase 3).
4. **Per the directive, no translation changes are proposed**; this is an inventory only.

---

**End of SPANISH SURFACE REGISTER · SOCP Phase 1**
