# TRACK 19.60 · Source of Truth

| Field / slot                     | Certified endpoint                                                                     | Duplicated? |
|----------------------------------|----------------------------------------------------------------------------------------|:-----------:|
| Vendor name · id · is_active     | `GET /api/suppliers` (find by id or name in the response list)                        | ❌          |
| Vendor documents (by id)         | `GET /api/employee-records/records?entity_kind=vendor&vendor_id=<id>`                 | ❌          |
| Vendor documents (fallback name) | `GET /api/employee-records/records?entity_kind=vendor&vendor_name=<name>`             | ❌          |
| Original document download       | `GET /api/employee-records/records/{id}/file`                                          | ❌          |
| Historical Records intake        | `/hr/historical-records/intake?entity_kind=vendor&vendor_id=<id>` (deep-link only)     | ❌          |
| Historical Records queue         | `/hr/historical-records/queue` (deep-link only)                                        | ❌          |

## String-based joins (Track 20.4 finding)
- PO / project relationships are matched **by supplier name string**. The thread labels them: "Matched by supplier name" — no FK integrity is claimed.

## No inference · no fabrication
Every fact the thread renders traces to one of the endpoints above. Missing fields render as "—" or honest-empty. No AI. No OCR. No fuzzy matching. No auto-vendor creation.
