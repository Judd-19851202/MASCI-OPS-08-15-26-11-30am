# TRACK 19.59 · Vendor Thread Readiness Contract

This document is the **exact contract Track 19.60 will consume**. The Vendor Thread promotion may render its Documents section entirely against the endpoints and shape defined below — **no additional backend work needed**.

## Query endpoints
```
GET /api/employee-records/records?entity_kind=vendor
  &vendor_id=<id>            (optional)
  &vendor_name=<name>        (optional)
  &state=<approval_status>   (optional; e.g. pending_approval, linked, rejected)
  &record_type=<slug>        (optional)
  &tag=<tag>                 (optional)
  &date_from=<YYYY-MM-DD>    (optional; effective_date range)
  &date_to=<YYYY-MM-DD>      (optional)
  &limit=200                  (default 200, max 500)
```

Auth: HR / Admin token via existing gate.

## Response shape
```
{
  "ok": true,
  "records": [
    {
      "id": "<uuid>",
      "entity_kind": "vendor",
      "ownership_lane": "vendor",
      "owning_department": "vendor",
      "vendor_id": "<supplier id or null>",
      "vendor_name": "<vendor name>",
      "vendor_display_name": "<display or null>",
      "employee_id": null,
      "employee_name_snapshot": null,
      "record_type": "w9 | certificate_of_insurance | contract_agreement | subcontract | rental_agreement | service_agreement | business_license | prequalification | vendor_packet | quote_proposal | pricing_sheet | safety_document | material_certification | correspondence | other_vendor_document",
      "record_category": "<optional>",
      "approval_status": "pending_match | pending_classification | pending_approval | linked | rejected",
      "status":          "same as approval_status",
      "effective_date":  "<YYYY-MM-DD or null>",
      "source_type":     "upload | manual_entry",
      "source_file_ref": "<internal file ref>",
      "source_file_name": "<original filename>",
      "source_file_hash": "<sha-256>",
      "imported_batch_id": "<batch id or null>",
      "related_incident_case_id": null,
      "related_project_id":      null,
      "related_asset_id":        null,
      "tags": [ "..." ],
      "notes": "...",
      "created_by": "<actor email>",
      "created_by_role": "hr | admin",
      "approved_by": "<or null>",
      "approved_by_role": "<or null>",
      "approved_at": "<iso or null>",
      "created_at": "<iso>",
      "updated_at": "<iso>"
    }
  ],
  "count": <int>
}
```

## Original-file download
```
GET /api/employee-records/records/{record_id}/file
```
Reused verbatim from the employee lane. Returns the preserved original file with the SHA-256 hash header.

## Vocabulary for the frontend
```
GET /api/employee-records/vocabulary
→ ownership_lanes: [..., "vendor"]
→ record_types_by_lane.vendor: [15 slugs]
→ entity_kinds: ["employee", "vendor"]
→ default_entity_kind: "employee"
```

## Track 19.60 rendering contract (Documents section)
The proposed `AdminVendorThread.jsx` may fill the Universal Thread `documents` slot by mapping each record to:
```
{
  id: rec.id,
  name: `${humanLabel(rec.record_type)}${rec.source_file_name ? ` · ${rec.source_file_name}` : ""}`,
  deep_link: `${API}/employee-records/records/${rec.id}/file`,
}
```
No new backend endpoint required.

## Guarantees to Track 19.60
- Vendor records are queryable by every filter listed above.
- Vendor records never appear in default (`entity_kind` absent) queries.
- Original file is preserved with SHA-256 hash.
- Approval + rejection audit trail is append-only and includes actor + role + timestamp.
- Effective date, tags, source provenance are optional but rendered as-is.
