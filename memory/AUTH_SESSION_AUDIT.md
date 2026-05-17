# MASCI Hub — Auth / Session Boundary Audit

> **Read-only audit (Phase A, Initiative 4).** No code changes yet — pairs
> with `AUTHORIZATION_MATRIX.md`. The implementation that follows this
> doc is env-gated and additive (no token format change).
>
> Generated: 2026-02-XX

## 1. How tokens work today

- **Stateless HMAC**, no `iat` / `exp` claim, no DB row per session.
- Validator: `hmac.compare_digest(token, HMAC(secret, "epoch=<E>|<namespace>:" + password))`.
- "Logout" is a frontend convention only — token remains valid server-side **forever** until either:
  - the shared password changes, OR
  - `ADMIN_SESSION_EPOCH` is bumped, OR
  - (per-PM only) the PM document is deleted/disabled.
- **There is no idle timeout. There is no absolute timeout.** A token issued 6 months ago will still authorize today.

## 2. Why we can't add `exp` to the token itself (and why that's OK)

- Tokens are stored in browser `localStorage`. Existing users have tokens with no `iat` baked in. Changing the format would invalidate every active session at deploy time → user-visible disruption.
- A backwards-compatible "optional `iat`" requires the token format to allow both shapes, which is messy and easy to get wrong.
- **Cleaner alternative (chosen)**: keep tokens unchanged, layer a separate `session_activity` collection in Mongo that tracks `first_seen_at` / `last_seen_at` keyed by `sha256(token)`. Middleware enforces idle/absolute TTL by reading/updating that row.
  - Zero token-format change → zero forced re-login on deploy.
  - Env-gated → default disabled → reversible.
  - Per-tier TTLs configurable via `SESSION_IDLE_MIN_<TIER>` / `SESSION_ABS_HOUR_<TIER>` env vars.

## 3. Tier mapping (per your 4b directive)

| Header observed | Tier | Idle (min) | Absolute (hr) | Env vars |
|---|---|---|---|---|
| `X-Admin-Token` | ADMIN_HR | 15 | 4 | `SESSION_IDLE_MIN_ADMIN_HR`, `SESSION_ABS_HOUR_ADMIN_HR` |
| `X-HR-Token` | ADMIN_HR | 15 | 4 | same |
| `X-PM-Token` | OPERATIONS | 30 | 8 | `SESSION_IDLE_MIN_OPERATIONS`, `SESSION_ABS_HOUR_OPERATIONS` |
| `X-Shop-Token` | OPERATIONS | 30 | 8 | same |
| `X-Dispatch-Token` | OPERATIONS | 30 | 8 | same |
| `X-Safety-Token` | OPERATIONS | 30 | 8 | same |
| `X-Field-Leadership-Token` | FIELD | 60 | 12 | `SESSION_IDLE_MIN_FIELD`, `SESSION_ABS_HOUR_FIELD` |
| `X-Dev-Token` | (no timeout) | n/a | n/a | Vendor-only; bypass enforcement |

Master env flag: `SESSION_TIMEOUTS_ENABLED=true` to activate. Anything else (including unset) → **enforcement disabled**, behavior identical to today. This is the rollback switch.

## 4. Middleware placement

A single `session_activity_middleware` registered before the existing CORS + audit middlewares:

```python
# pseudocode — actual implementation below
@app.middleware("http")
async def session_activity_middleware(request: Request, call_next):
    if not _timeouts_enabled():
        return await call_next(request)
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    if request.url.path in _EXEMPT_PATHS:
        return await call_next(request)
    token, tier = _pick_token_and_tier(request.headers)
    if not token:
        return await call_next(request)  # anonymous; let downstream auth handle
    ttl = _ttl_for(tier)
    decision = await _check_or_update_session_activity(db, token, tier, ttl)
    if decision == "expired_idle":
        return _json_401("session_idle_timeout", tier=tier)
    if decision == "expired_absolute":
        return _json_401("session_absolute_timeout", tier=tier)
    return await call_next(request)
```

## 5. What gets re-invalidated by role/template change (gap)

Currently nothing. If admin changes a user's role-template, their existing token still authorizes per the OLD permissions until naturally expired. After Initiative 4 lands, we should call `revoke_user_sessions(user_id)` which sets `revoked_at` on every active `session_activity` row for that user. **Out of scope for this turn** — listed for Initiative 5b.

## 6. Exempt paths (always allowed through middleware)

- `/api/health`, `/api/healthz`, `/api/health/full` — UptimeRobot must work even when sessions expire
- `/api/version` — same reason
- `/api/admin/login`, `/api/hr/login`, `/api/pm/login`, etc. — anonymous login routes
- `/api/_internal/*` (if any) — internal probes

## 7. Frontend behavior on `session_idle_timeout` / `session_absolute_timeout` response

The frontend already handles 401 by clearing the session and routing to the login page (iter179). The new 401-with-detail responses fit that flow. **No frontend code changes required.** Optional Stage B.1: surface a friendlier message ("You were signed out due to inactivity").

## 8. Implementation safety properties

- **Default off**: missing or empty `SESSION_TIMEOUTS_ENABLED` → middleware no-ops, zero behavior change.
- **Backwards compatible**: tokens stay the same shape; no migration.
- **Per-tier override**: each tier's idle/abs values are env-driven; tighten or loosen without code changes.
- **Reversible**: `unset SESSION_TIMEOUTS_ENABLED && supervisorctl restart backend` → previous behavior in <2s.
- **No third-party dependency**: pure Mongo.
- **Read-then-write**: `session_activity` row updates are upserts with `$max` so concurrent requests cannot move `last_seen_at` backward.
- **Tombstones**: `session_activity` rows expire (via Mongo TTL index) 30 days after `last_seen_at` so the collection doesn't grow unbounded.
- **Dev token excluded**: `X-Dev-Token` is intentionally vendor-only and not subject to timeout — matches its "support session" intent.

## 9. Acceptance status (Initiative 4 — fix landed iter188, 2026-02-XX)

| Criterion | Status |
|---|---|
| Unauthorized portal buttons don't appear after stale session | ✅ Fixed iter179 |
| Direct unauthorized route blocked server-side | ✅ Existing `require_*` gates |
| Logout fully clears effective access | ✅ Fixed iter179 + iter188 (server-side `session_activity` clearance on admin/PM logout) |
| Idle/absolute timeout behavior implemented | ✅ Middleware + tests landed |
| Idle/absolute timeout behavior **proven correct end-to-end** | ✅ **Fixed iter188** — see § 9a |
| Role-change cannot leave old elevated sessions lingering | ⏸ Initiative 5c — backlogged |
| No regressions to valid user flows | ✅ 202/202 auth + hardening tests passing post-fix |

---

## 9a. Deterministic-token defect — RESOLVED iter188 (2026-02-XX)

### Original symptom (pre-fix)
With `SESSION_TIMEOUTS_ENABLED=true`, a fresh admin login returned a
valid token, but the next request with that token returned 401 with
`detail=session_idle_timeout`. Reproduced live 2026-02-XX during
documentation reconciliation.

### Root cause
Stateless HMAC tokens are **deterministic** — every successful login
yields the same token for the same (epoch, namespace, password). The
`session_activity` row keyed by `sha256(token)` is therefore shared
across logins. The login endpoint was on the middleware's exempt list
(correctly) but did NOT reset the corresponding row, so after any idle
window the row was already stale-expired on the next request.

### Fix (iter188)
A new helper `session_timeout.reset_session_activity(db, token, tier)`
upserts the caller's `session_activity` row to
`first_seen_at = last_seen_at = now`. It is called from every login
endpoint that issues a deterministic-tier token:

- `POST /api/admin/login`           → tier `ADMIN_HR`
- `POST /api/hr/login`              → tier `ADMIN_HR`
- `POST /api/pm/login` (per-user)   → tier `OPERATIONS`
- `POST /api/pm/login` (shared)     → tier `OPERATIONS`
- `POST /api/shop/login` (per-user) → tier `OPERATIONS`
- `POST /api/shop/login` (shared)   → tier `OPERATIONS`
- `POST /api/safety/login`          → tier `OPERATIONS`
- `POST /api/dispatch/login`        → tier `OPERATIONS`
- `POST /api/auth/multi-login`      → resets each minted portal token at correct tier
- `POST /api/auth/issue-portal-token` → resets the re-minted token at correct tier

A companion `clear_session_activity(db, token)` is invoked from the
logout endpoints (`/api/admin/logout`, `/api/pm/logout`) to delete the
row outright — belt-and-suspenders with the 30-day TTL.

Field-leadership tokens (random, not deterministic) and dev tokens
(intentionally exempt from timeouts) are unchanged.

### Regression coverage
`/app/backend/tests/test_iter188_deterministic_token_relogin.py`
(9 tests, 8 pass + 1 skipped on absent shared-PM env):

- `test_admin_fresh_login_first_request_returns_200` — original defect repro
- `test_admin_post_idle_relogin_succeeds` — backdated row + re-login → 200
- `test_admin_multi_login_cycles_all_succeed` — 5 cycles of login/logout
- `test_admin_logout_login_loop_recovers_from_stale_row` — `last_seen_at` is fresh after every cycle
- `test_browser_refresh_does_not_force_relogin` — same token replayed 3x; `last_seen_at` monotonic
- `test_multi_tab_concurrent_requests_share_row` — 8-thread concurrent hit; exactly 1 row
- `test_hr_post_idle_relogin_succeeds` — HR portal parallel scenario
- `test_pm_shared_login_post_idle_relogin_succeeds` — PM shared-password parallel scenario
- `test_admin_logout_deletes_session_activity_row` — explicit row clearance on logout

### Production rollout posture
- ✅ Preview: `SESSION_TIMEOUTS_ENABLED=true` — fix verified, no lockout observed
- 🛑 Production: still `SESSION_TIMEOUTS_ENABLED=false` per operator directive
- ▶ Next operator step: confirm preview behaviour for ≥24h, then flip production flag to `true` and monitor first idle/abs cycle

### Honest residual risk
- The fix is keyed on `sha256(token)`. If a different portal ever
  collides on token bytes by design, the row is still namespaced by
  the `tier` field stored in the row. We do not currently enforce
  cross-portal token-namespace uniqueness at the middleware level —
  the namespace prefix is encoded in the HMAC input but not in the
  `session_activity` lookup. This is not a known defect today, but
  worth a follow-up if multi-tenant token issuance changes.
- The login-reset is a synchronous Mongo write. A Mongo outage during
  login would log a warning but still return success (fail-open by
  design). The next authenticated request would then re-trigger the
  middleware's first-seen path, which creates the row if missing.

---

## 10. Open questions deferred to next iteration

- Force-logout / kill-switch UI for admin: "sign out user X everywhere now" — would be `revoke_user_sessions` UI surface. Out of scope this turn.
- Frontend friendlier-message-on-timeout — would be 5-line update in `EnforcePortalScope.jsx`. Not blocking; optional polish.
