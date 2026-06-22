# TRACK 15.63 — Motive Map Surface Inventory (Phase 1)

**Date:** 2026-06-22  
**Phase:** 1 of 9  
**Mode:** static-analysis + code grep
**Status:** ✅ COMPLETE

## 1. Goal
Identify every map surface inside the MASCI Operations Platform that ingests Motive / Fleet GPS data and renders the MapLibre canvas. Surfaces beyond this list **do not** participate in the Track 15.63 hardening scope.

## 2. Inventory (canonical)

| # | Portal | Route | File | Composition | Selection model | Polling | Test ID |
|---|--------|-------|------|-------------|-----------------|---------|---------|
| 1 | Operations Center | `/operations-map` | `pages/OperationsMapPage.jsx` | `MapTopBar` · `MapOperationsBanner` · `ProjectIntelligenceStrip` · `MapFilterRail` · **`MapCanvas`** · `MapTimelineDock` · `AssetCardSheet` (when `?a=...` present) | `useMapState` URL-synced `?a=<unit_number>` (ID-based) | `useMapSnapshot({refreshMs:15000})` + `useTimeline({refreshMs:15000})` | `operations-map-page` · `ops-map-canvas` · `ops-map-asset-sheet` |
| 2 | Dispatch | `/dispatch-portal` (DispatchHub) | `components/DispatchMapHero.jsx` → `MapCanvas` | Hero embed: header strip · `MapCanvas` · counts strip · CTAs | Read-only navigation — click forwards to `/operations-map?asset=<unit>` | `useMapSnapshot({refreshMs:15000})` | `dispatch-map-hero` · `dispatch-map-canvas-wrap` |
| 3 | Shop | `/shop` (ShopHubV2) | `pages/ShopHubV2.jsx` → `MapCanvas` | Recovery panel: `MapCanvas` (clustered) + queue list | Local state `selectedUnit` (string `unit_number`, ID-based) | `useMapSnapshot({refreshMs:15000})` | `shop-recovery-map-wrap` |

### Shared engine
* `components/operations-map/MapCanvas.jsx` — **single** MapLibre 3.x engine. Wraps a CARTO Dark basemap with two GeoJSON sources (`assets` clustered · `geofences`) and a per-portal `onSelect` callback. Any fix to the shared component propagates to all three surfaces automatically.

### Shared hooks / state
* `lib/operations-map/useMapSnapshot.js` — 15-s polling fetch of `GET /api/operations-map/snapshot` (idempotent, non-blocking refresh, retains previous payload).
* `lib/operations-map/useMapState.js` — URL-synced filter + selection state (`useSearchParams`). Selection is **always** a string `unit_number`, never an object reference.

## 3. Surfaces audited and EXCLUDED from scope

These pages were grepped for MapLibre / Leaflet / Mapbox / "MapCanvas" and confirmed to have **no embedded map UI**, though they may consume operations-map data via tabular widgets:

* `pages/admin/AdminAssetAdmin.jsx` — tabular asset admin · no map.
* `pages/admin/AdminAssetMapping.jsx` — cleanup queue · no map.
* `pages/admin/AdminAssetSpineHealth.jsx` — spine health metrics · no map.
* `pages/admin/MappingCleanupTab.jsx` — admin cleanup UI · "mapping" refers to taxonomy mapping, not GIS.
* `pages/HrMotiveDrivers.jsx` · `pages/HrDriverProfile.jsx` — driver tables / profiles · no embedded map.
* `pages/operations-map/AssetCardSheet.jsx` — companion sidesheet to surface #1; no canvas of its own.
* `pages/SafetyDriverProfile.jsx` · `pages/DriverCommandProfile.jsx` — driver intel panels · no map.
* `components/MotiveOpsIntelPanel.jsx` · `components/ShopOpsIntelPanel.jsx` · `components/MotiveDriverIntelPanel.jsx` — KPI panels · no map.

The grep that produced this list:

```bash
grep -rn "MapCanvas\|maplibre\|leaflet\|mapbox" frontend/src \
  --include="*.jsx" --include="*.js" | grep -v node_modules
```

…returned **only** the three surfaces in §2.

## 4. PM / Executive surface check
There is **no** PM Command Center, Executive Overview, or Leadership Hub V2 map surface. PM/Exec pages link to `/operations-map` via `Link` components (verified via grep for `/operations-map`) but do not embed the canvas. No additional surfaces enter scope.

## 5. Conclusion
**Three** map surfaces · **one** shared engine. The Track 15.63 fix targets the shared `MapCanvas.jsx` plus per-portal callback stability in `DispatchMapHero.jsx`, `OperationsMapPage.jsx`, and `ShopHubV2.jsx`. Fixing the shared component covers all three surfaces.

## 6. Hard-rule compliance (Phase 1)
* ✅ Did not modify any code during this phase.
* ✅ Did not rewrite the fleet system.
* ✅ Did not replace the map provider.
* ✅ Did not change Motive API contracts.
* ✅ Did not invent additional surfaces — every entry above is anchored to a real `import MapCanvas` line in the codebase.
