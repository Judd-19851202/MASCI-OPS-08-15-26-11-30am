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
| Idle/absolute timeout behavior implemented | ✅ Middleware + tests landed |
| Idle/absolute timeout behavior **proven correct end-to-end** | ⚠️ **GAP — see § 9a below** |
| Role-change cannot leave old elevated sessions lingering | ⏸ Listed for Initiative 5c (after deterministic-token defect resolved) |
| No regressions to valid user flows | ⚠️ See § 9a — **regression observed in preview** |

---

## 9a. Operational defect discovered during 2026-02-XX reconciliation pass

**Severity: HIGH (preview), HIGH-if-promoted-to-production**

### Symptom
With `SESSION_TIMEOUTS_ENABLED=true` in the preview environment, a
fresh admin login (`POST /api/admin/login`) returns a valid token, but
the **very next request** with that token (e.g. `GET /api/admin/check`)
returns 401 with `detail=session_idle_timeout`.

Reproduced 2026-02-XX:

```
POST /api/admin/login          → 200, token returned (64-char HMAC)
GET  /api/admin/check (same)   → 401 {"detail":"session_idle_timeout",
                                       "tier":"ADMIN_HR"}
```

The `session_activity` row for the hashed token shows:
- `first_seen_at`: ~hour earlier (from a prior login that used the same
  deterministic token)
- `last_seen_at`: ~hour earlier (also stale)

### Root cause
Stateless HMAC tokens are **deterministic** —
`HMAC(secret, "epoch=<E>|admin:" + password)` produces the same token
on every successful login. The session_activity row is keyed by
`sha256(token)`, which is therefore identical across logins.

The login endpoint is on the middleware's exempt list (correctly — a
login request itself shouldn't be evaluated against idle/abs limits).
But the login endpoint **does not reset** the corresponding
`session_activity` row. So after any user has been idle longer than
their tier's idle limit, every future login is immediately rejected by
the middleware as `session_idle_timeout` against the stale
`last_seen_at`.

This affects all deterministic-token portals: Admin, PM (shared
password mode), and any HR/Shop/Dispatch/Safety user whose token is
re-issued identically.

### Why tests did not catch this
- `test_iter186b_session_timeout_middleware.py` tests the middleware
  in isolation with synthetic tokens and a fresh Mongo state per test.
- `test_iter187_admin_hardening_5b.py` calls real admin endpoints with
  a real login — and **3 tests are currently failing in preview**
  (2026-02-XX) because of exactly this defect. The handoff summary's
  claim of "192/192 passing" predates the activation of
  `SESSION_TIMEOUTS_ENABLED=true` in preview.

### Operational impact
- **Preview environment:** an admin/HR user idle >15 minutes (or
  PM/Shop/Dispatch idle >30 min) cannot log back in. Effectively
  locks them out until their tier's absolute window also expires —
  at which point the row would still report `expired_absolute`.
  Only ageing past the **TTL index** (30 days) lets them back in.
- **Production:** `SESSION_TIMEOUTS_ENABLED` is currently unset in
  production. **Do NOT flip it on without the fix below.** Doing so
  would cascade-lock every existing logged-in operator the moment
  their tier's idle window elapsed.

### Recommended fix (NOT applied this turn — operator hold per
"documentation reconciliation only" mandate)
The login endpoints (`/api/admin/login`, `/api/hr/login`,
`/api/pm/login`, `/api/shop/login`, `/api/dispatch/login`,
`/api/safety/login`) must, on successful authentication, reset the
caller's `session_activity` row:

```python
# pseudocode
await db.session_activity.update_one(
    {"token_hash": sha256(token).hexdigest()},
    {"$set": {
        "token_hash": ..., "tier": ...,
        "first_seen_at": now, "last_seen_at": now,
    }},
    upsert=True,
)
```

This makes login a deliberate "session reset" event — independent of
whether the token was previously seen.

A test must accompany the fix:

```
1. login → token A (deterministic)
2. simulate idle past tier limit (force-update session_activity to old timestamp)
3. login again → same token A
4. authenticated request → 200, not 401
```

### Workaround until fixed
Set `SESSION_TIMEOUTS_ENABLED=false` in `/app/backend/.env` and
restart backend. This is the documented rollback (§ 8 above). The
flag should remain OFF in production until the login-reset fix lands
and is verified.

### Triage classification
This is the kind of defect that only surfaces under live use — exactly
what end-to-end verification by the operator was supposed to catch.
It is honestly a hardening-initiative regression, not a hardening
success. The doc has been corrected accordingly.

## 10. Open questions deferred to next iteration

- Force-logout / kill-switch UI for admin: "sign out user X everywhere now" — would be `revoke_user_sessions` UI surface. Out of scope this turn.
- Frontend friendlier-message-on-timeout — would be 5-line update in `EnforcePortalScope.jsx`. Not blocking; optional polish.
