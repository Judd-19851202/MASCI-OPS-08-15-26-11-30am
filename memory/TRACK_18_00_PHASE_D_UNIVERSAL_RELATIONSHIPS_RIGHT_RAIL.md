# TRACK 18.00 · Phase D · Universal Relationships + Live Right Rail

**Status:** ✅ GO
**Date:** 2026-02-10
**Schema:** `18.00D`

---

## Mission
Every Transportation Operations entity is now connected, explainable, and navigable. One composer endpoint stitches relationships together live from existing collections — no graph DB, no relationship index, no data migration. The right rail in every workspace now answers "What is this connected to?" in real time, filtered by portal role.

---

## What shipped

### Backend — `routes/transportation_relationships.py`
* **Single composer endpoint** — `GET /api/admin/transportation/related/{entity_type}/{entity_id}`
* **11 supported entity types** — `driver`, `carrier`, `truck`, `dispatch_assignment`, `project`, `certificate`, `document`, `orientation`, `inspection`, `action_item`, `cleanup_signal`
* **5 sections** returned in a stable envelope — `recent_activity`, `timeline`, `related_records`, `open_actions`, `audit`
* **Schema version** stamped `18.00D` on every response
* **RBAC matrix** keyed on the `_actor` field set by `make_require_any_portal_token` (mirrors Phase C):
  - `admin` / `leadership` → all relations
  - `dispatch` → trucks, drivers, carriers, dispatch, projects, audit
  - `hr` → drivers, documents, orientation, audit
  - `pm` → projects, dispatch, trucks, audit
  - `safety` → drivers, trucks, audit
  - `shop` → trucks, audit
  - `fl` → drivers, projects, audit
  - unknown / anonymous → **403 with `no_relationships_permission`**
* **Unauthorized relations are OMITTED**, never redacted — existence of the relationship is never leaked.
* **Bounded** — every section capped (5/8/10/5/8); optional `?limit=N` clamped to `MAX_LIMIT=25`.
* **Read-only** — no `insert_*` / `update_*` / `delete_*` / `replace_*` / `find_one_and_update` anywhere in the route.
* **Graceful partial results** — per-section failure isolated via `_safe_find`; one bad collection never blanks the rail.

### Data sources (all existing)
| Section | Collections read |
|---|---|
| `recent_activity` | `audit_events` (newest slice) |
| `timeline` | `audit_events` |
| `related_records` | `transport_persons` · `carriers` · `transport_trucks` · `dispatch_assignments` · `driver_documents` · `carrier_documents` · `transport_orientation_assignments` · `transport_orientation_certificates` · `transport_truck_inspections` |
| `open_actions` | `transport_action_items` (status ∈ {open, in_progress}) |
| `audit` | `audit_events` |

### Frontend — `pages/transportation/TransportationWorkspaceShell.jsx`
* **`useTransportationRelationships(entityContext)`** hook — fetches `/admin/transportation/related/{type}/{id}` via `txGet` with a 30 s in-memory cache keyed on `type::id`.
* **`TxOpsRightRail`** now renders 5 live sections with per-section testids (`txops-rail-recent-activity`, `-timeline`, `-related`, `-open-actions`, `-audit`).
* **Three reactive states** — loading (`LoadingHint`), empty (`EmptyHint` per section), error (`ErrorHint`).
* **URL-driven context fallback** — when no `entityContext` prop is passed, the rail reads `?entity_type=&entity_id=` from `useLocation().search`, letting **Phase C search results deep-link** straight into any workspace with a populated rail.
* **Entity banner** at the top of the rail (`txops-rail-entity-banner`) deep-links to the entity's canonical route.
* **Per-row deep-links** — every row is a `<Link to={row.route}>`, never `#`.
* **Backwards-compatible** — every existing call to `<TransportationWorkspaceShell entityContext=…>` keeps working.

### Wiring
* `server.py` — `register_track_18_00_phase_d_routes(app, db, require_any_portal_dep=…)` mounted immediately after Phase C (single Phase-D import block).
* `scripts/deployment_gate.py` — `test_track_18_00_phase_d_universal_relationships.py` appended to the permanent gate list.

---

## Tests
`backend/tests/test_track_18_00_phase_d_universal_relationships.py` — **40/40 PASS** in 0.33s, covering all 30 mandated requirements + 10 bonus assertions:

| # | What it locks |
|---|---|
| 01 | Route prefix + GET path |
| 02 | GET-only (no POST/PATCH/DELETE/PUT) |
| 03 | 11 supported entity types |
| 04 | Anonymous → 403 `no_relationships_permission` |
| 05 | Admin envelope + schema_version `18.00D` |
| 06 | Dispatch token filtering |
| 07 | HR token never leaks trucks/dispatch |
| 08 | PM token sees project/dispatch/trucks |
| 09 | Safety token: drivers + trucks only |
| 10 | Shop token: trucks only |
| 11 | Unknown entity type → 400 |
| 12 | Unknown entity id → clean `(not found)` envelope |
| 13 | `SCHEMA_VERSION == "18.00D"` |
| 14 | Five required sections always present |
| 15 | No new relationship collection (`db.relationships`, etc.) |
| 16 | No graph DB driver (neo4j, networkx, gremlin, …) |
| 17 | No source-record mutation API used |
| 18 | Every related row has a `route` field |
| 19 | Unauthorized relations OMITTED, not redacted |
| 20 | Shell calls the related endpoint |
| 21 | Right rail renders 5 sections with testids |
| 22 | Search can drive entity context via URL params |
| 23 | Loading state exists |
| 24 | Empty state exists |
| 25 | Error state exists |
| 26 | No dead `#` related links |
| 27 | Phase A shell preserved |
| 28 | Phase B Mission Control preserved |
| 29 | Phase C Search still wired in server |
| 30 | Test file wired into deployment gate |
| 31 | Phase D registered in `server.py` with cross-portal helper |
| 32 | `SECTION_LIMITS` + `MAX_LIMIT=25` correct |
| 33 | Section limits enforced on output |
| 34 | Optional `limit` clamped to `[1, 25]` |
| 35 | Open actions filter status ∈ {open, in_progress} |
| 36 | Audit composer reads `audit_events` only |
| 37 | Garbage role → 403 |
| 38 | dispatch_assignment fans out into all 4 linked entities |
| 39 | `counts` envelope mirrors section lengths |
| 40 | Field Leadership token filtering |

**Cross-track regression — 91/91 PASS** (Phase A · B · C · D in 0.43 s).

---

## Live verification (preview)
```
GET /api/admin/transportation/related/driver/ghost          → 401 (anon blocked)
GET /api/admin/transportation/related/driver/ghost  +admin  → 200
   schema_version = "18.00D"
   sections        = recent_activity, timeline, related_records, open_actions, audit
   entity          = { type:"driver", id:"ghost", title:"(not found)", … }
GET /api/admin/transportation/related/alien/x       +admin  → 400 (unsupported_entity_type)
```

---

## Performance guards
* Bounded queries on every loader (default → `SECTION_LIMITS`, override clamped to `MAX_LIMIT=25`).
* No `find()` without a subsequent `limit()`.
* Frontend 30-second in-memory cache per `(entity_type, entity_id)` tuple — repeat hits within a workspace are free.
* Per-collection failures isolated via `_safe_find` → graceful partial results, never a blank rail.

---

## Audit policy
Per the directive, the rail load itself is **not audited** (would create noise). The composer reads `audit_events` to *populate* the audit + recent_activity + timeline sections; it writes nothing.

---

## Hard guarantees
* No new collection, no new index, no graph database.
* No new business logic / scoring / intelligence / dispatch logic / HR logic.
* No source-record mutation (statically locked by `test_17`).
* No leak of HR or document data to dispatch / shop / safety / fl portals (locked by RBAC tests 06–10, 19, 40).
* Phase A shell + Phase B Mission Control + Phase C Search all preserved (locked by tests 27–29).
* Every related row is deep-linkable (no `#` placeholders).

---

## Deferrals
* Graph visualization of relationships
* Manual link / unlink relationship editing UI
* AI relationship suggestions
* Cross-platform global relationships outside Transportation
* Relationship analytics dashboard

---

## Files
* `backend/routes/transportation_relationships.py` (NEW)
* `backend/server.py` (Phase D registration block added after Phase C)
* `backend/tests/test_track_18_00_phase_d_universal_relationships.py` (NEW · 40 tests)
* `frontend/src/pages/transportation/TransportationWorkspaceShell.jsx` (live rail + hook)
* `scripts/deployment_gate.py` (gate wiring)
* `memory/TRACK_18_00_PHASE_D_UNIVERSAL_RELATIONSHIPS_RIGHT_RAIL.md` (this doc)
