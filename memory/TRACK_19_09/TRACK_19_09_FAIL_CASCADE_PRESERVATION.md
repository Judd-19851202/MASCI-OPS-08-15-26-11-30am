# Track 19.09 · Fail-Cascade Preservation Verification

**Purpose**: Prove that the operational forms modernization in Track 19.09 has NOT altered the fail-cascade chain documented by the Track 19.08 audit (`TRACK_19_08_AUDIT/07_FAIL_CASCADE_ANALYSIS.md`).

## Preservation matrix

| Component | Pre-19.09 behaviour | Post-19.09 behaviour | Verdict |
| --- | --- | --- | --- |
| Equipment Pre-Op FAIL item → `fleet_defects` insert | Unchanged | Unchanged (no backend touched) | ✅ preserved |
| Equipment Pre-Op FAIL note requirement | Required, ≥10 chars | Required, ≥10 chars | ✅ preserved |
| Equipment Pre-Op FAIL photo requirement | Required | Required | ✅ preserved |
| Equipment Pre-Op critical-fluid submit blocker | Fires modal + returns from submit | Same | ✅ preserved |
| Equipment Pre-Op major-safety OOS trigger | Fires + returns from submit | Same | ✅ preserved |
| DVIR defect → `fleet_defects` insert per item | Unchanged | Unchanged | ✅ preserved |
| DVIR OOS (any high-severity defect) → `fleet_status.oos` upsert | Unchanged | Unchanged | ✅ preserved |
| DVIR `blockReason` local guard | Fires + returns from submit | Same | ✅ preserved |
| Shop workflow (`open → acknowledged → assigned → in_progress → repaired → cleared`) | Untouched | Untouched | ✅ preserved |
| Dispatch OOS management (`/dispatch/fleet/units/{unit_number}/oos`) | Untouched | Untouched | ✅ preserved |
| Notifications: `defect_open`, `defect_assigned`, `defect_cleared`, `fleet-unit-oos`, `fleet-unit-return-to-service` | Untouched | Untouched | ✅ preserved |
| `schedule_auto_email` for `dvir`, `equipment-inspection`, `fleet-defect` workflow keys | Untouched | Untouched | ✅ preserved |
| PDF renderers (`render_dvir_pdf`, `render_equipment_inspection_pdf`) | Untouched | Untouched | ✅ preserved |
| Trust-Spine correlation ids | Untouched | Untouched | ✅ preserved |
| `audit_events` writes on submit + on state transitions | Untouched | Untouched | ✅ preserved |
| Historical immutability (no PATCH / DELETE on `fleet_audit` / `equipment_inspections` records) | Untouched | Untouched | ✅ preserved |
| Motive / Samsara integration sync | Untouched | Untouched | ✅ preserved |

## The camera gate is NOT a defect

By design (see `TRACK_19_09_CAMERA_OBSTRUCTION_GATE.md` §4), the camera obstruction gate is a **pre-submit hard block**, not a fail-cascade branch. This means:

* An unanswered / obstructed camera **prevents submit entirely** — the operator cannot generate a record until they answer the question and physically clear the obstruction.
* Because no record is generated, no downstream cascade fires — no shop ticket, no OOS, no email, no PDF, no audit event.
* This is intentional: an obstructed camera is a trivial field-fix; a broken camera housing (which cannot be cleared) is a standard FAIL on the existing camera-item in the checklist, which DOES fire the cascade normally.

## Regression evidence

The Track 19.08 forms-audit snapshot lock (`test_track_19_08_forms_audit_snapshots.py`, 112 assertions) verifies that every documented critical route, collection, email workflow, and PDF renderer is still present. That entire suite is GREEN post-19.09.

Combined `19.03 + 19.04 + 19.05 + 19.06 + 19.06 Amendment + 19.07 + 19.08 + 19.09` regression: **373 / 373 pytest assertions GREEN**.

## Manual verification checklist for redesign leads

Before shipping Track 19.09 to production, confirm on the preview environment:

* [ ] Equipment Pre-Op FAIL on a critical-fluid item still triggers the fluid-loss modal.
* [ ] Equipment Pre-Op FAIL on a major-safety item still triggers the OOS modal.
* [ ] Equipment Pre-Op FAIL still requires ≥10-char description + photo.
* [ ] DVIR FAIL still produces `fleet_defects` records (check admin console + Motive sync if enabled).
* [ ] Shop portal still receives new defects with correct severity.
* [ ] Camera gate + defect FAIL can coexist on the same submit (camera clear + defect elsewhere → normal cascade; camera obstructed + any state → submit blocked).
* [ ] All existing autosave / draft-restore behaviour still works with the new camera fields.
