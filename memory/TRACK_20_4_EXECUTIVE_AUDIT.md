# TRACK 20.4 · Executive Audit

## Verdict
🟢 **PROMOTE + EXTEND (small).**

## One-paragraph summary
Unlike Employee, Fleet, Project, and Incident — where the full operational thread already existed and required only presentation adapters — the Vendor operational surface today is a **thin foundation with real gaps**. The certified pieces present are: (a) a name-only `suppliers` master (9 endpoints under `/api/suppliers` + `/api/admin/suppliers/*`) used for PO/DR autocomplete; (b) a rich PO Requests system (`/api/po-requests/*`, 12+ endpoints) that references vendors by string; (c) a Historical Records Intake pipeline that is currently **employee-only** by design; (d) a supplier picker component (`SupplierCombo`), a supplier master panel (`SupplierMasterPanel`), and a PM read-only supplier roster page (`PmSuppliers`). The certified pieces absent today are: W-9 storage, COI / insurance-certificate storage, contracts, subcontract agreements, business licenses, quotes/bids, invoices, payments, vendor performance history, prequalification records, do-not-use flags, dedicated vendor-document lanes, and a Vendor detail page. Every Universal Thread section except **Documents** can be filled via adapters over existing endpoints; **Documents** requires a small EXTENSION to Historical Records Intake to introduce a vendor lane. **No new vendor score. No new PDF. No new contract engine.** Estimated Track 19.60 build cost: ≤ 350 backend LOC (vendor lane in HR intake · optional richer supplier fields) + ≈ 500 frontend LOC (thread page + AdminSuppliers detail) + 1 lock file.

## Certified endpoints identified today
### Supplier master (name-only)
- `GET /api/suppliers` — public list
- `POST /api/suppliers/add` — via `SupplierCombo` (open-ended add)
- `GET /api/admin/suppliers/status` · `/archive`
- `POST /api/admin/suppliers` · `/admin/suppliers/upload` · `/admin/suppliers/{id}/restore`
- `PUT /api/admin/suppliers/{id}` · `DELETE /api/admin/suppliers/{id}`
- `GET /api/admin/suppliers/export`

### Purchase Orders (rich)
- `GET /api/po-requests` · `POST /api/po-requests` · `GET /api/po-requests/{po_id}`
- `POST /api/po-requests/{po_id}/approve` · `/receipt` · `/close` · `/cancel` · `/respond-clarification`
- `GET /api/po-requests/summary` · `/export.csv`
- `POST /api/admin/po-requests/scan-missing-receipts`

### Historical Records Intake (employee-scoped today)
- `HistoricalRecordsIntake.jsx` · `HistoricalRecordsQueue.jsx` · `HistoricalRecordsBatches.jsx` · `HistoricalRecordsBatchDetail.jsx`

### Cross-portal readers
- `PmSuppliers` — PM read-only roster
- `SupplierMasterPanel` — Admin panel
- `SupplierCombo` — inline picker across PO/DR/Meeting/Constraint/Incident forms

## Why PROMOTE + EXTEND (and not the others)
- **NOT `PROMOTE EXISTING FOUNDATION`** — a name-only supplier list is not a Universal Thread. It cannot answer "is this vendor healthy?" or "what did they deliver?" without extension.
- **NOT `PROMOTE + ADAPTERS`** — Documents (W-9, COI, contracts) do not exist in any certified collection. Filling that section with adapters over the current schema would misrepresent the state.
- **NOT `BUILD NEW`** — Suppliers + POs + Historical Records already give ~ 70 % of the operational picture. Building parallel systems duplicates ownership and violates the mandate.
- **YES `PROMOTE + EXTEND (small)`** — surgically extend Historical Records Intake with a **vendor lane** (parallel to the employee lane) and enrich the supplier record with a small set of status flags (W-9 on file · COI expiration · approved · do-not-use). Zero replacement of existing storage. Fully backwards-compatible.
