# PHASE 28.2 · Passkey Fan-Out Audit
## iter430 · 2026-05-25

## State after this phase
- `<PasskeyEnrollPrompt />` mounted on every gated portal hub:
  AdminHub, DispatchHub, FieldLeadershipHub, HrHub, PmHub, ShopHub,
  SafetyHub. Mounted once per page · self-gates (hidden if
  unsupported / already enrolled / dismissed) · NEVER nags.
- Public/driver flows EXCLUDED on purpose:
  - `/driver/*` magic-link forms
  - QR-code public tile surfaces
  - vendor/public surfaces
- Device management surface NOW LIVE: `/admin/profile` →
  "Your devices" section with read-only list + per-device "Remove".
  No security dashboard · no geo tracking · no fingerprinting.

## Component contract
- Lives at `/app/frontend/src/components/auth/PasskeyEnrollPrompt.jsx`.
- Operational language ONLY:
  - "Enable faster sign-in on this device?"
  - "Use Face ID / Touch ID / Windows Hello next time."
- Does NOT use the terms: FIDO, credential, biometric identity,
  authenticator, public-key, attestation.

## Real-device verification (operator-owned · see `PHASE28_2_REAL_DEVICE_VALIDATION.md`)
- ☐ iPhone Safari · enroll + sign-in + remove
- ☐ iPad Safari · enroll + sign-in + remove
- ☐ Android Chrome · enroll + sign-in + remove
- ☐ Windows Hello (Chrome) · enroll + sign-in + remove
- ☐ Windows Hello (Edge) · enroll + sign-in + remove
- ☐ Mac Touch ID · enroll + sign-in + remove
- ☐ Graceful fallback when unsupported · prompt stays hidden
- ☐ Password flow still works alongside passkeys (no MFA regression)

## What was intentionally NOT built
- ❌ Per-device geo/IP map
- ❌ "Last login" device feed beyond the existing `last_used_at`
- ❌ Cross-portal device sync UI (passkeys per directory user
  already span portals via `_mint_all_portal_tokens` in
  `_mint_multi_login_response_for_passkey`)
- ❌ Push notification on new device enrollment
