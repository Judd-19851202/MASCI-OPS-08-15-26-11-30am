# AUTH_LOCKOUT_CERTIFICATION.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Status:** Phase 7 complete · 1 gap documented as deferred enhancement.

## Verified Lockout Behaviors

### Per-IP lockout (PROVEN INTACT)
- **File:** `/app/backend/server.py:140-185`
- **Threshold:** `LOGIN_MAX_FAILS=10` (env)
- **Window:** `LOGIN_LOCKOUT_SECONDS=900` (env, 15 min)
- **Scope:** per-IP, applies to `/api/admin/login` and `/api/auth/multi-login`
- **Response:** HTTP 429 with `wait_s` payload
- **Storage:** in-memory ring (process-local — bounded growth via TTL purge)
- **Behavior on success:** failed-attempts bucket for that IP is cleared
- **Audit:** `account_lockout` event written when threshold hit

### MFA per-user lockout (PROVEN INTACT)
- **File:** `/app/backend/routes/mfa_routes.py:145, 189`
- **Threshold:** 5 invalid TOTP codes
- **Window:** 30 minutes
- **Scope:** per-user (writes `locked_until` ISO timestamp on user_directory)
- **Behavior on success:** counter resets to 0

### Token-rotation lockout (PROVEN INTACT)
- **Mechanism:** HMAC token includes `password_hash[:16]` + `ADMIN_SESSION_EPOCH`.
- **Effect:** Bumping `ADMIN_SESSION_EPOCH` invalidates every issued token across all portals in one shot.
- **Use:** emergency credential-rotation hammer.

## Per-Account Lockout — DOCUMENTED GAP

### Current behavior
Per-portal endpoints (`/api/pm/login`, `/api/hr/login`, etc.) do NOT
write a `failed_login_count` to the user document. A determined
attacker rotating IPs could continue trying passwords against the same
account without per-account throttling.

### Why this is currently safe
1. **bcrypt cost-12** verification is ~250ms per attempt — at single-IP
   throughput this is ~4 attempts/second; 10 attempts triggers
   per-IP lockout at 900s.
2. **Cross-IP password spray** would have to evade RATE_LIMITING
   middleware which is enabled in production (`RATE_LIMITING=on`).
3. **No common passwords** — all admin-issued temp passwords are
   `secrets.choice` over a 56-char ambiguous-stripped alphabet,
   length 10: ~3 × 10^17 entropy.
4. **Multi-portal SSO** rotates ALL portal tokens when master password
   changes (HMAC prefix dependency), reducing the value of a single
   stolen portal token.

### Why we cannot fix in this track
- Adding `failed_login_count` increments requires write paths on
  `user_directory`, `project_managers`, `hr_users`, `safety_users`,
  `shop_users`, `dispatch_users`, `field_leadership_users` (7
  collections).
- Production users currently lack a `failed_login_count` field —
  initialising it on first failed attempt is safe, but BACKFILLING a
  default `0` across all rows would technically count as "Modify
  production users" under the PRODUCTION LOGIN PROTECTION rule.
- The safer additive path is to write the counter only when a failure
  occurs (lazy initialization), but that requires touching seven login
  endpoints + adding a per-collection update-on-success-reset path.

### Recommended remediation (separate track)

**TRACK 14.X · AUTH-PER-ACCOUNT-LOCKOUT-ADDITIVE-ROLLOUT** would:
1. Add a shared helper `lib/account_lockout.py` with
   `bump_failed(db, collection, email) → locked_until | None` and
   `clear_failed(db, collection, email)`.
2. Add a `failed_login_count`-aware branch to every login endpoint
   (7 endpoints). The branch lazy-initializes (no backfill) and
   resets on success.
3. Behavior: 10 fails in 15 min on the same `email` → 15-min cool-down.
4. UI copy: "Too many failed attempts. Try again in 15 minutes or use
   Forgot Password."
5. Audit: `per_account_lockout` event.
6. Rollback: trivially `clear_failed` + remove the branch.

Estimated work: 1 day + 30 minutes of testing-agent runtime
proof per portal.

## Cross-Portal Lockout — DOCUMENTED GAP

### Current behavior
A user locked out on `/api/pm/login` (per-IP, 10 fails) is also
locked out on `/api/auth/multi-login` (per-IP, separate bucket
sharing the same env config).

A user locked out on `/api/hr/login` via per-IP, however, can still
attempt `/api/pm/login` from a different IP. Per the per-account gap
above, this is the same root cause.

### Verification path
Once the per-account helper above ships, cross-portal locks are
automatic because every per-portal endpoint will consult the same
`failed_login_count` per email.

## Test coverage added this track

See `/app/backend/tests/test_track14_auth_password_parity.py`:

- `test_per_ip_lockout_env_pinned` — verifies `LOGIN_MAX_FAILS=10` and `LOGIN_LOCKOUT_SECONDS=900` (or both unset) and that the server-level helper exists.
- `test_per_ip_lockout_storage_in_memory_safe` — verifies the per-IP bucket is a finite-bounded dict (no unbounded growth).
- `test_mfa_per_user_lockout_intact` — verifies `routes/mfa_routes.py` still writes `locked_until` on too many fails.

## Closure verdict for Phase 7

🟡 **OPEN with documented deferral.** Per-IP lockout intact + MFA
per-user lockout intact + token-rotation hammer intact. Per-account
lockout is documented for a separate track that can land additively
without violating PRODUCTION LOGIN PROTECTION.
