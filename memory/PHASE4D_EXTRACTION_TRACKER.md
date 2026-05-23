# Phase 4D · Architectural Extraction Tracker
**Status:** In progress · iter377 complete · iter378+ planned.

This file tracks one-route-family-at-a-time extraction from server.py. Each iteration must:
1. Identify the cleanest extraction unit.
2. Build a `routes/<family>_routes.py` builder factory.
3. Mount via `app.include_router(...)` in server.py.
4. Add a parity regression lock (functional + source-level guards).
5. Confirm full cumulative regression green.
6. NO auth drift · NO lifecycle drift · NO visibility drift · NO route renaming unless necessary.

---

## server.py size watch

| Iteration | Lines | Δ |
|---|---|---|
| Pre-iter370 baseline | ~12,230 | — |
| iter375 (MFA wiring added) | 12,259 | +29 |
| **iter377 (PM read-only extraction)** | **12,065** | **−194** |

First measurable reduction. Pattern proven safe.

---

## Iteration log

### iter377 · PM read-only routes · ✅ COMPLETE

**Extracted from server.py → routes/pm_routes.py:**
- `/pm/check` · `/pm/me`
- `/pm/crew/training-records` · `/pm/crew/ppe` · `/pm/crew/capas` · `/pm/crew/summary`
- Helper: `_pm_crew_employee_names(actor, days=180)`

**Why these 6:**
- Read-only — zero state mutation.
- All consume `require_admin` / `require_admin_async` dependencies that were already factored.
- Zero coupling to `_client_ip`, `_check_login_lockout`, `_record_login_failure`, `_directory_admin_token`, `_clear_session_activity` (none of which are referenced by these handlers).
- Lowest possible risk.

**Left in server.py for iter378+:**
- `/pm/login` · `/pm/forgot-password` · `/pm/reset-password` · `/pm/change-password` · `/pm/logout`
- Heavy IP-lockout + directory-fallback + session-activity coupling.

**Regression**: `tests/test_iter377_pm_routes_extraction.py` — 21/21 PASS.
- 4 functional parity tests (admin unlocks, anon denied, safety rejected, dispatch rejected).
- 6 response-shape tests (each route's output keys + values).
- 3 query-limit tests (lower/upper bound enforcement).
- 8 source-level guards (file exists, factory exists, handlers in new file, handlers gone from server.py, non-extracted routes preserved, helper migrated, mount wired).

**Live smoke**: 200 admin / 401 anon on all 6 routes; response shape identical to pre-extraction.

**Cumulative**: iter354 → iter377 = **171/171 PASS** in ~95s.

---

### iter378 · PM auth lifecycle routes (planned)

**Candidates** (login/logout/password lifecycle — must move as a unit because of shared coupling):
- `/pm/login` (uses `_check_login_lockout`, `_record_login_failure`, `_directory_admin_token`)
- `/pm/forgot-password`
- `/pm/reset-password`
- `/pm/change-password`
- `/pm/logout` (uses `_clear_session_activity`)

**Strategy:**
- Pass shared helpers (`_client_ip`, `_check_login_lockout`, `_record_login_failure`, `_directory_admin_token`, `_clear_session_activity`) as factory kwargs to `build_pm_router` (already extracted) and extend it with login routes.
- Alternative: separate `routes/pm_auth_routes.py` to keep concerns split.
- Add parity lock covering: login success, login wrong password, lockout after N failures, directory super-admin fallback, change-password rotation, logout audit event.

**Risk**: medium — login surface is high-traffic and has subtle directory fallback behavior. Recommend dedicated iteration.

---

### iter379 · Governance routes (planned)

**Candidates**: `/api/governance/*` (~600 LOC).
**Coupling**: low (governance has its own module `governance/inventory.py`).
**Risk**: low.

---

### iter380 · Notifications routes (planned)

**Candidates**: `/api/notifications/*` (~400 LOC).
**Coupling**: low (`notifications` helper module already exists).
**Risk**: low.

---

### iter381 · Shared lookup services (planned)

**Candidates**: `/api/master-lookup/*` (~500 LOC).
**Coupling**: low.
**Risk**: low.

---

### iter382+ · Remaining operational families (planned)

Daily reports, inspections, JHAs, employee CRUD, audit endpoints, etc. — extract incrementally with regression locks. Each family ~200-800 LOC.

---

## Permanent rules (per directive)

- One route family at a time.
- Regression locked **before** moving on.
- Behavior identical · no auth drift · no lifecycle drift · no visibility drift.
- No route renaming unless explicitly required.
- Each iteration adds ≥5 functional parity tests + ≥3 source-level guards.
- Cumulative pytest suite must stay green.
- If an iteration would touch >300 LOC or require a behavior change, STOP and consult operator.

---

## Architectural goals (when Phase 4D wraps)

- `server.py` reduced from 12,259 LOC to <4,000 LOC.
- Each route family lives in `/app/backend/routes/<family>_routes.py`.
- Each family file is a `build_<family>_router(db, ...deps)` factory.
- `server.py` is reduced to: app construction, shared dependencies (db, auth gates, schedulers), router mounting, startup/shutdown hooks.
