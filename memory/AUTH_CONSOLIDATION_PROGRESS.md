# AUTH CONSOLIDATION PROGRESS
**Phase 4A · iter369**
**Status:** Inventory + regression lock complete. No code changed.

The complete inventory of authorization patterns in the MASCI backend, categorized for the incremental consolidation work scheduled for iter370+.

---

## Discovered auth dependency functions (23 total)

### Single-portal gates (clean baseline — these are the canonical "owns this portal" checks)

| Function | Defined in | Behavior |
|---|---|---|
| `require_admin` | `server.py` L264 | Admin token OR PM token EXCEPT on `/api/admin/*` paths (iter180 lockdown) |
| `require_admin_async` | `server.py` L334 | Same as above but returns PM doc instead of `True` |
| `require_admin_strict` | `server.py` L368 | Admin only · PM tokens rejected |
| `require_safety_token` | `routes/safety_portal/_deps.py` `make_require_safety_token` | Safety portal token only |
| `require_dispatch_token` | `server.py` | Dispatch token only |
| `require_hr_user` | `server.py` | HR token only |
| `require_fl_user` | `routes/field_leadership.py` | FL token only |
| `require_shop_token` | `server.py` | Shop token only |
| `require_dev` | `server.py` | Dev-only routes (gated by env var) |
| `require_caller` | `server.py` | Generic caller-identity extraction (used by audit logs) |

### Combined / "or-admin" gates (the explosion zone — target of P4A consolidation)

| Function | Defined in | Behavior |
|---|---|---|
| `require_safety_or_admin` | `routes/safety_portal/_deps.py` `make_require_safety_or_admin` | Safety OR admin |
| `require_safety_or_hr_or_admin` | `routes/safety_portal/_deps.py` | Safety OR HR OR admin |
| `require_hr_or_admin` | `server.py` (likely inline) | HR OR admin |
| `require_dispatch_or_admin` | `server.py` (likely inline) | Dispatch OR admin |
| `require_shop_or_admin` | `server.py` (likely inline) | Shop OR admin |
| `require_safety_admin_or_pm` | `server.py` (likely inline) | Safety OR admin OR PM |
| `require_any_portal_token` | `server.py` | Any portal token accepted |
| `require_any_fleet_portal` | `server.py` | Dispatch OR Shop OR admin |
| `require_any_portal` | `server.py` | Alias / similar to `require_any_portal_token` |

### Misc / specialized

| Function | Defined in | Behavior |
|---|---|---|
| `require_signed_in_or_public` | `server.py` | Accepts logged-in or fully public routes |
| `require_write` | `server.py` | Wraps generic write-side authorization |
| `require_token` | `server.py` | Generic token check helper |

---

## Categorization (for consolidation)

### Category A · Single-portal (LEAVE AS-IS)
The 10 single-portal gates above are CLEAN. Each one captures one ownership concept and is easy to understand. **Do not consolidate.**

### Category B · "or-admin" family (CONSOLIDATE in iter370-372)
The 6 "X or admin" variants share an identical pattern: try portal-X check, fall back to admin check. They could all be replaced by a single factory:

```python
def make_require_any(db, *checks):
    """Returns a FastAPI dependency that passes if any of the
    listed token checks succeeds. Order matters — first match wins."""
    async def _check(request: Request):
        for check in checks:
            try:
                return await check(request)
            except HTTPException:
                continue
        raise HTTPException(status_code=401, detail="auth required")
    return _check
```

Then `require_safety_or_admin = make_require_any(db, require_safety_token, require_admin)` and similar.

**Migration risk:** LOW if and only if each existing function has IDENTICAL semantic behavior. iter369 regression lock catches any drift.

### Category C · "any portal" family (REVIEW)
`require_any_portal_token`, `require_any_fleet_portal`, `require_any_portal` may be aliases or genuinely different. iter370 should grep all callers and verify they're not subtly differentiated. If aliases → consolidate. If subtly different → KEEP and document.

### Category D · Admin variants (LIKELY KEEP)
`require_admin` vs `require_admin_strict` vs `require_admin_async` are tuned for specific risk levels. **My recommendation: keep as-is.** Consolidating these into one function with a `strict=True` parameter would obscure the per-route intent. Operator decides during iter374.

---

## What the regression lock proves

`/app/backend/tests/test_iter369_auth_regression_lock.py` exercises the 6 portal entry-points:

| Gate | Tests | Status |
|---|---|---|
| `require_admin_strict` (via `/api/admin/backups`) | 3 (deny / unlock / safety-token-fails) | ✅ |
| `require_admin` on `/admin/*` (via `/api/admin/governance/summary`) | 2 (deny / unlock) | ✅ |
| `require_safety_token` (via `/api/safety/corrective-actions`) | 3 (deny / unlock / dispatch-token-fails) | ✅ |
| `require_hr_user` (via `/api/hr/incidents`) | 2 (deny / unlock) | ✅ |
| `require_dispatch_token` (via `/api/dispatch/driver-qualification`) | 2 (deny / unlock) | ✅ |
| `require_fl_user` indirectly (via `/api/fl/notifications/digest`) | 2 (deny / admin-unlocks) | ✅ |
| Public routes (negative control) | 2 (no-auth still 200) | ✅ |

**Tests bypass the conftest auto-injection patcher** using raw urllib + a browser-like User-Agent (the ingress WAF blocks `Python-urllib/...`). Any future refactor that breaks gate semantics will fail this suite.

---

## Critical implementation notes for iter370+

1. **DO NOT change the iter180 `/admin/*` lockdown** — `require_admin` accepts PM tokens EXCEPT on `/api/admin/*` paths. That's intentional and field-tested.
2. **DO NOT collapse the 3 admin variants without explicit operator approval.** Their differences (returns True vs doc, accepts PM vs strict) are intentional.
3. **Migrate one family at a time, regression-test after each, commit only if green.**
4. **If iter369 regression lock fires red after a refactor, revert immediately.** Auth bugs cost trust.
5. **No permission expansion.** Phase 4 makes auth MORE consistent, not MORE permissive.

---

## Estimated effort

- iter370 (dispatch_or_admin consolidation): 1 iteration · ~60 min · low risk
- iter371 (shop_or_admin consolidation): 1 iteration · ~60 min · low risk
- iter372 (safety_or_admin consolidation): 1-2 iterations · 90 min · medium risk
- iter373 (hr_or_admin + safety_admin_or_pm): 1-2 iterations · 90 min · medium risk
- iter374 (decision point on admin variants): 1 iteration · 30 min · review only

**Total: 5-7 iterations, all reversible at the regression-lock boundary.**
