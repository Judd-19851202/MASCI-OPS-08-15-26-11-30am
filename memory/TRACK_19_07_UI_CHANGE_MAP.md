# Track 19.07 · UI Change Map

Every file touched. Every removal, every addition, every reason.

## Files touched

Only one file: `/app/frontend/src/pages/NewDailyReport.jsx`.

## Removals (UI surface only — schema untouched)

| Removed from primary UI | Preserved in | Reason |
| --- | --- | --- |
| "Tell the story of the day" section header | — | Was inviting duplication |
| Always-visible NarrativeWorkflow six-prompt block | Behind `<details data-testid="dr-narrative-additional-context">` | Duplicated production / materials / delays / safety inputs |
| "General Notes" label + placeholder "Anything else worth noting from today…" | — (renamed) | Vague intent invited redundancy |

## Additions

| Added | Purpose |
| --- | --- |
| Label "Operational notes (optional)" | Clear intent — unique context only, not another log |
| Helper text "What should someone reading this six months from now know that isn't already captured…" | Anchors operator to the 6-month archaeology test |
| Placeholder "Only unique operational context. Not another log." | Explicit anti-duplication cue |
| `<details data-testid="dr-narrative-additional-context">` collapsed disclosure with summary "Additional context (rarely needed)" | Preserves the six-prompt NarrativeWorkflow for edge-case operators; keeps `narrative_sections{}` schema binding intact |
| `data-cognitive-checkpoint="who-was-there"` on `band-people-on-site` + `band-equipment-resources` | Analytics + navigation hint |
| `data-cognitive-checkpoint="what-got-done"` on `band-work-performed` | " |
| `data-cognitive-checkpoint="what-impacted-today"` on `band-delays-constraints` | " |
| `data-cognitive-checkpoint="what-moved"` on `band-materials` | " |
| `data-cognitive-checkpoint="was-the-job-safe"` on `band-safety-incidents` | " |
| `data-cognitive-checkpoint="what-happens-next"` on `band-tomorrow` | " |
| Prefix label text upgrades: "Who was there? · People on Site", "What got done? · Work Performed & Production", "What impacted today? · Delays / Constraints / Extra Work", "What moved? · Materials / Import / Export", "Was the job safe? · Safety / Incidents / Inspections", "What happens next? · Tomorrow / Follow-Up" | Cognitive checkpoint framing per Track 19.07 spec |

## Zero changes to

* `dailyReportSchema.js` — `photo_min: 6` and every default preserved.
* `AttachmentUpload.jsx`, `PhotoUpload.jsx`, `EmployeeCombo.jsx`, `trench/EmployeePicker.jsx`.
* `lib/resiliency/*` (autosave, actor gate, draft store).
* `lib/hrRoster.js` (canonical HR roster contract).
* `lib/crewMemory.js` (device-local snapshot).
* Backend routes, models, PDF template, CSV export, email routing, trust-spine correlation.

## Test coverage

`tests/test_track_19_07_daily_report_cognitive_ux.py`:
* 5 report existence checks.
* Schema key roll-call (36 keys).
* Backend route roll-call.
* Cognitive-checkpoint attribute presence (6 checkpoints).
* Cognitive-checkpoint label presence (6 labels).
* NarrativeWorkflow-collapsed disclosure gate.
* "Tell the story of the day" removal verification.
* "Operational notes (optional)" + "isn't already captured" microcopy.
* Track 19.06 progressive-disclosure gates all still present.
* Photo minimum, Smart Prefill, autosave, HR roster, attachments, submit button — all intact.
