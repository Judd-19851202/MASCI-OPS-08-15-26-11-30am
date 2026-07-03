# TRACK 19.60 · Vendor Thread Promotion

## Route
`/admin/vendors/:vendorId/thread` — behind `RequireAdmin` (`A(...)`).
Page-level guard: `isAdmin()` → `<AccessDenied attemptedPortal="admin" />` otherwise.

## Section-by-section wiring
| # | Section                  | Adapter                | Source                                                         |
|---|--------------------------|------------------------|----------------------------------------------------------------|
| 1 | Mission Overview         | `missionAdapter`       | `/api/suppliers` (find by id/name) + document counts + `vendorHealth` |
| 2 | Attention                | `attentionAdapter`     | `is_active` + missing W-9 / COI + pending approvals            |
| 3 | Operational Guidance     | shell (unchanged)      | Honest empty — no vendor OI product exists                     |
| 4 | Timeline                 | `timelineAdapter`      | Vendor-lane records ordered by `approved_at` / `updated_at` / `created_at` |
| 5 | Relationships            | `relationshipAdapter`  | HR/Admin owner · document counts · PO history (matched by supplier name) · supplier master |
| 6 | Documents                | `documentsAdapter`     | `/employee-records/records?entity_kind=vendor&vendor_id=…` (fallback: `vendor_name`) |
| 7 | Photos                   | shell empty            | Honest empty — vendors do not have photos                       |
| 8 | Operational Intelligence | shell empty            | Honest empty — no vendor OI product                            |
| 9 | History                  | shell empty            | Honest empty — history lives in Historical Records Queue        |
|10 | Audit                    | shell empty            | Honest empty — audit lives in Historical Records Audit (Admin-only) |

## Universal Action Queue (max 5)
Composed from: missing W-9, missing COI, missing Contract, pending approvals count, inactive-vendor guard. Auto-capped at 5. Specific verbs (Upload · Approve · Verify · Restore) — no "monitor / review / watch".

## Cross-links (surgical)
- `admin-vendor-thread-upload-link` → `/hr/historical-records/intake?entity_kind=vendor&vendor_id=<id>` — HR/Admin can add another vendor document in one click.
- `admin-vendor-thread-master-link` → `/admin` — return to the admin hub.

## Nothing new
No new backend route. No new collection. No new PDF renderer. No new OI product. No new score model. No new AP / invoice / payment / contract engine.
