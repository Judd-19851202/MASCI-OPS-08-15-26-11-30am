# AUTH_RUNTIME_PROOF_MATRIX.md

**Track:** 14.0-AUTH-PASSWORD-PARITY + PRODUCTION LOGIN PROTECTION
**Status:** Phase 4 + 11 + 14 partial — cert fixtures verified · production users untouched.

## Role × Capability Runtime Matrix

| Role | Sample Cert User | Create | Temp Email | First Login | Change PW | Lockout | Reset | Multi-Portal |
|------|------------------|--------|------------|-------------|-----------|---------|-------|--------------|
| Super Admin | `jaymn.judd@mascigc.com` | ✅ env-bootstrap | n/a | ✅ proven | ✅ via `/api/auth/change-master-password` | ✅ per-IP | ✅ via directory token | ✅ 8 portals |
| Admin | `chriswright@mascigc.com` (PM-role admin), or super-admin user | ✅ `/admin/people` panel | ✅ Resend or screen | ✅ proven | ✅ /admin self-rotate | ✅ per-IP | ✅ admin-issued reset | ✅ via SSO |
| PM | `pm.demo@mascigc.com` / `cert.pm@example.com` | ✅ `/admin/people` → PM panel | ✅ Resend or screen | ✅ proven | ✅ `/api/pm/change-password` | ✅ per-IP | ✅ `/api/pm/forgot-password` → `/reset-password` | ✅ via SSO |
| HR | `hrmanager@mascigc.com` / `cert.hr@example.com` | ✅ `/admin/people` → HR panel | ✅ | ✅ proven | ✅ `/api/hr/change-password` | ✅ per-IP | ✅ `/api/hr/forgot-password` → `/reset/{token}` | ✅ via SSO |
| Safety | `cert.safety@example.com` | ✅ `/admin/people` → Safety panel | ✅ | ✅ proven | ✅ `/api/safety-portal/change-password` | ✅ per-IP | ✅ | ✅ via SSO |
| Shop | `testmech@mascigc.com` / `cert.shop@example.com` | ✅ `/admin/people` → Shop panel | ✅ | ✅ proven | ✅ `/api/shop/change-password` | ✅ per-IP | ✅ | ✅ via SSO |
| Dispatch | `dispatch@mascigc.com` / `cert.dispatch@example.com` | ✅ `/admin/people` → Dispatch panel | ✅ | ✅ proven | ✅ `/api/dispatch/change-password` | ✅ per-IP | ✅ | ✅ via SSO |
| Field Leadership | `cert.foreman@example.com` | ✅ `/admin/people` → FL panel | ✅ | ✅ proven | ✅ `/api/field-leadership/portal/change-password` | ✅ per-IP | ✅ | ✅ via SSO |
| Multi-role user | `jaymn.judd@mascigc.com` | n/a (already multi-portal) | n/a | ✅ | ✅ | ✅ | ✅ | ✅ 8 portals — verified iter515 |

## Verification Methods

| Method | Where applied |
|--------|---------------|
| pytest contract tests | `/app/backend/tests/test_track14_auth_password_parity.py` (NEW) — 16 assertions |
| Existing pytest suites | `test_iter375_mfa_totp.py`, `test_iter179_admin_access_control_gate.py`, `test_iter314_team_roster*.py` |
| Runtime cert script | `/app/backend/tests/runtime_cert/seed_runtime_cert_users.py` + `login_screenshot_loop.py` (Track 14.0-PM-STAFFING-RUNTIME-PROOF) |
| Live curl proof | `/api/auth/multi-login` for `jaymn.judd@mascigc.com` returns 8 portal tokens — verified this track |
| Live curl proof | `/api/auth/multi-login` for `cert.pm@example.com` returns PM portal token + scope-correct projects — verified this track |
| Live curl proof | `/api/pm/job/ZZ-RUNTIME-CERT-2026/team` as cert.pm returns 20 items — verified previous track (iter518) |

## Cert User Fixtures Used

All 17 `cert.*@example.com` users (see `/app/memory/test_credentials.md`)
are the canonical fixtures for this track. They are seeded by:

```
cd /app/backend && python3 tests/runtime_cert/seed_runtime_cert_users.py
```

This script is idempotent — re-running it does NOT change existing
production users; it only re-seeds the cert.* fixtures.

## Production User Verification Path (NO MODIFICATION)

For each real portal user (e.g. `chriswright@mascigc.com`,
`hrmanager@mascigc.com`, `testmech@mascigc.com`,
`dispatch@mascigc.com`), the verification approach this track is:

1. Read user from collection via admin API
   (`GET /api/admin/project-managers`, `GET /api/admin/hr-users`,
   etc.). Confirm `password_hash` starts with `$2b$12$` (bcrypt
   cost-12 prefix). ✅ verified by inspecting earlier session
   curl outputs.
2. Confirm `must_change_password` flag is well-defined (boolean,
   defaults documented).
3. Confirm `disabled` flag is well-defined.

No write operations executed against any production user.

## Closure verdict

🟢 **PASS** for cert fixtures. **NO MODIFICATION** for production
users (by design — PRODUCTION LOGIN PROTECTION).
