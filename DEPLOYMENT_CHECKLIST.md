# MASCI Operations Platform — Deployment Checklist

_Locked 2026-05-15 (iter142, Phase-1 Iter D). Author: main agent. Owner: jaymn.judd@mascigc.com._

This is the single source of truth for every production push to **`mascidocs.com`**.
Run through it linearly — every step is intentional. If any check fails, **STOP** and resolve before continuing.

---

## 0 · Pre-flight (5 min)

- [ ] **Pull latest preview build** — confirm `/api/version` `commit` matches the git SHA you intend to ship.
- [ ] **Run** `python3 /app/scripts/qa_audit.py` — open `/app/QA_PERF_AUDIT.md`, confirm:
  - 0 rows show `❌ SCAN` in the Query Plan Audit table.
  - 0 rows show `❌` in the TTL Coverage Audit table.
- [ ] **Login as Super Admin** (`jaymn.judd@mascigc.com`) → `/admin/deploy-readiness`:
  - Overall banner must read **READY TO DEPLOY** OR **ATTENTION REQUIRED** (warns only). **`DEPLOY BLOCKED` is a hard stop.**
  - Scroll to **Live Integration Probes** panel — `mongo` and `r2` must be `ok`. `resend` `ok` if you plan to send password-reset emails. `maintainx` and `motive` `disabled` is expected (MOCKED).
  - Click **Re-run + Alert** — note any new rows appear in `/api/admin/integrations/alerts`.
- [ ] **Last-known-good build** is also surfaced separately at `/admin/deploy-recovery` (rollback playbook page) — distinct from the readiness page.

---

## 1 · Environment Variable Diff (must run before push)

Production env vars live in the **Emergent deploy dashboard**. Preview env vars live in `/app/backend/.env`.
Run the diff below — production-only keys are highlighted **bold**.

| Key | Preview | Production | Notes |
|---|---|---|---|
| `MONGO_URL` | local pod | **prod Atlas cluster** | NEVER share atlas creds in git |
| `DB_NAME` | `test_database` | **`masci`** | |
| `CORS_ORIGINS` | `*.preview…` regex | **`https://mascidocs.com,https://www.mascidocs.com`** | hard-coded — no regex |
| `CORS_ORIGIN_REGEX` | `(set)` | empty | preview-only |
| `RATE_LIMITING` | `off` | **`on`** | |
| `AUTO_EMAIL_REPORTS` | `false` | **`true`** | activates Resend fan-out |
| `RESEND_API_KEY` | set | **set (production key)** | NOT the test key |
| `S3_ENDPOINT_URL` / `S3_BUCKET` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` | preview R2 | **prod R2** | separate bucket |
| `ADMIN_HMAC_SECRET` | 64+ char | **NEW 64+ char** | rotate at every prod push |
| `ADMIN_SESSION_EPOCH` | `1` | bump | **bumping forces re-login** for everyone |
| `EMERGENT_LLM_KEY` | set | set | universal — same key everywhere |
| `SUPER_ADMIN_BOOTSTRAP_PASSWORD` | set | **unset after first boot** | wipe once `user_directory` is seeded |
| `GIT_COMMIT` | unset | **set at deploy** | shows up in `/api/version` |
| `BUILT_AT` | unset | **set at deploy** | shows up in `/api/version` |

- [ ] Diff complete — every prod-only key is set.
- [ ] All API keys verified by reading the integration probe panel post-deploy (NOT just by comparing strings).

---

## 2 · Smoke Tests (run in order)

Use the **production** URL after deploy completes. Each step is ~10 seconds.

### Backend
- [ ] `curl https://mascidocs.com/api/health` returns `{"ok": true, ...}`
- [ ] `curl https://mascidocs.com/api/version` returns the SHA you just pushed
- [ ] `POST /api/auth/multi-login` with the Super Admin creds returns a token
- [ ] `GET /api/admin/deploy-readiness` (with that token) returns `overall_status` in (`ready`, `attention`) — NOT `blocked`
- [ ] `GET /api/admin/integrations/health` returns 6 probes, all `ok` or `disabled`

### Frontend
- [ ] `https://mascidocs.com` loads the Hub home in <3 seconds
- [ ] `/admin/login` accepts Super Admin creds and routes to `/admin`
- [ ] `/safety-portal/login` accepts the seeded safety user
- [ ] `/pm/login`, `/shop/login`, `/hr/login`, `/dispatch-portal/login` all render their login forms
- [ ] One sample equipment master edit dialog opens, scrolls cleanly, and renders the iter140/141 Cross-Portal Footprint + History panels

---

## 3 · Supervisor Restart Sequence

If you ever need to restart services on the production pod:

```bash
# Backend FIRST so it's ready when frontend reconnects
sudo supervisorctl restart backend
sleep 5
sudo supervisorctl status backend       # must be RUNNING
curl https://mascidocs.com/api/health   # must return ok:true

# Frontend last
sudo supervisorctl restart frontend
sleep 5
sudo supervisorctl status frontend
```

If `backend` shows `BACKOFF` or `FATAL`, check `/var/log/supervisor/backend.err.log` and **DO NOT** restart frontend until backend recovers.

---

## 4 · Rollback Playbook (last-known-good)

The platform commits one snapshot at every Emergent build step. **The fastest rollback is the Emergent platform's `rollback` button.**

1. **Identify last-known-good build** — `/admin/deploy-recovery` → "Build Version Stamps" panel. Pick the SHA labelled "ready (no warns)".
2. **Open the Emergent platform** → Builds → click **Rollback** next to that SHA. Confirm.
3. **Re-run §2 smoke tests** against `mascidocs.com` after rollback completes.
4. **If MongoDB schema changed since that SHA**, the rollback could leave orphaned fields. The platform handles this gracefully (extra fields are ignored), but capture a backup BEFORE rollback by visiting `/admin/system` → **Trigger Backup Now**.

### Hard recovery (rollback button unavailable)
- SSH to the production pod.
- `cd /app && git log --oneline -20`
- `git checkout <known-good-sha>`
- `sudo supervisorctl restart backend frontend`
- Run §2 smoke tests.

---

## 5 · Post-Deploy Tasks (30 min after push)

- [ ] Bump `ADMIN_SESSION_EPOCH` in the Emergent env dashboard → force every active token to re-validate.
- [ ] Watch `/api/admin/integrations/health?emit_alerts=true` for 5 min — any new alerts in `/api/admin/integrations/alerts` get triaged.
- [ ] Confirm `db.audit_events` is receiving new login events (NOT just the seed).
- [ ] Confirm one **manual Pre-Op inspection submission** triggers the Shop fan-out email (only if `AUTO_EMAIL_REPORTS=true`).
- [ ] Capture a **fresh backup** via `/admin/system` → Trigger Backup Now.
- [ ] Update `/app/memory/PRD.md` with the new build SHA + deploy timestamp.

---

## 6 · Known-Mocked Integrations (read before you ship)

These are **passive / MOCKED** and explicitly **must not** trigger live writes to third parties from a production deploy:

- **MaintainX** — work orders surfaced via `operations_events.linked_maintainx_work_order_id` with a `MaintainX WO (mocked)` subtitle marker. No live API.
- **Motive** — telematics framework only. No live API.

Both surface as `status: disabled` in the integration health panel. **Do not change** `MAINTAINX_API_KEY` / `MOTIVE_API_KEY` in production env vars until the live API is formally adopted (architectural guardrail locked 2026-05-14).

---

_Last updated: 2026-05-15. Bump this date whenever the procedure changes._
