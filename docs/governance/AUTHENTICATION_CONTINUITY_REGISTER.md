# AUTHENTICATION CONTINUITY REGISTER

Date: 2026-07-20  
Scope: PDC-01A authentication continuity proof for the exact `/app` workspace  
Mode: verification-only, no credential rotation, no user/auth record mutation for certification

## Certification objective
- Prove that this candidate preserves authentication continuity for existing users without forced resets, silent hash drift, signing-secret semantic changes, schema incompatibility, or startup-side overwrite behavior.

## Canonical evidence sources
- Password hashing and verification:
  - `backend/auth.py`
  - `backend/user_directory.py`
  - `backend/pm_auth.py`
- Session and multi-portal continuity:
  - `backend/user_directory.py`
  - `backend/routes/mfa_routes.py`
  - `backend/server.py`
- Passkey compatibility:
  - `backend/routes/passkeys.py`
- MFA compatibility:
  - `backend/routes/mfa_routes.py`
- Release-time proof tests:
  - `backend/tests/test_track14_auth_password_parity.py`
  - `backend/tests/test_iter369_auth_regression_lock.py`
  - `backend/tests/test_track_15_13e_production_auth_session_recovery.py`
  - `backend/tests/test_track_15_87_multi_portal_access_authority.py`
  - `backend/tests/test_iter375_mfa_totp.py`
  - `backend/tests/test_iter422_passkeys.py`

## Password hash compatibility
- `backend/auth.py`, `backend/user_directory.py`, and `backend/pm_auth.py` all verify existing hashes using `bcrypt.checkpw(...)`.
- New hashes are explicitly pinned to `bcrypt.gensalt(rounds=12)`.
- Current and legacy bcrypt hashes remain verifiable because verification does not depend on regenerating the original salt or cost string.
- No code path in this certification slice introduces mass rehash, opportunistic auto-rehash, or login-time overwrite.

## No forced reset or automatic rehash
- `backend/auth.py::verify_password`, `backend/user_directory.py::verify_password`, and `backend/pm_auth.py::verify_password` are read-only checks.
- Password hash writes occur only on explicit password-set or password-reset flows, never during passive verification.
- No PDC-01A change introduces background, startup, or login-triggered password rewrites.

## Signing-secret semantics unchanged
- JWT semantics in `backend/auth.py` remain `HS256` and continue to derive from `JWT_SECRET` without changing token claim shape.
- Directory admin, PM, shop, safety, dispatch, and related HMAC token families still bind to the same secret-and-epoch model already present in runtime code.
- This slice does not rotate secrets, rename keys, or alter token parsing contracts.

## Session and token continuity
- Existing sessions/tokens are classified honestly, not falsely claimed to be evergreen:
  - JWT access/refresh tokens continue to depend on existing secret material and expiry claims.
  - Directory sessions remain server-side records in `directory_sessions`.
  - Portal HMAC tokens remain tied to current password-hash prefixes and session epochs.
- Result: previously issued tokens keep their existing semantics; no new blanket invalidation behavior was introduced by this certification work.

## MFA and passkey schema compatibility
- MFA records remain compatible because `backend/routes/mfa_routes.py` continues to use the existing `mfa` subdocument shape (`enabled`, `encrypted_totp_secret`, `recovery_code_hashes`, `failed_attempts`, `locked_until`, `enrolled_at`).
- Passkey records remain compatible because `backend/routes/passkeys.py` continues to read/write the same credential metadata fields (`directory_user_id`, `credential_id`, `public_key`, `sign_count`, `rp_id`, `friendly_name`, timestamps, `disabled`).
- No destructive migration, field rename, or schema contraction was introduced in this slice.

## Role, tenant, company, and project-access compatibility
- Directory access still resolves from the existing `user_directory` row shape and portal grants.
- PM/project visibility still flows through `backend/pm_auth.py::PmScope` and related route consumers.
- No PDC-01A change mutates roles, memberships, project access mappings, or tenant/company linkage behavior.

## Reset and bootstrap behavior
- `backend/auth.py::seed_initial_users` is additive-only for missing seed users and leaves existing rows untouched.
- `backend/user_directory.py::bootstrap_super_admin` is idempotent and explicitly avoids password overwrite for existing accounts.
- No auth seed, overwrite, or migration run in this slice was broadened to rewrite existing user credentials at startup.
- Existing startup behavior is preserved and only documented here for continuity classification.

## Break-glass classification
- Legacy admin password path: still a fallback only, not a new deployment-time mutation.
- Developer and portal fallback paths remain subject to their pre-existing auth contracts.
- This register does not authorize new break-glass secrets or any password reset operation.

## Lockout and abuse controls
- Login lockout constants remain pinned in `server.py` and imported from `backend/lib/rate_limiting.py`.
- The certification slice preserves the existing fail-closed lockout design while allowing pytest-safe bypass only under explicit test conditions.
- No production lockout weakening is introduced.

## Rollback compatibility
- Rollback remains application/source only by default under the existing governed recovery doctrine.
- Because auth data schemas and secret semantics are unchanged in this slice, rollback compatibility with unchanged auth data is preserved.

## Compatibility proof matrix
| Concern | Evidence | Continuity status |
|---|---|---|
| Existing bcrypt hashes verify | `bcrypt.checkpw` in auth modules | PRESERVED |
| Mass reset introduced | No startup/login mass reset path added | NOT INTRODUCED |
| Automatic rehash introduced | No login-time overwrite path added | NOT INTRODUCED |
| JWT/session semantics changed | Existing token helpers unchanged | PRESERVED |
| MFA schema drift | Existing `mfa` fields unchanged | PRESERVED |
| Passkey schema drift | Existing `user_passkeys` fields unchanged | PRESERVED |
| Roles / memberships drift | No mutation path added in this slice | PRESERVED |
| Startup auth overwrite | Existing seeds remain additive/idempotent only | PRESERVED |
| Rollback with unchanged auth data | No auth data model rewrite in this slice | PRESERVED |

## Regression evidence
- The canonical auth continuity proof for PDC-01A is the combination of this register plus focused backend tests.
- Runtime-only auth tests that hit the preview URL are classified as environment-limited when the D1 fail-closed startup gate intentionally returns 502.
- That 502 state is not treated as a continuity pass; it is treated as honest non-execution for live preview proof.

## 2026-08-09 PRE-C10 auth/logout/session amendment status
- Status: **OPEN — shared root cause repaired, denominator still in progress**.
- Original recurring symptom:
  - signed-out return and stale portal context were not uniformly governed across login/logout boundaries;
  - Field Leadership direct login could inherit stale sibling portal tokens from a prior user/session;
  - Track 19.11 overlay smoke labels were still documentation-skipped, blocking `UNJUSTIFIED SKIPS = 0`.
- Root cause:
  - logout repair had been centralized, but successful portal-login flows were still allowed to write a new identity on top of old browser auth artifacts;
  - `/leadership/login` and `/field-leadership/portal/login` were not treated as explicit identity-switch routes by the shared login-route wipe;
  - portal-context stamping was not consistently refreshed at successful-login time.
- Why the prior repair was not permanent:
  - it fixed the sign-out/public-home path locally, but left the fresh-login boundary fragmented across page-specific logic;
  - a shared failure class remained where a new FL login could retain stale Dispatch/Safety tokens from the previous auth state.
- Shared owner/components:
  - `frontend/src/lib/sessionReset.js`
  - `frontend/src/components/EnforcePortalScope.jsx`
  - `frontend/src/lib/portalContext.js`
  - direct portal login pages and shared `SignIn.jsx` / `AdminLogin.jsx`
- Shared repair now in place:
  - new `prepareFreshLoginSession()` fail-closed browser wipe before every successful login write;
  - destination-based portal-context stamping;
  - FL login routes added to the shared explicit-login wipe;
  - redundant token-key cleanup to survive helper drift;
  - `memory/TRACK_19_11_SESSION_OVERLAY_REGRESSION_REPORT.md` written so Track 19.11 live-smoke assertions are documented, not skipped.
- Current direct evidence:
  - focused frontend regressions PASS: `Hub.session-home.test.jsx`, `c2_session_reset.test.js`, `AdminOS.truthLineage.test.jsx`;
  - preview browser repro before fix showed stale FL-over-admin sibling tokens (`dispatchToken` + `safetyToken` remained true);
  - preview browser repro after fix showed only governed FL+directory state remained and `portalContext` became `field-leadership`;
  - preview browser logout flow returned to `/`, restored a visible signed-out public entry, and browser-back landed on guarded login instead of privileged content;
  - Track 19.11 EN/ES overlay smoke passed across `/daily/submit`, `/equipment/new`, `/fleet/dvir/new`, and `/meetings/submit`;
  - public-vs-portal access doctrine was re-verified and repaired: `/field`, `/daily/submit`, `/equipment/submit`, `/shift`, `/fleet/dvir/new`, `/fleet/weekly-lead/new`, `/fleet/weekly-emergency/new`, `/field/calculators`, `/safety`, `/safety/inspections/new`, `/meetings/submit`, `/incidents/report`, `/jha`, `/trench-safety`, `/safety/cards`, `/safety/forms`, `/safety/forms/equipment-issuance/new`, and `/safety/forms/equipment-training/new` all load signed-out without redirect or session-expired overlay, while `/admin`, `/pm`, `/hr`, `/safety-portal`, `/dispatch-portal`, `/shop`, `/field-leadership/portal/dashboard`, and `/leadership` still redirect to governed login routes when signed out;
  - anonymous preview POST proof now exists for `/api/inspections`, `/api/safety-forms/equipment-issuances`, and `/api/safety-forms/equipment-trainings`.
  - anonymous-safe lookup hardening is now in place via `/api/public/jobs-lookup` and `/api/public/equipment-master-lookup`, with public form clients switched away from the broader internal `/api/jobs` and `/api/equipment-master` payloads.
  - training-boundary repair now closes the public/protected ambiguity for HR and Field Leadership training: signed-out runtime proves `/training` routes to `/hr/login` and `/field-leadership/portal/login` where governed, `/training/leadership/packet` redirects back to the protected track instead of exposing a broken packet path, and focused backend regression `test_prec10_training_packet_access_boundary.py` now proves `/api/training/packet.pdf?track=hr` is `401` signed-out and `200` with HR/Admin auth while `track=field` stays public.
- Remaining auth denominator still open:
  - all-role browser proof (Admin, Executive, PM, FL, Safety, HR, Shop, Dispatch, other governed roles);
  - expiry/deep-link/multi-workspace/full owner-observed replay;
  - full EN/ES + responsive + accessibility denominator;
  - final owner-observed disposition chain;
  - full route/API access matrix closure and guidance-center public/protected denominator;
  - full public device/draft continuity denominator per `docs/governance/PUBLIC_DEVICE_AND_DRAFT_CONTINUITY_CONTRACT.md`.

## Executive conclusion
- This register proves continuity by static contract and focused regression evidence.
- It does not claim deployment GO.
- It is the canonical replacement for stale `/app/memory/**` authentication support artifacts in deployment certification.