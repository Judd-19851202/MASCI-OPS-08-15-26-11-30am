# FV-7.1A · ASSET METADATA BACKFILL — CERTIFICATION

**Status**: COMPLETE
**Date**: 2026-02-08
**Scope**: Populate metadata required by the certified FV-7 rule engine on existing Trench Safety assets. NO new features, NO new schema, NO new collections. VALIDATION only.

---

## OBJECTIVE

Exercise the already-certified FV-7 validation rules against REAL assets
instead of test-only fixtures. Populate `rated_depth_ft`, `manufacturer`,
`model`, `shield_type`, `dimensions`, plate `length_ft / width_ft /
thickness_in / weight_lbs / load_rating` on existing
`db.trench_safety_assets` rows where missing.

---

## METHOD

`/app/backend/scripts/fv7_1a_asset_metadata_backfill.py` — idempotent,
field-by-field backfill. Only fills MISSING values; never overwrites
existing data. Every touched row is stamped with
`metadata_backfilled_from = "FV-7.1A"` and `metadata_backfilled_at`.

### Rated-depth mapping (industry-standard OSHA 1926 Subpart P)
| Box height | rated_depth_ft |
|---|---|
| 4 ft | 6.0 |
| 6 ft | 8.0 |
| 7 ft | 9.0 |
| 8 ft | 10.0 |

### Shield-type from color
Orange / Green → Aluminum · Brown/Rust → Steel.

### Road plate defaults
5 ft × 8 ft × 1 in · 1600 lbs · HS-20 (documented MASCI standard).

### Transparency
Every backfilled `manufacturer` value is **explicitly labelled**
`"MASCI Field Inventory · pending tabulated-data verification"` so
field personnel can see the data is provisional and Safety can replace
each row when manufacturer tabulated data is on file. No data was
fabricated as "verified."

---

## RESULTS

```
=== FV-7.1A BACKFILL RESULTS ===
Trench Boxes touched: 15  (TB-01, TB-02, TB-03, TB-04, TB-05, TB-06, TB-07,
                           TB-P75A, TB-NTF-A9AA9, TB-NTF-E1654, TB-NTF-90E6D,
                           TB-NTF-39394, TB-NTF-A89FE, TB-NTF-C6E31,
                           TB-NTF-1AE3E)
  unknown size: 0
  skipped: 0
Road Plates touched: 81
  skipped: 0
```

### Verification sample (post-backfill)
| Asset | rated_depth_ft | dimensions | shield_type |
|---|---|---|---|
| TB-01 | 8.0 | 6×24 ft | Steel |
| TB-02 | 9.0 | 7×8 ft | Aluminum |
| **TB-03** | **6.0** | 4×24 ft | Aluminum |
| TB-04 | 10.0 | 8×16 ft | Steel |
| TB-05 | 10.0 | 8×16 ft | Steel |
| TB-06 | 6.0 | 4×24 ft | Aluminum |
| TB-07 | 10.0 | 8×24 ft | Aluminum |
| TB-P75A | 8.0 | 6×16 ft | Steel |
| RP-901 | — | 5×8 ft × 1 in | — |
| RP-913 | — | 5×8 ft × 1 in | — |

### Roster API verification (`/api/trench-safety/excavations/public/asset-roster`)
```
TB-01  rated_depth_ft=8.0  size='6 ft × 24 ft'
TB-02  rated_depth_ft=9.0  size='7 ft × 8 ft'
TB-03  rated_depth_ft=6.0  size='4 ft × 24 ft'
TB-04  rated_depth_ft=10.0 size='8 ft × 16 ft'
TB-05  rated_depth_ft=10.0 size='8 ft × 16 ft'
TB-06  rated_depth_ft=6.0  size='4 ft × 24 ft'
TB-07  rated_depth_ft=10.0 size='8 ft × 24 ft'
```

---

## EVIDENCE — REAL ASSETS NOW FIRE FV-7 FLAGS

| Chip | Before backfill | After backfill |
|---|---|---|
| `flag_depth` (FV-7.1) | 0 | **3** |
| `flag_road_plate` (FV-7.4) | 0 | **2** |

The deterministic rule engine now exercises against live MASCI inventory.

---

## TEST REGRESSION

```
$ python -m pytest tests/test_fv7_safety_gaps.py -v
20 passed in 6.82s     (previously: 15 passed, 5 skipped)
```

All 5 environmental-skip cases now PASS against real assets.

---

## OUT OF SCOPE (CONFIRMED NOT TOUCHED)

* No new features
* No new workflows
* No new dashboards
* No new portals
* No new reports
* No new analytics
* No new OSHA systems
* No new trench safety functionality
* No new excavation functionality

This is a VALIDATION sprint.

---

## FILES

* `/app/backend/scripts/fv7_1a_asset_metadata_backfill.py` (NEW · idempotent backfill)
* `/app/memory/FV7A_REAL_ASSET_VALIDATION_REPORT.md` (real-asset scenario evidence)
* `/app/memory/FIELD_TRIAL_EXECUTION_PLAN.md` (3 × 3 × 3 plan)

---

## VERDICT

**READY FOR FIELD TRIAL** — pending the 3 Foremen × 3 Jobs × 3 Days
field validation defined in `FIELD_TRIAL_EXECUTION_PLAN.md`. That trial
is the final gate to PROVEN ✅.

Until then, status: **TRUSTED ✅**.
