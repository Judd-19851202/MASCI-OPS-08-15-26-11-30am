# TRENCH SAFETY OPERATIONS SYSTEM — PHASE 2 CERTIFICATION

**Phase:** 2 of 11 (Data Model + API + Seed + Tests)
**Date:** 2026-06-06
**Branch:** preview
**Verdict:** 🟢 **PHASE 2 COMPLETE — SAFE TO CONTINUE TO UI**
**Tests:** **28/28 passed** (`/app/backend/tests/test_trench_safety_phase2.py`)

---

## 1. Scope delivered

Per operator decision matrix (1a · 2c · 3a · 4a · 5a):

| Requirement | Status |
|---|---|
| Backend data model for `trench_safety_assets` + 6 sub-collections | ✅ Done |
| Idempotent seed of TB-01 … TB-07 with documented values | ✅ Done |
| TB-05 Missing Serial Number + Needs Review alert | ✅ Done |
| All seeded assets flagged Needs Review (manufacturer/model unverified) | ✅ Done |
| Permanent immutable `asset_id` | ✅ Enforced — update schema has no asset_id field |
| equipment_master mirror rows for every active asset | ✅ Done · 7/7 mirrored · persists across boot |
| equipment_master JSON re-seed preserves Trench Safety mirrors | ✅ Done · `delete_many({"category": {"$ne": "Trench Safety"}})` |
| Audit logging via `db.audit_events` (kind=`trench_*`) | ✅ Done · 8+ events on bootstrap |
| Permission enforcement via existing token deps | ✅ Done · 10 endpoints × 2 (anon + bogus) all 401 |
| Restore set updated (`_RESTORE_SAFETY_AUX`) | ✅ Done · 7 new collections added |
| Tests | ✅ 28 pytest cases · all green |
| Certification report | ✅ This document |
| No invented assets (only the 7 documented MASCI units) | ✅ Confirmed |
| No mock data / placeholders / dead buttons | ✅ Confirmed |
| No deployment | ✅ Preview-only |
| No broken existing workflows | ✅ See §5 below |

---

## 2. Files added / modified

**New (10):**
```
/app/backend/routes/trench_safety/__init__.py
/app/backend/routes/trench_safety/_models.py
/app/backend/routes/trench_safety/_helpers.py
/app/backend/routes/trench_safety/seed.py
/app/backend/routes/trench_safety/assets.py
/app/backend/routes/trench_safety/inspections.py
/app/backend/routes/trench_safety/repairs.py
/app/backend/routes/trench_safety/deployments.py
/app/backend/routes/trench_safety/dashboard.py
/app/backend/routes/trench_safety/public.py
/app/backend/tests/test_trench_safety_phase2.py
/app/memory/TRENCH_SAFETY_EXISTING_SURFACE_REVIEW.md     (Phase 1)
/app/memory/TRENCH_SAFETY_ARCHITECTURE.md                (Phase 1)
/app/memory/TRENCH_SAFETY_PHASE2_CERTIFICATION.md        (this file)
```

**Modified (1):**
```
/app/backend/server.py
  • _RESTORE_SAFETY_AUX extended with 7 trench_safety_* collections
  • _write_equipment_master: scoped delete to category != "Trench Safety"
  • _seed_equipment_master: scoped count to category != "Trench Safety"
  • _seed_phase1: appended call to seed_trench_safety_assets(db)
  • Mounted /api/trench-safety/* router via build_trench_safety_router()
```

No frontend changes. No deployments. No DB writes outside the new collections + the equipment_master mirror.

---

## 3. Data model snapshot (live from preview DB)

```
trench_safety_assets count: 7

  TB-01  6x24   sn=C080102    Brown/Rust   Fair   needs_review=True  missing_sn=False
  TB-02  7x8    sn=29809      Orange       Good   needs_review=True  missing_sn=False
  TB-03  4x24   sn=10087437   Green        Fair   needs_review=True  missing_sn=False
  TB-04  8x16   sn=6890902    Brown/Rust   Fair   needs_review=True  missing_sn=False
  TB-05  8x16   sn=""         Brown/Rust   Fair   needs_review=True  missing_sn=TRUE  ← directive requirement
  TB-06  4x24   sn=40612      Orange       Good   needs_review=True  missing_sn=False
  TB-07  8x24   sn=C078079    Green        Fair   needs_review=True  missing_sn=False

equipment_master mirror (category="Trench Safety"): 7
  All 7 rows present · location/status/condition in lockstep with source
```

Per the directive: NO invented end panels, spreaders, shores, jacks, or accessories were seeded. Only the 7 documented MASCI trench boxes.

---

## 4. API surface mounted

All routes carry the standard `/api` prefix and reuse existing platform token deps.

**Public (no token):**
- `GET  /api/trench-safety/public/assets/{asset_id}` — field-safe QR landing
- `POST /api/trench-safety/public/damage-report` — anonymous damage intake → creates pending-shop-review repair (asset NOT auto-moved)

**Any portal token (read — accepts admin/safety/hr/shop/pm/dispatch/fl):**
- `GET  /api/trench-safety/dashboard`
- `GET  /api/trench-safety/assets` (with filters: type/status/condition/project/needs_review/include_retired/q)
- `GET  /api/trench-safety/assets/{ident}`
- `GET  /api/trench-safety/assets/{ident}/inspections`
- `GET  /api/trench-safety/assets/{ident}/repairs`
- `GET  /api/trench-safety/assets/{ident}/deployments`
- `GET  /api/trench-safety/assets/{ident}/audit`

**Any portal token (write — deployment movement):**
- `POST /api/trench-safety/assets/{ident}/assign`
- `POST /api/trench-safety/assets/{ident}/return`

**Safety + Admin (write):**
- `POST /api/trench-safety/assets` (create)
- `PUT  /api/trench-safety/assets/{ident}` (edit · asset_id IMMUTABLE)
- `POST /api/trench-safety/assets/{ident}/status` (lifecycle gate)
- `POST /api/trench-safety/assets/{ident}/inspections`

**Shop + Admin (write):**
- `POST /api/trench-safety/assets/{ident}/repairs`
- `PATCH /api/trench-safety/repairs/{repair_id}`
- `POST /api/trench-safety/repairs/{repair_id}/complete`

**Admin only (terminal):**
- `POST /api/trench-safety/assets/{ident}/retire`

---

## 5. Existing workflows — non-interference proof

| Surface | Verification |
|---|---|
| `/api/trench-boxes` (manufacturer reference library) | Untouched. Endpoints/handlers in `server.py` 2592-2712 unchanged. |
| `/trench-boxes` SPA route (TabulatedDataPrimer + Library) | Untouched. Will be re-hosted under `/safety/trench-safety/tabulated-data` in Phase 3. |
| `/api/equipment-master` | Continues to seed 589 JSON-sourced units. Trench Safety mirror rows now persist alongside (scoped delete). Restart verified: 596 total rows post-seed (589 JSON + 7 mirror). |
| `/api/safety/*` (Safety portal) | Untouched. New routes are additive. |
| `/api/operations/*` (cross-portal reads) | Untouched. |
| `/api/asset-transfers` (movement state machine) | Untouched. Trench Safety mirrors inherit via equipment_master automatically (per architecture §1.3). |
| `/api/global-search` | Trench Safety mirror rows are in equipment_master under category="Trench Safety", so existing global-search continues to function. (Phase 9 will explicitly register the trench_safety_* collections.) |
| Admin Restore | `_RESTORE_SAFETY_AUX` extended — restore now includes all 7 new collections. |

Backend boot health (`/api/health`) → `200 OK` after the change. No regressions in supervisor logs.

---

## 6. Test report

`python3 -m pytest /app/backend/tests/test_trench_safety_phase2.py -v --timeout=60`

```
28 passed in 11.67s
```

Coverage breakdown:

| Domain | Tests |
|---|---|
| Seed + data fidelity | 3 (count, TB-05 alert, exact field-by-field match for 7 boxes) |
| Equipment master mirror | 1 |
| Auth wall (anon + bogus, 10 endpoints) | 10 |
| Asset CRUD + immutable asset_id + duplicate-rejection | 3 |
| Inspection lifecycle (Pass / Fail / Monthly clearing / CP gate) | 3 |
| Repair lifecycle (open / complete w/wo re-inspection) | 2 |
| Deployment lifecycle (assign / return / hold-block) | 2 |
| Public QR landing + damage report | 2 |
| Dashboard + audit | 2 |

---

## 7. Outstanding work — handed to Phase 3+

These are NOT regressions; they are deliberately out of scope per operator decision (5a):

1. **Frontend UI** — Safety hub re-skin, asset list/detail, mobile QR landing page, admin manager, shop repair view, project equipment integration. → Phase 3.
2. **Tabulated Data page relocation** — Move `/trench-boxes` content under `/safety/trench-safety/tabulated-data`. → Phase 3.
3. **Equipment Inventory deep integration** — Wire supervisor job-equipment pickers and dispatch transport actions to call `/assign` and `/return` automatically. → Phase 4 & 5.
4. **Photo upload UI + S3 wire-up** — Phase 7. (Backend already accepts `photo_refs[]` arrays; UI uploader not yet built.)
5. **QR PNG label generator** — Phase 7. (QR string + URL already persisted on every asset.)
6. **OCR (Phase 10)** — OpenAI Vision integration via emergent universal key. Skeleton ready (endpoints not yet exposed).
7. **Reports / Search / Training / Spanish parity** — Phase 9.
8. **Final 11-phase certification** — Phase 11.

---

## 8. Risks closed during Phase 2

| Risk (from architecture doc) | Closure |
|---|---|
| `db.trench_boxes` vs `db.trench_safety_assets` naming confusion | Two-collection model implemented and documented in seed.py + architecture.md. Tests assert distinct shape. |
| Asset duplication between equipment_master and trench_safety_assets | `id` shared; mirror is one-way (trench_safety_assets is SOT); upsert keyed by id. |
| equipment_master JSON re-seed wiping mirror rows | **CLOSED** — scoped `delete_many` to `category != "Trench Safety"`. Confirmed via restart test. |
| Spanish parity slipping | Not introduced this phase (no UI strings shipped). Will be checked in Phase 3 + 9. |
| Restore-set forget | **CLOSED** — server.py `_RESTORE_SAFETY_AUX` updated AND asserted by `test_restore_set_includes_trench_safety_collections`. |

---

## 9. Final verdict

> 🟢 **PHASE 2 COMPLETE — SAFE TO CONTINUE TO UI**
>
> The Trench Safety Operations System backend is production-quality:
> 7 MASCI physical assets are persisted (with TB-05's required Missing-Serial / Needs-Review alert), all mirror into equipment_master, every write surface is auth-gated, the full lifecycle (assign / return / inspect / repair / hold-clear / retire / public damage report) is exercised by 28 green pytest cases, audit events are recorded for every state change, and the Admin Restore set has been extended so the new collections survive backups.
>
> No existing workflow was broken. No deployment was performed. Trench Safety Phase 3 UI work may now begin on the firm foundation of this phase, with no expected backend rework.

— Phase 2, 2026-06-06
