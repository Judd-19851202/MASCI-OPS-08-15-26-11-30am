# Accountability Service Integration Report · Phase 1A-3

**Batch:** Pillar 1 · Phase 1A-3 · Accountability Service Surface
**Date:** 2026-05-31
**Scope:** Wrap the certified Phase 1A-2 projection layer in a read-only admin-strict service surface. Three endpoints. No source workflow change. No Command Center integration. No UI. No deploy.
**Discipline:** OMEGA · evidence-led · zero scope drift into Escalation / Notifications / Pillar 2 Command Center wiring / Pillar 3 / Pillar 4.

---

## 1 · Executive verdict

🟢 **INTEGRATED.** The certified projection layer is now reachable over a read-only admin-strict HTTP surface and demonstrably returns canonical accountability records from all six certified sources without touching any workflow.

| Endpoint | Verb | Auth | Purpose |
|---|---|---|---|
| `/api/admin/accountability/sources` | GET | `require_admin_strict` | Static metadata: canonical statuses + 6 supported sources |
| `/api/admin/accountability/item` | GET | `require_admin_strict` | Projection for a single source row (`?source_module=&source_record_id=`) |
| `/api/admin/accountability/snapshot` | GET | `require_admin_strict` | Bulk projection across all 6 sources, capped (`?per_source=N`, default 50) · 15 s in-memory cache |

---

## 2 · What was built

### 2.1 · New files

| Path | Type | LOC | md5 |
|---|---|---|---|
| `/app/backend/routes/accountability_service.py` | NEW · admin-strict router factory | 215 | `0e879cf9b774c41e48fe7eea38f63e71` |
| `/app/backend/tests/test_accountability_service_phase_1a3.py` | NEW · live HTTP cert suite (21 tests) | 291 | `e5d3f84d441ea41341c9654a483b122b` |

### 2.2 · Modified files (1 file · 8 lines)

| File | Change |
|---|---|
| `/app/backend/server.py` | Add 8 lines: import `build_accountability_router` and `include_router(...)` next to the Command Center router |

### 2.3 · Files **NOT** modified

- `/app/backend/lib/accountability_projection.py` — Phase 1A-2 contract is byte-identical (md5 `e8de1112f0e9793b94e556e0463e58b9`).
- `/app/backend/routes/command_center.py` — Pillar 2 Phase A surface untouched.
- `/app/backend/routes/tasks_notifications.py`, `safety_portal/corrective_actions.py`, `po_requests.py`, `fleet_ops.py`, incident routes — every source workflow untouched.
- `/app/frontend/**` — zero frontend change.

---

## 3 · Architecture

### 3.1 · Factory pattern (mirrors Command Center)

```python
# server.py
from routes.accountability_service import build_accountability_router

app.include_router(
    build_accountability_router(db, require_admin_strict),
    prefix="/api",
)
```

The router factory receives the `motor.AsyncIOMotorClient`-backed `db` handle plus the existing `require_admin_strict` dependency. This is the same pattern used by `build_command_center_router` (`server.py:8910-8913`).

### 3.2 · Module structure

```
routes/accountability_service.py
├── In-memory cache state (15s TTL · per_source-keyed)
├── _SOURCE_DESCRIPTORS  (static metadata)
├── Bulk page projection helpers
│     _project_tasks_page(db, limit)
│     _project_cas_page(db, limit)
│     _project_pos_page(db, limit)
│     _project_defects_page(db, limit)
│     _project_incidents_page(db, limit)        # async · CA lookup per row
│     _empty_virtual_section()                  # virtual signals are payload-driven
├── _counts_from_projections(items)             # roll-up totals
└── build_accountability_router(db, require_admin_strict_dep)
       ├── GET  /admin/accountability/sources
       ├── GET  /admin/accountability/item
       └── GET  /admin/accountability/snapshot
```

### 3.3 · Cache

| Property | Value |
|---|---|
| Cache key | `per_source` (integer) |
| TTL | 15 seconds |
| Storage | Process-local dict (mirrors Command Center pattern) |
| Invalidation | TTL-based only — no write path exists in this phase |
| Memory footprint | One snapshot dict per per_source value seen in the TTL window — bounded by operator usage |

### 3.4 · No new collection · no new write path

- The router imports the certified projection functions and queries the **existing** source collections (`db.tasks`, `db.corrective_actions`, `db.po_requests`, `db.fleet_defects`, `db.incidents`) with `find({}, {"_id": 0})`.
- The router does **NOT** insert into `db.accountability_timeline` (deferred to a later phase).
- The router does **NOT** mutate any source row.
- The router does **NOT** create any new collection.

---

## 4 · Auth surface

All three endpoints sit behind `require_admin_strict` (the same gate that protects backups, recovery, Command Center, Phase A drilldown). Behavior:

| Request | Status | Body |
|---|---|---|
| No `X-Admin-Token` header | 401 | `{"detail": "Admin login required"}` |
| Invalid `X-Admin-Token` | 401 | `{"detail": "Invalid admin token"}` |
| Valid admin token | 200 | payload |
| Valid token + unknown record id (on `/item`) | 404 | `{"detail": "<resource> <id> not found"}` |
| Valid token + unsupported source_module | 400 | `{"detail": "unsupported source_module <sm>"}` |
| Valid token + virtual source_module on `/item` | 404 | virtual signals have no backing row |

Auth gating is **identical** to every other admin-strict endpoint on the platform; no new auth code was written.

---

## 5 · Endpoint contracts

### 5.1 · `GET /api/admin/accountability/sources`

```json
{
  "canonical_statuses": ["open", "in_progress", "pending_review",
                          "resolved", "closed", "cancelled"],
  "sources": [
    {"source_module": "tasks", "collection": "tasks",
     "kind": "first_class", "is_async_projection": false,
     "description": "..."},
    {"source_module": "safety.corrective_actions", ...},
    {"source_module": "po.requests", ...},
    {"source_module": "equipment.dvir", ...},
    {"source_module": "safety.incidents",
     "is_async_projection": true, ...},
    {"source_module": "virtual.signals", "kind": "virtual", ...}
  ]
}
```

Static · no DB query. Useful for client discovery and contract introspection.

### 5.2 · `GET /api/admin/accountability/item?source_module=...&source_record_id=...`

Returns the canonical 23-field projection for one source row. Fields verified by `test_snapshot_every_item_has_canonical_24_field_shape`:

```
accountability_id, source_module, source_record_id, title,
owner_role, owner_user_id, owner_employee_id, owner_display_name,
assigned_at, assigned_by, due_at, status, priority,
first_viewed_at, first_viewed_by,
last_activity_at, last_activity_kind,
escalation_level,
resolved_at, resolved_by, resolution_notes,
overdue, timeline_events
```

### 5.3 · `GET /api/admin/accountability/snapshot?per_source=N`

```json
{
  "phase": "1A-3",
  "per_source": 50,
  "sections": {
    "tasks":                     {"items": [...], "counts": {...}},
    "safety.corrective_actions": {"items": [...], "counts": {...}},
    "po.requests":               {"items": [...], "counts": {...}},
    "equipment.dvir":            {"items": [...], "counts": {...}},
    "safety.incidents":          {"items": [...], "counts": {...}},
    "virtual.signals":           {"items": [],   "counts": {...}}
  },
  "rollup": {
    "total_items": 177,
    "overdue_items": 82,
    "by_status": {
      "open": 161, "in_progress": 2, "pending_review": 0,
      "resolved": 4, "closed": 6, "cancelled": 4
    }
  },
  "timing_ms": {
    "tasks": 58.3, "corrective_actions": 27.93, "po_requests": 29.21,
    "fleet_defects": 28.83, "incidents": 1358.41, "virtual": 0.0,
    "total": 1502.67
  },
  "cached": false
}
```

The roll-up arithmetic is enforced by `test_snapshot_rollup_arithmetic_matches_sections`.

---

## 6 · Live preview probe (evidence)

Captured 2026-05-31 14:55 UTC against preview source_hash `54b8a402de538a17579cabc2e6aaac38` + this batch's 8-line server.py addition:

```bash
$ curl -s "$URL/api/admin/accountability/sources" -H "X-Admin-Token: $T"
# → 200 · 6 sources listed with canonical_statuses

$ curl -s "$URL/api/admin/accountability/snapshot?per_source=100" -H "X-Admin-Token: $T"
# → 200
# phase=1A-3 · per_source=100 · cached=false
# rollup.total_items=277 · rollup.overdue_items=125
# tasks 100 · CA 8 · PO 100 · defects 50 · incidents 19 · virtual 0
# timing_ms.total=1484.74 (cold call · 90% in incidents async)

$ curl -s "$URL/api/admin/accountability/snapshot?per_source=100" -H "X-Admin-Token: $T"
# → 200 · cached=true (warm hit)

$ curl -s "$URL/api/admin/accountability/item?source_module=tasks&source_record_id=5f112422-...&_" \
       -H "X-Admin-Token: $T"
# → 200 · 23 canonical fields · source_module=tasks · status=open · escalation_level=0

$ curl -s "$URL/api/admin/accountability/item?source_module=tasks&source_record_id=does-not-exist" \
       -H "X-Admin-Token: $T"
# → 404

$ curl -s "$URL/api/admin/accountability/item?source_module=unknown.workflow&source_record_id=x" \
       -H "X-Admin-Token: $T"
# → 400

$ curl -s "$URL/api/admin/accountability/snapshot" -H "X-Admin-Token: BAD"
# → 401
```

---

## 7 · Out-of-scope confirmation

| Item | Status |
|---|---|
| Escalation Framework | 🛑 NOT BUILT (`CANONICAL_EVENT_KINDS` excludes `escalated`; `escalation_level=0` always · enforced by `test_snapshot_every_item_has_escalation_level_zero`) |
| Notification changes | 🛑 NOT BUILT |
| Emails / SMS | 🛑 NOT BUILT |
| Dashboard UI | 🛑 NOT BUILT (zero frontend change) |
| Executive Command Center integration | 🛑 NOT BUILT (`command_center.py` md5 unchanged) |
| ForgedOps Portal | 🛑 NOT BUILT |
| White Label Architecture | 🛑 NOT BUILT |
| Pillar 2 work | 🛑 NOT BUILT |
| Pillar 3 work | 🛑 NOT BUILT |
| Pillar 4 work | 🛑 NOT BUILT |
| Phase 1A-4 and beyond | 🛑 NOT BUILT (the new endpoints are reachable but no Command Center surface consumes them) |

---

## 8 · OMEGA discipline check

| Discipline rule | Verdict |
|---|---|
| Source workflows untouched | 🟢 |
| Projection library untouched (md5 stable) | 🟢 |
| Command Center router untouched | 🟢 |
| One new module · one new test file · 8 lines in server.py | 🟢 |
| No new collection | 🟢 |
| No notifications / emails / SMS / cron | 🟢 |
| No escalation logic | 🟢 |
| No frontend change | 🟢 |
| No deployment | 🟢 |
| Backup · recovery · scheduler · R2 · drill framework untouched | 🟢 (verified by regression tests) |

---

## 9 · Phase 1A-3 closeout

🟢 The certified projection layer is now reachable and testable through a clean read-only HTTP service surface. The integration is **passive** with respect to every existing workflow — no source row mutates, no Command Center route runs the projection, no UI shows it. Phase 1A-4 (Command Center owner-string replacement) is the next operator-authorized step.

🛑 **STOPPED.** No further work without authorization.
