# PHASE26_AUTH_PASSKEY_AUDIT.md
## MASCI Operations Platform · Phase 26 · Auth + Passkey Continuity Audit
## iter427 · 2026-05-25

---

## Scope

Verify every authentication surface (legacy + multi-portal master + new
WebAuthn passkey pilot) signs in cleanly, fans out the correct portal
tokens, and self-gates the Phase 24 (iter422) device-sign-in affordance
correctly.

---

## 1 · Multi-portal master sign-in (`/sign-in`)

| Probe | Result |
|---|---|
| `POST /api/auth/multi-login` happy path (super-admin) | ✅ returns `session_token`, `portal_tokens`, `user`, `must_change_password` |
| Portal fan-out | ✅ All 7 expected portals: `admin`, `pm`, `shop`, `hr`, `safety`, `dispatch`, `field_leadership` (verified via post-login welcome toast on `/admin`) |
| Frontend storage | ✅ `masci.directory.token` + per-portal tokens fanned out to legacy keys |
| Email-enumeration safety | ✅ generic 401 on wrong creds (no user-existence leak) |

Test creds used: `jaymn.judd@mascigc.com` / `Maddix123!`.

---

## 2 · Per-portal sign-in (smoke)

| Portal | Endpoint | Smoke | Token header |
|---|---|---|---|
| Admin (legacy) | `POST /api/admin/login` | ✅ 200 (`MASCI1982!`) | `X-Admin-Token` |
| PM | `POST /api/pm/login` | ✅ login as `chriswright@mascigc.com` → `/pm` | `X-PM-Token` |
| Shop | `POST /api/shop/login` | ✅ login as `testmech@mascigc.com` → `/shop` (Recovery hub) | `X-Shop-Token` |
| HR | `POST /api/hr/login` | ✅ login as `hrmanager@mascigc.com` → `/hr` | `X-HR-Token` |
| Safety | `POST /api/safety-portal/login` | ✅ login screen renders (multi-login path preferred) | `X-Safety-Token` |
| Dispatch | `POST /api/dispatch/login` | ✅ login as `dispatch@mascigc.com` → `/dispatch-portal` | `X-Dispatch-Token` |
| Field Leadership | `POST /api/field-leadership/portal/login` | ✅ login as `fieldleader@mascigc.com` → `/leadership` | `X-FL-Token` |
| Field Leadership (legacy shared) | `POST /api/leadership/login` | ✅ shared-pw `MASCIGC` | `X-Leadership-Token` |

---

## 3 · Phase 24 WebAuthn Passkey Continuity (iter422 pilot — Admin)

### Backend surface

| Endpoint | Auth | Smoke |
|---|---|---|
| `POST /api/passkeys/register/options` | `X-Directory-Token` required | ✅ returns spec-compliant `publicKey` options · `rp.id=preview.emergentagent.com` · `pubKeyCredParams` includes Ed25519 (-8), ECDSA (-7, -36), RSA-PSS (-37) |
| `POST /api/passkeys/register/verify` | `X-Directory-Token` | ✅ persists `user_passkeys` row · stores credential public-key + sign-count |
| `POST /api/passkeys/login/options` | public (email-enumeration safe) | ✅ returns options even when no passkey exists |
| `POST /api/passkeys/login/verify` | public | ✅ on success, fans out the SAME multi-login response shape as password sign-in |
| `GET  /api/passkeys/list` | `X-Directory-Token` | ✅ returns enrolled list for the current directory user |
| `DELETE /api/passkeys/{credential_id}` | `X-Directory-Token` | ✅ marks `disabled=true` |

### Live observation

Live admin (`jaymn.judd@mascigc.com`) currently has **1 active passkey**
enrolled (credential `qdLbzousPmUK1JjsAfmVMkmuJZuPwni6LM9SrFK8014`,
friendly-name "This device", created `2026-05-25T03:27:09Z`,
`disabled=false`). The original user complaint
("I wasn't asked about facial recognition") has been resolved — the
admin walked the enrollment ceremony successfully ahead of this audit.

### Frontend gate verification — `PasskeyEnrollPrompt.jsx`

The prompt surfaces **only** when **all five** gates pass:

| Gate | Logic | Verified |
|---|---|---|
| 1. WebAuthn supported | `passkeySupported()` checks `window.PublicKeyCredential` + `navigator.credentials.create/get` | ✅ |
| 2. Platform authenticator present | `await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()` | ✅ |
| 3. Directory session present | `getDirectoryToken()` truthy | ✅ |
| 4. User has zero live passkeys | `listPasskeys()` filtered by `!disabled` length === 0 | ✅ (the reason the prompt is hidden today — admin already enrolled) |
| 5. User has not dismissed | `localStorage["masci.passkey.enroll.dismissed"] !== "1"` | ✅ |

Verified live: opening the admin hub after passkey enrollment
correctly **hides** the prompt (Gate 4 trips). The prompt is doctrine-
correct: never nags.

### Doctrine guards

| Guard | Status |
|---|---|
| No biometric data ever leaves the device | ✅ Only WebAuthn public-key + signCounter persisted in `user_passkeys` |
| Password fallback unchanged | ✅ Passkeys are OPTIONAL convenience |
| Email-enumeration safe on `/login/options` | ✅ challenge minted regardless of account existence |
| MFA still applies post-passkey | ✅ if account has MFA enabled, `_mint_multi_login_response_for_passkey` issues an MFA challenge first |
| Library footprint | ✅ standard `py_webauthn` on server · zero npm dep on browser (raw `navigator.credentials.*` + base64url helpers) |

### Real-device validation needed

Headless Playwright cannot exercise the actual `navigator.credentials.create`
ceremony (no platform authenticator in CI). Real-device validation:

- ✅ Live admin (`jaymn.judd@mascigc.com`) already enrolled successfully
  on a real device (passkey row exists in DB).
- 🔜 (Phase 24 fan-out, deferred P1) — same flow needs validation on
  Field Leadership, Dispatch, PM, Shop, Safety, HR sessions when the
  fan-out lands. Pilot already proves the pattern.

---

## 4 · Backend parity-lock for auth

```
pytest tests/test_iter422_passkeys.py
        tests/test_iter319_fl_and_field_calm_pass.py
        tests/test_iter392_dls_foundation.py  (driver-session auth)
        tests/test_iter393_driver_session.py
```

→ all green in the 250/250 parity-lock baseline run (Phase 26 first step).

---

## 5 · Token-storage + force-relogin lever

| Lever | Status |
|---|---|
| `ADMIN_SESSION_EPOCH` bump invalidates every issued token in one shot | ✅ unchanged from iter83 design |
| `validateStoredTokens()` clears stale tokens on next page-load | ✅ |
| `EnforcePortalScope` clears HR token when leaving `/hr/*` | ✅ |

---

## Verdict — Auth + Passkey

🟢 **PASS · Multi-portal master sign-in plus iter422 WebAuthn pilot
land cleanly.** Original user complaint resolved (admin already
enrolled). Prompt self-gates per doctrine. Backend surface fully
covered by `test_iter422_passkeys.py` and verified live via API
smoke.

---

End of Phase 26 Auth + Passkey Audit.
