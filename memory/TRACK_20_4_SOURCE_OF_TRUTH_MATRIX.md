# TRACK 20.4 · Source-of-Truth Matrix

Exactly one authoritative owner per category. If two owners exist → architectural defect.

| Category                     | Authoritative source (today)                                         | Owner portal   | Duplicate? | Gap? |
|------------------------------|----------------------------------------------------------------------|----------------|:----------:|:----:|
| Vendor legal name / DBA      | `db.suppliers.name`                                                  | HR / Admin     | ❌         | ❌   |
| Vendor type / classification | *(no field today)*                                                   | —              | —          | ✅   |
| Tax ID / EIN                 | *(not stored today)*                                                 | —              | —          | ✅   |
| W-9                          | *(not stored generically today; carrier subset in `transport_docs`)* | —              | —          | ✅ (except carriers) |
| Insurance / COI              | *(carrier subset in `transport_docs.insurance_certificate`)*         | —              | —          | ✅ (except carriers) |
| Business license             | *(not stored today)*                                                 | —              | —          | ✅   |
| Contracts / subcontracts     | *(not stored today)*                                                 | —              | —          | ✅   |
| Scopes                       | Embedded in `po_requests.description`                                | HR / PM        | ❌         | Partial |
| Purchase orders              | `db.po_requests` → `/api/po-requests/*`                              | HR / PM        | ❌         | ❌   |
| Quotes / bids / proposals    | *(not stored today)*                                                 | —              | —          | ✅   |
| Invoices                     | *(not stored today; PO receipts capture partial data)*               | —              | —          | ✅   |
| Payments                     | *(not stored today)*                                                 | —              | —          | ✅   |
| Contact person / phone / email / address | *(not stored today)*                                     | —              | —          | ✅   |
| Projects worked              | Derivable from `po_requests` join on `project_number`                | HR / PM        | ❌         | ❌   |
| Materials supplied           | Derivable from `po_requests.description`                             | HR / PM        | ❌         | Partial |
| Trucking / hauling records   | `db.dispatch_haul_ledger`                                            | Dispatch       | ❌         | ❌   |
| Repair / service records     | Shop intel (`shop_intel.py`)                                         | Shop           | ❌         | ❌   |
| Rental equipment             | Equipment / fleet-ops                                                | Fleet          | ❌         | ❌   |
| Incidents involving vendor   | `incident_cases.involved_parties` (if populated) + cross-links       | Safety         | ❌         | Partial |
| Safety issues                | Safety cases (via cross-link) + carrier compliance                   | Safety         | ❌         | Partial |
| Performance notes            | *(not stored today)*                                                 | —              | —          | ✅   |
| Document uploads             | *(carriers via `transport_docs`; general vendors: none)*             | —              | —          | ✅   |
| Historical imports           | `HistoricalRecordsIntake` — employee-scoped                          | HR             | ❌         | ✅ (vendor lane needed) |
| Approvals                    | *(no explicit vendor-approval workflow today)*                       | —              | —          | ✅   |
| Status                       | `db.suppliers.is_active`                                             | Admin          | ❌         | Partial (needs do-not-use flag) |
| Inactive / do-not-use        | `db.suppliers.is_active=false` (soft)                                | Admin          | ❌         | Partial (no dedicated "do-not-use" flag) |
| Audit trail                  | *(no vendor-scoped audit today; PO has audit)*                       | —              | —          | ✅   |

## Duplicate-storage certificate
**No duplicate storage detected among categories that already exist.** The gaps are missing storage, not competing storage.

## Ownership doctrine (proposed for Track 19.60 · not enforced by this audit)
- **HR / Administration** owns the vendor master (writes to `suppliers` + future vendor documents).
- **Accounting / AP** owns payment fields *if* they are added later.
- **Admin / Super Admin** retains final authority over do-not-use flags.
- **PM · Safety · Shop · Fleet · Dispatch · Ops · Executive** are **read-only consumers** of the Vendor Thread via role-aware lenses.

If today's platform diverges from that doctrine, document it here but do not fix it.
