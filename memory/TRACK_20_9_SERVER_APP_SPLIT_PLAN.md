# TRACK 20.9 · Server.py + App.js Split Plan (Phase 2 · POST-DEPLOY)

**Verdict:** ❌ **DO NOT REFACTOR IN TRACK 20.9.**

Both files are structurally central to the platform. A pre-deploy split carries real regression risk that outweighs the aesthetic benefit. Track 20.9 documents the plan for a future dedicated split track (**Track 21.x**), executed AFTER the current deployment ships and stabilizes for at least one week.

## `backend/server.py` audit

- **Line count:** 15,986.
- **Imports from elsewhere:** 100+ files under `backend/routes/*.py` import symbols from `backend.server` (e.g. `require_admin`, `require_admin_pm_or_hr_read`, `schedule_auto_email`, `_dispatch_auto_email`, `_is_valid_admin_token`, `emit_workflow_stage` helpers, `db`, etc.).
- **Route registration:** the file is where the FastAPI `api_router` is created AND where 200+ inline routes are declared AND where 100+ `register_*_routes(api_router, db, require_admin, require_admin_pm_or_hr_read, ...)` callbacks are invoked to attach the route modules under `backend/routes/`.
- **Middleware:** CORS + trust-spine + backup scheduler + integration probes all live in this file.
- **Scheduler:** `_backup_scheduler_loop` and `asset_spine_scheduler` bootstrap.
- **Shared state:** `db` singleton, config env-var readers, `logger`, HMAC helpers.

## Why splitting is high-risk pre-deploy

1. **Circular-import surface.** Moving `require_admin` to `backend/auth/gates.py` requires updating every `backend/routes/*.py` file that imports it. A missed rename creates a runtime AttributeError only on the first request to that route.
2. **`_dispatch_auto_email` moved would break Track 20.6B synthetic-test-record gate.** The gate is inline with the dispatcher. Moving it out requires re-verifying the trust-spine event emission path.
3. **Scheduler lifecycle.** Startup + shutdown hooks are inline. Moving them requires re-verifying supervisor lifecycle.
4. **CORS middleware order matters.** The Track 15.79 photo-thumbnail cache middleware runs AFTER CORS. Ordering must be preserved.
5. **The current file works.** All 385+ envelope tests are green. All 300+ routes render. Zero-drift mandate says: don't touch what's proven.

## Phase-2 (post-deploy) split plan — LOW-RISK EXTRACTIONS FIRST

Executed on a dedicated **Track 21.x — Server.py Modularization**. Each extraction is its own micro-track with lock-test coverage BEFORE landing.

### Extraction 1 · Auth gates (~800 lines · 100+ import sites)
- New module: `backend/auth/gates.py`.
- Move: `_is_valid_admin_token`, `_is_valid_directory_admin_token_async`, `require_admin`, `require_admin_pm_or_hr_read`, `require_pm_or_admin`, `require_safety_or_admin`, `is_valid_pm_user_token_async`, `is_valid_hr_user_token_async`.
- Re-export from `backend/server.py` for backwards-compat.
- Lock test: assert every existing import in `backend/routes/*.py` still resolves.

### Extraction 2 · Trust-spine adapter (~200 lines)
- New module: `backend/trust_spine/dispatch.py`.
- Move: `_dispatch_auto_email`, `schedule_auto_email`, `auto_email_enabled`.
- **Preserve the Track 20.6B synthetic-test-record short-circuit verbatim.** Track 20.9 lock test verifies its presence; after extraction the same test must still pass on the new location.
- Lock test: `test_synthetic_test_record_short_circuit_present` (from Track 20.6B) MUST still pass.

### Extraction 3 · CORS + middleware (~150 lines)
- New module: `backend/middleware/cors_config.py`.
- Move: `_DEFAULT_CORS_REGEX`, `_cors_origins`, `_cors_credentials`, CORS middleware install, photo-thumbnail cache middleware.
- **Preserve order.** Photo-thumb middleware must run AFTER CORS.

### Extraction 4 · Scheduler loops (~400 lines)
- New module: `backend/schedulers/loops.py`.
- Move: `_backup_scheduler_loop`, backup supervisor arming, asset-spine scheduler.

### Extraction 5 · Health endpoints (~300 lines)
- New module: `backend/routes/health.py`.
- Move: `/api/health`, `/api/health/full`, `/api/version`, integration health probes.

### Extraction 6 · Miscellaneous helpers (~500 lines)
- New module: `backend/util/helpers.py`.
- Move: date helpers, `attach_correlation`, `emit_workflow_stage`, etc.

Each extraction adds ~1 hour of lock-test authoring and validation. Total Track 21.x scope: **~10 hours** with full test coverage. Not viable pre-deploy without high risk.

## `frontend/src/App.js` audit

- **Line count:** 1,283.
- **What lives in it:** every `<Route>` definition on the platform. 300+ route paths.
- **Ordering-sensitivity:** React Router `<Routes>` uses first-match. Reordering can silently change which component renders for a given path.
- **Auth-guard wrappers:** every route is wrapped by one or more of `A(...)`, `AP(...)`, `AH(...)`, `SP(...)`, `PMP(...)`, `SHP(...)`, `DP(...)`, `FLP(...)` (portal-guarded lazy loaders). Extracting requires preserving the guard semantics.

## Why splitting `App.js` is high-risk pre-deploy

1. **Route-ordering silent regression.** Moving a group of routes to a sub-file and re-including it could put them in a different `<Routes>` traversal order.
2. **Portal-guard wrappers.** Each is a HOC-like function. Extracting groups requires importing the wrappers.
3. **Lazy-loading + Suspense.** The current file uses `React.lazy(() => import(...))` for every route. Splitting into sub-files may fragment code-splitting boundaries and change bundle chunking.
4. **The current file works.** Track 20.8 human walkthrough proved every portal + primary surface renders cleanly. Zero-drift.

## Phase-2 (post-deploy) route-registry plan

Executed on a dedicated **Track 21.y — App.js Route-Group Extraction**. Each extraction preserves route order exactly.

- Extract `<Route path="/admin/*">` group → `frontend/src/routes/AdminRoutes.jsx`.
- Extract `<Route path="/pm/*">` group → `frontend/src/routes/PMRoutes.jsx`.
- Extract `<Route path="/hr/*">` group → `frontend/src/routes/HRRoutes.jsx`.
- Extract `<Route path="/safety/*">` group → `frontend/src/routes/SafetyRoutes.jsx`.
- Extract `<Route path="/shop/*">` group → `frontend/src/routes/ShopRoutes.jsx`.
- Extract `<Route path="/dispatch-portal/*">` group → `frontend/src/routes/DispatchRoutes.jsx`.
- Extract public routes (`/daily/submit`, `/trench-boxes`, etc.) → `frontend/src/routes/PublicRoutes.jsx`.

Lock test: `test_all_portal_routes_render` — hits every top-level portal path in headless Chromium; passes iff every existing surface still renders with the same top-level component.

## Ship posture

Track 20.9's zero-drift mandate: neither file was touched. Both stay at their current line counts. Both audits produced a Phase-2 plan for post-deploy execution.

## Deployment call

🟢 Ship the current file structure. Modularization is a post-deploy stability improvement, not a pre-deploy risk.
