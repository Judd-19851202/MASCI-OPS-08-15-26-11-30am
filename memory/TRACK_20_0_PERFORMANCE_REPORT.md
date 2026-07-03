# TRACK 20.0 · Performance Report

## Rendering
- Every Attention Strip issues **one** shared `GET /operational-intelligence/summary` request per portal load. Client-side filters to the portal's product IDs — no per-tile fetch storm.
- Cockpit sparkline is pure SVG rendered from data already in the summary payload — **zero additional HTTP requests**.
- Guidance Card fetches on demand only (modal open):
  1. `GET /operational-intelligence/history?product_id=X&limit=1`
  2. `GET /operational-intelligence/history/{id}` (single row)

  Two lightweight GET requests total, only when a user clicks a tile.
- Fleet Unit Thread pilot issues exactly **two** parallel GETs on mount:
  1. `GET /api/assets/{unit_number}/timeline` (Track 13.26 backbone)
  2. `GET /api/operational-intelligence/summary`

## Bundle & compile
- Frontend lint clean across every 19.51 → 19.55 file.
- Webpack compiles clean (no parse errors on latest restart).
- No new runtime dependencies added by any of the 5 remediation tracks — Track 20.0 adds zero.

## Backend
- No new endpoints created since Track 19.50.
- No new collections created.
- No new scheduler jobs.
- All Tracks 19.51 → 20.0 changes are **frontend-only additive**.

## Recommended future performance work (P3)
- **15-minute in-memory cache on `/operational-intelligence/summary`.** Corporate + Weekly-Ops previews currently take 6-7 seconds each; caching would collapse every portal's Attention-Strip first-paint to < 300 ms. Backend-only, one file. Non-blocking for production go-live.

## Verdict
🟢 **Performance profile is acceptable for production.** Every portal
issues one shared summary GET; drill-downs are lazy; no fetch storms.
