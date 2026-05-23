# AUTH CONSOLIDATION PROGRESS
**Phase 4A · iter370**
**Status:** R7 CLOSED · dispatch_or_admin parity LOCKED · zero behavior drift.

The complete inventory of authorization patterns in the MASCI backend, with execution progress tracked per iteration.

---

## Progress by iteration

| Iter | Work | Status |
|---|---|---|
| iter369 | Inventory + auth regression lock (16 tests) | ✅ |
| **iter370** | R7 fix (admin-strict fail-closed) + dispatch_or_admin parity lock (11 tests) | ✅ |
| iter371 | shop_or_admin family consolidation | 🟡 planned |
| iter372 | safety_or_admin family consolidation (highest-traffic) | 🟡 planned |
| iter373 | hr_or_admin + safety_admin_or_pm | 🟡 planned |
| iter374 | Auth hardening review checkpoint (no code) | 🟡 planned |

---

## iter370 deliverables · ✅ COMPLETE

### R7 fix — `require_admin_strict` now fails CLOSED
- **Before:** `if not expected_pw: return True` — empty env var = admin bypass.
- **After:** explicit `HTTPException(503, "Admin authentication not configured")`.
- **Location:** `/app/backend/server.py` L368-401 (require_admin_strict).
- **Regression lock:** `/app/backend/tests/test_iter370_r7_admin_strict_fail_closed.py` — 4/4 PASS:
  - Source-level guard: no future refactor can re-introduce the escape hatch shape.
  - Functional: valid admin token still unlocks (no breaking change).
  - Functional: no token still denies (401 unchanged).
  - Functional: PM token still rejected on admin-strict surface.

### Dispatch_or_admin parity lock
- **Discovery:** Two `dispatch_or_admin` gates exist:
  1. `routes/dispatch_portal_auth.py` L117 (closure inside `build_dispatch_router` factory)
  2. `server.py` L10670 `_require_dispatch_or_admin` (free function, used by `routes/fleet_ops.py`)
- **Decision:** **No code merge this iteration.** Both have identical semantics but live in different scopes. Merging requires moving the closure to module scope — bigger refactor.
- **Locked instead:** `/app/backend/tests/test_iter370_dispatch_or_admin_parity.py` — 7/7 PASS:
  - Both routes deny without token (parity).
  - Both routes accept admin token identically (parity).
  - Both routes reject safety token identically (cross-portal isolation parity).
  - Both source files keep their definitions (no accidental removal).
  - Both return identical `{role: 'admin'}` / `{role: 'dispatch', ...}` shape.

The parity lock means iter371+ can merge these two functions safely; any drift will fail this test.

---

## Discovered auth dependency functions (23 total)

(See iter369 baseline below — UNCHANGED in iter370.)

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

| Function | Variants | iter370 Status |
|---|---|---|
| `require_dispatch_or_admin` | 2 implementations (closure + free function) | 🔒 parity LOCKED iter370 · merge possible iter371+ |
| `require_safety_or_admin` | 1 canonical (`_deps.py`) + 1 wrapper (`_require_safety_or_admin_fleet`) | similar pattern · audit iter372 |
| `require_safety_or_hr_or_admin` | 1 implementation (`_deps.py`) | review iter373 |
| `require_hr_or_admin` | inline in server.py | audit iter373 |
| `require_shop_or_admin` | inline + `_require_shop_or_admin_fleet` wrapper | similar pattern · audit iter371 |
| `require_safety_admin_or_pm` | inline | audit iter373 |
| `require_any_portal_token` | server.py | review iter374 |
| `require_any_fleet_portal` | server.py | review iter374 |
| `require_any_portal` | server.py | review iter374 |

### Misc / specialized

(unchanged from iter369)

---

## Architectural pattern emerging

After iter370 discovery, the pattern is clearer:
- Each "or-admin" gate has a **canonical** implementation (inside its portal module factory) AND a **fleet-ops wrapper** (in server.py) for the cross-portal `fleet_ops.py` consumer.
- The wrappers exist because `fleet_ops.py` receives gate dependencies via kwargs, but the canonical closures live inside their own factory.

**Proposed iter371-iter373 consolidation pattern:**
1. For each portal (dispatch, shop, safety, hr): extract its `_or_admin` gate from the closure into module scope, parametrized on `db`.
2. server.py's wrapper then delegates: `_require_X_or_admin = make_require_X_or_admin(db)`.
3. Run parity lock from iter370 — must stay green.

This is a 2-3 hour refactor across iter371-iter373. Each iteration migrates ONE portal.

---

## Cumulative regression health

iter354 → iter370: **92/92 pytest items PASS** in 45s.

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
- **iter370 R7 admin-strict fail-closed — 4 tests** (NEW)
- **iter370 dispatch_or_admin parity — 7 tests** (NEW)

This suite must remain green throughout iter371+ work.
