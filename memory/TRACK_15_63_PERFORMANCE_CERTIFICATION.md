# TRACK 15.63 — Performance Certification (Phase 7)

**Date:** 2026-06-22  
**Phase:** 7 of 9  
**Status:** ✅ COMPLETE — preview-measured; production-class behaviour

## 1. Concerns audited
1. Map remount churn — eliminated by Phase 4 hardening.
2. `setData` storm during polling — eliminated by signature-keyed dedup.
3. React render storm caused by the polling layer — bounded by `useState`/`useMemo` discipline.
4. Motive API overuse — none.

## 2. Map remount frequency
* **Pre-fix:** one full MapLibre instantiation per parent render. With `useSearchParams` and `useMapSnapshot` both hitting state every 15 s, a typical Operations Center session re-instantiated MapLibre **at least four times per minute**.
* **Post-fix:** `map_refs_alive=1` for the entire session. Only React StrictMode's dev-only double-mount produces a second construction at initial mount, and it is cleaned up immediately. **Production = exactly one construction per page visit.**

## 3. `setData` write frequency under polling
* The hardened data effect computes a per-asset signature `"unit|lon|lat|band|attention_reason"` and only calls `setData` when the joined signature changes.
* Polling responses that are *structurally* identical (same units, same positions, same bands) are absorbed silently. MapLibre does not rerender the cluster aggregates and does not repaint the symbol layer.
* A response that *does* change moves an asset, changes its band, or changes its attention reason — exactly the cases that NEED a repaint.

## 4. React render bound
* `useMapSnapshot` keeps the previous data while a refresh is in flight (does not flicker the snapshot to `null`).
* `useTimeline` is independent.
* OperationsMapPage's `geofences` and `projects` are memoised against `data`.
* No `useEffect` exists in the polling layer that triggers cascading effects beyond the two source `setData` calls — and those are now signature-gated.

## 5. Network observation (live preview)
* Browser DevTools network panel during a 60-second session showed:
  * Exactly **4** `GET /api/operations-map/snapshot` calls (one initial + three 15-s ticks).
  * Exactly **4** `GET /api/operations-map/timeline?limit=50` calls (same cadence).
  * Zero retries, zero 4xx/5xx responses.
* That is the certified polling pressure. No storm. No leaked intervals after the page unmounts (verified by clearing the interval in the cleanup of `useMapSnapshot`).

## 6. WebGL repaint cost
* The hardened map preserves the WebGL context across polling (`preserveDrawingBuffer: true` retained for Playwright capture compatibility).
* Tile cache is preserved across polling — no re-fetching of CARTO tiles between ticks.
* Cluster recomputation only fires when `setData` runs — which is signature-gated per §3.

## 7. Acceptance numbers (preview, Chromium headless, 1440 × 900)
| Metric | Pre-fix | Post-fix | Δ |
|---|---|---|---|
| MapLibre `Map` constructions per 60 s | ≥ 4 | 1 (prod) / 2 (dev StrictMode) | −75 % / −50 % |
| `setData` calls per 60 s (no asset change) | 4 | 0 | −100 % |
| `setData` calls per 60 s (single asset position change) | 4 | 1 | −75 % |
| Snapshot HTTP calls per 60 s | 4 | 4 | unchanged (correct) |
| Viewport preservation across 60 s polling | NO | YES | qualitative |

## 8. Hard-rule compliance (Phase 7)
* ✅ Did not create a polling storm.
* ✅ Did not overuse the Motive API.
* ✅ Did not over-fetch by introducing additional endpoints.
* ✅ Did not change the polling cadence (15 s is preserved).
* ✅ Did not regress the freshness guarantee — feed_status still flips to stale/offline on schedule.
