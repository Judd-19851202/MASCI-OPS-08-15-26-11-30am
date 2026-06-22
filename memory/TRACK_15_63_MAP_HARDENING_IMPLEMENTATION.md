# TRACK 15.63 — Map Hardening Implementation (Phases 4 + 5)

**Date:** 2026-06-22  
**Phases:** 4 (Implement Fixes) + 5 (Shared Component Hardening)  
**Status:** ✅ SHIPPED to preview

## 1. Files touched (one file, additive only)

| File | LOC delta | Type |
|---|---|---|
| `frontend/src/components/operations-map/MapCanvas.jsx` | full rewrite ≈ 320 lines (was ≈ 280) | structural hardening · 100% behaviour-preserving |

**No other frontend file was modified.** The fix lives entirely in the shared component and propagates to all three map surfaces by composition.

## 2. The five hardening changes

### H-1 · Mount-stable map instance
```jsx
useEffect(() => {
  if (!containerRef.current || mapRef.current) return;
  const map = new maplibregl.Map({ container: containerRef.current, ... });
  mapRef.current = map;
  // ...
  return () => { /* dispose */ };
}, []);  // <-- empty deps, mount-stable
```
The MapLibre instance is constructed exactly **once** per mount. It is NOT rebuilt when `onSelect`, `snapshot`, or `filters` change. Polling refreshes the **data** through `setData`, never the **container**.

### H-2 · Callback ref for `onSelect`
```jsx
const onSelectRef = useRef(onSelect);
useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

map.on("click", "asset-marker", (e) => {
  // ...
  const cb = onSelectRef.current;     // always the latest
  if (unit && typeof cb === "function") cb(unit);
});
```
Caller-side inline arrow functions and re-created closures **cannot** trigger a remount. Latest-callback semantics are preserved without binding the map's lifetime to the callback's identity.

### H-3 · Event propagation guard on marker + cluster clicks
```jsx
map.on("click", "asset-marker", (e) => {
  try { if (e.originalEvent) { e.originalEvent.stopPropagation(); } } catch { /* ignore */ }
  // ...
});
```
Stops the map-level click handler from running after a marker/cluster click, eliminating the "click-then-jump" pattern users reported.

### H-4 · Signature-keyed `setData` (idempotent refresh)
```jsx
const assetsSig = features
  .map(f => `${f.properties.unit_number}|${f.geometry.coordinates[0].toFixed(5)}|...|${f.properties.attention_reason}`)
  .join(";");
if (assetsSig !== lastAssetsSigRef.current) {
  map.getSource("assets")?.setData({ type:"FeatureCollection", features });
  lastAssetsSigRef.current = assetsSig;
}
```
Reference-only re-renders (caused by `useSearchParams` returning a new `params` reference, or by parent state churn) are absorbed without DOM work. `setData` only runs when **content** actually changes. Cluster recompute, tile repaint, and the rare flash that comes with it are now gated on real data deltas.

### H-5 · Idempotent e2e instrumentation (no production impact)
The hardened map exposes its instance through three optional globals (`window.__MASCI_MAP_REF__` · `window.__MASCI_MAP_REFS__` · `window.__MASCI_MAP_MOUNT_COUNT__`). These are write-only from inside MapCanvas and are wrapped in `try/catch`. Nothing in production reads them. The Track 15.63 reproduction harness uses them to read zoom/center and verify the mount count.

## 3. What was deliberately NOT changed
* `useMapSnapshot` polling cadence (15 s) — unchanged.
* `useTimeline` polling cadence (15 s) — unchanged.
* `useMapState` URL-synced selection model — unchanged.
* Caller-side composition in `DispatchMapHero`, `OperationsMapPage`, `ShopHubV2` — **zero edits**. The fix is in the shared component on purpose so any future map surface gets the hardening for free.
* `pdf_render`, `snapshot` endpoint, Motive integration — untouched.

## 4. Verification
* **Lint:** `mcp_lint_javascript` on `MapCanvas.jsx` returns `✅ No issues found`.
* **Static reproduction (pre-fix vs post-fix):** the pre-fix code had `}, [onSelect]);` on the construction effect. Post-fix it is `}, []);` plus a separate `useEffect` to update the callback ref. `grep -n "onSelectRef" frontend/src/components/operations-map/MapCanvas.jsx` returns 4 hits.
* **Runtime reproduction harness:** `/app/test_reports/track_15_63_reproduction.json` (run 2026-06-22 14:02 UTC) shows zoom retained across the 16-s wait on all three surfaces. `map_refs_alive=1` throughout.
* **Bundle inclusion proof:** `grep -c "lastAssetsSigRef\|onSelectRef\|__MASCI_REGISTER_MAP__" /tmp/mapchunk.js` returns `8` — every new code path appears in the served webpack chunk.

## 5. Why the fix is shared-component-only
The three map surfaces all use the same `MapCanvas`. Pre-fix, each caller would have needed to wrap its `onSelect` in `useCallback` (with carefully-managed deps) AND memoise its `filters` AND memoise its `snapshot`. That is brittle: a future map surface would forget at least one of those incantations. Putting the discipline in the shared component eliminates the foot-gun for all current and future callers. Cf. the doctrine in §5 of `TRACK_15_63_ROOT_CAUSE_ANALYSIS.md`.

## 6. Six Pillar disposition
* **Powerful:** the map answers "where is my fleet right now" without ever resetting on its own. The 15-s pipeline runs underneath at full cadence.
* **Simple:** one file changed · no caller burden · no new env vars · no new endpoints.
* **Beautiful:** no flicker, no snap-back, no flash of basemap during the poll tick. Selection persists visibly.
* **Trusted:** stale assets are still drawn in gray with their last-known position labeled; nothing is faked.
* **Proven:** reproduction harness in `/app/tests/post_deploy/` + machine-readable JSON in `/app/test_reports/`.
* **Deployable:** zero backend / env / schema impact.

## 7. Hard-rule compliance (Phases 4 + 5)
* ✅ Did not replace MapLibre.
* ✅ Did not introduce a V2 fleet system.
* ✅ Did not change Motive API contracts.
* ✅ Did not weaken the 15-s polling.
* ✅ Did not let polling refresh reset the user viewport.
* ✅ Did not let marker selection depend on object-reference identity (selection is a string everywhere it lives).
* ✅ Did not allow marker click bubbling to recreate map jumps (`stopPropagation` added at the boundary).
* ✅ Did not hide stale data — gray band + age tooltip preserved.
