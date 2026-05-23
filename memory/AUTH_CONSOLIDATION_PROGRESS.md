# AUTH CONSOLIDATION PROGRESS
**Phase 4A · iter370 + iter371**
**Status:** Dispatch family CONSOLIDATED · Shop fleet-gate CONSOLIDATED · zero behavior drift.

The complete inventory of authorization patterns in the MASCI backend, with execution progress tracked per iteration.

---

## Progress by iteration

| Iter | Work | Status |
|---|---|---|
| iter369 | Inventory + auth regression lock (16 tests) | ✅ |
| iter370 | R7 fix (admin-strict fail-closed) + dispatch_or_admin parity lock (11 tests) | ✅ |
| **iter370 (completed)** | Dispatch shared factory `make_require_dispatch_or_admin` extracted · both consumers delegate · regression lock updated to lock new shape | ✅ |
| **iter371** | Shop fleet-gate shared factory `make_require_shop_or_admin_fleet` extracted · 7-test regression lock added · richer `require_shop_or_admin` intentionally preserved | ✅ |
| iter372 | safety_or_admin family consolidation (highest-traffic) | 🟡 planned |
| iter373 | hr_or_admin + safety_admin_or_pm | 🟡 planned |
| iter374 | Auth hardening review checkpoint (no code) | 🟡 planned |

---

## iter370 deliverables · ✅ COMPLETE

### R7 fix — `require_admin_strict` now fails CLOSED
- **Before:** `if not expected_pw: return True` — empty env var = admin bypass.
- **After:** explicit `HTTPException(503, "Admin authentication not configured")`.
- **Location:** `/app/backend/server.py` L368-401 (require_admin_strict).
- **Regression lock:** `/app/backend/tests/test_iter370_r7_admin_strict_fail_closed.py` — 4/4 PASS.

### Dispatch_or_admin consolidation — FINISHED iter370
- **Canonical factory:** `routes/dispatch_portal_auth.make_require_dispatch_or_admin(db, is_valid_admin_token_fn)` — single source of truth for the role-dict shape and semantics.
- **dispatch_portal_auth.build_dispatch_router** → uses `require_dispatch_or_admin = make_require_dispatch_or_admin(db, is_valid_admin_token_fn)`. No closure body.
- **server.py** → imports the factory at module load, builds `_shared_dispatch_or_admin` once, and `_require_dispatch_or_admin` wrapper delegates to it (keeps signature for fleet_ops kwargs injection).
- **Regression lock:** `/app/backend/tests/test_iter370_dispatch_or_admin_parity.py` — 8/8 PASS:
  - Functional: deny without token, accept admin, reject safety (cross-portal isolation) on BOTH variants.
  - Source-level: shared factory exists, both consumers reference it, server.py wrapper no longer contains the role-dict literal.

---

## iter371 deliverables · ✅ COMPLETE

### Shop fleet-gate consolidation
**Key insight:** The two shop gates are NOT semantically equal (unlike dispatch):
- `server.py require_shop_or_admin` → richer chain (admin/shop-HMAC/shop-user/PM-token/per-PM-doc) + iter180 admin-namespace lockdown.
- `_require_shop_or_admin_fleet` → narrow (admin/shop-HMAC only), `{role: ...}` dict shape. Used only by fleet_ops.

The narrow fleet gate was extracted into a shared factory; the richer gate was intentionally NOT touched.

- **Canonical factory:** `routes/shop_portal_deps.make_require_shop_or_admin_fleet(db, is_valid_admin_token_fn, shop_token_for_fn)`.
- **server.py** → imports the factory at module load, builds `_shared_shop_or_admin_fleet` once, and `_require_shop_or_admin_fleet` wrapper delegates to it.
- **Regression lock:** `/app/backend/tests/test_iter371_shop_or_admin_parity.py` — 7/7 PASS:
  - Functional: deny without token, accept admin, reject dispatch (cross-portal isolation).
  - Source-level: shared factory exists, server.py wrapper delegates (no inline role dict), the richer `require_shop_or_admin` is preserved with its iter180 admin-namespace lockdown.

---

## Discovered auth dependency functions (23 total)

(See iter369 baseline below — UNCHANGED in iter370/iter371.)

### Single-portal gates (clean baseline — these are the canonical "owns this portal" checks)

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
| `require_caller` | `server.py` | Generic caller-identity extraction (used by audit logs) | KEEP |

### Combined / "or-admin" gates (consolidation target)

| Function | Variants | Status |
|---|---|---|
| `require_dispatch_or_admin` | shared factory + 2 delegating consumers | ✅ CONSOLIDATED iter370 |
| `_require_shop_or_admin_fleet` | shared factory + delegating wrapper | ✅ CONSOLIDATED iter371 |
| `require_shop_or_admin` (richer) | inline (admin+shop+PM, namespace lockdown) | 🔒 KEEP (different surface) |
| `require_safety_or_admin` | 1 canonical (`_deps.py`) + 1 wrapper (`_require_safety_or_admin_fleet`) | similar pattern · audit iter372 |
| `require_safety_or_hr_or_admin` | 1 implementation (`_deps.py`) | review iter373 |
| `require_hr_or_admin` | inline in server.py | audit iter373 |
| `require_safety_admin_or_pm` | inline | audit iter373 |
| `require_any_portal_token` | server.py | review iter374 |
| `require_any_fleet_portal` | server.py | review iter374 |
| `require_any_portal` | server.py | review iter374 |

---

## Architectural pattern emerging (refined post-iter371)

The consolidation pattern is now proven across TWO portals:

1. Each "or-admin" fleet-ops gate has a **canonical factory** at module scope (in the portal's deps file).
2. The factory takes `db` and `is_valid_admin_token_fn` (plus any portal-specific token helpers).
3. server.py's wrapper function survives for FastAPI's kwargs-injection contract with `fleet_ops.py`, but its body now delegates to the factory output.
4. A regression lock per iteration locks (a) factory existence, (b) consumer delegation, (c) cross-portal isolation.

**Next:** iter372 applies the same pattern to safety (highest-traffic).

---

## Cumulative regression health

iter354 → iter371: **100/100 pytest items PASS** in ~55s.

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
- iter370 dispatch_or_admin parity (updated for consolidated shape) — 8 tests
- **iter371 shop_or_admin fleet parity — 7 tests** (NEW)

This suite must remain green throughout iter372+ work.
