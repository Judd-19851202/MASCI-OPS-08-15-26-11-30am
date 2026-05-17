# MASCI Hub — Mandatory Deploy Checklist

> Status: **ACTIVE — Effective immediately**
> Owner: MASCI Operations
> Last updated: 2026-02-XX (Phase 2 hardening)

This checklist is the single source of truth for what MUST happen before
clicking the Emergent "Deploy" button on `mascidocs.com`. Every step is
binary: ✅ passed or ❌ blocker. **No exceptions.**

A production deploy that skipped any step below is a process violation,
even if the build was urgent and "looked fine."

---

## 0. CI vs Deploy — discipline boundary

**Read this first.** GitHub Actions (`/.github/workflows/ci.yml`) and
Emergent Deploy are two different things and protect against two
different classes of failure. Do not confuse them.

| Surface | What it does | What it does NOT do |
|---|---|---|
| GitHub Actions CI | Static gate on every push/PR: Python syntax compile + ruff errors + frontend lint + frontend production build | Run live backend tests · validate auth/RBAC behaviour · check scheduler/R2/backup health · trigger a deploy |
| `bash scripts/pre_deploy_check.sh` (preview env) | **Operational deploy gate** — runs the full backend pytest suite (incl. auth + RBAC critical paths) against a live preview backend + Mongo | Touch production · push code · invoke deployment |
| Emergent Deploy button | Pushes preview to production (`mascidocs.com`) | Read GitHub Actions status · read CI exit codes · enforce any external gate |

**Discipline:**

- **GitHub Actions passing is necessary, but not sufficient.** A green CI
  badge does not prove auth, RBAC, scheduler, or backup behaviour. It
  only proves the code compiles and the frontend builds.
- **`pre_deploy_check.sh` is the binding gate for production deploys.**
  It must exit 0 in the preview environment before the Emergent Deploy
  button is clicked.
- **A human approves every production deploy.** Emergent Deploy does not
  read CI status, does not run pre-deploy checks, and does not run
  post-deploy smoke tests on its own. All three are operator
  responsibilities, enforced by this checklist.
- **CI alone never protects production.** Do not describe it that way in
  documentation, ticket descriptions, or status reports.

---



Run, in this order, from `/app`:

```bash
bash scripts/pre_deploy_check.sh
```

This must exit `0`. It enforces:

- ✅ Backend syntax compile (server.py + routes/)
- ✅ Backend lint (ruff — errors only)
- ✅ Frontend lint (eslint)
- ✅ Frontend production build
- ✅ Auth + RBAC critical-path tests (test_admin_auth, iter172, iter174,
       iter175, iter176, iter177, iter179, iter180, iter126_dispatch_auth,
       iter155_admin_pm)
- ✅ Full backend pytest suite

If anything fails: **STOP. Do not deploy.** Fix in preview first.

---

## 2. Testing-agent sweep (after non-trivial changes)

For any change that touches auth, RBAC, scheduler, backup pipeline,
identity mirror, role templates, or cross-portal routing, run the
testing agent (`testing_agent_v3_fork`) on the preview environment and
attach the resulting `/app/test_reports/iteration_*.json` to the deploy
ticket. Resolve every reported issue **before** deploying — not after.

---

## 3. Auth verification (live preview)

- ✅ Admin login → can read `/api/admin/*`
- ✅ HR user → can NOT read `/api/admin/*`
- ✅ PM token → can NOT read `/api/admin/*` (iter180)
- ✅ Cross-portal sign-out wipes session tokens (iter179)
- ✅ Catch-all route renders `NotFound` (iter181)

Quick probe:

```bash
python3 /app/iter181_iter182_prod_verification.py --base <preview-or-prod>
```

---

## 4. Health verification

- ✅ `GET /api/health` returns 200 with `{ok: true}`
- ✅ `GET /api/healthz` returns 200
- ✅ `GET /api/health/full` returns 200 with `mongo=true scheduler=true backup_recent=true`
- ✅ `GET /api/version` returns commit + source_hash; matches local

```bash
python3 /app/scripts/post_deploy_check.py --base https://mascidocs.com
```

---

## 5. Backup scheduler verification (iter182)

- ✅ `GET /api/admin/backups-scheduler-state` shows `seconds_since_last_tick < 3600`
- ✅ `recent_health` history shows the last entry was within the
       expected cadence (hourly lite, nightly full)
- ✅ No "backup overdue" email has fired in the last 24h **without** an
       actual missed window (no false-positive storm)

---

## 6. R2 (object storage) verification

- ✅ R2 bucket size below 50 GB alert threshold —
       `python3 /app/scripts/r2_usage_check.py` (thresholds: 45 GB warn / 50 GB alert; overridable via `R2_USAGE_WARN_GB` / `R2_USAGE_ALERT_GB`)
- ⏳ Lifecycle policy present (90-day expiration on `backups/auto-90d/`) — **NOT yet active in production.** Apply with `python3 /app/scripts/r2_lifecycle_apply.py` once the R2 token has `Workers R2 Storage = Edit`. See `/app/memory/R2_RETENTION_AUDIT.md`.

---

## 7. Regression smoke (post-deploy on production)

Within 10 minutes of clicking Deploy:

- ✅ `mascidocs.com/` loads (no Cloudflare 520)
- ✅ Login as a real user from each portal (HR / Shop / PM / Safety / Dispatch / Admin)
- ✅ At least one read-write action per portal (e.g. file a daily report,
       open a JHP, view employee directory)
- ✅ Browser console: zero red errors on any portal hub

---

## 8. Sentry verification (once DSNs configured)

Sentry is scaffolded but **inactive in production today** — no DSN is
set, so the SDK is a silent no-op. The verifications below apply only
once DSNs are added and the backend/frontend are redeployed:

- ⏳ Sentry dashboard receiving frontend errors with `env=production`
- ⏳ Sentry dashboard receiving backend exceptions with `env=production`
- ⏳ No PII / tokens in any Sentry event (spot-check 5 latest events)

If `SENTRY_DSN` is unset, this section is informational only — do not
treat its checks as required for a production deploy until Sentry is
turned on.

---

## Roles & responsibilities

| Step | Owner |
|------|-------|
| 1, 2 | Engineering (agent + human reviewer) |
| 3, 4 | Engineering before deploy, Ops after deploy |
| 5    | Engineering on weekly cadence; Ops monitors emails |
| 6    | Engineering monthly |
| 7    | Ops within 10 min of every deploy |
| 8    | Engineering on Sentry-touch deploys, Ops weekly |

---

## Process violations log

Record any deploy that skipped a step (even if outcome was fine).
This log is reviewed monthly; repeated violations trigger a process review.

| Date | Deploy ID | Step(s) skipped | Reason | Outcome | Reviewer |
|------|-----------|-----------------|--------|---------|----------|
| _none yet_ | | | | | |
