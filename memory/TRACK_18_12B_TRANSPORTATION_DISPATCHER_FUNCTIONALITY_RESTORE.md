TRACK 18.12B · TRANSPORTATION OPERATIONS DISPATCHER FUNCTIONALITY RESTORE
=========================================================================

DATE      : 2026-02-15
STATUS    : ✅ GO (browser-verified for dispatch session via testing_agent_v3_fork)
SCOPE     : Stop unhandled 401/403 crashes inside `/transportation-operations/*` for
            non-admin dispatch users. Replace raw "Admin login required" / 401 text
            with a Transportation-branded restricted state. Preserve admin-only
            governance boundaries. No new endpoints, no new collections, no
            schema drift, no RBAC weakening.

────────────────────────────────────────────────────────────────────────────
ROOT CAUSE
────────────────────────────────────────────────────────────────────────────
Track 18.12 fixed the routing prefix so dispatch users stay inside
`/transportation-operations/*`. But the underlying data fetches in
`_orientation.jsx`, `_intelligence.jsx`, `_command_queue.jsx`,
`_lists.jsx`, and `_views.jsx` were calling `api.get(...)` (or the
single-shot `txGet` wrapper) directly against admin-strict
`/api/admin/transportation/*` endpoints. For dispatch / non-admin tokens
those endpoints return 401 with `detail = "Admin login required"`.
Loaders had three failure modes:

 1. `setErr(e.message)` → React rendered the raw `"Request failed with
    status code 401"` string inside the operational chrome.
 2. `setErr(e.response?.data?.detail)` → rendered the raw
    `"Admin login required"` string inside the operational chrome.
 3. Unhandled axios rejection → red dev-overlay runtime error.

All three are forbidden by 18.12B doctrine.

────────────────────────────────────────────────────────────────────────────
FIX SHAPE (surgical)
────────────────────────────────────────────────────────────────────────────
1. **Single 401/403 doorway** — `_shared.jsx::txGet()` already absorbed
   401/403 and resolved with a restricted-tagged payload. Strengthened
   the payload (`{ data: { restricted: true, rows: [], items: [],
   signals: [], records: [] }, status, __txRestricted: true }`) and
   set `config.skipSessionStatus = true` so the global session-status
   bus never publishes a "Session Expired" modal for this absorbed
   class of failure.

2. **Detection helper** — `isTxRestricted(r)` recognises the marker.

3. **Error-message sanitiser** — `txCatch(e)` strips forbidden tokens
   ("Admin login required" / "Request failed with status code 4xx" /
   "Forbidden" / "Unauthorized") from any escaped error message that
   reaches a `setErr(...)` callsite. Returns `null` for absorbed 401/403
   so callers can switch to the restricted state.

4. **Loader contract** — every Transportation Operations loader now:
     • awaits `txGet(...)`
     • short-circuits to `<TxOpsRestrictedData />` when `isTxRestricted(r)`
     • catches and runs raw errors through `txCatch(e)` before display
     • never renders `e.response?.data?.detail` raw
     • never renders `e.message` raw

5. **Role-aware nav** — `visibleTxOpsNavGroups()` hides the
   `administration` group from non-admin tokens. Dispatchers never see
   a Bucket-C workspace that would immediately 401.

6. **Lists/Workspaces restricted state** — `_lists.jsx` Carriers /
   Drivers / Trucks list views and each `*Workspace` detail surface
   now branch to `<TxOpsRestrictedData />` on the restricted marker
   instead of returning empty tables or unguarded `data.carrier.x`
   reads.

7. **Audit Timeline** — `AuditTimeline` in `_views.jsx` renders
   `<TxOpsRestrictedData />` on restricted state. Bucket-C, so the nav
   item itself is already hidden — this is defence in depth.

8. **Compliance / Document / Inspection / Rate centers** — same
   restricted-state guards.

────────────────────────────────────────────────────────────────────────────
FILES TOUCHED
────────────────────────────────────────────────────────────────────────────
- /app/frontend/src/pages/transportation/_shared.jsx
- /app/frontend/src/pages/transportation/_orientation.jsx
- /app/frontend/src/pages/transportation/_intelligence.jsx
- /app/frontend/src/pages/transportation/_command_queue.jsx
- /app/frontend/src/pages/transportation/_lists.jsx
- /app/frontend/src/pages/transportation/_views.jsx

Zero backend changes.

────────────────────────────────────────────────────────────────────────────
ROUTE PRESERVATION
────────────────────────────────────────────────────────────────────────────
- `/dispatch-portal/*` — UNCHANGED.
- Driver magic-link workflows — UNCHANGED.
- `/admin/transportation/*` admin oversight — UNCHANGED (admin tokens
  still see every workspace and every loader resolves with real data).
- Admin-only endpoints REMAIN admin-strict on the backend.
- No new routes added. No routes removed.

────────────────────────────────────────────────────────────────────────────
RBAC PRESERVATION
────────────────────────────────────────────────────────────────────────────
- Admin-strict endpoints stay admin-strict — frontend gracefully renders
  a restricted state for non-admin tokens instead of leaking data.
- No endpoint was relaxed.
- No portal-aware bypass was added.

────────────────────────────────────────────────────────────────────────────
TESTS
────────────────────────────────────────────────────────────────────────────
- `backend/tests/test_track_18_12b_transportation_dispatcher_functionality.py`
  — AST + static scan lock. See the test file for the 30+ assertions.
- `testing_agent_v3_fork` browser smoke documented in
  `/app/test_reports/iteration_track_18_12b_transportation_dispatcher_functionality.json`

────────────────────────────────────────────────────────────────────────────
RISKS / DEFERRALS
────────────────────────────────────────────────────────────────────────────
- Mission Control's `useTransportationReadiness()` already relies on the
  cross-portal `/api/operations/transportation/readiness` endpoint which
  accepts every portal token. No change required.
- Reports remains intentional ComingSoon (R8-compliant).
- No deferred 18.12B work.
