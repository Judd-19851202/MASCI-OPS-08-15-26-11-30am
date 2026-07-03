# TRACK 19.60 · Documents Section Certification

## Source
Track 19.59 vendor-lane records: `GET /api/employee-records/records?entity_kind=vendor&vendor_id=<id>` (with `vendor_name` fallback).

## Rendering
Every record maps to a single line:
```
{
  id: rec.id,
  name: `${VENDOR_TYPE_LABEL[rec.record_type]} · state: ${rec.approval_status}[ · eff: <date>][ · <filename>]`,
  deep_link: `${API}/employee-records/records/${rec.id}/file`
}
```
Grouped display is emergent — records are sorted by the shell in insertion order. The `record_type` label is the primary group cue.

## Vendor document type catalog (Track 19.59)
- W-9
- Certificate of Insurance / COI
- Contract / Agreement
- Subcontract
- Rental Agreement
- Service Agreement
- Business License
- Prequalification
- Vendor Packet
- Quote / Proposal
- Pricing Sheet
- Safety Document
- Material Certification
- Correspondence
- Other Vendor Document

## Original file download
Every document row deep-links to `/employee-records/records/{id}/file` — the certified original-file endpoint reused verbatim from the employee lane. SHA-256 hash preserved by the intake pipeline; the thread does not touch it.

## What is NOT rendered
- No upload UI in the thread. Users click the header cross-link to reach `/hr/historical-records/intake?entity_kind=vendor&vendor_id=<id>`.
- No inline PDF viewer — the shell shows a plain deep-link.
- No compliance meter / percentage complete.
- No OSHA / court / insurance claim.

## Permission boundary
Every deep-link is server-gated by the certified employee-records auth envelope. If a caller lacks the Admin token, the download returns 401/403 — the browser will surface the standard error.
