# PHASE 30 · Operational Truth Search
## iter432 · 2026-05-25 · PLANNING DOC

## Scope decision
This is the **planning** doctrine. Engineering MVP lands in Phase 31
as one disciplined endpoint + one calm UX.

## Mission
ONE unified operational retrieval surface that answers questions in
**operational language**, not database language.

Operator-typed query   →  Operational truth, ranked by recency.

Examples:
| Operator query       | Returns                                                    |
|----------------------|------------------------------------------------------------|
| "Truck 47 breakdown" | latest assignments + continuity events + recovery rows referencing truck 47 |
| "Oxford delay"       | Oxford project's continuity events + open Field Memory     |
| "tanker BOL"         | operational_attachments with type=load_proof on tanker assignments |
| "returned to service"| latest recovery_history rows with `to=returned_to_service` |

## Index coverage (read-only · NO secondary store)
The MVP must scan and merge results from EXISTING collections:
1. `dispatch_assignments` — id / truck / driver / project / state
2. `dispatch_continuity_events` — title + note
3. `operational_attachments` — filename + operational_note + type
4. `dispatch_assignments.recovery_history` — `to` state + note
5. `equipment` — unit_label
6. `projects` — name
7. `field_memory_notes` — body + subject_label
8. `users` — name + email (admin search only)

## Doctrine
- **NO Elasticsearch** · NO Solr · NO Algolia · NO vector store.
- Mongo text indexes + a tiny Python ranker. Add `$text` indexes on
  the columns above with weighted fields.
- ONE endpoint: `GET /api/operational-search?q=...&kinds=...`
- One response shape:
  ```jsonc
  {
    "q": "Truck 47 breakdown",
    "total": 8,
    "items": [
      {"kind": "assignment", "id": "asgn-1",
       "label": "Truck 47 · Oxford Rd · breakdown · 2h ago",
       "ts": "...", "href": "/dispatch/assignments/asgn-1"},
      {"kind": "continuity_event", "id": "...", "label": "...", ...},
      ...
    ]
  }
  ```
- Each `item.label` is **operational truth**, not a row dump.
- Each `item.href` deep-links to where the operator can act.
- Calm typography: single-column list · 7-day-recency badge · no
  rank score visible · no faceting UI.

## UX (when engineering lands)
- One `<OperationalSearchBar />` component in the global header (visible to
  every gated portal · NOT public).
- Keyboard shortcut: `/` focuses the bar.
- Live results in a `<ResultStrip />` that appears below the bar.
- Mobile-first · full-screen result list with thumb-friendly tap targets.
- Bilingual placeholder: "Search operational truth…" / "Buscar verdad operacional…"

## What this phase did NOT do
- ❌ Did NOT build any search engine
- ❌ Did NOT add any search collection
- ❌ Did NOT touch any frontend

## Acceptance gates (when engineering lands)
- ☐ Single endpoint · single response shape · single component.
- ☐ MUST work without internet (Mongo native text only — no
  third-party SaaS).
- ☐ MUST never block the UI on any single slow result.
- ☐ Operational language test: a non-developer can compose 5 useful
  queries from memory.
- ☐ NO ranking score surfaced · NO analytics surface.
