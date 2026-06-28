TRACK 18.12C · TRANSPORTATION ROLE PERMISSIONS REAL FUNCTIONALITY FIX
======================================================================

DATE   : 2026-02-15
STATUS : ✅ GO (Super Admin + Dispatch both verified live)
SCOPE  : Reclassify core operational Transportation workspaces from
         admin-only to dispatcher-operational at the BACKEND level so
         dispatchers can actually run trucking. Frontend now routes
         both `X-Admin-Token` and `X-Dispatch-Token` headers on every
         Transportation read. Restricted banners are reserved for
         genuinely admin-only governance surfaces (Audit Timeline,
         Intelligence dashboard, Automation Health writes, Email Routes,
         HR Sync, Orientation Module CMS).

────────────────────────────────────────────────────────────────────────────
ROOT CAUSE OF 18.12B REJECTION
────────────────────────────────────────────────────────────────────────────
18.12B silenced 401/403 with restricted banners but left the underlying
admin-only gates in place. A dispatcher could click Drivers, Carriers,
Trucks, Orientation, Compliance — and see a calm "not available for your
role" state instead of crashing — but they STILL could not operate the
platform. The platform was treating core trucking workspaces as admin
governance surfaces, which is architecturally wrong: Administration
governs, Transportation Operations EXECUTES.

────────────────────────────────────────────────────────────────────────────
FIX SHAPE
────────────────────────────────────────────────────────────────────────────
1. BACKEND — switched the following READ endpoints from
   `Depends(require_admin_dep)` to `Depends(require_dispatch_or_admin_dep)`
   (a.k.a. `ops_guard` alias). The dispatch-or-admin gate validates
   both `X-Admin-Token` and `X-Dispatch-Token` and falls back to
   admin-strict when no dispatch dep is wired (so admin callers
   continue to authenticate cleanly).

   /api/admin/transportation/carriers                      (list)
   /api/admin/transportation/carriers/{cid}                (read)
   /api/admin/transportation/carriers/{cid}/workspace      (read)
   /api/admin/transportation/persons                       (list — drivers)
   /api/admin/transportation/persons/{pid}                 (read)
   /api/admin/transportation/persons/{pid}/workspace       (read)
   /api/admin/transportation/trucks                        (list)
   /api/admin/transportation/trucks/{tid}                  (read)
   /api/admin/transportation/trucks/{tid}/workspace        (read)
   /api/admin/transportation/eligibility/{type}/{id}       (read)
   /api/admin/transportation/dashboard                     (compliance summary)
   /api/admin/transportation/documents/queue               (review queue)
   /api/admin/transportation/inspections/queue             (review queue)
   /api/admin/transportation/timeline/{type}/{id}          (per-entity timeline)
   /api/admin/transportation/orientation/dashboard         (summary)
   /api/admin/transportation/orientation/modules           (list — read)
   /api/admin/transportation/orientation/modules/{id}/questions (read)
   /api/admin/transportation/orientation/assignments       (list)
   /api/admin/transportation/orientation/certificates      (list)
   /api/admin/transportation/automation/actions            (Morning Queue read)
   /api/admin/transportation/automation/forecast           (30-day forecast read)
   /api/admin/transportation/intelligence/cleanup-signals  (Mission Control card)
   /api/admin/transportation/intelligence/cleanup-signals/{key} (drill-down)

2. BACKEND · STILL ADMIN-STRICT (Class C — governance):
   /api/admin/transportation/audit-timeline               (compliance trail)
   /api/admin/transportation/intelligence/dashboard       (Executive)
   /api/admin/transportation/intelligence/recommendations
   /api/admin/transportation/intelligence/predictions
   /api/admin/transportation/intelligence/dispatch-learning
   /api/admin/transportation/automation/run, /dry-run, /health (writes + status)
   /api/admin/transportation/automation/digest/*          (digest engine)
   /api/admin/transportation/automation/actions/{aid}     (PATCH resolve/dismiss)
   /api/admin/transportation/automation/runs              (run history)
   /api/admin/transportation/automation/events            (dedupe ledger)
   /api/admin/transportation/intelligence/cleanup-signals/{key}/materialize-actions (POST)
   /api/admin/transportation/hr-sync, /hr-sync/report
   /api/admin/transportation/email-routes(/*)
   ALL POST/PATCH on carriers/persons/trucks/orientation modules/questions
   ALL POST/PATCH on rate schedules + carrier-document review writes

3. FRONTEND — `txHeaders()` helper added in
   `/app/frontend/src/pages/transportation/_shared.jsx`. Every
   transportation `txGet(...)` call now sends BOTH
   `X-Admin-Token` and `X-Dispatch-Token`. The `_local_dispatch_or_admin`
   gate in the backend reads either header. Existing restricted-state
   guards remain in place but now only trigger when the backend
   genuinely refuses (intelligence dashboard, automation health, etc.).

4. FRONTEND · NAV — `visibleTxOpsNavGroups()` continues to hide the
   Administration group from dispatch users. Class C deep-links still
   render `<TxOpsRestrictedData />` cleanly.

────────────────────────────────────────────────────────────────────────────
FILES TOUCHED
────────────────────────────────────────────────────────────────────────────
BACKEND
- /app/backend/routes/transportation.py
- /app/backend/routes/transportation_experience.py
- /app/backend/routes/transportation_orientation.py
- /app/backend/routes/transportation_automation.py
- /app/backend/routes/transportation_intelligence.py
- /app/backend/server.py  (wired the new dispatch deps into router registrations)

FRONTEND
- /app/frontend/src/pages/transportation/_shared.jsx (`txHeaders()`, txGet uses it)

TESTS (contract updates for the new classification)
- /app/backend/tests/test_track_18_00_phase_f_portal_aware_data_layer.py::test_25
- /app/backend/tests/test_track_18_00_phase_g_final_polish.py::test_24
- /app/backend/tests/test_track_16_06_transportation_experience_layer.py::test_6
- /app/backend/tests/test_track_16_07_transportation_workflow_activation.py::test_2
- /app/backend/tests/test_track_16_15_operational_cleanup_companion.py::test_21
- /app/backend/tests/test_track_16_15a_dashboard_cleanup_signal_mirror.py::test_11
- NEW: /app/backend/tests/test_track_18_12c_transportation_role_permissions.py

────────────────────────────────────────────────────────────────────────────
ZERO RBAC WEAKENING — ZERO NEW COLLECTIONS — ZERO ROUTE BREAKAGE
────────────────────────────────────────────────────────────────────────────
- Every endpoint that was admin-strict for SECURITY reasons (writes,
  PII, governance, deep analytics) stays admin-strict.
- The endpoints we widened were INCORRECTLY admin-strict — they are
  core operational reads dispatchers genuinely need to run trucking
  (Drivers, Carriers, Trucks, Orientation summary, Compliance summary,
  Morning Queue, Forecast, Cleanup Signals).
- No new collections, no schema drift, no route URL changes, no
  /dispatch-portal/* changes, no driver magic-link changes, no
  /admin/transportation/* breakage.

────────────────────────────────────────────────────────────────────────────
TESTS
────────────────────────────────────────────────────────────────────────────
- Track 16 + 17 + 18 family regression: **1429 PASS** / 1 skipped.
- New 18.12C lock test:
  `/app/backend/tests/test_track_18_12c_transportation_role_permissions.py`
  — 30+ assertions covering each migrated endpoint, the ops_guard
  alias contract, txHeaders frontend wiring, every Class C admin-strict
  endpoint that must NOT have been widened.
- Live browser smoke as Super Admin & Dispatch (separate sessions):
  - Super Admin /transportation-operations/carriers → 200 rows real data
  - Super Admin /transportation-operations/orientation → real dashboard
  - Dispatch    /transportation-operations/carriers → 200 rows real data
  - Dispatch    /transportation-operations/drivers  → 159 rows real data
  - Dispatch    /transportation-operations/trucks   → 6 rows real data
  - Dispatch    /transportation-operations/orientation → loading → dashboard
  - Dispatch    /transportation-operations/compliance  → real summary
  - Dispatch    /transportation-operations/audit       → TxOpsRestrictedData (correct)
  - Dispatch    Administration nav group → HIDDEN (correct)

────────────────────────────────────────────────────────────────────────────
FINAL CALL
────────────────────────────────────────────────────────────────────────────
GO.  A dispatcher can now actually USE Transportation Operations — see
Drivers, Carriers, Trucks, Orientation, Compliance, Live Operations,
Mission Control, Dispatch, Reports, Cleanup, Morning Queue, Forecast,
per-entity timeline. Administration governance (Audit Timeline,
Intelligence deep analytics, Automation Health writes, HR Sync, Email
Routes, Orientation Module CMS) remains admin-strict. Restricted
banners only fire on genuinely admin-only surfaces.
