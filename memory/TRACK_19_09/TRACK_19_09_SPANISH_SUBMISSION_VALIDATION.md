# Track 19.09 · Spanish Submission Validation

Verifies the platform's Spanish-submission contract remains intact after Track 19.09.

## Contract (unchanged since Track 14.0-S1)

1. English is the **canonical operational language**. All persisted records, PDFs, emails, PM/Admin/Safety portal reads, and historical exports are in English.
2. Spanish crews may switch the UI to Spanish via the `<LangToggle>` control (`{ lang, setLang }` from `@/lib/i18n`).
3. In Spanish mode, every UI string is served from the `ES` dictionary. Missing keys silently fall back to the English literal — an audit test guards against this.
4. In Spanish mode, crew members may type ANY narrative / comment / description / defect note freely in Spanish. No client-side rejection.
5. On submit, `translateUserInput(payload, "es")` translates the Spanish free-text fields to English via the platform's OpenAI-backed translator (`frontend/src/lib/translateOnSubmit.js`).
6. The bilingual sidecar (`persistBilingualSidecar`, Track 14.0-S1 Amendment A) preserves the original Spanish text for audit.
7. Downstream: PM Portal, Admin Portal, Safety Portal, Emails, PDFs, Reports, Historical Records — ALL remain in English.

## Verification

| Aspect | Verification method | Result |
| --- | --- | --- |
| No new EN-only strings introduced | Parametric test `test_spanish_translation_exists[…]` × 35 keys | ✅ |
| Camera gate operator flow in Spanish | Test asserts ES translation present for every visible string | ✅ |
| Downstream commitment panel in Spanish | Same | ✅ |
| Retro-filled 19.06 amendment strings | Same | ✅ |
| Retro-filled 19.07 cognitive-checkpoint strings | Same | ✅ |
| `translateUserInput` still wired on Equipment Pre-Op submit | Existing code path preserved (lines 532-538 of `NewEquipmentInspection.jsx`) | ✅ |
| `translateUserInput` still wired on DVIR submit | Existing code path preserved (unmodified in 19.09) | ✅ |
| Bilingual sidecar (`persistBilingualSidecar`) still fires | Existing code path preserved (lines 540-550 of `NewEquipmentInspection.jsx`) | ✅ |
| Backend / PM / Safety / Admin remain English | Zero backend touched in 19.09 | ✅ |

## Camera-gate Spanish walkthrough (5:30 AM foreman scenario)

Foreman opens `/equipment/new` on iPad, taps ES toggle:

1. Sees "Verificación de Seguridad del Sistema de Cámaras" (band header).
2. Reads "¿Este equipo tiene un sistema de cámaras?" (Sí / No / No estoy seguro).
3. Taps "Sí".
4. Follow-up appears: "¿Las cámaras delantera e interior están libres y despejadas de obstrucciones?" (Sí — despejadas / No — hay obstrucción).
5. If they tap "No — hay obstrucción" they see:
    * Header: "Crítico de seguridad · Envío bloqueado"
    * Body: "Despeje la obstrucción antes de operar. La visibilidad de las cámaras debe estar libre y clara."
    * Textarea label: "Describa la obstrucción (opcional — para el registro del taller)"
    * Placeholder: "p. ej., lodo en el lente, carcasa rota, cinta cubriendo la cámara"
6. If they attempt Submit anyway, they see toast "Confirme si las cámaras están libres y despejadas de obstrucciones" (or the "clear obstruction" red toast).
7. Once they physically clear the lens + flip to "Sí — despejadas", submission is allowed.
8. On successful submit, they land on ThankYou which shows the Spanish downstream-commitment bullet list.

## Result

**Zero drift from the Track 14.0-S1 bilingual doctrine.** Every new UI element ships with equal citizenship in EN and ES. Backend contract untouched.
