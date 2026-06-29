TRACK 19.00 · HR DRIVER MODEL AUDIT
====================================

DATE   : 2026-06-29
SCOPE  : Audit the HR-owned source of truth for driver identity,
         CDL credentials, and approval state. Confirms what already
         exists and what Track 19.00 should pull from (vs. duplicate).

────────────────────────────────────────────────────────────────────────────
COLLECTION
────────────────────────────────────────────────────────────────────────────
`employees`  ← single source of truth for employee identity and HR
driver-qualification data. NO new collection introduced by Track 19.00.

────────────────────────────────────────────────────────────────────────────
FIELDS (HR-owned, projected through HR endpoints)
────────────────────────────────────────────────────────────────────────────
Identity:
  · `id`                              UUID per row
  · `employee_id`                     canonical HR employee id (preferred)
  · `name`                            full display name
  · `first_name` / `last_name`        when split
  · `phone`, `email`                  contact baseline
  · `trade`                           e.g. "Driver", "Operator"
  · `supervisor`                      employee id of supervisor
  · `lifecycle_status`                "Active" / "Inactive"
  · `deleted_at`                      soft delete (null if active)

CDL credential:
  · `cdl_holder`                      bool  — IS this a CDL driver?
  · `cdl_class`                       "A" / "B" / "C"
  · `cdl_state`                       2-letter state
  · `cdl_license_number`              string
  · `cdl_expiration_date`             ISO date string
  · `cdl_endorsements`                array (N · H · P · S · T · X)
  · `cdl_restrictions`                array

Medical:
  · `medical_card_expiration_date`    ISO date string

Approved non-CDL drivers (separate concept):
  · `approved_company_driver`         bool  — approved to drive
                                              company / non-CDL vehicles.
                                              NOT a haul driver.

Operational status (HR-side):
  · `driver_status`                   "active" · "suspended" · "restricted" · "inactive"

────────────────────────────────────────────────────────────────────────────
ENDPOINTS THAT EXPOSE THIS MODEL
────────────────────────────────────────────────────────────────────────────
  · `GET /api/hr/driver-qualification/dashboard`              · HR
  · `GET /api/dispatch/driver-qualification/dashboard`        · Dispatch
  · `GET /api/field-leadership/driver-qualification/dashboard`· FL

All three are served by the SAME helper:
  `lib/driver_qualification.py :: fetch_driver_qualification_dashboard`

Projection is shared and intentionally narrow — no email / phone /
private notes leak into Dispatch or Field Leadership views.

Allowed driver_status values (constant): {active, suspended, restricted, inactive}.

────────────────────────────────────────────────────────────────────────────
FRONTEND SURFACES (HR)
────────────────────────────────────────────────────────────────────────────
  · HR Workspace → Driver Qualification dashboard
  · HR Workspace → Employees → Employee detail (CDL panel)
  · Dispatch / Field Leadership read the same data via the helper.

Add / edit flows for CDL fields are HR-owned — Transportation must
NOT round-trip identity writes back to HR.

────────────────────────────────────────────────────────────────────────────
PERMISSIONS
────────────────────────────────────────────────────────────────────────────
  · HR can read / write all CDL identity fields.
  · Safety can read the safety-relevant subset.
  · Dispatch + Field Leadership get a READ-ONLY projection.
  · Admin has full oversight.

────────────────────────────────────────────────────────────────────────────
GAPS BEFORE TRACK 19.00
────────────────────────────────────────────────────────────────────────────
  · There was NO way to expose "eligible HR CDL drivers, minus the
    ones already in Transportation" to an operator inside
    Transportation Operations.
  · There was NO convenience endpoint to link a single HR CDL
    employee into Transportation idempotently.

────────────────────────────────────────────────────────────────────────────
TRACK 19.00 CLOSURE
────────────────────────────────────────────────────────────────────────────
Track 19.00 adds two READ/WRITE endpoints — neither edits HR data:
  · `GET  /api/admin/transportation/eligible-hr-cdl-drivers`   (NEW)
  · `POST /api/admin/transportation/persons/link-from-hr`      (NEW)

Both endpoints READ from `employees` and WRITE only into
`transport_persons`. HR remains the source of truth for identity.

────────────────────────────────────────────────────────────────────────────
SOURCE-OF-TRUTH RECOMMENDATION
────────────────────────────────────────────────────────────────────────────
HR `employees` REMAINS source of truth for:
  · legal identity
  · employment lifecycle
  · CDL credential record
  · medical card record
  · approved_company_driver flag
  · employee phone / email baseline

Transportation `transport_persons` IS source of truth for:
  · whether the employee is operationally usable in Transportation
  · transportation status (pending_review / active / suspended / inactive)
  · safety hold (transportation-side)
  · transportation notes
  · dispatch eligibility plumbing
