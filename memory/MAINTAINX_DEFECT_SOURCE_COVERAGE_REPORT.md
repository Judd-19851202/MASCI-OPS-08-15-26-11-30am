# MAINTAINX · DEFECT SOURCE COVERAGE REPORT

**Date:** 2026-06-04 19:30 UTC
**Sprint:** OMEGA — Defect Source Coverage Command Center
**Mode:** READ-ONLY (no writes; no MaintainX traffic; no deploys)

This sprint delivers the read-only operational visibility layer the master plan called for: a single screen where any superintendent / shop manager / safety manager / operations manager / executive can answer the nine success-criteria questions **without opening MaintainX**.

---

## 1 · What was built

### Backend (single new service · two new read-only endpoints)
- NEW `backend/services/maintainx_defect_coverage.py` (320 LOC) — pure aggregator that reads `fleet_defects`, `equipment_inspections`, `asset_holds`, `asset_mappings`, `equipment_master` and emits a classified coverage report. **Zero writes.**
- MOD `backend/routes/integrations/maintainx_p0.py` — registers two read-only endpoints:
  - `GET /api/admin/maintainx/defect-coverage` (admin-strict, full payload)
  - `GET /api/integrations/maintainx/defect-coverage` (any-portal token, same payload)
- MOD `backend/routes/integrations/__init__.py` — passes `require_any_portal` into the P0 registrar.

### Frontend (three new surfaces)
- NEW `components/admin/MaintainxDefectCoverageSection.jsx` — full Admin "MaintainX Defect Source Coverage" section: 7-cell overview tile, 6-row source breakdown grid, defect explorer with right-side drawer.
- NEW `components/shop/ShopMaintainxReadinessTile.jsx` — Shop-portal **Readiness Queue** tile (Ready / Blocked / Duplicate Risk / Awaiting RTS counts). Read-only. No buttons.
- NEW `components/dispatch/DispatchEquipmentMaintenanceIndicator.jsx` — small calm Dispatch-hub line showing `Equipment Maintenance Issues Requiring Attention: X` with a "View Equipment Status" link. Suppresses itself when the count is zero. No MaintainX UI.

### Surface placement
- Admin Integration Center → `MaintainX · Read-First` tab → new coverage section appears **directly below** Connection Status / Asset Match / Dry-Run sections.
- Shop Hub → new tile under the existing "Last Activity" line, **before** the Equipment Needing Attention section.
- Dispatch Hub → small indicator placed at the very top of the main content area, **above** Operational Attention.

---

## 2 · Live preview baseline (no MaintainX API key set)

Captured from the live preview admin endpoint:

```
GET /api/admin/maintainx/defect-coverage?since_days=60

totals.open_defects        = 138
totals.high_severity       = 110
totals.safety_critical     = 110
totals.out_of_service      = 110
totals.ready_for_maintainx = 2
totals.blocked             = 134
totals.duplicate_risk      = 2
totals.mapped              = 0
totals.excluded            = (closed/cleared rows skipped)
writes_performed.{maintainx, equipment_master, fleet_defects,
                  equipment_inspections, asset_holds, asset_mappings}
                                                          = 0 / 0 / 0 / 0 / 0 / 0
```

The headline finding is **134 BLOCKED defects** — almost all of them blocked because the unit_number recorded on the inspection / hold cannot be resolved into a live `equipment_master` row. This is exactly the kind of data-quality intelligence the operator needs **before** MaintainX writes are enabled.

`Ready: 2` and `Duplicate Risk: 2` give the operator a concrete starting point: 2 defects are mapped + ready to flow, 2 represent likely double-submits.

---

## 3 · Source breakdown grid (admin)

Each row clickable; clicking filters the Defect Explorer below to that source. Columns: **Open · OOS · Safety · Ready · Blocked · Dup Risk · Mapped**.

| Source | Backend collection | Aggregated by |
| --- | --- | --- |
| Fleet DVIR | `fleet_defects` (rows where `inspection_kind` ≠ `manual_oos`) AND `equipment_inspections.kind in {pre_op, weekly_lead, weekly_emergency, dvir}` | `_norm_fleet_defect`, `_norm_inspection` (with `is_fleet=True` branch) |
| Equipment Pre-Op | `equipment_inspections` (no `kind` set; heavy-equipment shape) | `_norm_inspection` (with `is_fleet=False` branch) |
| Equipment Inspection | reserved bucket — distinguished by future `kind="scheduled_inspection"` rows; currently merged into Pre-Op until source rows arrive | same path |
| Dispatch Breakdown | `asset_holds.source_module="dispatch"` | `_norm_hold` |
| Shop Issues | `asset_holds.source_module="shop"` | `_norm_hold` |
| Manual OOS | `fleet_defects.inspection_kind="manual_oos"` OR `asset_holds.source_module="admin"` | `_norm_fleet_defect`, `_norm_hold` |

---

## 4 · Defect Explorer (admin)

For each defect row the explorer surfaces:

| Field | Source |
| --- | --- |
| Source | `source_type` |
| Equipment Name | `equipment_master.display_label` |
| Unit Number | `unit_number` (truck_unit_number / trailer_unit_number / equipment_unit) |
| Reported By | `reported_by_name` / `driver_name` / `operator_name` / `created_by` |
| Date Reported | `reported_at` / `created_at` / `inspection_date` |
| Severity | derived from row's severity OR `out_of_service` |
| Current Status | `fleet_defects.status` or `"open"` for inspections |
| Out-of-Service Flag | derived |
| Photos Present | `bool(row.photos)` |
| RTS Required | `True` whenever `out_of_service` or `severity ∈ {oos,high,critical}` |
| MaintainX Status | classifier output (Not Evaluated / Ready / Blocked / Duplicate Risk / Mapped / Excluded) |
| Reasons | classifier free-text list (e.g. `missing_unit_number`, `asset_unmapped_but_classifiable`) |

Drawer is read-only; **no action buttons**.

---

## 5 · Success criteria roll-up

| # | Question the operator must answer without opening MaintainX | Where in the UI it is answered |
| --- | --- | --- |
| 1 | How many maintenance issues exist? | Overview tile · `Open Defects` counter |
| 2 | Where did they originate? | Source breakdown grid · 6 rows |
| 3 | Which assets are affected? | Defect Explorer · `Unit Number` + `Equipment Name` per row |
| 4 | Which issues are OOS? | Overview tile · `Out of Service` counter AND row-level flag |
| 5 | Which issues are safety critical? | Overview tile · `Safety Critical` counter AND row-level flag |
| 6 | Which issues are ready for MaintainX? | Overview tile · `Ready` counter AND classifier badge |
| 7 | Which issues are blocked? | Overview tile · `Blocked` counter AND classifier badge + reasons |
| 8 | Which issues would create duplicate work orders? | Overview tile · `Duplicate Risk` counter AND classifier badge |
| 9 | How much maintenance activity would flow into MaintainX if enabled today? | The combined `Ready + Duplicate Risk` counters give a quantified preview |

All nine answerable from a single tab.

---

## 6 · Safety guarantees

| Surface | Behaviour |
| --- | --- |
| MaintainX | Untouched. The new endpoint never calls MaintainX. |
| `equipment_master` | Read-only `find()` only |
| `fleet_defects` | Read-only `find()` only |
| `equipment_inspections` | Read-only `find()` only |
| `asset_holds` | Read-only `find()` only |
| `asset_mappings` | Read-only `find()` only |
| New collections introduced | NONE |
| Buttons that mutate any operational row | NONE (drawer is display-only) |
| RTS / DVIR / Pre-Op / Shop / Dispatch logic | Unchanged — zero edits to any defect-originating route |
| Auth gate | Admin endpoint behind `require_admin`; portal endpoint behind `require_any_portal` (Shop / Safety / HR / PM / Dispatch / FL / Admin) |

The frontend renders a footer panel on every Coverage render asserting `writes_performed: mx=0 · eq_master=0 · fleet_defects=0 · inspections=0 · holds=0 · mappings=0`. Verified live.

---

## 7 · Lint sweep

```
ESLint MaintainxDefectCoverageSection.jsx         0 blocking · 0 advisory
ESLint ShopMaintainxReadinessTile.jsx             0 blocking · 0 advisory
ESLint DispatchEquipmentMaintenanceIndicator.jsx  0 blocking · 0 advisory
ESLint ShopHub.jsx (modified import + render)     0 / 0
ESLint DispatchHub.jsx (modified import + render) 0 / 0
```

Backend P0 tests re-run: **13/13 PASS** in 0.16s.

---

## 8 · Verdict — Defect Source Coverage

```
DEFECT SOURCE COVERAGE COMMAND CENTER  :  COMPLETE

  Admin overview tile + 7 totals               : DONE
  Source breakdown grid (6 rows)               : DONE (clickable filters)
  Defect Explorer with drawer                  : DONE
  Shop Readiness Queue tile                    : DONE (4 cells)
  Dispatch indicator (count only, no MX UI)    : DONE
  Live preview shows real data                 : YES (138 open / 110 OOS)
  Zero writes verified                         : YES
  Backend regression                           : 13/13 PASS
```
