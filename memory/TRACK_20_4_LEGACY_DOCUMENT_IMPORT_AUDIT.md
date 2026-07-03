# TRACK 20.4 · Legacy Document · Paper Import Audit

## Current state
`HistoricalRecordsIntake.jsx` + `HistoricalRecordsQueue.jsx` + `HistoricalRecordsBatches.jsx` + `HistoricalRecordsBatchDetail.jsx` implement a certified batch-upload → review-queue → approve pipeline. **All lanes are employee-scoped today** (`employee_records` / `employee_documents`).

## Extension recommendation for Track 19.60
Extend the intake to accept a **vendor lane** without disturbing the employee lane. Concretely:

| Aspect                | Employee lane (today)                          | Vendor lane (proposed)                                   |
|-----------------------|------------------------------------------------|----------------------------------------------------------|
| Target entity         | `employee_id`                                   | `vendor_id` (from `suppliers.id`)                        |
| Batch model           | `historical_batches.entity_kind="employee"`     | `historical_batches.entity_kind="vendor"`                |
| Review queue          | Shared queue with `entity_kind` filter          | Shared queue with `entity_kind="vendor"` filter          |
| Document type catalog | Employee doc types                              | `w9`, `insurance_certificate`, `business_license`, `contract`, `subcontract_agreement`, `quote`, `proposal`, `invoice`, `correspondence`, `safety_document`, `compliance_document`, `material_certification`, `other` |
| Approval routes       | HR approves                                     | HR / Admin approves (Accounting also for AP-relevant)     |
| File storage          | Existing storage                                | Same storage · new `namespace="vendor"`                   |
| Permissions           | HR/Admin write · role-aware read                | Same envelope · with the Track 20.4 role lens applied     |
| Audit                 | Existing `historical_records_audit`             | Same collection · discriminated by `entity_kind`          |

## Rationale
- Zero new collection required — reuse `historical_records` and `historical_batches` with an `entity_kind` discriminator.
- Zero new upload pipeline — reuse the existing multipart intake.
- Zero new review UI — extend queue filters to include `entity_kind`.
- Corruption risk to employee lane is zero because the discriminator is validated on write.

## Explicit non-goals
- Do NOT build a parallel vendor intake page.
- Do NOT create `vendor_documents` as a new collection.
- Do NOT bypass HR/Admin approval.
- Do NOT allow PM/Safety/Shop to approve — they may submit, HR/Admin approves.

## What can NOT be reused
- **Contract signing / e-signature workflow** — does not exist today for any entity. Deferred to a later track.
- **Contract renewal reminders** — deferred (may plug into `document_expirations` later).

## Verdict
🟢 **Historical Records Intake can be safely extended** to serve vendor documents. Small backend LOC (schema discriminator + admin approve variant) + small frontend LOC (entity picker + doc type list). No corruption risk to employee lifecycle ownership.
