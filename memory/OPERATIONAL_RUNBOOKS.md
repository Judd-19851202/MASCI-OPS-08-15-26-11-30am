# MASCI Operational Runbooks — Phase Sigma (iter437)

**Audience:** On-call operator / platform owner.
**Companion docs:** `ATLAS_ALERTS_RUNBOOK.md` (alert config), `REGRESSION_STRATEGY.md` (gating), `PHASE_RESTORE_DRILL_ATLAS_BLOCKER.md` (forensic precedent), `ROLE_ACCESS_CERTIFICATION.md` (auth proof), `PERFORMANCE_FORENSICS.md` (perf state).
**Discipline:** Every runbook entry must end at a green proof state. Never declare "done" without a verification step.

---

## RB-01 — Restore failure (R2 → preview)

**Trigger:** `python3 tools/restore_drill.py <zip>` exits non-zero, or partial restore leaves preview DB in a half-state.

**Triage**
1. Read tail of `/tmp/restore_drill*.log` for the actual Atlas error.
2. Check `GET /api/cluster/capacity` — if `severity != ok`, jump to **RB-02**.
3. Verify the zip wasn't corrupted: `unzip -t /tmp/restore_source.zip | tail -5`.

**Containment**
1. **Stop the restore script** if still running: `pkill -f restore_drill.py`.
2. **Identify partial-write collections** in preview:
   ```bash
   python3 -c "
   import os; from pathlib import Path
   for line in Path('/app/backend/.env').read_text().splitlines():
       if '=' not in line or line.strip().startswith('#'): continue
       k,_,v = line.partition('='); os.environ.setdefault(k.strip(), v.strip().strip('\"').strip(\"'\"))
   from pymongo import MongoClient
   db = MongoClient(os.environ['MONGO_URL'])['masci_safety_preview']
   for c in sorted(db.list_collection_names()):
       s = db.command('collStats', c)
       if s.get('count',0) > 0:
           print(f'  {c}: {s[\"count\"]} docs, {s[\"storageSize\"]/1e6:.2f} MB')
   "
   ```
3. **Drop the partial collections** (preview only — never touch prod):
   ```bash
   python3 -c "
   import os; from pathlib import Path
   for line in Path('/app/backend/.env').read_text().splitlines():
       if '=' not in line or line.strip().startswith('#'): continue
       k,_,v = line.partition('='); os.environ.setdefault(k.strip(), v.strip().strip('\"').strip(\"'\"))
   from pymongo import MongoClient
   assert os.environ['DB_NAME'].endswith('_preview'), 'NOT preview — ABORT'
   db = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
   for c in ['<list-from-step-2>']:  # fill in
       db.drop_collection(c)
   "
   ```

**Recovery**
1. Re-download the source backup if it's gone (often `/tmp` is wiped on restart):
   ```bash
   python3 -c "<re-download snippet — see Phase Restore certification §11>"
   ```
2. Run a clean wipe-then-restore (matches certified flow):
   ```bash
   # Wipe preview entirely (preview only — guardrail in tools/restore_drill.py)
   python3 -c "
   import os; from pathlib import Path
   for line in Path('/app/backend/.env').read_text().splitlines():
       if '=' not in line or line.strip().startswith('#'): continue
       k,_,v = line.partition('='); os.environ.setdefault(k.strip(), v.strip().strip('\"').strip(\"'\"))
   from pymongo import MongoClient
   assert os.environ['APP_ENV']=='preview' and os.environ['DB_NAME'].endswith('_preview')
   db = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
   for c in db.list_collection_names(): db.drop_collection(c)
   "
   # Then restore
   cd /app/backend && python3 tools/restore_drill.py /tmp/restore_source.zip
   ```
3. **Re-bootstrap the super-admin** (restored user_directory has prod password hashes that won't match `SUPER_ADMIN_BOOTSTRAP_PASSWORD`):
   ```bash
   python3 -c "
   import os; from pathlib import Path
   for line in Path('/app/backend/.env').read_text().splitlines():
       if '=' not in line or line.strip().startswith('#'): continue
       k,_,v = line.partition('='); os.environ.setdefault(k.strip(), v.strip().strip('\"').strip(\"'\"))
   from pymongo import MongoClient
   db = MongoClient(os.environ['MONGO_URL'])['masci_safety_preview']
   r = db.user_directory.delete_many({'is_super_admin': True})
   print(f'deleted {r.deleted_count}')
   "
   sudo supervisorctl restart backend
   # backend's _bootstrap_user_directory() will rewrite the row from env
   ```

**Verification (PROOF REQUIRED)**
```bash
# (a) Capacity OK
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2) && curl -fsS "$URL/api/cluster/capacity"
# (b) Regression suite green
cd /app/backend && python3 -m pytest tests/regression/test_critical_flows.py -q
# (c) Playwright green
cd /app/backend && python3 -m pytest tests/pw_suite/test_critical_flows_pw.py -q
```
All three exit 0 = restore recovery COMPLETE.

---

## RB-02 — Quota saturation (Atlas `Writes are blocked`)

**Trigger:** Banner shows `⛔ DATABASE WRITES MAY FAIL — cluster at capacity` OR API responses surface `OperationFailure: you are over your space quota`.

**Triage**
1. `GET /api/cluster/capacity` — record exact `storage_used_mb` and `storage_used_pct`.
2. Identify the largest-growth collection in the last 24h via R2 backup deltas:
   ```bash
   # latest backup size vs 24h prior
   python3 -c "<see PHASE_RESTORE_DRILL_ATLAS_BLOCKER §7 growth-analysis snippet>"
   ```

**Containment (preview-side only — never touch prod)**
- If the bloat originated from a recent restore/preview test: drop the partial preview collections per **RB-01**.
- Do NOT run `db.dropDatabase()` or anything else against `masci_safety`.

**Resolution paths (in priority order)**
1. **Tier upgrade** (correct fix per Phase R precedent): M10 → M20 via Atlas dashboard. Online migration. After: bump `ATLAS_QUOTA_MB` in `/app/backend/.env`, restart backend.
2. **Targeted lifecycle reclaim** — only with explicit approval per directive:
   - Drop preview if appropriate (zero prod impact).
   - Apply pending TTL recommendations from `PERFORMANCE_FORENSICS.md` § 4 (idempotency_keys patch).
3. **Manual purge of bloat collections** — last-resort, requires explicit operator sign-off.

**Verification**
- Banner returns to `severity=ok`.
- Probe write into preview succeeds.
- Regression suite green.

---

## RB-03 — Failed deploy rollback

**Trigger:** A production deploy fails one of the three gates in `REGRESSION_STRATEGY.md` § 3.

**Immediate response (within 5 min)**
1. **Do NOT promote** the failed build. Mark the build as `failed` in Emergent dashboard.
2. **Identify the gate** that failed:
   - Gate A (API regression): which assertion?
   - Gate B (Playwright): which flow + which viewport? Screenshot at `/app/test_reports/playwright/`.
   - Gate C (capacity): hard block — go to **RB-02**.

**Rollback steps**
- Emergent platform: use the **Rollback** feature (do not git-reset, per platform rules) to revert to the last green deploy.
- Once rollback is live, re-run all three gates against the rolled-back production URL to confirm baseline.

**Postmortem**
1. Triage the failure on preview using `OPERATIONAL_RUNBOOKS.md` decision tree.
2. Document root cause in a new `PHASE_*.md` artifact under `/app/memory/`.
3. DO NOT re-attempt the deploy until the regression suite green-lights against preview.

---

## RB-04 — Production isolation failure

**Trigger:** `/api/version` reports `app_env=production` but `db_name` looks like a `_preview` DB, or vice-versa. OR: the `env_safety_check` fixture in any pytest run fails with `REFUSING TO RUN`.

**Severity:** P0 — STOP all writes immediately.

**Triage**
1. Confirm symptom: `curl <pod_url>/api/version | jq '.app_env, .db_name'`.
2. Check `/app/backend/.env`:
   ```bash
   grep -E '^(APP_ENV|DB_NAME)' /app/backend/.env
   ```
3. Check supervisor logs for the startup safety check:
   ```bash
   grep -E '(REFUSING|app_env|DB_NAME)' /var/log/supervisor/backend.*.log | tail -20
   ```

**Resolution**
1. **STOP the backend** if it's running mismatched: `sudo supervisorctl stop backend`.
2. **Fix `.env`** to align APP_ENV and DB_NAME (preview → `*_preview`, production → no suffix).
3. **Restart**: `sudo supervisorctl restart backend`. The startup check in `server.py` will refuse to start if still misaligned — that's the desired behavior.
4. If misalignment caused writes, see `PHASE_RESTORE_DRILL_ATLAS_BLOCKER.md` § 12 for the original incident pattern; treat affected writes as suspect.

**Verification**
- `/api/version` reports the correct pair.
- Regression suite `test_env_identity_*` green.
- Playwright `test_public_hub_renders_with_env_banner` shows the correct banner.

---

## RB-05 — Attachment integrity drift (R2 references not resolving)

**Trigger:** Frontend reports broken photos / 404 on `/api/job-photos/.../thumb-signed` / restore-drill verification reports missing R2 keys.

**Triage**
1. Pick a sample failed key. Run:
   ```bash
   python3 -c "
   import os, boto3; from pathlib import Path
   for line in Path('/app/backend/.env').read_text().splitlines():
       if '=' not in line or line.strip().startswith('#'): continue
       k,_,v = line.partition('='); os.environ.setdefault(k.strip(), v.strip().strip('\"').strip(\"'\"))
   s3 = boto3.client('s3', endpoint_url=os.environ['S3_ENDPOINT_URL'],
       aws_access_key_id=os.environ['S3_ACCESS_KEY'], aws_secret_access_key=os.environ['S3_SECRET_KEY'], region_name='auto')
   key = '<paste-the-failing-key>'
   try: print(s3.head_object(Bucket=os.environ['S3_BUCKET'], Key=key))
   except Exception as e: print('MISSING', e)
   "
   ```
2. If the key truly doesn't exist in R2, search for it in any available historical backup zip in R2:
   ```bash
   # the backup zip itself may contain the photo bytes
   unzip -l /tmp/restore_source.zip | grep <photo-name>
   ```

**Resolution**
- Single missing photo → log it; the application should degrade gracefully (alt text + placeholder).
- Systematic missing photos (>10) → suspend any cleanup automation on R2; check Cloudflare R2 lifecycle policies (`R2_LIFECYCLE_ACTIVATION.md`, `R2_RETENTION_AUDIT.md`).

**Verification**
- Sample 20 random photos from the latest restore drill — all should pass `s3.head_object`. Recorded proof in `PHASE_RESTORE_DRILL_ATLAS_BLOCKER.md` § 7 (37/37 verified).

---

## RB-06 — Regression suite failure handling

**Trigger:** `pytest tests/regression/test_critical_flows.py` exits non-zero.

**Triage by test name**

| Failing test                                    | Most likely root cause                              | First action                              |
|-------------------------------------------------|------------------------------------------------------|--------------------------------------------|
| `test_env_identity_*`                           | Preview pod misaligned with `_preview` DB           | RB-04                                      |
| `test_multi_login_*`                            | Super-admin bootstrap broken                        | Restart backend; check `[directory]` logs  |
| `test_portal_me[*]`                             | Specific portal token mint broken                    | Inspect that portal's auth route          |
| `test_hr_token_cannot_act_as_admin` / `test_pm_token_cannot_act_as_hr` / `test_random_token_is_rejected` | **AUTH SECURITY REGRESSION** | **P0 SECURITY INCIDENT** — see RB-09     |
| `test_critical_lists[*]`                        | A list endpoint returns non-200                      | Curl the specific endpoint; check logs    |
| `test_hr_perf_budget[*]`                        | DB perf regression (projection reverted?)           | `git log routes/hr_portal.py`              |
| `test_no_auth_protected_endpoints_401[*]`       | Auth gate REMOVED from a protected endpoint          | **P0 SECURITY INCIDENT** — see RB-09     |
| `test_reference_data_*`                         | Preview DB wiped / drifted                          | Re-run restore drill (RB-01)              |
| `test_cluster_capacity_*`                       | Cluster probe endpoint broken                       | Inspect `routes/cluster_capacity.py`       |

**Verification:** suite returns `N passed in <10s` with all 43 (or current total) green.

---

## RB-07 — Playwright flow failure handling

**Trigger:** `pytest tests/pw_suite/test_critical_flows_pw.py` exits non-zero.

**Triage**
1. Open the failure artifact at `/app/test_reports/playwright/<test>.png` for the visual.
2. Open `<test>.json` for the URL at failure + console-log tail.

**Flow-specific guidance**

| Flow                                          | What it tests                                           | If failing, check                          |
|-----------------------------------------------|---------------------------------------------------------|--------------------------------------------|
| `test_public_hub_renders_with_env_banner`     | App shell loads + preview banner visible                | SplashOverlay stuck; React build failed   |
| `test_cluster_capacity_reachable_from_browser`| CORS + endpoint reachability from browser fetch         | Check `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` |
| `test_admin_login_round_trip[mobile]` only    | Mobile-specific selector issue                          | Check responsive form layout              |
| `test_admin_can_reach_daily_reports`          | Token injection + critical API + restored data         | If 0 docs returned, restore drill needed  |
| `test_logout_clears_portal_tokens`            | `/api/auth/multi-logout` + localStorage discipline      | Logout endpoint regression                |

**Verification:** `15 passed in <60s` (or current total).

---

## RB-08 — Cluster CPU / Connection alert spike

**Trigger:** Atlas alert fires for CPU > 75% / Connections > 1200.

**Triage**
1. `GET /api/cluster/capacity` — should still be `ok` (CPU alerts can fire without storage stress).
2. Check `/admin/system` panel for active sessions count + recent backup status.
3. Identify recent deploys via Emergent dashboard — a new query plan can spike CPU.

**Containment**
- If connection-leak suspected: `sudo supervisorctl restart backend` (resets the connection pool). NOT a fix, but buys time.
- If runaway query: identify via Atlas Performance Advisor (UI). Document the query in a fresh `PHASE_*.md` artifact.

**Resolution**
- Index recommendations from Performance Advisor.
- M10 → M20 upgrade if CPU sustained > 50% for 7 days.

---

## RB-09 — AUTH SECURITY INCIDENT (P0)

**Trigger:** A negative-path regression assertion fails:
- `test_hr_token_cannot_act_as_admin`
- `test_pm_token_cannot_act_as_hr`
- `test_random_token_is_rejected`
- `test_no_auth_protected_endpoints_401[*]`

OR the role access probe shows an unexpected 200.

**Severity:** **P0** — possible privilege escalation in production.

**Immediate response**
1. **HALT all deploys** to production.
2. **Bump `ADMIN_SESSION_EPOCH`** in production .env to invalidate every active token (see `test_credentials.md` § "Force re-login for ALL active users").
3. **Run the full role-access probe** against production (NOT preview) to determine blast radius:
   ```bash
   # Point ROLE_CERT_BASE_URL at production, run probe, save log
   ```

**Postmortem**
- File the incident artifact under `/app/memory/PHASE_SECURITY_INCIDENT_<date>.md`.
- Identify the offending PR/commit via `git log` on the affected file (`grep -l <route>` in `routes/` and `server.py`).
- Add a regression test that locks the gap closed; only un-halt deploys after the test is green.

---

## RB-10 — Regression suite latency drift

**Trigger:** Regression suite total runtime exceeds 30s (baseline ~9s; Playwright ~36s).

**Why it matters:** A slow suite gets skipped or ignored. The deploy gate's value depends on the operator actually running it.

**Triage**
1. Run with `-v --durations=10` to find the slowest tests.
2. Common culprits: network latency to preview pod, Atlas cold start, missing index added recently.

**Resolution**
- Add timeouts to test fixtures (already in `conftest.py` — `set_default_timeout(20_000)`).
- If a specific test is consistently slow, profile its endpoint via `tools/perf_probe.py` and treat as a perf incident (RB-08 / PERFORMANCE_FORENSICS.md).

---

## Appendix A — Standing proof-points

| Check                                        | Command                                                                |
|----------------------------------------------|------------------------------------------------------------------------|
| Env identity (preview vs prod)               | `curl -s $URL/api/version`                                            |
| Cluster capacity                             | `curl -s $URL/api/cluster/capacity`                                   |
| Regression suite green                       | `cd /app/backend && python3 -m pytest tests/regression -q`            |
| Playwright suite green                       | `cd /app/backend && python3 -m pytest tests/pw_suite -q`              |
| Role access probe green                      | `cd /app/backend && python3 tools/role_access_probe.py`               |
| Perf probe green                             | `cd /app/backend && python3 tools/perf_probe.py`                      |
| Backend supervised + responsive              | `sudo supervisorctl status backend && curl -fsS $URL/api/health`      |

---

## Appendix B — When to call the on-call human

Page the operator if:
1. `/api/version` returns 500 for > 60 s.
2. Cluster `severity=critical` for > 5 min.
3. ANY of the 4 security-class regression tests fail (RB-09).
4. Production deploy gates fail and rollback also fails.
5. Restore drill rollback fails — preview DB stuck in a half-state.

For everything else: run the appropriate RB, log evidence, hand off at next shift.
