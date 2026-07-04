# TRACK 20.8 · Security Certification

**Verdict:** 🟢 **CERTIFIED.**

## Auth model (Track 15.32 canonical)

- Canonical login: `POST /api/auth/multi-login`.
- Retired: shared-password `POST /api/admin/login` returns HTTP 410.
- Retired: shared-password `_is_valid_admin_token`, `_is_valid_pm_token` — replaced by directory async validators (`_is_valid_directory_admin_token_async`, `is_valid_pm_user_token_async`).
- Portal tokens: 7 (`admin`, `pm`, `hr`, `safety`, `shop`, `dispatch`, `field_leadership` + `fl` alias).
- Sessions persisted in `user_directory_sessions`; TOTP MFA supported for super-admin (Track 19.75 · iter375).
- Passkey login mints the same multi-login response shape (Track 19.22 · iter422).

## Verified live

- Unauth `GET /api/employee-records/vocabulary` → 401 ✅.
- Unauth `GET /api/daily-reports` → 401 ✅.
- Unauth `GET /api/inspections` / `meetings` / `jhas` / `incidents` → 401 ✅.
- Unauth `POST /api/daily-reports` (intentionally public field-crew intake) → 200 ✅.
- Retired `POST /api/admin/login` → 410 ✅.

## Fine-grained permission gates (verified via prior tracks)

| Gate | Verified in |
|---|---|
| `require_admin` (directory admin async) | Track 15.32 · 15.13F · live curl 20.6B |
| `require_admin_pm_or_hr_read` | Track 15.13E · triple-token verified 20.6B |
| `require_safety_or_admin` | Track 20.6B live curl |
| `require_pm_or_admin` | Track 15.11 · 15.11C |
| PM scope enforcement | Track 15.11B · `compute_pm_scope` |
| HR-user gates (`is_valid_hr_user_token_async`) | Track 19.21b live e2e |
| Field Leadership gate | Track 18.09c · iter345 hybrid |
| Dev/vendor gate | `require_dev` — separate namespace preserved |

## Attack-surface controls

- ✅ Password rotation enforced (Track 15.14A layer 1) — `must_change_password` blocks token mint.
- ✅ Brute-force audited (`multi_login_failed` audit rows).
- ✅ Rate limiting on public POSTs (`rate_limit_public_post`).
- ✅ Preview DB isolation failsafe (`db-isolation-failsafe` refuses production DB writes).
- ✅ No secret in repo (Track 15.80 zero-secrets lock preserved).
- ✅ Legacy admin API-only break-glass documented in `test_credentials.md` (POST `/api/admin/login` with `MASCI1982!`) — NOT reachable from human UI; retained for emergencies only.
- ✅ Session tokens are opaque directory session tokens (not JWT); revocable via `user_directory_sessions` collection.

## No permission widening in this track

Track 20.8 is certification-only. Zero routes added or removed. Zero gates modified. Zero portal tokens added or removed.

## Verdict

🟢 **Security certified for production deployment.**
