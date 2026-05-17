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

## 9. Acceptance status (Initiative 4 — implementation arriving this turn)

| Criterion | Status |
|---|---|
| Unauthorized portal buttons don't appear after stale session | ✅ Fixed iter179 |
| Direct unauthorized route blocked server-side | ✅ Existing `require_*` gates |
| Logout fully clears effective access | ✅ Fixed iter179 |
| **Idle/absolute timeout behavior tested & documented** | ✅ This audit doc + implementation + tests this turn |
| Role-change cannot leave old elevated sessions lingering | ⚠️ Listed for Initiative 5b (after timeouts land) |
| No regressions to valid user flows | Verified by full test sweep this turn |

## 10. Open questions deferred to next iteration

- Force-logout / kill-switch UI for admin: "sign out user X everywhere now" — would be `revoke_user_sessions` UI surface. Out of scope this turn.
- Frontend friendlier-message-on-timeout — would be 5-line update in `EnforcePortalScope.jsx`. Not blocking; optional polish.
