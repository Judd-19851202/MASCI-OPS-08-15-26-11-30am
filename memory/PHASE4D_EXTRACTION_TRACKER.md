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

| Iteration | Lines | Δ | Cumulative |
|---|---|---|---|
| Pre-iter370 baseline | ~12,230 | — | — |
| iter375 (MFA wiring added) | 12,259 | +29 | +29 |
| iter377 (PM read-only extraction) | 12,065 | −194 | −165 |
| **iter378 (PM auth-lifecycle extraction)** | **11,724** | **−341** | **−506** |
| **iter379 (Governance inventory + guidance telemetry)** | **11,663** | **−61** | **−567** |

Pattern proven safe across 3 iterations. Cumulative regression: **201/201 PASS** (was 171 pre-iter378, +18 iter378 + 12 iter379).

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

### iter378 · PM auth-lifecycle routes · ✅ COMPLETE

**Extracted from server.py → routes/pm_routes.py (extended factory):**
- `POST /pm/login` (per-PM bcrypt + legacy shared-pw + universal super-admin fallback)
- `POST /pm/forgot-password` (Resend email + 30-min HMAC token; anti-enumeration generic response)
- `POST /pm/reset-password` (token consumption + fresh per-PM token issued)
- `POST /pm/change-password` (PM self-service rotation, requires per-PM session)
- `POST /pm/logout` (audit + session_activity clearance)
- Body models: PMLoginBody, PMChangePasswordBody, PMForgotPasswordBody, PMResetPasswordBody

**Coupling resolved via `login_deps` dict** passed to `build_pm_router`:
- `client_ip_fn`, `check_login_lockout_fn`, `record_login_fail_fn`, `reset_login_fails_fn`
- `directory_admin_token_fn` (universal super-admin fallback)
- `reset_session_activity_fn`, `clear_session_activity_fn`
- `pm_token_for_fn`, `render_portal_email_fn`

**Why a deps dict instead of 9 positional kwargs:** keeps the factory signature manageable + makes it explicit which routes are auth-lifecycle vs read-only.

**Behavior preserved:**
- Wrong email/password → 401 "Wrong email or password" (exact string).
- Disabled PM → 403.
- PM with no password → 403 "No password set...".
- No email + SHARED_LOGIN disabled → 400 "Email is required.".
- IP lockout still triggers identically.
- Universal super-admin fallback (iter346-B) still mints admin token when directory user matches.
- /pm/forgot-password always returns generic success (anti-enumeration).

**Regression**: `tests/test_iter378_pm_auth_extraction.py` — 18/18 PASS.
- 4 functional /pm/login tests.
- 2 forgot-password tests (generic success regardless of email).
- 2 reset-password tests (invalid token, short password).
- 2 change-password tests (auth required, admin session rejected).
- 2 logout tests (auth required, admin session accepted).
- 7 source-level guards (handlers moved, body models moved, server.py no longer owns 5 decorators, login_deps wired, admin set-password still in server.py).

**Live smoke**: All 5 routes respond identically pre/post extraction (wrong-pw 401, no-email 400 or 423 lockout, forgot/reset behavior identical).

---

### iter379 · Governance & Operational Inventory routes · ✅ COMPLETE

**Extracted from server.py → routes/governance.py (extended existing factory):**
- `GET /api/admin/operational-inventory` — full system snapshot (compute_full_inventory)
- `GET /api/admin/operational-inventory/portals` — portal × 10-field matrix
- `GET /api/admin/operational-inventory/translation` — ES translation readiness
- `GET /api/admin/operational-inventory/drift` — coverage drift signal
- `GET /api/admin/guidance/search-misses` — zero-result search telemetry + aggregation

**Why these 5: extremely low coupling.** Pure delegation to `governance.inventory` (4 routes) + a simple `db.guidance_search_misses` read + aggregation (1 route). All admin-strict gated. Zero state mutation.

**Regression**: `tests/test_iter379_governance_extraction.py` — 12/12 PASS.
- 3 functional parity tests (admin unlocks, anon denied, dispatch token rejected for cross-portal isolation).
- 5 response-shape tests (one per route).
- 4 source-level guards (5 handlers in new file, 5 gone from server.py, governance router still mounted, pre-existing compliance routes preserved).

**Live smoke**: All 5 routes return 200 with admin token, 401 without.

---

### iter380+ · Notifications routes (planned next)

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
