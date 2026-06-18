# TRACK 15.13K-B · GAP #1 — IN-SPA FAILURE INJECTION PROOF

**Status:** 🟢 PROVEN (Gap #1 only).  
**Track overall:** OPEN — Gap #2 (real production on-device verification) still pending user action.  
**Run date:** 2026-06-18

## Test method

Real SPA workflow, real Playwright route interception:

1. Browser opens `/hr/login` on the live preview build.
2. HR Manager (`hrmanager@mascigc.com` / `CertProof2026!`) signs in via the
   actual login form (data-testid driven).
3. Lands on `/hr`.
4. `page.route("**/api/hr/daily-reports*", ...)` is installed with a
   per-call counter that fulfils the **first** request with HTTP 503
   (`{"detail":"Service Temporarily Unavailable"}`) and lets every
   subsequent call pass through to the live backend.
5. The SPA navigates internally to `/hr/daily-reports`. The
   `HrDailyReports.jsx` component mounts and fires its own `fetchList()`.
6. Browser waits 11 s — long enough for the component's 4 s auto-retry to
   trip (the retry scheduler lives in `fetchList()` lines 86–99 of
   `/app/frontend/src/pages/HrDailyReports.jsx`).
7. Live DOM is queried for the PASS criteria.

No raw JSON access. No mocked URL navigation. No app bypass. The real
SPA path under the real Cloudflare → ingress → React Router chain.

## Browser-observed results

| # | Check | Observed | Required |
|---|---|---|---|
| 1 | First `/api/hr/daily-reports` response was 503 | `first_503_returned = True`; browser console: `Failed to load resource: the server responded with a status of 503` | ✅ |
| 2 | Retry actually fires (SPA, not test) | `hr_dr_calls = 3`; third call returned 200 from the live backend | ✅ |
| 3 | Data loads after retry | `[data-testid^="hr-dr-row-"]` count = **600** rows | ✅ |
| 4 | No permanent empty state | `[data-testid="hr-dr-empty"]` count = 0 | ✅ |
| 5 | No permanent loading spinner | `.animate-spin` count inside `[data-testid="hr-dr-list"]` = 0 | ✅ |
| 6 | No "Session Expired" modal | `getByText("Session Expired")` / `"session expired"` / `"sign in again"` all = 0 | ✅ |
| 7 | No "SERVER UNREACHABLE" banner | `[data-testid="backend-status-banner"]` count = 0; `getByText("Server Unreachable")` count = 0 | ✅ |

Screenshot of the resulting Daily Reports table (fully populated, no
banner, no modal) saved at `/tmp/gap1_after_retry.png` during the run.

## Why this matters

`HrDailyReports.jsx` lines 86–99 contain a 4 s + 8 s auto-retry on any
5xx. The frontend `api.js` interceptors no longer emit
`session_expired` for portal-scoped 5xx/401-on-portal-routes
(TRACK 15.13E + 15.13H). `BackendStatusBanner` requires 4 consecutive
`/api/health` failures over ≈60 s before flipping to "down". This Gap
#1 test exercises all three guards in one shot against the real DOM.

## Gap #2 still required

This certification is explicitly **NOT** a substitute for the real
production on-device verification (Gap #2). The track remains open
until the user deploys to `mascidocs.com` and runs the navigation +
network-toggle + lock/unlock script on their physical device with
ZERO occurrences of Session Expired / Server Unreachable / Empty
list / Forced refresh / Broken navigation.
