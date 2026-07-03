# TRACK 19.54 · Operational Thread Specification

## What is an Operational Thread?
A **read-only chronological timeline** of related operational events
tied to a single subject (equipment unit · employee · project · incident).

The Thread eliminates the "click through five portals" problem: when
an operator drills into a subject, they see all related events on one
scroll — inspections, repairs, safety notes, incidents, POs,
assignments, photos, history entries — in a single, timestamped list.

## Component
`OperationalThread.jsx` under
`/app/frontend/src/components/operational_intelligence/`.

## Contract
```jsx
<OperationalThread
  title="Operational thread"       // section header
  subject="Excavator 42 · CAT 349F" // subject label
  events={[                        // caller-provided array
    { kind: "inspection", at: "2026-07-04T09:00:00Z", title: "DVIR pass", deep_link: "/…" },
    { kind: "safety",     at: "2026-07-03T15:30:00Z", title: "Trench safety observation", summary: "…" },
    // …
  ]}
  emptyLabel="No related events yet."
  testId="unit-42-thread"
/>
```

### Event schema (caller-provided)
| Field      | Required | Notes                                                                 |
|------------|:--------:|-----------------------------------------------------------------------|
| `kind`     | ✅        | inspection · repair · safety · incident · po · assignment · photo · history · other |
| `at`       | ✅        | ISO-8601 timestamp (sorted DESC by this field)                        |
| `title`    | ✅        | One-line label                                                        |
| `summary`  | optional | Two-line summary max                                                  |
| `deep_link`| optional | React Router path (link renders on the title)                         |
| `id`       | optional | Stable key                                                            |

## Zero-drift guarantees
- **Read-only.** The component contains NO `fetch(`. Enforced by
  lock test `test_operational_thread_is_read_only`.
- **No storage.** Thread never persists, never mutates state, never
  writes to a collection.
- **No aggregation logic.** Callers assemble the array from existing
  endpoints; the Thread is a pure renderer.
- **No new backend.** The Thread does not imply any new backend
  route.

## Six-Pillar compliance
| Pillar      | Evidence                                                              |
|-------------|-----------------------------------------------------------------------|
| Powerful    | Displays every kind of related event on one screen.                   |
| Simple      | Fixed 3-line entry format: chip · timestamp · title (+ optional).     |
| Beautiful   | Consistent divider grid · calm spacing.                               |
| Trusted     | Every event echoes caller payload verbatim.                           |
| Proven      | Lock test enforces read-only guarantee.                               |
| Operational | Deep links let the user jump to the source system in one click.       |

## Adoption plan
Track 19.54 ships the primitive. Adoption in each domain (Fleet Unit
Detail, Employee 360, Project Detail, Incident Detail) will be done in
follow-up tracks — the primitive is available now for any surface that
wants to consume it. No forced adoption inside this track.
