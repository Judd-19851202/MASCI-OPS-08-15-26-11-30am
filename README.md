# MASCI Operations Platform

Field-first operations, safety, and asset-management platform for MASCI. Built as a React SPA + FastAPI backend on MongoDB with Cloudflare R2 for object storage and Resend for transactional email.

Production URL: **https://mascidocs.com**
Preview URL pattern: `https://<pod>.preview.emergentagent.com`

---

## Table of contents
1. [Architecture at a glance](#architecture-at-a-glance)
2. [Boot the platform locally](#boot-the-platform-locally)
3. [Run the tests](#run-the-tests)
4. [Frontend lint](#frontend-lint)
5. [Deploy](#deploy)
6. [Rollback](#rollback)
7. [Environment variables](#environment-variables)
8. [Health checks](#health-checks)
9. [Email-safety rule (READ BEFORE TESTING)](#email-safety-rule-read-before-testing)
10. [Track discipline](#track-discipline)
11. [Common runbooks](#common-runbooks)

---

## Architecture at a glance
- **Frontend** — React 19 SPA (CRA + craco), single-page router with 300+ routes, single canonical `PhotoUpload.jsx` control cascaded to 16 consumer forms, single canonical multi-portal login (`POST /api/auth/multi-login` — Track 15.32).
- **Backend** — FastAPI on Uvicorn, bound to `0.0.0.0:8001`, 300+ routes all prefixed `/api`. Supervisor-managed.
- **Database** — MongoDB via Motor (async). Collection layout described in `/app/memory/PRD.md`.
- **Object storage** — Cloudflare R2 (Track iter64 photo storage + Track iter429 attachment retention).
- **Email** — Resend transactional. Auto-dispatch gated by `AUTO_EMAIL_REPORTS`. **Synthetic-test-record short-circuit** in `_dispatch_auto_email` (Track 20.6B) — any record with `project_name` starting `TEST_` is short-circuited before Resend with a trust-spine `status="skipped"` audit.
- **Universal Operational Threads** — Employee · Project · Incident · Vendor · Asset (Equipment) · Fire Protection. Each thread has a lock test suite under `backend/tests/test_track_19_*.py` / `test_track_20_*.py`.
- **Trust Spine** — Track 15.76 event backbone that emits lifecycle stages for every workflow (routing → recipients → notification → provider → completed / skipped / failed). Powers dashboards + audit.

---

## Boot the platform locally
Services are supervisor-managed inside the container. **Do not run uvicorn or `yarn start` directly** — go through supervisor.

```bash
# Restart both services (only needed on .env or dependency changes;
# code changes hot-reload automatically).
sudo supervisorctl restart backend
sudo supervisorctl restart frontend

# Status
sudo supervisorctl status

# Tail backend logs (foreground)
tail -f /var/log/supervisor/backend.err.log
tail -f /var/log/supervisor/backend.out.log
```

Frontend hot-reloads on file save. Backend hot-reloads on file save (uvicorn `--reload`).

---

## Run the tests

```bash
# The Track-20.8 deployment gate — runs the full regression envelope
cd /app && REACT_APP_BACKEND_URL="<preview or prod URL>" python -m pytest \
  backend/tests/test_track_20_8_deployment_certification.py \
  backend/tests/test_track_20_6b_test_hardening.py \
  backend/tests/test_track_20_7_universal_photo_capture.py \
  backend/tests/test_track_19_62_fire_protection_phase_a.py \
  backend/tests/test_track_20_6_fire_protection_audit.py \
  backend/tests/test_track_20_5_asset_thread_audit.py \
  backend/tests/test_track_20_4_vendor_thread_audit.py \
  backend/tests/test_track_19_21_e2e_live.py \
  backend/tests/test_daily_reports.py \
  backend/tests/test_job_photos.py \
  --timeout=180

# Latest release-gate result (Track 20.9 · 2026-08-04): 385+ passed · 0 skipped · 0 failed
```

Individual suites:
```bash
python -m pytest backend/tests/test_daily_reports.py -v
python -m pytest backend/tests/test_job_photos.py -v
```

---

## Frontend lint
Track 20.9 introduced a **real** ESLint 9 gate (previous `lint` script was a stub).

```bash
cd /app/frontend
yarn lint            # Reports errors + warnings (does not fail on warn-only)
yarn lint:strict     # Fails on any warning — CI-mode
yarn build           # CRA build (production compile + internal ESLint pass)
```

The config lives at `/app/frontend/eslint.config.js` and mirrors the platform's static-analyzer rules. Track 20.9 fixed two Class-A undefined-identifier bugs it caught (`restoreRow` in `MasterListPanel.jsx`, `branding` in `TrenchBoxPosterCard.jsx`). Remaining lint findings are cosmetic tech debt (see `memory/TRACK_20_9_CLEANUP_REPORT.md`).

---

## Deploy
See **`DEPLOYMENT_CHECKLIST.md`** — the single source of truth. Track 20.8 release-gate certification is a prerequisite for every production push.

Fastest path:
1. Land all changes via the Emergent "Save to GitHub" flow.
2. Trigger prod deploy from the Emergent dashboard.
3. Run the smoke section of `DEPLOYMENT_CHECKLIST.md`.
4. Watch `/api/health/full` on production for 24h.

**Never** manually `git push`. Direct users to the Emergent Save-to-GitHub feature.

---

## Rollback
See `memory/TRACK_20_8_ROLLBACK_CHECKLIST.md`.

Fastest: **Emergent platform → Builds → Rollback** next to the last-known-good SHA. Confirm. Re-run the smoke section of `DEPLOYMENT_CHECKLIST.md`.

Never manually `git reset` on production. The Emergent rollback preserves audit + backup state; git reset does not.

---

## Environment variables

### Backend (`/app/backend/.env`)
Required in all environments:
- `MONGO_URL` — MongoDB connection string (never hardcoded in source).
- `DB_NAME` — target database name.
- `EMERGENT_LLM_KEY` — universal Emergent LLM key.

Production-only:
- `AUTO_EMAIL_REPORTS=true` — enables Resend auto-dispatch on real records.
- `RESEND_API_KEY` — Resend transactional key.
- `SCHEDULER_ENABLED=true` — enables background schedulers (backup, digest, asset-spine).
- `S3_ENDPOINT_URL` / `S3_BUCKET` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` — Cloudflare R2 credentials.
- `ADMIN_HMAC_SECRET` — 64+ char rotating secret.
- `ADMIN_SESSION_EPOCH` — bump to force universal re-login.
- `CORS_ORIGINS` — production allow-list (`https://mascidocs.com,https://www.mascidocs.com`). Preview leaves this empty and the regex fallback covers `*.preview.emergentagent.com` + `*.emergent.host`.
- `GIT_COMMIT` / `BUILT_AT` — set at deploy; surfaces in `/api/version`.

### Frontend (`/app/frontend/.env`)
- `REACT_APP_BACKEND_URL` — externally-reachable backend origin. Never hardcode API URLs in source; always read from this variable.

---

## Health checks

```bash
# Basic
curl https://mascidocs.com/api/health          # {"ok": true, ...}

# Deep (mongo · scheduler · backup_recent · integrations)
curl https://mascidocs.com/api/health/full     # {"ok": true, "backup_recent": true, ...}

# Deployment readiness (super-admin token required)
curl -H "X-Admin-Token: $TOKEN" https://mascidocs.com/api/admin/deploy-readiness
```

Every deploy MUST show:
- `/api/health` → 200
- `/api/health/full` → 200 with `backup_recent: true`
- `/api/admin/deploy-readiness` → `overall_status` in (`ready`, `attention`) — NEVER `blocked`.

---

## Email-safety rule (READ BEFORE TESTING)

**ANY test suite that hits a workflow-submit endpoint (`POST /api/daily-reports`, `POST /api/incidents`, `POST /api/meetings`, etc.) MUST use a `TEST_`-prefixed `project_name`.**

The synthetic-test-record short-circuit in `backend/server.py::_dispatch_auto_email` intercepts these records and emits a trust-spine `status="skipped"` audit BEFORE any Resend call:

```python
if record["project_name"].startswith("TEST_"):
    await emit_workflow_stage(..., status="skipped",
                              failure_reason="synthetic_test_record")
    return
```

This is the ONLY reason it is safe to run the test envelope against the preview environment where `AUTO_EMAIL_REPORTS=true` and `RESEND_API_KEY` is real. Any test that skips the prefix will fire real email to real inboxes. Track 20.6B doctrine.

**Never** set `AUTO_EMAIL_REPORTS=true` locally without also verifying every test file in scope uses `TEST_` prefixes.

---

## Track discipline
Every release passes through a Track:
- **Feature tracks** (19.xx) — new capability.
- **Audit tracks** (20.0–20.5) — forensic review of an existing thread.
- **Cleanup tracks** (20.6B, 20.9) — test hardening, tech-debt closure, non-behavioral cleanup.
- **Release gates** (20.7 photo capture, 20.8 final certification) — go/no-go verdicts.

Every track produces:
- Executive summary + fix reports.
- Zero-Drift Matrix.
- Test Report.
- Ledger updates (`PRD.md`, `CHANGELOG.md`, `TECHNICAL_DEBT_REGISTER.md`).
- A lock test at `backend/tests/test_track_<n>_*.py`.

Discovered issues are classified per Track 20.6A doctrine:
- **A · Fix Now** — inside the same track.
- **B · Blocks Deployment** — must remediate before ship.
- **C · Existing Tech Debt** — safe to defer, must register.
- **D · False Positive** — evidence required.

---

## Common runbooks

### The backend won't start / supervisor shows `BACKOFF`
```bash
tail -100 /var/log/supervisor/backend.err.log
# Fix the traceback (typically: missing pip package after requirements bump)
pip install -r /app/backend/requirements.txt
sudo supervisorctl restart backend
```

### A user reports "Take Photo did not open the camera"
This is closed by Track 20.7. Verify the fallback:
1. Open `/daily/submit` on the affected device.
2. Confirm the button relabels to **CHOOSE FROM FILES** with hint "Camera unavailable — choose a file instead" when no webcam is present.
3. Confirm on mobile the camera intent still fires normally.

### A user reports "I clicked Restore but nothing happened"
This was TD-20.9-A01 — fixed in Track 20.9. If it reproduces after deploy, the fix regressed. Compare `MasterListPanel.jsx::restoreRow` against `memory/TRACK_20_9_CLEANUP_REPORT.md`.

### Rotating the admin HMAC secret
1. Generate a new 64+ char random string.
2. Update `ADMIN_HMAC_SECRET` on the Emergent env dashboard.
3. Bump `ADMIN_SESSION_EPOCH`.
4. Redeploy.
5. All active sessions will invalidate; users re-login via multi-login.

---

_Last updated: 2026-08-04 (Track 20.9)._
