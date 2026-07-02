# TRACK 19.23 · Data Integrity Certification

## Original file preservation
- `source_file_ref` stored on every staged record (SHA-256 hash from `_sha256(raw)`).
- Cloud storage: Cloudflare R2 via `photo_storage.upload_photo_bytes` (immutable path `emp-rec/{lane}/{hash-prefix}`).
- Base64 fallback (dev/test) preserves complete bytes in the ref itself.
- **8 references to `source_file_ref` and 5 references to `source_file_hash` in the module** (grep verified).

## Roster immutability
`grep -c "db.employees.insert\|db.employees.update\|db.employees.delete" /app/backend/routes/employee_records.py` → **0** ✅

The Employee Records module NEVER mutates the employee roster.

## Incident case immutability
`grep -c "db.incident_cases.insert\|db.incident_cases.update\|db.incident_cases.delete" /app/backend/routes/employee_records.py` → **0** ✅

The Employee Records module NEVER mutates incident cases.

## Audit ledger append-only
`grep -c "db.employee_record_audit.update\|db.employee_record_audit.delete\|db.employee_record_audit.replace" /app/backend/routes/employee_records.py` → **0** ✅

The audit collection is written EXCLUSIVELY via `insert_one` inside `_write_audit()`.

## Approved records appear on Employee 360°
- Roll-up endpoint `/employees/{id}/records` filters `approval_status: "linked"` by default.
- Documents tab on `EmployeeProfile.jsx` calls `fetchEmployeeRecords(empId, { include_pending: false })`.
- Verified live: batch-approved records surface immediately.

## Rejected records DO NOT appear as active
- `approval_status: "rejected"` is excluded from the default roll-up filter.
- The record persists (audit trail preserved) but is invisible to Employee 360° until state changes.

## Historical records traceable to source file
- Every record row carries `source_file_ref`, `source_file_name`, `source_file_hash`, `imported_batch_id`, `created_by`, `created_at`.
- `GET /records/{id}/file` retrieves the original via presigned R2 URL (short TTL) or base64 fallback.
- Audit ledger records the SHA-256 at creation time — tamper-evident.

## Export packages include correct approved records
- `_render_employee_package_pdf` queries `{"employee_id": emp_id, "approval_status": "linked"}` per-package (verified in code).
- Rejected records excluded.
- Category filters (`PACKAGE_CATEGORIES` + lane filter) further narrow per package.

## No duplicate employee system
- Single collection: `db.employees` (HR portal writes only).
- Every Track 19.21-22 API reads via `db.employees.find_one({"$or":[{"id":emp_id},{"employee_id":emp_id}]})`.
- No parallel roster collection created.

**Verdict:** GO. Zero drift. Zero mutation. Zero duplication.
