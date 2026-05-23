# AUTH CONSOLIDATION PROGRESS
**Phase 4A · iter370–iter374 · ✅ COMPLETE**
**Status:** Dispatch / Shop / Safety / HR families ALL CONSOLIDATED · Phase 4A wrapped via iter374 audit checkpoint · zero behavior drift.

The complete inventory of authorization patterns in the MASCI backend, with execution progress tracked per iteration.

---

## Progress by iteration

| Iter | Work | Status |
|---|---|---|
| iter369 | Inventory + auth regression lock (16 tests) | ✅ |
| iter370 | R7 fix (admin-strict fail-closed) · dispatch_or_admin shared factory + delegation + regression lock | ✅ |
| iter371 | shop_or_admin fleet shared factory + delegation · richer `require_shop_or_admin` preserved | ✅ |
| iter372 | safety_or_admin fleet shared factory + delegation · richer write/read gates preserved | ✅ |
| **iter373** | `make_require_hr_user` shared factory · hr_portal delegates · two `require_hr_or_admin` closures documented as intentionally distinct | ✅ |
| **iter374** | Auth Hardening Review checkpoint (REPORT ONLY) · Phase 4A signed off · see `ITER374_AUTH_HARDENING_REVIEW.md` | ✅ |

---

## iter370 deliverables · ✅ COMPLETE

### R7 fix — `require_admin_strict` now fails CLOSED
- **Before:** `if not expected_pw: return True` — empty env var = admin bypass.
- **After:** explicit `HTTPException(503, "Admin authentication not configured")`.
- **Location:** `/app/backend/server.py` L368-401.
- **Regression lock:** `tests/test_iter370_r7_admin_strict_fail_closed.py` — 4/4 PASS.

### Dispatch consolidation (FINISHED)
- **Canonical factory:** `routes/dispatch_portal_auth.make_require_dispatch_or_admin(db, is_valid_admin_token_fn)` — single source of truth.
- `dispatch_portal_auth.build_dispatch_router` → uses `require_dispatch_or_admin = make_require_dispatch_or_admin(...)`.
- `server.py` → imports factory at module load, builds `_shared_dispatch_or_admin` once, wrapper delegates.
- **Regression lock:** `tests/test_iter370_dispatch_or_admin_parity.py` — 8/8 PASS.

---

## iter371 deliverables · ✅ COMPLETE

### Shop fleet-gate consolidation
**Key insight:** The two shop gates are NOT semantically equal:
- `server.py require_shop_or_admin` → richer chain (admin/shop-HMAC/shop-user/PM-token/per-PM-doc) + iter180 admin-namespace lockdown. **Untouched.**
- `_require_shop_or_admin_fleet` → narrow (admin/shop-HMAC only), `{role:...}` shape. Used only by fleet_ops. **Migrated.**

- **Canonical factory:** `routes/shop_portal_deps.make_require_shop_or_admin_fleet(db, is_valid_admin_token_fn, shop_token_for_fn)`.
- `server.py` wrapper delegates to factory output.
- **Regression lock:** `tests/test_iter371_shop_or_admin_parity.py` — 7/7 PASS.

---

## iter372 deliverables · ✅ COMPLETE

### Safety family inventory

| Helper | Type | iter372 Action |
|---|---|---|
| `make_require_safety_token` (`_deps.py`) | canonical safety-only gate, no duplicate | KEEP |
| `make_require_safety_or_admin` (`_deps.py`) | richer write-side · returns `{_actor:...}` · 3 consumers via factory | KEEP (already factored) |
| `make_require_safety_or_hr_or_admin` (`_deps.py`) | shared HR/Safety/Admin read · already factored | KEEP |
| `make_require_safety_admin_or_pm` (`_deps.py`) | iter322 read gate (Safety/Admin/PM) | KEEP |
| **`_require_safety_or_admin_fleet`** (server.py L10694) | narrow fleet-ops gate · returns `{role:...}` · used only by fleet_ops kwargs injection | **MIGRATED to factory** |
| `_li_require_uploader` (server.py L10158) | specialized HR/Safety/Admin uploader · distinct return shape | KEEP — not a duplicate |
| `_require_any_fleet_portal` (server.py L10746) | 4-way multi-portal aggregator | KEEP — iter374 audit |

### Migration executed
- **Canonical factory:** `routes/safety_portal/_deps.py · make_require_safety_or_admin_fleet(db, is_valid_admin_token_fn)`.
  - Return shape `{role:...}` preserved (admin-first check order, identical to dispatch + shop fleet factories).
  - Distinct from `make_require_safety_or_admin` (which keeps the `_actor` return shape) — both coexist.
- `server.py` → imports factory at module load, builds `_shared_safety_or_admin_fleet` once, wrapper delegates (signature preserved for fleet_ops kwargs injection).

### Regression lock: `tests/test_iter372_safety_or_admin_parity.py` — 21/21 PASS
**Functional · fleet gate:**
- anon denied (401), admin accepted, safety accepted, dispatch rejected (cross-portal), shop rejected (cross-portal).

**Functional · richer surfaces (untouched):**
- Site inspection POST denies anon, topic library admin works.

**Functional · iter322 read gate (`safety_admin_or_pm`):**
- `/api/incidents` accepts admin AND safety (locks iter322 fix).
- Anonymous rejected.

**Functional · HR/Safety/Admin shared visibility:**
- `/api/safety/training-records` accepts admin AND safety AND HR.
- Anonymous rejected.

**Source-level (7 guards):**
- Shared fleet factory exists.
- Richer `make_require_safety_or_admin` preserved (`_actor` shape contract intact).
- server.py delegates (no inline role dict in wrapper body).
- `make_require_safety_token`, `safety_or_hr_or_admin`, `safety_admin_or_pm` all preserved.

### Live smoke verification
- `/api/safety/fleet/emergency-equipment` — admin 200 · safety 200 · dispatch 401 · anon 401.
- `/api/incidents` — admin 200 · safety 200 · anon 401.
- `/api/safety/training-records` — admin 200 · safety 200 · hr 200 · anon 401.

**Zero permission drift. Zero portal visibility change. CAPA / Incident / Training surfaces unchanged.**

---

## Discovered auth dependency functions (23 total)

### Single-portal gates (clean baseline)

| Function | Defined in | Behavior | Status |
|---|---|---|---|
| `require_admin` | `server.py` L264 | Admin OR PM EXCEPT on `/api/admin/*` (iter180 lockdown) | KEEP |
| `require_admin_async` | `server.py` L334 | Same as above but returns PM doc instead of `True` | KEEP |
| `require_admin_strict` | `server.py` L368 | Admin only · PM tokens rejected · **iter370 R7 fixed** | KEEP, hardened |
| `require_safety_token` | `routes/safety_portal/_deps.py` | Safety portal token only | KEEP |
| `require_dispatch_token` | `routes/dispatch_portal_auth.py` factory | Dispatch token only | KEEP |
| `require_hr_user` | `server.py` | HR token only | KEEP |
| `require_fl_user` | `routes/field_leadership.py` | FL token only | KEEP |
| `require_shop_token` | `server.py` | Shop token only | KEEP |
| `require_dev` | `server.py` | Dev-only routes (gated by env var) | KEEP |
| `require_caller` | `server.py` | Generic caller-identity extraction | KEEP |

### Combined / "or-admin" gates (consolidation status)

| Function | Variants | Status |
|---|---|---|
| `require_dispatch_or_admin` | shared factory + 2 delegating consumers | ✅ CONSOLIDATED iter370 |
| `_require_shop_or_admin_fleet` | shared factory + delegating wrapper | ✅ CONSOLIDATED iter371 |
| `_require_safety_or_admin_fleet` | shared factory + delegating wrapper | ✅ CONSOLIDATED iter372 |
| `require_shop_or_admin` (richer) | inline (admin+shop+PM, iter180 lockdown) | 🔒 KEEP (different surface) |
| `require_safety_or_admin` (richer, `_deps.py`) | factory, returns `_actor` | 🔒 KEEP (different return shape) |
| `require_safety_or_hr_or_admin` | factory, used by 2 callers | KEEP (already factored) |
| `require_hr_or_admin` | inline in server.py | audit iter373 |
| `require_safety_admin_or_pm` | factory (iter322 fix) | KEEP |
| `require_any_portal_token` | server.py | review iter374 |
| `require_any_fleet_portal` | server.py | review iter374 |
| `require_any_portal` | server.py | review iter374 |

---

## Architectural pattern (proven across 3 portals)

The factory + delegation pattern is now proven for dispatch (iter370), shop (iter371), and safety (iter372):

1. Each "or-admin" fleet-ops gate has a `make_require_X_or_admin_fleet(db, is_valid_admin_token_fn[, ...])` factory at module scope in the portal's deps file.
2. `server.py` imports the factory once at module load, builds the gate, and the surviving wrapper function delegates (preserves FastAPI kwargs-injection signature for fleet_ops).
3. One regression lock per iteration covers (a) anon denied, (b) own portal accepted, (c) admin accepted, (d) cross-portal tokens rejected, (e) richer gates and shared-visibility surfaces unchanged, (f) source-level shape (factory exists, wrapper delegates, no inline role-dict rebuild).

**iter373 candidates:** `require_hr_or_admin` (inline in server.py — needs factory extraction).

---

## Cumulative regression health

iter354 → iter374: **134/134 pytest items PASS** in ~57s. **Phase 4A complete.**

- iter354 governance phase2 — 5 tests
- iter355 employee linkage — 5 tests
- iter356 capa lifecycle — 11 tests
- iter357 notifications digest — 5 tests
- iter358 digest expansion — 6 tests
- iter359 employee roster field — 5 tests
- iter363 employee linkage persistence — 11 tests
- iter364 p1 linkage persistence — 6 tests
- iter368 incident-capa reverse link — 4 tests
- iter369 auth regression lock — 16 tests
- iter370 R7 admin-strict fail-closed — 4 tests
- iter370 dispatch_or_admin parity — 8 tests
- iter371 shop_or_admin fleet parity — 7 tests
- iter372 safety_or_admin fleet parity — 21 tests
- **iter373 hr_user factory parity — 13 tests** (NEW)
- iter374 — report-only, no new tests

---

## iter373 deliverables · ✅ COMPLETE

### HR family inventory (after careful audit)

| Helper | Location | Type | Action |
|---|---|---|---|
| **`require_hr_user`** (closure) | `routes/hr_portal.py` L133 | canonical HR-only token resolver | **MIGRATED to factory** |
| `require_hr_or_admin` (closure) | `routes/employee_lifecycle.py` L760 | filter-on-aggregator (`require_any_portal_token` + filter) · 403 error | KEEP — intentional pattern |
| `require_hr_or_admin` (closure) | `routes/field_leadership_portal.py` L135 | direct admin/HR chain · exception-swallow on PM-only · 401 error | KEEP — tightly coupled |
| `make_require_safety_or_hr_or_admin` | `routes/safety_portal/_deps.py` | shared HR/Safety read | KEEP (already factored) |

### Migration executed
- **Canonical factory:** `routes/hr_portal_deps.py · make_require_hr_user(db)`.
  - Mirrors `make_require_safety_token` shape and behavior.
  - Returns `{**user, "_actor_kind": "hr_user"}`.
  - 401 "HR login required" / "HR session expired or invalid" preserved verbatim.
- `routes/hr_portal.py` → imports factory, builds `require_hr_user = make_require_hr_user(db)`. No inline closure body.
- The two `require_hr_or_admin` closures left INTENTIONALLY UNCHANGED. Rationale documented in `routes/hr_portal_deps.py` module docstring AND locked by 2 source-level regression tests.

### Regression lock: `tests/test_iter373_hr_user_parity.py` — 13/13 PASS
- **HR-only gate (5 tests):** anon denied, HR accepted on `/api/hr/me` + `/api/hr/training-records`, safety/admin rejected on `/api/hr/me` (HR portal is HR-only).
- **Shared HR/Safety/Admin surface unchanged (3 tests):** admin/safety/HR all accepted on `/api/safety/training-records`.
- **Source-level (5 tests):** factory exists with `_actor_kind=hr_user` shape, hr_portal delegates, employee_lifecycle's filter-on-aggregator closure preserved, field_leadership's direct-chain closure preserved, `make_require_safety_or_hr_or_admin` factory still canonical.

### Live smoke verification
- `/api/hr/me` — hr 200 · admin 401 (HR portal is HR-only) · anon 401.
- `/api/hr/training-records` — hr 200 · anon 401.

**Zero permission drift. Zero portal visibility change.**

---

## iter374 deliverables · ✅ COMPLETE (REPORT ONLY)

Full audit checkpoint published to `/app/memory/ITER374_AUTH_HARDENING_REVIEW.md`. Highlights:

- **3 aggregator gates** audited (`make_require_any_portal_token`, `_require_any_fleet_portal`, `_require_fleet_submitter`). All have distinct semantics — recommendation: **DO NOT consolidate further** without operator approval.
- **3 intentional closure gates** preserved (`_li_require_uploader`, two `require_hr_or_admin` variants). Documented rationale for each.
- **3 admin variants** (`require_admin`, `require_admin_async`, `require_admin_strict`) — recommendation: **KEEP three-variant shape** (PM-policy + return-shape differences are intentional).
- **Cross-portal isolation matrix** documented for all 15 surface families. Zero permission expansion or removal across iter370→iter374.
- **Audit log integrity** verified — all factories raise identical exceptions with identical messages; audit middleware attribution unchanged.

### Recommended next steps (operator decision)
- **P4B · MFA TOTP for super-admins** — highest trust-reinforcement win.
- **P4D · server.py architectural extraction** — `server.py` is 12k+ LOC.
- **P4C · production parity** — playbook ready, awaiting operator deploy.

---

## Phase 4A sign-off

✅ 4 fleet-style gates consolidated to shared factories.
✅ R7 admin-strict vulnerability closed.
✅ 134/134 cumulative regression tests passing.
✅ Zero permission drift across all surfaces.
✅ All intentional differences documented and locked.
