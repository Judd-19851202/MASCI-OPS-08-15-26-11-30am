# TRACK 19.25 · Intake Session Foundation

## Problem
Bulk historical imports had operators re-typing provenance (source cabinet · box · location) 100+ times per file. Session-level metadata was missing.

## Solution
Additive fields on the existing batch model. No new collection, no new endpoint.

## Fields added
On `record_import_batches` documents (via `CreateBatchBody`):
- `source_name` — human-language descriptor ("2019 HR File Cabinet")
- `source_type` — enum-like: `cabinet · binder · box · folder · digital · other`
- `source_location` — human-language: "University High School · trailer"

On every `employee_records` document created by `POST /batches/{id}/uploads`:
- `intake_source_name` (inherited from batch)
- `intake_source_type` (inherited)
- `intake_source_location` (inherited)
- `intake_batch_label` (inherited so operators can find the record's source at a glance)

## Surfaces
- **Batches list page** (`/hr/historical-records/batches`): 3 new form inputs — Source name · Source type · Location. Hint: "Provenance is inherited by every file in this batch."
- **Batch detail page** (`/hr/historical-records/batches/:id`): session provenance strip surfaces above records list.
- **Employee 360° · Documents tab**: each doc card shows "Source: {intake_source_name} · {intake_source_type} · {intake_source_location}" in italic 10px.

## Live end-to-end verification (curl)
```
Create batch with source_name="2019 HR File Cabinet" source_type=cabinet
  → batch stored with provenance
Upload 2 files
  → each record inherits: intake_source_name="2019 HR File Cabinet"
                          intake_source_type="cabinet"
                          intake_source_location="Main office · trailer"
                          intake_batch_label="Track 19.25 test"
Bulk classify + bulk approve
  → records become linked
GET /employees/{empId}/records?lane=hr
  → records-with-session: 2 · source_name preserved
```

## Zero drift
- No schema migration. `record_import_batches` accepts extra fields via `ConfigDict(extra="allow")`.
- No new endpoints.
- No new collections.
- Fields default to empty strings when the batch was created without them (pre-19.25 batches remain fully compatible).

**Verdict:** GO. Provenance now travels with every record from cabinet to Employee 360°.
