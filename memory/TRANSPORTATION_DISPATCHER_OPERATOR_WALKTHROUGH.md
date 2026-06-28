TRANSPORTATION DISPATCHER OPERATOR WALKTHROUGH
==============================================

DATE   : 2026-02-15
USER   : Dispatch / non-admin transportation user
LOGIN  : `dispatch@mascigc.com` / `DispatchTest2026!`  (per
         /app/memory/test_credentials.md)
TOKEN  : X-Dispatch-Token (per-user bcrypt HMAC)
ENTRY  : Multi-login or `/dispatch-portal/login`, then navigate to
         `/transportation-operations`.

For each step the walkthrough asserts:
  • URL stays inside `/transportation-operations/*` (no admin bounce)
  • No red runtime overlay
  • No raw "Request failed with status code 401"
  • No raw "Admin login required" / "Forbidden" / "Unauthorized" text
  • Page either presents role-safe content OR a Transportation-branded
    restricted state

╔═════════════════════════════════════════════════════════════════════════════╗
║ Step │ Path                                              │ Expected outcome    ║
╠═════════════════════════════════════════════════════════════════════════════╣

 1. Open `/transportation-operations`
    EXPECT
      • Mission Brief renders ("Transportation Operations is healthy …" or
        equivalent).
      • Workspace Actions strip renders all 8 chips.
      • 8 Mission Control cards render with numeric KPIs (or "—").
      • "Top cleanup opportunity" slot below renders
        `data-testid="tx-dashboard-top-cleanup-error"` (TxOpsRestrictedData)
        because cleanup-signals is admin-strict — calm, Transportation-branded.
      • Recent activity card shows "— recent events".
      • Administration group is NOT in the sub-nav (filtered by
        `visibleTxOpsNavGroups`).

 2. Click "Dispatch" in the Workspace strip → /transportation-operations/dispatch
    EXPECT
      • DispatchBridgeWorkspace renders (linkout chrome only).
      • No errors.

 3. Click "Drivers" → /transportation-operations/drivers
    EXPECT
      • `<TxOpsRestrictedData data-testid="tx-drivers-list-restricted" />`
      • PageHeader still reads "Drivers".
      • Refresh button still visible but clicking it does not bring back
        any error overlay (silent re-fetch into restricted state).

 4. Click "Carriers" → /transportation-operations/carriers
    EXPECT
      • `<TxOpsRestrictedData data-testid="tx-carriers-list-restricted" />`

 5. Click "Fleet" (alias to trucks) → /transportation-operations/trucks
    EXPECT
      • `<TxOpsRestrictedData data-testid="tx-trucks-list-restricted" />`

 6. Click "Compliance" → /transportation-operations/compliance
    EXPECT
      • `<TxOpsRestrictedData data-testid="tx-compliance-restricted" />`

 7. Click "Orientation" → /transportation-operations/orientation
    EXPECT
      • Dashboard tab renders
        `<TxOpsRestrictedData data-testid="tx-orient-dashboard-restricted" />`.
      • Click Modules / Assignments / Certificates / Email Pilot —
        each renders its own restricted state. No raw 401 / Admin
        login text.

 8. Click "Live Operations" → /transportation-operations/live-operations
    EXPECT
      • Live Operations workspace renders (uses cross-portal-safe
        summary). No overlay.

 9. Click "Intelligence" → /transportation-operations/intelligence
    EXPECT
      • Executive sub-tab renders `tx-intel-exec-restricted`.
      • Recommendations sub-tab → `tx-intel-recs-restricted`.
      • Predictions → `tx-intel-pred-restricted`.
      • Learning Loop → `tx-intel-learning-restricted`.
      • Cleanup Companion → `tx-intel-cleanup-restricted`.

10. Click "Automation" / Command Queue
     /transportation-operations/command-queue
    EXPECT
      • Morning Queue renders `tx-cq-restricted`.
      • Automation Health renders `tx-cq-health-restricted` +
        `tx-cq-hr-sync-restricted` + `tx-cq-digest-restricted`.
      • Forecast renders `tx-cq-forecast-restricted`.

11. Click "Cleanup" → /transportation-operations/intelligence/cleanup
    EXPECT
      • `tx-intel-cleanup-restricted` (same as step 9 — same surface).

12. Click "Reports" → /transportation-operations/reports
    EXPECT
      • ComingSoon card — `reports-coming-soon` testid. No crash.

13. Look for "Administration" group in the sub-nav
    EXPECT
      • Group is HIDDEN. Deep-linking to
        `/transportation-operations/audit` still works but renders
        `tx-audit-restricted` (TxOpsRestrictedData).

14. Use Search rail (top of every page) — `txops-search-rail`
    EXPECT
      • Typing in the input runs admin-strict suggest endpoint that
        returns empty results for non-admin. No raw 401 text. No
        runtime overlay.

15. Right rail (xl screens)
    EXPECT
      • Sections show "Unable to load relationships" calm hint when
        an entity is selected; no admin-chrome bleed.

16. Refresh any "Refresh" button (Drivers / Carriers / Trucks / etc.)
    EXPECT
      • Restricted state re-renders cleanly. No overlay.

ADMIN SESSION SANITY (regression)
───────────────────────────────────
A. Login as admin via `/admin/login` (jaymn.judd@mascigc.com / Maddix123!)
   then visit /admin/transportation — every workspace loads real data
   exactly as before.

B. Cross-portal regression — admin's `/transportation-operations`
   doorway also loads real data (admin token satisfies admin-strict
   endpoints).

C. Confirm:
    • Audit Timeline visible for admin via nav group "Administration".
    • Cleanup Companion shows real signals.
    • Intelligence shows real metrics.
    • Orientation shows real dashboard.
    • Command Queue shows real automation health.

RESULT
──────
Every step PASSES. No runtime overlay. No raw 401 / "Admin login
required" / Forbidden / Unauthorized text anywhere under
`/transportation-operations/*`. Dispatchers can operate Mission
Control, Dispatch, Live Operations, and see clean
Transportation-branded restricted states everywhere governance is
admin-only. Admin oversight is untouched.
