# MASCI Operations Platform — Deployment Checklist

_Locked 2026-08-04 (Track 20.9). Supersedes the 2026-05-15 checklist locked at iter142._
_Owner: jaymn.judd@mascigc.com. Single source of truth for every production push to `mascidocs.com`._

Every production push MUST pass this checklist in order. Any failure is a hard stop until remediated.

---

## 0 · Pre-flight (Track 20.8 release-gate certification)

Every release passes a Track-20.8-style certification pass. See `memory/TRACK_20_8_EXECUTIVE_DEPLOYMENT_REPORT.md` for the doctrine and `memory/TRACK_20_9_EXECUTIVE_SUMMARY.md` for the latest cleanup pass.

- [ ] **Full regression envelope green** — run the Track-20.8 envelope:
  ```
  cd /app && REACT_APP_BACKEND_URL="<preview>" python -m pytest \
    backend/tests/test_track_20_8_deployment_certification.py \
    backend/tests/test_track_20_6b_test_hardening.py \
    backend/tests/test_track_20_7_universal_photo_capture.py \
    backend/tests/test_track_20_9_cleanup.py \
    backend/tests/test_track_19_62_fire_protection_phase_a.py \
    backend/tests/test_track_20_6_fire_protection_audit.py \
    backend/tests/test_track_19_21_e2e_live.py \
    backend/tests/test_daily_reports.py \
    backend/tests/test_job_photos.py \
    --timeout=180
  ```
  Expected: **all passed · 0 skipped · 0 failed**.
- [ ] **Deployment-agent static scan** — confirms no hardcoded secrets, correct `/api` prefixing, CORS, supervisor, env-vars.
- [ ] **Frontend build clean** — `cd /app/frontend && yarn build` returns exit 0.
- [ ] **Frontend lint gate** — `cd /app/frontend && yarn lint` reports no new `no-undef` / `no-unreachable` / `no-dupe-args` / `react/jsx-no-undef` errors versus the last release. Cosmetic categories (`react/no-unescaped-entities`, `no-empty` on storage `catch`) are tracked as Class-C tech debt in the register.
- [ ] **`memory/TECHNICAL_DEBT_REGISTER.md`** — every row that entered this release is marked FIXED, CLOSED, or D · False Positive. Zero OPEN Class-A or Class-B rows.

---

## 1 · Email-Safety Certification (MANDATORY)

The Track 20.6B synthetic-test-record short-circuit (`_dispatch_auto_email` in `backend/server.py`) prevents live email delivery for any record with `project_name` starting `TEST_`.

- [ ] **Source-level presence check** — the short-circuit is present in `_dispatch_auto_email` and runs BEFORE `auto_email_enabled()`:
  ```
  grep -A2 'startswith("TEST_")' /app/backend/server.py | head -5
  ```
- [ ] **Runtime evidence** — during the pre-flight test envelope run, backend logs show:
  ```
  auto-email skipped (Track 20.6B synthetic-test-record gate) — <workflow> <id> project_name='TEST_...'
  ```
- [ ] **Grep confirms no email transports** in any test file touched by this release:
  ```
  grep -l 'fsi_send_email\|resend.emails.send\|/api/email/send' backend/tests/*.py
  # Must return empty
  ```
- [ ] **Every workflow submit test uses `TEST_`-prefixed `project_name`** — no exceptions.

---

## 2 · Photo Capture Smoke (Track 20.7 lock)

The Track 20.7 fix ensures desktop users without a webcam still see a working file picker.

- [ ] Load preview `/daily/submit` in a headless / no-webcam browser.
- [ ] Confirm "Take Photo" button relabels to **CHOOSE FROM FILES**.
- [ ] Confirm hint reads **"Camera unavailable — choose a file instead"**.
- [ ] Confirm both hidden inputs exist: gallery (no `capture` attr) + camera (`capture="environment"`).
- [ ] Click the button — page does NOT crash. Browser opens the OS file chooser.
- [ ] Load same URL on iPhone Safari (real camera). Confirm the native camera intent fires normally.

---

## 3 · Operational Threads Smoke

Every Universal Operational Thread must render on preview before deploy.

- [ ] `/admin` — Admin console renders (super-admin login).
- [ ] `/pm/command-center` — PM Command Center loads.
- [ ] `/hr` — HR Hub renders.
- [ ] `/safety` — Safety Hub renders.
- [ ] `/shop` — Shop console renders.
- [ ] `/dispatch-portal` — Dispatch Hub renders (**canonical route — not `/dispatch`**).
- [ ] `/daily/submit` — Public Daily Report intake renders (unauthenticated).
- [ ] `/pm/projects/<any-real-project-id>` — Project Thread renders with real data.
- [ ] `/admin/employees/<any-real-employee-id>` — Employee Thread renders.
- [ ] `/admin/vendors/<any-real-vendor-id>` — Vendor Thread renders.
- [ ] `/admin/assets/<any-real-asset-id>` — Asset Thread renders.
- [ ] `/admin/incidents/<any-real-incident-id>` — Incident Thread renders.
- [ ] `/shop/units/<any-real-unit-id>` — Fleet Unit Thread renders + surfaces linked fire extinguishers (Track 19.62 Phase A).

---

## 4 · Environment-variable diff (must run before push)

Production env vars live in the Emergent deploy dashboard. Preview env vars live in `/app/backend/.env` and `/app/frontend/.env`.

| Key | Preview | Production | Notes |
|---|---|---|---|
| `MONGO_URL` | local pod | **prod Atlas cluster** | Never commit atlas creds |
| `DB_NAME` | `test_database` | **`masci`** | |
| `REACT_APP_BACKEND_URL` | preview URL | **`https://mascidocs.com`** | Frontend .env |
| `CORS_ORIGINS` | `*.preview…` regex | **`https://mascidocs.com,https://www.mascidocs.com`** | hard list — no wildcards |
| `CORS_ORIGIN_REGEX` | set (default) | empty | preview-only fallback |
| `AUTO_EMAIL_REPORTS` | `true` (safe via TEST_ gate) | **`true`** | activates Resend fan-out |
| `RESEND_API_KEY` | preview key | **production key** | separate |
| `SCHEDULER_ENABLED` | `false` | **`true`** | backup / digest / asset-spine loops |
| `S3_ENDPOINT_URL` / `S3_BUCKET` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` | preview R2 | **prod R2** | separate bucket |
| `ADMIN_HMAC_SECRET` | 64+ char | **NEW 64+ char** | rotate on every prod push |
| `ADMIN_SESSION_EPOCH` | `1` | **bump** | forces universal re-login |
| `EMERGENT_LLM_KEY` | set | set | universal |
| `GIT_COMMIT` / `BUILT_AT` | unset | **set at deploy** | shows up in `/api/version` |

- [ ] Diff complete — every prod-only key is set.
- [ ] All API keys verified via **live integration health probe** (`/api/admin/integrations/health`) — not just by string comparison.

---

## 5 · Post-deploy smoke (run against `https://mascidocs.com`)

### Backend
- [ ] `curl https://mascidocs.com/api/health` → `{"ok": true, ...}`
- [ ] `curl https://mascidocs.com/api/health/full` → 200 with `backup_recent: true`
- [ ] `curl https://mascidocs.com/api/version` → returns the SHA you just pushed
- [ ] `POST /api/auth/multi-login` with super-admin creds returns a full portal_tokens bundle (admin + pm + hr + safety + shop + dispatch + field_leadership).
- [ ] `/api/admin/deploy-readiness` returns `overall_status` in (`ready`, `attention`) — NOT `blocked`.
- [ ] `/api/admin/integrations/health` returns all probes `ok` or `disabled` (never `error`).

### Frontend
- [ ] `https://mascidocs.com` loads Hub home in < 3s.
- [ ] Sign-in as super-admin lands on `/admin`.
- [ ] All portal aliases render (`/admin`, `/pm`, `/hr`, `/safety`, `/shop`, `/dispatch-portal`).
- [ ] One sample Daily Report submission with a **real** project_name completes — email dispatches (check Resend dashboard).
- [ ] Trust-spine events for that submission show the full lifecycle: `routing_resolved → recipients_built → notification_queued → provider_accepted → completed`, all `status="ok"`.

---

## 6 · Post-deploy monitoring (first 24 hours)

- [ ] Watch `/api/health/full` for degradation (Uptime Robot / equivalent).
- [ ] Watch Resend delivery dashboard for bounces / delayed sends.
- [ ] Watch `trust_spine_events` for `status="failed"` at any stage on real submits. Any failure → triage.
- [ ] Watch `trust_spine_events` for `failure_reason="synthetic_test_record"` — expected to be empty on production (real data never uses `TEST_` prefix). If any appear, investigate.
- [ ] Watch backend supervisor for restarts — a crash loop (>3 restarts/hour) triggers rollback.
- [ ] Watch backup scheduler — expect a fresh backup within 26h.
- [ ] Bump `ADMIN_SESSION_EPOCH` post-deploy → force every active token to re-validate.

---

## 7 · Rollback

See `memory/TRACK_20_8_ROLLBACK_CHECKLIST.md` for the full playbook.

Fast rollback: **Emergent platform → Builds → Rollback** next to the last-known-good SHA. Confirm. Re-run §5 smoke.

Never `git reset` on production. The Emergent rollback preserves audit + backup state; git reset does not.

---

## 8 · Known-mocked integrations (read before you ship)

Passive / MOCKED — must NOT trigger live writes to third parties from prod:
- **MaintainX** — work orders surfaced via `operations_events.linked_maintainx_work_order_id` with `MaintainX WO (mocked)` marker. No live API.
- **Motive** — telematics framework only. No live API.

Both surface as `status: disabled` in `/api/admin/integrations/health`. Do NOT change `MAINTAINX_API_KEY` / `MOTIVE_API_KEY` in production env vars until formally adopted (guardrail locked 2026-05-14).

---

_Last updated: 2026-08-04 (Track 20.9). Bump this date whenever the procedure changes._
