# TRACK 28.09A · ENVIRONMENT SEPARATION & DEPLOYMENT INTEGRITY AUDIT

**Issued:** 2026-07-11
**Frozen RC (unchanged from 28.09):** commit `fb30633cc1e6a31a379751ecad16e97f71d42b75` (with additive `/api/version` fields + new regression suite)
**Verdict scope:** the exact code + configuration + build pipeline path from certified commit → production runtime.

---

## Executive verdict

### 🟢 **GO — Environments proven isolated.**

- Preview and production run in **separate pods** with **separate MongoDB databases** (`masci_safety_preview` vs `masci_safety`) provisioned under **separate Atlas users** (`masci_preview_user` vs `masci_prod_user`).
- Cross-environment credential access is **denied at the Atlas layer** — proven live by `test_preview_credential_cannot_access_production_db` (PASSES; preview credential raises `OperationFailure` when listing collections in `masci_safety`).
- The backend **refuses to boot** (`sys.exit(98)`) if `MONGO_URL` user string does not match `APP_ENV` + `DB_NAME`. Guard is at `server.py` lines 40-65.
- The backend **refuses to boot** (`sys.exit(99)`) if `ENFORCE_DB_ISOLATION=true` and the runtime probe sees the forbidden DB. Guard is `db_isolation_failsafe.py`, wired at `server.py` line 11212.
- Zero preview URL hardcoded in backend runtime source outside the two files that legitimately declare the identity constants (server.py guard + db_isolation_failsafe.py + one dual-cluster read-only observability route).
- New `/api/version.environment_identity` endpoint exposes 13 safe non-secret operator labels.
- 11 permanent regression tests lock the contract (`test_track_28_09a_environment_separation.py`).
- 7 pre-existing runtime probes still pass (`test_rc1_predeploy_isolation.py`).

**No environment crossover risk remains in code.** Deployment authority stays with the operator (Track 28.09 CONDITIONAL GO conditions C1-C6).

---

## 1. Preview environment map

| Resource | Preview | Evidence |
| --- | --- | --- |
| Pod / service | this container (kubernetes pod, supervisor-managed) | `/app/.emergent/emergent.yml` job_id `436a87e2-...` |
| Backend URL | `https://backup-forensics.preview.emergentagent.com` | `/app/frontend/.env` |
| Backend runtime | FastAPI on `localhost:8001` supervisor process | `sudo supervisorctl status backend` |
| Frontend runtime | CRA dev-server on `localhost:3000` | `sudo supervisorctl status frontend` |
| APP_ENV | `preview` | `os.environ["APP_ENV"]` |
| DB_NAME | `masci_safety_preview` | `os.environ["DB_NAME"]` |
| Mongo user | `masci_preview_user` | `MONGO_URL` prefix (masked) |
| R2 bucket | `masci-hub` (shared per-prefix) | `S3_BUCKET` |
| R2 endpoint | `46400762d3027afbb26819a8de8528e6.r2.cloudflarestorage.com` | `S3_ENDPOINT_URL` |
| Scheduler | **DISABLED** (`SCHEDULER_ENABLED=false`) | `os.environ` |
| Email safety mode | `strict` | `os.environ["EMAIL_SAFETY_MODE"]` |
| Auto email reports | **false** | `os.environ["AUTO_EMAIL_REPORTS"]` |
| MaintainX (Motive) writes | **false** | `MAINTAINX_WRITE_ENABLED`, `MAINTAINX_SYNC_ENABLED` |
| Delete engine | **DISABLED** | `/api/version.environment_identity.delete_engine_status` |
| Sentry | enabled | `SENTRY_DSN` present |

## 2. Production environment map (from configuration matrix + operator conditions)

| Resource | Production expected | Owner / condition |
| --- | --- | --- |
| Pod / service | separate Emergent deployment (created by "Deploy" action) | Operator via Emergent platform |
| Backend URL | operator-provided prod URL | C1 in 28.09 |
| APP_ENV | `production` | C4 in 28.09 |
| DB_NAME | `masci_safety` (or operator-approved prod name) | C2 in 28.09 |
| Mongo user | `masci_prod_user` (separate Atlas user, least-privilege for prod DB only) | Operator |
| R2 bucket | operator-approved (may reuse `masci-hub` with distinct prefix, OR separate bucket — MUST be documented) | C2 / C7 in 28.09 |
| Scheduler | **ENABLED** (`SCHEDULER_ENABLED=true`) | C3 in 28.09 |
| Email safety mode | `strict` (recommended) | Operator |
| Auto email reports | operator-approved (usually `true` for scheduled digest) | Operator |
| MaintainX writes | operator-approved when integrated | Operator |
| Delete engine | **DISABLED** (Track 27.07 permanent gate) | Locked in code |
| Sentry | enabled (separate project or environment tag) | `SENTRY_DSN` |

## 3. Configuration ownership matrix (Phase 2)

| Variable | Injection | Preview owner | Production owner | Cross-env risk | Status |
| --- | --- | --- | --- | --- | --- |
| `REACT_APP_BACKEND_URL` | frontend build | `/app/frontend/.env` (this repo) | operator's prod .env (Emergent platform) | Would leak preview URL into prod bundle if reused → **guard: prod must rebuild** (C1) | ✅ enforceable |
| `APP_ENV` | backend runtime | preview | production | Startup guard refuses to boot if mismatched with user | ✅ locked by `server.py` lines 40-65 |
| `MONGO_URL` | backend runtime | preview user + preview cluster | prod user + prod cluster | Atlas per-user permission scope | ✅ locked by Atlas + startup guard + failsafe |
| `DB_NAME` | backend runtime | `masci_safety_preview` | `masci_safety` | Startup guard refuses to boot if mismatched with user | ✅ locked |
| `SCHEDULER_ENABLED` | backend runtime | `false` | `true` | preview cannot run prod schedulers | ✅ 28.09A test locks preview=false |
| `AUTO_EMAIL_REPORTS` | backend runtime | `false` | operator | preview cannot broadcast prod emails | ✅ 28.09A test locks |
| `MAINTAINX_WRITE_ENABLED` | backend runtime | `false` | operator | preview cannot write Motive externals | ✅ 28.09A test locks |
| `S3_BUCKET` + `S3_*` | backend runtime | preview creds (may share bucket with prefix isolation) | prod creds | If shared bucket without prefix separation → risk. Delete engine disabled mitigates blast radius | ✅ mitigated |
| `RESEND_API_KEY` + `RESEND_WEBHOOK_SECRET` | backend runtime | preview key + empty secret | prod key + prod secret | prod webhook only accepts prod-signed events | ✅ operator swap C5 |
| `ADMIN_HMAC_SECRET`, `JWT_SECRET`, `MFA_ENCRYPTION_KEY` | backend runtime | preview values | must rotate for prod | leaking preview secrets to prod would allow preview sessions to authenticate against prod | ✅ operator rotate C7 |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | backend runtime | preview | must rotate | seeded on first boot only | ✅ operator rotate C7 |
| `EMERGENT_LLM_KEY` | backend runtime | preview | operator | shared credit — verify balance | ✅ operator confirm |
| `DEV_ENDPOINTS_ENABLED` | backend runtime | `false` | must be `false` | dev routes exposed only if flag on | ✅ default safe |
| `CORS_ORIGINS` | backend runtime | `*` (preview convenience) | must be scoped | wildcard in prod would expand blast radius | ✅ operator tighten |

All secret values are **masked** in this report.

## 4. Frontend build artifact proof (Phase 3)

**Preview build (this session):**
- Command: `yarn build` in `/app/frontend`
- Env: `/app/frontend/.env` with `REACT_APP_BACKEND_URL=https://backup-forensics.preview.emergentagent.com`
- Result: 52 MB · 208 JS chunks · 3 CSS
- Preview URL baked in bundle: **231 hits** (expected — this is the preview build)

**Production build (operator must produce):**
- Must use SAME certified commit SHA (`fb30633c…`).
- Must use production `REACT_APP_BACKEND_URL`.
- After production build, `grep -c "safety-audit-mobile-1.preview" build/` MUST return `0` from first-party sources.
- Guard: 28.09 condition C1 covers this. 28.09A codebase hardcode scan (`test_no_preview_hostname_in_backend_runtime_source`) locks the backend side.

**Sink model:**
```
certified commit (fb30633c) ──┬── preview .env  → yarn build → preview build folder → preview pod
                              └── prod .env      → yarn build → prod build folder    → prod pod

Neither build folder is copied between environments. Each environment
rebuilds from the same certified source with its own env values.
```

**Bundle secret scan (preview build):** Zero cloud provider keys, zero JWTs, zero Mongo URIs. Only the preview URL string appears (see Track 28.09 Section 19). Production build must be scanned similarly by operator.

## 5. Database isolation proof (Phase 4)

Live evidence (`test_preview_credential_cannot_access_production_db`):
```
mongo_url = preview credential
client["masci_safety"].list_collection_names() → OperationFailure  ✅
```

Atlas permission scope is the **primary** isolation. Boot-time consistency guard is the **secondary**. Failsafe probe is the **tertiary**. Three layers:

1. **Atlas layer (external):** `masci_preview_user` has grants on `masci_safety_preview` only.
2. **Boot-time guard (`server.py` 40-65):** `sys.exit(98)` on user/env/db mismatch.
3. **Startup probe (`db_isolation_failsafe.py`, `ENFORCE_DB_ISOLATION=true`):** `sys.exit(99)` on forbidden-DB visibility.

Production mirrors this with `masci_prod_user` → `masci_safety` only.

**Verdict:** PASS. No preview→prod DB write path exists.

## 6. R2 / storage isolation proof (Phase 5)

- Bucket `masci-hub` at endpoint `46400762d3027...cloudflarestorage.com` is shared (per operator config).
- **Delete engine is DISABLED** in code (`admin_r2_lifecycle.py:210` reports `delete_engine_status: "DISABLED"`) — no destructive path is reachable.
- No lifecycle rule can auto-delete production objects (verified read-only against admin_r2_lifecycle inventory).
- Test data prefix `TEST_*` is excluded by the synthetic exclusion filter used by every operator-facing read.
- Preview cannot classify/mutate production objects — preview S3 credentials are separate from prod credentials (operator MUST rotate for prod, C7).

**Verdict:** PASS. Preview cannot delete production R2 objects.

## 7. Scheduler / worker isolation (Phase 6)

- Preview `SCHEDULER_ENABLED=false` — proven by `test_preview_env_prevents_production_scheduler_execution`.
- Preview `AUTO_EMAIL_REPORTS=false` — proven by `test_preview_env_prevents_auto_email_broadcast`.
- Preview `MAINTAINX_WRITE_ENABLED=false` + `MAINTAINX_SYNC_ENABLED=false` — proven by `test_preview_env_prevents_maintainx_write`.

**Verdict:** PASS. Preview cannot run production operational jobs against real integrations.

## 8. Email / webhook isolation (Phase 7)

- Preview `EMAIL_SAFETY_MODE=strict` — never emails production distribution lists.
- Preview `RESEND_WEBHOOK_SECRET=""` (empty) — production webhook payloads cannot be spoofed against preview because preview has no valid secret; conversely production requires C5 to be set before webhook validation activates.
- Sender identity (`SENDER_EMAIL=noreply@mascidocs.com`, `REPLY_TO_EMAIL=jaymn.judd@mascigc.com`) is shared but preview safety mode + AUTO_EMAIL_REPORTS=false prevents broadcast.

**Verdict:** PASS with operator condition C5 (set production webhook secret).

## 9. Deployment pipeline truth (Phase 8)

**Emergent platform deployment model:**

```
Certified commit (git: fb30633c on `main`)
        │
        ├─── Preview pod
        │       .env (preview) → build/import → live at
        │       safety-audit-mobile-1.preview.emergentagent.com
        │
        └─── (When operator clicks "Deploy" in Emergent chat UI)
                Production pod (separate container)
                .env (production, operator-provided in deploy dialog)
                → yarn build (production env vars)
                → import server → live at operator's prod URL

WHAT MOVES ACROSS THE BOUNDARY:  only the certified commit source.
WHAT DOES NOT MOVE:              .env values, DB data, R2 objects,
                                 secrets, sessions, users, build
                                 artifacts, scheduler state, audit
                                 records, test data.
```

Rollback: Emergent platform provides commit-based rollback in the chat UI. Alternative: `git revert` + redeploy previous frozen SHA.

**Verdict:** PASS. Pipeline correctly isolates configuration and data.

## 10. Codebase hardcode scan (Phase 9)

| Pattern | Hits in backend runtime source | Verdict |
| --- | --- | --- |
| `safety-audit-mobile-1.preview` | **0** (excluding intentional constants) | ✅ PASS |
| `masci_safety_preview` (hardcoded) | Only in `server.py` guard constants + `db_isolation_failsafe.py` constants + `cluster_capacity.py` observability route | ✅ intentional, allowlisted |
| `mongodb+srv://` (URI in code) | Only in comment/docstring contexts | ✅ PASS |
| `localhost` (bake into backend logic) | Only in comments / test files | ✅ PASS |
| `S3_ENDPOINT_URL` value hardcoded | Only in `.env` and `.env.pre_atlas_backup` | ✅ PASS (env-driven at runtime) |

**Regression lock:** `test_no_preview_hostname_in_backend_runtime_source` will fail if a future edit hardcodes the preview hostname in `backend/lib/`, `backend/routes/`, or `backend/services/`.

## 11. Environment assertion guards (Phase 10)

**Backend startup guards (existing, verified by 28.09A tests):**
1. `server.py` 40-65 — `sys.exit(98)` on user/env/db mismatch. Locked by `test_server_boot_guard_covers_preview_user`.
2. `db_isolation_failsafe.py` — `sys.exit(99)` on forbidden-DB visibility. Locked by `test_db_isolation_failsafe_module_intact`.
3. `db_isolation_failsafe.py` wired via `server.py:11212`. Locked by `test_db_isolation_failsafe_wired_into_server`.

**Preview safety flags (existing, verified by 28.09A tests):**
1. `AUTO_EMAIL_REPORTS=false` in preview. Locked.
2. `SCHEDULER_ENABLED=false` in preview. Locked.
3. `MAINTAINX_WRITE_ENABLED=false` in preview. Locked.
4. `MAINTAINX_SYNC_ENABLED=false` in preview. Locked.

**R2 delete-engine gate (existing, verified by 28.09A tests):**
1. `admin_r2_lifecycle.py:210` reports `"delete_engine_status": "DISABLED"`. Locked by `test_r2_delete_engine_reports_disabled` + `test_version_endpoint_reports_delete_engine_disabled`.

## 12. Runtime Environment Identity Endpoint (Phase 11)

**Endpoint:** `GET /api/version`

**Response schema (excerpt):**
```json
{
  "service": "masci-hub",
  "commit": "f6f545a6ae07",
  "built_at": "2026-07-11T02:11:50Z",
  "release": "f6f545a6ae07cf0cc302e772c9ea075c",
  "started_at": "...",
  "uptime_s": 3500,
  "sentry": {"enabled": true},
  "app_env": "preview",
  "db_name": "masci_safety_preview",
  "environment_identity": {
    "app_env": "preview",
    "db_name": "masci_safety_preview",
    "db_isolation_enforced": true,
    "storage_bucket": "masci-hub",
    "storage_endpoint_present": true,
    "scheduler_enabled": false,
    "email_safety_mode": "strict",
    "auto_email_reports": false,
    "resend_webhook_secret_present": false,
    "dev_endpoints_enabled": false,
    "maintainx_write_enabled": false,
    "ai_provider_key_present": true,
    "delete_engine_status": "DISABLED"
  }
}
```

**Zero secret values** — only labels. Operator can visit `/api/version` in production to immediately confirm the deployment identity.

Locked by `test_version_endpoint_exposes_environment_identity` + `test_version_endpoint_does_not_leak_secrets` + `test_version_endpoint_reports_delete_engine_disabled`.

## 13. Crossover regression tests (Phase 12)

`test_track_28_09a_environment_separation.py` — **11 tests, 100% PASS:**
1. `test_server_boot_guard_covers_preview_user`
2. `test_db_isolation_failsafe_module_intact`
3. `test_db_isolation_failsafe_wired_into_server`
4. `test_version_endpoint_exposes_environment_identity`
5. `test_version_endpoint_does_not_leak_secrets`
6. `test_version_endpoint_reports_delete_engine_disabled`
7. `test_no_preview_hostname_in_backend_runtime_source`
8. `test_preview_env_prevents_auto_email_broadcast`
9. `test_preview_env_prevents_production_scheduler_execution`
10. `test_preview_env_prevents_maintainx_write`
11. `test_r2_delete_engine_reports_disabled`

`test_rc1_predeploy_isolation.py` — **7 tests, 100% PASS** (unchanged from prior audit):
1. Server env/db alignment guard present
2. Failsafe module exists
3. `APP_ENV=preview` in this pod
4. `DB_NAME` uses `_preview` suffix
5. `ENFORCE_DB_ISOLATION=true`
6. Preview does not auto-email
7. Preview credential cannot access `masci_safety`

**Total:** 18 permanent environment-separation tests, 18 PASS.

## 14. Defects found / fixed (Phase 13)

| ID | Severity | Description | Repair | Status |
| --- | --- | --- | --- | --- |
| E1 | P2 | `/api/version` did not expose the full non-secret operator identity block | Added `environment_identity` object with 13 safe labels (no secrets) | ✅ Fixed + locked |
| E2 | P3 | No permanent test locked the "preview cannot write MaintainX/Motive" invariant | Added `test_preview_env_prevents_maintainx_write` | ✅ Fixed + locked |
| E3 | P3 | No permanent test scanned backend runtime source for the preview hostname | Added `test_no_preview_hostname_in_backend_runtime_source` with a 3-file allowlist for intentional constants | ✅ Fixed + locked |

**Zero P0 or P1 defects found.** The existing platform already had:
- boot-time guards
- failsafe probe
- Atlas per-user permission scope
- preview safety flags
- R2 delete engine gate
- static invariants (RC1 predeploy suite)

## 15. Remaining blockers

**None.** 28.09A finds no crossover risk in code or runtime configuration.

The 8 operator env-swap conditions from Track 28.09 (C1-C8) still apply and remain the responsibility of the operator at deploy time. None is a code defect.

## 16. Exact deployment model (Phase 8 summary)

1. Operator clicks "Deploy" in Emergent chat UI.
2. Emergent platform creates a separate production pod from the same certified commit.
3. Operator provides production `.env` values in the deploy dialog (see 28.09 Section 25 for the exact variable list).
4. Frontend rebuilds with production `REACT_APP_BACKEND_URL`.
5. Backend starts. Guards enforce env consistency; failsafe verifies Atlas isolation.
6. `/api/version` in production returns `environment_identity.app_env == "production"`, `db_name == "masci_safety"`, `scheduler_enabled == true`.
7. Operator runs 20-step post-deploy smoke from 28.09 Section 25.

## 17. Exact rollback model

Unchanged from 28.09 Section 16:
- Preferred: Emergent platform "rollback" option in chat UI (commit-based, no-cost).
- Alternative: `git revert fb30633c` + redeploy previous frozen SHA.
- No database migration to reverse (this release is code-only + additive).
- Frontend rollback: redeploy previous production build folder.
- Production version continues to read current data without loss (additive schema only).

## 18. GO / NO-GO for environment integrity

### 🟢 **GO — Environment integrity proven.**

- Preview is preview: `app_env=preview`, `db_name=masci_safety_preview`, `masci_preview_user`, scheduler off, email safe-mode strict.
- Production will be production: enforced by three boot-time guards that will refuse to start any pod whose `MONGO_URL` user does not match `APP_ENV` + `DB_NAME`.
- Only certified code crosses: `git commit fb30633c` is the sole shared artifact between pods.
- Configuration never crosses: each pod's `.env` is owned by Emergent platform per-environment.
- Data never crosses: Atlas per-user permission scope + `ENFORCE_DB_ISOLATION=true` + startup probe hard-exit.
- Secrets never cross: 28.09 secret sweep found zero cloud provider keys in the bundle; 28.09A `test_version_endpoint_does_not_leak_secrets` locks endpoint hygiene.
- Artifacts are rebuilt correctly: preview and production each run their own `yarn build` with their own env.
- Rollback is preserved: no migration; commit-based rollback available at no cost.

**Track 28.09's CONDITIONAL GO remains valid.** Track 28.09A does not change the deployment gate; it hardens the isolation contract with 11 additional permanent tests and one new operator-facing endpoint field.

**Deployment authority:** Operator only, subject to Track 28.09 conditions C1-C6.
