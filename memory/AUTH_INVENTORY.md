# AUTH_INVENTORY.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Date:** 2026-02-15
**Status:** Phase 1 complete · read-only audit

## Backend Auth/Password Endpoints (canonical inventory)

### Master / Multi-Portal
| Endpoint | Method | File | Purpose |
|----------|--------|------|---------|
| `/api/auth/multi-login` | POST | `routes/auth_directory_routes.py:220` | Unified email+password login. Returns `session_token` + 8 `portal_tokens` map. Single source of truth for all SSO. |
| `/api/auth/me-directory` | GET | `routes/auth_directory_routes.py:320` | Returns the signed-in directory user. |
| `/api/auth/issue-portal-token` | POST | `routes/auth_directory_routes.py:327` | Mint a fresh portal token from a valid directory session. |
| `/api/auth/change-master-password` | POST | `routes/auth_directory_routes.py:390` | Self-service password change for directory users. |
| `/api/auth/multi-logout` | POST | (in auth_directory_routes.py) | Revoke session + portal tokens. |
| `/api/auth/mfa/verify-login` | POST | `routes/mfa_routes.py:255` | MFA second-factor verification. |

### Per-Portal Login (legacy + per-user)
| Portal | Login | Forgot | Reset | Change | Admin-Reset |
|--------|-------|--------|-------|--------|-------------|
| Admin (legacy) | `POST /api/admin/login` (`auth.py`) | n/a | n/a | n/a | n/a |
| PM | `POST /api/pm/login` (`pm_routes.py:321`) | `POST /api/pm/forgot-password` (446) | `POST /api/pm/reset-password` (543) | `POST /api/pm/change-password` (581) | `POST /api/admin/project-managers/{id}/set-password` (`pm_admin.py:190`) + `/email-welcome` |
| HR | `POST /api/hr/login` (`hr_portal.py:142`) | `POST /api/hr/forgot-password` (223) | `POST /api/hr/reset/{token}` (259) | `POST /api/hr/change-password` (209) | `POST /api/admin/hr-users/{id}/reset-password` (1534) |
| Safety | `POST /api/safety-portal/login` (`routes/safety_portal/auth_users.py`) | `/safety-portal/forgot-password` | `/safety-portal/reset/{token}` | `/safety-portal/change-password` | Admin reset endpoint in `routes/safety_portal/admin_users.py` |
| Shop | `POST /api/shop/login` | `/api/shop/forgot-password` | `/api/shop/reset-password` | `/api/shop/change-password` | `POST /api/admin/shop-users/{id}/set-password` + `/email-welcome` |
| Dispatch | `POST /api/dispatch/login` (`dispatch_portal_auth.py:153`) | `/api/dispatch/forgot-password` (228) | `/api/dispatch/reset-password` (237) | `/api/dispatch/change-password` (215) | `POST /api/admin/dispatch-users/{id}/reset-password` (276) + `/impersonate` (298) |
| Field Leadership | `POST /api/field-leadership/portal/login` (`field_leadership_portal.py:162`) | `/portal/forgot-password` (284) | `/portal/reset/{token}` (329) | `/portal/change-password` (268) | `POST /api/admin/field-leadership-users/{id}/reset-password` |
| Safety Forms (password-gated) | `POST /api/safety-forms/login` (`safety_forms.py:958`) | n/a (shared password) | n/a | n/a | env `SAFETY_FORMS_PASSWORD` |
| Dev (internal) | `POST /api/dev/login` | n/a | n/a | n/a | env `DEV_PASSWORD` |
| Leadership (legacy) | `POST /api/leadership/login` (`field_leadership.py:334`) | n/a (shared password) | n/a | n/a | env `LEADERSHIP_PASSWORD` |

### Passkey/WebAuthn (additive)
| Endpoint | File |
|----------|------|
| `POST /api/passkeys/login/options` | `routes/passkeys.py:343` |
| `POST /api/passkeys/login/verify` | `routes/passkeys.py:395` |

## Frontend Auth Screens

| Page | Path | Login | Forgot | Reset | Change |
|------|------|-------|--------|-------|--------|
| Sign-In (master) | `/sign-in` | ✅ unified | n/a | n/a | n/a |
| Admin | `/admin/login` | `AdminLogin.jsx` | n/a | n/a | n/a |
| PM | `/pm/login` | `PmLogin.jsx` | inline link | `PmResetPassword.jsx` | `PmChangePassword.jsx` |
| HR | `/hr/login` | `HrLogin.jsx` | `HrForgotPassword.jsx` | `HrResetPassword.jsx` | `HrChangePassword.jsx` |
| Safety | `/safety-portal/login` | `SafetyLogin.jsx` | `SafetyForgotPassword.jsx` | `SafetyResetPassword.jsx` | `SafetyChangePassword.jsx` |
| Shop | `/shop/login` | `ShopLogin.jsx` | inline link | `ShopResetPassword.jsx` | `ShopChangePassword.jsx` |
| Dispatch | `/dispatch-portal/login` | `DispatchLogin.jsx` | `DispatchForgotPassword.jsx` | `DispatchResetPassword.jsx` | `DispatchChangePassword.jsx` |
| Field Leadership | `/field-leadership/portal/login` | `FieldLeadershipPortalLogin.jsx` | inline | per-token reset | `FieldLeadershipPortalChangePassword.jsx` |
| Leadership (legacy) | `/leadership` | `LeadershipLogin.jsx` | n/a | n/a | n/a |
| Safety Forms | `/safety/forms/login` | `SafetyFormsLogin.jsx` | n/a | n/a | n/a |
| Dev | `/dev/login` | `DevLogin.jsx` | n/a | n/a | n/a |

Shared widgets:
- `AdminPasswordConfirm.jsx` — re-authenticate before destructive admin actions.
- `FormPasswordGate.jsx` — public form password gate.
- `PasswordInput.jsx` — shared input with show/hide.
- `PortalLoginShell.jsx` — shared login chrome.
- `PortalLoginHelp.jsx` — shared help text.

## Canonical Helper Inventory

| Module | hash_password | verify_password | generate_temp_password | make_*_token | make_*_reset_token |
|--------|---------------|-----------------|------------------------|--------------|---------------------|
| `pm_auth.py` | bcrypt rounds=12 | bcrypt.checkpw | 10 chars, no ambiguous | hash[:16]-bound | 30-min HMAC |
| `user_directory.py` | bcrypt rounds=12 | bcrypt.checkpw | n/a (directory token only) | n/a | n/a |
| `hr_users.py` | **imports from pm_auth** | imports | imports | hr-prefixed | 30-min HMAC |
| `safety_users.py` | **imports from pm_auth** | imports | imports | safety-prefixed | 30-min HMAC |
| `shop_users.py` | **imports from pm_auth** | imports | imports | shop-prefixed | 30-min HMAC |
| `dispatch_users.py` | **imports from pm_auth** | imports | imports | dispatch-prefixed | 30-min HMAC |
| `auth.py` (legacy admin) | bcrypt rounds=12 **(pinned this track)** | bcrypt.checkpw | n/a | HMAC of `ADMIN_PASSWORD` | n/a |
| `mfa.py` | bcrypt.gensalt() | bcrypt.checkpw | n/a (TOTP codes) | n/a | n/a |

## Lockout & Rate Limit Inventory

| Layer | Mechanism | Threshold | Window | Scope | Source |
|-------|-----------|-----------|--------|-------|--------|
| App-wide (server.py) | In-memory per-IP attempts on `/api/admin/login` and `/api/auth/multi-login` | `LOGIN_MAX_FAILS=10` (env) | `LOGIN_LOCKOUT_SECONDS=900` (env, 15min) | per-IP | `server.py:140-185` |
| Per-account | NOT IMPLEMENTED at write time — see AUTH_LOCKOUT_CERTIFICATION.md | — | — | — | gap |
| MFA | Per-user failed-code tracking with `locked_until` field | per-user | per-user | per-user | `mfa_routes.py:145,189` |

## Env Var Inventory (auth-relevant)

| Var | Default | Effect |
|-----|---------|--------|
| `ADMIN_PASSWORD` | empty | Legacy break-glass admin password. Empty disables admin gate. |
| `ADMIN_HMAC_SECRET` | random per-process if unset | HMAC secret for all per-portal tokens (PM/HR/Safety/Shop/Dispatch/FL). |
| `ADMIN_SESSION_EPOCH` | "1" | Bump to invalidate every issued token (admin/PM/HR/Safety/Shop/Dispatch/FL). |
| `SUPER_ADMIN_EMAIL` | `jaymn.judd@mascigc.com` | Bootstrap admin email. |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | `Maddix123!` | Initial password; rotated to `user_directory.password_hash` after first login. |
| `PM_PASSWORD` | `Happy123!` | Legacy shared PM password break-glass. |
| `PM_SHARED_LOGIN_ENABLED` | true | Whether legacy PM bypass is on. |
| `SHOP_PASSWORD` | `Nothappy123!` | Legacy shared shop break-glass. |
| `SAFETY_FORMS_PASSWORD` | `1982` | Public safety forms gate. |
| `LEADERSHIP_PASSWORD` | `MASCIGC` | Leadership shared password. |
| `DEV_PASSWORD` | `Maddix8530!` | Internal dev portal. |
| `LOGIN_MAX_FAILS` | 10 | Per-IP attempts before lockout. |
| `LOGIN_LOCKOUT_SECONDS` | 900 | Lockout duration. |
| `RATE_LIMITING` | off (preview) / on (prod) | Global rate-limit toggle. |
| `MFA_ENCRYPTION_KEY` | required for prod | Fernet key for TOTP secret encryption. |
