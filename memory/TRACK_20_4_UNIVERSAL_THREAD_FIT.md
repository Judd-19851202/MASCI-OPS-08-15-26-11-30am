# TRACK 20.4 · Universal Thread Fit Matrix

| # | Universal Thread section    | Fillable today?      | Route / endpoint                                                                       | Adapter | Extension needed? | Build needed? |
|---|-----------------------------|:--------------------:|----------------------------------------------------------------------------------------|:-------:|:-----------------:|:-------------:|
| 1 | Mission Overview            | ✅ Almost            | `GET /api/suppliers` (find by name/id) + a couple of new status flags on the doc       | ✅      | Small (flags)     | ❌            |
| 2 | Attention                   | ✅ Almost            | Derived from COI expiration + do-not-use flag + PO overdue receipts (`/po-requests/summary`) | ✅ | Small (flags)     | ❌            |
| 3 | Operational Guidance        | Partial              | No `vendor_intelligence` OI product. Guidance derives from missing docs / expiring COIs. Suitable as explanatory copy, not a new OI product. | ✅ | ❌ | ❌ |
| 4 | Timeline                    | ✅                   | Union of `po_requests` events + `dispatch_haul_ledger` events + document uploads       | ✅      | ❌                | ❌            |
| 5 | Relationships               | ✅ (string-based)    | POs (`po_requests?supplier=`) + projects (derived) + PMs (derived)                     | ✅      | ❌                | ❌            |
| 6 | Documents                   | ❌ **Missing**       | Needs vendor lane in Historical Records                                                | ✅ (via extension) | ✅ (vendor lane) | ❌ |
| 7 | Photos                      | Honest empty         | Not applicable to most vendors                                                         | shell empty | ❌            | ❌            |
| 8 | Operational Intelligence    | ❌ No dedicated OI   | No new OI product required — thread renders honest empty for OI section OR reuses `corporate_intelligence` summary snippet | shell (with honest empty) | ❌ | ❌ |
| 9 | History                     | Partial              | Derived from PO history + document uploads + status changes                            | ✅      | ❌                | ❌            |
|10 | Audit                       | ❌                   | Needs vendor-scoped audit → derive from `historical_records_audit` on vendor entity   | ✅ (via extension) | Small (entity_kind filter) | ❌ |

## Delta from other threads
- Fleet / Employee / Project / Incident promotions were **pure frontend** because every section had a certified backend source.
- Vendor promotion is **PROMOTE + EXTEND (small)** because Documents + Audit need the vendor lane in Historical Records to exist.

## No new OI product
The Vendor Thread will NOT introduce a new OI product. Guidance and OI sections either reuse existing portfolio products or render honest empty.

## Estimated LOC
- Backend: ≤ 350 (schema discriminator + admin approve variant for vendor lane + optional richer supplier fields).
- Frontend: ≈ 500 (`AdminVendorThread.jsx` or `HrVendorThread.jsx` + adapters + vendor detail entry point).
- Lock test: ≈ 130.
