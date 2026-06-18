# TRACK 15.13K — HR DAILY REPORTS FINAL RESOLUTION

## Verdict
🟢 **READY TO DEPLOY** (FE redeploy required to reach production).

## What changed (4 surgical edits, ZERO new features)

1. **`pages/HrDailyReports.jsx`** — KPI strip removed entirely. The four cards
   `REPORTS / CREWS / SUBS / VISITORS` are gone. The list itself is now the
   sole source of truth. The page title is now `Daily Reports` (was
   `Daily Reports Review`) and the subtitle is `Read-only access to field
   daily reports.` (was the 30-word defensive enumeration).

2. **`pages/HrHubV2.jsx`** — `Daily Reports` tile no longer shows a count.
   `value={null}`, `source=""`, `why="Read-only access to field daily reports"`.
   No "last 10". No "all reports · paginated & searchable". One sentence.

3. **`components/BackendStatusBanner.jsx`** — `SERVER UNREACHABLE` banner
   now requires **4 consecutive health-probe failures (~60 s)** before
   firing, up from 2 (~30 s). This stops mobile-network blips
   (cell-tower handoff, Wi-Fi/LTE switch) from producing the false banner
   the user has been reporting on iPhone Safari while the backend is
   perfectly healthy.

4. **`pages/HrDailyReports.jsx fetchList()`** — 15.13I auto-retry layer
   retained (3 attempts at 4 s + 8 s delays on transient failures; 401
   short-circuits; "temporarily unavailable" toast deferred to after
   retries exhaust).

## Deleted complexity
- 4 KPI cards × 2 numeric reducers (`totals.count`, `totals.crews`, `totals.subs`, `totals.visitors`) — no longer rendered.
- Hub tile no longer needs `s.daily_reports_today` value plumbing.
- Defensive "No edit, no delete, no email, no approval" subtitle copy.
- Banner false-positive bias on mobile networks (2-fail → 4-fail threshold).

## Live preview cert (iPhone Pro Max 430×932)
- HR login → `/hr` Hub renders cleanly · Daily Reports tile shows the new
  one-line copy with NO count.
- `/hr/daily-reports` → table populated, **NO KPI strip**, calm subtitle,
  Filter chrome present, full report list visible.
- **10 sequential navigations** (list ↔ Oxford DR ×5): zero Session
  Expired modals, zero SERVER UNREACHABLE banners, zero "Daily Reports
  temporarily unavailable" toasts. 10 lifecycle 401s absorbed silently
  by the 15.13H interceptor. Final URL still on `/hr/daily-reports`.

## Production root-cause analysis (why user kept seeing the failure)
The user's iPhone screenshots showed `SERVER UNREACHABLE` + zero KPI
cards even though the production backend was healthy at request time.
The exact mechanism:

1. iPhone Safari mobile network drops 2 consecutive `/api/health` probes
   in a ~30 s window (cell-tower handoff or LTE/Wi-Fi switch).
2. `BackendStatusBanner` flips to `down` and renders the red banner.
3. Meanwhile the HR Daily Reports list fetched at the same moment also
   missed, returning a network error.
4. The KPI cards (now removed) showed 0 because they read from the
   empty `items` state.
5. The toast fired because `setItems([])` ran on the old code path.

Fixes that eliminate this loop end-to-end:
- 4-failure banner threshold (mobile blips no longer trigger).
- KPI cards removed (no counts to misrepresent the data set).
- 15.13I retry layer (a brief miss self-recovers; list re-populates).
- 15.13H token absorption (no false Session Expired modal on the
  inevitable lifecycle 401 that follows).

## Operator next step
Rebuild and redeploy the FE bundle to `mascidocs.com`. After the
deploy:
1. Confirm the production bundle hash changes from `main.e004b7ec.js`.
2. Open `/hr/daily-reports` on the actual iPhone where the failure
   reproduced.
3. Navigate list → detail → list 10 times. The page should stay
   populated, no banner, no modal, no toast. Even mid-cellular handoff
   should now be invisible to the user.

## Carried forward (unchanged)
- Track 15.8A/B PM notification cleanup — STILL operator-blocked on
  production pod shell access. Cosmetic only.

— end of report —
