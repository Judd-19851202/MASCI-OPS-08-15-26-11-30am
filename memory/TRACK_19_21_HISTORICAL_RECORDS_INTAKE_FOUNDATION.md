# Track 19.21 · Historical Records Intake Foundation

**Scope:** P0 foundation — data model + upload batches + manual classify + approval + audit. **NOT** OCR · **NOT** AI classification · **NOT** fuzzy matching.

## Data model

### `db.record_import_batches`
- `id` (uuid) · `ownership_lane` · `label` · `notes`
- `created_by` · `created_by_role` · `created_at`
- `file_count` · `record_count` · `status` (open · closed)

### `db.employee_records` (universal record model)

All fields listed. `employee_id` may be `null` while state is `pending_match`. `record_type` may be `null` while state is `pending_classification`. Both become required at `pending_approval`.

- `id` · `employee_id` · `employee_name_snapshot` (snapshotted at creation for audit stability)
- `record_type` · `record_category` · `ownership_lane` · `owning_department`
- `created_by` · `created_by_role` · `reviewed_by` · `approved_by` · `approved_at` · `approved_by_role`
- `rejected_by` · `rejected_at` · `rejection_reason`
- `approval_status` (mirrors `status` — 5 states)
- `effective_date` · `source_type` (`upload` | `manual_entry`)
- `source_file_ref` · `source_file_name` · `source_file_hash` · `imported_batch_id`
- `related_incident_case_id` · `related_training_id` · `related_asset_id` · `related_project_id` · `related_supervisor_id`
- `tags` (list) · `notes` (string)
- `created_at` · `updated_at`

### `db.employee_record_audit` (append-only)
- `id` · `record_id` · `event` (record_created · record_approved · record_rejected · record_reassigned)
- `actor_email` · `actor_role` · `details` (event-specific payload) · `ts`

## Workflow

```
1. HR / Safety / Asset admin creates a batch:
   POST /api/employee-records/batches { ownership_lane, label, notes }
   → returns batch_id
2. Files are uploaded via the existing Track 19.04 attachment pipeline
   (any of pdf/xlsx/xlsm/xls/csv or images). File metadata (ref/name/hash)
   is captured and passed to record creation.
3. For each file, a record is created:
   POST /api/employee-records/records {
     ownership_lane, record_type, employee_id, effective_date, notes, tags,
     source_file_ref, source_file_name, source_file_hash, imported_batch_id, ...
   }
   → returns record with state pending_classification | pending_match | pending_approval
4. Records sit in the lane's review queue:
   GET /api/employee-records/queues/{lane}
5. Reviewer classifies + matches employee (if missing), then approves:
   POST /api/employee-records/records/{id}/approve
   → state = linked · appears in Employee 360° "Documents" tab
6. If wrong: reject or reassign.
   POST /records/{id}/reject { reason }
   POST /records/{id}/reassign { employee_id, record_type, ownership_lane }
```

Every step writes to `db.employee_record_audit`.

## Original file preservation

- Files are stored via the existing Track 19.04 R2 pipeline (`documents/YYYY/MM/…`).
- The record carries `source_file_ref` (R2 key), `source_file_name` (original filename), `source_file_hash` (sha256).
- The R2 object is IMMUTABLE — updates create new versions with new refs.
- Approval + rejection never modify the file — only the record document is mutated.

## Duplicate detection (basic · Phase 1)

- sha256 hash is stored on every record.
- Callers may check duplicates before creating a record: `GET /api/employee-records/records?source_file_hash=<sha256>`.
- Automatic sha256 dedup in the create endpoint is deferred to Track 19.22 (P2-C in the audit roadmap).

## Not yet built (deferred by explicit doctrine)

- OCR text extraction from uploaded PDFs
- AI classification (record_type suggestion)
- Fuzzy employee matching (suggested employee_id)
- Auto-approval based on confidence
- Duplicate detection at ingest time (currently query-time only)
- Frontend Review Queue UI page (backend endpoint exists; page ships in Track 19.21b)
- Frontend Historical Import upload page (Track 19.21b)

## Lane permissions

See `TRACK_19_21_PERMISSION_OWNERSHIP_MODEL.md`.

## Audit contract

Every mutation (create · approve · reject · reassign) writes to `db.employee_record_audit`. The audit collection is append-only — the module has no update/delete/replace paths (locked by `test_audit_ledger_is_append_only_by_design`).
