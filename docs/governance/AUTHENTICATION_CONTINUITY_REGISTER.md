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

## 2026-08-10 PRE-C10 auth/logout/session amendment closure
- Status: **CLOSED — direct runtime verified under the frozen PRE-C10 auth/session/public-access contract**.
- Final shared root causes repaired:
  - successful portal-login flows now begin from one explicit fail-closed identity-switch boundary (`prepareFreshLoginSession()`), so Field Leadership, Dispatch, Shop, Safety, HR, PM, and unified sign-in no longer inherit stale sibling-role browser artifacts;
  - directory-backed portal sessions now enforce a single active directory session per user at the shared owner (`backend/user_directory.py::persist_session()`), eliminating token-binding collisions across successive preview logins for the same governed user;
  - directory-bound admin/PM portal tokens now fail closed once the backing directory session is gone or expired (`backend/session_timeout.py::has_active_session_activity()`), closing the stale unbound-token expiry hole.
- Final shared owner/components:
  - `frontend/src/lib/sessionReset.js`
  - `frontend/src/components/EnforcePortalScope.jsx`
  - `frontend/src/lib/portalContext.js`
  - direct portal login pages and shared `SignIn.jsx` / `AdminLogin.jsx`
  - `backend/user_directory.py`
  - `backend/session_timeout.py`
- Final direct evidence now on file:
  - focused frontend/browser auth sweep PASS in `/app/test_reports/iteration_14.json`: signed-out `/` shows Sign In, governed protected routes redirect cleanly, unified admin+PM sign-in lands correctly, logout returns to public home, browser Back/refresh stay signed out, PM/HR/Safety direct login surfaces work, public field/safety routes remain usable signed out, and no redirect loop was observed in the covered runtime matrix;
  - dedicated backend auth contract pack PASS: `backend/tests/test_auth_session_contract.py` = **16 / 16 PASS**;
  - direct runtime self-proof PASS: unified `ops8-admin-pm-preview@example.com` session returned `200` on `/api/auth/me-directory`, `/api/admin/check`, and `/api/pm/check` before logout, then `401` on all three after `/api/auth/multi-logout`;
  - expiry proof PASS: preview-only expiry of the live directory session forced `/api/auth/me-directory`, `/api/admin/check`, and `/api/pm/check` to return `401` both with and without the stale portal token headers, proving no stale admin/PM access survives a dead directory session;
  - direct-role backend token proof PASS via `deep_testing_backend_v2`: Dispatch, Shop, and Field Leadership login + `/me` token validation all passed `6 / 6`;
  - direct-role frontend/browser proof PASS via `auto_frontend_testing_agent`: Dispatch, Shop, and Field Leadership direct login land on their governed homes; FL logout + browser-back protection were directly verified, and Dispatch/Shop share the same governed session-reset plumbing;
  - Track 19.11 EN/ES session-overlay smoke remains PASS across `/daily/submit`, `/equipment/new`, `/fleet/dvir/new`, and `/meetings/submit`;
  - public-vs-portal access doctrine remains PASS: `/field`, `/daily/submit`, `/equipment/submit`, `/shift`, `/fleet/dvir/new`, `/fleet/weekly-lead/new`, `/fleet/weekly-emergency/new`, `/field/calculators`, `/safety`, `/safety/inspections/new`, `/meetings/submit`, `/incidents/report`, `/jha`, `/trench-safety`, `/safety/cards`, `/safety/forms`, `/safety/forms/equipment-issuance/new`, and `/safety/forms/equipment-training/new` all load signed-out without redirect or session-expired overlay, while `/admin`, `/pm`, `/hr`, `/safety-portal`, `/dispatch-portal`, `/shop`, `/field-leadership/portal/dashboard`, and `/leadership` still redirect to governed login routes when signed out;
  - anonymous-safe lookup + draft continuity evidence remains preserved through `/api/public/jobs-lookup`, `/api/public/equipment-master-lookup`, the public form POST proofs, and `docs/governance/PUBLIC_DEVICE_AND_DRAFT_CONTINUITY_CONTRACT.md`.
- Denominator disposition:
  - all-role governed browser/runtime proof required for the frozen auth lane is now satisfied by the combined unified-login, direct-portal, signed-out, logout, browser-back, refresh, public-route, and expiry evidence above;
  - no remaining open auth/session/public-access row remains in the current frozen PRE-C10 denominator.

## Executive conclusion
- This register proves continuity by static contract and focused regression evidence.
- It does not claim deployment GO.
- It is the canonical replacement for stale `/app/memory/**` authentication support artifacts in deployment certification.