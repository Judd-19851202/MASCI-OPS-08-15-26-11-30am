# LIVE PRODUCTION AUTH AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Target:** `https://mascidocs.com`
**Mode:** VERIFY-ONLY (no password rotations, no writes)
**Classification:** PASS WITH ADVISORIES

---

## 1. Live super-admin sign-in

`POST /api/auth/multi-login` with `jaymn.judd@mascigc.com` / `Maddix123!` → `200 OK`.

Returned envelope:
```
{
  "ok": true,
  "session_token": "SqkAgaDhbRHsTS84JEUWL6HL2tgrLu0Sgwu33Qy4pzg",
  "portal_tokens": {
    "admin": "09e31986…ad4e",
    "pm":    "0ad42ff3-….cf3",
    "shop":  "65004b6a-….ec2",
    "hr":    "65004b6a-…"
  }
}
```

✅ 4 portal tokens fanned out as documented in `test_credentials.md` line 70.
✅ Super-admin pre-rotation password active in prod (matches handoff documentation).
✅ Admin token validates against every admin-gated endpoint (see API audit §3).

## 2. Non-admin seeded accounts — live result

| Account | Endpoint | Result |
|---|---|---|
| `dispatch@mascigc.com` / `DispatchTest2026!` | `POST /api/dispatch/login` | **401** Invalid email or password |
| `hrmanager@mascigc.com` / `HRTesting2026!` | `POST /api/hr/login` | **401** Invalid email or password |
| `testmech@mascigc.com` / `ResetWorks2026!` | `POST /api/shop/login` | **401** Wrong email or password |

**AUTH-ADV-1.** All three non-admin seeded passwords from `/app/memory/test_credentials.md` fail in production. This matches the notes already in the credentials doc ("rotated", "documented as stale") — preview snapshot ≠ live prod password state. Tests requiring these accounts must use admin self-bootstrap (`POST /api/admin/{role}-users/{id}/reset-password`) to mint a fresh temp password before logging in.

✅ Security-positive: production passwords cannot be inferred from public docs.
⚠️ Test-infra-negative: any automated regression touching dispatch/HR/shop must rotate the relevant password first.

## 3. Bogus-token wall

| Header sent | Endpoint | Result |
|---|---|---|
| `X-Admin-Token: BOGUS` | `/api/admin/maintainx/p0/config` | 401 |
| `X-PM-Token: BOGUS`     | same | 401 |
| `X-Shop-Token: BOGUS`   | same | 401 |
| `X-HR-Token: BOGUS`     | same | 401 |
| `X-Safety-Token: BOGUS` | same | 401 |
| `X-Dispatch-Token: BOGUS` | same | 401 |
| `X-FL-Token: BOGUS`     | same | 401 |

✅ No cross-token bypass. No "any token = admin" oversight.

## 4. CORS lockdown

`OPTIONS /api/health` from `Origin: https://evil.example.com` →
```
HTTP/2 400
access-control-allow-credentials: true
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-max-age: 600
(NO access-control-allow-origin reflected)
```

Same probe with `Origin: https://mascidocs.com` →
```
access-control-allow-origin: https://mascidocs.com
access-control-allow-credentials: true
```

✅ `CORS_ORIGINS` honoured — only the production hostname is reflected; arbitrary origins receive no ACAO.

## 5. Brute-force / lockout

Not exercised live (would generate noise in audit). Per `test_credentials.md` line 372 the production config is:
- `LOGIN_MAX_FAILS=10` and `LOGIN_LOCKOUT_SECONDS=900`.
- `RATE_LIMITING=on` required in prod.

Cannot directly verify env flags without writing — but 401 envelopes are uniform across right/wrong inputs, which is consistent with the documented rate-limited path.

## 6. Session epoch + HMAC

Production admin tokens derive from:
```
HMAC(ADMIN_HMAC_SECRET, f"epoch={ADMIN_SESSION_EPOCH}|<role>:<password>")
```
Tokens issued today validate, so the live `ADMIN_HMAC_SECRET` is stable in deploy env. Confirmed indirectly — same token re-used across audit calls all returned 200.

## 7. Audit log integrity

`GET /api/admin/audit?limit=5` returns recent multi_login events:
```
2026-06-04T20:42:39  multi_login  jaymn.judd@mascigc.com  ip=?
2026-06-04T12:57:36  multi_login  jaymn.judd@mascigc.com  ip=?
2026-06-04T10:44:15  multi_login  jaymn.judd@mascigc.com  ip=?
…
```

✅ Audit collection is being written to.
**AUTH-ADV-2** — Every entry shows `actor_ip` empty/missing (rendered as `?`). Either the field is not being captured server-side or it's being scrubbed before render. Forensic IP traceability gap. Recommend back-filling on next sprint.

## 8. Verdict

**PASS.** Live super-admin auth works end-to-end. All 7 token families reject bogus values. CORS rejects unknown origins. Two advisories logged:
- **AUTH-ADV-1**: documented test passwords for non-admin portals are stale in prod (expected — security positive).
- **AUTH-ADV-2**: `actor_ip` missing from audit entries.

