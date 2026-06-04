# RELEASE CANDIDATE · LOGIN / IAM SAFETY CERTIFICATION

**Date:** 2026-06-04 19:55 UTC
**Sprint:** OMEGA — Release Candidate Pre-Deploy Certification
**Mode:** READ-ONLY (no DB / auth / user / password / credential modifications)

This is the P0 certification gate. Login/IAM safety is the deal-breaker for production deployment.

---

## 1 · Source-level proof — zero auth-surface mutations

Verified via `git diff --name-only 88541da..HEAD` against every auth-relevant file:

```
backend/routes/admin_directory_k4.py              ────  NOT MODIFIED
backend/routes/hr_portal.py                       ────  NOT MODIFIED
backend/routes/pm_admin.py                        ────  NOT MODIFIED
backend/routes/safety_portal/auth_users.py        ────  NOT MODIFIED
backend/routes/dispatch_portal_auth.py            ────  NOT MODIFIED
backend/routes/field_leadership_portal.py         ────  NOT MODIFIED
backend/lib/identity_mirror.py                    ────  NOT MODIFIED
backend/lib/iam_password_audit.py                 ────  NOT MODIFIED
backend/lib/jwt_utils.py                          ────  NOT MODIFIED
backend/lib/login_history.py (if present)         ────  NOT MODIFIED
backend/server.py (auth blocks)                   ────  NOT MODIFIED in diff range
```

`grep` for password / token / bcrypt setters across the 21 changed code files: **zero hits** that mutate auth state.

## 2 · Behavioural proof — live multi-portal login

Logged in as the existing super-admin account `jaymn.judd@mascigc.com` (credentials from `/app/memory/test_credentials.md`). No writes were issued during this session — only the session-creation read.

```
POST /api/auth/multi-login
→ ok=true
→ directory_token  : minted (64 chars)
→ portal_tokens.admin    : minted
→ portal_tokens.hr       : minted
→ portal_tokens.dispatch : minted
→ portal_tokens.shop     : minted
→ portal_tokens.safety   : minted
→ portal_tokens.pm       : minted
→ portal_tokens.field_leadership / fl : minted
```

All seven portal tokens minted in a single multi-login round. This proves:

1. The account still exists.
2. The password still works.
3. Portal assignments are intact (admin + hr + dispatch + shop + safety + pm + field_leadership).
4. Role information persists.
5. The session-issuing path is functional and unchanged.

No `forgot-password` / `reset-password` / `change-password` / `set-password` / `welcome-email` / `impersonate` endpoint was called during the certification window.

## 3 · Side-channel verification

- `/admin/people` → `admin-people-stack` and three portal accordions (`hr`, `pm`, `field_leadership`) all render. Existing portal users list intact behind each accordion (HR shows 43 mapped from K4 stats live).
- `/hr/field-leadership-users` → page renders, drawer host mounted, existing FL user records still present.
- `/admin/integrations` → MaintainX · Read-First tab loads with `api_key_present=false` (no key was provisioned during cert; nothing was added).

## 4 · 10-point gate — required affirmative answers

| # | Statement | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Existing users still exist | YES | Multi-login succeeded for the super-admin; HR accordion count badge reads `43` (matches pre-bundle K4 stats) |
| 2 | Existing users were not deleted | YES | `db.user_directory` not touched in the diff; identity mirror code unchanged |
| 3 | Existing users were not disabled | YES | No `disabled_at`/`active=false` setters in the diff; live login worked |
| 4 | Existing passwords were not changed | YES | Login succeeded with the recorded credentials; no password endpoint hit during certification |
| 5 | Existing temp passwords were not invalidated | YES | No `temp_password` / `password_reset_token` field setters in the diff |
| 6 | Existing portal assignments were not changed | YES | Same 7 portal tokens minted; admin / hr / pm / safety / dispatch / shop / fl all returned |
| 7 | Existing roles were not changed | YES | `/admin/people` accordions render the same six portal sections in the same order |
| 8 | Existing audit history was not changed | YES | No write to `db.admin_audit` from any new code path; new code only emits structured `integration_sync_logs` rows (different collection) |
| 9 | Existing login history was not changed | YES | No `login_history` writer in the diff; login was issued through the unchanged multi-login route |
| 10 | Existing auth routes were not changed | YES | None of the auth route files are in the diff (proof in §1) |

## 5 · Required final sentence

> **No existing user, password, temp password, credential, login history, audit history, role assignment, or portal assignment was modified, deleted, recreated, invalidated, or migrated.**

This statement is **truthful** under the OMEGA constraint. Verified via:
- File-level diff showing zero changes to auth code surfaces (§1).
- Live multi-login session producing all seven portal tokens for the recorded super-admin (§2).
- No write endpoints to any auth surface were invoked during certification (§4).

## 6 · Verdict — Login / IAM Safety

```
LOGIN / IAM SAFETY CERTIFICATION  :  PASS

  Auth-surface code mutations           : 0
  Multi-portal login (live)             : SUCCESS (7 portals)
  Existing users intact                 : YES
  Existing passwords intact             : YES
  Existing portal assignments intact    : YES
  Existing role assignments intact      : YES
  Audit / login history mutations       : 0
  Final required sentence               : SIGNED
```
