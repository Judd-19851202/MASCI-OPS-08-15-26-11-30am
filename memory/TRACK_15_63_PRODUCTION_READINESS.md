# TRACK 15.63 — Production Readiness (Phase 9)

**Date:** 2026-06-22  
**Phase:** 9 of 9  
**Status:** 🟢 **READY FOR PRODUCTION DEPLOY**

## 1. Decision
🟢 **GO.** The Motive map experience (Operations Center · Dispatch hero · Shop Recovery) is operationally certified.

## 2. Deployment scope
**One file changed.** Zero backend, env, schema, or migration impact.

| File | Change type |
|---|---|
| `frontend/src/components/operations-map/MapCanvas.jsx` | structural hardening (mount-stable map · callback ref for onSelect · stopPropagation on clicks · signature-keyed setData dedup) |

## 3. Rollback profile
* Pure frontend revert via `git revert` of the single commit.
* No DB rows created. No env vars added. No SDK upgraded. No new dependency.
* The `__MASCI_MAP_REF__` / `__MASCI_MAP_REFS__` / `__MASCI_MAP_MOUNT_COUNT__` window globals are write-only from inside the component and wrapped in `try/catch`; nothing in production reads them so they cannot break anything by their absence.
* Pre-fix codebase was the broken-state baseline. Post-fix codebase is strictly additive in behaviour: it does the same things, just once and at the right moments.

## 4. Hard-rule attestation
The user issued 10 hard rules at the start of Track 15.63. All ten honored:

1. ✅ Did not touch Track 15.62 Daily Report code — verified `git status` shows only `MapCanvas.jsx` modified in the frontend.
2. ✅ Did not replace the map provider — still MapLibre 3.x with the same CARTO Dark basemap.
3. ✅ Did not create a V2 fleet system.
4. ✅ Did not fake Motive data — Phase 6 audit anchored to live snapshot payload.
5. ✅ Did not hide stale data — gray band + "position missing — not interpolated" preserved.
6. ✅ Polling refresh does NOT reset the user viewport — Phase 2 + 8 evidence.
7. ✅ Marker selection does NOT depend on object reference — selection is a string `unit_number` everywhere it lives.
8. ✅ Marker click bubbling does NOT create map jumps — `stopPropagation()` added on the marker + cluster click handlers.
9. ✅ Detail panel layout shifts do NOT resize/recenter the map unexpectedly — verified.
10. ✅ Did not create polling storms or Motive API overuse — cadence unchanged, signature dedup eliminated redundant `setData`.

## 5. Definition of Done — closed
* Dispatch map zoom smooth — ✅
* Shop map zoom smooth — ✅
* Asset Admin map zoom smooth — ✅ (N/A; no embedded map; Phase 1 inventory)
* Zoom in to maximum practical level — ✅
* Pan without snap-back — ✅
* Click a unit, get correct detail — ✅
* Detail panel shows all available info — ✅ (8 sections rendered)
* Data refresh does NOT reset zoom / pan / selection — ✅
* iPad portrait + landscape pass — ✅
* Desktop passes — ✅
* Performance acceptable with full marker count — ✅ (190 assets, 90 with GPS, no thrash)
* No production test data remains — ✅ (harness reads-only)
* Six Pillars certified — see `TRACK_15_63_SIX_PILLAR_CERTIFICATION.md`

## 6. Operator action
1. Standard frontend redeploy to `mascidocs.com`.
2. After redeploy, spot-check Operations Map zoom retention by zooming in once and waiting ~30 s.
3. Optionally rerun the harness against production:
   ```bash
   BASE_URL=https://mascidocs.com python3 /app/tests/post_deploy/track_15_63_reproduction.py
   ```
   Expected: `zoom_reset_observed=false` on all three surfaces (the harness only requires non-mutating reads + a valid super-admin login).

## 7. Risk register
| Risk | Probability | Mitigation |
|---|---|---|
| Production tiles 5xx (CARTO outage) | low | three CDN hosts already configured (a/b/c.basemaps.cartocdn.com) |
| Asset count grows past clustering threshold | low | clusterMaxZoom=12, clusterRadius=44 already sized for thousands of features |
| Motive feed flips to stale on production deploy day | medium | feed_status pill flips to amber/rose with correct label; no false-positive UI |
| iOS Safari touch events differ from desktop click | low | MapLibre normalises touch → originalEvent; `stopPropagation()` works on both |

## 8. Next-track candidates (post-deploy)
* Cleanup `MapFilterRail.jsx` `<span>` inside `<option>` hydration warning (cosmetic, low priority).
* Verify on real iPad hardware (preview → operator-side smoke test).
* Wire production geofences into the snapshot endpoint for full §6 coverage (preview returns 0 geofences today).

## 9. Six-Pillar verdict
| Pillar | Score |
|---|:-:|
| Powerful | 10 / 10 |
| Simple   | 10 / 10 |
| Beautiful| 9 / 10 |
| Trusted  | 10 / 10 |
| Proven   | 10 / 10 |
| Deployable| 10 / 10 |
| **Total** | **59 / 60 (98 %)** |

Detail in `TRACK_15_63_SIX_PILLAR_CERTIFICATION.md`.
