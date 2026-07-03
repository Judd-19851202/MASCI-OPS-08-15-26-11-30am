# TRACK 20.4 · Vendor Surface Inventory

## Frontend surfaces (certified · in use)
| Surface                                       | Path                                                       | Portal            | Purpose                                              |
|-----------------------------------------------|------------------------------------------------------------|-------------------|------------------------------------------------------|
| PM Suppliers (read-only)                      | `pages/pm/PmSections.jsx` → `PmSuppliers`                  | PM                | Approved supplier roster                             |
| Supplier Master Panel                         | `components/SupplierMasterPanel.jsx`                       | Admin             | CRUD + upload + archive                              |
| Supplier Combo (inline picker)                | `components/SupplierCombo.jsx`                             | Cross-portal      | Type-to-add name in PO/DR/Meeting/Constraint/Incident|
| PO Requests                                   | `pages/PoRequests.jsx`                                     | PM · HR · Admin   | Rich PO CRUD, receipts, approvals                    |
| Historical Records Intake                     | `pages/HistoricalRecordsIntake.jsx`                        | HR / Admin        | **Employee-scoped today**                             |
| Historical Records Queue / Batches / Batch    | `pages/HistoricalRecords{Queue,Batches,BatchDetail}.jsx`   | HR / Admin        | **Employee-scoped today**                             |
| Admin Equipment (includes suppliers side)     | `pages/admin/AdminEquipment.jsx`                           | Admin             | "Equipment & Suppliers" combined section              |

## Backend modules relevant to vendors
| Module                                                | Purpose                                                                        |
|-------------------------------------------------------|--------------------------------------------------------------------------------|
| `backend/server.py` — `/suppliers` + `/admin/suppliers/*` | Name-only supplier master · 9 endpoints                                    |
| `backend/routes/po_requests.py`                       | Full PO Requests router — 12+ endpoints                                        |
| `backend/routes/po_digest_admin.py` + `po_digest.py`  | Digest of PO health / overdue receipts                                          |
| `backend/routes/dispatch_haul_ledger.py`              | Trucking / hauling flows — vendor referenced as string                          |
| `backend/routes/transportation.py`                    | Carrier compliance (has `insurance_certificate` + `w9` + `hauling_agreement`) — **carrier-scoped, not general vendor** |
| `backend/routes/document_expirations.py`              | Generic document expiration tracker                                             |
| `backend/routes/employee_lifecycle.py`                | Historical Records Intake backend (employee-scoped)                             |

## Data collections
| Collection                    | Scope        | Status                                                        |
|-------------------------------|-------------|---------------------------------------------------------------|
| `suppliers`                   | Vendors      | ✅ Present — name-only                                        |
| `po_requests`                 | POs          | ✅ Present — rich schema, references vendor by string          |
| `historical_records`          | Employees    | ✅ Present — employee-scoped intake                            |
| `transport_docs` / equivalent | Carriers     | ✅ Present — W-9/COI/hauling agreement for carriers only       |
| `document_expirations`        | Cross-cutting| ✅ Present — generic doc expiration tracker                    |
| `contracts`                   | —            | ❌ **Missing** — no dedicated contract collection              |
| `vendor_documents`            | —            | ❌ **Missing** — no vendor-scoped document lane                |
| `vendor_prequalification`     | —            | ❌ **Missing**                                                 |
| `vendor_performance`          | —            | ❌ **Missing** (implicit via PO receipt notes)                 |
| `vendor_invoices`             | —            | ❌ **Missing**                                                 |
| `vendor_payments`             | —            | ❌ **Missing**                                                 |

## PDFs / report packages
- None specific to vendors today. PO packages exist but no "Vendor Package" PDF exists.

## Cross-portal touchpoints
| Consumer surface        | Vendor touchpoint                                              | Notes                                            |
|-------------------------|----------------------------------------------------------------|--------------------------------------------------|
| `HrEmployees.jsx`       | Deep-links to `/po-requests?id=...`                            | HR reviews open POs by employee                  |
| `ProjectHealth.jsx`     | PO widgets by status                                           | Project-scoped                                    |
| `PmHubV2.jsx`           | `po_pending_approval` / `po_pending_receipt` / `po_overdue_receipt` chips | Portfolio                             |
| `PoRequests.jsx`        | Direct PO CRUD                                                 | Vendor by string                                  |
| `NewDailyReport.jsx`    | Supplier picker (`SupplierCombo`)                              | Vendor by string                                  |
| `NewMeeting.jsx`        | Supplier picker                                                | Vendor by string                                  |
| `NewConstraint.jsx`     | Supplier picker                                                | Vendor by string                                  |
| `NewIncident.jsx`       | Supplier picker                                                | Vendor by string                                  |
| `TransportationOnboardingCompliance` | Carrier-scoped W-9/COI                            | Carriers only, not general vendors                |

## Gaps summarised
- **No unified vendor detail page** exists today.
- **No document lane for vendor-scoped uploads** (W-9, COI, contract, license).
- **No contract engine** — draft / review / send / signature / renewal.
- **No prequalification record**.
- **No performance history collection** (only implicit via PO history).
- **No do-not-use / restricted status flag**.
- **No vendor-scoped audit trail**.
