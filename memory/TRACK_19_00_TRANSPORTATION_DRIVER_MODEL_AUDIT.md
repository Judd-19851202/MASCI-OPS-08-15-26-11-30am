TRACK 19.00 · TRANSPORTATION DRIVER MODEL AUDIT
================================================

DATE   : 2026-06-29
SCOPE  : Audit `transport_persons` and the supporting endpoints,
         dispatch eligibility plumbing, and the new Track 19.00 link /
         create writes.

────────────────────────────────────────────────────────────────────────────
COLLECTION
────────────────────────────────────────────────────────────────────────────
`transport_persons`  — single source of truth for Transportation
driver records (both MASCI employees and leased / carrier drivers).

────────────────────────────────────────────────────────────────────────────
DOCUMENT SHAPE
────────────────────────────────────────────────────────────────────────────
Identity / linkage:
  · `id`                              UUID
  · `tenant`                          "masci"
  · `kind`                            "masci_employee" | "leased_driver"
  · `employee_id`                     populated when kind=masci_employee (→ HR)
  · `carrier_id`                      populated when kind=leased_driver (→ carriers)

Identity snapshot (operational, copied from HR at link time — HR is the
source of truth):
  · `first_name` / `last_name`
  · `phone`, `email`
  · `license_number`, `cdl_class`

Transportation-owned operational state:
  · `status`                          "pending_review" · "active" · "suspended" · "inactive"
  · `safety_hold`                     bool — transportation-side hold
  · `notes`                           transportation operations notes

Audit / link metadata (Track 19.00):
  · `linked_from_hr_at`               ISO timestamp (set by link-from-hr)
  · `linked_from_hr_by`               actor label
  · `created_at`, `created_by`
  · `updated_at`, `updated_by`

────────────────────────────────────────────────────────────────────────────
ENDPOINTS
────────────────────────────────────────────────────────────────────────────
| Endpoint                                                  | Read     | Write          |
|-----------------------------------------------------------|----------|----------------|
| GET    /api/admin/transportation/persons                  | dispatch | —              |
| GET    /api/admin/transportation/persons/{pid}            | dispatch | —              |
| POST   /api/admin/transportation/persons                  | —        | dispatch+admin |
| PATCH  /api/admin/transportation/persons/{pid}            | —        | dispatch+admin |
| POST   /api/admin/transportation/persons/link-from-hr     | —        | dispatch+admin (NEW) |
| GET    /api/admin/transportation/eligible-hr-cdl-drivers  | dispatch | —              (NEW) |

`require_dispatch_or_admin_dep` is the cross-role guard.

────────────────────────────────────────────────────────────────────────────
DUPLICATE PREVENTION
────────────────────────────────────────────────────────────────────────────
  · POST `/persons` — `find_existing_employee_projection` and
    `find_existing_leased_driver` block duplicates by employee_id or
    by carrier_id + license_number / name.
  · POST `/persons/link-from-hr` — checks `transport_persons` for an
    existing `kind=masci_employee` row with the same `employee_id`
    and returns `{already_linked: true}` instead of inserting.

────────────────────────────────────────────────────────────────────────────
FRONTEND
────────────────────────────────────────────────────────────────────────────
Surface: `/transportation-operations/drivers` and
`/admin/transportation/drivers/{id}`.

Component: `/app/frontend/src/pages/transportation/_lists.jsx :: DriversList`.

Track 19.00 added:
  · CTA `[Link MASCI CDL Driver]` → `LinkHRDriverModal`
  · CTA `[Add Leased Driver]`     → `AddLeasedDriverModal`
  · No restricted banner on the core operational page.

────────────────────────────────────────────────────────────────────────────
DISPATCH ELIGIBILITY
────────────────────────────────────────────────────────────────────────────
`_upsert_eligibility` materialises a row in `transport_eligibility_state`
for each person, key = (target_type="person", target_id=person.id). On
link-from-hr the eligibility row is computed with the HR context
(`_hr_lifecycle_context` reads lifecycle_status, CDL/medical
expirations) so dispatch can immediately see why the driver is or is
not eligible.

────────────────────────────────────────────────────────────────────────────
SEARCH / RIGHT RAIL
────────────────────────────────────────────────────────────────────────────
`transport_persons` rows already participate in the existing
Transportation Search index and Right Rail relationships (carrier ↔
drivers, drivers ↔ orientation / certificates / documents). No new
search index needed.

────────────────────────────────────────────────────────────────────────────
PRE-TRACK 19.00 GAPS
────────────────────────────────────────────────────────────────────────────
  · POST/PATCH endpoints were admin-only — dispatchers could see
    drivers but could not maintain them.
  · There was no UI for adding or linking drivers from inside
    Transportation Operations.
  · No idempotent "Link HR CDL driver" path.

────────────────────────────────────────────────────────────────────────────
POST-TRACK 19.00 STATE
────────────────────────────────────────────────────────────────────────────
  · Dispatchers can create / edit / link drivers from inside
    Transportation Operations.
  · HR identity remains protected — `link-from-hr` only WRITES to
    `transport_persons` and never to `employees`.
  · Audit events fire on every create / update / link.
  · Frontend modals are operational and use
    `data-testid="link-hr-driver-modal" / "add-leased-driver-modal"`.
