# TRACK 19.36 · TIMELINE

**Date:** 2026-07-03 · **Anchor:** `TRACK_19_36_EXECUTIVE_INTELLIGENCE.md`

## Source of truth
The timeline is assembled from **exactly one** certified collection: `incident_case_events` (the same collection served by `/api/incident-cases/{id}/timeline` since Track 19.16 Phase A).

## Rules
- Zero synthesis. No event is invented.
- No re-ordering. Events are returned in the order the audit surface returns them.
- Every event records: `id · at · actor_name · actor_role · event_type · from_state · to_state · reason · summary · source`.
- The `source` field is always `"incident_case_events"` — the collection auditors query directly.

## Summary composition
`_compose_event_summary()` deterministically formats a one-line summary from four existing fields (`event_type`, `from_state`, `to_state`, `actor`, `reason`). No LLM, no free text.

## Traceability
Any timeline row can be traced back with:

```
db.incident_case_events.find_one({ "id": <row.id> })
```

The document returned is byte-identical to the source of the summary.

## Never editable
The assembler is read-only. Consumers may render, filter, or paginate the timeline, but they cannot mutate any row. The append-only invariant of `incident_case_events` (Track 19.16 Phase A) remains the enforcement layer.

## Renderer surfaces
- **PDF:** a bordered table (`Timestamp · Event · Actor`) inside the "Timeline (traceable)" section.
- **Frontend Executive Case Report page:** an ordered list, each entry with `at`, `summary`, and actor.

Both surfaces consume the exact same array from the Executive Intelligence Model — one source, one rendering per surface.
