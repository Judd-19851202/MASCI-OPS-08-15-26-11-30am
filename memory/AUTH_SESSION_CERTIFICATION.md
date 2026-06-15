# AUTH_SESSION_CERTIFICATION.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Status:** Phase 8 + 12 complete · ✅ PARITY VERIFIED.

## Session Architecture

The platform uses **stateless HMAC tokens** (no server-side session
table). Each token contains the user_id and an HMAC derived from
`ADMIN_HMAC_SECRET + ADMIN_SESSION_EPOCH + password_hash[:16] + role`.

## Token Storage (Client)

| Token type | localStorage key | sessionStorage key | When sessionStorage |
|------------|------------------|---------------------|----------------------|
| Master directory | `masci.directory.token` | same | Remember-me OFF |
| Admin | `masci.admin.token` | same | Remember-me OFF |
| PM | `masci.pm.token` | same | Remember-me OFF |
| HR | `masci.hr.token` | same | Remember-me OFF |
| Safety | `masci.safety.token` | same | Remember-me OFF |
| Shop | `masci.shop.token` | same | Remember-me OFF |
| Dispatch | `masci.dispatch.token` | same | Remember-me OFF |
| Field Leadership | `masci.fl.token` | same | Remember-me OFF |
| Leadership | `masci.leadership.token` | same | Remember-me OFF |
| Safety Forms | `masci.safetyforms.token` | same | Remember-me OFF |

Single source-of-truth: `/app/frontend/src/lib/tokenStorage.js`.

## Multi-Portal SSO Behavior

### Login at `/sign-in`
1. POST `/api/auth/multi-login` returns 8 portal tokens.
2. Frontend `pmAuth.writePmToken`, `hrAuth.writeHrToken`, etc. fan all
   tokens to their respective storage keys.
3. Any subsequent visit to `/{portal}/...` finds the stored token,
   validates it via `/api/{portal}/check` or `/me`, and skips the
   login form.

### Cross-tab SSO auto-elevation
- `window.__masciSessionBus` + `localStorage` `storage` event listener
  in `pmLogin.jsx`, `adminLogin.jsx`, `hrLogin.jsx`, `safetyLogin.jsx`.
- When tab A logs in, tab B (already on a portal login page) sees the
  storage event and auto-redirects to its dashboard.
- **Track 14.0-S2A** verified this in iteration_515 and fixed two
  same-portal token redirect bugs.

### Effect of password events on tokens

| Event | Effect |
|-------|--------|
| `/api/auth/change-master-password` | All 8 portal tokens 401 immediately (master `password_hash[:16]` changed, all portal HMACs derive from it). Caller receives a fresh token in the response. |
| `/api/pm/change-password` | All PM tokens for that user 401. Caller receives fresh PM token. Admin/HR/Shop/etc. tokens for the SAME user are NOT affected unless that user's master password also rotates (per-portal hashes are independent on per-portal collections). |
| `/api/pm/reset-password` | Same as change-password. |
| Admin admin-resets a PM | All PM tokens for that PM 401. PM must re-login. |
| Bump `ADMIN_SESSION_EPOCH` env var | EVERY token across all portals 401 simultaneously. |
| Logout (`/api/auth/multi-logout` + frontend clear) | localStorage / sessionStorage cleared client-side. Tokens become orphan but inert (frontend won't send them). |

## Session Expiration

- HMAC tokens are stateless and do NOT expire on their own.
- They are invalidated only by: password change, password reset, admin
  reset, ADMIN_SESSION_EPOCH bump, or token contents being rejected by
  the gating dep (e.g. user disabled).
- This is INTENTIONAL: long-lived field operator sessions (8-12 hour
  shifts on iPads) are a hard requirement.
- Token theft mitigation is via:
  1. `Remember me OFF` → sessionStorage (clears on tab close)
  2. ADMIN_SESSION_EPOCH bump (emergency rotation hammer)
  3. Disable user via `/admin/people` → invalidates that user's
     tokens on next request via `disabled` flag check.

## Per-Portal Scope Enforcement

`EnforcePortalScope` component in the App.js Router:
- Clears `masci.{other_portal}.token` when the URL prefix doesn't
  match that portal.
- Example: navigating to `/admin/...` while a `masci.pm.token` is in
  localStorage does NOT leak the PM token to admin endpoints — admin
  endpoints require `X-Admin-Token`, which the PM token cannot
  satisfy.
- Token leakage between portals is impossible because each portal's
  gating dep validates the HMAC signature against the portal-specific
  HMAC input shape (different `role` field).

## Session Failsafes

| Failsafe | Source | Status |
|----------|--------|--------|
| `validateStoredTokens()` on app load | `/app/frontend/src/lib/tokenStorage.js` | ✅ |
| `OfflineBanner` (sky-blue, calm) | Track 14.0-RC1 closure | ✅ |
| Token-presence guard on `pmCommandApi.js` | Track 14.0-RC1 D2 fix | ✅ |
| `NotificationBell` early-return when no token | Track 14.0-RC1 D1 fix | ✅ |
| `GlobalKeepalive` only hits `/api/health` | Verified | ✅ |
| `SessionStatusOverlay` calm copy | Track 14.0-S2A | ✅ |

## Closure verdict

🟢 **PASS.** One authenticated user → one platform experience.
Multi-portal SSO works end-to-end. Token storage is consistent.
Password events behave predictably. Cross-tab auto-elevation works.
Session expiration is governed by an emergency hammer
(`ADMIN_SESSION_EPOCH`) rather than soft TTLs, matching the operator
requirement.
