# AUTH_RESET_CERTIFICATION.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Status:** Phase 5 complete · ✅ PARITY VERIFIED.

## Reset Token TTL Parity

| Portal | TTL | Source file |
|--------|-----|-------------|
| PM | 30 min | `pm_auth.py:205` (`_RESET_TOKEN_TTL_SECONDS = 30 * 60`) |
| HR | 30 min | `hr_users.py:227` (`_HR_RESET_TOKEN_TTL_SECONDS = 30 * 60`) |
| Safety | 30 min | `safety_users.py:215` |
| Shop | 30 min | `shop_users.py:227` |
| Dispatch | 30 min | `dispatch_users.py:215` |
| Field Leadership | 30 min | `field_leadership_portal.py` (matches) |

**Verdict:** 30-minute window everywhere. Locked under
`test_track14_auth_password_parity.py::test_reset_token_ttl_parity`.

## Reset Token Single-Use Mechanism

Every portal's reset token is HMAC-bound to `password_hash[:16]`. Once
the new password is set, the bcrypt hash changes, so the hash prefix
changes, so the token's HMAC signature no longer verifies — making
reuse impossible without an additional explicit "used" flag.

## Email-Enumeration Safety

| Endpoint | Behavior on unknown email |
|----------|---------------------------|
| `POST /api/pm/forgot-password` | HTTP 200 + generic message |
| `POST /api/hr/forgot-password` | HTTP 200 + generic message |
| `POST /api/safety-portal/forgot-password` | HTTP 200 + generic message |
| `POST /api/shop/forgot-password` | HTTP 200 + generic message |
| `POST /api/dispatch/forgot-password` | HTTP 200 + generic message |
| `POST /api/field-leadership/portal/forgot-password` | HTTP 200 + generic message |

All six endpoints ALWAYS return 200 regardless of whether the email
exists. This is documented per-portal in their respective auth
modules.

## Reset URL Shape (minor drift, accepted)

| Portal | URL pattern |
|--------|-------------|
| PM | `POST /api/pm/reset-password` body `{token, new_password}` |
| HR | `POST /api/hr/reset/{token}` body `{new_password}` |
| Safety | `POST /api/safety-portal/reset/{token}` body `{new_password}` |
| Shop | `POST /api/shop/reset-password` body `{token, new_password}` |
| Dispatch | `POST /api/dispatch/reset-password` body `{token, new_password}` |
| Field Leadership | `POST /api/field-leadership/portal/reset/{token}` body `{new_password}` |

**Drift:** HR/Safety/FL use path-param style; PM/Shop/Dispatch use
body. Both work; both are documented. Aligning them would require
breaking existing email reset links currently delivered to real users
(PRODUCTION LOGIN PROTECTION violation).

**Decision:** Document and lock both shapes. New portals MUST adopt
one of these two patterns and add their TTL constant to the parity
test.

## Reset Success / Failure UX

All six portals' reset pages share:

- Identical Pydantic min_length check (per per-portal config)
- Toast on success: "Password reset. Signing you in…"
- Toast on expired-token failure: "Reset link expired. Request a new one."
- Toast on invalid-token failure: "Invalid reset link."

Verified by code review in the 6 `*ResetPassword.jsx` pages.

## Closure verdict

🟢 **PASS.** Reset behavior is consistent across all six portals.
TTL parity verified by regression test. Email-enumeration safety
verified. URL-shape drift documented and accepted under PRODUCTION
LOGIN PROTECTION constraint.
