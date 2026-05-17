# MASCI Hub — Phase 2 Hardening Runbook

> **Active runbook** for Phase 2 operational hardening (Sentry, session
> timeouts, R2 lifecycle, restore drills, Admin/HR audit).
>
> **Milestone close-out tracking lives in `/app/memory/PHASE2_MILESTONE_CLOSEOUT.md`** — that doc is the canonical sign-off ledger for when Phase 2 is closed and the Training / Help / Operational Guidance initiative is unblocked. This runbook is the implementation status; the close-out doc is the gate.
>
> Pairs with:
>
> - `/app/memory/PHASE2_MILESTONE_CLOSEOUT.md` — sign-off ledger
> - `/app/memory/SENTRY_PRODUCTION_CUTOVER.md` — Sentry production runbook
> - `/app/memory/R2_LIFECYCLE_ACTIVATION.md` — R2 activation runbook
> - `/app/memory/DATA_PORTABILITY.md` — backup export system
> - `/app/memory/AUTHORIZATION_MATRIX.md` — Admin/HR access classification
> - `/app/memory/AUTH_SESSION_AUDIT.md` — session-boundary state
> - `/app/memory/RESTORE_DRILL.md` — restore drill procedure
> - `/app/memory/R2_RETENTION_AUDIT.md` — R2 lifecycle state
> - `/app/memory/DEPLOY_CHECKLIST.md` — pre-deploy gate

---

## 1. Sentry (Initiative 1)

### Status
- ✅ Backend scaffolded (`/app/backend/sentry_init.py`)
- ✅ Frontend scaffolded (`/app/frontend/src/lib/sentryInit.js`)
- ✅ PII scrubber active (passwords, tokens, secrets, api_keys, Authorization/Cookie headers)
- ✅ Release identifier wired to `/api/version` `source_hash` — **frontend + backend share the same release string deterministically**
- ✅ Auto session tracking enabled (release health works out of the box)
- ✅ Tests: `test_iter186_phase2_hardening.py::test_sentry_*` (3 tests)
- ✅ **Preview DSNs wired 2026-02-XX** (`SENTRY_DSN` + `REACT_APP_SENTRY_DSN` in `.env`s, `SENTRY_ENV=preview`)
- ✅ **SDKs installed:** backend `sentry-sdk[fastapi]==2.60.0`; frontend `@sentry/react==10.53.1`
- ✅ **Release identifier verified live** — backend `/api/version` and frontend Sentry init both report `release=39ed7cf313e808e76a450ffe99e1c683` (full 32-char source_hash). Frontend pulls release from `/api/version` at boot — no rebuild needed when source_hash changes.
- ✅ **Controlled verification 2026-02-XX:** backend `capture_message` + `capture_exception` succeeded; frontend test error fired via global error handler succeeded. Both projects (`masci-backend-python`, `masci-frontend-javascript-react`) received events under `environment=preview`.
- 🛑 **Production DSNs NOT yet configured** — operator must add `SENTRY_DSN` + `REACT_APP_SENTRY_DSN` to the production env when ready.

### Required env vars (set in `/app/backend/.env` and `/app/frontend/.env`)
| Var | Default | Notes |
|---|---|---|
| `SENTRY_DSN` | _unset_ | Backend DSN. If empty, Sentry is a no-op. |
| `REACT_APP_SENTRY_DSN` | _unset_ | Frontend DSN. If empty, no-op. |
| `SENTRY_ENV` | `production` | Environment tag. Set to `staging` for staging, `local` for dev. |
| `REACT_APP_SENTRY_ENV` | `production` | Same, frontend. |
| `SENTRY_TRACES_RATE` | `0` | Performance sampling rate (0–1). Start at 0; enable later. |
| `SENTRY_PROFILES_RATE` | `0` | Profiling sample rate. |
| `REACT_APP_SENTRY_TRACES_RATE` | `0` | Frontend performance. |
| `REACT_APP_SENTRY_REPLAY_RATE` | `0` | Session Replay sampling. Start at 0. |

### Activation steps (when DSNs are ready)
1. Create two Sentry projects (or one with separate envs): `masci-hub-backend`, `masci-hub-frontend`.
2. Copy DSNs into the respective `.env` files.
3. `sudo supervisorctl restart backend` (backend picks up env on restart).
4. Rebuild frontend (`yarn build` or trigger redeploy) — `REACT_APP_*` vars are baked at build time.
5. Verify via `GET /api/version` — `sentry.enabled` must be `true`.
6. Trigger a controlled error in staging first, then production.

### Alert rules to configure in Sentry UI (after first events arrive)
See **`/app/memory/SENTRY_PRODUCTION_CUTOVER.md § 5`** for the 5 recommended alert rules — that doc is the canonical production cutover runbook.

### Production cutover
See **`/app/memory/SENTRY_PRODUCTION_CUTOVER.md`** — single source of truth. Tracks the cutover sign-off in § 10.

### Rollback
Unset `SENTRY_DSN` (and `REACT_APP_SENTRY_DSN`) → restart → Sentry goes back to no-op.

---

## 2. Session / portal hardening (Initiative 4)

### Status
- ✅ Mongo-backed middleware (`/app/backend/session_timeout.py`)
- ✅ Tiered defaults: Admin/HR 15/4, Operations 30/8, Field 60/12
- ✅ TTL index on `session_activity.last_seen_at` (30 days) — no unbounded growth
- ✅ Token format unchanged (zero forced re-login at deploy time)
- ✅ Health/version/login endpoints exempt
- ✅ Tests: `test_iter186_phase2_hardening.py` (5 unit) + `test_iter186b_session_timeout_middleware.py` (8 integration) + `test_iter187_admin_hardening_5b.py` (9 integration) + `test_iter188_deterministic_token_relogin.py` (9 regression — admin/HR/PM)
- ✅ **ACTIVE in preview** (`SESSION_TIMEOUTS_ENABLED=true`)
- ✅ **Deterministic-token defect fixed iter188 (2026-02-XX)** — login endpoints now reset/upsert `session_activity` on successful auth; logout clears the row. 202/202 auth + hardening tests passing.
- 🛑 **Production flag remains OFF per operator directive.** Next step: ≥24h preview soak, then production flip and first-cycle monitoring.

### Required env vars
| Var | Default | Notes |
|---|---|---|
| `SESSION_TIMEOUTS_ENABLED` | `false` | Master switch. Anything else → enforcement disabled. |
| `SESSION_IDLE_MIN_ADMIN_HR` | `15` | Admin/HR idle minutes |
| `SESSION_ABS_HOUR_ADMIN_HR` | `4` | Admin/HR absolute hours |
| `SESSION_IDLE_MIN_OPERATIONS` | `30` | PM/Shop/Dispatch/Safety idle |
| `SESSION_ABS_HOUR_OPERATIONS` | `8` | PM/Shop/Dispatch/Safety absolute |
| `SESSION_IDLE_MIN_FIELD` | `60` | Field Leadership idle |
| `SESSION_ABS_HOUR_FIELD` | `12` | Field Leadership absolute |

### Activation steps
1. Add `SESSION_TIMEOUTS_ENABLED=true` to `/app/backend/.env`.
2. `sudo supervisorctl restart backend`.
3. Verify via `GET /api/version` — `session_timeouts.enabled` must be `true` and the tier values you expect.
4. Existing logged-in users get a "fresh" `session_activity` row on their next request (last_seen_at = now), so no one is forced out at the flip. Real expiry kicks in only after `last_seen_at` reaches the configured idle TTL.

### Rollback
Set `SESSION_TIMEOUTS_ENABLED=false` (or unset it) → restart → enforcement disabled. The `session_activity` collection auto-expires within 30 days.

### § 2a — Deterministic-token defect (RESOLVED iter188)

The defect surfaced during the 2026-02-XX doc reconciliation pass: HMAC tokens are deterministic per (epoch, namespace, password), so the `session_activity` row keyed by `sha256(token)` survived across logins. Login endpoints were exempt from the middleware but did not reset the row — so any operator idle past their tier's idle limit was permanently locked out.

**Fix (iter188):** every login endpoint now calls `session_timeout.reset_session_activity(db, token, tier)` on success, which `$set`s `first_seen_at = last_seen_at = now`. Admin and PM logouts additionally call `clear_session_activity(db, token)` to delete the row.

**Endpoints updated:** `/api/admin/login`, `/api/hr/login`, `/api/pm/login` (per-user + shared), `/api/shop/login` (per-user + shared), `/api/safety/login`, `/api/dispatch/login`, `/api/auth/multi-login`, `/api/auth/issue-portal-token`.

**Regression coverage:** 9 tests in `test_iter188_deterministic_token_relogin.py` covering fresh login, post-idle re-login, multi-login cycles, browser refresh, multi-tab concurrency, cross-portal (admin/HR/PM-shared), and logout row clearance.

Full root cause analysis and fix details: `/app/memory/AUTH_SESSION_AUDIT.md § 9a`.

---

## 3. R2 lifecycle (Initiative 3)

### Status
- ✅ Backups write to `backups/auto-90d/<filename>` (lifecycle-scoped prefix)
- ✅ Legacy `backups/*.zip` untouched (NO retroactive deletion)
- ✅ Usage probe (`/app/scripts/r2_usage_check.py`): 19.48 GB / 707 objects (well below 45 GB warn / 50 GB alert)
- ✅ Passive scheduler-side warning (no email storm — log + `backup_health` row only)
- ✅ Lifecycle apply tooling (`/app/scripts/r2_lifecycle_apply.py`) with `--show / --dry-run / --verify / apply`
- ✅ Sentinel-based `--verify` round-trip (write → read → confirm rule → cleanup)
- ⏳ **Lifecycle rule not yet applied** — current R2 token returns `AccessDenied` on `PutBucketLifecycleConfiguration`

### Activation runbook
See **`/app/memory/R2_LIFECYCLE_ACTIVATION.md`** — single source of truth for the operator-gated rollout. Tracks sign-off in § 10.

### Rollback
See `R2_LIFECYCLE_ACTIVATION.md § 9` — two layers (credential revert → rule removal). Both are non-destructive.

---

## 4. Restore drill (Initiative 2)

### Status
- ✅ End-to-end drill executed 2026-05-17 — 160 records restored from a real R2 backup into side DB `masci_restore_drill_2026_05_17_144307` on preview Mongo
- ✅ Verdict: **PASS** (mongo connectivity ✓, 6 lite-mode collections populated, daily_reports attachments intact)
- ✅ Side DB dropped after verification
- ✅ Logged in `/app/memory/RESTORE_DRILL.md`

### Operator quickstart
```bash
MONGO_URL=$(grep MONGO_URL /app/backend/.env | cut -d= -f2 | tr -d '"')
DRILL_DB="masci_restore_drill_$(date +%Y_%m_%d_%H%M%S)"

# 1. List available backups
python3 /app/scripts/restore_drill.py --list --limit 10

# 2. Dry run
python3 /app/scripts/restore_drill.py --backup <key> --target "$MONGO_URL" \
    --target-db "$DRILL_DB" --dry-run

# 3. Real restore (refuses any target-db not starting with masci_restore_drill_)
python3 /app/scripts/restore_drill.py --backup <key> --target "$MONGO_URL" \
    --target-db "$DRILL_DB"

# 4. Cleanup
mongosh "$MONGO_URL" --eval "db.getSiblingDB(\"$DRILL_DB\").dropDatabase()"
```

### Safety rails (enforced in code)
- `--target-db` MUST begin with `masci_restore_drill_` (override: `--i-know-what-i-am-doing`)
- `--target-db` CANNOT equal live `DB_NAME`
- Source backup is never modified
- R2 lifecycle is NOT triggered by drill objects (drill writes to Mongo only)

### Cadence
Quarterly, per `RESTORE_DRILL.md`. The next drill is due **Q3 2026** (90 days from 2026-05-17).

---

## 5. Admin / HR access matrix (Initiative 5)

### Status
- ✅ Read-only audit: `/app/memory/AUTHORIZATION_MATRIX.md`
- ✅ **5b-broader implemented in code** (iter187):
  - Denied-access events written to `audit_events` for `require_admin` and `require_admin_strict`
  - Backup download (`GET /api/admin/backups/{filename}`) writes a `backup_downloaded` chain-of-custody row
  - Backup delete (`DELETE /api/admin/backups/{filename}`) requires `?confirm=<filename>` matching the path
  - Step-up re-auth helper (`require_recent_step_up_raise`) wired into the 7 super-sensitive K4 mutation endpoints — env-gated by `ADMIN_STEP_UP_ENABLED`. **Currently a no-op (pass-through)** because `ADMIN_STEP_UP_ENABLED` is unset in both preview and production env. Flip it on (and front-end issues a `POST /api/admin/auth/verify-password` step-up call) to enforce the ≤5-minute window.
- ✅ Tests: `test_iter187_admin_hardening_5b.py`
- ⏸ Role-change-induced session invalidation NOT implemented — depends on Initiative 4 being active and is deferred to Initiative 5c.

---

## 6. Test coverage

| Test file | Description |
|---|---|
| `test_iter186_phase2_hardening.py` | Sentry config gate (3) · session-timeout config (4) · `/api/version` surface (2) · restore drill safety rails (3) · R2 lifecycle `--verify` (1). 1 skipped if not exercising live env. |
| `test_iter186b_session_timeout_middleware.py` | Middleware integration (8): noop-disabled · first-seen · idle expiry · absolute expiry · health exempt · anonymous · tier-strictest · dev-token-bypass |
| `test_iter187_admin_hardening_5b.py` | Denial logging · backup chain-of-custody · delete confirmation rail · step-up env-gate (pass-through when disabled · record/check round-trip when enabled) |
| `test_iter185_human_readable_export.py` | Stage A + B regression — confirmed unchanged by hardening work |

**Test discipline note:** the canonical truth for total test counts is whatever `bash /app/scripts/pre_deploy_check.sh` reports at the time of deploy. Quoted numbers in older docs are point-in-time snapshots and can drift; trust the live gate output, not the doc.

---

## 7. Pre-deploy checklist (Phase 2 specific)

1. ✅ `bash /app/scripts/pre_deploy_check.sh` exits 0
2. ✅ `GET /api/version` returns expected `release` + `session_timeouts.enabled` + `sentry.enabled`
3. ✅ `GET /api/health/full` returns 200 with all subsystems true
4. ✅ Stage B export tests pass (no regression on hardening work)
5. ✅ Session timeouts default DISABLED in env (turn on only after staging soak)
6. ✅ Sentry DSNs match the right environment (staging DSN never lands in production env)
7. ✅ R2 token (if rotated) has the right permission scope
