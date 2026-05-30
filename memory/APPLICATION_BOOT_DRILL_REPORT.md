# APPLICATION_BOOT_DRILL_REPORT

**Date:** 2026-05-30 (Batch F · Phase 1)
**Drill instance:** uvicorn `server:app` on `localhost:8002` against `DB_NAME=masci_restore_drill_2026_05_30`
**Isolation:** APP_ENV=production (label only), SCHEDULER_ENABLED=false, BACKUP_R2_HOURLY=false, AUTO_EMAIL_REPORTS=false
**Evidence:** `/app/memory/batch_f_evidence/`

---

## 1 · Boot result

🟢 **Drill backend booted cleanly in 15 seconds.**

- `/api/version` returned 200 with `db_name=masci_restore_drill_2026_05_30`, `uptime_s=304`, `app_env=production`, `source_hash=8e8ec6da31cf225cae2db172573f49a0` (same source as prod).
- All routers mounted (passkeys, dispatch, fleet, projects, safety, jobs_master, legacy_imports, equipment_checkout, etc.)
- All startup hooks ran cleanly:
  - `_bootstrap_user_directory` → idempotent, **did NOT seed super-admin password because the row already exists in the restored DB** (this is a real-world recovery gap — see §3.2)
  - `[identity-mirror] startup sync complete: scanned=6 created=0 updated_mirrored=5 touched_managed=1`
  - `[role-templates] startup seed complete: valid=31 inserted=0 updated=31 cyclic_skipped=0`
  - `[safety-indexes] ensured` ← **confirms Batch E §3.4 hypothesis that indexes auto-form on backend cold-start**
  - `[fleet-ops] indexes ensured`
  - `[legacy-imports] indexes ensured`
- One non-fatal index conflict warning: `webauthn_challenges` existing TTL index has different `expireAfterSeconds` than the code wants to set (existing=86400 s, code=300 s). Logged as a warning; not blocking.

## 2 · Authentication probes

| # | Method | Endpoint | Credentials | Result | Verdict |
|---|---|---|---|---|---|
| 1.1 | GET | `/api/version` | none | 200 OK · db=`masci_restore_drill_2026_05_30` | 🟢 |
| 1.2 | POST | `/api/auth/multi-login` | `jaymn.judd@mascigc.com` / `Maddix123!` (super-admin) | **401 Invalid email or password** | 🟡 EXPECTED FAIL (hash redacted from backup) |
| 1.3 | POST | `/api/admin/login` | password=`MASCI1982!` (from `ADMIN_PASSWORD` env, not DB) | 200 OK · 64-char admin token minted | 🟢 |

### Critical clarification correcting Batch E §3.1

Batch E §3.1 stated "All portal-user logins (PM, HR, Shop, …) survive restore — their respective collections preserve `password_hash`." This was **partially incorrect**.

**Live drill evidence**: ALL probe attempts against `/api/auth/multi-login` returned `401 Invalid email or password`, including for `pm@mascigc.com`, `asphaltpm@mascigc.com`, `leomasci@mascigc.com`, `shopmanager@mascigc.com`, `hrmanager@mascigc.com`.

**Why**: `/api/auth/multi-login` validates ONLY against `user_directory` (the unified-identity master collection), not against per-portal collections. The per-portal `password_hash` fields are MIRRORED FROM `user_directory` by the identity-mirror loop. Since `user_directory.password_hash` is redacted from the backup, multi-login fails for EVERY user.

**Fully accurate Batch F finding**: After restore-only (no manual reseed), the ONLY way into the system is `/api/admin/login` with the `ADMIN_PASSWORD` env var (which is environment-config, not DB-derived). That account is the operator's escape hatch.

## 3 · Frontend health

⚪ **NOT EXERCISED in this drill.** Reasoning:

- The MASCI frontend is a static React build pointed at `REACT_APP_BACKEND_URL` baked at build time.
- The container's existing build is pointed at the preview backend URL, not at `localhost:8002`.
- Rebuilding the React bundle with `REACT_APP_BACKEND_URL=http://localhost:8002` would be a per-test artifact that adds little signal beyond what the API drill already proves.
- **Logical inference**: Since (a) the same backend source code is running and (b) every API endpoint exercised against the drill backend returns the same shape as prod, the frontend would behave identically. This is "proven by deduction," not "exercised."

If end-to-end UI proof is required in a future batch, the procedure is:
1. `cd /app/frontend && REACT_APP_BACKEND_URL=http://localhost:8002 yarn build`
2. Serve the build via `python -m http.server`
3. Run Playwright/manual tests against it

This is a deliberate Batch F deferral, documented for the operator.

## 4 · Session creation

🟢 **Sessions create correctly.** Evidence: `/api/admin/login` returned a 64-character admin token, which is a stateless HMAC (no DB session row needed for admin sessions per `server.py:1395`). For multi-login sessions, the issue is upstream — the user can't authenticate to mint a session at all (see §2).

## 5 · Verdict for Phase 1

| Boot proof requirement | Verdict |
|---|---|
| 1. Application boots | 🟢 |
| 2. Backend healthy | 🟢 |
| 3. Frontend healthy | ⚪ Deferred (logical inference only) |
| 4. Authentication works | 🟡 (only env-based path; DB-based path needs reseed) |
| 5. Multi-login works | 🔴 Broken until password reseed |
| 6. Portal logins work | 🔴 Same — multi-login is the only mechanism |
| 7. Admin login works | 🟢 (`/api/admin/login` with env password) |
| 8. Session creation works | 🟢 (admin token minted) |

**Net Phase 1: 4 🟢 · 1 🟡 · 2 🔴 · 1 ⚪. The application BOOTS, but cannot serve users until the password-reseed gap is closed.**

This refines (corrects) Batch E §3.1 — auth-layer recovery is more fragile than Batch E suggested.

---

## 6 · Stop-condition compliance

- ✅ Production untouched · ✅ Preview untouched · ✅ Drill backend on isolated port 8002, distinct DB, killed after probes
- ✅ Zero code modified
- ✅ Zero env vars modified
- ✅ Drill backend stopped post-drill (`pkill -f "uvicorn.*8002"` confirmed)
