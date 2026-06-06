# TRENCH SAFETY · PHASE 4A — GO / NO-GO CERTIFICATION

**Phase:** 4A — Equipment Inventory + Project Assignment + Operations Integration
**Date:** 2026-02 (preview pod)
**Verdict:** 🟢 **GO — Phase 4A operational layer is certified. Phase 4B (Inspections / Holds) authorized to begin.**

---

## 1. Scope (per OMEGA Directive)

> "Make trench safety assets behave as first-class operational assets inside MASCI."

Phase 4A delivers:

1. Equipment Inventory Integration (trench assets visible in existing `equipment_master`).
2. Project Assignment (project name/#, superintendent, foreman, assigned-by, date).
3. Automatic propagation of current project / location / operational status / deployment history / audit history on every assign + return.
4. Project Dashboards display the trench safety assets currently on that project.
5. Operations visibility through the existing equipment_master pipe (no duplicate systems).

Phase 4A explicitly **does NOT** build: Inspections, Holds, Certifications, Transport, Dispatch, Shop Repair, QR PNG, OCR, Reports.

---

## 2. Phase 4A Certification Matrix (10 / 10 PASS)

| # | Requirement                                                | Evidence                                                                                                                                    |
|---|------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | TB-01 through TB-07 visible inside equipment inventory     | `GET /api/equipment-master?category=Trench%20Safety` returns 7 rows with `unit_number` = TB-01…TB-07, `category` = "Trench Safety". Verified by `test_equipment_master_lists_trench_safety_with_unit_number`. |
| 2 | Searchable                                                 | Rows carry `unit_number` / `make_model` / `display_label` / `vin_serial_number` / `category` — every field the existing Equipment Master Fleet search and category filter consumes. Verified by `test_equipment_master_searchable_by_asset_id`. |
| 3 | Assignable                                                 | `POST /api/trench-safety/assets/{id}/assign` accepts `project_id`, `project_number`, `project_name`, `superintendent`, `foreman`, `assigned_by`, `source`. Verified by `test_assign_propagates_superintendent_foreman_to_asset_and_deployment`. |
| 4 | Location updates                                           | On assign, `current_location` ← project_name; on return, `current_location` ← yard. Mirror keeps `location` aligned. Verified by `test_assignment_mirrors_to_equipment_master` + `test_return_clears_current_project_fields`. |
| 5 | Project updates                                            | `current_project_id` / `current_project_name` / `current_project_number` / `current_superintendent` / `current_foreman` set + cleared correctly. Same tests as row 4 plus `test_by_project_excludes_after_return`. |
| 6 | Deployment history created                                 | Each assign+return cycle inserts a `trench_safety_deployments` row carrying superintendent / foreman / project_number. Verified by `test_deployment_history_grows_and_carries_phase4a_fields`. |
| 7 | Audit history created                                      | `audit_events` rows with `kind=trench_asset_assigned` and `trench_asset_returned`. Verified by `test_audit_events_record_assign_and_return`. |
| 8 | Existing equipment unaffected                              | `GET /api/equipment-master` still returns the JSON-seeded fleet plus Trench Safety as one of many categories (>=2 categories present). Verified by `test_equipment_master_still_serves_other_categories`. |
| 9 | Existing dispatch unaffected                               | No dispatch routes modified. The trench-safety `by-project` endpoint is read-only and lives under `/api/trench-safety/*`. Manual review of `routes/operations.py` (separate file) confirms zero edits to `routes/dispatch_*.py` or `services/dispatch*`. |
|10 | Existing projects unaffected                               | `PmProjectDetail` adds a single read-only panel beneath the existing OperationalTimelineSidecar. PM Jobs read endpoint untouched. PM scope helper untouched. Visual review confirms no removal/edit of existing PM tiles. |

**Total: 10 of 10 PASS.**

---

## 3. Backend test suite

```
tests/test_trench_safety_phase4a.py  ── 16 / 16 PASS  ── 16.17s
tests/test_trench_safety_phase2.py   ── 28 / 28 PASS  ── 15.05s   (regression — clean)
```

### Phase 4A coverage (16 tests)
1. equipment_master lists trench safety with unit_number populated
2. equipment_master searchable by asset_id
3. Assign propagates superintendent/foreman/project_number to asset + deployment
4. Assignment mirrors to equipment_master
5. Return clears all current_* project fields
6. by-project returns current assignments
7. by-project supports project_number AND project_name lookups
8. by-project requires at least one filter (422 otherwise)
9. by-project excludes asset after return
10. by-project include_history returns deployment history
11. Inspection Hold blocks assignment (409)
12. Deployment history grows + carries Phase 4A fields
13. Audit events record assign + return
14. Operations picker returns projection
15. Operations picker available_only filter
16. Equipment master still serves other categories (no regression)

---

## 4. Code Deliverables

### Backend
| File | Change |
|------|--------|
| `routes/trench_safety/_helpers.py` | `upsert_equipment_master_mirror` now writes `unit_number`, `year`, `make`, `model`, `make_model`, `display_label`, `vin_serial_number`, `preop_equipment_type`, `company`, `comments`, plus the operational fields `operational_status`, `current_location`, `current_project_number`, `last_inspection_at`, `next_inspection_due` so trench assets render identically to fleet rows in the existing Equipment Master Fleet table. |
| `routes/trench_safety/_models.py` | `DeploymentAssign` now accepts optional `project_number`, `superintendent`, `foreman`. |
| `routes/trench_safety/deployments.py` | Assign endpoint persists + propagates the new fields and clears them on return. |
| `routes/trench_safety/operations.py` | **NEW.** `GET /api/trench-safety/by-project` (current + optional history; supports `project_id` / `project_number` / `project_name`). `GET /api/trench-safety/operations/picker` (slim projection with `available_only`, `asset_type`, `operational_status` filters). |
| `routes/trench_safety/__init__.py` | Wires `register_operations_routes`. |

### Frontend
| File | Change |
|------|--------|
| `pages/trench_safety/TrenchSafetyAssignDialogs.jsx` | **NEW.** `AssignToProjectDialog` + `ReturnFromProjectDialog` (no mock data; operator types project, superintendent, foreman; backend writes a real deployment row). |
| `pages/trench_safety/TrenchSafetyAssetDetail.jsx` | Adds the Assign / Return action bar (status-gated), shows current project / superintendent / foreman, replaces the Phase-3 read-only note with a full Deployment History timeline table. |
| `pages/trench_safety/TrenchSafetyAssetsList.jsx` | New `Current Project` column (project name + #). |
| `components/trench/TrenchSafetyOnProjectPanel.jsx` | **NEW.** Read-only panel for the per-project surface — Asset / Type / Size / Condition / Status / Last Inspection / Location + QR-view link. |
| `pages/PmProjectDetail.jsx` | Mounts `TrenchSafetyOnProjectPanel` beneath the OperationalTimelineSidecar. |
| `lib/i18n.js` | Spanish translations for every new Phase 4A string. |

### Tests
| File | Change |
|------|--------|
| `backend/tests/test_trench_safety_phase4a.py` | **NEW.** 16-test suite. |

---

## 5. Architecture compliance

- **No duplicate systems.** Trench assets continue to live in `trench_safety_assets`; the existing `equipment_master` is the only inventory surface; existing PmShell / PmProjectDetail is the only per-project surface; existing audit_events stream is the only audit surface.
- **Mirror is unidirectional.** Writes go to `trench_safety_assets` → mirrored to `equipment_master`. Equipment Master writes that touch a Trench Safety row remain blocked because the trench mirror is owned by `_helpers.upsert_equipment_master_mirror`.
- **Public/Field surface untouched.** Phase 3.5 public field view did not regress (Phase 2 regression suite still 28/28).

---

## 6. Verdict

🟢 **GO — Phase 4A Operational Layer certified.**

Phase 4B (Inspections / Holds / Certifications) is authorized to begin.

Phase 4A leaves the fleet in a clean Available state via the `_phase4a_setup` teardown — the operational layer is now battle-ready for the safety lifecycle layer.
