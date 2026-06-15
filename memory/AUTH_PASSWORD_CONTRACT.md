# AUTH_PASSWORD_CONTRACT.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Date:** 2026-02-15
**Status:** CANONICAL — locked under regression tests.

This is the single source of truth for the MASCI / ForgedOps platform
password contract. Any future change requires a regression-test update
and a new closure ledger.

## 1. Password Hashing

| Aspect | Standard | Verified-in |
|--------|----------|-------------|
| Algorithm | **bcrypt** | All 7 user libraries |
| Work factor | **rounds = 12 (explicit)** | `pm_auth.hash_password`, `user_directory.hash_password`, `auth.hash_password` (pinned this track) |
| Salt | bcrypt-managed (per-hash, random) | bcrypt default |
| Storage | `password_hash` field (string, UTF-8 / ASCII) | all collections |
| Pepper | none (bcrypt salt sufficient) | — |
| API leakage | password_hash is NEVER returned by any public/admin API | `routes/admin_directory_k4.py`, `routes/auth_directory_routes.py`, all per-portal /me endpoints |

## 2. Password Minimum Length

| Surface | Minimum | Maximum | Enforced where |
|---------|---------|---------|----------------|
| Multi-login change-master | 10 | 200 | `auth_directory_routes.py` Pydantic |
| Auth.py change endpoints | 10 | 200 | `auth.py:127-144` |
| PM change-password | 6 | n/a | `pm_auth.py:39` |
| HR/Safety/Shop/Dispatch (via pm_auth) | 6 | n/a | imported |
| Recommended uniform minimum | **8** | 200 | — (currently 6 per-portal, 10 master) |

**Drift Note:** Per-portal endpoints accept 6-char minimum; master uses
10. Documented but not enforced as a single value because changing
existing user passwords is prohibited under PRODUCTION LOGIN
PROTECTION. Future track: AUTH-MIN-LENGTH-NORMALIZATION.

## 3. Temporary Password Contract

| Aspect | Standard | Source |
|--------|----------|--------|
| Generator | `secrets.choice` over alphabet (letters + digits, **excluding** ambiguous `0 O 1 l I`) | `pm_auth.generate_temp_password` |
| Length | **10** characters | default arg |
| Re-use | Each issuance is fresh — admin reset always mints a new pw | confirmed |
| Storage | bcrypt-hashed; admin sees plaintext **ONCE** in response | confirmed |
| Delivery | (a) `Show on screen` (b) `Email to user` via Resend (c) `Download welcome PDF` | per-portal admin endpoints |
| `must_change_password=true` | Set on every admin reset | confirmed |
| First-login flow | `/{portal}/login` returns `must_change_password=true` → frontend redirects to `/{portal}/change-password` | per-portal logic |
| Expiration | Token-bound (HMAC includes `password_hash[:16]` — changing pw invalidates) | confirmed |

## 4. HMAC Token Contract

| Aspect | Standard |
|--------|----------|
| Algorithm | HMAC-SHA256 |
| Secret | `ADMIN_HMAC_SECRET` (env, shared across all per-portal libs) |
| Epoch | `ADMIN_SESSION_EPOCH` — bumping invalidates every token in one shot |
| Token shape | `{user_id}.{HMAC}` for per-user portals; `{HMAC-of-password}` for legacy admin |
| HMAC input | `f"epoch={SESSION_EPOCH}|{role}:{password_hash[:16]}"` |
| Auto-invalidation | Changing password changes `password_hash[:16]` → all old tokens 401 immediately |
| Storage (client) | `localStorage` (default) or `sessionStorage` (Remember Me unchecked) under `masci.{portal}.token` |
| Header | `X-{Portal}-Token` (e.g. `X-PM-Token`, `X-Admin-Token`) |

## 5. Reset Token Contract

| Aspect | Standard |
|--------|----------|
| Algorithm | HMAC-SHA256 of `(user_id, password_hash[:16], expiry_ts)` |
| TTL | **30 minutes** |
| Single-use | Enforced via `password_hash[:16]` binding — once new password set, hash prefix changes, token signature no longer verifies |
| Email-enumeration safe | Forgot-password endpoints ALWAYS return HTTP 200 with generic message regardless of email existence |
| Verified in | `pm_auth.py:205`, `hr_users.py:227`, `safety_users.py:215`, `shop_users.py:227`, `dispatch_users.py:215` |

## 6. Failed Login & Lockout Contract

| Layer | Threshold | Window | Scope | Behavior |
|-------|-----------|--------|-------|----------|
| Server (per-IP) | `LOGIN_MAX_FAILS=10` | `LOGIN_LOCKOUT_SECONDS=900` (15 min) | per-IP | 429 with wait_s |
| MFA verify | 5 fails | 30 min | per-user | `locked_until` timestamp set |
| Per-account (forms login attack on same email) | **NOT IMPLEMENTED** | — | — | See AUTH_LOCKOUT_CERTIFICATION.md |

**Gap accepted:** Per-account lockout is a deferred enhancement. Per-IP
lockout + bcrypt cost-12 already make credential stuffing
prohibitively slow. Adding per-account lockout requires writes to
existing user documents which is restricted under PRODUCTION LOGIN
PROTECTION. Documented in `AUTH_LOCKOUT_CERTIFICATION.md`.

## 7. Email Template Standard

| Section | Standard |
|---------|----------|
| Sender | `MASCI Operations <no-reply@mascigc.com>` (Resend FROM_ADDRESS env) |
| Subject | `Your MASCI {Portal} login — temp password` |
| Body sections | (1) Welcome + portal name (2) Email + temp password (one-line bold) (3) Login link `https://mascidocs.com/{portal}/login` (4) "Change immediately on first login" instruction (5) Security warning: do NOT forward, do NOT share (6) Support contact |
| Welcome PDF | Attached to PM admin email-welcome flow; not currently universal |
| Language | English by default; ES rendered if recipient `language_preference=es` |

## 8. Audit Event Catalog

Every auth event MUST write to `db.audit_events` or `db.admin_audit`:

| Event Name | Triggered by | Required fields |
|------------|--------------|-----------------|
| `multi_login_success` | `POST /api/auth/multi-login` | actor, ip, portals_granted |
| `multi_login_failure` | failed login | ip, email_tried (truncated), reason |
| `portal_login_success` / `_failure` | per-portal login | actor, portal, ip |
| `password_change` | self-service | actor, portal |
| `password_reset_requested` | forgot-password | email_hash, ip (not email itself for enumeration safety) |
| `password_reset_completed` | reset-password | actor, ip |
| `admin_reset_password` | admin-issued reset | actor=admin, target user, delivery=email/screen/custom |
| `admin_impersonate_*` | admin "view as" | actor, target |
| `mfa_enroll` / `_verify` / `_disable` | MFA endpoints | actor |
| `account_lockout` | per-IP or per-MFA | ip or user, threshold_hit |

## 9. Session Behavior After Password Events

| Event | Effect on tokens |
|-------|------------------|
| Password change (self) | All old tokens for that user 401 immediately (HMAC reads new `password_hash[:16]`). Caller receives a fresh token in the response so they stay signed in. |
| Password reset (forgot flow) | All old tokens 401. User must log in again. |
| Admin-issued reset | All old tokens 401. Forces re-login. |
| `ADMIN_SESSION_EPOCH` bump | EVERY token across all portals 401 simultaneously. |
| Logout | Frontend clears `masci.*.token` from both `localStorage` and `sessionStorage`. Backend has no server-side session table to clear (tokens are stateless HMACs). |

## 10. Multi-Portal SSO Behavior

- `/api/auth/multi-login` returns ALL portal tokens the directory user
  is entitled to (e.g. super admin gets 8 tokens).
- Frontend `tokenStorage.js` fans them into `masci.{portal}.token`.
- Visiting `/{portal}/...` re-uses the stored portal token — no
  re-login required.
- A token's HMAC includes `password_hash[:16]`, so changing the master
  password rotates ALL portal tokens simultaneously without needing a
  multi-portal logout.

## 11. Break-Glass / Emergency Access

The following routes exist as documented emergency-only paths and
MUST remain audit-logged + manually-invoked-only:

| Route | When to use | Documented in |
|-------|-------------|----------------|
| `POST /api/admin/login` (legacy, body `{password: ADMIN_PASSWORD}`) | Master directory unreachable, full-platform recovery | test_credentials.md "Legacy Admin Console" |
| `POST /api/pm/login` body `{password: PM_PASSWORD}` no email | PM portal API-only office bypass | test_credentials.md "Legacy shared-password emergency bypass" |
| `POST /api/dev/login` | ForgedOps internal ops manual / snapshot access | test_credentials.md "Developer Portal" |

These are intentionally NOT reachable from human-facing UIs — they are
API-only and require knowledge of the env-var password. Audit events
fire on every use.

## 12. Production-Login-Protection Invariants

Under PRODUCTION LOGIN PROTECTION, this track guarantees:

1. ZERO existing password hashes were rewritten.
2. ZERO existing sessions were invalidated.
3. ZERO new env vars added (only existing ones documented).
4. ZERO Pydantic min_length defaults reduced (no weakening of
   existing validators).
5. ZERO routes deleted; legacy bypass paths preserved exactly.
6. Only ONE source-code edit: `auth.py::hash_password` pinned from
   `bcrypt.gensalt()` (default 12) to `bcrypt.gensalt(rounds=12)` —
   identical work factor, documentary only.

All other deliverables this track are documentation + regression
tests that LOCK the canonical behavior without changing it.
