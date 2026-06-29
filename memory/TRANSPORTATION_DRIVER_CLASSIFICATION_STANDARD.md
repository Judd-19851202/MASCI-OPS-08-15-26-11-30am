TRANSPORTATION DRIVER CLASSIFICATION STANDARD
==============================================

DOCTRINE :  HR identity is the source of truth. Transportation
            operational readiness is the source of truth for what a
            dispatcher can actually use. Do NOT mix the two.

────────────────────────────────────────────────────────────────────────────
THE FOUR CLASSES
────────────────────────────────────────────────────────────────────────────

1. MASCI CDL Driver
   -------------------
   HR `employees` row where `cdl_holder = true`.
   Has CDL credential fields populated (cdl_class, cdl_license_number,
   cdl_state, cdl_expiration_date, medical_card_expiration_date).
   ELIGIBLE to be linked into Transportation as `transport_persons`
   with `kind = masci_employee`.

   Example: HR Driver Qualification Dashboard rows with CDL=true.

2. MASCI Non-CDL Approved Driver
   ------------------------------
   HR `employees` row where:
     · `cdl_holder = false` (or unset)
     · `approved_company_driver = true`
   This employee is approved to operate company vehicles that do NOT
   require a CDL. They are NOT a haul driver. They MUST NOT appear in
   the Transportation CDL driver operating list.

   Track 19.00 enforcement:
     · `GET /api/admin/transportation/eligible-hr-cdl-drivers` filters
       on `cdl_holder=true` — these employees do not appear.
     · `POST /api/admin/transportation/persons/link-from-hr` rejects
       these employees with HTTP 422 and the canonical message
       "Employee is not a CDL holder."

3. Carrier Driver (Leased Driver)
   --------------------------------
   `transport_persons` row where `kind = leased_driver` and
   `carrier_id` points at a row in `carriers`. NOT an HR employee.
   Identity is owned by Transportation (no HR link).

   Created via the "Add Leased Driver" modal in Transportation
   Operations · Drivers.

4. Inactive / Not Dispatch-Eligible
   ---------------------------------
   ANY of the three classes above with one of:
     · `transport_persons.status` ∈ {"suspended", "inactive"}
     · `transport_persons.safety_hold = true`
     · HR `employees.lifecycle_status = "Inactive"`
     · CDL or medical card expired
   These rows remain visible in the Drivers list with a chip indicating
   the blocker, but are NOT returned by
   `/api/dispatch/transportation/eligible-drivers`.

────────────────────────────────────────────────────────────────────────────
SOURCE-OF-TRUTH MATRIX
────────────────────────────────────────────────────────────────────────────
| Field                              | Owner          | Editable in Transportation? |
|------------------------------------|----------------|-----------------------------|
| name / first_name / last_name      | HR (employees) | NO (copy at link time)      |
| phone / email                      | HR             | snapshot only               |
| cdl_holder                         | HR             | NO                          |
| approved_company_driver            | HR             | NO                          |
| cdl_class / cdl_license_number     | HR             | NO (snapshot only)          |
| cdl_state                          | HR             | NO                          |
| cdl_expiration_date                | HR             | NO                          |
| medical_card_expiration_date       | HR             | NO                          |
| lifecycle_status (Active/Inactive) | HR             | NO                          |
| transport_persons.status           | Transportation | YES                         |
| transport_persons.safety_hold      | Transportation | YES                         |
| transport_persons.notes            | Transportation | YES                         |
| carriers.* (identity + status)     | Transportation | YES                         |

If an HR-owned field is wrong (e.g. CDL expiration mistyped), the
operator goes to HR. The Transportation modal shows the snapshot for
context, but does NOT round-trip writes back to HR.

────────────────────────────────────────────────────────────────────────────
WHAT THIS PREVENTS
────────────────────────────────────────────────────────────────────────────
  · A non-CDL approved company driver (e.g. a foreman approved to
    drive a pickup truck) ending up in the Transportation haul-driver
    list and being dispatched on a truck they cannot legally operate.
  · Transportation silently editing an HR employee's CDL number or
    medical card date — the credential record must remain HR-owned.
  · Duplicate driver rows when an HR CDL driver is linked twice.

────────────────────────────────────────────────────────────────────────────
WHAT THIS ENABLES
────────────────────────────────────────────────────────────────────────────
  · Dispatchers can find every CDL driver HR has on file, in one
    place, inside Transportation Operations.
  · Carrier drivers can be created and managed without going through
    HR (they aren't HR employees).
  · Dispatch eligibility recomputes immediately on link via the
    shared `_upsert_eligibility` materialiser.
