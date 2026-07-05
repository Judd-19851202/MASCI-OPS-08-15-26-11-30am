# DR-ROI-001F-FINAL-REPAIR · Amendment · EN/ES Field Mode

## Status
🟢 **CLOSED** (2026-02-05) · integrated into the platform-native Daily
Job Report V2 without breaking anything.

## Core Rule
The crew can work in Spanish. The platform can help them in Spanish.
The **canonical submitted operational record is always English**. Every
Spanish freeform entry is stored verbatim in the append-only bilingual
audit collection, translated to English on submit via the AI Provider
Gateway, and the English canonical value is what ODS / PM / Admin /
Executive dashboards / PDF / exports consume.

## Frontend
- New library `frontend/src/lib/dailyReportV2Lang.js` — exports
  `DICTIONARY` (100+ EN/ES pairs), `DrV2LangProvider`, `useDrV2Lang`
  (React context hook returning `{lang, setLang, t(key)}`), and
  `LangToggle` (EN / ES pill toggle used in the shell header).
- Default language: **English**. Persisted per-user via
  `localStorage["dr_v2_field_lang"]`.
- The DR-V2 shell wraps the app in `<DrV2LangProvider>` and renders the
  toggle next to the report ID / save-status chip.
- Every section file (`DaySetupSection`, `CrewTimeSection`,
  `EquipmentSection`, `ActivityCardsSection`, `ConstraintChipsSection`,
  `TomorrowReadinessSection`, `SafetyQualitySection`, `PhotosSection`,
  `AISummarySection`, `SignatureSubmitSection`) + `PhotoIntelligencePanel`
  now imports `useDrV2Lang` and renders every visible label through
  `t("s0X.…")`. Constraint chips + shift options + equipment status
  options + activity status/unit options + tomorrow-readiness field
  labels all go through the dictionary.
- The Daily Operational Summary textarea + read-only body carry a
  `lang={lang}` attribute for correct spellcheck.
- Draft carries `field_language` (`"en"` or `"es"`) so autosave
  persists it server-side.

## Backend
- New task in the AI Gateway task router: `translation_es_en →
  (anthropic, claude-sonnet-4-5-20250929)` — provider-neutral, opaque
  to the UI.
- New route: `POST /api/dr-v2/reports/{report_id}/canonicalize`
  registered in `server.py`.
- Request: `{ draft: {...}, field_language: "en"|"es" }`.
- English draft → **no-op fast path** (`translation_status="not_required"`,
  translations=[], canonical_draft=draft as-is).
- Spanish draft → walks `TRANSLATABLE_PATHS` (10 well-known freeform
  fields on the draft), dispatches each string through the gateway with
  a strict system prompt ("preserve every fact, quantity, and unit
  exactly"), rewrites the canonical_draft in place with English text,
  and records every original / canonical / confidence / provider /
  timestamp entry in `dr_v2_bilingual_audit` (append-only).
- If `min_confidence < 0.7` OR any string returned a gateway_error, the
  response sets `needs_supervisor_review=true` — the caller must
  surface the supervisor-review flow before submit.

## Bilingual Audit Schema (`dr_v2_bilingual_audit` collection)
```
{
  audit_id: uuid,
  report_id: string,
  field_language: "es",
  canonical_language: "en",
  translations: [{
     field_path: "activity_cards[].notes",
     pointer: ["activity_cards", 0, "notes"],
     original_user_text: "colocamos base granular en el tramo este",
     original_user_language: "es",
     canonical_english_text: "placed granular base on the east segment",
     translation_status: "translated",
     translation_confidence: 0.92,
     translation_provider: "anthropic",
     translated_at: "2026-02-05T13:39:00Z",
     reviewed_by_user: false
  }],
  translation_status: "ok" | "needs_review" | "not_required" | "empty",
  needs_supervisor_review: bool,
  min_confidence: 0.92,
  created_at: iso,
  canonical_draft: {...},     // canonical English payload consumed by ODS
  original_draft: {...},      // exact user input for audit
}
```

## Translatable Field Paths (server-side)
- `activity_cards[].notes`
- `constraint_cards[].what_happened`
- `constraint_cards[].impact`
- `tomorrow_readiness.crew_needs`
- `tomorrow_readiness.equipment_needs`
- `tomorrow_readiness.material_needs`
- `tomorrow_readiness.decisions_needed`
- `safety.quality_notes`
- `day_setup.location_label`
- `accepted_summary` (supervisor-edited Daily Operational Summary)

## Behavior Guarantees (no drift)
- HR crew time, equipment master, safety gates, excavation / JHA / JHP
  gate, minimum-6-photo rule, PhotoUpload, SignaturePad, autosave,
  draft recovery — **unchanged** by ES mode.
- V1 Daily Report — **byte-untouched**.
- Photo Intelligence, ODS emission — **untouched**.
- PM / Admin / Executive dashboards — **untouched** and consume only
  canonical English from `canonical_draft`.
- Default PDF output — English only (bilingual PDF is a future task).
- No live emails.

## AI / Summary Rules
- When `field_language==="es"`, the supervisor-facing Daily Operational
  Summary is rendered in Spanish (the summary source narrative is
  drafted by the AI Gateway; `lang` attribute on the render div hints
  screen readers + spellcheck).
- On submit, the canonicalize endpoint canonicalizes the
  supervisor-approved narrative back to English before the record is
  finalized.
- If translation confidence < 0.7 the endpoint returns
  `needs_supervisor_review=true` — the caller must show the supervisor
  the side-by-side original/canonical view before proceeding.
- AI may not change meaning; the system prompt requires exact fact /
  quantity / unit preservation.

## Lock Envelope
`backend/tests/test_dr_roi_001f_en_es_lock.py` — 9 assertions:
1. `test_lang_library_exports_are_complete`
2. `test_dictionary_has_en_and_es_for_every_key` (≥60 EN/ES pairs)
3. `test_shell_wraps_provider_and_renders_toggle`
4. `test_default_language_is_english`
5. `test_key_sections_wire_the_lang_hook`
6. `test_canonicalize_route_registered_and_helpers_work`
7. `test_canonicalize_no_op_for_english_language`
8. `test_task_router_carries_translation_task`
9. `test_ods_only_receives_english_canonical` (audit fields present)

**Total DR-ROI-001F envelope: 32/32 assertions green** (9 EN/ES + 14
platform consistency + 9 DR-ROI-001E regression).

## Live Smoke
- `/daily-report/v2` with `localStorage.dr_v2_field_lang="es"` renders
  everything in Spanish: header ("OPERACIONES DE CAMPO MASCI · Reporte
  Diario de Obra"), Section 01 "Configuración del Día", Section 02
  "Cuadrillas MASCI en el sitio", Section 03 "Equipo en el sitio",
  Section 06 "Mañana / Seguimiento", Section 07 "Seguridad · Calidad",
  Section 08 "Fotos de campo", Section 09 "Resumen Operacional del
  Día", Section 10 "Firma + Envío". Placeholders ("Nombre completo"),
  primary CTAs ("AGREGAR MIEMBRO", "Capturar GPS", "Obtener clima"),
  and the Borrador / Sin guardar chip all translated.
- EN toggle flips everything back instantly with no reload.
- No PDF buttons anywhere on the form. No AI branding. No dark chrome.

## Rollback Recipe
```
rm backend/routes/dr_v2_canonicalize.py
rm backend/tests/test_dr_roi_001f_en_es_lock.py
git checkout HEAD~ -- backend/server.py \
                     backend/services/ai_gateway/task_router.py \
                     frontend/src/pages/daily-report-v2/**/*.jsx
rm frontend/src/lib/dailyReportV2Lang.js
rm /app/memory/DR_ROI_001F_FINAL_REPAIR_EN_ES_MODE.md
```
