# TRACK 15.62 · Dead Field Recovery (R-DEAD-FIELDS)

## Evidence (from 15.61 forensics — never re-typed; cited from `forensics.json`)

| Field | Non-empty rate in production (60-day · n=154) |
|---|---|
| `schedule_delays_notes` | **0.0 %** |
| `weather_impact_notes` | **0.0 %** |
| `linked_excavation_ids` | **0.0 %** |

These three fields are present on the form, render on the PDF (as empty rows when blank), and are never used. Their continued presence trains operators to skip-and-scroll.

## Recommendation (Session B will implement)

| Field | Session B treatment |
|---|---|
| `schedule_delays_notes` | **subsume** into the new `narrative_sections.delays` prompt — same operational intent, better UX |
| `weather_impact_notes` | **subsume** into the new `narrative_sections.delays` prompt OR (optional) keep as collapsed "More weather context" textarea behind progressive disclosure |
| `linked_excavation_ids` | **collapse behind progressive disclosure** ("Add excavation references") — keeps the surface for the rare day excavations are referenced without forcing the operator past it |

## What Session A did

- **No removal from the schema.** Both `schedule_delays_notes` and `weather_impact_notes` remain valid optional fields. Existing reports continue to render them in the PDF.
- The new `narrative_sections.delays` prompt provides the better narrative surface; Session B will favour it.
- `linked_excavation_ids` stays. Session B will hide it behind a progressive-disclosure toggle on the form.

## Six Pillars

Powerful 8 · Simple 10 · Beautiful 9 · Trusted 9 · Proven 9 · Deployable 10 → **55/60**.

## Status

✅ **Documented and rationalised. No code changes required in Session A** — the change is form-side, deferred to Session B per the approved architecture. Backend already supports both paths.
