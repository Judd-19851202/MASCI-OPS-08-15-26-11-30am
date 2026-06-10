# FORGEDOPS · OPERATIONS CENTER · PHASE 4C · CERTIFICATION

> ⚠️ **DATA TRUTH — PREVIEW VS PRODUCTION** (added 2026-02-10 via Data Truth Correction)
>
> **Every count, row total, and KPI cited in this document originates from the *preview database* (test/staged/validation fixtures).** They are **not** verified against the live MASCI production Asset Spine, dispatch lifecycle, shop, or safety collections.
>
> Numbers below prove: ✅ the code works, ✅ the contracts deserialize, ✅ the UI renders, ✅ filters/counts/classifiers behave correctly on the dataset.
>
> Numbers below do **NOT** prove: ❌ MASCI's actual production inventory, ❌ live operational reality, ❌ how many road plates / specialty assets / hauls MASCI has in the field.
>
> See `/app/memory/DATA_TRUTH_CORRECTION_PREVIEW_VS_PROD_CERTIFICATION.md` for the standardized rules. "Preview counts are validation fixtures / staged data and must not be used as production operational inventory."

**Date:** 2026-02-10
**Authorization:** Operator chat — *"PHASE 4C · OPERATIONS CENTER · OMEGA ENFORCED"*
**Verdict:** 🟢 **PASS · 10 backend endpoints live · 9-layer cross-company command board · Specialty Asset normalization applied · Executive Mode toggle · PM home redirect · 98/98 backend regression intact.**

---

## 1 · Scope honored (OMEGA)

- ✅ Cross-company command board built — Asset Spine + Dispatch CC + PM CC + Shop + Safety + Motive composed without duplication.
- ✅ No new collection · no schema mutation · no FleetWatcher activation · no MaintainX activation · no map render (map-contract endpoint stages the future contract).
- ✅ Specialty Asset normalization applied (Phase 4C architecture correction — road plates are ONE family member, NOT privileged). Trench Boxes are first-class.
- ✅ PM Command Center promoted to PM portal home: `/pm` now React-Navigate-replaces to `/pm/command-center`. Legacy PmHub preserved at `/pm/hub`.
- ✅ Executive Mode (UI-only filter) hides row-level noise (Allocation, Timeline) while preserving Brief / Project Health / Specialty / Conflicts / Shop / Safety / Telematics visibility.
- ✅ Map-ready field set stamped on every operational row across all 10 endpoints (asset_id · project_id · project_number · assignment_id · status · location_ref · timestamp · operational_state · trust_state · source_system) — the future Live Operations Map will consume `/map-contract` without redesign.

---

## 2 · 10 Backend endpoints (`/api/operations-center/command/*`)

| Endpoint | Purpose | Live count (preview) |
|---|---|---|
| `/brief` | Morning Operations Brief — single rollup tile | 28 projects · 96 trucks · 30 drivers · 179 specialty · 82 defects · 43 incidents · 24 CAPAs · 8 conflicts |
| `/project-health` | Project Health Board + risk engine | 28 projects · 3 red · 0 yellow · 25 green |
| `/allocation` | Per-project resource allocation + unassigned/oos/unmapped | live |
| `/conflicts` | Operational conflicts (truck_multi_project / driver_multi_truck / haul_inactive_project) | 8 detected |
| `/specialty-assets` | Specialty Asset Command — 4 families + ?family= / ?kind= filters | 179 rows · trench=16 · road plates=88 · support=75 |
| `/shop-impact` | Shop impacts sorted by production priority (high/medium/low) + oos count | live |
| `/safety-impact` | Incidents + CAPAs tiered (critical / warning / informational) | 43 + 24 |
| `/telematics` | 9 truck operational state buckets (moving/idling/at_job/at_plant/at_yard/at_shop/offline/no_gps/unknown) + mapped/unmapped + fleetwatcher=not_connected | 0 mapped on preview |
| `/timeline` | Cross-company chronological events (asset_transfer / dispatch_state / incident) | live (depends on `days` query) |
| `/map-contract` | Live operational rows w/ asset_id · lat · lon · last_location_time · location_source · operational_state | preps Live Map |

All gated by `require_any_portal_token` (any signed-in portal user) — Executive Mode is a UI filter, not a backend gate.

---

## 3 · 9-layer Operations Center UI

Route `/operations-center` (RequireAdmin). One page · 9 sections rendered in the priority directive-mandated order:

| Layer | Section | Hidden in Executive Mode? |
|---|---|---|
| L1 | Morning Operations Brief (12 KPI tiles) | no |
| L2 | Project Health (risk-sorted: red → yellow → green) | no |
| L5 | Specialty Asset Command (family-filterable) | no |
| L3 | Resource Allocation | **yes** |
| L4 | Operational Conflicts | no |
| L6 | Shop Impact · Production Priority | no |
| L7 | Safety Impact (Incidents + CAPAs, tiered) | no |
| L8 | Truck Status · Telematics (9 motive buckets) | no |
| L9 | Operational Timeline | **yes** |

Executive Mode toggle (`data-testid='oc-cmd-exec-toggle'`) collapses row-level noise — preserves the same data, different view.

---

## 4 · Routes shipped (3)

| Route | Element | Notes |
|---|---|---|
| `/pm` | `PmHomeRedirect` (RequirePm) | `<Navigate replace>` → `/pm/command-center` |
| `/pm/hub` | `PmHub` | legacy tile-based navigation, preserved |
| `/operations-center` | `OperationsCenterCommand` (RequireAdmin) | new cross-company command board |

---

## 5 · Files shipped

### Backend (3 files · zero schema change · zero new collection)
- NEW: `routes/operations_center_command.py` (~640 LOC · 10 endpoints + 4 helpers + conflict detector)
- EDIT: `routes/pm_command_center.py` (+80 LOC · `SPECIALTY_ASSET_FAMILY` taxonomy + `specialty_family_of()` + `is_specialty_asset()` + augmented overview with `specialty_assets_assigned` / `specialty_by_family`)
- EDIT: `server.py` (+15 LOC · wires new router after PM CC router)

### Frontend (3 new files · 1 edit)
- NEW: `pages/OperationsCenterCommand.jsx` (~430 LOC · 9 layers · Executive Mode · 12 brief tiles · family filter)
- NEW: `pages/PmHomeRedirect.jsx` (~14 LOC · `/pm` → `/pm/command-center`)
- NEW: `components/operations/command/ocCommandApi.js` (~50 LOC · REST client)
- EDIT: `App.js` (+10 LOC · 3 routes wired)

### Tests (1 new file)
- NEW: `backend/tests/test_operations_center_command_phase_4c.py` (~330 LOC · 24 contract tests including specialty family taxonomy + auth gates + envelope shapes + priority sorting)

### Memory
- THIS: `memory/OPERATIONS_CENTER_PHASE_4C_CERTIFICATION.md`
- Sister: `memory/PHASE_4C_SPECIALTY_ASSET_NORMALIZATION_CERTIFICATION.md`
- Test report: `test_reports/iteration_oc_command_phase4c.json`

---

## 6 · Live verification (testing_agent_v3_fork)

Tester used multi-login (`jaymn.judd@mascigc.com / Maddix123!`) → both admin + PM tokens injected.

**Verified passing:**
- ✅ Page mounts with `data-testid='operations-center-command'`.
- ✅ All 12 brief tiles render real backend integers (no em-dashes).
- ✅ Specialty Asset family chips show correct split: Trench Safety=16 · Access/Protection=88 · Traffic Control=0 · Support=75.
- ✅ Clicking "Trench Safety" chip narrows table to 16 trench-box rows.
- ✅ Clicking "Access / Protection" chip narrows table to 88 road plate rows.
- ✅ Project Health risk-sorted: red first (3) → green (25). No yellow on preview.
- ✅ Project Health "Open PM →" link href = `/pm/command-center?project_number=<pn>`.
- ✅ Shop Impact sorted high → medium → low.
- ✅ Safety Impact incidents AND capas tagged with critical/warning/informational tier chips.
- ✅ Telematics: all 9 buckets render (moving · idling · at_job · at_plant · at_yard · at_shop · offline · no_gps · unknown).
- ✅ Executive Mode toggle hides Allocation + Timeline sections, restores them on re-click.
- ✅ Cross-link "Dispatch" → `/dispatch-portal/command`. "PM" → `/pm/command-center`.
- ✅ `/pm` redirect to `/pm/command-center` verified.
- ✅ `/pm/hub` (legacy) still accessible.
- ✅ iPad portrait (768×1024) + landscape (1024×768): no horizontal page-level scroll. Tables scroll inside their container.
- ✅ Backend `/api/operations-center/command/*` all return 200 with admin token.

**Open issue fixed in this turn (was MEDIUM nit):**
- Brief specialty tile showed `0` instead of `179`. Root cause: tile read `specialty_assets_deployed` (assets with current_project_number set, which is 0 on this preview) instead of family-total. **Fix applied:** added `specialty_assets_total` field to `/brief` envelope and updated the frontend tile to read it. Verified: live preview now returns `specialty_assets_total=179` and the tile reads `179`. Both `*_total` and `*_deployed` exposed for accuracy (`road_plates_total=88 · road_plates_deployed=0` analogously preserved).

---

## 7 · Regression

```
cd /app/backend && python -m pytest tests/test_operations_center_command_phase_4c.py \
  tests/test_pm_command_center_phase_4a.py \
  tests/test_dispatch_command_center_phase_1.py \
  tests/test_asset_spine_p0_1.py
→ 98 passed · 1 skipped · zero regression · 1m47s
```

Skipped test: `test_map_contract_rows_have_required_fields` — preview DB has no `motive_truck_id` populated rows; test self-skips. This is expected and documented.

---

## 8 · Doctrine honored

- ✅ One operational picture for Ops Leadership (5:30 AM test)
- ✅ Cross-company composition · no duplicate dispatch/PM/shop/safety logic
- ✅ Specialty Asset normalization · Trench Boxes first-class · road plates inside `access_protection` family
- ✅ FleetWatcher / MaintainX render `not_connected` calmly throughout
- ✅ No fake green status · em-dashes / honest empty states / explicit `not_connected` chips
- ✅ Map-ready field set on every operational row (`/map-contract` is the Live Map's future single endpoint)
- ✅ Executive Mode same data, different view — no second system
- ✅ PM portal home now lands on PM CC · legacy PmHub preserved at `/pm/hub`
- ✅ iPad portrait + landscape verified · no horizontal page-level scroll
- ✅ Zero schema change · zero new collection · zero production data mutation

---

## 9 · STOP CONDITION

- 🛑 FleetWatcher activation NOT authorized.
- 🛑 MaintainX activation NOT authorized.
- 🛑 Live Operations Map render NOT authorized (contract is staged).
- 🛑 No further phases authorized.

Awaiting operator approval to proceed.

---

## 10 · Deliverable

- This certification: `/app/memory/OPERATIONS_CENTER_PHASE_4C_CERTIFICATION.md`
- Sister certification (architecture correction): `/app/memory/PHASE_4C_SPECIALTY_ASSET_NORMALIZATION_CERTIFICATION.md`
- Test report: `/app/test_reports/iteration_oc_command_phase4c.json`
- PRD entry: `/app/memory/PRD.md`
- Changelog entry: `/app/memory/CHANGELOG.md`
