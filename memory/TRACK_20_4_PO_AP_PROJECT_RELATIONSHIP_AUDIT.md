# TRACK 20.4 · PO · AP · Project Relationship Audit

## Join keys that already exist
| Relationship                   | Source collection            | Join key                                       | Route to read                                                       |
|--------------------------------|------------------------------|-----------------------------------------------|---------------------------------------------------------------------|
| Vendor → POs                   | `po_requests`                | `po_requests.supplier_name == suppliers.name` | `GET /api/po-requests?supplier=<name>` (client-filtered today)     |
| Vendor → Projects worked        | `po_requests` × `jobs_master`| project_number derived via PO                 | Multi-hop join at read time                                        |
| Vendor → PM (approver)          | `po_requests.approvals[]`    | approver_user                                 | Same PO endpoint                                                    |
| Vendor → Material movement      | `material_movement_daily`    | supplier/plant name string                    | Same daily endpoint                                                 |
| Vendor → Dispatch / hauling     | `dispatch_haul_ledger`       | carrier / supplier name string                | Ledger endpoint                                                     |
| Vendor → Repair / service       | Shop intel                   | supplier/vendor name string                   | Shop intel endpoints                                                |
| Vendor → Equipment rentals      | Equipment / fleet-ops        | supplier name (weak link)                     | Fleet endpoints                                                     |

## Missing joins (all string-based today · none is a strong FK)
- Vendor identity is a **string** across POs / DR / dispatch. There is no `vendor_id` FK.
- Any Track 19.60 thread must therefore render relationships via **name-match / match by name** and label them clearly ("Match by name — 12 POs · $NN").
- Do not fabricate stronger relationships than the data supports.

## Recommended read pattern for the Vendor Thread
For each vendor named `<n>`, in parallel:
- `GET /api/po-requests?supplier=<n>` → PO history / open / receipts
- `GET /api/dispatch-haul-ledger?carrier=<n>` (or equivalent) → hauling
- `GET /api/shop-intel?supplier=<n>` → repairs
- `GET /api/material-movement/daily?supplier=<n>&date_from=<x>` → materials moved
- Historical Records queue filtered by `entity_kind="vendor"&entity_id=<vendor_id>` → documents

**All existing endpoints. Zero new backend routes required to power reads.**

## Ownership rule
No new AP collection is proposed by this audit. Payments and invoicing remain **out of scope** for Track 19.60. If a payment surface is later added, its owner is **Accounting / AP** — never PM.
