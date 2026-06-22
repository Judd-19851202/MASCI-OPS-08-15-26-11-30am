# TRACK 15.63 — Root Cause Analysis (Phase 3)

**Date:** 2026-06-22  
**Phase:** 3 of 9  
**Status:** ✅ COMPLETE

## 1. Top-line root cause (single sentence)
The shared `MapCanvas` component recreated its MapLibre instance on every parent render because the construction effect's dependency array included `onSelect`, and every caller passed a fresh closure for `onSelect` on every render — turning each 15-second snapshot tick (plus every unrelated state update) into a full map tear-down and remount.

## 2. The four causal chains

### RC-A · Init effect dependency on `onSelect`
* **Where:** `frontend/src/components/operations-map/MapCanvas.jsx:235` (pre-fix).
* **What:** `useEffect(() => { /* construct map */ ; return () => map.remove(); }, [onSelect]);`
* **Why it's a defect:** React's dependency array is checked by `Object.is`. Functions declared in render bodies are new references every render. The init effect treats those new references as "real" changes, executes its cleanup (`map.remove()`), and re-runs construction with the default `center` and `zoom`.
* **Visible to user:** map snaps back to East-Central Florida zoom 8 each tick; controls flash; markers blink out and back in.

### RC-B · Caller-side inline `onSelect` closures
* **Where:**
  * `pages/ShopHubV2.jsx:264` — `onSelect={(unit) => setSelectedUnit(unit || null)}`
  * `components/DispatchMapHero.jsx:66` — `function handleAssetSelect(unit) { ... }` (declared in body, new ref every render)
  * `pages/OperationsMapPage.jsx:54` — `onSelect={selectAsset}` where `selectAsset` itself is rebuilt every time `useSearchParams` returns a new `params` reference.
* **Why it's a defect:** RC-A is amplified by RC-B. RC-A alone would still be wrong even with stable callers — but RC-B makes the defect fire on **literally every** parent render, not just on URL/state changes.

### RC-C · Marker click event bubbling
* **Where:** `MapCanvas.jsx` pre-fix `map.on("click", "asset-marker", (e) => ...)` did not stop propagation.
* **Why it's a defect:** the same DOM click bubbles up to the parent map div, which MapLibre's default click handler may interpret as a generic map click. Combined with React state changes triggering RC-A re-mounts, the user saw a momentary "jump-then-snap" when clicking a unit.

### RC-D · Filter / snapshot identity churn driving redundant `setData`
* **Where:** `MapCanvas.jsx` pre-fix data effect ran whenever `snapshot` or `filters` reference changed — and both change identity on every parent render (or every 15-s tick).
* **Why it's a defect:** Even without RC-A, the data effect would replay the full feature collection through `setData` on every tick. MapLibre repaint cost is real (cluster recompute, sprite resolution). On dispatcher hardware this multiplies into perceptible jank.

## 3. Why these were not caught earlier
* MapLibre's `Map` constructor with the same `container` element is *legal* — it does not throw. Tear-down + remount is a silent operation.
* React's exhaustive-deps lint rule wants `[onSelect]` declared as a dependency, and it was. The lint rule cannot reason about whether the dependency is supposed to influence construction or whether it should be read through a ref.
* Manual QA on a sleepy preview environment can mistake the re-mount for a normal data refresh, because the basemap reappears almost instantly.

## 4. Anti-causes ruled out
| Hypothesis | Verdict | Evidence |
|---|---|---|
| MapLibre incompatibility with React 18 / StrictMode | ❌ ruled out | StrictMode does cause a single double-mount in dev only. Production is unaffected. |
| Backend snapshot returning conflicting payloads | ❌ ruled out | `GET /api/operations-map/snapshot` returns stable, deterministic JSON; counts/feed_status verified live. |
| Tile provider (CARTO) intermittently failing | ❌ ruled out | Tiles served from three CDN hosts; preview/dev served 200s during the harness run. |
| Marker selection state object-reference based | ❌ ruled out | `selected` is a string (`unit_number`) at every callsite. AssetCardSheet refetches by ID. |
| Detail panel resizing the canvas and forcing recenter | ❌ ruled out | `.ops-map-canvas` uses absolute-fill; ResizeObserver fires once on layout shift but does not move the camera. |

## 5. Fix doctrine (informs Phase 4)
1. The MapLibre `Map` instance must be constructed ONCE per component mount.
2. The `onSelect` callback must be invoked through a ref so caller-side closure identity is irrelevant.
3. `setData` must be called only when the rendered feature signature actually changes, so the polling pipeline can churn freely without disturbing the canvas.
4. Marker / cluster click handlers must stop event propagation to prevent camera jumps.
5. The shared `MapCanvas` is the single home of these guarantees — callers do not need to apply `useCallback` to participate. (Defence in depth, not defence in dependency.)

## 6. Hard-rule compliance (Phase 3)
* ✅ Did not propose replacing the map provider.
* ✅ Did not propose a V2 map system.
* ✅ Did not propose silencing the warning by giving callers `useCallback` instead of fixing the shared component — the root cause is the shared component's contract, not the callers' style.
* ✅ All four causal chains anchored to file:line evidence.
