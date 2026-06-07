# Phase 7.5A · Tabulated Data

## Drift fix (DRIFT-1)
- `POST/PUT/DELETE /api/trench-boxes` re-gated from `require_admin` → `require_safety_or_admin` (server.py).
- `/safety/trench-safety/tabulated-data` now renders `TrenchBoxTabulatedLibrary adminMode={true}` — the upload, replace, and delete controls that previously only existed at `/admin/trench-boxes`.
- `/admin/trench-safety/tabulated-data` mirrors the same component for Admin Portal parity.
- Legacy public `/trench-boxes` redirects to `/trench-safety/tabulated-data`.
- Existing PDFs preserved — no schema change, no data migration. All Manufacturer / Model / Folder paths intact.

## Component reuse
Both Safety and Admin paths render the same React tree:
```
TrenchSafetyTabulatedData
└─ TabulatedDataPrimer (existing, unchanged)
└─ TrenchBoxTabulatedLibrary adminMode={true} (existing, unchanged · adminMode flag flipped)
```
No duplicate library code; no parallel UI.

## Public side (read-only)
- `/trench-safety/tabulated-data` (public surface from earlier sprint) keeps `adminMode={false}` — crew browse + download only.

## Validation curl (admin token)
```
POST /api/trench-boxes {"manufacturer":"PHASE75A_TEST","model":"M1",…} → 200 · {id:"…"}
```
Curl with no token / wrong token → 401 (gate enforced).

## Alerts (existing dashboard)
The Safety Hub already shows `Missing Tabulated Data` count via `dashboard.py`. Unlinked Assets / Duplicate PDFs / Expired References surface inside the hub alerts strip and need no additional UI in Phase 7.5A.
