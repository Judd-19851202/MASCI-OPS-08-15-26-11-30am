# Phase 1 · Dead Code Report

**Date:** 2026-02-05
**Policy:** Delete only machine-proven-dead code with zero AST-wide incoming references. Anything uncertain is classified, not deleted.

## Backend
- `class Config` in Pydantic BaseModel subclasses: **0** (down from 1 after Track 22.4A)
- `regex=` in FastAPI parameter carriers: **0** (down from 12 after Track 22.3)
- `schema_extra=`, `json_encoders=`, `@validator`, `@root_validator`: **0** (audit-clean at Phase 1 close)
- Legacy `@app.on_event("startup")` handlers: **0** (down from 51 across Tracks 22.1D–22.1L)
- Legacy `@app.on_event("shutdown")` handlers: **0** (down from 1 after Track 22.1K)
- Un-referenced backend imports flagged in this pass: **0**

## Frontend (App.js machine cross-reference — Track 22.2 inventory)
- Total imports: 318 (138 eager + 180 lazy)
- Imports with `hits ≤ 1` AND not appearing in any `<Route element={...}>`: **0**
- Duplicate route paths: **0**
- Duplicate provider mounts: **0**

## Documentation-preserved (Class C · not deleted)
| # | File | Lines | Reason for preservation |
|---:|---|---|---|
| 1 | `frontend/src/App.js` | 5 | `// AuthProvider removed 2026-04-28 — Crew Hub scrapped.` — tombstone documents a scrapped architectural direction; consolidation into feature-file docstring during Track 22.2 Phase B |
| 2 | `frontend/src/App.js` | 87–93 | Documented `NewIncident` retirement — explains why an on-disk file (`pages/NewIncident.jsx`) is not routed AND why it must be preserved (iter333/335/336 lock tests scan it). Delete requires updating those lock tests first. |
| 3 | `frontend/src/App.js` | 565 | Same block, second appearance — companion narrative comment |

## Retained on disk (Class E · intentional design)
- `frontend/src/pages/NewIncident.jsx` — scanned by lock tests iter333/335/336 as cross-form pattern reference. Zero routes reference it (verified). Deletion blocked by lock-test dependency.

## Deletions executed this session
_None._ Every candidate was either already clean (backend) or required cross-file lock-test coordination (frontend).

## Rationale for zero deletions
The Defect Constitution requires machine-proven dead status with zero incoming references. Every backend candidate was already handled by Tracks 22.3 / 22.4A. The frontend candidates all have live cross-file dependencies (lock-test scans, documented narrative). Removing them without the accompanying Track 22.2 Phase B route extraction would violate the constitutional rule "anything uncertain: do not delete."

## Class summary
- **Class A · to-delete-now:** 0
- **Class C · owned, deferred to Track 22.2 Phase B / 22.4B / 22.6:** 3 (see PHASE_1_OPEN_ITEM_MATRIX.md)
- **Class E · intentional retention:** 1 (`NewIncident.jsx`)
