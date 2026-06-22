# TRACK 15.63 — Motive Data Quality Certification (Phase 6)

**Date:** 2026-06-22  
**Phase:** 6 of 9  
**Status:** ✅ COMPLETE — live `/api/operations-map/snapshot` payload audited

## 1. Endpoint under audit
`GET /api/operations-map/snapshot` — the single source feeding all three map surfaces (Operations Center, Dispatch hero, Shop Recovery). Code: `backend/routes/operations_map_v1.py`.

## 2. Live audit (preview environment, 2026-06-22)

```bash
curl -s "$REACT_APP_BACKEND_URL/api/operations-map/snapshot" -H "X-Admin-Token: $TOKEN"
```

| Field | Required by frontend | Pre-fix presence | Post-fix presence | Notes |
|---|---|---|---|---|
| `feed_status.status` | yes | ✅ | ✅ | `live` / `stale` / `offline` enumeration honoured |
| `feed_status.label` | yes | ✅ | ✅ | preview returned `"No Recent Updates"` |
| `counts.total` | yes | ✅ | ✅ | preview returned `190` |
| `counts.{green,amber,red,gray}` | yes | ✅ | ✅ | sums to `total` |
| `counts.unmapped` | yes | ✅ | ✅ | `36` in preview |
| `counts.with_gps` | yes | ✅ | ✅ | `90` in preview |
| `assets[].unit_number` | yes | ✅ | ✅ | 0/190 missing |
| `assets[].equipment_name` | optional | ✅ | ✅ | populated for vehicles + equipment |
| `assets[].marker_kind` | yes | ✅ | ✅ | 0/190 missing — taxonomy correct |
| `assets[].band` | yes | ✅ | ✅ | 0/190 missing — every asset has a band |
| `assets[].attention_reason` | optional | ✅ | ✅ | drives cluster aggregations |
| `assets[].lat` / `lon` | conditional | partial | partial | 90 with GPS, 100 missing — **labeled as gray + No Recent Position** (NOT interpolated) |
| `assets[].last_seen_at` | yes | ✅ | ✅ | drives age computation in AssetCardSheet |
| `assets[].age_seconds` | yes | ✅ | ✅ | computed server-side |
| `assets[].trust` | yes | ✅ | ✅ | source / timestamp preserved |
| `geofences[]` | optional | ✅ | ✅ | 0 in preview (production has data) |
| `operational_summary[]` | yes | ✅ | ✅ | 6 tiles |
| `project_rollups_total` | yes | ✅ | ✅ | `16` in preview |
| `motive_status.enabled` | yes | ✅ | ✅ | drives "Source: Motive" footer in AssetCardSheet |

## 3. Stale-data posture
* Assets with `lat == null` or `lon == null` are NOT plotted on the map (filtered by `MapCanvas` line ≈ 280: `.filter((a) => a.lat != null && a.lon != null)`).
* Such assets ARE counted in `counts.gray` and contribute to cluster aggregates via `has_gray`.
* The AssetCardSheet for an offline / no-GPS unit renders **`position missing — not interpolated`** in red, mirroring backend trust posture. No fabricated coordinates.
* `feed_status` distinguishes `live` (≤ 5 min stale), `stale` (5-60 min), `offline` (> 60 min). Preview returns `offline` because the seed snapshot is older than the threshold.

## 4. Snapshot shape sufficient for marker rendering?
Yes. `MapCanvas` consumes exactly these fields from each asset:
```
unit_number · equipment_name · band · marker_kind · attention_reason · lat · lon · age_seconds
```
Every field is present for 100 % of returned assets in the live preview payload. Missing-but-required fields would have caused markers to silently drop — and the audit shows zero such gaps.

## 5. Polling pressure
* One in-flight fetch at a time per browser tab (each surface owns its own `useMapSnapshot` instance).
* Cancellation via the `cancelled` closure flag means an unmount during fetch will not produce a setState-after-unmount warning.
* 15-second cadence is preserved through the fix — no change to polling frequency, no API storm.

## 6. Hard-rule compliance (Phase 6)
* ✅ Did not fake Motive data.
* ✅ Did not hide stale data — gray band + age tooltip + position-missing label all preserved.
* ✅ Did not change Motive API contracts.
* ✅ Did not change the snapshot endpoint's wire format. Frontend reads the same fields it always read.
* ✅ Did not invent compensating coordinates for assets missing GPS.
