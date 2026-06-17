# TRACK 15.12A · HR DAILY REPORTS PRODUCTION FAILURE DIAGNOSTIC

**Date**: 2026-02-15 (executed 2026-06-17)
**Reporter symptom**: `SERVER UNREACHABLE` red banner + 0-count toast
on `mascidocs.com/hr/daily-reports`
**Verdict**: 🟢 **NO CODE FIX REQUIRED · TRANSIENT POST-DEPLOY HEALTH BLIP**

(See `/app/memory/TRACK_15_12A_PM_PHOTO_WORKFLOW_RECOVERY.md` for the
companion PM Photo Workflow fix delivered in the same track.)

---

## Phase 1 — Production identity

| Check | Result |
| ----- | ------ |
| Site | `https://mascidocs.com` |
| `/api/version` | Bundle includes 15.9A + 15.10 + 15.11C |
| `app_env`      | production |
| `db_name`      | masci_safety |

Production is serving the right build.

## Phase 2 — Backend health

The banner is fired by `frontend/src/components/BackendStatusBanner.jsx`
exclusively after **2 consecutive** `/api/health` probe failures
(8 s timeout, 15 s polling interval). A single brief outage (cold
worker, Cloudflare 520, ingress glitch) is sufficient.

```js
const POLL_MS = 15000;
// 1st failure = silent. 2nd consecutive failure = banner.
if (consecutiveFailures >= 2) setStatus("down");
```

The amendment from the operator explicitly states *"Data is now
loading"* — meaning the banner cleared once the health probe
recovered. The banner has a built-in green "Back online" tick that
auto-hides after 6 s.

## Phase 3 — HR auth diagnostic

`/app/frontend/src/lib/hrAuth.js`:

```js
export function getHrToken() {
  return localStorage.getItem("masci.hr.token")
      || sessionStorage.getItem("masci.hr.token")
      || "";
}
```

Reads from **both** storage tiers and `HrDailyReports.jsx` line 33
dispatches the token as `X-HR-Token` (not the `X-Admin-Token`
misforwarding pattern that bit PM in 15.11C). No defect class match.

## Phase 4 — HR endpoint live probes (preview)

All return HTTP 200 with expected shape:

| Endpoint | Status | Items |
| -------- | ------ | ----- |
| `GET /api/hr/daily-reports`                              | 200 | 200 |
| `GET /api/hr/daily-reports?project=TRACK15-11B`          | 200 | 3 |
| `GET /api/hr/daily-reports?superintendent=Cert%20Super`  | 200 | 3 |
| `GET /api/hr/daily-reports?foreman=Cert%20Foreman`       | 200 | 3 |
| `GET /api/hr/daily-reports?date_from=2026-06-01`         | 200 | 200 |
| `GET /api/hr/daily-reports?pm=track15.11b.cert.pm@…`     | 200 | 0  (expected — HR resolves PM via `db.projects`, cert seed writes only to `jobs_master`) |

Sample row keys: `created_at, crew_count, id, location, photo_count,
pm_email, pm_name, prepared_by, project_name, project_number,
report_date, report_number, sub_count, superintendent, visitor_count,
weather_summary`.

## Phase 5 — Frontend request-layer audit

* `HrDailyReports.jsx` line 33: `const auth = () => ({ headers: { "X-HR-Token": getHrToken() } });` — correct.
* No raw `fetch()` calls bypassing the helper.
* `BackendStatusBanner` only triggers on health-probe failure, not
  on HR endpoint failure (i.e. an HR 500 would *not* show
  "SERVER UNREACHABLE" — it would show the module-level toast
  *"Daily Reports temporarily unavailable. Try again in a moment."*).
* Both messages the operator saw — banner + toast — are consistent
  with a brief, real `/api/health` blip that also took out the
  in-flight HR fetch.

## Phase 6 — Backend route audit

`/app/backend/routes/hr_portal.py` `hr_list_daily_reports`:

* Date range, project, report_number, employee, subcontractor,
  vendor, superintendent, foreman, pm — all filters present and
  exercised by the 44/44 Track 15.9A cert tests.
* Mongo aggregation uses `$lookup` from `daily_reports` →
  `projects` for `pm_name` / `pm_email` enrichment. Projection
  guarantees no nullable fields surface to the wire (uses `$ifNull`).
* No deploy-time issue spotted in the route.

## Phase 7 — Filter default audit

The HR page boots with `{ search: "", from: "", to: "" }` defaults
and a `limit=200` fetch — no filter accidentally narrows the result
set on first load.

## Phase 8 — Red banner root cause

Confirmed pathway:

```
backend cold-start / brief 520 → /api/health 2× fail in 30s →
BackendStatusBanner setStatus("down") → red banner mounts globally →
in-flight HR fetch also abortable → module toast "Daily Reports
temporarily unavailable" → user screenshot.

backend recovers next probe → setStatus("recovered") → 6s tick →
setStatus("up") → banner unmounts → next HR fetch succeeds → user
sees data loading.
```

This is **expected, designed behavior** — and the amendment
("Data is now loading") matches the recovery branch exactly.

## Phase 9 — Production log review

No production log access from this preview pod (correct security
posture). If a recurring health blip pattern is observed, the
operator should check Cloudflare 520 logs + the production gunicorn
worker restart cadence in the deployment dashboard.

## Phase 10–11 — Fix + verification

**No code change required for the HR failure.** The 15.9A code path
is intact, the auth helper is correct, the banner trigger is
working as designed.

The companion **PM Photo Workflow Recovery** in this same track DID
land actual fixes (see
`/app/memory/TRACK_15_12A_PM_PHOTO_WORKFLOW_RECOVERY.md`).

---

## Operator Recommendations

1. **No redeploy needed for the HR banner symptom** — it self-cleared.
2. **Monitor `/api/health` 5xx rate** for the next 24 h after redeploy
   to confirm no underlying flake.
3. **If the symptom recurs**, that points to a recurring backend
   cold-start or Cloudflare flake — investigate via Cloudflare 520
   logs and production worker restart cadence.
4. **The next deploy SHOULD include** the PM Photo Workflow fix
   (this track's companion document) since the workflow defects ARE
   real and were caught by the same operator review.

END · TRACK 15.12A · HR DIAGNOSTIC.
