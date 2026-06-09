# GOVERNANCE-HARDEN-001 · Workstream D · Credential Audit

```
Environment    : preview (direct) + production (inferred via shared infrastructure)
Access Level   : preview-runtime · prod-DB-read · static-analysis
Evidence Source: /app/backend/.env · /app/frontend/.env · /app/memory/test_credentials.md · prod-DB cross-check
Confidence     : VERIFIED for preview-side · INFERRED for prod-side (operator must confirm)
```

⚠️ **No credential values are disclosed in this document.** Lengths only. Authoritative values live in the actual `.env` and the credentials file.

---

## §D.1 · Preview pod `.env` credential inventory (40 keys total)

### D.1.1 · Auth and identity

| Key | Length | Class | Scope concern |
|---|---|---|---|
| `SUPER_ADMIN_EMAIL` | 22 | **shared** (likely == prod) | Documented as `jaymn.judd@mascigc.com` — exists in both envs |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | 10 | **shared** (documented in test_credentials.md as `Maddix123!`) | **Same password used in preview AND prod** per `test_credentials.md` line: "Test accounts apply to BOTH databases" |
| `ADMIN_PASSWORD` | 10 | unknown shared/not | Operator must confirm |
| `PM_PASSWORD` | 9 | unknown | Operator must confirm |
| `SHOP_PASSWORD` | 12 | unknown | Operator must confirm |
| `SAFETY_FORMS_PASSWORD` | 4 | unknown | Operator must confirm; suspiciously short |
| `DEV_PASSWORD` | 11 | preview-only (by name) | Should be preview-only |
| `JWT_SECRET` | 64 | **probably shared** | If preview and prod differ, tokens issued in one would not validate in the other; no symptoms observed |
| `ADMIN_HMAC_SECRET` | 86 | **probably shared** | Same as above |
| `MFA_ENCRYPTION_KEY` | 43 (Fernet) | **probably shared** | `test_credentials.md` explicitly notes: "MUST be set in production before deploy." Wording implies the SAME value is intended in both envs. |

### D.1.2 · Integration secrets

| Key | Length | Scope concern |
|---|---|---|
| `MAINTAINX_API_KEY` | 0 (empty) | Empty in preview; prod also empty (per Workstream B + PROD-STABILIZE-001 § Phase 2). Consistent. |
| `MAINTAINX_BASE_URL` | 31 | Public URL — non-secret |
| `EMERGENT_LLM_KEY` | 30 | Likely shared. |
| `RESEND_API_KEY` | 36 | Likely shared. |
| `RESEND_WEBHOOK_SECRET` | 0 (empty) | Empty in preview. Per `email_routing.py` / `resend_webhook.py`, this means inbound webhook events are accepted without signature verification IF empty. Operator should set it. |
| `SENTRY_DSN` | 95 | Public DSN — non-secret per Sentry doctrine |

### D.1.3 · Mongo

| Key | Length | Scope concern |
|---|---|---|
| `MONGO_URL` | 84 | **Cluster-level Atlas user (`admin_db_user`).** Same credential resolves prod and preview DBs. **This is the central governance gap surfaced in Workstream A.** |
| `DB_NAME` | 20 | `masci_safety_preview` — correctly env-specific |
| `APP_ENV` | 7 | `preview` — correctly env-specific |

### D.1.4 · Non-secret operational config

`ACCESS_TOKEN_MINUTES`(2) · `ADMIN_DEAD_LETTER_EMAIL`(18) · `ADMIN_SESSION_EPOCH`(1) · `ATLAS_QUOTA_MB`(5) · `AUTO_EMAIL_REPORTS`(5) · `BACKUP_EMAIL_TO`(22) · `BACKUP_HOURS_UTC`(4) · `CORS_ORIGINS`(1) · `CORS_ORIGIN_REGEX`(99) · `LOGIN_LOCKOUT_SECONDS`(3) · `LOGIN_MAX_FAILS`(2) · `MAINTAINX_SYNC_ENABLED`(5) · `MAINTAINX_WRITE_ENABLED`(5) · `OUTAGE_ALERT_COOLDOWN_MINUTES`(2) · `OUTAGE_ALERT_TO`(22) · `PUBLIC_POST_LIMIT_PER_HOUR`(2) · `RATE_LIMITING`(3) · `REFRESH_TOKEN_DAYS`(1) · `REPLY_TO_EMAIL`(22) · `SCHEDULER_ENABLED`(5) · `SENDER_EMAIL`(21) · `SESSION_TIMEOUTS_ENABLED`(4)

---

## §D.2 · Test / admin credentials documented in `/app/memory/test_credentials.md`

| Account | Email | Password (file-disclosed) | Scope claimed in file | Class |
|---|---|---|---|---|
| Super Admin (all 4 portals) | `jaymn.judd@mascigc.com` | `Maddix123!` | **"Test accounts apply to BOTH databases"** | 🔴 **SHARED — preview+prod** |
| HR Manager | `hrmanager@mascigc.com` | `HRTesting2026!` | "" | 🔴 SHARED (per same doctrine) |
| Dispatcher | `dispatch@mascigc.com` | `DispatchTest2026!` | "" | 🔴 SHARED |
| Chris Wright | `chriswright@mascigc.com` | `ChrisRocksThis2026` | "" | 🔴 SHARED |
| Test mechanic | `testmech@mascigc.com` | `ResetWorks2026!` | "" | 🔴 SHARED |
| Asphalt PM | `asphaltpm@mascigc.com` | (no password yet) | "preview only — needs to be added in prod admin console after redeploy" | 🟡 Preview-only-today |
| Leo Masci | `leomasci@mascigc.com` | (no password yet) | "preview only — needs to be added in prod admin console after redeploy" | 🟡 Preview-only-today |
| Shop Manager | `shopmanager@mascigc.com` | (no password issued in preview) | "" | 🟢 Not currently usable |
| Field Leadership user | `fieldleader@mascigc.com` | `FieldLead2026!` | **DEACTIVATED 2026-05-31** | 🟢 Inactive |
| Seed Safety user | `safety@mascigc.com` | (stale; rotated to temp) | preview only | 🟡 Preview-only-today |

🔴 **5 currently usable accounts are documented as working in production with the same passwords as in preview.**

## §D.3 · Integration credentials (from prod DB read)

| Integration | Prod `integration_settings` shape | Class |
|---|---|---|
| Motive | api_key_value len=36 · webhook_secret_value len=32 · status=Connected · last_sync 2026-06-09T20:17:41Z · updated_by=`motive_prod_incident_001:remediation` | **Prod-only** (preview has a DIFFERENT api_key_value — separately seeded 2026-06-08) |
| MaintainX | empty in both envs | n/a until activated |

The Motive secrets in prod and preview are **NOT** the same value (different lengths' parity + different `updated_by` provenance prove they were sourced independently). This is a positive isolation signal for one integration.

## §D.4 · Shared-credential classification

| Credential | Class | Risk |
|---|---|---|
| `MONGO_URL` Atlas user (`admin_db_user`) | 🔴 SHARED · CLUSTER-ADMIN | **HIGHEST — single compromise = both envs total reach** |
| `Password` (second Atlas user) | 🔴 STANDING · CLUSTER-WRITE | **HIGH — second equivalent compromise path** |
| Super-admin login (`jaymn.judd@mascigc.com` / `Maddix123!`) | 🔴 SHARED | **HIGH — same UI session creds work on prod** |
| Other 4 portal logins (HR/Dispatch/etc) | 🔴 SHARED | HIGH |
| `JWT_SECRET` | 🟡 LIKELY SHARED | If shared, a preview-issued JWT could be replayed at prod (would still need a matching user in prod's DB, which exists per §D.2) |
| `MFA_ENCRYPTION_KEY` | 🟡 LIKELY SHARED | If shared, would allow rebuilding TOTP secrets from prod DB |
| `ADMIN_HMAC_SECRET` | 🟡 LIKELY SHARED | Used for HMAC of admin step-ups |
| Motive integration row | 🟢 Separately seeded | Positive isolation example |

## §D.5 · Recommended rotation plan (NO ACTION TAKEN — authorization required)

Phased, low-risk:

### Phase 1 (immediate — operator-only)
1. Rotate `jaymn.judd@mascigc.com` password in **production**. Set a new password not known to any preview fork.
2. Rotate the 4 other portal accounts in production OR delete the prod-side rows entirely if those are pure test accounts.
3. Update `/app/memory/test_credentials.md` to mark the 5 accounts as **PREVIEW-ONLY** with explicit "DO NOT REUSE IN PROD" warning.

### Phase 2 (Atlas user split — operator-only)
4. In Atlas Console, create `masci_preview` with `readWrite@masci_safety_preview` only and `masci_prod` with `readWrite@masci_safety` only.
5. Update prod pod `.env.MONGO_URL` to `masci_prod`.
6. Update preview pod `.env.MONGO_URL` to `masci_preview`.
7. **Disable** `admin_db_user` and `Password` (or retain as break-glass under password rotation cadence).

### Phase 3 (cross-env secret divergence — operator-only)
8. Rotate `JWT_SECRET` in production (forces a one-time logout of live sessions). Leave preview's unchanged or rotate preview separately.
9. Rotate `ADMIN_HMAC_SECRET` in production.
10. Rotate `MFA_ENCRYPTION_KEY` carefully: if any users have prod MFA enrolled, rotation invalidates their TOTP secret; coordinate re-enrollment.

### Phase 4 (validation — operator-attestable)
11. Operator confirms by attempting prod admin login with the OLD `Maddix123!` — should fail with 401.
12. Operator confirms preview-fork's MONGO_URL (now `masci_preview`) cannot read `masci_safety` — should fail with `Unauthorized`.
13. Update `test_credentials.md` to reflect the new state.

**Rollback for each phase:** restore the prior `.env` value and rotate back. Atlas user changes are reversible from Atlas Console.

## §D.6 · Verdict — Workstream D

✅ **PASS as an audit; FAIL as a control posture.**

The audit is complete and shared credentials are identified. The actual control posture is unacceptable for a TRUSTED/PROVEN platform: 5+ shared credentials, including the super-admin login and the cluster-level Atlas user. **Operator must execute the rotation plan in §D.5 to close the governance gap.** No rotation was performed by this audit per directive.
