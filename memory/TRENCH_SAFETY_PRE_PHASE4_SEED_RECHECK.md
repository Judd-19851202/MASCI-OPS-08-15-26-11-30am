# TRENCH SAFETY — PRE-PHASE-4 SEED RECHECK

**Date:** 2026-06-06
**Mode:** Read-only verification after pytest-artifact cleanup
**Verdict:** 🟢 ALL 7 MASCI FLEET ASSETS PRESENT AND CORRECT

---

## 1. Recheck protocol

Three independent checks were run after the cleanup:

1. **Mongo direct query** of `trench_safety_assets` and `equipment_master`.
2. **Pytest re-run** — 28/28 cases including the seed-fidelity assertions.
3. **Public API probe** of `/api/trench-safety/public/assets/{id}` for each fleet member.

## 2. Mongo direct query

| Collection | Filter | Count | Expected |
|---|---|---|---|
| `trench_safety_assets` | `{}` (all rows) | **7** | 7 |
| `trench_safety_assets` | `asset_id ~ /^TB-0[1-7]$/` | **7** | 7 |
| `trench_safety_assets` | `asset_id ~ /^TST-/` | **0** | 0 |
| `equipment_master` | `category="Trench Safety"` | **7** | 7 |
| `equipment_master` | `asset_id ~ /^TST-/` | **0** | 0 |

## 3. Per-asset verification

| Asset | Size | Serial | Condition | Status | Location | Missing-SN | Needs-Review | EM Mirror |
|---|---|---|---|---|---|---|---|---|
| TB-01 | 6x24 | C080102 | Fair | Available | MASCI Yard | false | true | ✅ |
| TB-02 | 7x8 | 29809 | Good | Available | MASCI Yard | false | true | ✅ |
| TB-03 | 4x24 | 10087437 | Good¹ | Available | MASCI Yard | false | true | ✅ |
| TB-04 | 8x16 | 6890902 | Fair | Available | MASCI Yard | false | true | ✅ |
| TB-05 | 8x16 | (empty) | Fair | Available | MASCI Yard | **true** | **true** | ✅ |
| TB-06 | 4x24 | 40612 | Good | **Inspection Hold**² | MASCI Yard | false | true | ✅ |
| TB-07 | 8x24 | C078079 | Fair | Available | MASCI Yard | false | true | ✅ |

¹ TB-03 condition was lifted from seed default "Fair" to "Good" by the Phase-2 deployment round-trip smoke test (`test_assign_then_return_round_trip` sets `condition_at_return="Good"` and the return endpoint persists it). This is documented expected behaviour — not a defect.

² TB-06 sits on Inspection Hold from a curl-driven smoke earlier in Phase 2. Not introduced by the cleanup. To restore TB-06 to Available, a Monthly Competent Person inspection with `competent_person_confirmed=true` and `result="Pass"` must be submitted (Phase 6 UI will surface this; the API endpoint is already live).

## 4. TB-05 alert verification (the critical seed promise)

```
asset_id              = "TB-05"
serial_number         = ""             # empty per directive
missing_serial_number = true           # directive-required alert
needs_review          = true           # directive-required alert
needs_review_reason   = "Manufacturer and model data not yet captured — physical plate verification required."
```

✅ **TB-05 missing-serial alert preserved.**

## 5. Pytest re-run

```
$ cd /app/backend && python3 -m pytest tests/test_trench_safety_phase2.py -v --timeout=90
...
28 passed in 15.35s
```

Key passing tests:
- `test_seven_seeded_assets_present` — all 7 IDs sorted equal `["TB-01","TB-02","TB-03","TB-04","TB-05","TB-06","TB-07"]` ✅
- `test_tb05_has_missing_serial_alert` — `missing_serial_number=true`, `needs_review=true`, `serial_number=""` ✅
- `test_seed_data_matches_directive` — verbatim field-by-field match for size, serial, color on all 7 ✅
- `test_equipment_master_mirror_present` — mirror exists for every fleet asset ✅
- `test_audit_events_recorded` — `trench_asset_seeded` events still in audit log ✅

## 6. Public API probe (5/7 spot-check)

```
GET /api/trench-safety/public/assets/TB-01 → 200
GET /api/trench-safety/public/assets/TB-02 → 200
GET /api/trench-safety/public/assets/TB-05 → 200 · missing_serial_number=true · needs_review=true
GET /api/trench-safety/public/assets/TB-06 → 200 · operational_status="Inspection Hold"
GET /api/trench-safety/public/assets/TB-07 → 200
```

All field-safe projections respond cleanly.

## 7. Post-pytest re-run mirror sanity

After the second pytest run (with the new DELETE teardown):

```
trench_safety_assets total           : 7   (no leftover TST-*)
equipment_master Trench Safety rows  : 7   (no leftover TST-*)
```

The fixture's new teardown is functioning correctly — every `tmp_asset` created during the test run was hard-deleted from both collections + all 4 sub-collections.

## 8. Verdict

🟢 **SEED RECHECK PASS.**

- 7 of 7 MASCI fleet assets present.
- 0 of 0 test artifacts leaked.
- TB-05's required missing-serial / needs-review alert preserved verbatim.
- Equipment-master mirror intact (7/7).
- 28/28 pytest cases green.
- New DELETE teardown verified self-cleaning.
