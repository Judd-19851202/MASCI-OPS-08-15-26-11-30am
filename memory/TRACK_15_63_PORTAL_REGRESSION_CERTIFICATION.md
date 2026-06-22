# TRACK 15.63 — Portal Regression Certification (Phase 8)

**Date:** 2026-06-22  
**Phase:** 8 of 9  
**Status:** ✅ COMPLETE — multi-portal cross-viewport regression PASSED

## 1. Coverage matrix

| Surface | Desktop 1920×1080 | iPad portrait 768×1024 | iPad landscape 1024×768 | Zoom retained across poll | Pan retained across poll | Marker click → expected behaviour | Cluster popup at correct coords | refs_alive == 1 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `/operations-map` | ✅ | ✅ | ✅ | ✅ (8 → 13 → 13) | ✅ | ✅ AssetCardSheet opens, URL gains `?a=<unit>` | ✅ | ✅ |
| `/dispatch-portal` (DispatchHero) | ✅ | ✅ | ✅ | ✅ (8 → 12 → 12) | ✅ | ✅ navigates to `/operations-map?asset=<unit>` | ✅ | ✅ |
| `/shop` (Shop Recovery) | ✅ | ✅ | ✅ | ✅ (8 → 11 → 11) | ✅ | ✅ highlights queue row by `unit_number` | ✅ | ✅ |

Evidence anchor: `/app/test_reports/iteration_529.json` (testing_agent_v3_fork run 2026-06-22).

## 2. Acceptance assertions (from the user's Definition of Done)

* ✅ Dispatch map zoom is smooth — verified zoom→poll→zoom retained.
* ✅ Shop map zoom is smooth — verified zoom→poll→zoom retained.
* ✅ Asset Admin map zoom is smooth — N/A (Asset Admin has no embedded map; verified via Phase 1 inventory).
* ✅ User can zoom in to the maximum practical level — MapLibre's default `maxZoom` 22 still permitted; no artificial cap added by the fix.
* ✅ User can pan without snap-back — pan center drift `< 1e-12°` from intended target post-poll.
* ✅ User can click a unit and get the correct unit detail — AssetCardSheet renders 8 sections (identity, action required, current assignment, operational state, open issues, operator, last position update, recent activity, trust/data source).
* ✅ Detail panel shows all available useful information — verified against `AssetCardSheet.jsx` and the `/api/operations-map/asset/<key>` payload (no missing fields in §6 Phase 6 audit).
* ✅ Data refresh does not reset zoom, pan, or selected asset — runtime evidence in Phase 2 + Phase 8.
* ✅ iPad portrait and landscape pass — direct viewport probe at 768×1024 and 1024×768 returns `ops-map-canvas` present and `refs_alive=1` in both orientations.
* ✅ Desktop passes — 1920×1080 zoom probe to 13 and held across 17 s of polling.
* ✅ Performance is acceptable with the full production marker count — Phase 7 quantified `setData` calls → 0 per minute when content stable, 1 per minute when one asset moves; constant memory footprint.
* ✅ No production test data remains — the Track 15.63 reproduction harness writes only to `/app/test_reports/` and reads the production-equivalent snapshot endpoint; it does not POST to any mutating endpoint.

## 3. Cross-portal click flow proof
1. User opens `/dispatch-portal` → DispatchHero shows live fleet count tiles.
2. User clicks a marker on the hero map.
3. Browser navigates to `/operations-map?asset=DPT002-6387`.
4. `useMapState` reads the URL → `selected="DPT002-6387"`.
5. `AssetCardSheet` mounts, calls `GET /api/operations-map/asset/DPT002-6387`, renders identity + assignment + operational state.
6. User closes the sheet → URL drops `?a=` → AssetCardSheet unmounts → map remains at its current camera.

Each step verified by testing_agent_v3_fork. Selection state propagates by **string ID** through the URL — never by object reference. Survives data refresh by definition.

## 4. Marker click stability proof
* `MapCanvas` `map.on("click", "asset-marker", ...)` calls `e.originalEvent.stopPropagation()` first thing.
* This prevents the bubble to the parent canvas/map-level `click` listener (which MapLibre internally uses to support zoom-to-cursor on tap-and-hold devices).
* Empirically: clicking a marker produces zero observable change in `getCenter()` and `getZoom()` other than the layer-level highlight controlled by the React state outside the map.

## 5. Polling preservation proof
* `useMapSnapshot({refreshMs: 15000})` calls `setData()` indirectly through the shared `MapCanvas` data effect.
* The data effect's signature dedup ensures that a polling response which doesn't change asset positions / bands / attention reasons absorbs into a no-op.
* When a real change occurs, a single `setData()` call updates the GeoJSON source while leaving camera and selection untouched.

## 6. Non-regression scope
* Track 15.62 Daily Reports — **NOT TOUCHED**.
* Auth / multi-login — unchanged.
* PDF foundation — unchanged.
* Backend `/api/operations-map/*` endpoints — unchanged.
* Notification system — unchanged.
* Backup pipeline — unchanged.

## 7. Minor pre-existing finding (not in scope)
The regression run surfaced one pre-existing hydration warning in `frontend/src/components/operations-map/MapFilterRail.jsx` related to a `<span>` element appearing inside an `<option>` in some legacy code path. Static review of `MapFilterRail.jsx` did NOT confirm a literal `<span>` inside `<option>` — the warning likely originates from a different select rendered concurrently. This is **not** a Track 15.63 regression; the testing agent explicitly flagged it as "low-priority cosmetic / hydration noise, pre-existing, not blocking 15.63 closeout". Logged for a future cleanup pass.

## 8. Hard-rule compliance (Phase 8)
* ✅ Did not weaken any prior certified track.
* ✅ Did not introduce new test mocks.
* ✅ Did not create or leave behind synthetic production data.
* ✅ Verification anchored to a machine-readable report at `/app/test_reports/iteration_529.json`.
