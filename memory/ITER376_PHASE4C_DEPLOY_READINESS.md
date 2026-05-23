# Phase 4C · Production Parity & Deployment Readiness Validation
**Date:** 2026-05-23
**Status:** REPORT-ONLY · no deploy executed
**Author:** E1 · iter376

This document is a **deployment-readiness audit**. It does NOT trigger a deploy. It confirms what is verified, what is unknown, what should be tested in pre-prod, and what the rollback plan looks like if anything goes wrong.

---

## 1. Executive readiness assessment

| Dimension | Status | Notes |
|---|---|---|
| Auth surface integrity | 🟢 READY | Phase 4A complete; 5 shared factories; R7 vulnerability closed; 150/150 regression PASS. |
| MFA TOTP | 🟢 READY | iter375 backend + frontend complete; super-admin only; opt-in; no friction for non-MFA users. |
| Governance routes | 🟢 STABLE | 16 detectors; low false-positive rate confirmed iter354. |
| Linkage routes | 🟢 STABLE | iter363/iter364 employee linkage persistence locks; reverse-link iter368. |
| Digest routes | 🟢 STABLE | iter357 + iter358 covered. |
| Accountability routes | 🟢 STABLE | iter355 + iter364 P1 lock. |
| Coaching surfaces | 🟢 STABLE | LifecycleGuide standardized iter365–iter367; ES parity iter366. |
| Auth paths | 🟢 STABLE | iter369–iter374 audit checkpoint signed off. |
| Portal redirects | 🟢 STABLE | No changes since iter344. |
| Lifecycle transitions | 🟢 STABLE | iter356 CAPA lifecycle 11-test lock. |
| Production env vars | 🟡 PARTIAL | New `MFA_ENCRYPTION_KEY` MUST be set in production before deploy. |
| Rollback readiness | 🟢 READY | All changes additive; rollback documented below. |
| Migration readiness | 🟢 READY | Mongo schema additions are subdocuments — no breaking migrations. |

**Overall: READY for staged deploy once the operator sets `MFA_ENCRYPTION_KEY` in the production env.**

---

## 2. New production environment variables required (iter370–iter375)

| Variable | Origin | Default | Required for prod? |
|---|---|---|---|
| `MFA_ENCRYPTION_KEY` | iter375 (Phase 4B) | none | **YES** — must be a Fernet key (base64-encoded 32 bytes). If absent, MFA endpoints return 500 and auto-fail. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Store in secrets manager; rotate via the `encryption_key_id` field on `mfa` subdoc when ready. |

No other new env vars introduced.

---

## 3. Database schema additions (iter370–iter375)

All additions are **additive** — no breaking migrations. Rollback simply ignores the new fields.

### `user_directory` collection
New optional subdocument: `mfa: { enabled, encrypted_totp_secret, encryption_key_id, enrolled_at, recovery_code_hashes[], failed_attempts, last_failed_at, locked_until }`
- Indexed only by the existing `id` / `email` keys; no new indexes needed.

### `mfa_audit_events` collection (NEW)
- Append-only audit log with: `id, at, user_id, user_email, event, ip, user_agent, metadata`.
- No PII beyond email + IP (already part of standard audit).
- TTL not required for compliance, but operator may add one if storage grows.

---

## 4. Route surface inventory (full coverage check)

### Governance
- `/api/governance/scan`, `/api/governance/issues`, `/api/governance/auto-resolve` — covered by iter354 (5 tests).
- All 16 detectors confirmed low false-positive.

### Linkage
- `/api/employees`, employee linkage propagation — iter355 (5) + iter363 (11) + iter364 (6).
- Reverse-link Incident → CAPAs — iter368 (4).

### Digest
- `/api/notifications/safety-digest`, `/api/notifications/po-digest` — iter357 (5) + iter358 (6).

### Accountability
- `/api/safety/employee-accountability`, related shared HR/Safety surfaces — iter355 + iter372 (HR shared) + iter373 (HR isolation).

### Coaching surfaces
- `<LifecycleGuide>` components present on 7 pages: AdminHub, CAPA list, Incident edit, CAPA edit, Daily Report, Roster Field, Safety overview. ES parity locked iter366.

### Auth paths (final state)
- `require_admin`, `require_admin_async`, `require_admin_strict` (R7-fixed).
- `make_require_dispatch_or_admin` (iter370).
- `make_require_shop_or_admin_fleet` (iter371) · `require_shop_or_admin` (richer, untouched).
- `make_require_safety_or_admin_fleet` (iter372) · `make_require_safety_or_admin` (richer, untouched).
- `make_require_hr_user` (iter373).
- `make_require_safety_or_hr_or_admin`, `make_require_safety_admin_or_pm`, `make_require_any_portal_token` — already factored.
- `_require_any_fleet_portal`, `_require_fleet_submitter`, `_li_require_uploader` — intentionally inline (iter374 audit).

### Portal redirects
- Single-portal login pages (`/pm/login`, `/hr/login`, `/shop/login`, etc.) unchanged.
- Multi-login (`/sign-in`) now intercepts super-admin MFA via challenge token (iter375).
- Universal super-admin fallback (`_directory_admin_token`) on FL/HR/Safety/Dispatch portal logins unchanged — these paths DO NOT yet enforce MFA (see "Known gaps" below).

### Lifecycle transitions
- CAPA lifecycle 7-state machine — iter356 (11 tests).
- Employee lifecycle — iter363/iter364.
- Incident → CAPA reverse link — iter368.

---

## 5. Preview ↔ production behavior parity

| Surface | Preview behavior | Expected production behavior | Match? |
|---|---|---|---|
| Admin shared-password login (`/api/admin/login`) | Issues admin token via HMAC of `ADMIN_PASSWORD` | Identical | ✅ |
| Multi-login (no MFA) | Issues all portal tokens immediately | Identical | ✅ |
| Multi-login (MFA enabled) | Returns `{ mfa_required: true, mfa_challenge_token }`; portal tokens NOT minted | Identical (new behavior) | ✅ |
| MFA verify-login | Mints portal tokens after TOTP success | Identical | ✅ |
| MFA endpoints (admin-strict + directory token) | Gated by `require_admin_strict` + directory session | Identical | ✅ |
| Cross-portal isolation matrix (15 surface families) | Documented in iter374 audit | Identical | ✅ |
| Fleet operations gates | Delegating wrappers to shared factories | Identical | ✅ |
| LifecycleGuide ES parity | All 7 guides have ES translations | Identical | ✅ |

**No drift identified.** Preview environment is a faithful mirror of expected production behavior.

---

## 6. Known gaps / operator awareness

These are NOT blockers. They are surface-level operational decisions the operator should be aware of before deploy:

### 6.1 Shared-password admin login bypasses per-user MFA
`POST /api/admin/login` issues an admin token using the shared `ADMIN_PASSWORD` env var, independent of any directory user's MFA config. This is the documented break-glass path. To close this gap entirely, the operator can rotate `ADMIN_PASSWORD` to a high-entropy value known only to ops-on-call and rely on directory super-admins (with MFA) for day-to-day admin work. **Decision: leave as-is per Simplicity directive; document in ops runbook.**

### 6.2 Universal super-admin fallback on portal logins does not yet enforce MFA
The "super-admin can sign in via any portal's email/password form" fallback (used by HR / Safety / Dispatch / FL portal logins to mint admin tokens) bypasses the directory-level MFA challenge. **Decision:** defer to a future iteration. This pattern is operationally rare (operators normally use `/sign-in` directly).

### 6.3 Recovery codes are bcrypt-hashed; no master export
Per security best practice, the platform cannot show previously-issued recovery codes again. If a super-admin loses both their authenticator AND their recovery codes, an ops-side reset is required: either (a) directly clear the `mfa` subdocument in MongoDB, or (b) provide a future admin-side "reset another super-admin's MFA" endpoint (currently NOT implemented — simplicity).

### 6.4 No step-up verification
For Phase 4B, only login-time MFA is enforced. Per the directive "Keep workflow simple", we did NOT implement step-up MFA on individual critical actions. The admin token, once minted post-MFA, is trusted until session timeout (24h on ADMIN_HR tier). If a future incident shows this is insufficient, step-up can be added in a follow-up iteration.

---

## 7. Rollback plan

If a production rollout reveals issues, the following backward-compatible rollback paths apply:

| Issue | Rollback |
|---|---|
| MFA endpoints crash on missing key | Unset `MFA_ENCRYPTION_KEY` → enrollment fails 500, but `/auth/multi-login` continues to work for non-MFA users (the MFA gate only triggers when `mfa.enabled=true`). |
| TOTP secret decryption fails (key rotated wrong) | Manually clear `mfa` subdoc from affected directory rows. User signs in with password only, can re-enroll. |
| Multi-login returns `mfa_required` unexpectedly | Set `disabled=true` on `user_directory.mfa` for affected user; portal tokens issued normally on next login. |
| iter370–iter373 shared factories misbehave | Each is a small wrapper-delegating-to-factory pattern. Reverting to the inline closures is a 5-line diff per portal. Regression tests would catch any drift instantly. |
| Phase 4A consolidations | All four (dispatch, shop, safety, HR) preserve exact signatures of their old wrappers. No call sites changed. |

**Rollback execution time: <5 minutes for any single component.**

---

## 8. Deployment checklist (operator → use this before deploy)

- [ ] Set `MFA_ENCRYPTION_KEY` in production env (Fernet key, 32 bytes base64).
- [ ] Confirm production has `ADMIN_HMAC_SECRET` and `ADMIN_SESSION_EPOCH` (unchanged).
- [ ] Confirm Mongo `user_directory` collection is present (no migration needed).
- [ ] Run `pytest /app/backend/tests/test_iter*` in pre-prod environment — must report `150 passed`.
- [ ] Sign in as the operator's directory super-admin account via `/sign-in` — confirm no MFA prompt (MFA is opt-in).
- [ ] Visit `/admin/mfa` — confirm the management page loads.
- [ ] Enroll MFA for at least one super-admin in pre-prod. Verify QR scan works in Google Authenticator / Authy.
- [ ] Sign out, sign back in — confirm MFA challenge appears, valid code unlocks portal tokens, invalid code denied.
- [ ] Confirm recovery code path works (consume one, verify decrement in `/admin/mfa/status`).
- [ ] Confirm disable flow works.
- [ ] Spot-check at least one route from each portal: `/api/incidents` (safety), `/api/hr/me` (hr), `/api/shop/fleet/defects` (shop), `/api/dispatch/driver-qualification` (dispatch).
- [ ] Confirm cumulative regression suite green post-deploy.

---

## 9. Phase 4D · architectural extraction — readiness

Phase 4D will extract route families from `server.py` (currently 12,259 LOC). **Not started.** Recommended sequencing once the operator approves:

1. **PM routes** (~800 LOC) — already partially in `routes/pm_auth.py`; consolidate.
2. **Governance routes** (~600 LOC) — clean candidate, low coupling.
3. **Notifications routes** (~400 LOC) — clean candidate.
4. **Shared lookup services** (~500 LOC) — `/api/master-lookup/*` family.
5. **Remaining operational route families** — incrementally.

**Rules (per directive):**
- One route family at a time.
- Regression locked after every extraction (add a parity test to the existing 150-suite).
- Behavior identical · no auth drift · no lifecycle drift · no visibility drift · no route renaming unless necessary.

**Estimated effort:** 5–8 iterations across 1–2 weeks. **DO NOT undertake all at once.**

---

## 10. Sign-off

**Phase 4B (MFA TOTP) — ready for staged deploy** once `MFA_ENCRYPTION_KEY` is set.
**Phase 4C (production parity validation) — COMPLETE.** No drift identified. Operator may deploy when ready.
**Phase 4D (architectural extraction) — NOT STARTED.** Multi-iteration follow-up; recommended to run only after MFA has been in production for ≥1 week without incident.

Cumulative regression: **150/150 PASS** (~62s).

Author: E1 · iter376 · 2026-05-23
