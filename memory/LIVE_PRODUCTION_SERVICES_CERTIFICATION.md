# LIVE PRODUCTION · SERVICES CERTIFICATION
## OMEGA Directive · Phase 8 of 10

**Date**: 2026-06-03
**Target**: https://mascidocs.com (production)

---

## 🟡 PHASE 8 VERDICT — PARTIAL CERTIFICATION (BACKEND CORE 🟢 · ANCILLARY SERVICES REQUIRE OPERATOR)

External probes confirm the core backend is running with Sentry enabled and session-timeout discipline configured. Scheduler, notifications, backups, webhooks, photo viewer, email, and file storage cannot be fully certified from outside — checklist below.

---

## 1 · What the agent verified externally

| Service | Probe | Result |
|---|---|:-:|
| Backend health | `GET /api/health` | 🟢 200 — `{"ok":true,"service":"masci-hub"}` |
| Backend uptime stability | `GET /api/version` started_at timestamp | 🟢 stable since 2026-06-03T09:21:50Z |
| Sentry error capture | `/api/version` `sentry.enabled` | 🟢 `true` |
| Session timeout discipline | `/api/version` `session_timeouts` | 🟢 ADMIN_HR (15m / 4h), OPERATIONS (30m / 8h), FIELD (60m / 12h) |
| Edge / DDOS layer | response `server` header | 🟢 Cloudflare in front |
| HSTS | response header | 🟢 `max-age=63072000; includeSubDomains; preload` |
| Database name | `/api/version` `db_name` | 🟢 `masci_safety` |
| App environment | `/api/version` `app_env` | 🟢 `production` |

🟢 **Core backend services posture is correct.**

---

## 2 · Services requiring operator-side verification

### 2.1 · Scheduler operational
- [ ] Verify in Admin → Scheduler / Cron dashboard that:
  - Scheduled jobs ran in the last 24 hours
  - No failed jobs in the queue
  - The singleton-lock acquired by one worker (not multiple)

### 2.2 · Notifications operational
- [ ] Trigger a notification-producing action (e.g., submit a Daily Report) and verify:
  - In-app notification delivered to the intended recipient
  - Email notification (if RESEND_API_KEY configured) delivered within 5 minutes

### 2.3 · Backups operational
- [ ] Verify the last MASCI_full_backup_*.zip in production storage is within the last 24 hours
- [ ] Verify the backup file size is non-trivial (≥ 100 MB for a populated DB)
- [ ] Verify no `.tmp.*` orphaned backup files (these indicate aborted backups; preview pod recently had 1.4 GB of orphans, since cleaned — please verify the same is not happening on prod)

### 2.4 · Recovery operational
- [ ] (Covered in Phase 5 walkthrough) — Recovery Stream + Universal Undo

### 2.5 · Webhooks operational
- [ ] Trigger a webhook-producing event (e.g., Resend delivery webhook)
- [ ] Verify `RESEND_WEBHOOK_SECRET` validation passes (this test is part of the pre-deploy regression suite and the `test_hotfix_bundle_a_webhook_secret.py` test PASSES; live verification is the operator's final confirmation)

### 2.6 · Photo viewer operational
- [ ] Upload a photo to a Daily Report or Incident
- [ ] Reopen the record and confirm the photo renders in the viewer
- [ ] Confirm no console errors in the photo lightbox

### 2.7 · Email operational
- [ ] Trigger an automated email (e.g., equipment inspection completion) on a project where `AUTO_EMAIL_REPORTS=true`
- [ ] Verify the email arrives at the intended recipient within 5 minutes
- [ ] Note: the preview pod has `RESEND_API_KEY missing` and `AUTO_EMAIL_REPORTS=false` by design — production must have these set in Emergent Production Deploy panel for live email to flow

### 2.8 · File storage operational
- [ ] Upload a file (image, PDF) to any workflow
- [ ] Re-load the page and confirm the file persists with correct URL
- [ ] Confirm download works
- [ ] Confirm file size limits enforced for over-large uploads (graceful error, not 500)

---

## 3 · Health-status summary table

| Service | Probable status | Confidence |
|---|:-:|---|
| Backend HTTP | 🟢 | HIGH (live probe) |
| Sentry | 🟢 enabled | HIGH (`/api/version`) |
| Session timeout enforcement | 🟢 configured | HIGH (`/api/version`) |
| Database connectivity | 🟢 (implied by health endpoint success) | MEDIUM |
| Scheduler | UNVERIFIED | requires operator |
| Notifications | UNVERIFIED | requires operator |
| Backups | UNVERIFIED | requires operator |
| Webhooks | UNVERIFIED | requires operator |
| Photo viewer | UNVERIFIED | requires operator |
| Email | UNVERIFIED | requires operator |
| File storage | UNVERIFIED | requires operator |

---

## 4 · Phase 8 outcome

🟡 **PARTIAL CERTIFICATION** — Backend core CERTIFIED 🟢; ancillary services require operator-side verification using the checklist above.
