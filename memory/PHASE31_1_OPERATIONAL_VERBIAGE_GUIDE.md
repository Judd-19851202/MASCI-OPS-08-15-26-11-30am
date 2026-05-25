# PHASE 31.1 · Operational Verbiage Guide

_iter437 · 2026-05-25_

## Why this guide exists

Phase 31.1 uses operational language ONLY. The spec banned a list of
common SaaS / consumer-app terms because they signal "account
system" or "surveillance" to crews. This file is the canonical
allow / ban list that every future iteration touching crew memory
must respect.

## Allowed vocabulary

- **crew setup** · **saved setup** · **previous setup** · **last setup**
- **saved on this device**
- **stay only on this device**
- **your crew device or personal device**
- **edit crew and equipment after loading**
- **previously submitted reports**
- **use yesterday's**
- **start blank**
- **clear saved setup**
- **name this setup**
- _Optional nicknames_ (operator-supplied): `Paving Crew A`,
  `Milling Crew`, `Utility Crew`, `Airport Night Crew`

## Banned vocabulary (NEVER ship to UI strings)

| Banned | Reason | Use instead |
|--------|--------|-------------|
| profile | implies account / identity | **crew setup** · **saved setup** |
| template | implies admin-managed library | **previous setup** · **last setup** |
| cache | implies "we'll auto-fill silently" | **saved on this device** |
| autofill | violates "never silent" doctrine | **load yesterday's setup** |
| synced | implies cross-device | (silence — Phase 31.1 has no sync) |
| account setup | implies registration | **crew setup** |
| workforce profile | surveillance language | (delete entirely) |
| browser memory | technical jargon | **saved on this device** |

## Tone rules

1. **Operational, not technical.** Talk like the foreman in the
   trailer. Never reference IndexedDB, localStorage, schema versions,
   TTLs, or storage backends in user-visible strings.
2. **Calm, not urgent.** No exclamation points, no red colors,
   no "WARNING" or "IMPORTANT" prefixes. Amber chrome with
   `border-amber-300 bg-amber-50` is the entire chrome budget.
3. **Bilingual.** Every new EN string ships with its ES translation
   in `lib/i18n.js`. The ES translation also respects the banned-word
   list (e.g. `cache` → `caché` is also banned · use `guardado en
   este dispositivo`).
4. **Decision-supportive.** The microcopy must always tell the
   operator what each button does. Never trick them into a destructive
   action with a vague label.
5. **Anti-marketing.** No "Smart Memory!", "AI-powered crew suggestion",
   "Workforce intelligence". Just plain operational text.

## Audit pass (iter437)

Every Phase 31.1 user-facing string was scanned for the banned list:

| String | Banned word present? |
|--------|----------------------|
| "Use yesterday's crew and equipment setup from this device?" | ❌ clean |
| "Saved setups stay only on this device." | ❌ clean |
| "Use this option only if this is your crew device or personal device." | ❌ clean |
| "You can edit crew and equipment after loading." | ❌ clean |
| "Starting blank will not erase previously submitted reports." | ❌ clean |
| "Use Setup" / "Start Blank" / "Clear Saved Setup" | ❌ clean |
| "Name this setup" / "Optional · name this setup" / "e.g. Paving Crew A" | ❌ clean |
| "Save name" / "saved" / "today" / "yesterday" / "days ago" | ❌ clean |
| "Crew setup loaded · edit anything as needed." | ❌ clean |
| "Saved setup cleared from this device." | ❌ clean |

Result: 100% compliant. No banned-word leakage in any iter437 string.

## Discipline for future contributors

When adding ANY new string related to crew memory:
1. Run a grep for the 8 banned words: `profile / template / cache /
   autofill / synced / account / workforce / browser memory`.
2. If any match, rewrite the string before merge.
3. Add an entry to this file's audit table.
4. Add the EN → ES pair to `lib/i18n.js`.

## Bilingual spot check

| EN | ES |
|----|----|
| Use yesterday's crew and equipment setup from this device? | ¿Usar la configuración de cuadrilla y equipo de ayer de este dispositivo? |
| Saved setups stay only on this device. | Las configuraciones guardadas permanecen solo en este dispositivo. |
| Use Setup | Usar configuración |
| Start Blank | Empezar en blanco |
| Clear Saved Setup | Borrar configuración guardada |
| Name this setup | Nombrar esta configuración |
| crew member / crew members | miembro de cuadrilla / miembros de cuadrilla |
| equipment item / equipment items | equipo / equipos |
| saved yesterday | guardada ayer |

None of the ES strings introduce banned terms in either language.
