# PHASE 5 — LOCATION SYNC REPORT

## Goal
Whenever a trench safety asset moves through Dispatch, the `current_location`, `current_project_*`, and `operational_status` on the canonical `trench_safety_assets` row stay in lockstep with reality.

## Sync rules

| Transfer event | `current_location` | `current_project_*` | `operational_status` |
|----------------|--------------------|----------------------|-----------------------|
| `in-transit` | `"In Transit"` | unchanged | `In Transport` (only if no hold) |
| `receive` to **project** | `to_location_label` | set to `to_project_*` | `Assigned` (only if no hold) |
| `receive` to **yard** | `to_location_label` (yard name) | cleared | `Available` (only if no hold) |
| `cancel` | restored to `transport_from_location` | unchanged (project not yet set) | `Available` if was `In Transport` |

## Hold preservation
- After every mutation, `apply_resolved_status(asset_id, actor)` runs the Phase 4B priority resolver. Active holds always beat `In Transport` / `Assigned` / `Available`.
- The bridge **does not write** `operational_status` if any hold is active (`has_hold == True`). Instead, only the location bookkeeping fields are written; the resolver then keeps the hold winning.

## Mirror sync
`upsert_equipment_master_mirror` runs automatically inside `apply_resolved_status`. After every transfer event, the trench asset's `equipment_master` shadow row carries the freshest `operational_status`, `current_project_*`, `current_location`, `active_holds`, and `certification_status`. Dispatch / Project / Search consumers see one consistent truth.

## Deployment timeline sync
- On `receive` to a project, the bridge **closes any open deployment** and opens a new one with `source = "Dispatch / Transport Log"`. This keeps the Phase 4A deployment timeline accurate even when the move was initiated by Dispatch (not via the explicit Assign dialog).
- On `receive` to a yard, the bridge closes any open deployment with `auto_returned=true`.

## Evidence
| Test | Outcome |
|------|---------|
| `test_in_transit_marks_trench_asset_in_transport` | ✅ |
| `test_receive_to_project_updates_status_and_project` | ✅ |
| `test_receive_to_yard_clears_project_and_marks_available` | ✅ |
| `test_cancel_restores_status` | ✅ |
| `test_equipment_master_mirror_reflects_transport` | ✅ |
| `test_by_project_sees_transported_asset` | ✅ |

## Compliance
- Single source of truth: `trench_safety_assets`.
- Single mirror direction.
- Holds always win.
