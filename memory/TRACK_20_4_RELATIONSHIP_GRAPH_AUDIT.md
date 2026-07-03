# TRACK 20.4 · Relationship Graph Audit

| Node                           | Grounded in                                                | Route?                                                              | Clickable? | Notes                                     |
|--------------------------------|------------------------------------------------------------|---------------------------------------------------------------------|:----------:|-------------------------------------------|
| Vendor (subject)               | `db.suppliers`                                             | `/api/suppliers` (list) · `/admin/suppliers/{id}` (mutate)          | Self       | Master record                             |
| Projects                       | `po_requests.project_number` join                          | `/api/pm/jobs` / Project Thread                                     | ✅         | Weak — name-based                         |
| PMs (approvers)                | `po_requests.approvals[]`                                  | Employee Thread                                                     | ✅         | If HR permission allows                   |
| POs                            | `po_requests` (supplier name string)                       | `/po-requests?supplier=<n>`                                         | ✅         | —                                         |
| Contracts                      | Vendor lane of Historical Records                          | `/historical-records/queue?entity_kind=vendor&entity_id=<id>`       | ✅ (later) | Requires extension                        |
| Invoices                       | *(not stored today)*                                       | Gap                                                                 | ❌         | Show honest empty                         |
| Payments                       | *(not stored today)*                                       | Gap                                                                 | ❌         | Show honest empty                         |
| COIs                           | Vendor lane of Historical Records + expiration signal      | Same as contracts                                                   | ✅ (later) | Extension                                 |
| W-9                            | Vendor lane of Historical Records                          | Same                                                                | ✅ (later) | Extension                                 |
| Contacts                       | *(not stored today)*                                       | Gap                                                                 | ❌         | Show honest empty                         |
| Materials                      | `material_movement_daily`                                  | Existing endpoint                                                   | Text-only  | Name-based                                |
| Dispatches                     | `dispatch_haul_ledger`                                     | Existing endpoint                                                   | ✅         | Name-based                                |
| Equipment / rentals            | Fleet endpoints                                            | Existing                                                            | Text-only  | Weak link                                 |
| Repairs                        | `shop_intel`                                               | Existing                                                            | ✅         | Name-based                                |
| Incidents                      | `incident_cases.involved_parties` + `cross_links`          | Incident Thread                                                     | ✅         | If Safety permission allows               |
| Safety documents               | Vendor lane of Historical Records                          | Same                                                                | ✅ (later) | Extension                                 |
| Performance notes              | *(not stored today)*                                       | Gap                                                                 | ❌         | Show honest empty                         |
| Documents (generic)            | Vendor lane of Historical Records                          | Same                                                                | ✅ (later) | Extension                                 |
| Audit                          | `historical_records_audit` filtered by entity              | Same                                                                | Admin only | Extension                                 |

## Rules
- No fake edges. Where the join key is a string, the edge is labelled "match by name".
- Missing categories render honest-empty in the thread. **Never fabricate a fact.**
- Cross-portal deep-links respect the destination's own permission gate.
