# TRENCH SAFETY — TEST ARTIFACT CLEANUP REPORT

**Date:** 2026-06-06
**Mode:** Narrow data-hygiene cleanup · NOT a Phase 4 build
**Scope:** Remove retired `TST-*` pytest artifacts from `trench_safety_assets` and `equipment_master`
**Verdict:** ✅ CLEANUP COMPLETE — 16 ROWS PURGED, 0 REAL ASSETS TOUCHED

---

## 1. Pre-cleanup state

`trench_safety_assets` total: **23** rows
- 7 MASCI fleet assets (TB-01 … TB-07)
- 16 retired pytest test artifacts (`TST-######`)

`equipment_master` rows with `category="Trench Safety"`: **23** (mirror parity)

## 2. Safety-criteria gate

Per directive — only records satisfying ALL of these were eligible:
1. `asset_id` starts with `TST-`
2. `is_active` is `False`
3. `operational_status == "Retired"`

A 4th implicit safeguard was added: candidate must NOT start with any protected fleet prefix (`TB-`, `EP-`, `SP-`, `HS-`). Any failure ⇒ ABORT without deleting anything.

**Verification script:** `/tmp/pre_phase4_cleanup.py`

```
candidate trench_safety_assets rows with asset_id ^TST- : 16
All 16 candidates passed safety verification.
Protected MASCI fleet present (TB-01..TB-07): 7 of 7
```

## 3. Candidate inventory (all 16 deleted)

| Asset ID | Status | is_active | Size | Color |
|---|---|---|---|---|
| TST-608246 | Retired | false | 4x12 | Red |
| TST-609268 | Retired | false | 4x12 | Yellow |
| TST-610071 | Retired | false | 4x12 | Yellow |
| TST-611186 | Retired | false | 4x12 | Yellow |
| TST-611822 | Retired | false | 4x12 | Yellow |
| TST-613052 | Retired | false | 4x12 | Yellow |
| TST-614353 | Retired | false | 4x12 | Yellow |
| TST-615310 | Retired | false | 4x12 | Yellow |
| TST-637830 | Retired | false | 4x12 | Red |
| TST-638874 | Retired | false | 4x12 | Yellow |
| TST-639701 | Retired | false | 4x12 | Yellow |
| TST-640843 | Retired | false | 4x12 | Yellow |
| TST-641491 | Retired | false | 4x12 | Yellow |
| TST-642745 | Retired | false | 4x12 | Yellow |
| TST-643996 | Retired | false | 4x12 | Yellow |
| TST-644937 | Retired | false | 4x12 | Yellow |

Each was created by `tests/test_trench_safety_phase2.py::tmp_asset` fixture (placeholder size `4x12`, no serial, no manufacturer, retired on teardown). None was a real MASCI fleet asset.

## 4. Delete operations executed

```
equipment_master rows deleted   : 16
trench_safety_assets rows deleted: 16
audit_events written            : 16  (kind=trench_asset_test_artifact_purged)
```

Each deletion left a forensic audit entry in `db.audit_events` for traceability:
```
{
  "kind": "trench_asset_test_artifact_purged",
  "asset_id": "TST-######",
  "actor": "system:pre_phase4_cleanup",
  "detail": {
    "reason": "Retired pytest test artifact removed per OMEGA pre-Phase-4 directive",
    "source": "/tmp/pre_phase4_cleanup.py"
  }
}
```

## 5. Post-cleanup state

```
trench_safety_assets total           : 7  ✅
equipment_master Trench Safety rows  : 7  ✅
TST-* in trench_safety_assets        : 0  ✅
TST-* in equipment_master            : 0  ✅
TB-01..TB-07 in trench_safety_assets : 7  ✅
TB-05 missing_serial_number flag     : true  ✅ (preserved)
TB-05 needs_review flag              : true  ✅ (preserved)
```

## 6. Pytest teardown remediation

**File modified:** `/app/backend/tests/test_trench_safety_phase2.py`

The `tmp_asset` fixture now performs a **two-step teardown**:

1. Retire via the public `/api/trench-safety/assets/{id}/retire` lifecycle (idempotent).
2. Hard-delete the rows from `trench_safety_assets`, `equipment_master`, and all 4 sub-collections (`_inspections`, `_repairs`, `_deployments`, `_qr_scans`) via a direct Mongo connection using the same `MONGO_URL`/`DB_NAME` env the backend uses.

This is the ONLY place in the test-suite permitted to write to the DB directly. Best-effort: never fails teardown.

**Verification of the new teardown:**

After re-running `pytest tests/test_trench_safety_phase2.py` (28/28 green, see `TRENCH_SAFETY_PRE_PHASE4_SEED_RECHECK.md`):
- `trench_safety_assets` count: 7 (no leftover TST-*)
- `equipment_master` Trench Safety count: 7 (no leftover TST-*)

The fixture self-cleans every run going forward.

## 7. What was NOT touched

- ❌ TB-01 through TB-07 (not modified, not deleted, all 7 still Available except TB-06 which remains in its pre-existing Inspection Hold state per Phase 2 lifecycle smoke).
- ❌ TB-05's `missing_serial_number` and `needs_review` flags — both still `true`.
- ❌ The existing `db.trench_boxes` manufacturer-reference collection (untouched).
- ❌ Any equipment_master row outside `category="Trench Safety"` (untouched).
- ❌ Phase 2 backend code, Phase 3 frontend code, route definitions, audit pipeline.
- ❌ No deployment.
- ❌ No new features.

## 8. Verdict

✅ **TEST ARTIFACT CLEANUP COMPLETE.**

- 16 retired pytest rows purged from both `trench_safety_assets` and `equipment_master`.
- 16 audit events written.
- Pytest fixture upgraded so future runs self-clean.
- All 7 MASCI fleet assets verified intact post-cleanup.
- Zero real assets touched.
- Zero existing workflows affected.
