# Operational Timeline Foundation

_Phase V-Prelude · Priority #8 · doctrine + scope · 2026-05-28._

## Mission

Establish the chronology infrastructure that lets future RFI +
Schedule + external-collaboration systems compose without
re-doing this work. **Cross-system chronology is a substrate, not
a feature.**

The flow the timeline should eventually support:

```
issue discovered
  ↓
photos uploaded
  ↓
report references issue
  ↓
constraint created
  ↓
owner contacted
  ↓
resolved
```

In V-Prelude we lay the substrate. We do NOT build the full UI.

## In scope (V-Prelude foundation only)

- A typed **link** structure across the new and existing
  collections.
- An aggregation endpoint that returns chronology for one
  reference (project / location / discipline).
- A minimal read-only timeline panel on constraint / incident
  detail pages (slate text, no chart).

## Out of scope (V.1+)

- ⛔ Standalone "/timeline" page
- ⛔ Gantt-style rendering
- ⛔ Predecessor / successor logic
- ⛔ Critical-path math
- ⛔ Tag-based timeline grouping

## Schema (the substrate)

A single `operational_links` collection captures cross-artifact
relationships:

```jsonc
{
  "id":              "uuid4",
  "kind_a":          "constraint | report | incident | inspection | photo | meeting | (future) rfi | (future) activity",
  "id_a":            "fk · same collection as kind_a",
  "kind_b":          "same enum",
  "id_b":            "fk",
  "relation":        "evidence | reference | resolution | escalation | duplicate",
  "project_id":      "denormalized for fast project-scoped queries",
  "created_by":      "actor_id",
  "created_at":      "tz-aware ISO (TRUST-TIME-1)",
}
```

This single table glues constraints ↔ reports ↔ photos ↔
incidents ↔ inspections ↔ (future) RFIs ↔ (future) schedule
activities.

## Aggregation endpoint

```
GET /api/timeline?project_id=...&from=...&to=...
→ {
    "items": [
      { "kind": "incident", "id": "...", "at": "...", "title": "...", "linked_to": [...] },
      ...
    ],
    "generated_at": "tz-aware ISO"
  }
```

Single-project scoped. Sorted by `at` (operator-local-tz aware).
No pagination beyond 200 items per call (V-Prelude scope).

## Surface (V-Prelude)

A calm panel labeled **"Chronology"** appears at the bottom of
constraint / incident detail pages:

```
Chronology · this constraint
  · 5/12 photo: trench wall slough  (linked photo)
  · 5/13 daily report: density failed STA 144+50 (linked)
  · 5/14 constraint opened (this record)
  · 5/15 owner contacted (chronology note)
  · 5/17 resolved · ULM coord complete
```

Text-only. Slate. No icons beyond Lucide. No animation. No
zoom-in / zoom-out. **No chart.**

## Linkage UX

- Photos uploaded from a daily-report form auto-link to that
  report.
- Constraint create form has an optional "Link to existing
  report / incident / inspection" multi-select.
- A constraint resolution can reference photos and notes
  inline — they're added to the chronology automatically.

## Governance hooks

- TRUST-TIME-1 compliant on every `at`.
- Authority Mismatch Probe: no new patterns.
- TRUST-1B Timestamp Doctrine Probe scans the new timeline panel
  component.
- OPS-1 `trust_surfaces` registry adds:
  - `operational-timeline-panel` (read-only)
- OPS-1 stanza is INFORMATIONAL ONLY — never blocks deploy.

## Phase-V handoff

When V.1 RFI MVP lands, RFI commits a `kind_a: rfi` row to
`operational_links` on every cross-link action. When V.3
Schedule lands, schedule activities likewise. The timeline
endpoint is forward-compatible — no new endpoint required.

## Performance budget

- `/api/timeline` p95 < 250 ms with 5,000 link rows per project.
- Link insert is O(1) — one insert per cross-reference action.
- No background jobs. No indexer. No queue.

## Stop condition

Substrate doctrine only. Implementation alongside Priority #1
(constraints) — constraints are the first surface that
materially benefits from the timeline panel.
