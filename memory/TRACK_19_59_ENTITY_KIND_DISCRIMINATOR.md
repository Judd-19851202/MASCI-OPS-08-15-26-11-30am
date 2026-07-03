# TRACK 19.59 · Entity Kind Discriminator

## Canonical field
`entity_kind` — persisted on both records and batches.

## Allowed values
- `"employee"` — default. Every pre-Track-19.59 record is treated as employee.
- `"vendor"` — new. Only permitted in the `vendor` ownership lane.

## Backwards-compatibility rules
1. **Missing entity_kind → employee.** `list_records` treats absent `entity_kind` as employee scope. Query defaults to `{"entity_kind": {"$in": ["employee", None]}}` so every legacy row surfaces.
2. **Vendor records never appear in employee queries.** Only `?entity_kind=vendor` OR `?lane=vendor` reveals vendor rows.
3. **Cross-lane guard.** `create_record` refuses `entity_kind="vendor"` inside a non-vendor lane, and refuses `entity_kind="employee"` inside the `vendor` lane. This is a strict architectural boundary.
4. **Approval gate splits.** Vendor records require `vendor_id` OR `vendor_name`. Employee records still require `employee_id`. Both still require `record_type`.
5. **Audit ledger records the discriminator.** Every `record_created` audit entry preserves `entity_kind` + `vendor_id` + `vendor_name` for forensic traceability.

## Non-goals
- No fuzzy matching between vendor strings.
- No automatic vendor master creation.
- No inference of vendor identity from filename or content.
- No AI classification.

## Rationale
The `entity_kind` field is the canonical discriminator even though `ownership_lane == "vendor"` is equivalent at the storage layer. Keeping the field explicit provides:
- A single-field query filter that survives future lane renames.
- A clear audit signal — investigators can `grep entity_kind vendor` on the audit ledger.
- A future-safe hook for additional entity kinds (asset · project · incident) if ever needed, without touching the ownership-lane taxonomy again.
