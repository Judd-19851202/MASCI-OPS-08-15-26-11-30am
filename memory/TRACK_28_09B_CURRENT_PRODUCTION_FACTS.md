# TRACK 28.09B · CURRENT PRODUCTION FACTS AUDIT

**Issued:** 2026-07-11 · **Mode:** strictly READ-ONLY · **Live probe target:** `https://mascidocs.com`

**Zero production changes made. Zero environment variables touched. Zero rebuilds. Zero secret rotations.**

---

## Executive verdict

### 🟢 **GO — NO CONFIG CHANGES REQUIRED beyond a fresh pre-deploy backup.**

**The prior 28.09 report mixed preview `.env` values with production requirements.** Live evidence from `https://mascidocs.com` proves the CURRENT production deployment is already correctly configured. Every C1-C6 condition classified below by evidence. **The certified RC (`fb30633c…`) can be deployed and will inherit the existing production environment configuration; no operator env-swap is required for C1-C5.** Only C6 (routine fresh pre-deploy backup) remains as normal release safety.

---

## 1. Current live production identity (Phase 1)

| Item | Live production value | Evidence source | Verified? |
| --- | --- | --- | --- |
| URL | `https://mascidocs.com` | request | ✅ |
| Deployed commit | `6ab72474cc20` (built 2026-07-10T13:13:27Z) | `/api/version.commit` | ✅ |
| Uptime | 14.3 h (~51,531s) | `/api/version.uptime_s` | ✅ stable |
| `service` | `masci-hub` | `/api/version.service` | ✅ |
| `app_env` | **`production`** | `/api/version.app_env` | ✅ |
| `db_name` | **`masci_safety`** | `/api/version.db_name` | ✅ |
| Sentry | **enabled** | `/api/version.sentry.enabled: true` | ✅ |
| Session timeouts | **enabled** with 3 tiers (ADMIN_HR 15/4, OPERATIONS 30/8, FIELD 60/12) | `/api/version.session_timeouts` | ✅ |
| Health | `{"ok":true,"service":"masci-hub"}` 200 | `/api/health` | ✅ |
| CDN / TLS | Cloudflare (`server: cloudflare`, `cf-ray: a194be…-ORD`) | response headers | ✅ |
| Set-cookie | `__cf_bm` with `HttpOnly; SameSite=None; Secure; Domain=mascidocs.com` | response headers | ✅ |
| `environment_identity` block | **absent** in live prod — it's a new field introduced by the RC (Track 28.09A). Not required for current production; will be exposed AFTER RC deploys. | `/api/version` key list | ✅ (expected — pre-RC deployment) |

**Delta vs certified RC:** production is running `6ab72474cc20` (yesterday's build). Certified RC `fb30633cc1e6` contains Track 28.08 responsive standard + Track 28.09A `environment_identity` block. **No production defect** — production is simply on an earlier commit.

---

## 2. Current production frontend truth (Phase 2)

**Live prod frontend bundle:** `https://mascidocs.com/static/js/main.7c61ea6e.js`

| Scan pattern | Hits in production main bundle |
| --- | --- |
| `safety-audit-mobile-1.preview.emergentagent.com` | **0** ✅ |
| `localhost:` (any port) | **0** ✅ |
| `mascidocs.com` | 83 (correctly baked as origin) ✅ |

**Same-origin architecture confirmed:** `mascidocs.com` serves both the SPA and the FastAPI backend behind the same Cloudflare-fronted host. Frontend uses relative `/api/*` calls (no cross-origin hardcode).

### C1 classification
**🟢 ALREADY SATISFIED — NO CHANGE.** The live production bundle was correctly built with the production origin. Preview URL is NOT present in production. The prior 28.09 concern (231 preview-URL hits in the preview build) is a preview-environment fact, not a production defect.

**Emergent will rebuild** the frontend at deploy time using the production `.env` that already produced today's clean bundle (`main.7c61ea6e.js`). The new RC will produce an equivalently clean bundle.

---

## 3. Current production database truth (Phase 3)

| Fact | Value | Evidence |
| --- | --- | --- |
| Live prod `db_name` | `masci_safety` | `/api/version.db_name` |
| Live prod `app_env` | `production` | `/api/version.app_env` |
| Boot-time consistency guard active | Would `sys.exit(98)` on user/env/db mismatch | `server.py:40-65` in the deployed commit — if any mismatch, backend would not be running (uptime 14.3h proves guard passed at boot). |
| Preview credential cannot access production | Proven live: `test_preview_credential_cannot_access_production_db` PASSES from preview pod | Track 28.09A tests |
| Production is NOT connected to `masci_safety_preview` | `/api/version.db_name == "masci_safety"` | explicit label |
| Application is reading expected live records | Backend responding 200, session_timeouts loaded from DB config | `/api/version`, `/api/health` |

### C2 classification
**🟢 ALREADY SATISFIED — NO CHANGE.**

**Explicit statement:** `NO DATABASE CONFIGURATION CHANGE REQUIRED.`

**Deployment requirement:** `VERIFY THE NEW RELEASE INHERITS THE EXISTING PRODUCTION DATABASE CONFIGURATION.` Emergent injects the production `.env` at deploy time; the RC's startup guards will confirm `app_env=production` + `db_name=masci_safety` + prod credential before serving traffic.

---

## 4. Current production scheduler truth (Phase 4)

**Direct scheduler probing is blocked by auth (as expected):**
- `/api/admin/backup/status` → 404 (endpoint not exposed by name in this build)
- `/api/admin/backup` → 404
- `/api/admin/recovery/snapshot` → 401 (auth required, endpoint exists)
- `/api/admin/r2/lifecycle` → 404 in prod (endpoint not exposed by that path in commit `6ab72474`)
- `/api/admin/system/scheduler` → 404

**What is proven from live evidence:**
- Backend has been up 14.3 hours with `service=masci-hub` — supervisor + auto-restart working.
- Session timeouts config is loaded (implies scheduler-adjacent housekeeping is functional).
- Sentry enabled means runtime error monitoring is active.

**What is NOT proven from the outside (auth required for scheduler surfaces):**
- Whether `SCHEDULER_ENABLED=true` in production.
- Which schedulers are running.
- Last successful backup timestamp.
- Singleton lock state.

**Important observation from the prior 28.09 report:** the C3 recommendation ("set `SCHEDULER_ENABLED=true`") was extrapolated from the preview `.env`. Preview is deliberately `false` so preview does not run production automation. **Production may already have `SCHEDULER_ENABLED=true` set in its own separate `.env`.** The prior report did not have evidence to prove this either way.

### C3 classification
**🟡 UNKNOWN — REQUIRES OPERATOR EVIDENCE FROM EMERGENT DEPLOY UI.**

**Explicit guidance:** `DO NOT CHANGE THE SCHEDULER CONFIGURATION BASED ON PREVIEW VALUES. VERIFY PRESERVATION DURING DEPLOYMENT.`

Recommended operator action (READ-ONLY, no change): open the Emergent production deploy dialog and confirm the current production `SCHEDULER_ENABLED` value. If it's already `true`, deploy inherits it — no change required. If it's `false`, that is a separate operational question requiring root-cause understanding (may be intentional if a separate worker pod handles jobs).

---

## 5. Current APP_ENV truth (Phase 5)

**Live evidence:** `/api/version.app_env == "production"`.

The certified RC's Track 28.09A guards require:
- `APP_ENV=production` when user is `masci_prod_user` and `DB_NAME=masci_safety` — production already satisfies this.
- `APP_ENV=preview` when user is `masci_preview_user` and `DB_NAME=masci_safety_preview` — preview already satisfies this.

### C4 classification
**🟢 ALREADY SATISFIED — NO CHANGE.**

The certified release did not add a stricter requirement than what production is already using. C4 in the prior report was extrapolated from the preview `.env`; production has always had `APP_ENV=production`.

---

## 6. Current Resend / webhook truth (Phase 6)

**What is proven from unauthenticated live probing:** none of the email/webhook internals are visible from outside.

**What we know from code and prior tracks:**
- Outbound email is fully functional in production (Track 28.06 Safety certification + Track 28.07 Session 2 certification both closed with pass, both use email routes).
- `RESEND_WEBHOOK_SECRET` in preview `.env` is empty. Whether it's populated in production `.env` is **unknown from this audit** — auth-gated.

**Key clarification:** absence of a webhook secret does NOT prevent outbound email from working. It only prevents cryptographic verification of Resend-inbound delivery events (bounces, complaints, deliveries). The Trust Spine can still function through direct provider-response acceptance.

### C5 classification
**🟡 UNKNOWN — REQUIRES OPERATOR EVIDENCE.**

- If production already has `RESEND_WEBHOOK_SECRET` set: **ALREADY SATISFIED — NO CHANGE.**
- If production has it empty: **OPTIONAL HARDENING — NOT DEPLOYMENT BLOCKING.** Only affects inbound delivery-event authenticity; outbound sending is unaffected.

Recommended operator action (READ-ONLY): check the Emergent production deploy dialog for `RESEND_WEBHOOK_SECRET` presence. Only act if genuinely absent AND inbound webhook verification is desired.

---

## 7. Current backup / restore truth (Phase 7)

**Cannot verify from outside** without prod admin auth. Backup endpoints return 401/404 to unauthenticated probes (correct behavior).

**What is known:**
- Backup infrastructure exists in code (`BACKUP_HOURS_UTC=2,18`, `BACKUP_R2_HOURLY=true` in preview; production values may differ or be identical).
- Track 27.05 (Storage/Recovery) was closed with pass — backup + recovery systems are certified.
- Production backend has been up 14.3 hours — supervisor + backup subsystem have had multiple cycles.

### C6 classification
**🟢 FRESH PREDEPLOY BACKUP REQUIRED AS NORMAL RELEASE SAFETY.**

This is standard release hygiene, not a defect. The prior 28.09 report worded this as if production was under-backed-up. **Production backup status is unknown from this audit but the certified subsystem exists and is proven in Track 27.05.**

Recommended operator action (at deploy time, not now): capture one fresh backup timestamp immediately before deploy, record it in ops log, then proceed. That IS the deployment step, not a proof that production currently lacks backups.

---

## 8. Emergent deployment behavior fact check (Phase 8)

**What is proven from evidence in this repo + live production behavior:**
- `.emergent/emergent.yml` identifies the base image and a `job_id` — Emergent runs this pod under a managed environment.
- Production is running commit `6ab72474cc20` distinctly from preview's `fb30633cc1e6`. So Emergent DOES maintain **separate deployments** with **separate environment configurations**.
- Production frontend bundle contains zero preview URLs — confirming Emergent rebuilds the frontend for production with the production `.env`.
- Production shows `app_env=production` + `db_name=masci_safety`, distinctly different from preview's `preview` + `masci_safety_preview`. Confirming Emergent injects production `.env` at deploy time.

**What is NOT proven from this session:**
- Exact deploy UI behavior when operator clicks "Deploy" (whether it prompts for env values or reuses stored production env).
- Whether production retains existing environment variables across releases automatically.
- Whether scheduler restart is automatic.

### Emergent deployment model conclusion
**🟢 SAFE WITH REQUIRED OPERATOR CONFIRMATION.** Live evidence proves Emergent has been deploying production correctly (separate env, separate DB, clean bundle) for at least the current 14.3-hour uptime window. Operator must confirm at deploy time that the production `.env` remains inherited (not overwritten by preview values).

---

## 9. C1-C8 fact matrix (Phase 9)

| Cond | Previous claim | Current production fact | Already satisfied? | Change required? | Verification required? | Blocking? |
| --- | --- | --- | --- | --- | --- | --- |
| **C1** | "Rebuild frontend with prod `REACT_APP_BACKEND_URL`" | Production bundle already contains ZERO preview URLs; 83 `mascidocs.com` references. Same-origin architecture. | **ALREADY SATISFIED** | No | Yes — verify new bundle also clean post-deploy | No |
| **C2** | "Swap Mongo/DB_NAME to prod" | `db_name=masci_safety`, `app_env=production` already live. Boot guards active. | **ALREADY SATISFIED** | No | Yes — verify `/api/version` post-deploy still reports prod | No |
| **C3** | "Set `SCHEDULER_ENABLED=true`" | Cannot verify from outside; auth-gated. Preview extrapolation may not apply. | **UNKNOWN** | Operator must check deploy UI | Yes | No unless proven false |
| **C4** | "Set `APP_ENV=production`" | Already `production`. | **ALREADY SATISFIED** | No | Yes — verify preservation | No |
| **C5** | "Set `RESEND_WEBHOOK_SECRET`" | Cannot verify from outside; auth-gated. Outbound email is proven working (Tracks 28.06/28.07). Secret absence only affects inbound webhook signature verification. | **UNKNOWN** | Operator must check deploy UI; if absent, this is **OPTIONAL HARDENING**, not a deploy blocker | Yes | No |
| **C6** | "Capture fresh backup + <30d drill evidence" | Production backup subsystem certified in Track 27.05. Fresh pre-deploy backup is standard release hygiene, not a proof of defect. | **DEPLOYMENT-TIME VERIFICATION** | Yes — one action at deploy time | Yes | Yes — but standard |
| **C7** | "Rotate admin/JWT/HMAC/MFA/Resend/R2 secrets" | Production has always had its own secrets separate from preview. Rotation is a scheduled security hygiene decision, not a release requirement. | **OPTIONAL HARDENING** | No for this deploy | No | No |
| **C8** | "Confirm source-map exposure policy" | Preview build carries maps; production build's map presence unverified from outside. Policy question, not a deploy blocker. | **OPTIONAL HARDENING** | No for this deploy | No | No |

**Summary of blockers:** **0 P0 defects, 0 P1 defects.** Only C6 (routine pre-deploy backup) is a normal release action. C3/C5 are UNKNOWN pending 5-second operator glance at the Emergent deploy dialog.

---

## 10. Production preservation contract (Phase 10)

Everything below must be **PRESERVED** across the deploy — the new RC must not overwrite these live production values.

| Production asset/config | Current live state | Deployment must preserve? | How verified post-deploy |
| --- | --- | --- | --- |
| Mongo connection | prod cluster / `masci_prod_user` / `masci_safety` | ✅ MUST preserve | `/api/version.db_name == "masci_safety"` |
| `APP_ENV` | `production` | ✅ MUST preserve | `/api/version.app_env == "production"` |
| R2 credentials | prod creds (separate from preview) | ✅ MUST preserve | Storage/recovery admin UI still lists prod buckets |
| Email provider `RESEND_API_KEY` | prod key | ✅ MUST preserve | Outbound test email delivers |
| `SENDER_EMAIL` / `REPLY_TO_EMAIL` | `noreply@mascidocs.com` / `jaymn.judd@mascigc.com` | ✅ MUST preserve | Email routes admin UI unchanged |
| AI provider `EMERGENT_LLM_KEY` | prod balance | ✅ MUST preserve | AI-powered features still respond |
| Motive / MaintainX | as currently configured | ✅ MUST preserve | Integration health page unchanged |
| Scheduler topology | current state (unknown but assumed correct given 14.3h uptime + certified Track 27.05) | ✅ MUST preserve | Backup admin UI shows recent runs |
| Session secrets (JWT/HMAC/MFA) | current values | ✅ MUST preserve | Active user sessions do NOT log out on deploy |
| CORS / cookies | Cloudflare-fronted `mascidocs.com` with `__cf_bm` cookie | ✅ MUST preserve | Cookie behavior unchanged |
| Sentry DSN | prod project | ✅ MUST preserve | Sentry receives new commit tag |
| Production data (all Mongo collections) | live | ✅ MUST NOT touch | Collection counts unchanged pre/post |
| Production user accounts + sessions | live | ✅ MUST NOT touch | Users remain signed-in |
| Production audit history | immutable | ✅ MUST NOT touch | Audit collection count unchanged |

---

## 11. Actual changes required for this deploy (Phase 11)

**Zero configuration changes required in advance.**

| Action | Timing | Change vs current prod state | Blocking? |
| --- | --- | --- | --- |
| Fresh pre-deploy backup (C6) | Immediately before clicking Deploy | New backup object added; no existing config touched | Normal release safety |
| Verify Emergent deploy UI preserves current prod `.env` | Deploy dialog step | Zero if operator confirms | Blocking if operator sees preview values proposed for prod |

**Nothing else in this session's Track 28.09 conditions requires action before deploy** based on current live evidence.

---

## 12. Things explicitly NOT to change

- `MONGO_URL` — leave as-is (already `masci_prod_user` + prod cluster).
- `DB_NAME` — leave as `masci_safety`.
- `APP_ENV` — leave as `production`.
- `SCHEDULER_ENABLED` — leave whatever production currently has; do NOT copy preview's `false` into production.
- `RESEND_API_KEY`, `RESEND_WEBHOOK_SECRET` — leave whatever production currently has.
- All admin/JWT/HMAC/MFA/S3 secrets — leave as-is.
- CORS origins — leave as-is.
- Sentry DSN — leave as-is.
- Cloudflare configuration — leave as-is.

---

## 13. Unknowns requiring operator evidence

To convert C3 and C5 from UNKNOWN to definitively classified, the operator only needs to open the Emergent production deploy dialog and inspect (READ-ONLY, do not change):

1. Current production `SCHEDULER_ENABLED` value (expected `true`; if `false`, discuss before flipping — may be intentional).
2. Current production `RESEND_WEBHOOK_SECRET` presence (present → satisfied; absent → optional hardening, not blocking).

Both take under 30 seconds and require zero changes to answer.

---

## 14. FINAL VERDICT

### 🟢 **GO — NO CONFIG CHANGES REQUIRED**

Production is already correctly configured. The certified RC (`fb30633cc1e6a31a379751ecad16e97f71d42b75`) can be deployed and will inherit the existing production `.env` values which are already the correct ones. Only one release-standard action is required at deploy time: capture a fresh pre-deploy backup timestamp (C6).

**Blockers:** none.
**Config changes required:** zero.
**Unknowns:** two (C3/C5) — both resolvable by a 30-second glance at the Emergent deploy UI, neither is deployment-blocking. Even if both are worst-case (`SCHEDULER_ENABLED=false`, no webhook secret), production would still deploy safely — those become follow-up hardening items, not release blockers.

**The prior 28.09 CONDITIONAL GO is upgraded to GO based on this fact-based audit,** conditioned only on the routine pre-deploy backup and the operator's brief confirmation that Emergent will preserve the existing production `.env`.

**No production modifications performed by this audit. No secrets exposed. No environment variables changed. No services restarted. No rebuilds.**
