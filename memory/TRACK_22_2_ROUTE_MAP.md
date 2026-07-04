# TRACK 22.2 · Route Map (canonical)

**Date:** 2026-02-04
**Source:** `frontend/src/App.js` · lines 483–1276 (`<Routes>` block)
**Machine-extracted by:** `memory/track_22_2/extract_app_js_inventory.py`
**Total routes:** 385 · Unique paths: 385 · Duplicate paths: 0

Full per-route detail (path · guard · target · load) lives in the machine-readable JSON at:
- `/app/memory/track_22_2/APP_JS_INVENTORY.json` (field: `routes[]`)

## Route-group buckets (52 total)

Grouped by URL top-segment. This is the recommended file-split for `frontend/src/app/feature-routes/*.jsx`.

| Group | Routes | Guard mix | Suggested file |
|---|---:|---|---|
| admin | 99 | A=63 · AP=25 · PUBLIC=8 · APS=3 | `feature-routes/admin.jsx` |
| safety | 55 | SF=33 · PUBLIC=22 | `feature-routes/safety.jsx` |
| pm | 44 | P=22 · AP=20 · PUBLIC=2 | `feature-routes/pm.jsx` |
| hr | 31 | H=28 · PUBLIC=3 | `feature-routes/hr.jsx` |
| shop | 26 | S=24 · PUBLIC=2 | `feature-routes/shop.jsx` |
| dispatch (dispatch-portal) | 14 | DP=10 · PUBLIC=4 | `feature-routes/dispatch.jsx` |
| field-leadership | 13 | PUBLIC=9 · FL=4 | `feature-routes/field-leadership.jsx` |
| trench-safety (public) | 7 | PUBLIC=7 | `feature-routes/trench-safety.jsx` |
| incidents | 6 | PUBLIC=6 | `feature-routes/incidents.jsx` |
| fleet | 6 | PUBLIC=5 · S=1 | `feature-routes/fleet.jsx` |
| odr | 5 | PUBLIC=5 | `feature-routes/odr.jsx` |
| _internal dev | 5 | D=5 | `feature-routes/dev.jsx` |
| qaqc | 4 | PUBLIC=4 | `feature-routes/qaqc.jsx` |
| meetings | 4 | PUBLIC=4 | `feature-routes/meetings.jsx` |
| daily | 4 | PUBLIC=4 | `feature-routes/daily.jsx` |
| training | 4 | PUBLIC=4 | `feature-routes/training.jsx` |
| operations | 4 | PUBLIC=4 | `feature-routes/operations.jsx` |
| constraints | 3 | PUBLIC=3 | `feature-routes/constraints.jsx` |
| jha | 3 | PUBLIC=3 | `feature-routes/jha.jsx` |
| equipment | 3 | PUBLIC=3 | `feature-routes/equipment.jsx` |
| guidance | 3 | PUBLIC=3 | `feature-routes/guidance.jsx` |
| public/hub | 2 | PUBLIC=2 | `feature-routes/public.jsx` |
| field | 2 | PUBLIC=2 | `feature-routes/field.jsx` |
| transportation-public | 2 | PUBLIC=2 | `feature-routes/transportation.jsx` |
| driver | 2 | PUBLIC=2 | `feature-routes/driver.jsx` |
| ops-training | 2 | PUBLIC=2 | `feature-routes/ops-training.jsx` |
| legal | 2 | PUBLIC=2 | `feature-routes/legal.jsx` |
| dev misc | 2 | PUBLIC=1 · D=1 | *(fold into dev.jsx)* |
| **remaining 24 buckets** | 1 each | mostly PUBLIC | `feature-routes/misc.jsx` |

The 24 "1-route" buckets (`/notifications`, `/access-denied`, `/tasks`, `/sign-in`, `/change-password`, `/time-off`, `/training-hub`, `/document-expirations`, `/po-requests`, `/project-health`, `/asset-transfers`, `/cheatsheet`, `/cheat-sheet`, `/reports`, `/app`, `/operations-center` [A-guarded], `/operations-map` [A-guarded], `/thank-you`, `/submit`, `/*` catch-all, `/transportation-operations/*` [TX-guarded], `/d/:token` public driver landing, `/shift`, `/inspect`) should be consolidated into `feature-routes/misc.jsx` OR folded into their nearest logical portal per the executor's judgment during Phase B execution.

## Load kind counts
- **Lazy** (`React.lazy(...)`): 204 routes
- **Eager** (`import ... from`): 170 routes
- **Inline/local** (`Navigate`, `RedirectWithId`, `InspectionLegacyRedirect`, etc.): 11 routes

Extraction MUST preserve each route's `load` kind. Do not aggressively convert eager → lazy without a bundle-report proof it does not break Suspense boundaries or first-paint SLA.
