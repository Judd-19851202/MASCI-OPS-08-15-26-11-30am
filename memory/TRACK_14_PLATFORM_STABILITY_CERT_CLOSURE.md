# TRACK 14.0-SAFETY-INCIDENT-AUTH-LIFECYCLE + AMENDMENT A · CLOSURE LEDGER

**Date**: 2026-02-15
**Status**: ✅ COMPLETE · PROVEN · VERIFIED · DEPLOY-READY
**Five-Pillar Score**: 5/5 (Powerful · Simple · Beautiful · Trusted · Proven)

---

## 1. Track Status

CLOSED. All P0 user-reported instability symptoms are eliminated:

* ❌ False "Session Expired" modal over valid Safety incident detail content
* ❌ False "Connection Problem" modals during normal use
* ❌ Safety user redirected to /safety-portal/login after viewing detail
* ❌ Health Board showing services as TRANSIENT after single transient blip
* ❌ Background widget failures triggering platform-wide modals

All replaced with quiet, namespace-scoped, role-correct behavior.

---

## 2. Root Cause

**Single architectural defect** — the global axios response interceptor in
`/app/frontend/src/lib/api.js` published every 401 / no-response error to
the `sessionStatusBus`, which raised a blocking platform-wide modal
regardless of whether:

1. The 401 came from a non-active portal (e.g. Safety user's accidental
   `/api/admin/*` background call).
2. The failed request was an *expected probe* (e.g. UndoLastTransitionButton's
   GET `/workflows/{id}/last-transition`, which 401's by design for
   non-admin viewers so the affordance hides itself).
3. The request was a cancelled / aborted in-flight call from a component
   unmount (`errorClassification.js` had `|| true` coercing every
   no-response error into NETWORK_UNREACHABLE).
4. The system health probe was just having a single transient blip
   (badge required only 2 consecutive failures before flipping to DOWN).

Combined effect: any single background hiccup → platform-wide "Session
Expired" or "Connection Problem" modal over still-valid content.

---

## 3. Surgical Fix (Six Surfaces)

### 3.1 `/app/frontend/src/lib/api.js`

Namespace-aware + helper-aware 401 absorption. A 401 on:

* `/api/admin/*`, `/api/shop/*`, `/api/hr/*`, `/api/pm/*`, `/api/safety/*`,
  `/api/dispatch/*`, `/api/dev/*`, `/api/leadership/*`, `/api/safety-forms/*`,
  `/field-leadership/portal*` — clears matching token only, NO global modal.
* `/api/workflows/*`, `/api/notifications/*`, `/api/operations/*`,
  `/api/operations-center` (cross-portal helpers) — silent absorption,
  NO token wipe, NO global modal.

Only "true session-loss" 401s (non-namespaced) still publish the overlay.

`skipSessionStatus: true` honored everywhere; allows individual callers
to opt out.

### 3.2 `/app/frontend/src/lib/errorClassification.js`

* Removed `|| true` that coerced every no-response into NETWORK_UNREACHABLE.
* Cancelled requests (`ERR_CANCELED`, `CanceledError`, `AbortError`) →
  `kind: null` (no overlay).
* Truly unknown failures → `kind: null` (per-call only).
* Only explicit timeout/network signals raise the global "Connection
  Problem" modal.

### 3.3 `/app/frontend/src/components/SystemHealthBadge.jsx`

* Every ping now uses `skipSessionStatus: true` (probe-of-probes can't
  poison the same overlay it's reporting on).
* `FAIL_STREAK_THRESHOLD = 3` (was 2). Single transient blip no longer
  paints any service red.
* 401/403 on probe treated as auth-gated (level=ok, msg=`{status} · auth`)
  rather than outage. A PM viewing /admin sees clean ALL OK, not a
  false alarm.

### 3.4 `/app/frontend/src/components/UndoLastTransitionButton.jsx`

* GET `/workflows/{wf}/{id}/last-transition` now uses `skipSessionStatus: true`.
* POST `/workflows/{wf}/{id}/undo-last-transition` now uses
  `skipSessionStatus: true` (defensive belt-and-braces).
* Belt-and-braces alongside the api.js silent-list.

### 3.5 `/app/frontend/src/components/IncidentLifecyclePanel.jsx`, `ExpirationsSummary.jsx`, `AdminUnifiedDirectoryPanel.jsx`

* All background widget reads now pass `skipSessionStatus: true`. A
  failed lifecycle / expirations / directory fetch shows its own inline
  error state, never the global overlay.

### 3.6 `/app/frontend/src/pages/ViewIncident.jsx`

* `BackLink` testId switches to `safety-nav-back` when pathname starts
  with `/safety-portal`, so Playwright role-matrix tests can address
  the Safety back affordance distinctly from the admin one.

---

## 4. Role Matrix Findings (Backend lifecycle role gate)

| Role               | GET /lifecycle | POST /transition | UI gating              |
|--------------------|----------------|------------------|------------------------|
| Super Admin        | 200            | 200              | All buttons visible    |
| Safety Manager     | 200            | 200              | Investigate + Close    |
| Safety Officer     | 200            | 200              | Investigate + Close    |
| Safety Coordinator | 200            | 200              | Investigate + Close    |
| PM                 | 200            | 403              | Read-only buttons      |
| HR/Shop/Dispatch   | 401/403        | 401/403          | Hidden                 |
| Foreman/FL         | 403            | 403              | Hidden                 |

Backend test coverage: `/app/backend/tests/test_iter451_incident_lifecycle.py`
(pre-existing, unchanged — still passes).

---

## 5. Stability Soak Result

Frontend playwright agent (iteration_505) ran the full 7-flow regression:

| Flow                                       | Result |
|--------------------------------------------|--------|
| STABILITY-1 · Super Admin 60s idle         | ✅ PASS |
| STABILITY-2 · Safety-only token detail     | ✅ PASS (P0 FIXED) |
| STABILITY-3 · Manual publish + dismiss     | ✅ PASS |
| STABILITY-4 · Background-401 isolation     | ✅ PASS |
| LIFECYCLE-1 · Admin lifecycle panel        | ✅ PASS |
| CROSS-PORTAL workflows 401 absorption      | ✅ PASS |
| Notifications helper 401 (raw fetch noted) | ✅ PASS |

7/7 frontend acceptance flows PASS. Backend pytest 22/22 PASS in
iteration_504. Track14 regression suite 5/5 PASS.

---

## 6. Regression Lock

New file: `/app/backend/tests/test_track14_platform_stability_regression.py`

Pins the backend contract the frontend silent-list depends on:

* `/api/health` is public 200
* `/api/workflows/*` returns 401/403/404 (not 5xx) without auth
* `/api/notifications` returns 401/403/404 (not 5xx) without auth
* `/api/operations/expirations/summary` returns 401/403/404 (not 5xx)
* `/api/incidents/<bogus>` returns 401/404 (not 5xx)

If any of these starts returning 5xx, the frontend would classify as
BACKEND_UNAVAILABLE and the global overlay would regress. The test
suite catches that contract drift.

---

## 7. Production Redeploy Impact

* No backend changes. Redeploy of frontend assets only.
* No schema changes.
* No environment-variable changes.
* No removed routes or removed components.
* Behaviour change is strictly *less* overlay, *more* localized error
  handling. No new failure modes introduced.

---

## 8. Remaining Risks (acceptable / out of scope)

* Raw `fetch()` callers (e.g. notification bell internals,
  operationsCenterApi.js) bypass the axios interceptor entirely. They
  already use their own try/catch + local toast pattern, so they do
  not contribute to the false-modal problem. Documented; no further
  action required.
* The legacy "global overlay" architecture is preserved (decision: less
  surgical scope, lower risk). A future iteration may invert to an
  allow-list of paths that ARE allowed to publish session_expired
  (e.g. `/api/auth/me`, `/api/auth/refresh`) for additional safety.

---

## 9. Five-Pillar Scorecard

* **POWERFUL** — Safety roles can open, investigate, and close
  incidents end-to-end. Super Admin inherits cleanly. Backend role
  gate proven.
* **SIMPLE** — One axios interceptor change, one classification fix,
  one badge threshold bump. No new abstractions, no new dependencies.
* **BEAUTIFUL** — No more random "Session Expired" or "Connection
  Problem" modals over valid content. Health badge stays calm and
  honest.
* **TRUSTED** — Permissions are role-correct on backend; frontend
  doesn't lie about session state.
* **PROVEN** — 7-flow runtime certification via testing agent
  (iteration_505). 5-test backend regression lock. 22/22 backend
  pytest in iteration_504.

---

## 10. GO / NO-GO

**RECOMMENDATION: GO** for production redeploy.

— main agent · 2026-02-15
