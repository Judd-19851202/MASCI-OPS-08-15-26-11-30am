# TRACK 19.59 · Vendor Lane Implementation

## Backend — `backend/routes/employee_records.py`
| Element                       | Change                                                                                             |
|-------------------------------|----------------------------------------------------------------------------------------------------|
| `OWNERSHIP_LANES`             | Added `"vendor"` as fifth lane (backwards-compatible)                                              |
| `ENTITY_KINDS` constant       | New — `("employee", "vendor")`                                                                     |
| `DEFAULT_ENTITY_KIND`         | New — `"employee"` (missing on any record → employee)                                              |
| `LANE_APPROVERS["vendor"]`    | New — `{"hr", "admin"}` only                                                                       |
| `LANE_RECORD_TYPES["vendor"]` | New — 15 human-readable slugs                                                                      |
| `CreateBatchBody`             | Added `entity_kind: Optional[str]`                                                                 |
| `CreateRecordBody`            | Added `entity_kind`, `vendor_id`, `vendor_name`, `vendor_display_name` (all optional)              |
| `create_record()`             | Resolves canonical `entity_kind`; guards vendor identity vs lane; sets vendor identity on records  |
| `approve_record()`            | For vendor records, requires `vendor_id` OR `vendor_name` (in place of `employee_id`)              |
| `list_records()`              | Accepts `entity_kind`, `vendor_id`, `vendor_name` query params. **Defaults to employee scope** when `entity_kind` is absent. |
| `vocabulary()`                | Returns `entity_kinds` + `default_entity_kind`                                                     |
| `create_batch()`              | Persists `entity_kind` on the batch document                                                       |
| `_actor_can_read_lane()`      | Unchanged — vendor lane restricted to HR/Admin by omission                                         |
| `_actor_can_approve()`        | Unchanged — behaviour flows through the new `LANE_APPROVERS["vendor"]` entry                       |
| `_write_audit()`              | Now records `entity_kind`, `vendor_id`, `vendor_name` in `record_created` details                  |

## Frontend — `frontend/src/pages/HistoricalRecordsIntake.jsx`
| Element                     | Change                                                                                            |
|-----------------------------|---------------------------------------------------------------------------------------------------|
| `LANE_LABEL.vendor`         | New — "Vendor (HR/Admin)"                                                                         |
| `LANE_STYLE.vendor`         | New — emerald palette                                                                             |
| Vendor identity state       | `vendorName` + `vendorId` local state                                                             |
| Conditional employee picker | `EmployeeCombo` hidden when `lane === "vendor"`                                                    |
| Vendor identity block       | New block behind `data-testid="intake-vendor-block"` — name required, id optional, HR/Admin note   |
| Submit payload              | Routes `entity_kind="vendor"` + `vendor_name/id` when lane is vendor; every other case unchanged   |

## What was NOT changed
- Upload endpoint — reused verbatim.
- Batch endpoints — reused verbatim.
- Approval/rejection workflow — reused verbatim (with the added vendor-identity gate).
- Audit ledger — reused verbatim (with additional entity_kind + vendor_id/name in detail dict).
- File preservation / SHA-256 hash — unchanged.
- Original-file download endpoint — unchanged.
- Employee 360 / Employee Thread / HR Accountability Timeline — untouched.
- OI engine / scheduler / email pipeline — untouched.
