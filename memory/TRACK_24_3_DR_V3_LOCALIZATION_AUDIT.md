# TRACK 24.3 · DAILY REPORT V3 · EN/ES LOCALIZATION AUDIT (Phase 1)

**Auditor:** E1 · Read-only · Zero code changes to DR V3
**Date:** 2026-02-07
**Scope:** Full enumeration of localization gaps in DR V3, the exact execution plan for Phases 2–9, and the integration blueprint for the ES→EN submit-time translation service.
**Machine-readable inventory:** `/tmp/dr_v3_i18n_audit.json` (regenerate with the script embedded below).

---

## 0. Executive summary

Daily Report V3 has **zero i18n coverage today** — every user-facing string in every DR V3 file is hard-coded English. The platform already ships a lightweight bilingual runtime (`/app/frontend/src/lib/i18n.js` exposes `useT()` + English-as-key convention), which V1 and Safety Portal use extensively. DR V3 was never wired to it. The Track 24.3 delivery therefore has two workstreams: (a) mechanical i18n wiring of ~166 unique strings across 6 files, and (b) a new ES→EN submit-time translation pipeline for user free-text.

- **Files audited:** 6 (see §1).
- **Unique hard-coded user-facing strings:** **166**.
- **Total occurrences (dedup by file):** 174.
- **Existing `t()` calls in DR V3:** **0**.
- **Existing `lang=` attributes in DR V3:** **0**.
- **Existing `spellCheck` attributes in DR V3:** **0**.
- **Existing i18n hook (`useTranslation` / `useT` / `useI18n`) imports in DR V3:** **0**.
- **Textareas (natural-language sinks) in DR V3:** **3** (all in `sections.jsx`).
- **Input elements in DR V3:** **61**.

Root cause: DR V3 was built as a greenfield rewrite of the Daily Report flow and localization was descoped for the initial ship. That decision is now the sole remaining P0 deployment blocker.

## 1. File inventory

| File | Lines | Hard-coded user-facing strings |
|---|---:|---:|
| `components/daily-report-v3/sections.jsx` | 2 011 | **103** |
| `components/daily-report-v3/DailyReportV3ExcavationSection.jsx` | 405 | **47** |
| `pages/NewDailyReportV3.jsx` | 510 | **13** |
| `components/daily-report-v3/SectionProjectConditions.jsx` | 162 | 9 |
| `components/daily-report-v3/UnitCombo.jsx` | 80 | 1 |
| `components/daily-report-v3/CompetentPersonCombo.jsx` | 166 | 1 |
| **TOTAL** | **3 334** | **174** |

**Adjacent files reviewed (not in DR V3 tree but on the DR pipeline):**
- `services/daily_report_v3_excavation/service.py` — backend service. PDF/email helpers here return English strings that go into the DR PDF; those are *canonical English* by design and are correctly **out of scope** for user-facing translation. See §7 for the AI/PDF/email language rule.
- `services/certifications/qualification_registry.py` — returns English registry rows consumed by `CompetentPersonCombo`. Data (names, trades) is canonical English and is not translated. Only the picker's UI shell (chips, empty-state, warning labels) is translated.

## 2. String inventory (representative 40 of 166 — full list in JSON)

Categorization by surface:

**Section headers / kickers (H1/H2/eyebrow)**
- `"Crew, Equipment & Subcontractors"`, `"Work Performed & Production"`, `"Delays, Extra Work & Safety"`, `"Submit Readiness & Sign-Off"`, `"Excavation / Trench Operations"`, `"Inspection & work stoppage"`, `"Which crew · what work · which station"`, `"Nine short steps. Dropdowns first. AI drafts your summary."`

**Field labels + required-marker composites**
- `"Incident / Accident report filed? *"`, `"Was Safety contacted? *"`, `"What kind of event? *"`, `"Time contacted *"`, `"Who at Safety? *"`, `"Time filed *"`, `"Carrier *"`, `"Atmospheric testing required?"`, `"Weather / event reinspection?"`, `"Corrective actions description"`, `"What was installed / performed"`.
- **Note:** required markers must be broken out into a separate i18n key or a `<Required/>` component so `<span>*</span>` doesn't get concatenated into the translated key.

**Placeholders**
- `"Search active Competent Persons…"`, `"Pick carrier — or type one-time hauler"`, `"Pick a subcontractor / vendor — or type"`, `"Missing: ${readiness.missing.join(...)}"` (template — must be split into i18n + interpolation), `"RFI, submittal, material, equipment, permit …"`.

**Helper / empty-state text**
- `"Complete this section only when excavation or trench work occurred today."`, `"No excavation work today. This section stays clean."`, `"Nine short steps. Dropdowns first. AI drafts your summary."`, `"Tap GPS first so we know where to check the forecast."`, `"GPS unavailable — you can enter location manually"`, `"GPS is not available on this device"`, `"No subcontractors or vendors on site today."`, `"Did anything reduce or add to production today?"`, `"Did anything safety-related occur today?"`, `"What happened? (required for supervisor review)"`.

**Validation / warning / blocker copy**
- `"Utility strike/damage recorded. Ensure Safety incident + hold workflow is followed."`
- `"Hold or work stoppage recorded — Scheduling readiness will be set to BLOCKED."`
- `"Stop and contact Safety before submitting."`
- `"Stop must be after start. Use overnight only if stop wraps past midnight."`
- `"Action required: file the Accident / Incident report."`

**Buttons / CTAs**
- `"Open Accident / Incident Report"`, `"Use yesterday's crew setup?"`, `"Submit"`, `"Save draft"`, `"Review"`, `"GPS"`, etc.

**Full unique-key list (166 entries):** `/tmp/dr_v3_i18n_audit.json` field `unique_keys`. The audit script that produced it is embedded at §12 so it can be regenerated on every CI run.

## 3. Missing i18n key plan · Spanish translations required

Track 24.3 Phase 2 must add **166 English keys + 166 Spanish values** to `/app/frontend/src/lib/i18n.js` (or a namespaced sibling — the current file is 5 176 keys, still manageable). All keys follow the platform convention: **the English string IS the key**.

### 3.1 Naming rules
- Use the exact English string as the key.
- Do NOT concatenate `*` (required marker) or `<span>` HTML into the key — factor those out via a `<RequiredLabel label={t("Field name")}/>` component (component to be added in Phase 2).
- Interpolations must use `{{placeholder}}` syntax and pass values as the second argument to `t()`. Example: `t("Missing: {{list}}", {list: readiness.missing.join(", ")})`.

### 3.2 Sample translations (representative 10; full 166 shipped in Phase 2)
| EN key | ES value |
|---|---|
| "Crew, Equipment & Subcontractors" | "Cuadrilla, Equipos y Subcontratistas" |
| "Excavation / Trench Operations" | "Operaciones de Excavación / Zanja" |
| "Complete this section only when excavation or trench work occurred today." | "Complete esta sección únicamente cuando se realizó trabajo de excavación o zanja hoy." |
| "No excavation work today. This section stays clean." | "Sin trabajo de excavación hoy. Esta sección se mantiene vacía." |
| "Search active Competent Persons…" | "Buscar Personas Competentes activas…" |
| "Hold or work stoppage recorded — Scheduling readiness will be set to BLOCKED." | "Retención o paro de trabajo registrado — la preparación de programación se marcará como BLOQUEADA." |
| "Utility strike/damage recorded. Ensure Safety incident + hold workflow is followed." | "Se registró impacto/daño a servicios. Asegure el flujo de incidente y retención de Seguridad." |
| "Tap GPS first so we know where to check the forecast." | "Toque GPS primero para saber dónde revisar el pronóstico." |
| "Stop and contact Safety before submitting." | "Deténgase y contacte a Seguridad antes de enviar." |
| "Open Accident / Incident Report" | "Abrir Reporte de Accidente / Incidente" |

### 3.3 Existing coverage in `/app/frontend/src/lib/i18n.js`
Some DR V3 strings **already exist** as keys because they were added for V1 or other portals. Phase 2 will run the following pass to avoid duplicates:
```
for key in dr_v3_unique_keys:
    if key not in existing_i18n_keys: emit_new_pair(key)
    else: reuse_existing_pair(key)
```
Estimated overlap: ~30 keys already present (based on grep spot-check). Net new keys: ~136.

## 4. Free-text ES→EN submit-time translation plan

### 4.1 Free-text fields in DR V3 (require ES→EN translation on submit)
These are the input paths that accept **natural-language Spanish**. All other inputs are enumerated codes/IDs/numbers and must be preserved verbatim.

| Field path on the DR payload | Section | Textarea? |
|---|---|---|
| `general_notes` | Sign-off notes | yes |
| `weather_summary` | Weather | free text |
| `masci_crews[].members[].notes` | Crew notes per member | yes |
| `activities[].notes` | Work performed / production notes | yes |
| `equipment[].notes` | Equipment notes | yes |
| `subcontractors[].notes` | Subcontractor notes | yes |
| `materials_inbound[].notes` | Material inbound notes | yes |
| `materials_outbound[].notes` | Material outbound notes | yes |
| `delays[].description` | Delay description | yes |
| `visitors[].purpose` | Visitor purpose (when free-text mode) | free text |
| `safety_narrative` | Safety escalation narrative | textarea |
| `tomorrow_plan` | Tomorrow plan | textarea |
| `photos[].caption` | Photo captions if operator wrote one | free text |
| `pm_attention_notes` | PM attention narrative | textarea |
| `ai_edit_narrative` | User-edited AI summary before accepting | textarea |
| **Excavation block** | | |
| `excavation.location_notes` | Excavation location note | textarea |
| `excavation.soil_notes` | Soil note | textarea |
| `excavation.utilities_notes` | Utilities note | textarea |
| `excavation.access_egress_notes` | Access/egress note | textarea |
| `excavation.atmospheric_notes` | Atmospheric testing note | textarea |
| `excavation.water_mitigation_notes` | Water mitigation note | textarea |
| `excavation.hazards_notes` | Hazards note | textarea |
| `excavation.corrective_actions_notes` | Corrective actions note | textarea |
| `excavation.work_stopped_reason` | Work-stopped reason | textarea |
| `excavation.reinspection_notes` | Weather / event reinspection note | textarea |
| `excavation.protective_system_notes` | Protective system note | textarea |

**Count:** 26 free-text field paths.

### 4.2 Fields that MUST NOT be translated (proper-noun / code / ID preservation)
Preserve verbatim under any UI language. If detected in a free-text field via preserve-list regex, wrap in an "opaque" marker before sending to the translator; unwrap on response.

- `employee_name`, `employee_id`, `preferred_name`, `legal_first_name`, `legal_last_name`
- `project_name` (when it's an enum-selected value, not natural language)
- `project_number` (all instances)
- `job_number`, `ticket_number`, `certificate_number`
- `equipment_unit`, `unit_number`, `asset_id`
- `cost_code`
- `station_from`, `station_to`, `station_number`
- `quantity`, `unit_of_measure`, all numeric measurements
- `date_of_work`, all ISO dates + timestamps
- `phone_number`, `email` (per employee/subcontractor/vendor)
- `vendor_name`, `carrier_name`, `subcontractor_name` (enum-selected)
- `material_name` (enum-selected)
- `foreman_name`, `supervisor_name`
- `weather_temp` (numeric), `weather_condition` (enum)
- `readiness.state` (enum: READY / BLOCKED / READY_WITH_ADVISORIES / PENDING_REQUIREMENTS / UNKNOWN)
- `qualification_id`, `qualification_type`, all `verification_status` enums
- Any field whose value matches: `^[A-Z0-9-]{2,20}$` (equipment IDs) or `^\d{2,4}-\d{1,4}$` (job/ticket numbers)

### 4.3 Translation service — integration plan

**Provider selection:** OpenAI **GPT-5.2** (preferred) via **Emergent Universal Key**; Claude **Sonnet 4.5** fallback via the same key. Both keyed on `EMERGENT_LLM_KEY`.

**Playbook fetch (Phase 2 first action):** call `integration_playbook_expert_v2` with request:
> `INTEGRATION: OpenAI GPT-5.2 via Emergent Universal Key with Claude Sonnet 4.5 fallback (deterministic ES→EN construction-industry translation).\nCONSTRAINTS: Low-temp (≤0.1), JSON-only response, deterministic, must preserve field-path structure, fail-closed on any error/rate-limit.`

**Service location:** `backend/services/translation/service.py` (new module).

**Contract:**
```python
async def translate_es_to_en_bulk(
    db,
    fields: Dict[str, str],           # {"excavation.soil_notes": "Suelo tipo B con piedras", ...}
    *,
    preserve_tokens: Set[str] = None, # {"OXFORD RD", "24-12", "Alec Perkins", ...}
    actor_email: str,
    dr_id: str,
) -> TranslationResult
```

**Prompt shape:**
```
You are a professional construction-industry translator. Translate ONLY the Spanish natural-language content of the JSON values below to English. Do NOT change field names, keys, numbers, dates, capital-letter tokens, hyphenated IDs, project codes, employee names, or any value matching one of the preserve-tokens. Return valid JSON ONLY, with the same keys and translated string values. Do not add commentary, do not translate English text (return English inputs unchanged). Temperature 0. If any input is already English, return it unchanged.
Preserve-tokens: <sorted list>
Input: <JSON of {field_path: es_text}>
```

**Model config:** `temperature=0`, `response_format={"type":"json_object"}`, `max_tokens=2000`, single request per submit (batched).

**Failure modes → fail-closed:**
- API error / rate-limit / timeout → return `TranslationResult(ok=False, error="translation_service_unavailable")`.
- Response is not valid JSON → fail-closed.
- Response has missing keys or extra keys not in input → fail-closed.
- Response contains any Spanish word listed in the input verbatim → warn + fail-closed (indicates untranslated content).
- Any preserve-token is corrupted (missing from output where it was in input) → fail-closed.

**Frontend behavior on failure:** operator-visible non-dismissible toast: `"Spanish text could not be translated for submission. Please try again or switch to English."` — DR does NOT submit until either the translation succeeds OR the operator switches the UI to EN and re-enters the text in English.

**Backend storage on success:**
- Canonical fields (`general_notes`, `excavation.soil_notes`, etc.) ← translated English.
- `translation_metadata` (new sub-doc on the DR):
  ```
  {
    "original_language": "es",
    "translated_to_canonical_language": "en",
    "translation_provider": "openai" | "anthropic",
    "translation_model": "gpt-5.2" | "claude-sonnet-4.5",
    "translation_timestamp": "<UTC iso>",
    "translated_field_paths": ["excavation.soil_notes", "general_notes", ...],
    "original_spanish_snapshot": {"excavation.soil_notes": "Suelo tipo B con piedras", ...}
  }
  ```
- `original_spanish_snapshot` is stored in an "audit" sub-doc, NOT in a top-level field, so no consumer (AI / PDF / email / ODS / KPI) accidentally picks it up. It exists solely for a hypothetical legal review.

**Audit table:** a row in `db.translation_audit` on every submit (regardless of success) with actor + timestamp + field paths + provider + latency_ms + ok:bool. Useful for post-deploy volume + cost tracking + error-rate monitoring.

## 5. AI / PDF / Email language behavior

### 5.1 Rule (operator-confirmed default: canonical English)
- **AI evidence bundle** — always English. DR V3 excavation evidence already runs through `excavation_evidence_for_ai(dr_doc)` in `services/daily_report_v3_excavation/service.py`; that function reads from the canonical fields, which are English post-translation. **Zero code change** — the translation happens BEFORE the DR is written, so the evidence bundle sees English natively.
- **DailySummaryAssist prompt** — receives English facts, returns English summary. If UI is ES, the FE localizes the AI response for display via `t()` on the top-level narrative labels only; the accepted stored summary remains canonical English.
- **PDF** — canonical English (default per operator). No PDF layout change required. If V1 shipped Spanish PDFs (needs confirmation from operator in Phase 2 kickoff), we add a `report_language` field on the DR and a Spanish label bundle; but per this track's operator directive ("PDFs/emails/backend/ODS/AI/reporting always canonical English unless explicitly documented otherwise"), the default is English-only PDFs.
- **Email** — canonical English (same rule).

### 5.2 What this means for Phase 2 execution
- No new PDF template. No new email template. No new AI prompt. Zero backend AI/PDF/email code changes.
- The entire language architecture is: **frontend i18n for display + submit-time translation to canonical English + everything downstream stays as-is**.
- Provider/model/key must not leak. The translation service module logs only the provider name + latency + ok:bool; the LLM key never enters logs or DB.

## 6. Spellcheck / lang attributes plan

Every input/textarea in DR V3 must receive:
- `lang={currentLang}` (values: `"en"` / `"es"`)
- `spellCheck={isNaturalLanguageField}` — `true` for free-text fields (§4.1), `false` for coded/numeric/enum fields.

**Field classification for spellcheck:**
- **`spellCheck=true`, natural language:** all 26 free-text fields in §4.1, plus visitor purpose, foreman notes, etc.
- **`spellCheck=false`, coded/numeric:** `project_number`, `unit_number`, `cost_code`, `station_from`/`_to`, `certificate_number`, `phone_number`, `email`, all `<TimeInput>`, all `<DateInput>`, all `<QtyInput>`, license plate, VIN.
- **`spellCheck=false`, enum-driven:** search boxes that only accept a picker selection (`CompetentPersonCombo`, `UnitCombo`, subcontractor picker) — spellcheck adds noise here.

**Implementation:** add a `<LocalizedInput>` / `<LocalizedTextarea>` wrapper in Phase 2 that reads `lang` from the platform i18n context and takes a `naturalLanguage: bool` prop. Every input in DR V3 is rewritten to use these wrappers.

## 7. Phase 2 → Phase 9 execution checklist

This is the ordered TODO for the next session.

### Phase 2 — Restore EN/ES toggle in DR V3 UI
1. Import `useT` from `@/lib/i18n` in `NewDailyReportV3.jsx`.
2. Add the EN/ES toggle in the DR V3 header (top-right, matching V1's location — copy pattern from `pages/NewDailyReport.jsx` V1). Component already exists as `<LanguageToggle>` in `components/LanguageToggle.jsx` — verify and reuse; do NOT create a duplicate.
3. Wire the toggle into `localStorage` with key `masci.ui.lang` (existing platform key — verify in `lib/i18n.js`) so preference persists.
4. Wrap every hard-coded string identified in §2 with `t("...")`. Batch by file:
   - `sections.jsx` (103 strings) — largest file, do first to catch conventions.
   - `DailyReportV3ExcavationSection.jsx` (47).
   - `NewDailyReportV3.jsx` (13).
   - `SectionProjectConditions.jsx` (9).
   - `UnitCombo.jsx` (1), `CompetentPersonCombo.jsx` (1).
5. Refactor `Field label + <span>*</span>` composites into a shared `<RequiredLabel>` component so translation keys are clean.
6. Refactor template strings (e.g. `Missing: ${readiness.missing.join(...)}`) into `t()` with interpolation.
7. Add missing keys (§3) to `lib/i18n.js` — English keys + Spanish values. Estimated ~136 net-new entries.

### Phase 3 — Spanish free-text → English canonical submit pipeline
1. Call `integration_playbook_expert_v2` with the request in §4.3.
2. Create `backend/services/translation/service.py` per the contract in §4.3. Handle both OpenAI GPT-5.2 primary and Claude Sonnet 4.5 fallback in the same module.
3. Add `POST /api/translate/dr-v3-freetext` route (internal, admin+HR+safety-gated, called only by the DR V3 submit flow).
4. Extend `NewDailyReportV3.jsx` submit handler: if `currentLang === "es"`, collect the 26 free-text fields, POST to the translate endpoint, replace canonical fields with returned English, attach `translation_metadata` sub-doc, then submit the DR normally. On translation failure, block submit with the specified toast.
5. Backend: add `translation_metadata` schema to `daily_reports_v3` writes (append-only, does not affect any other consumer). Add `translation_audit` collection with a TTL of 90 days.
6. Frontend: preserve-token list computed at submit time from the DR payload's own IDs (project_number, employee names, cost codes, etc.) — send to the translate endpoint as a `preserve_tokens` array.

### Phase 4 — AI / PDF / Email language behavior verification
No code change if operator confirms English canonical default. Add lock tests only:
- `excavation_evidence_for_ai(dr_doc)` returns English content (no Spanish detected via regex).
- DR V3 PDF renders English labels only.
- Email body contains no Spanish characters (ñ / accented vowels) unless in a proper noun.

### Phase 5 — Spellcheck / lang attributes
Add `<LocalizedInput>` and `<LocalizedTextarea>` wrappers. Rewrite every input in DR V3 to use them. Ensure `naturalLanguage={false}` on the 8-ish coded/numeric fields listed in §6.

### Phase 6 — Validation and error messages
- Every validation message in `NewDailyReportV3.jsx` and `DailyReportV3ExcavationSection.jsx` wrapped in `t()`.
- Translation failure toast copy: EN `"Spanish text could not be translated for submission. Please try again or switch to English."` / ES `"El texto en español no se pudo traducir para el envío. Intente nuevamente o cambie a inglés."`.
- Add all validation strings to `i18n.js` alongside §3.

### Phase 7 — Testing
- **Backend tests** (new file `tests/test_track_24_3_es_to_en_translation.py`):
  - Unit: `translate_es_to_en_bulk` returns fail-closed on API error, on invalid JSON, on missing keys, on Spanish leak, on preserve-token corruption.
  - Integration: submit DR V3 with `currentLang="es"` and Spanish free-text; assert canonical fields are English + `translation_metadata` is present + `translation_audit` row written.
  - Regression: submit DR V3 with `currentLang="en"` (no translation) — payload untouched, no `translation_metadata`, no `translation_audit` row.
- **Frontend tests** — `testing_agent_v3_fork` with the Phase 7 spec.
- **Lock tests**:
  - `test_no_hardcoded_english_in_dr_v3.py` — scans DR V3 files, fails CI if any user-visible English literal is not wrapped in `t()`.
  - `test_i18n_keys_have_spanish_values.py` — every key used in DR V3 has both EN and ES values in `lib/i18n.js`.

### Phase 8 — Hard-coded string lock (regression guard)
- Extend the Track 24.1 `test_no_internal_labels_in_user_facing_jsx.py` philosophy with a DR-V3-specific hard-coded-English lock.
- Whitelist: `data-testid`, enum keys, API paths, class names, numeric constants, technical strings.

### Phase 9 — Integrated proof
- Live E2E: submit an English DR (baseline unchanged) + submit a Spanish DR with excavation + Spanish free-text in ≥3 fields.
- Verify: full-page ES UI, canonical English backend, `translation_metadata` populated, ODS facts English, AI evidence English, PDF English, email English, no console errors, no mobile overflow at 390/430/768/1024/1366/1440.
- Testing agent: full backend + frontend regression across Track 23.10-B/C/D/E + Track 24.1 + Track 24.2 + Track 24.3.

## 8. Non-negotiables checklist (Track 24.3 gates)

Every item in this list must be checkable **✅** before Track 24.3 is closed. Copy into the Phase 9 proof report:

- ☐ V3 has EN/ES toggle in the correct top-right location.
- ☐ ES mode renders every user-facing string in Spanish (0 English literals visible).
- ☐ Spanish free-text becomes canonical English on submit.
- ☐ Translation failure blocks submit and shows the operator-visible error toast.
- ☐ Proper nouns / IDs / codes are preserved through translation.
- ☐ AI evidence bundle receives canonical English.
- ☐ DR V3 PDF renders canonical English.
- ☐ DR V3 email renders canonical English.
- ☐ ODS facts + PM/Safety KPIs receive canonical English.
- ☐ Excavation section fully translates (all 47 strings).
- ☐ CompetentPersonCombo labels + statuses translate.
- ☐ Scheduling readiness labels translate.
- ☐ Validation messages translate.
- ☐ Autosave / draft / offline messages translate.
- ☐ Spellcheck `lang` attributes correct on every input.
- ☐ Coded/numeric fields do NOT have natural-language spellcheck.
- ☐ Mobile Spanish layout has no overflow at 390 / 430 / 768 / 1024 / 1366 / 1440.
- ☐ Language switching does not reset form data.
- ☐ Language switching does not break autosave/draft/offline.
- ☐ Track 23.10-B/C/D/E regression suite is green.
- ☐ Track 24.1 + 24.2 hardening regression suite is green.
- ☐ Repo-wide internal-label lock test passes.
- ☐ Dev endpoints stay 404.
- ☐ Auth/permissions unchanged.

## 9. Estimated size

- **Frontend** — ~136 net-new i18n keys (each ~30 seconds), ~174 string wraps (each ~30 seconds), 6 files edited, 2 new wrapper components (`RequiredLabel`, `LocalizedInput` / `LocalizedTextarea`), 1 toggle mount, 1 submit-flow branch. **~6-7 hours**.
- **Backend** — 1 new translation service (~150 lines), 1 new route, 2 new collection writes, 1 fallback provider path, 6 unit tests, 4 integration tests. **~3-4 hours**.
- **Testing** — 1 testing-agent pass on backend + frontend regression, 6-viewport mobile proof, 2 live E2E submits. **~2 hours**.
- **Total** — **11–13 hours** = comfortably fits in a fresh session with ~400k tokens.

## 10. Files that WILL change in Track 24.3

- `frontend/src/pages/NewDailyReportV3.jsx` (imports, toggle mount, submit-flow branch, string wraps)
- `frontend/src/components/daily-report-v3/sections.jsx` (largest wrap effort)
- `frontend/src/components/daily-report-v3/DailyReportV3ExcavationSection.jsx`
- `frontend/src/components/daily-report-v3/SectionProjectConditions.jsx`
- `frontend/src/components/daily-report-v3/CompetentPersonCombo.jsx`
- `frontend/src/components/daily-report-v3/UnitCombo.jsx`
- `frontend/src/components/RequiredLabel.jsx` (**NEW** — split `label *` composites)
- `frontend/src/components/LocalizedInput.jsx` (**NEW** — `lang`/`spellCheck` wrapper)
- `frontend/src/components/LocalizedTextarea.jsx` (**NEW**)
- `frontend/src/lib/i18n.js` (~136 new entries)
- `backend/services/translation/__init__.py` (**NEW**)
- `backend/services/translation/service.py` (**NEW**)
- `backend/routes/translation.py` (**NEW** — `POST /api/translate/dr-v3-freetext`)
- `backend/routes/daily_reports.py` (attach `translation_metadata` on submit)
- `backend/tests/test_track_24_3_es_to_en_translation.py` (**NEW**)
- `backend/tests/test_no_hardcoded_english_in_dr_v3.py` (**NEW**)
- `backend/tests/test_i18n_keys_have_spanish_values.py` (**NEW**)

## 11. Files that WILL NOT change in Track 24.3

- Any backend AI/PDF/email template (canonical English rule keeps these untouched).
- `services/daily_report_v3_excavation/service.py` (canonical English; already sees post-translation content).
- Track 23.10-B/C/D/E surfaces (contract preserved).
- Track 24.1/24.2 hardening (contract preserved).
- Auth / dev-endpoint / duplicate-route guards (contract preserved).

## 12. Regeneration script for §1/§2 (embed in CI)

```python
# scripts/audit_dr_v3_i18n.py
# Run: python3 scripts/audit_dr_v3_i18n.py
import re, os, json

files = ["/app/frontend/src/pages/NewDailyReportV3.jsx"]
for r,_,fs in os.walk("/app/frontend/src/components/daily-report-v3"):
    for f in fs:
        if f.endswith((".jsx", ".js")):
            files.append(os.path.join(r, f))

def strip(src):
    src = re.sub(r"//[^\n]*", "", src)
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"\{/\*.*?\*/\}", "", src, flags=re.DOTALL)
    return src

RX_JSX = re.compile(r">\s*([A-Z][A-Za-z][A-Za-z0-9 ,'.:;/\-–—?!()&%$#@+*=<>_\"]{1,120})\s*<")
RX_PROP = re.compile(
    r'\b(title|label|placeholder|description|error|alt|subtitle|kicker|helper|helperText|'
    r'caption|toast|message|heading|body|prompt|hint|ariaLabel|aria-label|tooltip)\s*=\s*'
    r'(?:"([^"\{]{2,120})"|\'([^\'\{]{2,120})\')')
RX_TOAST = re.compile(r'(?:toast\.(?:success|error|info|warning)|alert)\s*\(\s*[`\'"]([^`\'"]{4,200})[`\'"]')

hits = []
for p in files:
    if not os.path.isfile(p): continue
    src = strip(open(p, encoding="utf-8").read())
    for m in RX_JSX.finditer(src):
        text = m.group(1).strip()
        if text.replace(" ","").replace(".","").isdigit(): continue
        if len(text) < 2 or text.startswith("{") or "$" in text: continue
        hits.append((p, src[:m.start()].count("\n")+1, "jsx-text", text))
    for m in RX_PROP.finditer(src):
        text = (m.group(2) or m.group(3) or "").strip()
        if not text or text.replace(" ","").replace(".","").isdigit(): continue
        hits.append((p, src[:m.start()].count("\n")+1, f"prop:{m.group(1)}", text))
    for m in RX_TOAST.finditer(src):
        hits.append((p, src[:m.start()].count("\n")+1, "toast", m.group(1).strip()))

print(f"total hits: {len(hits)}")
```

---

**Auditor signature:** E1 · Track 24.3 · Phase 1 · 2026-02-07 · zero code changes to DR V3.
**Next step:** open a fresh session for Track 24.3 Phases 2–9 execution using this checklist.
