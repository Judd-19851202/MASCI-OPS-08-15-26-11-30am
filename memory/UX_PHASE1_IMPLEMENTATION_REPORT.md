# UX Phase 1 · Implementation Report

**Batch:** OMEGA · Sprint Scheduler Hardening + UX Phase 1 · Phase B
**Scope:** F-001 · F-002 · F-003 · F-004 · F-005 (five 🔴 high-friction items from `REAL_USER_DISCOVERABILITY_AUDIT.md`)
**Mode:** Preview-only implementation · production deploy pending operator authorization
**Date:** 2026-06-01

---

## 1 · Headline

🟢 **5 of 5 high-friction items closed in preview.** All changes are surgical, additive, and route-safe. Total LOC delta: 307 (frontend only — no backend changes for Phase B).

| ID | Friction | Persona | Change | Status |
|---|---|---|---|---|
| **F-001** | Sandy / Per-Day Detail — variance grid does not deep-link to per-day timecard | HR / Payroll | Added `→ Per-Day Detail` link on every variance row + query-string acceptance on Time Verification | 🟢 |
| **F-002** | Time Verification vs. Payroll Variance confusing copy | HR / Payroll | Rewrote both HR Hub tile descriptions to clarify *who* uses which surface and *what* it does | 🟢 |
| **F-003** | No in-app digest replay — Mondays were email-only | PM / HR / Executive / Dispatcher | New `/admin/scheduler-runs` page reads from the new `scheduler_runs` collection · admin tile in AdminHub | 🟢 |
| **F-004** | Superintendents can't find JHA from Field Leadership Hub | Field Leadership | Added "Job Hazard Plans (JHA)" tile under new "On-Site Reference" group | 🟢 |
| **F-005** | Superintendents can't see Asset Transfers from FL Hub | Field Leadership | Added "Asset Transfers" tile in the same "On-Site Reference" group | 🟢 |

---

## 2 · Per-friction implementation detail

### 2.1 · F-001 · Sandy / Per-Day Detail drill-through

**Before:** A variance row in `HrPayrollVariance.jsx` showed the employee name and CSV-vs-MASCI hour deltas. To investigate, Sandy had to open a new tab, navigate to `/hr/time-verification`, re-enter the week-ending, re-type the employee name, and switch the view to "daily".

**After:**

* `HrPayrollVariance.jsx:336-349` — each row's employee cell now renders an additional `→ Per-Day Detail` link below the name. The link target is `/hr/time-verification?employee=<encoded>&week_ending=<batch.week_ending>&open_detail=daily` and opens in a new tab (`target="_blank"`).
* `HrTimeVerification.jsx:45-65` — page now reads `employee`, `week_ending`, and `open_detail=daily` from the query string on mount. Pre-populates the employee filter and switches the view to "daily" immediately.
* `data-testid="hr-pv-perday-link-{row_index}"` per OMEGA testid contract.

**LOC delta:** +14 (`HrPayrollVariance.jsx`) +14/-2 (`HrTimeVerification.jsx`).

### 2.2 · F-002 · HR Hub tile copy clarification

**Before:**
```
Time Verification     — "Daily report labor and payroll cross-check."
Payroll Variance      — "Reconcile Exact CSV against MASCI hours."
```

Sandy reportedly did not know which tile to use first when investigating a payroll mismatch.

**After:**
```
Time Verification     — "Spot-check one employee's day-by-day timecard for any week."
Payroll Variance (CSV) — "Upload a payroll CSV → flag mismatches against tracked hours."
```

The new copy makes the **input** explicit (employee on the left tile, CSV on the right tile) and the **action** explicit (spot-check vs. upload-and-flag). The "(CSV)" suffix in the Payroll Variance label completes the disambiguation at a glance.

**LOC delta:** +2/-2 (`HrHub.jsx`).

### 2.3 · F-003 · In-app digest replay (Scheduler Runs page)

**Before:** Operators received Monday PO/safety/operator digests via Resend. To answer "did Monday's digest go out · to whom · was it duplicated", they had to grep stdout logs. The platform held no DB row about the fire.

**After:**

* New `lib/scheduler_runs.py` writes one row per scheduler fire to `scheduler_runs` with `started_at`, `finished_at`, `host`, `pid`, `recipients`, `duration_s`, `status`, `dedup_attempts`, `dedup_attempt_log`.
* New `routes/scheduler_runs_admin.py` exposes `GET /api/admin/scheduler-runs` and `GET /api/admin/scheduler-runs/{scheduler}/{slot_key}`.
* New `frontend/src/pages/AdminSchedulerRuns.jsx` (~213 LOC) renders a paginated history table:
  * Filters: scheduler (po / safety / operator / all), status (done / failed / in_progress), date range.
  * Each row shows scheduler · slot_key · started_at · duration · recipients · status · dedup_attempts.
  * Drill into a row → expanded view shows full `dedup_attempt_log` and `meta`.
* `AdminHub.jsx:84-103` adds a single Link tile labelled "Scheduler Runs · Digest History" with `data-testid="admin-tile-scheduler-runs"` and an amber-bordered card.
* `App.js:413` registers the route `/admin/scheduler-runs` behind the `A()` admin guard.

**LOC delta:** +213 (new page) +19 (AdminHub tile) +3 (App.js routing).

### 2.4 · F-004 · JHA in Field Leadership Hub

**Before:** `/jha` was linked from the root `Hub.jsx` only. A superintendent landing on `/leadership` could not see it. Result: phone calls to the office for "what's the JHA for trenching today".

**After:**

* `FieldLeadershipHub.jsx:113-128` adds a `jha_plans` entry to `FL_EXTERNAL_TILES` with bilingual title/description (orange accent, `Shield` icon, links to `/jha`).
* `FieldLeadershipHub.jsx:192-201` adds a new "06 · On-Site Reference" group that contains JHA + Asset Transfers (see §2.5).
* Copy: *"Open today's JHA before high-risk work (trenching ≥ 5', confined space, hot work). Acknowledge with crew. View the full library by task type."*

**LOC delta:** +33 (`FieldLeadershipHub.jsx`).

### 2.5 · F-005 · Asset Transfers in Field Leadership Hub

**Before:** `/asset-transfers` was a PM-portal tile only. Superintendents had no way to confirm yard-to-job equipment moves from their own hub.

**After:**

* `FieldLeadershipHub.jsx:128-143` adds an `asset_transfers` entry to `FL_EXTERNAL_TILES` (blue accent, `Truck` icon, links to `/asset-transfers`).
* Surfaces in the same "06 · On-Site Reference" group introduced for F-004.
* Copy: *"See incoming and outgoing equipment for your jobs. Track in-transit deliveries from the yard, returns to storage, and inter-job moves."*

**LOC delta:** +17 (within the same `FieldLeadershipHub.jsx` block).

---

## 3 · File-by-file summary

| File | Type | LOC delta | Friction closed |
|---|---|---|---|
| `frontend/src/pages/HrPayrollVariance.jsx` | edit | +14 | F-001 |
| `frontend/src/pages/HrTimeVerification.jsx` | edit | +14/-2 | F-001 |
| `frontend/src/pages/HrHub.jsx` | edit | +2/-2 | F-002 |
| `frontend/src/pages/FieldLeadershipHub.jsx` | edit | +50 | F-004 · F-005 |
| `frontend/src/pages/AdminSchedulerRuns.jsx` | new | +213 | F-003 |
| `frontend/src/pages/AdminHub.jsx` | edit | +19 | F-003 |
| `frontend/src/App.js` | edit | +3 | F-003 |
| **Total · frontend** | | **+315/-4** | **5 of 5** |

Backend changes for F-003 (the `scheduler_runs` collection + admin route) are documented in `SCHEDULER_HARDENING_REPORT.md` §2 and shipped as part of Phase A.

---

## 4 · Bilingual coverage

| Locale | F-001 | F-002 | F-003 | F-004 | F-005 |
|---|---|---|---|---|---|
| `en` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `es` | n/a (UI controls inherit) | n/a (HR Hub copy is `en` only on this surface) | n/a (admin-only) | ✅ | ✅ |

Field Leadership Hub is the only surface that meaningfully cuts across crew members who prefer Spanish — both new tiles ship with `es` strings.

---

## 5 · Test IDs

| Element | testid |
|---|---|
| Per-Day Detail link (F-001) | `hr-pv-perday-link-{row_index}` |
| Scheduler Runs tile (F-003) | `admin-tile-scheduler-runs` |
| Scheduler Runs page root | inherited from `AdminSchedulerRuns.jsx` (`admin-scheduler-runs-page`) |
| JHA tile (F-004) | inherited from `FieldLeadershipHub` tile builder |
| Asset Transfers tile (F-005) | inherited from `FieldLeadershipHub` tile builder |

---

## 6 · OMEGA discipline

| Rule | Observed |
|---|---|
| Only listed frictions touched | ✅ F-001 · F-002 · F-003 · F-004 · F-005 |
| No drift into F-006+ (medium/low friction) | ✅ — log entries deferred to future batch |
| No new pillars · no white-label · no ForgedOps | ✅ |
| Additive only (no removed surfaces, no removed routes) | ✅ |
| Backward compatible (links open in new tab; old paths still work) | ✅ |
| Production untouched | ✅ — preview only |

🛑 Implementation complete. Continue to `UX_PHASE1_CERTIFICATION_REPORT.md`.
