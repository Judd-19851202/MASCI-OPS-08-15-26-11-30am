TRACK 19.00 · TRANSPORTATION DRIVER + CARRIER OPERATIONS FOUNDATION
====================================================================

DATE          : 2026-06-29
RELEASE       : preview build f4ed6f08… → ships at next redeploy
ENV           : implemented in preview pod · operator redeploys to prod
DOCTRINE      : HR owns identity · Transportation owns operational readiness · Visible = Usable

────────────────────────────────────────────────────────────────────────────
WHAT WE BUILT
────────────────────────────────────────────────────────────────────────────
Track 19.00 turns Transportation Operations into a usable driver +
carrier operating base. Dispatchers and admins can now do real work
from inside Transportation Operations:

  · Find an HR CDL employee and idempotently link them into the
    Transportation haul-driver list (without ever overwriting HR
    identity).
  · Add a leased / carrier driver under an existing carrier.
  · Add and edit carriers (DOT, MC, contact, status, safety hold).

The HR ↔ Transportation distinction is enforced:
  · CDL drivers (HR `cdl_holder=true`) are Transportation candidates.
  · Non-CDL approved drivers (HR `approved_company_driver=true` only)
    stay in HR. They do NOT pollute the Transportation CDL list.

────────────────────────────────────────────────────────────────────────────
KEY DECISIONS
────────────────────────────────────────────────────────────────────────────
Permission policy (operator-approved):
  · Dispatcher CAN create/edit Transportation drivers AND carriers.
  · No new "Transportation Manager" role is introduced — that can be a
    follow-on track if MASCI wants tighter governance.
  · Admin-only governance endpoints (audit timeline governance, deep
    Intelligence admin analytics, HR sync governance, email route
    governance, Automation Health, etc.) REMAIN admin-only.

Workflow style: modal (in-context), not dedicated /new pages.

Backfill: dry-run-capable operator-run script. Not auto-run on boot.

────────────────────────────────────────────────────────────────────────────
BACKEND CHANGES
────────────────────────────────────────────────────────────────────────────
File: `/app/backend/routes/transportation.py`

| Endpoint                                                            | Before  | After                          |
|---------------------------------------------------------------------|---------|--------------------------------|
| `POST /api/admin/transportation/carriers`                           | admin   | dispatch + admin               |
| `PATCH /api/admin/transportation/carriers/{cid}`                    | admin   | dispatch + admin               |
| `POST /api/admin/transportation/persons`                            | admin   | dispatch + admin               |
| `PATCH /api/admin/transportation/persons/{pid}`                     | admin   | dispatch + admin               |
| `GET  /api/admin/transportation/eligible-hr-cdl-drivers`            | —       | dispatch + admin (NEW)         |
| `POST /api/admin/transportation/persons/link-from-hr`               | —       | dispatch + admin (NEW)         |

Audit events (already emitted by the existing `_audit` helper):
  · `transport_carrier_create` · `transport_carrier_update`
  · `transport_person_create` · `transport_person_update`
  · `transport_person_link_from_hr`  ← NEW (Track 19.00)

Duplicate-prevention is enforced server-side in two places:
  1. `find_existing_employee_projection` on POST `/persons` (existing).
  2. `link-from-hr` query for an existing `kind=masci_employee` row
     before insert; returns `already_linked=true` if present.

CDL guard:
  `link-from-hr` rejects any HR employee where `cdl_holder` is not
  truthy with HTTP 422 + canonical message:

      "Employee is not a CDL holder. Non-CDL approved drivers cannot
       be linked into the Transportation haul-driver list."

────────────────────────────────────────────────────────────────────────────
FRONTEND CHANGES
────────────────────────────────────────────────────────────────────────────
New file: `/app/frontend/src/pages/transportation/_modals.jsx`

Components:
  · `LinkHRDriverModal`     — picker over eligible HR CDL drivers.
                              Search + 50-row paginated list. Per-row
                              "Link" CTA that calls link-from-hr and
                              refreshes the list. Banned-term-free
                              error display.
  · `AddLeasedDriverModal`  — carrier select + driver identity +
                              license / CDL class + status + notes.
  · `AddCarrierModal`       — legal_name (required) + type + DOT + MC
                              + contact (name/phone/email) + status +
                              safety hold + notes.
  · `EditCarrierModal`      — same fields, pre-populated from the row.

All four modals send BOTH `X-Admin-Token` and `X-Dispatch-Token` so
they work for either role.

Wiring in `/app/frontend/src/pages/transportation/_lists.jsx`:
  · `CarriersList` now renders [Add Carrier] + per-row [Edit] CTAs.
  · `DriversList` now renders [Link MASCI CDL Driver] +
    [Add Leased Driver] CTAs.

Helpers added to `/app/frontend/src/pages/transportation/_shared.jsx`:
  · `txPost(path, body)` and `txPatch(path, body)` mirror `txGet`
    semantics — both portal tokens injected, ODS-safe.

────────────────────────────────────────────────────────────────────────────
BACKFILL SCRIPT
────────────────────────────────────────────────────────────────────────────
File: `/app/backend/scripts/track_19_00_link_hr_cdl_to_transport.py`

Default mode: DRY-RUN. Commit mode requires `--commit`.

Live preview run (dry-run) verified:
    HR CDL employees scanned     : 20
    already linked (no-op)       : 1
    would create / created       : 5 / 0
    skipped (missing emp_id)     : 0
    skipped (cdl_holder false)   : 0

Idempotent · no duplicate inserts · NOT wired to boot. Operator-run
only. Documented in `TRANSPORTATION_DRIVER_CARRIER_BACKFILL_PLAN.md`.

────────────────────────────────────────────────────────────────────────────
TESTS
────────────────────────────────────────────────────────────────────────────
File: `/app/backend/tests/test_track_19_00_transportation_driver_carrier_foundation.py`

Coverage:
  · all 7 required docs exist (parametrised)
  · eligible-hr-cdl-drivers returns only cdl_holder=true rows
  · eligible-hr-cdl-drivers excludes already-linked rows by default
  · eligible-hr-cdl-drivers accepts dispatch AND admin tokens
  · link-from-hr 404s on unknown employee
  · link-from-hr is idempotent (same id returned · already_linked=true)
  · dispatch can create a carrier
  · dispatch can patch a carrier
  · anonymous is blocked on both link-from-hr and carrier create
  · `cdl_holder` enforcement is present in the route source
  · classification doc distinguishes CDL vs non-CDL
  · backfill script exists with default dry-run
  · backfill script is NOT wired into server.py
  · frontend `_modals.jsx` exists with the four canonical testids
  · `_lists.jsx` renders the three new CTAs

────────────────────────────────────────────────────────────────────────────
DEFERRALS
────────────────────────────────────────────────────────────────────────────
  · Full FMCSA Clearinghouse query/result tracking (separate compliance
    integration; HR already tracks medical-card + license expirations
    and surfaces them in the picker).
  · "External / temporary driver" classification beyond carrier-linked
    leased drivers (no current use case).
  · A dedicated "Transportation Manager" role with narrower write
    permissions than dispatcher (out of scope; this track uses
    dispatcher-can-write).
  · Insurance / W9 / agreement field modelling on the carrier doc
    beyond what already exists. The current carrier model exposes
    legal_name / dba / type / DOT / MC / contact / status / safety
    hold / notes. Compliance status fields can be layered in a
    follow-on track without rework.

────────────────────────────────────────────────────────────────────────────
RISKS / WATCH ITEMS
────────────────────────────────────────────────────────────────────────────
  · Visible = Usable now requires that any dispatcher seeing the
    Drivers / Carriers list also sees the new CTAs. The buttons render
    unconditionally — the underlying endpoints will gate writes if a
    future role is added that should not write.
  · The legacy non-CDL `approved_company_driver` field is still
    surfaced inside the eligible-HR list (read-only) so operators can
    see when an employee is both CDL and approved-non-CDL. The
    classification doc warns operators that approved_company_driver=true
    alone is NOT a qualifier for Transportation linking.

────────────────────────────────────────────────────────────────────────────
DEPLOY READINESS
────────────────────────────────────────────────────────────────────────────
  · Backend boots cleanly (verified live `/api/health` 200 after edit).
  · Lint clean (Python + JavaScript).
  · No new collections, no destructive migrations, no schema breaks.
  · Backwards-compatible — admin clients keep working unchanged.
  · Operator action at next redeploy:
      1. Re-deploy the preview build.
      2. Optionally run the backfill script against the production
         Atlas DB with `--commit` after a `--dry-run` review.
