# TRACK 19.59 · Employee Safety Sentinels

The vendor extension must NOT contaminate the employee lifecycle. This document enumerates the explicit sentinels.

## Sentinel 1 — vendor records never surface in default queries
`list_records()` filters to `entity_kind in ["employee", None]` unless the caller explicitly opts into `entity_kind=vendor` (or `lane=vendor`). Every existing Employee-Thread / HR Accountability Timeline / Employee 360 read path benefits from this default automatically — they continue to receive employee rows only.

Assertion: `test_list_records_defaults_to_employee_scope`.

## Sentinel 2 — vendor records refuse to be created inside employee lanes
`create_record()` raises 400 if `entity_kind="vendor"` is submitted with any lane other than `"vendor"`. Symmetrically, it raises 400 if `entity_kind="employee"` is submitted with the `"vendor"` lane. This guarantees the lane and the discriminator remain in lock-step.

Assertion: `test_create_record_rejects_cross_lane_entity_kind`.

## Sentinel 3 — vendor approval requires vendor identity
`approve_record()` rejects vendor-lane approvals that lack `vendor_id` OR `vendor_name`. Employee-lane approvals continue to require `employee_id`. Both continue to require `record_type`.

Assertion: `test_approve_record_requires_vendor_identity_for_vendor_lane`.

## Sentinel 4 — vendor records carry no employee identity
The record document persists `employee_id=None`, `employee_name_snapshot=None` when `entity_kind="vendor"`. Symmetrically, `vendor_id / vendor_name / vendor_display_name` are `None` for employee records.

Enforcement: hard-coded in `create_record` (see lines that set each field based on `entity_kind`).

## Sentinel 5 — audit records the discriminator
Every `record_created` audit row includes `entity_kind`, `vendor_id`, `vendor_name`. Investigators can `grep entity_kind vendor` across the audit ledger.

Assertion: `test_audit_records_entity_kind`.

## Sentinel 6 — approval permission is HR/Admin only for vendor lane
`LANE_APPROVERS["vendor"] = {"hr", "admin"}`. Safety, Asset Admin, PM, Field, Public all receive 403 on any vendor-lane mutating call.

Assertion: `test_vendor_approvers_hr_admin_only`.

## Sentinel 7 — legacy PDF exports untouched
`/api/employee-records/employees/{emp_id}/exports/{package}.pdf` reads only `employee_records` with `employee_id` set. Vendor records store `employee_id=None`, so they are naturally excluded from every employee export. No code change needed.

## Sentinel 8 — HR Accountability Timeline untouched
The Employee Thread's accountability timeline reads a separate endpoint. Track 19.59 did not touch it.

## Sentinel 9 — Employee 360 / Employee Thread reads default-filter
Every existing consumer of `list_records()` that does not pass `entity_kind` receives employee rows only, thanks to Sentinel 1. This includes Employee 360, Employee Thread, HR Employees list, and PM Employee reads.

## Sentinel 10 — no OI / scheduler / email path touched
`test_no_oi_or_scheduler_touched` locks the OI engine folder to 9 files. No scheduler / email pipeline / notification surface was modified.

## Regression check
Running `pytest test_track_19_21_employee_records_platform.py test_track_19_21b_historical_records_intake.py test_track_19_22_operational_completion.py` after Track 19.59 → **all GREEN**. Only the pre-existing `test_four_ownership_lanes_exist` was updated to acknowledge the new fifth lane (naming preserved; assertion widened).
