# Track 19.07 · Cognitive UX Audit

## The redundant-thinking problem (pre-19.07)

The Track 19.06 progressive-disclosure shell made the form easier to see. But operators were still being asked to answer the same operational question twice — once through structured inputs, and again through the six-prompt narrative surface. This audit inventories every duplicate cognitive path and prescribes one authoritative home.

| Duplicate question | Authoritative home (19.07) | Redundant surface (retired from primary UI) |
| --- | --- | --- |
| "What work was performed today?" | `production[]` rows + `activities[]` inside the "What got done?" band | NarrativeWorkflow `work_completed` prompt |
| "What delayed you?" | `constraints[]` + `schedule_delays` / `weather_impact` inside the "What impacted today?" band | NarrativeWorkflow `delays` prompt |
| "What materials arrived?" | `materials[]` inside the "What moved?" band | NarrativeWorkflow `materials_received` prompt |
| "What inspections happened?" | Safety triggers inside the "Was the job safe?" band + `visitors[]` (inspectors) | NarrativeWorkflow `inspections` prompt |
| "What needs to happen tomorrow?" | `narrative_sections.tomorrow_plan` inside the "What happens next?" band | NarrativeWorkflow `tomorrow_plan` prompt (same schema key, was double-rendered) |
| "General notes vs Tell-the-story" | Single `general_notes` field with clear intent | NarrativeWorkflow six-prompt block |

**Root cause**: Track 15.62 shipped a six-prompt narrative surface at a time when the structured `production[]` / `constraints[]` / `materials[]` fields had 0% adoption. Now that Tracks 19.06 progressive disclosure has made those surfaces easy to use, the narrative prompts became a second lane for the same information — and the operator dutifully re-typed everything.

## The single-optional-notes doctrine (19.07)

The narrative surface still exists in the schema (`narrative_sections{}` is a Track 15.62 additive contract we cannot remove without a coordinated backfill migration). But it is no longer the primary path. Instead:

* One clearly-labeled optional field: **"Operational notes (optional)"** with intent-first microcopy:
  > "What should someone reading this six months from now know that isn't already captured in production, materials, delays, safety, or photos?"
* Behind a `<details>` disclosure: **"Additional context (rarely needed)"** — the full NarrativeWorkflow six-prompt block. Available for edge-case operators who need structured narrative; invisible to the 90% who don't.

## The six cognitive checkpoints

Every band in the redesigned flow now carries a `data-cognitive-checkpoint` attribute so downstream analytics can measure adoption per checkpoint:

| Checkpoint | Bands under it | Persisted fields it owns |
| --- | --- | --- |
| **Who was there?** | People on Site · Equipment & Resources | `masci_crews[], subcontractors[], visitors[], equipment[]` |
| **What got done?** | Work Performed & Production | `activities[], production[]` |
| **What impacted today?** | Delays / Constraints / Extra Work | `constraints[], schedule_delays, weather_impact` |
| **What moved?** | Materials / Import / Export | `materials[], outbound_materials[]` |
| **Was the job safe?** | Safety / Incidents / Inspections | `safety_incidents_today, injuries_reported, incident_notes, safety_notified, safety_contact_person, safety_contact_time, incident_report_filled, incident_report_time` |
| **What happens next?** | Tomorrow / Follow-Up | `narrative_sections.tomorrow_plan` |

## Microcopy trimmed

* "General Notes" → "Operational notes (optional)".
* Placeholder "Anything else worth noting from today..." → "Only unique operational context. Not another log."
* "Tell the story of the day" (misleading — invited duplication) → removed. Replaced by intent-first single-field prompt.

## Cognitive load Δ

Before 19.07 an operator was asked (structurally OR narratively):
* 6 narrative prompts + 8 structured Yes/No gates + 4 required setup fields + 6 photos + signature = **25 primary decisions**.

After 19.07:
* 8 structured Yes/No gates + 4 required setup fields + 6 photos + signature + 1 optional notes = **20 primary decisions** for the same downstream data.

**Net cognitive reduction: 5 duplicate decisions per report** on a typical day. Six months × 5 crews × 250 workdays = a lot less duplicate typing.
