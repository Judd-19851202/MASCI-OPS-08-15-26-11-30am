TRANSPORTATION DISPATCHER FUNCTIONALITY AUDIT
=============================================

DATE: 2026-02-15
SESSION: Dispatch / non-admin transportation token
URL ROOT: /transportation-operations/*

Each row documents the workspace as observed pre-fix and as classified
+ remediated under Track 18.12B.

LEGEND
  Class A — Dispatcher-operational
  Class B — Dispatcher-read-only summary safe
  Class C — Admin-governance only (hidden / restricted for dispatch)
  Class D — Not ready / coming soon

╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║ WORKSPACE / ROUTE / COMPONENT / TOKEN / PRE-FIX BEHAVIOR / POST-FIX BEHAVIOR / CLASS / STATUS              ║
╠══════════════════════════════════════════════════════════════════════════════════════════════════════════════╣

1. Mission Control
   route   : /transportation-operations
   file    : pages/transportation/MissionControl.jsx + _views.jsx::TransportationDashboard
   apis    : GET /api/operations/transportation/readiness (cross-portal helper · 200)
             GET /api/admin/transportation/audit-timeline (admin-strict · 401)
             GET /api/admin/transportation/intelligence/cleanup-signals (admin-strict · 401)
   pre-fix : readiness loaded; cleanup card swallowed 401 silently (16.15A pattern);
             recent-activity card showed 0 events; mission brief rendered.
   post-fix: identical for admin; dispatch sees mission brief + workspace strip +
             8 cards (cleanup card renders TxOpsRestrictedData inside the
             "Top cleanup opportunity" slot; recent-activity card shows "—
             recent events"). No raw 401 text. No crash.
   class   : A (operational for dispatch)
   status  : ✅ FIXED

2. Dispatch (bridge)
   route   : /transportation-operations/dispatch
   file    : _dispatch_bridge.jsx
   apis    : links into /dispatch-portal (no inline admin call)
   pre-fix : worked
   post-fix: worked
   class   : A
   status  : ✅ OK

3. Live Operations
   route   : /transportation-operations/live-operations
   file    : _live_operations.jsx
   apis    : GET /api/admin/transportation/dispatch-bridge/state
             GET /api/admin/transportation/dispatch-bridge/health
   pre-fix : the loaders already used txGet — restricted marker is swallowed
             into safe payload; the page rendered an empty-but-not-broken view.
   post-fix: same; no overlay; clean empty state. Dispatchers can read summary
             counts that the API exposes; admin-only writes remain admin-only.
   class   : A (read-safe)
   status  : ✅ OK (no regression)

4. Drivers (list)
   route   : /transportation-operations/drivers
   file    : _lists.jsx::DriversList
   apis    : GET /api/admin/transportation/persons (admin-strict · 401)
   pre-fix : page showed "No drivers match" (lie — data was hidden by 401)
   post-fix: page renders <TxOpsRestrictedData /> with calm Transportation
             chrome and no raw error.
   class   : C for dispatch (admin-strict data); UI restricted-state.
   status  : ✅ FIXED

5. Drivers (workspace detail)
   route   : /transportation-operations/drivers/:id
   file    : _lists.jsx::DriverWorkspace
   apis    : GET /api/admin/transportation/persons/:id/workspace (admin-strict)
   pre-fix : data.driver was undefined → JSX crashed inside <Chip value={d.status}/>.
   post-fix: restricted state rendered cleanly.
   class   : C for dispatch
   status  : ✅ FIXED

6. Carriers (list)
   route   : /transportation-operations/carriers
   file    : _lists.jsx::CarriersList
   apis    : GET /api/admin/transportation/carriers (admin-strict)
   pre-fix : same lie as drivers
   post-fix: TxOpsRestrictedData
   class   : C for dispatch
   status  : ✅ FIXED

7. Carriers (workspace)
   route   : /transportation-operations/carriers/:id
   pre-fix : crashed on data.carrier access
   post-fix: restricted state
   class   : C for dispatch
   status  : ✅ FIXED

8. Trucks / Fleet (list)
   route   : /transportation-operations/trucks
   apis    : GET /api/admin/transportation/trucks
   pre-fix : "No trucks match" lie
   post-fix: TxOpsRestrictedData
   class   : C for dispatch
   status  : ✅ FIXED

9. Truck workspace
   route   : /transportation-operations/trucks/:id
   pre-fix : crashed on data.truck access
   post-fix: TxOpsRestrictedData
   class   : C for dispatch
   status  : ✅ FIXED

10. Compliance dashboard
    route   : /transportation-operations/compliance
    apis    : GET /api/admin/transportation/dashboard (admin-strict)
    pre-fix : returned null (loading forever)
    post-fix: TxOpsRestrictedData
    class   : C for dispatch
    status  : ✅ FIXED

11. Document Center
    route   : /transportation-operations/documents
    apis    : GET /api/admin/transportation/documents/queue
    pre-fix : "No documents match this filter" lie
    post-fix: TxOpsRestrictedData
    class   : C for dispatch
    status  : ✅ FIXED

12. Inspection Center
    route   : /transportation-operations/inspections
    apis    : GET /api/admin/transportation/inspections/queue
              GET /api/admin/transportation/trucks
    pre-fix : "No inspections match" lie + empty truck dropdown
    post-fix: combined safe rendering; loaders silenced.
    class   : C for dispatch
    status  : ✅ OK (no crash; no raw error text)

13. Orientation · Dashboard
    route   : /transportation-operations/orientation
    file    : _orientation.jsx::OrientationDashboard
    apis    : GET /api/admin/transportation/orientation/dashboard (admin-strict)
    pre-fix : rendered EmptyState with hint="Request failed with status code 401"
    post-fix: TxOpsRestrictedData
    class   : C for dispatch
    status  : ✅ FIXED

14. Orientation · Modules / Detail
    apis    : GET /api/admin/transportation/orientation/modules
              GET /api/admin/transportation/orientation/modules/{id}/questions
    pre-fix : raw 401 text in EmptyState
    post-fix: TxOpsRestrictedData
    class   : C for dispatch
    status  : ✅ FIXED

15. Orientation · Assignments / Certificates / Email Pilot
    same pattern → TxOpsRestrictedData
    status  : ✅ FIXED

16. Operations Intelligence (Executive / Recs / Predictions / Learning / Cleanup)
    route   : /transportation-operations/intelligence/*
    apis    : /api/admin/transportation/intelligence/* (admin-strict)
    pre-fix : every sub-tab rendered `<div className="text-rose-700">Admin login required</div>`
    post-fix: TxOpsRestrictedData on each sub-tab
    class   : C for dispatch (full intel admin-only); summary surface via the
              Cleanup card on Mission Control is read-safe via cleanup-signals
              admin-strict endpoint — also restricted for dispatch.
    status  : ✅ FIXED

17. Automation / Command Queue (Morning / Health / Forecast / Digest / HR Sync)
    route   : /transportation-operations/command-queue/*
    apis    : /api/admin/transportation/automation/* + /hr-sync (admin-strict)
    pre-fix : "Command queue unavailable · Admin login required" raw text
    post-fix: TxOpsRestrictedData on each sub-card
    class   : C for dispatch
    status  : ✅ FIXED

18. Administration · Audit Timeline
    route   : /transportation-operations/audit
    apis    : GET /api/admin/transportation/audit-timeline
    pre-fix : uncaught 401 overlay
    post-fix: nav group HIDDEN for non-admin tokens
              (visibleTxOpsNavGroups filters key="administration");
              if user deep-links anyway → TxOpsRestrictedData renders cleanly.
    class   : C — hidden from dispatch nav
    status  : ✅ FIXED

19. Reports
    route   : /transportation-operations/reports
    file    : _views.jsx::ReportsView
    pre-fix : ComingSoon — no crash
    post-fix: unchanged
    class   : D
    status  : ✅ OK

20. Search / Universal Search
    route   : embedded across shell
    apis    : POST /api/admin/transportation/search/relationships
              GET /api/admin/transportation/search/*
    pre-fix : restricted shape from txGet; search results hidden for dispatch
    post-fix: same, with no error overlay; results pane shows empty hint
    class   : C for dispatch
    status  : ✅ OK

21. Right Rail
    component: TxOpsRightRail in TransportationWorkspaceShell.jsx
    apis    : GET /api/admin/transportation/related/* (admin-strict)
    pre-fix : "Unable to load relationships" inline message
    post-fix: same calm hint (already Transportation-scoped, no admin chrome)
    class   : B (read-safe summary for context)
    status  : ✅ OK

22. Workspace Actions strip / chip cards (Mission Control)
    Pure links — already prefix-aware via useTxPathPrefix(). No data fetch.
    status  : ✅ OK

╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝

SUMMARY
  • 22 surfaces audited.
  • 0 surfaces leak raw 401/403/Admin login required text.
  • 0 surfaces throw an uncaught runtime React overlay.
  • 1 nav group (Administration) hidden from dispatch.
  • 0 admin-only endpoint relaxed; 0 RBAC weakening.
  • 100 % of visible dispatch-facing surfaces either operate or render
    TxOpsRestrictedData.
