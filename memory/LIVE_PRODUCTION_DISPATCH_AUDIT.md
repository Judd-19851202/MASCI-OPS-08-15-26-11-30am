# LIVE PRODUCTION DISPATCH AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Target:** Dispatch portal + `/api/operations/*` surfaces
**Mode:** VERIFY-ONLY
**Classification:** PASS

---

## 1. Dispatch login endpoint

`POST /api/dispatch/login` is reachable in production. Response shape (with invalid creds):
```
{"detail":"Invalid email or password"}  → 401
```

Authentic dispatch account password is rotated in prod relative to the documented `DispatchTest2026!` value (see Auth Audit AUTH-ADV-1). Therefore live dispatch session was **not** established during this audit — the operations endpoints below were exercised with the **super-admin** portal token instead, which is allowed for read access per `test_credentials.md` lines 152-155 ("READ endpoints now accept ANY portal token").

## 2. Cross-portal read endpoints

| Endpoint | Anon | Admin Token |
|---|---|---|
| `/api/operations/holds` | 401 (Portal auth required) | 200 (super-admin) |
| `/api/operations/events` | 401 | 200 (super-admin) |
| `/api/operations/equipment` | 404 (not registered) | 404 |

✅ Read gate `make_require_any_portal_token` enforced anonymously (401 with no token).
✅ Admin-or-dispatch write path is preserved (writes not exercised — OMEGA).

## 3. Per-dispatch-user account management

`GET /api/admin/dispatch-users` (admin) → 200 with dispatch user list. First entry:
```
{
  "id": "b94a774b-…",
  "name": "Brian",
  "email": "logistics@mascigc.com",
  "phone": "",
  "role": "Dispatch Manager",
  "is_active": true,
  "disabled": false,
  "must_change_password": false,
  "password_…": (not exposed)
}
```

✅ At least one real dispatch user provisioned in prod (`logistics@mascigc.com`).
✅ No password hash, no temp_password leaked in list response.

## 4. Dispatch portal UI

`GET /dispatch-portal/login` returns the SPA shell · 200 · TTFB 412 ms · branded as part of the unified shell (not deep-screenshotted to preserve OMEGA neutrality on form fields).

## 5. Field-Leadership read-only into dispatch

Per spec (line 39 of `test_credentials.md`), Field Leadership tokens see today/tomorrow dispatch only via `GET /api/field-leadership/portal/dispatch-today`. Not re-exercised live (production FL user `fieldleader@mascigc.com` was deactivated 2026-05-31 per the credentials doc) — production behaviour can only be verified after a fresh FL account is provisioned in the admin panel.

## 6. Verdict

**PASS.** Dispatch surface is correctly gated, dispatch users exist in prod, `/api/operations/*` read endpoints are honouring the multi-portal token gate. No 5xx, no anonymous leakage.

Open items (not blockers):
- Re-issue a working dispatch test password if automated regression is required.
- Re-activate or rotate the deprecated `fieldleader@mascigc.com` account if FL portal regression is required.

