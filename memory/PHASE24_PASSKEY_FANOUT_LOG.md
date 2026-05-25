# PHASE24_PASSKEY_FANOUT_LOG.md
## Phase 24 · Passkey / Device Sign-In Fan-Out to All Gated Portals
## iter430 · scope-only (execution next session)

---

## Current state (Admin pilot · iter422)

| Surface | Passkey-enabled |
|---|---|
| `/sign-in` (multi-portal master) | 🟢 backend ready · frontend prompt mounted on `/admin` |
| `/admin` post-sign-in `PasskeyEnrollPrompt` | 🟢 (Admin pilot proven · 11 enrolled passkeys) |
| All other portal sign-ins | 🔴 not yet |

## Target state after Phase 24 fan-out

| Surface | Passkey-enabled |
|---|---|
| `/sign-in` (multi-portal master) | 🟢 (unchanged) |
| `/admin` post-sign-in | 🟢 (unchanged) |
| Field Leadership portal post-sign-in | 🟢 NEW |
| Dispatch portal post-sign-in | 🟢 NEW |
| PM portal post-sign-in | 🟢 NEW |
| Shop portal post-sign-in | 🟢 NEW |
| Safety portal post-sign-in | 🟢 NEW |
| HR portal post-sign-in | 🟢 NEW |
| Governance portal post-sign-in | 🟢 NEW |
| **NOT enabled** | public Field Tile · Driver Shift QR · public forms · magic-link continuity |

---

## Why most of the work is already done

The iter422 pilot built it on standard `py_webauthn` with a clean abstraction:

- `routes/passkeys.py` — backend register/login/list/revoke (already accepts any portal token; just need to mount the prompt in more portal hubs)
- `lib/passkeys.js` — frontend WebAuthn helpers (browser-agnostic, no library dependency)
- `components/auth/PasskeyEnrollPrompt.jsx` — 5-gate calm prompt with EN/ES copy

**Net engineering: mount the existing `<PasskeyEnrollPrompt />` component in 7 portal hub pages.** Estimated ~1 session.

---

## Per-portal mount plan

| Portal hub file | Action |
|---|---|
| `pages/FieldLeadershipPortalHub.jsx` (or equivalent) | add `<PasskeyEnrollPrompt portalTokenKey="masci.fl.token" />` at top of hub |
| `pages/DispatchHub.jsx` | same |
| `pages/PMHub.jsx` (or equivalent) | same |
| `pages/ShopHub.jsx` | same |
| `pages/SafetyPortalHub.jsx` (or equivalent) | same |
| `pages/HRHub.jsx` (or equivalent) | same |
| `pages/GovernanceHub.jsx` (or equivalent) | same |
| `pages/AdminHub.jsx` | already has it |

Only diff per portal: which token to use (each portal has its own session token key in localStorage).

---

## Login-screen "Sign in with device" button

Each portal sign-in page gets a **second button** below the password form:

```
[ Sign in with device ]   (only renders when passkeySupported() && hasEnrolledOnThisDevice)
```

Tap → fires `signInWithPasskey()` from `lib/passkeys.js` → on success, fans out the portal-specific token and redirects to the portal hub.

If the user has never enrolled on this device, the button stays hidden. They sign in with password. AFTER successful password sign-in, the `<PasskeyEnrollPrompt>` offers enrollment (one-time, dismissible per device).

---

## Doctrine guardrails (held)

| Restraint | How enforced |
|---|---|
| Calm language only | "Sign in with device" not "WebAuthn", "FIDO", "biometric" |
| Dismissible | Gate 5 (localStorage flag) preserves dismissal per device |
| Once per device/user | Gate 4 (zero live passkeys) auto-hides after enrollment |
| No nagging | reload-time-only check · no in-session re-prompts |
| Password fallback ALWAYS available | passkey is additive · never replaces password path |
| MFA coexists | passkey + MFA TOTP both remain available for accounts that have MFA armed |
| EN/ES continuity | all strings already in `i18n.js` (iter422) |
| No public/driver impact | scope strictly to gated portals · NOT Field Tile, NOT Driver QR, NOT magic-links |
| No security dashboard | `/profile/devices` is a simple read-only + revoke surface, NOT an "Identity Center" |

---

## Device management surface (NEW · low-risk)

Route: `/profile/devices`

Layout:
- Header: "Devices that can sign you in" / "Dispositivos que pueden iniciar sesión por usted"
- List of enrolled passkeys for the current directory user:
  - Friendly name (e.g., "Jaymn's iPhone")
  - Created date
  - Last used date
  - **[Remove]** button
- Empty state: "No devices enrolled yet. Sign in normally on a phone or laptop and you'll be offered the option to enable device sign-in."

Backend endpoints already exist:
- `GET /api/passkeys/list`
- `DELETE /api/passkeys/{credential_id}`

Frontend mount: add route in `App.js` · single new page file `pages/ProfileDevices.jsx` (~150 LOC).

---

## Testing plan

| Test | Asserts |
|---|---|
| `test_iter431_fl_portal_login_password_path` | password-only sign-in still works on FL portal |
| `test_iter431_dispatch_portal_login_password_path` | same for Dispatch |
| `test_iter431_pm_portal_login_password_path` | same for PM |
| `test_iter431_shop_portal_login_password_path` | same for Shop |
| `test_iter431_safety_portal_login_password_path` | same for Safety |
| `test_iter431_hr_portal_login_password_path` | same for HR |
| `test_iter431_governance_portal_login_password_path` | same for Governance |
| `test_iter431_passkey_register_options_works_for_each_portal_token` | server returns valid publicKey options regardless of which portal-token header is used |
| `test_iter431_profile_devices_lists_user_passkeys` | GET `/profile/devices` route returns enrolled list |
| `test_iter431_profile_devices_revoke_disables_credential` | DELETE works · revoked credential cannot login |
| `test_iter431_admin_pilot_passkey_still_works` | regression-guard for iter422 |

---

## Out of scope (explicit NOT-doing)

- ❌ Driver-side passkeys (Driver Shift QR is intentionally simpler — no auth at all)
- ❌ Public Field Tile (no auth surface there to harden)
- ❌ Public forms (anonymous-friendly · adding passkeys would block legitimate field crew submissions)
- ❌ Magic-link driver-side continuity (already its own auth pattern · doesn't need passkeys)
- ❌ Identity-center dashboard (operator restraint doctrine: no identity-management UI)
- ❌ Audit log of who-enrolled-when (existing iter422 ledger covers it · no UI needed)

---

## Estimated effort

- Engineering time: **1 focused session**
- Files touched: ~12 (7 portal hubs + 7 sign-in pages + 1 `/profile/devices` page + 1 router file + tests)
- Risk: **LOW** (each portal gets the exact same proven Admin pilot pattern)
- Reverts cleanly: any portal can be feature-flagged off via `PASSKEY_PORTALS` env var (additive enable list)

---

## Status

📋 **PLAN COMPLETE · execution awaits operator green-light**

---

End of Phase 24 Passkey Fan-Out Log.
