# TRACK 19.23 · Historical Records Intake · Human Workflow Certification

## Surfaces
- `/hr/historical-records/intake` — single-record manual intake
- `/hr/historical-records/queue` — review queue (approve/reject/reassign)
- `/hr/historical-records/batches` — bulk batch list
- `/hr/historical-records/batches/:batchId` — bulk batch detail

## HR workflow (live-verified)
1. Upload `.txt` file to `/hr/historical-records/intake` with lane=HR, type=`hr_document`, employee link. ✅ toast "Record staged for approval."
2. Open Review Queue → new row appears in HR tab with pending_approval state. ✅
3. Click Approve → toast "Record approved." Row disappears. ✅
4. Navigate to Employee 360° Documents tab → new record visible under HR lane with "linked" pill. ✅

## Safety workflow (live-verified via safety token)
1. Safety cannot view HR lane vocabulary: `allowed_lanes_for_actor == ["safety"]` ✅
2. Safety cannot access HR queue: `GET /queues/hr` returns 403 ✅
3. Safety can upload to Safety lane and link Incident Case ID (Track 19.21 Safety-lane-only field) ✅
4. Safety CANNOT approve HR lane record: `_actor_can_approve` returns False for cross-lane ✅

## Asset Administrator workflow
1. Asset admin (Shop token with `is_asset_admin` flag) can only see Asset lane. ✅
2. Asset-lane intake reveals Asset ID field (Track 19.21 Asset-lane-only field). ✅
3. Asset admin CANNOT approve HR/Safety lane records. ✅

## Reject flow (live-verified)
1. Stage record → click Reject in queue → reason "Duplicate of file X" required.
2. Toast "Record rejected." → record does NOT appear on Employee 360° (approval_status="rejected" excluded from `approval_status: "linked"` filter). ✅
3. Audit ledger writes `record_rejected` event with reason + actor stamp. ✅

## Batch flow (live-verified end-to-end)
1. `POST /batches` with lane=hr, label="QA batch" → batch created ✅
2. `POST /batches/{id}/uploads` with 2 files → `created: 2`, both in `pending_classification` ✅
3. `POST /batches/{id}/apply` with `record_type=hr_document, employee_id=<emp>` → `modified: 2`, state → `pending_approval` ✅
4. `POST /batches/{id}/approve-all` → `approved: 2`, records now `linked` ✅
5. Records visible on target employee's 360° Documents tab ✅
6. Records missing employee_id or type at approval time → skipped by approve-all (server-side safeguard) ✅

## No OCR / No AI / No auto-file / No silent linking
- `employee_records.py` imports 0 ML libraries (grep verified).
- No fuzzy matching library imports.
- No async job that automatically assigns records without an explicit human `apply` or per-row edit.
- Every state transition writes to `db.employee_record_audit` (append-only).

**Verdict:** GO. Full workflow certified.
