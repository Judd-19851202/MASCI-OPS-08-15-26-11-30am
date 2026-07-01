# Track 19.07 · Information Architecture

The redesigned Daily Report is organized around six cognitive checkpoints — the way a superintendent actually replays the day. Every persisted fact has exactly one authoritative home in the UI. No fact is asked twice.

```
JOB SETUP  (administrative — fades into background)
├── Section 01 · Report Information
├── Section 02 · Weather
└── Section 03 · General Info + safety triggers (front-loaded)

WHO WAS THERE?  (people + equipment on site)
├── Section 04 · MASCI Crews — presence gate
├── Section 05 · Subcontractors — presence gate
├── Section 06 · Visitors / Inspectors — presence gate
└── Section 07 · Equipment — presence gate

WHAT MOVED?  (logistics only)
├── Section 08 · Materials Delivered / Imported — presence gate
└── Section 09 · Outbound Materials / Hauled Off — presence gate

WHAT GOT DONE?  (completed work + structured production)
└── Section 10 · Activity / Production / Quantities

WHAT IMPACTED TODAY?  (anything affecting production)
└── Section 10 · Delays / Constraints / Extra Work — presence gate

WAS THE JOB SAFE?  (safety story)
├── Section 03 safety triggers (accidents, injuries, escalation cascade)
└── Photos + attachments (evidence)

WHAT HAPPENS NEXT?  (future-facing)
└── Section 10b · Tomorrow / Follow-Up

SIGN-OFF / SUBMIT  (validation gate)
├── Distribution list
├── Prepared By signature
└── 6-photo minimum + submit gate

OPTIONAL · ADDITIONAL CONTEXT (rarely needed)
└── NarrativeWorkflow — collapsed under <details>. Preserved for
    schema compat; invisible to the 90% path.
```

## Authoritative-home invariant

| Operational fact | Home | Never asked again in |
| --- | --- | --- |
| Crew names / hours / trades | `masci_crews[]` (People) | Notes · Narrative · Activities |
| Subcontractor company / hours | `subcontractors[]` (People) | Notes · Narrative |
| Visitor / inspector | `visitors[]` (People) | Safety · Notes |
| Equipment on site + hours | `equipment[]` (People) | Notes · Narrative |
| Materials delivered | `materials[]` (What Moved) | Notes · Narrative · Activity |
| Materials hauled off | `outbound_materials[]` (What Moved) | Notes · Narrative |
| Structured production qty | `production[]` (What Got Done) | Notes · Narrative · Activity |
| Legacy work log | `activities[]` (What Got Done) | — kept for backward compat; UI de-emphasized |
| Delays / weather / constraints | `constraints[]` + `schedule_delays` + `weather_impact` (What Impacted) | Notes · Narrative |
| Injury / accident | `injuries_reported` + `safety_incidents_today` cascade (Was Safe) | Notes · Narrative |
| Photos (min 6) | `photos[]` (Was Safe · evidence) | — |
| Tickets / PDFs / Excel | `attachments[]` (What Moved · What Got Done — evidence) | — |
| Tomorrow / follow-up | `narrative_sections.tomorrow_plan` (What Happens Next) | Notes · Narrative |
| Unique operational context | `general_notes` (Sign-Off) — one optional field | — |

## Zero backend drift

* No schema key added, renamed, or removed.
* No route added, renamed, or removed.
* `narrative_sections{}` schema field preserved for backward compat (historical DRs continue to render it on PDF/PM/email; the operator surface is de-emphasized behind a `<details>` disclosure).
* All Track 19.03 / 19.04 / 19.05 / 19.06 contracts intact.

## Progressive disclosure preserved (Track 19.06)

Every 19.06 Yes/No presence gate remains. The cognitive checkpoints layer sits ABOVE the presence gates, not instead of them — this is a semantic labeling refinement + duplicate-question removal, not a structural rewrite.
