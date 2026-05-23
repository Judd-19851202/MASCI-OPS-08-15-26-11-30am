# Phase 4B · Operator Deploy Handoff (MFA TOTP)
**For:** Operator/DevOps preparing the production cutover.
**Status:** Pre-prod ready · cumulative regression 171/171 PASS.

---

## P0 · Three operator actions before production

### 1. Set `MFA_ENCRYPTION_KEY` in production environment

Generate a fresh Fernet key for production (do NOT reuse the preview key):

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add it to your production `.env` (or your secrets manager):

```
MFA_ENCRYPTION_KEY=<the-44-char-base64-key-you-just-generated>
```

**Important:**
- This key encrypts the TOTP secrets at rest in MongoDB. If you lose it, all enrolled super-admins must re-enroll. Treat it like `ADMIN_HMAC_SECRET`.
- Store a copy in your password manager / vault. Do NOT commit it to git.
- The preview environment uses a different key — they intentionally do not share key material so a preview compromise does not affect production.

### 2. Execute the 10-item deploy checklist

From `/app/memory/ITER376_PHASE4C_DEPLOY_READINESS.md` (full report — read once before cutover):

- [ ] Set `MFA_ENCRYPTION_KEY` in production env (above).
- [ ] Confirm production has `ADMIN_HMAC_SECRET` and `ADMIN_SESSION_EPOCH` (unchanged from prior deploys).
- [ ] Confirm production MongoDB has the `user_directory` collection populated (no schema migration required — `mfa` subdoc is added on-demand).
- [ ] Run `pytest /app/backend/tests/test_iter*` in a pre-prod environment that mirrors production. Must report `171 passed`.
- [ ] Sign in as a super-admin via `/sign-in` on pre-prod → confirm NO MFA prompt (MFA is opt-in until you enroll).
- [ ] Visit `/admin/mfa` on pre-prod → confirm the management page loads cleanly.
- [ ] Enroll MFA for at least ONE super-admin in pre-prod. Scan the QR with Google Authenticator / Authy / 1Password / Microsoft Authenticator (any will work — verified via pyotp standard).
- [ ] Sign out, sign back in → confirm the MFA challenge screen appears, the 6-digit code unlocks portal tokens, invalid codes are denied.
- [ ] Test one recovery code → confirm it works exactly once and the `recovery_codes_remaining` count decrements in `/admin/mfa/status`.
- [ ] Test the disable flow → confirm sign-in returns to normal after MFA is removed.

### 3. Smoke-test in pre-prod before going live for staff

Before announcing MFA to your super-admin users, run the full enroll → login → recovery → disable cycle yourself in pre-prod. Estimated time: 5 minutes.

**Why pre-prod first:**
- Catches any operator-environment differences (clock drift between server and authenticator app, MongoDB connectivity, env var typos).
- TOTP requires synchronized clocks (±30s tolerance). If your production server has significant clock drift, codes will fail. Verify with `date -u` on the production host vs your phone.

---

## After deploy · communicate to super-admin users

A simple template:

> **Subject: MFA available for your MASCI Operations admin account**
>
> Two-factor authentication is now available on the MASCI Operations Platform. It's optional for now, but strongly recommended given your admin access.
>
> To enroll:
> 1. Sign in as usual at `<your-prod-url>/sign-in`.
> 2. Go to `<your-prod-url>/admin/mfa`.
> 3. Click "Start MFA Enrollment".
> 4. Scan the QR code with your authenticator app (Google Authenticator, Authy, 1Password, or Microsoft Authenticator all work).
> 5. Save your recovery codes somewhere safe (e.g. your password manager).
> 6. Enter the first 6-digit code to confirm.
>
> Next time you sign in, you'll be prompted for a code in addition to your password. If you lose your phone, use a recovery code (each works once). If you lose both your phone AND recovery codes, contact ops to clear your MFA config — you'll re-enroll on next login.

---

## Rollback plan (if anything goes wrong)

| Issue | Rollback |
|---|---|
| MFA endpoints return 500 | Verify `MFA_ENCRYPTION_KEY` env var is set. Restart the FastAPI worker. |
| A user is locked out (lost authenticator + recovery codes) | Connect to production MongoDB, run `db.user_directory.updateOne({email:"…"}, {$unset:{mfa:""}})`. User signs in with password only, can re-enroll. |
| Multi-login returns `mfa_required` for a user who never enrolled | Same Mongo command as above — clears the MFA subdoc. |
| Code rotation (key compromise) | Generate a new `MFA_ENCRYPTION_KEY`, clear `mfa` subdoc for all users, ask everyone to re-enroll. Estimated user impact: 2 minutes per super-admin. |

Full rollback procedure documented in `/app/memory/ITER376_PHASE4C_DEPLOY_READINESS.md` § 7.

---

## Audit trail location

All MFA events are recorded in MongoDB collection `mfa_audit_events`:

```javascript
db.mfa_audit_events.find().sort({at:-1}).limit(20)
```

Event types: `ENROLLMENT_STARTED`, `ENROLLMENT_COMPLETED`, `TOTP_VERIFY_SUCCESS`, `TOTP_VERIFY_FAILURE`, `RECOVERY_CODE_USED`, `RECOVERY_CODE_FAILURE`, `MFA_DISABLED`, `RECOVERY_CODES_REGENERATED`, `LOGIN_MFA_CHALLENGE_ISSUED`, `MFA_LOCKED_HIT`.

No secrets or recovery codes are ever logged — only the success/failure event with the actor email, IP, and user-agent.
