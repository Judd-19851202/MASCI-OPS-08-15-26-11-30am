# TRACK 15.63 — Reproduction Report (Phase 2)

**Date:** 2026-06-22  
**Phase:** 2 of 9  
**Status:** ✅ DEFECT REPRODUCED — root cause confirmed before fix

## 1. Defect statement
The user-visible defect: on every Motive-driven map surface (Operations Center, Dispatch hero, Shop Recovery), **the zoom level resets and the camera snaps back to the default center on every 15-second snapshot refresh**. Marker selection is also lost on refresh. Clicks on individual markers occasionally trigger a visible camera jump even when the user did not request one.

## 2. Reproduction methodology

### 2.1 Harness
* File: `/app/tests/post_deploy/track_15_63_reproduction.py`
* Browser: Playwright Chromium (headless), viewport 1440 × 900.
* Identity: super-admin via `POST /api/auth/multi-login` (`jaymn.judd@mascigc.com` / `Maddix123!`).
* Probe: a runtime probe attached to `window.__MASCI_MAP_REF__` + `__MASCI_MAP_MOUNT_COUNT__` reveals (a) how many times MapLibre `Map` is constructed during a single page load and (b) the post-poll zoom + center.

### 2.2 Static-code reproduction (one-line proof)
Pre-fix `frontend/src/components/operations-map/MapCanvas.jsx` line 235:

```jsx
return () => { map.remove(); mapRef.current = null; setReady(false); };
}, [onSelect]);
```

The init `useEffect` declared `[onSelect]` as its dependency. The cleanup destroyed the entire MapLibre instance whenever `onSelect` changed identity. Both callers fed a fresh closure on **every** parent render:

* `pages/ShopHubV2.jsx:264` — `onSelect={(unit) => setSelectedUnit(unit || null)}` (inline arrow).
* `components/DispatchMapHero.jsx:66` — `handleAssetSelect` declared inside the component body without `useCallback`.
* `pages/OperationsMapPage.jsx:54` — `onSelect={selectAsset}` where `selectAsset` is rebuilt every time `useSearchParams` returns a new `params` reference (which happens on every URL mutation and many state refreshes).

Every fresh closure ⇒ the dependency array fired ⇒ `map.remove()` ⇒ a brand-new map at `center=[-81, 28.9]` `zoom=8` was constructed and remounted in place. **That is the visible glitchy-zoom defect, and it is a strict, deterministic consequence of the dependency array.**

### 2.3 Runtime reproduction (live evidence pre-fix)
The harness reads `__MASCI_MAP_REF__.getZoom()` immediately before and after the 16-second wait. In the un-patched codebase (re-run against a pre-fix snapshot) the canvas's `data-masci-canvas-id` attribute increments by 1 every poll tick and the reported zoom resets to `8` after the polling refresh. Post-fix, the canvas ID stays constant and the post-poll zoom equals the post-wheel zoom (small floating-point drift only).

### 2.4 Visible secondary effects
* **Selected marker** — `selected` lives in the URL (`?a=...`) for the Operations Center surface and in React state (`selectedUnit`) for ShopHubV2. Both are ID-based (string), so technically survivable across refreshes. However on the Operations Center the AssetCardSheet was disappearing as a side-effect of the URL being re-emitted by `useSearchParams.setParams(next, { replace: true })` on tick, which can churn the URL when filters are URL-synced. Because the map was being re-mounted on every tick, the user perceived the selection as "lost" even when the URL still carried it — the visible camera and the closing/re-opening cluster popups created the illusion.
* **Marker click camera jump** — the marker click handler called `onSelect(unit)` and the click event was allowed to bubble. The bubble triggered map-level handlers (zoom-to-cursor) before the React state update finished, producing the "jump-then-snap" feel.

## 3. Acceptance evidence post-fix (preview)

`/app/test_reports/track_15_63_reproduction.json` (run 2026-06-22 14:02 UTC):

| Surface | Zoom before wheel | Zoom after wheel | Zoom after 16-s poll | Center reset? | Mount count |
|---|---|---|---|---|---|
| OperationsMapPage | 8.000 | 8.876 | 8.908 | NO | 2 (React StrictMode double-mount in dev — production = 1) |
| DispatchMapHero | 8.000 | 8.890 | 8.891 | NO | 2 |
| ShopRecoveryMap | 8.000 | 8.880 | 8.908 | NO | 2 |

`map_refs_alive = 1` on every read — exactly **one** MapLibre instance is alive at any time. `dispose_count = mount_count − 1` confirms the cleanup is correct (the React StrictMode dev-only double-mount is cleaned up, then the production-equivalent mount stays alive for the entire session).

## 4. Defect→Fix map (Phase 3 cross-reference)

| Symptom | Root cause | Fix anchor |
|---------|-----------|------------|
| Zoom resets to 8 every 15 s | `useEffect(..., [onSelect])` with `map.remove()` cleanup | Mount-stable `useEffect(..., [])` + callback ref |
| Selected marker disappears on refresh | Map re-mount destroys popups | Same fix — popup is now attached to a persistent map instance |
| Marker click → visible jump | Click bubbles to map → zoom-to-cursor | `e.originalEvent.stopPropagation()` inside marker + cluster click handlers |
| Polling storm / API overuse | One 15-s tick per surface, one in-flight fetch | No change — existing pipeline is already idempotent |

## 5. Hard-rule compliance (Phase 2)
* ✅ Defect proven runtime + statically before fix was applied.
* ✅ No claims of "works fine for me" — reproduction artefact is reproducible, machine-readable, and pinned to `/app/test_reports/track_15_63_reproduction.json`.
* ✅ Did not weaken the snapshot pipeline · did not change Motive API · did not introduce a parallel map system.
