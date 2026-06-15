# AUTH_EXISTING_USER_PROTECTION_CERTIFICATION.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Status:** ✅ HARD-LOCK SATISFIED. ZERO production user changes.

## Production Login Protection Invariants

This certification verifies that the entire Auth-Parity track changed
nothing that could affect a real user's ability to log in.

### Invariant 1 — ZERO password hashes rewritten
**Test:** No call to `bcrypt.hashpw` was executed against any
existing user document during the track.
**Evidence:**
- `git diff` shows only one bcrypt-related edit: `auth.py::hash_password`
  pinned from `bcrypt.gensalt()` to `bcrypt.gensalt(rounds=12)`.
- bcrypt's default work factor IS currently 12, so existing hashes
  produced under the unpinned version remain verifiable by the new
  pinned version (verification uses the cost factor embedded in the
  hash, not the gensalt arg).
- No migration script, no startup re-hash, no admin endpoint executed.

### Invariant 2 — ZERO sessions invalidated
**Test:** `ADMIN_SESSION_EPOCH` was NOT changed.
**Evidence:**
- `/app/backend/.env` `ADMIN_SESSION_EPOCH=1` unchanged.
- No `make_pm_token` / `make_hr_token` / etc. invocations during this
  track.

### Invariant 3 — ZERO users logged out
**Test:** No call to any `/{portal}/logout` or
`/api/auth/multi-logout` endpoint.
**Evidence:** Track is documentation + regression tests only.

### Invariant 4 — ZERO production user data modified
**Test:** No write to `user_directory`, `project_managers`,
`hr_users`, `safety_users`, `shop_users`, `dispatch_users`,
`field_leadership_users`.
**Evidence:** `git diff` of `backend/` shows zero writes to any of
these collections this track.

### Invariant 5 — Existing routes preserved
**Test:** All legacy login routes still resolve.
**Evidence:**
- `POST /api/admin/login` (legacy) — preserved
- `POST /api/pm/login` legacy shared-password path — preserved
- `POST /api/dev/login` — preserved
- `POST /api/leadership/login` — preserved
- `POST /api/safety-forms/login` — preserved

### Invariant 6 — Pydantic validators NOT weakened
**Test:** No `min_length` reduction across any Pydantic
auth-related model.
**Evidence:** `git diff` shows no edits to `auth.py:127-144` or any
per-portal Pydantic. The single edit at `auth.py:60` is a
function-body change, not a model change.

### Invariant 7 — Env vars unchanged
**Test:** `/app/backend/.env` has identical auth-relevant keys.
**Evidence:** No edits to `.env` this track.

### Invariant 8 — No env-var DEFAULTS changed
**Test:** `LOGIN_MAX_FAILS`, `LOGIN_LOCKOUT_SECONDS`, etc. defaults
in `server.py` unchanged.
**Evidence:** No edits to `server.py:140-185`.

## What this track DID change

1. **`/app/backend/auth.py`** — single line: `bcrypt.gensalt()` →
   `bcrypt.gensalt(rounds=12)` for documentary explicitness. Behavior
   identical (bcrypt's default IS 12).

2. **Eight new memory docs** —
   - `AUTH_INVENTORY.md`
   - `AUTH_PASSWORD_CONTRACT.md`
   - `AUTH_LOCKOUT_CERTIFICATION.md`
   - `AUTH_RESET_CERTIFICATION.md`
   - `AUTH_SESSION_CERTIFICATION.md`
   - `AUTH_EXISTING_USER_PROTECTION_CERTIFICATION.md` (this file)
   - `AUTH_RUNTIME_PROOF_MATRIX.md`
   - `AUTH_REGRESSION_SUITE_SUMMARY.md`

3. **One new pytest file** —
   `/app/backend/tests/test_track14_auth_password_parity.py` (read-only
   contract assertions; does NOT execute against live users).

## Deferred work (separate tracks, NO production impact yet)

- **TRACK 14.X · AUTH-PER-ACCOUNT-LOCKOUT-ADDITIVE-ROLLOUT** —
  documented in `AUTH_LOCKOUT_CERTIFICATION.md`. Lazy-init failed
  counter; no backfill; no existing user change until they fail to
  authenticate.
- **TRACK 14.Y · AUTH-MIN-LENGTH-NORMALIZATION** — currently per-portal
  is 6, master is 10. Bumping per-portal to 10 would invalidate
  existing 6-9 char passwords on next change, but does NOT invalidate
  currently active sessions. Recommended to ship with a deprecation
  banner.

## Closure verdict

🟢 **GO.** PRODUCTION LOGIN PROTECTION fully satisfied. Every user
who could log in before this track can still log in after, with the
exact same password, the exact same token, the exact same portal
permissions.
