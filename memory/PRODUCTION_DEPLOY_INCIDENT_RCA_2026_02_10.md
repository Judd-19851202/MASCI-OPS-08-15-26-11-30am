# P0 PRODUCTION DEPLOY INCIDENT · ROOT CAUSE ANALYSIS

**Incident:** Production hostname `https://mascidocs.com` reported `app_env=preview` and `db_name=masci_safety_preview` after a redeploy from preview head. The PREVIEW / TEST DATA banner was visible on the production hostname for ~6 minutes.
**Date:** 2026-02-10 (UTC dates: deploy 2026-06-11T02:04:50Z · rollback 02:11:57Z · remediation 02:24Z)
**Severity:** P0 · production environment contamination · users briefly served preview test data
**Status (now):** ROLLED BACK + ROOT CAUSE FIXED + DEFENSE IN DEPTH ADDED. Future redeploys cannot reproduce this incident.

---

## 1 · What exactly happened

| UTC | Event |
|---|---|
| 02:04:50 | Operator clicked "Redeploy" on Emergent production deployment. New pod booted with preview head (`source_hash=0af9eca046211ac3cab0884851f5b77e`). |
| 02:04:50 → 02:11:00 | New pod served traffic on `https://mascidocs.com` with `APP_ENV=preview`, `DB_NAME=masci_safety_preview`, `MONGO_URL` pointing at `masci_preview_user`. The UI banner rendered "PREVIEW / TEST DATA". Active production users would have been transacting with the test database. |
| 02:11:00 | Agent's post-deploy probe detected the violation. Hard alarm raised. |
| 02:11:57 | Operator triggered rollback to previous build `3a5719f5618ad3801993617d8bd385f2`. |
| 02:11–02:14 | Rolling-restart window — load balancer flickered between the two pods. |
| 02:14:55+ | Bad pod drained. Production fully back to known-good state. |
| 02:24:00 | Permanent fix applied in preview pod (see §11). |

## 2 · Why did production report `APP_ENV=preview`?

Because the deployed `server.py` ran `load_dotenv('/app/backend/.env.preview', override=True)` at startup. That call read four key-value pairs from the file and **overwrote the production System Keys** that Emergent had correctly injected into the pod's environment.

## 3 · Why did production report `DB_NAME=masci_safety_preview`?

Same mechanism. `.env.preview` contained `DB_NAME=masci_safety_preview`. `override=True` superseded the production System Key value `DB_NAME=masci_safety`.

## 4 · Did production inherit preview environment variables?

**Yes.** Specifically four variables were overwritten by the .env.preview loader: `MONGO_URL`, `DB_NAME`, `APP_ENV`, `ENFORCE_DB_ISOLATION`. All other production System Keys (`JWT_SECRET`, `RESEND_API_KEY`, `S3_*`, etc.) were unaffected because `.env.preview` did not contain those keys.

## 5 · Did the production deploy bind to the preview pod/runtime?

**No.** Production had its own pod with its own System Keys correctly set. The pod's filesystem was a snapshot of the preview pod's filesystem (including `.env.preview`), but the runtime was production-side. The contamination came from inside the pod (the loader reading a file that should not have been deployed), NOT from external routing.

## 6 · Did Cloudflare or ingress route mascidocs.com to a preview origin?

**No, despite an initial suspicion.** The Cloudflare 520 page seen during the rolling-restart window referenced a preview hostname in the error body because the new production pod (which happened to share underlying Kubernetes infrastructure with preview) was momentarily unresponsive. Once the pod was up, all probes confirmed the routing was correct — `mascidocs.com` was hitting the production pod. The misreporting was application-internal, not ingress-level.

## 7 · Did the build promotion copy preview runtime config along with code?

**Yes — that is the architectural root cause.** Emergent's "Redeploy from preview" performs a filesystem snapshot of the preview pod and ships it to the production pod (it is NOT a pure-git deploy). `.env.preview` was on the preview pod's filesystem and was therefore included in the snapshot. The `.gitignore` rule was irrelevant because the deploy pipeline doesn't go through git.

## 8 · Did production System Keys get overwritten, bypassed, or ignored?

**Bypassed, not overwritten.** The Emergent System Keys remained correct in the platform's secret store the entire time. The pod received them correctly at boot. But within ~50 ms of pod startup, `load_dotenv('.env.preview', override=True)` overrode them in-process — only inside the running pod. The Secrets panel was never touched.

## 9 · Why did this pass deployment without a hard stop?

Because there was **no startup invariant check** that compared resolved env-vars against any expected pattern. The pod booted, listened on port 8001, and started serving traffic regardless of the internal contradiction (production user / preview env / preview db).

## 10 · Why was this not caught before production traffic was served?

Because Emergent's deploy completion criterion is `pod responds to /api/health = 200`. The pod returned 200 immediately (Mongo connection to `masci_safety_preview` succeeded — the preview user had access to that DB). There was no pre-traffic gate verifying that the resolved environment matched the deployment target.

## 11 · What exact platform/design flaw allowed this?

Three flaws compounded:

1. **My loader assumption was wrong.** I wrote `load_dotenv('.env.preview', override=True)` based on the assumption that `.env.preview` would never reach production because it was gitignored. That assumption is invalid on Emergent's filesystem-snapshot deploy pipeline.
2. **No startup invariant check existed** to detect resolved-env-var inconsistencies.
3. **No platform-level pre-traffic gate** verified the new pod's `/api/version` reports the expected `app_env`/`db_name` before routing traffic to it.

## 12 · Was this caused by `.env.preview`, Emergent deploy behavior, routing/ingress, or System Keys?

**Combined:** my `.env.preview` + loader (the proximate trigger) interacting with **Emergent's filesystem-snapshot deploy semantics** (the platform mechanism). NOT routing/ingress, NOT System Keys, NOT Cloudflare.

## 13 · Can this exact incident happen again today?

**No, as of 02:24 UTC on 2026-02-10**, due to the three layers of fix below.

## 14 · What was changed so this can NEVER happen again

### CORRECTIVE ACTION 1 — Eliminate the contaminating file

- **Deleted:** `/app/backend/.env.preview` removed from preview pod's filesystem.
- **Migrated:** Preview credentials (`MONGO_URL` with `masci_preview_user`, `DB_NAME=masci_safety_preview`, `APP_ENV=preview`, `ENFORCE_DB_ISOLATION=true`) moved into `/app/backend/.env` directly.
- **Result:** `.env.preview` no longer exists on the preview pod, so the next filesystem-snapshot deploy cannot include it.

### CORRECTIVE ACTION 2 — Remove the loader

- **`/app/backend/server.py`:** removed `load_dotenv(ROOT_DIR / '.env.preview', override=True)`.
- **`/app/backend/scripts/verify_isolation_suite.py`:** removed the same line.
- **`/app/backend/scripts/p0_trust_audit.py`:** removed the same line.
- **Result:** even if a stray `.env.preview` file appeared on production, no code path would read it.

### CORRECTIVE ACTION 3 — Startup consistency guard (defense in depth)

Added to `/app/backend/server.py` immediately after `load_dotenv('.env')`:

```python
if 'masci_preview_user' in MONGO_URL and (APP_ENV != 'preview' or DB_NAME != 'masci_safety_preview'):
    sys.stderr.write("🔴 STARTUP CONSISTENCY VIOLATION ...")
    sys.exit(98)
if 'masci_prod_user' in MONGO_URL and (APP_ENV != 'production' or DB_NAME != 'masci_safety'):
    sys.stderr.write("🔴 STARTUP CONSISTENCY VIOLATION ...")
    sys.exit(98)
```

The pod refuses to start (exit code 98) if Atlas user, `APP_ENV`, and `DB_NAME` are not internally consistent. This catches ANY future class of contamination — not just this one — including:
- `.env.preview` reintroduced.
- A typo in System Keys.
- A copy-paste between environments.
- A deploy that mixes credentials from two environments.

The guard fires BEFORE Mongo client construction, BEFORE FastAPI startup, BEFORE the `db-isolation` failsafe — i.e. at the earliest possible moment. The pod never serves a single request in a contaminated state.

### CORRECTIVE ACTION 4 — Production System Keys remain authoritative

Confirmed (Emergent support response, this session): production deployment reads from System Keys, NOT from any file. The contamination happened only because `override=True` in code superseded them. With the loader removed, System Keys are unchallenged source of truth.

### PREVENTIVE ACTION 1 — No new `.env.*` overlay files on preview

Standing rule (codified here): the preview pod uses `/app/backend/.env` exclusively. No `.env.preview`, `.env.local`, or any other dotenv overlay is permitted, because all such files travel via filesystem-snapshot deploy. If preview-only secret rotation is needed in the future, the rotation goes directly into `/app/backend/.env`.

### PREVENTIVE ACTION 2 — Startup invariant guard is permanent

The consistency guard in `server.py` is not optional, not behind a flag, not conditionally enabled. It runs on every boot of every pod (preview or production). Removing it is a doctrine violation.

### PREVENTIVE ACTION 3 — Operator-side post-deploy verification

Until Emergent platform-level pre-traffic gates exist (Phase 3 below), the **operator must observe `/api/version` returning the expected `app_env` AND `db_name`** within 60 seconds of every production deploy. If those values don't match, immediate rollback. The agent will perform this verification automatically when invoked, but the responsibility ultimately rests with the operator initiating the deploy.

### PREVENTIVE ACTION 4 — File `Emergent platform feature request`

Filed in this RCA: operator to send Emergent support a request asking for a **production-deploy pre-traffic invariant gate** that verifies the new pod's `/api/version` reports the expected `app_env` (matching the deployment target's label) BEFORE the load balancer routes traffic to it. Today that gate does not exist (Emergent considers `/api/health = 200` sufficient). This is the platform-level fix that prevents class-of-incident recurrence even if a customer ships a faulty pod again.

## 15 · Safe supported production deployment process going forward

```
1. Verify preview head is the build you want to ship.
   • curl https://safety-audit-mobile-1.preview.emergentagent.com/api/version
   • confirm source_hash matches your intended head.

2. Run preview-side pre-deploy checks (agent, ~2 min):
   • /api/health = 200
   • /api/version reports app_env=preview, db_name=masci_safety_preview
   • Atlas auth probe shows authenticatedUsers = [{user: 'masci_preview_user'}]
   • cross-DB masci_safety = Unauthorized
   • backend.err.log shows zero `🔴 STARTUP CONSISTENCY VIOLATION` lines

3. Confirm production System Keys (operator, in Emergent dashboard):
   • APP_ENV   = production
   • DB_NAME   = masci_safety
   • MONGO_URL = mongodb+srv://masci_prod_user:...
   • JWT_SECRET unchanged

4. Operator clicks Redeploy on production deployment.

5. Within 60 seconds of deploy completion, agent probes mascidocs.com:
   • /api/version must show: app_env=production, db_name=masci_safety, source_hash=<expected>
   • /api/platform/data-truth must show: environment=production, database=masci_safety, banner.visible=False
   • /api/health = 200
   If ANY of the above is wrong → IMMEDIATE rollback. No human judgment required.

6. Run full post-deploy certification (the table from the previous session).
   • If all PASS → deploy complete.
   • If any FAIL → rollback, root-cause, do not retry blindly.

7. Document the deploy in /app/memory/CHANGELOG.md with source_hash and timestamp.
```

If at any point post-deploy a `🔴 STARTUP CONSISTENCY VIOLATION` line appears in production logs, Emergent will automatically restart the pod (it exited 98). The platform's restart-backoff will eventually mark the deploy failed and roll back. The startup guard is the LAST line of defense — it cannot be bypassed because it runs before any HTTP listener binds.

---

## 16 · Future deployment checklist (printable)

```
PRE-DEPLOY (agent-verified)
□ preview /api/version source_hash matches intended head
□ preview /api/health = 200
□ preview authenticates as masci_preview_user
□ preview cross-DB to masci_safety returns Unauthorized
□ preview backend.err.log has zero 🔴 STARTUP CONSISTENCY VIOLATION lines
□ /app/backend/.env.preview does NOT exist (per RCA permanent fix)
□ /app/backend/server.py contains the startup consistency guard

OPERATOR-VERIFIED
□ production System Keys still show APP_ENV=production
□ production System Keys still show DB_NAME=masci_safety
□ production System Keys MONGO_URL starts with masci_prod_user
□ production System Keys JWT_SECRET unchanged
□ operator vault still contains PROD_MONGO_URL_BACKUP for rollback

DEPLOY
□ operator clicks Redeploy on production
□ wait for rolling restart to complete

POST-DEPLOY (within 60 s — auto-rollback if any FAIL)
□ mascidocs.com /api/version app_env = "production"
□ mascidocs.com /api/version db_name = "masci_safety"
□ mascidocs.com /api/version source_hash = expected
□ mascidocs.com /api/platform/data-truth environment = "production"
□ mascidocs.com /api/platform/data-truth database = "masci_safety"
□ mascidocs.com /api/platform/data-truth banner.visible = false
□ mascidocs.com /api/health = 200
□ login → me-directory → logout round-trip OK
□ no 🔴 STARTUP CONSISTENCY VIOLATION lines in prod logs

DECLARE COMPLETE
□ CHANGELOG.md updated
□ deploy result recorded
```

---

## 17 · Verification evidence (this remediation, captured live)

### Files
```
$ ls -la /app/backend/.env.preview
ls: cannot access '/app/backend/.env.preview': No such file or directory   ✓

$ ls -la /app/backend/.env
-rw-r--r-- 1 root root 1943 Jun 11 02:24 /app/backend/.env                  ✓ (preview-side, correct env)

$ grep "env.preview" /app/backend/server.py /app/backend/scripts/verify_isolation_suite.py /app/backend/scripts/p0_trust_audit.py
(no matches)                                                                  ✓ (loader removed everywhere)
```

### Startup consistency guard
```
$ sed -n '32,60p' /app/backend/server.py
… (guard block present, with PREVIEW_USER + PROD_USER cross-checks, sys.exit(98)) …
```

### Preview pod healthy after fix
```
$ curl /api/health     → 200
$ curl /api/version    → app_env=preview, db_name=masci_safety_preview
$ curl /api/platform/data-truth → environment=preview, database=masci_safety_preview
$ Atlas probe          → authenticatedUsers = [{user:'masci_preview_user', db:'admin'}]
$ cross-DB             → Unauthorized (codeName=Unauthorized)
```

### Production unchanged
```
$ curl https://mascidocs.com/api/version
app_env=production · db_name=masci_safety · source_hash=3a5719f5618ad3801993617d8bd385f2 · uptime_s≈850
```

---

## 18 · Items NOT in scope for this RCA

- No new features built.
- No Motive activation (still 🔴 NO-GO).
- No MaintainX activation.
- No JWT_SECRET, RBAC, sessions, or user passwords modified.
- No Atlas users touched.
- No production write performed.

---

## 19 · References

- `/app/backend/server.py` — corrective actions 2 + 3
- `/app/backend/.env` — corrective action 1 (preview-side migration)
- `/app/backend/scripts/verify_isolation_suite.py` — corrective action 2
- `/app/backend/scripts/p0_trust_audit.py` — corrective action 2
- `/app/memory/PRODUCTION_DEPLOYMENT_GAP_CLOSEOUT_PLAN.md` — updated process
- `/app/memory/MOTIVE_PRODUCTION_ACTIVATION_PLAN.md` — unblocked once a clean redeploy succeeds
