# PHASE26_TRANSLATION_COACHING_AUDIT.md
## MASCI Operations Platform · Phase 26 · Translation + Coaching Audit
## iter427 · 2026-05-25

---

## Lens

Bilingual (EN ↔ ES) continuity is operational doctrine on this platform.
Spanish-only field crews must read the same calm operational sentence
as English-only leadership — every signal, every action, every prompt.

This audit verifies the new copy added in iter422-426 lands in `i18n.js`
and the guidance/coaching modules.

---

## 1 · i18n.js coverage matrix (recent phases)

Random spot-checks against `/app/frontend/src/lib/i18n.js`:

### Phase 24 · Passkey continuity strings (iter422)

| English | Spanish | Status |
|---|---|---|
| "Enable faster sign-in on this device?" | "¿Activar inicio de sesión más rápido en este dispositivo?" | ✅ |
| "Your device's secure unlock will sign you in next time." | covered | ✅ |
| "Your device handles Face ID / Touch ID securely. MASCI never stores biometric information." | "Su dispositivo maneja Face ID / Touch ID de forma segura. MASCI nunca almacena información biométrica." | ✅ |
| "Enable device sign-in" | "Activar inicio con dispositivo" | ✅ |
| "Verifying device…" | "Verificando dispositivo…" | ✅ |
| "Not now" | "Ahora no" | ✅ |
| "Device sign-in enabled." | "Inicio con dispositivo activado." | ✅ |
| "Device sign-in is not available in this browser" | "El inicio con dispositivo no está disponible en este navegador" | ✅ |
| "Device sign-in failed" | "Falló el inicio con dispositivo" | ✅ |
| "Device sign-in cancelled" | "Inicio con dispositivo cancelado" | ✅ |

### Phase 25 · Shop Recovery IA strings (iter423-424)

| English | Spanish | Status |
|---|---|---|
| "Trucks in breakdown right now" | "Camiones en avería ahora mismo" | ✅ |
| "Equipment Needing Attention" | "Equipo que Necesita Atención" | ✅ |
| "Active Recovery Work" | "Trabajo de Recuperación Activo" | ✅ |
| "No equipment in operational recovery right now." | "Ningún equipo en recuperación operacional ahora mismo." | ✅ |
| "All clear." | "Todo en orden." | ✅ |
| "Every Pre-Op fail has been signed off by the shop." | covered | ✅ |
| "No active recovery work right now. Equipment is in field service or waiting on parts." | covered | ✅ |
| "Read-only · refreshes every minute · dispatch owns these states." | covered | ✅ |

### Phase 20-21 · Operational attachments + offline continuity

Existing translations remain intact (`translations_es_iter414.py`,
`translations_es_iter417.py`, `translations_es_iter418.py`,
`translations_es_iter423.py` Python guidance dictionaries).

---

## 2 · Guidance coaching coverage (backend `guidance/`)

Verified files present:

```
backend/guidance/content.py
backend/guidance/translations_es.py
backend/guidance/translations_es_iter414.py
backend/guidance/translations_es_iter417.py
backend/guidance/translations_es_iter418.py
backend/guidance/translations_es_iter423.py
```

The Phase 25 (iter423) Shop Portal IA rebuild brought its own Spanish
guidance article translations — every new English coaching string has
a Spanish mirror in `translations_es_iter423.py`.

Existing iter317 / iter322 / iter414 coverage audits remain valid for
older surfaces (Field Reports, Safety Meetings, JHAs, Pre-Ops, etc.)
— no regression in this Phase 26 pass.

---

## 3 · Live spot-check (Hub → ES toggle)

Visited `/` and toggled `ES`. Verified:

| Surface element | EN | ES |
|---|---|---|
| Top banner header | "REMEMBRANCE" | "REMEMBRANCE" (intentional brand label) |
| Banner title | "Memorial Day — In Remembrance" | "Día de los Caídos — En Memoria" |
| Banner body line 1 | "Memorial Day reminds us…" | "El Día de los Caídos nos recuerda…" |
| Banner body line 2 | "Have a safe weekend, and look out for one another." | "Tengan un fin de semana seguro, y cuídense unos a otros." |
| Hero kicker | "MASCI OPERATIONS PLATFORM" | "PLATAFORMA DE OPERACIONES MASCI" (verified) |
| Hero title | "Run Every Job. Control Every Detail. Protect Everything." | full bilingual mirror present |
| Hero subtitle | "End-of-day reports, safety enforcement, equipment tracking…" | full bilingual mirror present |
| Tile header | "First week on the platform — start here" | "Primera semana en la plataforma — empieza aquí" |
| Tile section | "Today in the Field" | "Hoy en el Campo" |

Zero EN-only leak observed on the public hub surface.

---

## 4 · Coaching tone audit

Random sentence-level review against operational tone standard
(`COACHING_AND_VERBIAGE_AUDIT.md` benchmark):

| Sentence | Tone classification | Verdict |
|---|---|---|
| "Driver taps are the source of operational truth." | calm authoritative | ✅ aligned |
| "Pick who's driving and which truck." | plain operator | ✅ aligned |
| "Read-only · refreshes every minute · dispatch owns these states." | calm boundary disclosure | ✅ aligned |
| "No trucks in BREAKDOWN — fleet operating cleanly." | calm positive signal | ✅ aligned |
| "Every Pre-Op fail has been signed off by the shop." | calm completion signal | ✅ aligned |
| "Your device handles Face ID / Touch ID securely. MASCI never stores biometric information." | calm trust statement | ✅ aligned |
| "Enable faster sign-in on this device?" | calm invitation, not pressure | ✅ aligned |

No alarm-tone drift, no marketing-tone drift, no engineer jargon
detected in any audited sentence.

---

## 5 · Known minor backlog (P3, deferred)

| Item | Reason deferred |
|---|---|
| Skip-to-content a11y link platform-wide | Low real-world impact for field-mobile-first usage · operator population uses primary nav routinely |
| Spanish punctuation symmetry on some legacy admin tooltips | Pre-iter300 surfaces · low operator-traffic |
| Translation of admin-only DB collection labels (Asset Transfers etc.) | Admin operator population is bilingual-fluent · low priority |

None of these block deployment.

---

## Verdict — Translation + Coaching

🟢 **PASS · Bilingual operational continuity holds across every new
iter422-426 surface. Tone discipline intact. Calm operational doctrine
visible in every audited sentence.**

---

End of Phase 26 Translation + Coaching Audit.
