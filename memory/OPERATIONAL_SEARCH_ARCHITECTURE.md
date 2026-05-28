# Operational Search Architecture

_Phase V-Prelude · Priority #2 · doctrine + scope · 2026-05-28._

## Mission

A superintendent in the field types "trench" or "utility conflict
SR-7" and finds every relevant operational artifact — incidents,
reports, inspections, constraints, photos — in under one second,
on a 4G connection.

This is **operational recall**, not enterprise search. No SaaS-y
faceted filter UI. No advanced query language. No knowledge graph.

## In scope (Phase V-Prelude)

- A single `/api/search` endpoint with text-only query.
- Backend uses MongoDB text indexes on existing collections.
- Results grouped by artifact kind (incidents · reports ·
  inspections · constraints · photos).
- Mobile-first result UI · calm typography · no thumbnails larger
  than 64 px.

## Out of scope (V.1+)

- ⛔ Vector / semantic search
- ⛔ NLP intent parsing
- ⛔ External-document ingestion
- ⛔ Saved searches
- ⛔ Search analytics dashboard
- ⛔ Faceted filter UI (replaced by a single calm `kind` segmented control)

## Architecture (draft)

### Indexes (Mongo `text` index per collection)
```python
# incidents          — title, description, location_label
# daily_reports      — narrative, weather_notes, manpower_notes
# inspections        — checklist_notes, findings
# meetings           — title, agenda, action_items
# constraints        — title, notes, operational_impact, owner
# photos             — caption, project, discipline
```

Each index ONLY touches the operationally relevant fields. No PII.
No system metadata. No internal IDs.

### Endpoint
```
GET /api/search?q=<term>&kind=<all|incidents|reports|inspections|constraints|photos>
```

Response:
```jsonc
{
  "query": "trench",
  "elapsed_ms": 42,
  "groups": [
    { "kind": "incidents",   "count": 3, "items": [...] },
    { "kind": "constraints", "count": 1, "items": [...] },
    { "kind": "photos",      "count": 17, "items": [...] }
  ]
}
```

Each item: `id`, `kind`, `title`, `project`, `occurred_at`
(tz-aware), `snippet` (≤ 160 chars, highlighted).

## Ranking (deliberately boring)

1. Exact phrase match in `title` → top.
2. Recency: same-month results bubble above same-year results.
3. Open / unresolved status bubbles above resolved.
4. **No vanity scoring · no "relevance" magic.**

## UX commitments

- Single search box in every portal shell header.
- Mobile: full-screen search overlay (one tap to open, one tap to dismiss).
- Results paginate at 20 per group.
- Each result hits **one tap** to navigate to the detail surface.
- Empty-state copy is calm: "No matches. Try a project number or a
  single keyword like 'trench' or 'fire-watch'."

## Performance budget

- p95 response: < 200 ms with 5,000 records per collection.
- Concurrent ceiling: 50 requests/min/portal (rate-limited).
- No client-side full-text scan — server-only.

## Governance hooks

- Admin-only `/api/admin/search/health` returns index status and
  total scanned records (TRUST-TIME-1 compliant timestamps).
- OPS-1 adds a `search_health` stanza (registered count vs live).
- TRUST-1B probe verifies no `new Date(x).toLocaleString()` slips
  into the search result row component.

## Phase-V handoff

Phase V.1 RFI MVP will add `rfis` to the search index. Phase V.3
Schedule will add `schedule_activities`. The endpoint contract is
forward-compatible (add a new `kind`, that's all).

## Stop condition

Doctrine only. Implementation begins on operator command. The
endpoint MUST NOT ship without the OPS-1 stanza + the
`/api/admin/search/health` admin probe (both are governance
prerequisites under the calm-doctrine contract).
