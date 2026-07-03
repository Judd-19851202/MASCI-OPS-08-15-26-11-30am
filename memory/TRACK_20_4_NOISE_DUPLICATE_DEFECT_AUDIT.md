# TRACK 20.4 · Noise · Duplicate · Defect Audit

| Finding                                                                       | Classification | Rationale                                                                              |
|-------------------------------------------------------------------------------|:--------------:|----------------------------------------------------------------------------------------|
| `db.suppliers` — name-only master                                             | KEEP · EXTEND  | Foundation is sound. Add W-9-on-file / COI-expiration / prequalification / do-not-use flags in Track 19.60. |
| `SupplierMasterPanel` (Admin)                                                 | KEEP           | Keeps CRUD there. Cross-link "Open thread" button in Track 19.60.                     |
| `SupplierCombo`                                                                | KEEP           | Inline picker. Consider showing do-not-use badge next to name in a future track.       |
| `PmSuppliers` (read-only roster)                                              | KEEP · PROMOTE | Add "Open thread" link per vendor in Track 19.60.                                     |
| `PoRequests` per-vendor filter                                                | KEEP           | Continues to be the write surface for POs.                                             |
| Historical Records Intake (employee-only today)                                | EXTEND         | Add vendor lane (`entity_kind="vendor"`).                                             |
| Carrier compliance (transport_docs.insurance_certificate / w9 / hauling_agreement) | KEEP + ADAPT | Carrier-scoped. Do NOT duplicate into a general vendor system — deep-link from the Vendor Thread when the vendor IS a carrier. |
| Duplicate vendor lists in Admin+PM navigation                                  | ADAPT          | Same source but different lens — acceptable. Label clearly.                            |
| Free-text supplier names on DR / PO / Meeting / Constraint / Incident          | RESTRICT       | Not fixable in this track. Future migration to `supplier_id` FK could improve joins.  |
| Contact fields duplicated across surfaces                                      | RESTRICT       | No contact collection exists — no duplication yet.                                     |
| Contract "storage" spread across attachments                                   | EXTEND         | Consolidate under vendor lane of Historical Records.                                   |
| No dedicated Vendor detail page                                                | PROMOTE        | Build the Universal Thread page in Track 19.60.                                        |
| No dedicated audit                                                             | EXTEND         | Reuse `historical_records_audit` with `entity_kind` discriminator.                     |

## Zero defects
No architectural conflict was found (no duplicate collections, no competing ownership). The gaps are missing storage — not competing storage.

## What is NOT recommended
- Do NOT build `vendor_documents` as a new collection.
- Do NOT build `contracts` as a new collection now.
- Do NOT build `vendor_intelligence` as a new OI product.
- Do NOT build a parallel intake pipeline.
