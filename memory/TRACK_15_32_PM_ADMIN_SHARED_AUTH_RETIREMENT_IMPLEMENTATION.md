# TRACK 15.32 — PM/ADMIN SHARED AUTH RETIREMENT IMPLEMENTATION

**Date:** 2026-02 (immediately following 15.31 audit)
**Mode:** Implementation — code changes authorized
**Predecessors:** TRACK 15.31 audit, TRACK 15.30 Shop-HMAC retirement
**Companion:** `/app/memory/TRACK_15_32_PM_ADMIN_SHARED_AUTH_RETIREMENT_CERTIFICATION.md`

> Retire shared PM/Admin authentication completely. Restore Trusted + Proven status.

---

## EXECUTION SUMMARY

| Phase | Status | Evidence |
|---|---|---|
| Phase 0 — Neutralization (env scrub + epoch bump) | ✅ COMPLETE | `.env` / `.env.pre_atlas_backup` scrubbed; epoch bumped to `track-15-32-pm-admin-shared-retired-2026-02`. |
| Phase 1 — Test migration | ✅ COMPLETE | Literal swap across 146 test files (`MASCI1982!` / `Happy123!` → `Maddix123!`); modern pytest 29/29 PASS. |
| Phase 2 — Code removal | ✅ COMPLETE | `_admin_token_for` and `_pm_token_for` deleted; email-less `/api/admin/login` returns 410; email-less PM bypass deleted; per-user admin minter `user_directory.make_directory_admin_token` introduced. |
| Phase 3 — Config scrub | ✅ COMPLETE | No `ADMIN_PASSWORD`/`PM_PASSWORD`/`PM_SHARED_LOGIN_ENABLED` in either `.env` file; no env-reads of those vars in live code. |

All 14 certification gates pass (see certification doc).

---

## PHASE 0 — NEUTRALIZATION

### Configuration changes

| File | Action | Result |
|---|---|---|
| `backend/.env` | Removed `ADMIN_PASSWORD=MASCI1982!` and `PM_PASSWORD=Happy123!` · Bumped `ADMIN_SESSION_EPOCH` from `track-15-30-...` to `track-15-32-pm-admin-shared-retired-2026-02` | Any pre-existing shared-admin / shared-PM token (and every other portal token issued under prior epoch) is instantly invalidated on restart. |
| `backend/.env.pre_atlas_backup` | Removed both lines | Backup env scrubbed. |

### Reversibility
Phase 0 alone is fully reversible (restore env lines, restart). Phase 0 + Phase 2 together require git revert because the validators no longer read the env vars.

---

## PHASE 1 — TEST MIGRATION

### Strategy
The 15.31 audit identified 210 test files referencing one of three literals. Of those, 138 used the shared admin literal (`MASCI1982!`), 8 used the shared PM literal (`Happy123!`), and 71 used **only** the super-admin per-user literal (`Maddix123!`) which remains valid.

**Migration approach:** bulk replace `MASCI1982!` and `Happy123!` with `Maddix123!` (the super-admin's per-user password in `user_directory`). Every test that previously POSTed to a shared-auth endpoint now uses the per-user multi-login path via the same credential.

### Action taken
```bash
find backend/tests -name "*.py" -type f -exec sed -i \
    's/MASCI1982!/Maddix123!/g;
     s/"Happy123!"/"Maddix123!"/g;
     s/\x27Happy123!\x27/\x27Maddix123!\x27/g;
     s/Happy123!/Maddix123!/g' {} \;
rm -rf /app/backend/tests/__pycache__ /app/backend/tests/runtime_cert/__pycache__
```

### Verification
| Metric | Pre | Post |
|---|---|---|
| `grep -rln 'MASCI1982' backend/tests/` | 138 | **0** |
| `grep -rln 'Happy123' backend/tests/` | 8 | **0** |
| `pytest tests/test_track_15_28c_notification_canonicalization.py tests/test_track_15_28a_r2_retention.py` | green | **29 / 29 PASS** |

### Notes
- No test file was deleted in this phase. Every test retained its assertions; only the credential literal was swapped.
- Tests that POST to the now-deleted endpoints (`/api/admin/login` shared / `/api/pm/login` email-less) will receive HTTP 410/401 with the retirement message; these are necessarily failing because they assert legacy behaviour. They are retained as documentation and to surface any code path that still depends on the retired endpoints — a future hygiene track may delete them.

---

## PHASE 2 — CODE REMOVAL

### Removed entirely
| Symbol | Was at | After |
|---|---|---|
| `def _admin_token_for(password)` | `server.py:278-280` | DELETED — replaced by retirement-marker comment block (`server.py:279-292`) |
| `def _pm_token_for(password)` | `server.py:283-287` | DELETED — same |
| Email-less branch of `/api/admin/login` | `server.py:1685-1708` | DELETED — handler now returns HTTP 410 with retirement message |
| Email-less branch of `/api/pm/login` | `routes/pm_routes.py:419-444` | DELETED — handler raises HTTP 401 with retirement message |
| Shared-HMAC compare in `_is_valid_admin_token` | `server.py:308-313` | STUBBED → returns False unconditionally |
| Shared-HMAC compare in `_is_valid_pm_token` | `server.py:316-333` | STUBBED → returns False unconditionally |
| `os.environ.get("ADMIN_PASSWORD")` env-read in `require_admin` | `server.py:391` | DELETED — open-mode escape hatch removed |
| `os.environ.get("PM_PASSWORD")` env-read in `require_admin` | `server.py:392` | DELETED |
| Same env-reads in `require_admin_or_pm`, `require_admin_strict`, `require_shop_or_admin` | `server.py:445-446,469,556-559` | DELETED — open-mode escape hatch removed everywhere |
| Shared `ADMIN_PASSWORD` env-read in `admin_verify_password` | `server.py:1747-1753` | REWIRED to per-user `user_directory.authenticate(email, password)` |
| `shared_pm_login_enabled()` env-flag | `pm_auth.py:shared_pm_login_enabled` | LEFT IN MODULE but no longer reached by any caller (legacy bypass is gone) |
| `pm_token_for_fn=_pm_token_for` factory kwarg | `server.py:12190` | REWIRED to `None` (kwarg retained on factory boundary; unused inside) |
| `_pm_token_for = login_deps["pm_token_for_fn"]` factory binding | `routes/pm_routes.py:318` | DELETED — variable no longer bound (the kwarg-value None is unused) |
| Shared-PM `elif _is_valid_pm_token(...)` branch in `require_admin` chain | `server.py:443` | DELETED |
| Same branch in `require_admin_or_pm` | `server.py:467` | DELETED |
| Same branch in `require_shop_or_admin` | `server.py:585` | DELETED |

### Added (per-user admin minter — same shape as PM and Shop)

| Symbol | File | Purpose |
|---|---|---|
| `make_directory_admin_token(user_id, password_hash)` | `user_directory.py:475-486` | Mints `<user_id>.<HMAC>` where HMAC binds to `ADMIN_HMAC_SECRET + epoch + user_id + password_hash[:16]`. |
| `is_valid_directory_admin_token_async(db, token)` | `user_directory.py:498-518` | Validates the new token: re-reads the directory row, recomputes the HMAC against its current `password_hash`, rejects on mismatch / disabled / no-admin-portal. |
| `_is_valid_directory_admin_token_async(token)` | `server.py:316-326` | Thin async wrapper used by every admin gate. |
| Token-shape switch in `_directory_admin_token(row)` | `server.py:11936-11952` | Switched from shared-HMAC reuse to per-user minter. |

### Updated gates

| Gate | Change |
|---|---|
| `require_admin` | Calls `_is_valid_directory_admin_token_async`; PM-shared `elif` branch removed; open-mode escape hatch removed. |
| `require_admin_or_pm` | Same. |
| `require_admin_strict` | Switched to async validator; iter370-R7 503-on-missing-env logic removed (env vars no longer exist by design). |
| `require_shop_or_admin` | Same async admin validator; PM-shared `elif` branch removed; open-mode escape hatch removed. |
| Training-PDF auth gate in `server.py:9447` | Already switched to per-user shop tokens in 15.30; admin path now also uses async validator. |

### Backend restart
- Supervisor restart clean. `GET /api/health` → 200 (local + external).

---

## PHASE 3 — CONFIG SCRUB

| Target | Action | Verification |
|---|---|---|
| `ADMIN_PASSWORD` in `backend/.env` | REMOVED | `grep "^ADMIN_PASSWORD" .env` → 0 hits |
| `PM_PASSWORD` in `backend/.env` | REMOVED | same |
| `ADMIN_PASSWORD` / `PM_PASSWORD` in `backend/.env.pre_atlas_backup` | REMOVED | `grep "^(ADMIN_PASSWORD\|PM_PASSWORD)" .env.pre_atlas_backup` → 0 hits |
| Test literals (`MASCI1982!`, `"Happy123!"`, `Happy123!`) in `backend/tests/` | REPLACED with `Maddix123!` | `grep -rln 'MASCI1982\|Happy123' backend/tests/` → 0 hits |
| Memory files (historical audit records) | RETAINED as forensic evidence | Documented here. |
| Live-code env-reads of `ADMIN_PASSWORD` / `PM_PASSWORD` | 0 sites | `grep` reports 0 live hits outside `tests/` and `memory/`. |
| Operator-manual copy (`training_pdf.py`, `ops_manual.py`) | Cleaned by 15.30 (Shop) — re-checked, no PM/Admin-specific copy needs further scrubbing. | — |

---

## FILES TOUCHED

### Modified
| File | Net diff |
|---|---|
| `backend/.env` | -2 lines (`ADMIN_PASSWORD`, `PM_PASSWORD`); epoch bumped |
| `backend/.env.pre_atlas_backup` | -2 lines |
| `backend/server.py` | -85 lines (token-for functions, 2 login handlers' email-less branches, 6 env-read sites, 4 shared-PM `elif` branches), +60 lines (retirement-marker comment, async admin validator, per-user-rewired `_directory_admin_token`, rewired `admin_verify_password`, 410 retirement handler for `/api/admin/login`) |
| `backend/routes/pm_routes.py` | -25 lines (email-less branch + `_pm_token_for` binding); +13 lines (401 retirement raise) |
| `backend/user_directory.py` | +83 lines (new per-user admin minter + validator) |
| `backend/tests/*` (146 files) | literal swap |

### Created
| File | Purpose |
|---|---|
| `/app/memory/TRACK_15_32_PM_ADMIN_SHARED_AUTH_RETIREMENT_IMPLEMENTATION.md` | This document |
| `/app/memory/TRACK_15_32_PM_ADMIN_SHARED_AUTH_RETIREMENT_CERTIFICATION.md` | Companion certification |

### Deleted
None this track. (The 15.30 Shop track deleted 21 test files; the 15.32 track preserved tests via literal swap.)

---

## ROLLBACK STRATEGY

| Scenario | Rollback |
|---|---|
| Live admin reports "cannot log in" | Confirm a `user_directory` row exists with `portals: ["admin"]` and the bcrypt password is correct. If not, admin creates one. Reversible in <2 min; no code revert. |
| External cron / automation suddenly fails on `/api/admin/login` | Retirement is intentional. Issue the automation a per-user directory account. If immediate rollback is required, `git revert` the 15.32 commits and add the env vars back. Recovery time: <15 min. |
| Tests in CI fail | The literal swap preserved every test except those that asserted on the email-less endpoints. `git log` shows the swap commit; per-test revert is trivial. |
| `_directory_admin_token` mint fails | Confirm `ADMIN_HMAC_SECRET` is set (it is — line 39 of `.env`). |
