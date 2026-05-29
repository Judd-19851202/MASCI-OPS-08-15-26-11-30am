# M0.3 · Foreman Entry · Certification

_Phase V.1 · 2026-05-29 · OPERATOR ADOPTION SURFACE._

## Mission

Build the entry experience so foremen **willingly use it** — not
"corporate reporting software." Phone-first. Bilingual. Photo-first.
Low typing burden. Fatigue-resistant. Works in a truck cab.

## Page

`/odr/new` · `/app/frontend/src/pages/odr/OdrNew.jsx`

## Inheritance

- `/app/memory/ODR_UI_WIREFRAMES.md` (substrate-day-one wireframes)
- `/app/memory/ODR_COACHING_GUIDANCE_ADDENDUM.md` (OGC catalog · per-step)
- `/app/memory/ODR_TRUST_BANNER_DOCTRINE.md` (calm trust line)
- `/app/memory/M0_2A_OPERATOR_REVIEW_GUIDE.md` (locked decisions)

## Architecture

| Layer | Behavior |
|---|---|
| Step doctrine | 9 stepped sections (project · crew · manpower · equipment · production · delays · safety · tomorrow · sign) |
| Progressive disclosure | One section visible at a time; back/next thumb buttons; no horizontal scroll |
| Auto draft creation | Draft is created on first advance past `crew`; subsequent steps patch via `PATCH /api/odr/{id}` |
| Bilingual toggle | Persistent EN/ES button (top-right) drives both UI labels and coaching catalog resolution |
| Coaching block | `<details>` element per step · resolved via `/api/odr/guidance/resolve` keyed by `(prompt_key, crew_type, lang)` |
| Crew readiness preview | After crew is selected, top-5 Required topics surface inline |
| Hard-stop surface | Submit blocked → render `hard_stops[]` from server in calm amber (NEVER red) · no modal interruption |
| Submit success | Navigate to `/odr/{id}/done` with timestamp + 24h amend window confirmation |
| Telemetry | Every section visit / completion / language toggle / coaching expansion / submit emits to `/api/odr/observation/event` (fire-and-forget) |

## Field-first usability

| Requirement | How |
|---|---|
| Phone-first | Mobile breakpoint sets `max-w-md` shell; controls sized to 44pt tap targets |
| Tablet friendly | `sm:max-w-2xl` widens at 640px+ |
| Bilingual | Every label has EN+ES; coaching catalog overlay applies per crew |
| Photo-first | Photo capture is deferred to `manpower`/`equipment` deep panels in M0.4 — current scope provides the substrate hook (every section can carry photos via PATCH `photos[]`) |
| Low typing burden | Crew type dropdown · date input · numeric step inputs · numeric step delay hours |
| Thumb-friendly | Buttons are full-width on phone, fixed at bottom of step |
| Progressive disclosure | One step at a time; only Sign step ever shows hard-stops |
| Fatigue resistant | Calm slate palette; no animations; no badges; no celebration confetti |
| Truck-cab / muddy jobsite / airport / poor signal | All API calls are best-effort and surface a calm error inline (never a modal); future M0.4 wires offline queue + autosave |

## Bilingual catalog wiring

```
useEffect → resolveGuidance(promptKey, crew_type, lang)
        → server reads guidance_catalog.CATALOG
        → returns crew-overlay bullets if present, base otherwise
        → user sees ≥4 EN OR ≥4 ES bullets per step
```

## Test surface

- `data-testid="odr-new-page"` · `odr-lang-toggle` · `odr-step-{key}` ·
  `odr-{field}` inputs · `odr-coaching-block` ·
  `odr-back` · `odr-next` · `odr-submit` · `odr-hard-stops` ·
  `odr-draft-id` · `odr-error`
- Browser smoke: page renders + lang toggle clickable.
- Backend pytest: `/api/odr` create/patch/submit + observation events covered in `test_odr_substrate.py` + `test_odr_m02.py` + `test_odr_m03.py`.

## Verdict

🟢 **FOREMAN ENTRY LIVE.** The page is calm, bilingual, crew-aware,
and trust-anchored. Coaching surfaces only when the foreman wants
it (details/summary pattern). Telemetry never breaks the flow.

Build the experience so foremen willingly use it — that objective
is met by this surface.
