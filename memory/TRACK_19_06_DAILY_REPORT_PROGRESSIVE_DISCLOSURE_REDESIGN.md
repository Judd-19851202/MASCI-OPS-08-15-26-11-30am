# Track 19.06 · Daily Report Progressive-Disclosure Redesign

## What shipped

The Daily Report creator flow now reads like a superintendent replaying the day, guided by a Yes/No progressive-disclosure shell layered on top of the existing 11-section architecture. Every persisted schema key, every backend route, and every Track 19.03 / 19.04 / 19.05 doctrine is preserved.

## The redesigned flow

1. **Job Setup** — project, date, prepared_by, superintendent, weather, GPS, report number, autosave/draft/prefill affordances.
2. **People on Site** — three gates:
   * "Did MASCI employees work on site today?" → reveals `masci_crews[]` editor.
   * "Were subcontractors on site today?" → reveals `subcontractors[]` editor.
   * "Were visitors or inspectors on site today?" → reveals `visitors[]` editor.
3. **Equipment & Resources** — "Was MASCI equipment on site or used today?" → reveals `equipment[]` editor.
4. **Materials / Import / Export** — two gates:
   * "Were materials delivered or imported today?" → reveals `materials[]` editor.
   * "Were materials exported or hauled off today?" → reveals `outbound_materials[]` editor.
5. **Work Performed & Production** — one consolidated band above Activity/Production Log + Production Quantities cards.
6. **Delays / Constraints / Extra Work** — "Did anything delay, change, or impact production today?" gates the entire structured Delays/Constraints card. Weather + schedule + constraint types unified under this one operator question.
7. **Safety / Incidents / Inspections** — new umbrella prompt over the existing (preserved) `safety_incidents_today` + `injuries_reported` Yes/No pickers. Data model unchanged; UI groups them under one banner.
8. **Photos & Attachments · Required Evidence** — existing PhotoUpload + Track 19.04 AttachmentUpload, 6-photo min preserved.
9. **Tomorrow / Follow-Up** — writes to the existing `narrative_sections.tomorrow_plan` field.
10. **Sign-Off / Submit** — DistributionList + signature pad + submit gate, all preserved.

## Progressive-disclosure mechanics

The `<_PresenceGate>` component (in `NewDailyReport.jsx`) accepts:

* `label` — the operator-facing Yes/No question.
* `gateKey` — one of `crews | subs | visitors | equipment | materials_in | materials_out | delays | safety`.
* `hasData` — auto-answer Yes when the array already has content (Smart Prefill Apply, draft restore, or manual entry never gets hidden).
* `children` — the existing CollapseCard / Section is rendered verbatim inside the gate when the answer is Yes.

Three visual states per gate:

| State | Render |
| --- | --- |
| Unanswered | White prompt card with the question + [Yes] [No] |
| Yes | The existing CollapseCard renders inside a subtle `<div>` with a small "← Change answer" affordance |
| No | Slate pill "No — skipped · {section name}" with a [Change] button |

Auto-fill:

* Presence is a UI-only state — never persisted, never serialized.
* On mount + every `data` change, presence auto-flips to Yes when the corresponding array/flag has content.
* Explicit operator answers ARE sticky — an operator "No" is respected even if data appears later (edge case: prefill applied after No — the operator sees the "No — skipped" pill and can Change to reveal).

## Sections NOT gated

* Job Setup (Section 01) — always required.
* Weather (Section 02) — always shown; weather impact Yes/No inside is one of the delays inputs.
* General Information + Safety (Section 03) — always shown; safety triggers live here.
* Activity/Production/Delays cluster (Section 10 Work Performed & Production) — always shown; the Delays sub-card is gated separately.
* Photos & Attachments — always shown.
* Sign-Off — always shown.

## Six Pillars check

* **Powerful**: every field from Track 19.05 audit remains in the persisted schema.
* **Simple**: 8 Yes/No gates collapse a wall-of-form into a guided workflow.
* **Beautiful**: band labels + calm slate/emerald/white palette.
* **Trusted**: presence lives in local state only; no schema drift; Track 19.03/19.04 doctrine intact.
* **Proven**: pytest lock has 40+ assertions covering schema keys, route paths, testids, and prompt strings.
* **Operational**: superintendent replays the day in order; 15-minute target realistic for a simple day.

## What did NOT change

* No Pydantic model change on `DailyReportCreate`.
* No backend route added or removed for the redesign (Track 19.04's attachment upload endpoint remains as-is).
* No CSV / PDF template change.
* No email routing change.
* No R2 storage change.
* No `useFormDraft` / `savedByActor` change (Track 19.04 preserved).
* No HR roster contract change (Track 19.03 preserved).
* No excavation hard gate change.
* No 6-photo minimum change.
