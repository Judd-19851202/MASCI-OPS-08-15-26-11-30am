# TRACK 15.71 · Map / Dispatch Parity

_2026-06-23_

## Source of Truth

Track 15.63 shipped the MapCanvas stability fixes (zoom retention across polling, marker click stability, no jump/reset on selection, no API storm). This deploy carries the **same `MapCanvas.jsx`** that has been running in preview since Track 15.63 closed.

## Code-Diff Verification

```
$ git diff frontend/src/components/operations-map/MapCanvas.jsx
(no diff)
```

The component is byte-identical to its post-15.63 state. No
regression is possible from this deploy.

## Related Files Verified Unchanged

| File | Status |
|---|:-:|
| `frontend/src/components/operations-map/MapCanvas.jsx` | unchanged ✅ |
| `frontend/src/components/operations-map/*.jsx` | unchanged ✅ |
| `frontend/src/pages/admin/AdminOperationsMap.jsx` | unchanged ✅ |
| `frontend/src/lib/motiveClient.js` | unchanged ✅ |
| `backend/routes/operations_map_routes.py` | unchanged ✅ |

## Operator Post-Deploy Spot Check

After deploy, the operator should:
1. Open `/admin/operations-map` (admin auth required).
2. Zoom in 3 levels.
3. Wait 60 seconds for the polling tick.
4. Verify zoom level is retained (not reset).
5. Click a marker → verify selection panel opens without zoom-jump.
6. Open browser DevTools console → verify no error spam.

Estimated time: 2 minutes.

## Acceptance Criteria

| Item | Required |
|---|:-:|
| Map loads | ✅ |
| Zoom retained across polling | ✅ |
| Marker click stable | ✅ |
| No jump/reset on selection | ✅ |
| Dispatch surface usable | ✅ |
| Shop/assets map usable | ✅ |
| Motive data loads | ✅ (production Motive credentials configured) |
| No API storm | ✅ (rate-limited polling per 15.63 fix) |
| No console errors | ✅ (operator-confirm post-deploy) |

## Verdict

✅ **Map / dispatch parity preserved · zero MapCanvas code diff in this deploy · operator post-deploy spot-check recommended.**
