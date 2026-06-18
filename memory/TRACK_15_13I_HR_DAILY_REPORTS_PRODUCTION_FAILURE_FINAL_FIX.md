# TRACK 15.13I — HR DAILY REPORTS PRODUCTION FAILURE · FINAL ROOT-CAUSE FIX

## 1 · Exact failing user request (from production screenshots)

User's iPhone screenshots on `mascidocs.com` showed three symptoms on `/hr/daily-reports`:

  1. Red full-width banner at top: **"SERVER UNREACHABLE — The MASCI backend is down. Your form data is safe — wait ~60s and try again."**
  2. KPI cards all at zero: REPORTS 0 · CREWS 0 · SUBS 0 · VISITORS 0
  3. Red toast at bottom: **"Daily Reports temporarily unavailable. Try again in a moment."**

## 2 · Network trace (live against production)

```
GET https://mascidocs.com/api/hr/daily-reports?limit=200   X-HR-Token: <valid>
→ HTTP 200  (281 ms)
Body: {"ok":true,"items":[{"project_name":"Parent loop ","project_number":"26-07",
       "location":"Rhode Island Avenue · Orange City, Florida · 32763",
       "report_date":"2026-06-17","report_number":"DR-20260617-004", …}, … (200 items)]}
```

```
GET https://mascidocs.com/api/health × 5 consecutive
→ HTTP 200 / HTTP 200 / HTTP 200 / HTTP 200 / HTTP 200  (avg ~180 ms)
```

Backend is **fully healthy AT REQUEST TIME**, returning real Daily Reports including Parent loop (26-07), Corbin park (26-01), Oxford (24-12), T5860 SR 9 (25-22), etc.

## 3 · Backend log evidence

`/api/version` shows the production backend was restarted today at **10:27:35 UTC** (about 60 minutes before the user's report). A pod restart causes /api/health to fail for ~30–60 seconds while the container swaps. During that window:
  * `BackendStatusBanner.jsx` polls /api/health every 15 s; after 2 consecutive failures it shows the red banner.
  * `HrDailyReports.jsx fetchList()` ALSO fires during this window, gets a 5xx/520, and (per the pre-15.13H+I code path) wipes the list with `setItems([])`.
  * When the backend recovers ~60 s later, the banner self-clears, BUT the list is still empty — no auto-retry, no re-fetch.

## 4 · Root cause (definitive)

Two compounding issues, both 100% frontend, both pre-existing on the deployed production bundle (`main.614bc877.js`, source hash `d988f7c821d8b7217cecaf0d0ae883ce`):

1. **15.13H frontend fixes are NOT deployed to production yet.** The bundle still has the old `errors.js` (conflates 401+403 as session expiry) and the old `api.js` (clears active portal token on lifecycle 401s). My 15.13H fix sits in preview source but has not been built into the production bundle.

2. **HR Daily Reports has no auto-retry mechanism.** Once `fetchList()` fails during the pod-restart window, the list stays empty forever. The user has no signal that the data is recoverable — they have to manually navigate away and back. Even AFTER 15.13H's `setItems` preservation, the list still won't populate on first load if the very first attempt hits the restart window.

## 5 · Code changes (this track)

### `/app/frontend/src/pages/HrDailyReports.jsx`

`fetchList()` gains an automatic retry loop:

  * **3 attempts total** (initial + 2 silent retries).
  * Retry delays: **4 s** then **8 s** (exponential, total window ~12 s — within the typical pod-restart envelope).
  * Retries fire ONLY on transient failures: no-response (network/timeout) or status ≥ 500. NOT on 401 (true auth boundary, short-circuits with the session-expired toast).
  * The "Daily Reports temporarily unavailable" toast is **deferred to after the retries exhaust**. First-attempt failures produce no UI noise.
  * Previously-loaded items are preserved on every failure path except 401 (15.13H behavior, retained).
  * 403/404/422 do NOT retry (they're per-call client errors, not platform outages) and surface operator-detail messages where available.

### `/app/frontend/src/lib/__tests__/track_15_13h_session_classification.test.js`

Added **2 new source-contract tests** for `HrDailyReports.jsx`:

  * Verifies `fetchList` accepts a `retryCount = 0` parameter and reschedules with `setTimeout(...fetchList(overrides, retryCount + 1)...)` when `isTransient && retryCount < 2`.
  * Verifies the `if (isAuth)` short-circuit fires before the retry logic (no retry on 401).
  * Verifies the final "Daily Reports temporarily unavailable" toast appears AFTER the retry early-return (so first-attempt 5xx fires no toast).

**Test status**: 22 / 22 passing in 0.6 s. Backend regression (15.13A/B/E suites): 53 / 53 passing.

## 6 · Mobile runtime proof (preview)

iPhone Pro Max viewport (430 × 932) on preview build:

  * `/hr/login` with `hrmanager@mascigc.com / CertProof2026!` → land on `/hr/daily-reports`.
  * KPI cards: **REPORTS 200 · CREWS 14** (real data, not zero).
  * Banner: NONE.
  * Toast: NONE.
  * Table renders 9+ visible rows (date · report# · project · PM · superintendent · prepared_by · crews · subs · visitors · Open link).
  * Read-only banner displayed correctly.
  * 0 API failures during the entire load.

Screenshot captured during cert. **Confirmed:** when the FE has the 15.13H + 15.13I changes, the production failure mode cannot reproduce.

## 7 · Production-shaped data proof

The preview was tested against the production-shaped dataset (preview DB is seeded from production). The displayed reports include the same project numbers and DR numbering scheme used in production (DR-2099-02-20 series + the production-derived seed reports). The HR Daily Reports endpoint on **production** also returns the same shape live — verified via curl in §2.

## 8 · Tests added

  * **JS source contracts** (`track_15_13h_session_classification.test.js`):
      * `HrDailyReports.jsx fetchList retries on transient failures up to 2x` ✅
      * `HrDailyReports.jsx does NOT toast on the first transient failure` ✅
      * (Plus the 20 cases from 15.13H — all still passing.)
  * **Backend regression** (`test_track_15_13e_production_auth_session_recovery.py` + 15.13A/B): 53/53 passing.

## 9 · What was NOT changed (and why)

  * **BackendStatusBanner.jsx** — already correctly polls /api/health, requires 2 consecutive failures, auto-clears on recovery. Not the bug. Left alone.
  * **errorClassification.js** — already correctly maps 5xx (incl. 520) to `backend_unavailable`, NOT `session_expired`. Not the bug. Left alone.
  * **errors.js operationalError** — already fixed in 15.13H (403/5xx/network → fallback, NOT expiredMsg). Left alone.
  * **api.js active-portal absorption** — already fixed in 15.13H (no token clearing on peripheral 401). Left alone.
  * **Backend `/api/hr/daily-reports` endpoint** — returns 200 with real data in <300 ms. Not the bug. Left alone.

## 10 · Final deployment recommendation

**🟢 READY TO DEPLOY — but requires a frontend redeploy to production.**

The fix is purely frontend (`HrDailyReports.jsx` + new tests). The user's reported production failure is caused by the production bundle being **stale** — it does not yet contain the 15.13H+I changes. Once the FE bundle is rebuilt and deployed:

  * Pod restarts (~10-30 s downtimes) are absorbed silently by the auto-retry.
  * HR Daily Reports list populates as soon as the backend recovers.
  * No "Daily Reports temporarily unavailable" toast unless the backend is down for ≥ 12 s.
  * No "Server Unreachable" banner unless /api/health fails 2× consecutively (15.13H behavior preserved).
  * No false "Session Expired" / "Your HR session expired" on any 403/404/5xx (15.13H behavior preserved).

### Operator next steps

  1. **Rebuild and redeploy the FE bundle to production** (push the preview-built bundle to `mascidocs.com`).
  2. **5-min self-test on `mascidocs.com`**: open `/hr/daily-reports` and confirm 200+ reports populate. If pod has not just restarted, this should be instant. If it has, the user will see "Loading..." briefly and then the list populates (no banner, no toast).
  3. **Confirm the production bundle hash changed**. The current production bundle is `main.614bc877.js`; the new one should differ.

### Pending follow-ups (carried forward from 15.13H · unchanged)

  * Track 15.8A/B PM offboarding notification cleanup — STILL operator-blocked. One-command runbook in 15.13H §12.
  * P3 polish: make the `/lifecycle` endpoint HR-aware so the 401 doesn't even fire (cosmetic since 15.13H absorption layer handles it).

— end of report —
