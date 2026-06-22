# TRACK 15.62 · Narrative Recovery (R-UX-NARRATIVE) — design contract for Session B

## Session A scope

Session A established the **backend contract** the Session B frontend will write into:

- New optional field `narrative_sections: Dict[str, str]` on `DailyReportCreate` (six keys).
- `lib/daily_report_rollup.py.narrative_health` aggregates `with_narrative_sections` so the dashboards measure adoption.
- `pdf_render._render_narrative_sections(sections)` already renders the six sections in the Daily Report PDF (proven by the Session A verification harness).
- `GET /api/admin/daily-report-health` already exposes `narrative_sections_completion_pct` so the operator can watch the lift in real time.

## Session B contract for the frontend redesign

The frontend `NarrativeWorkflow` component must write into the following exact schema:

```jsonc
narrative_sections: {
  work_completed:      "free-text · what was accomplished today",
  delays:              "free-text · what slowed progress",
  inspections:         "free-text · what tests/inspections occurred",
  materials_received:  "free-text · what arrived (deliveries)",
  follow_ups:          "free-text · what needs attention",
  tomorrow_plan:       "free-text · what is planned for tomorrow"
}
```

All six keys are optional. Empty strings are filtered out by both the aggregator and the PDF render.

## UX contract

| Behaviour | Requirement |
|---|---|
| Operator sees six guided prompts (NOT a free-text-only field) | yes |
| Each prompt is a short label + textarea | yes |
| Prompts are visible WITHOUT requiring the operator to add rows or open a wizard | yes |
| Operator can leave individual prompts blank | yes |
| Submit gate does NOT require any of the six fields | yes — by directive |
| Header completeness pill (R-UX-PROMPT) lights green when ≥ 3 of 6 sections are non-empty | yes |
| Photos may carry per-photo captions (R-PHOTO-CAPS) | yes — separate optional `photo_captions[]` already on schema |
| `activities[]` row UI remains available for operators who prefer the table mode | yes — preserve as collapsible / secondary tab |
| Existing `general_notes` field hidden when `narrative_sections` is in use (avoid two parallel narrative surfaces post-launch) | yes — but legacy display preserved on `ViewDailyReport` so historical reports keep showing `general_notes` |

## Six Pillars on the design

Powerful 9 · Simple 10 · Beautiful 10 · Trusted 9 · Proven (deferred to Session B) · Deployable 9 → projected **56/60** when Session B lands and a 14-day adoption window is measured.

## Status

✅ **Backend contract complete and verified.**
⏸ Frontend implementation deferred to Session B per the architecture approved on 2026-06-22.

Until Session B ships, this is the canonical contract any FE work must obey.
