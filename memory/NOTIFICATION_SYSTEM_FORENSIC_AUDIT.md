# Notification System Forensic Audit
**Mode:** READ-ONLY. Zero code changes. Zero deployment.
**Date:** 2026-02-07
**Scope:** Every notification, alert, email, digest, bell, dashboard alert, and escalation surface present in the MASCI platform today.

This is the master inventory. Per-trigger / per-template detail lives in `EMAIL_TEMPLATE_INVENTORY.md`, `RESEND_USAGE_AUDIT.md`, `ALERT_ENGINE_AUDIT.md`. The Trench Safety reuse plan lives in `TRENCH_SAFETY_NOTIFICATION_PLAN.md`.

---

## 1 · What notification systems exist today?

### 1.1 Unified Task + Notification Engine (the shared core)
File: `backend/routes/tasks_notifications.py` · iter150 (Phase 2.5).
- Two collections: `db.tasks` (operational task / action items) + `db.notifications` (central feed).
- Public Python services:
  - `task_service.create(db, payload)` — creates a task, auto-fanout to assignee role.
  - `notification_service.fanout(db, payload)` — drops a row into `db.notifications` keyed by recipient_role / recipient_id.
- HTTP API (any portal token, scoped to caller):
  - `GET    /api/tasks` · list with filters
  - `GET    /api/tasks/summary`
  - `GET    /api/tasks/{id}`
  - `POST   /api/tasks`
  - `PATCH  /api/tasks/{id}`
  - `POST   /api/tasks/{id}/comment`
  - `GET    /api/notifications` — bell feed
  - `GET    /api/notifications/unread-count` — header badge
  - `POST   /api/notifications/{id}/read`
  - `POST   /api/notifications/read-all`
  - `POST   /api/notifications/{id}/acknowledge`

### 1.2 NotificationBell (bell icon · frontend)
File: `frontend/src/components/NotificationBell.jsx`.
- Mounted in `AdminShell.jsx`, `SafetyShell.jsx`, `PmShell.jsx` — appears in every protected portal header.
- Reads from `/api/notifications`; calls `markRead`, `markAllRead`, `getUnreadCount` via `lib/tasksApi.js`.
- Severity icons / colours: Info (slate), Warning (amber), Critical (red).
- Sub-badge: amber "upload queued" indicator for offline-resiliency queue (iter166).

### 1.3 Event Fanout helper
File: `backend/lib/event_fanout.py`.
- `emit_task_and_notification(...)` + `emit_notification(...)` — convenience wrappers so source modules don't repeat boilerplate.
- Idempotency via dedupe keys on `db.event_dispatch_ledger`.

### 1.4 Operational Intelligence Digest (in-app, role-scoped)
File: `backend/routes/notifications.py` (separate from `tasks_notifications.py`).
- `GET /api/admin/notifications/digest`  (admin-strict)
- `GET /api/safety/notifications/digest` (safety_or_admin)
- Aggregates findings from iter354-356 detectors (governance, document expirations, payroll variance, daily-report gaps, etc.) into a role-scoped payload — NOT a separate collection.

### 1.5 Trench Safety alerts (derived view)
File: `backend/routes/trench_safety/alerts.py`.
- `GET /api/trench-safety/alerts` — computed on demand from `assets`, `holds`, `certifications`, `inspections`, `repairs`. No alerts collection.
- Kinds: `critical_damage`, `expired_certification`, `missing_certification`, `failed_inspection`, `hold_applied`, `due_soon_30`, `due_soon_60`.

---

## 2 · What email systems exist today?

### 2.1 Resend (transactional · the only sender)
- Library: `resend` Python SDK.
- API key: `RESEND_API_KEY` env (set in `/app/backend/.env`).
- Sender: `SENDER_EMAIL=noreply@mascidocs.com`.
- Reply-to: `REPLY_TO_EMAIL=jaymn.judd@mascigc.com`.
- Outbound gating: `AUTO_EMAIL_REPORTS=false` (preview env). Email-stub or "preview" path runs when either env is missing — see §5.

### 2.2 House-style wrappers (per-domain `_send_email` adapters)
All async, all Resend, all share the same gating rules:

| Wrapper | File | Domain |
|---|---|---|
| `_safety_send_email` | `server.py` ~9266 | Safety digest, safety portal password resets |
| `_hr_send_email` | `server.py` ~9190 | HR portal account / reset |
| `_po_digest_send_email` | `server.py` ~10147 | PO Request weekly digest |
| `_job_photos_send_email` | `server.py` ~8976 | Job-photo bundle email |
| `_directory_send_email` | `server.py` ~10856 | Auth directory invites |
| `fsi_send_email` | `lib/fsi_email_sender.py` | FSI (Field Submitter Identity) dispatcher — daily report / incident revision and access notices |

All wrappers behave consistently when keys/flags are missing: they log a stub line (`[xxx-stub]` / `[xxx-preview]`) and return False/None without raising — so preview environments never burn Resend quota.

### 2.3 Resend Webhook (inbound deliverability truth)
File: `backend/routes/resend_webhook.py` · iter452.5.2.
- Receives Resend webhook events: `delivered`, `bounced`, `complained`, `deferred`.
- Writes `notification_delivery_*` audit rows.
- Hard bounce on a Tier 1-4 recipient automatically escalates ownership to Tier 5 (dead letter) via `ADMIN_DEAD_LETTER_EMAIL=safety@mascigc.com`.

---

## 3 · What templates exist?
See `EMAIL_TEMPLATE_INVENTORY.md` for the full per-template record. Headline counts:

| Template family | Render path | Count |
|---|---|---|
| Auto-email per record-type (PDF attached) | `pdf_render.build_email_subject` + `_dispatch_auto_email` | 7 kinds (inspection / meeting / jha / incident / daily-report / equipment-inspection / qaqc) |
| Safety-office forms | `routes/safety_forms.py` via `build_email_subject_for_kind` | 3 kinds (issuance / return / training) |
| Field-leadership records | `routes/field_leadership.py` | 10 kinds (write_up, verbal_coaching, attendance, recognition, equipment_checkout, new_employee_eval, crew_eval, promotion_recommendation, training_deficiency, supervisor_notes), + employee_termination, time_off_request |
| Portal account / password reset HTML | per-portal renderers | 5 portals (PM, Shop, HR, Safety, Field Leadership) |
| Digests (weekly HTML) | `safety_digest.py`, `lib/operator_digest.py`, `po_digest.py`, `routes/safety_portal/digest.py` | 4 digest streams |
| Health / Backup / Outage alerts (admin-only) | `health_monitor.py`, `backup_verification.py`, `outage_alerts.py` | 3 admin alarms |
| Photo bundle email | `routes/job_photos.py` | 1 (with attachments) |
| FSI revision / reopen | `routes/daily_report_lifecycle.py`, `routes/incident_lifecycle.py` | 2 |
| Access / auth | `routes/auth_directory_routes.py`, `routes/pm_admin.py` | 2 |

Subject builder: `pdf_render.build_email_subject` / `build_email_subject_for_kind` enforce a uniform `[MASCI · <TAG>] <project> · <project_number> · <short_title> · <doc_id>` so Gmail/Outlook filters work platform-wide.

---

## 4 · What events trigger emails?
Quick summary (full per-event table in `EMAIL_TEMPLATE_INVENTORY.md`):

| Trigger source | Event | Email path |
|---|---|---|
| `routes/safety.py` POST inspection / meeting / jha / incident | record created | `schedule_auto_email(kind, record)` → PDF + email to dist |
| `routes/daily_reports.py` POST | daily report created | `schedule_auto_email("daily-report", doc)` |
| `routes/equipment.py` POST inspection | equipment inspection created | `schedule_auto_email("equipment-inspection", doc)` (Shop Manager only) |
| `routes/qaqc.py` POST | QA/QC record created | `schedule_auto_email("qaqc", doc)` |
| `routes/safety_forms.py` POST issuance / return / training | record created | `build_email_subject_for_kind` + send |
| `routes/field_leadership.py` (10 kinds) + termination + time_off | record created | dedicated sender per kind |
| `routes/daily_report_lifecycle.py` | revision requested | `fsi_send_email(subject="[MASCI] Daily Report revision needed — …")` |
| `routes/incident_lifecycle.py` | incident reopened / CA requested | `fsi_send_email(...)` |
| `routes/safety_portal/auth_users.py` | password reset / temp password | `_safety_send_email` |
| `routes/hr_portal.py` | password reset / new account | `_hr_send_email` |
| `routes/pm_routes.py` | PM password reset | `_directory_send_email` |
| `routes/field_leadership_portal.py` | password reset / new account | per-portal sender |
| `server.py` Shop password reset | reset | "[MASCI] Reset your Shop Portal password" |
| `routes/auth_directory_routes.py` | access account created | "[MASCI] Your access account — <action> (temporary password inside)" |
| `routes/pm_admin.py` | privileged action access change | `"[MASCI · ACCESS] {headline}"` |
| `routes/shop_parts.py` | parts request created/updated | `"[MASCI · PARTS] {unit_number} · …"` |
| `safety_digest.py` cron | Monday 14:00 UTC | Weekly Safety Digest |
| `lib/operator_digest.py` cron | Monday 14:00 UTC | Weekly Operations Digest |
| `po_digest.py` cron | Monday 14:00 UTC | PO Request weekly digest |
| `routes/safety_portal/digest.py` | manual or scheduled | safety portal digest |
| `backup_verification.py` cron | weekly | "[MASCI · BACKUP] Weekly Verification …" |
| `health_monitor.py` cron | every health pulse, when RED | "🚨 HEALTH FAIL · {n} subsystem(s)" |
| `outage_alerts.py` | platform outage detected | `🚨 PLATFORM OUTAGE · {issue_key}` (cooldown 15 min) |
| Backup silent alarm | `server.py:5812` | `[MASCI ALARM] Backup silent for {h}h — action needed` |
| `routes/job_photos.py` | photo bundle shared | `MASCI Photos — N photo(s)` |

---

## 5 · Who receives them?
- **Auto-email per record (safety/daily/equipment/qaqc):** PM-of-record + always-CC list resolved via `recipients_for_record_async` (`server.py`). `equipment-inspection` is overridden to **Shop Manager only**. `incident` with Major/Severe severity adds an extra CC list from `severe_incident_cc` routing key.
- **Digests:**
  - Safety Digest → `SAFETY_DIGEST_TO_EMAIL` env or admin-config routing key.
  - Operator Digest → `OPERATOR_DIGEST_RECIPIENTS` (comma-separated) → falls back to Safety Digest list.
  - PO Digest → every active PM (scoped to their assigned jobs) + every active HR user (platform-wide).
- **Alarms:** Health/Backup/Outage → `BACKUP_EMAIL_TO=jaymn.judd@mascigc.com` (also `SUPER_ADMIN_EMAIL`) and `OUTAGE_ALERT_TO` env.
- **Dead-letter:** `ADMIN_DEAD_LETTER_EMAIL=safety@mascigc.com` (set when Tier 1-4 resolution bounces).
- **Password resets / account emails:** the affected user only.

---

## 6 · What events trigger bell notifications?
All flow through `notification_service.fanout(db, {type, ...})`. Discovered event types:

| `type` | Source module | Recipient role |
|---|---|---|
| `task.assigned` | `routes/tasks_notifications.py` | assignee_role |
| `task.closed` | `routes/tasks_notifications.py` | original assigner |
| `po.approval_visibility` | `routes/po_requests.py` | admin / pm |
| `daily_report.pending_review` | `routes/daily_report_lifecycle.py` | pm |
| `fire_ext.deficiency` | `routes/safety_portal/fire_extinguishers.py` | safety |
| `payroll_variance.manual_run` | `routes/payroll_variance.py` | admin / hr |
| `asset_transfer.requested` | `routes/asset_transfers.py` | safety / dispatch |
| `asset_transfer.approved` | `routes/asset_transfers.py` | requester / dispatch |
| `asset_transfer.dispatch_pickup` | `routes/asset_transfers.py` | dispatch |
| `asset_transfer.in_transit` | `routes/asset_transfers.py` | requester |
| `asset_transfer.received` | `routes/asset_transfers.py` | requester (× 2 paths) |
| `asset_transfer.rejected` | `routes/asset_transfers.py` | requester |
| `preop.failed` | `routes/equipment.py` | shop manager (× 2 paths) |
| `document.expired` | `routes/document_expirations.py` | safety + hr |
| `inspection.deficiency` | `routes/safety.py` | safety (deficiency) |
| `inspection.stop_work` | `routes/safety.py` | safety + admin |
| `meeting.submitted` | `routes/safety.py` | safety |
| `jha.submitted` | `routes/safety.py` | safety |
| `incident.created` | `routes/safety.py` | safety + admin (× 2 paths) |
| `fl.submitted` | `routes/field_leadership.py` | safety / leadership |
| `qaqc.deficiency` | `routes/qaqc.py` | safety / qa (× 2 paths) |

Severity coloring: `Info`, `Warning`, `Critical` (rendered by `NotificationBell.jsx`).

**Trench Safety: NO `trench.*` types are fanned out today.** Holds, inspections, certifications, and repairs all write to `audit_events` but do not call `notification_service.fanout`. This is gap §10.

---

## 7 · What events trigger dashboard alerts?
- **Trench Safety Hub** (`/safety/trench-safety`) reads `GET /api/trench-safety/dashboard` which embeds an `alerts` object (computed from current state, not stored). Surfaces counts for: Inspection Hold, Maintenance Hold, Certification Hold, Safety Hold, certification due-soon-30/60, expired certs, missing tabulated data, failed inspections.
- **Trench Safety Alerts endpoint** (`GET /api/trench-safety/alerts`) returns the per-asset rows.
- **Safety Portal hub** uses the unified `/api/safety/notifications/digest` to surface governance / payroll / document expiration counts.
- **Admin Hub** uses `/api/admin/notifications/digest`.
- **NotificationBell** surfaces unread `db.notifications` for the caller.

No dashboard-only side-channel alerts — every alert is either a derived view over canonical collections or a row in `db.notifications`.

---

## 8 · Infrastructure Trench Safety should reuse
1. `task_service.create` + `notification_service.fanout` (`routes/tasks_notifications.py`) — for any future Trench Safety action requiring assignee follow-up (e.g. "TB-05 missing serial — Safety to verify").
2. `lib/event_fanout.emit_task_and_notification` — convenience wrapper, idempotent.
3. `_safety_send_email` (and the wider house-style email gating) — already shaped for "preview-safe" sending. Trench Safety digest, if added, should reuse this exact wrapper.
4. `pdf_render.build_email_subject_for_kind` — add `"trench-inspection"`, `"trench-cert"`, `"trench-repair"`, `"trench-hold"` tags to keep prefixes uniform.
5. `routes/resend_webhook.py` — bounce/complaint handling is already platform-wide; Trench Safety emails inherit it for free.
6. `routes/notifications.py` digest aggregator — add a `_build_safety_trench_section(db)` to surface trench alerts inside the existing Safety digest payload.
7. `db.audit_events` — Trench Safety already writes here. Notification rules can derive from these events instead of building a parallel store.
8. EN/ES translation layer in `frontend/src/lib/i18n.js` — every notification surface already pipes through it.

---

## 9 · Duplicated or abandoned notification surfaces
- **None outright abandoned**, but two adjacent stacks exist:
  - `routes/tasks_notifications.py` (operational notifications — bell feed) vs.
  - `routes/notifications.py` (intelligence digest payload — read-only aggregate).
  Both are intentional and have distinct contracts. Documenting the boundary is enough; no consolidation needed.
- Legacy `routes/admin_digest_config.py` overlaps with the modern `safety_digest.py` cron — both can email the Weekly Safety Digest. `admin_digest_config.py` is reachable for manual "send now" runs but the scheduled cron lives in `safety_digest.py`. Not duplicated by accident — they share the same renderer.
- `_safety_send_email`, `_hr_send_email`, `_po_digest_send_email` are intentionally separate so each domain's brand line / from-name / failure logging stays distinct. The shared sender is `lib/fsi_email_sender.py:fsi_send_email`. The wrappers exist as thin shims over the same library — not duplication.

---

## 10 · Gaps for Trench Safety operations

| # | Gap | Current state | Suggested reuse (no code yet) |
|---|---|---|---|
| G1 | No bell notification on **new public damage report** | `POST /trench-safety/public/damage-report` creates a `trench_safety_repairs` row but does NOT call `notification_service.fanout`. Safety + Shop see it only by polling the queue. | Reuse `lib/event_fanout.emit_notification` with `type: "trench_safety.damage_report"`, recipient_role: `safety`. |
| G2 | No bell notification on **inspection Fail Major/Critical** | `inspections.py` auto-opens Inspection Hold, but no fanout. | `type: "trench_safety.inspection_failed"`, recipient_role: `safety` (+ `shop` if `requires_reinspection`). |
| G3 | No bell notification on **hold opened** | Audit row only. | `type: "trench_safety.hold_opened"`, recipient_role: `safety`. |
| G4 | No bell notification on **certification expiring / expired** | Surfaces in dashboard counts only. | Reuse the `document_expirations.py` 30/60/90-day step pattern via the same `notification_service.fanout` invocation. |
| G5 | No bell notification on **shop completes repair → Safety verification needed** | Repair status flips to `Completed`; only the Shop queue surfaces it. | `type: "trench_safety.awaiting_safety_verification"`, recipient_role: `safety`. |
| G6 | No email for any trench safety event | Auto-email pipeline never adds `trench-*` kinds. | Add `trench-inspection`, `trench-hold`, `trench-cert`, `trench-repair` subject tags to `SUBJECT_TYPE_TAGS`; wire `schedule_auto_email` from the trench engines. |
| G7 | Weekly Safety Digest does not include trench safety metrics | `safety_digest.py` queries safety incidents / corrective actions but not `trench_safety_assets`. | Add a `_safety_trench_section` to the digest builder. |
| G8 | NotificationBell EN/ES strings already exist for tasks but **no trench notification strings yet** | i18n.js | Add EN→ES keys for each new `trench_safety.*` type. |
| G9 | Tier 5 dead-letter (`safety@mascigc.com`) does not yet receive trench safety-specific subject prefixes | OK behaviour, but cosmetically the bounce-handling subject line would benefit from a `[MASCI · TRENCH]` tag | Add `trench-safety` to `SUBJECT_TYPE_TAGS`. |
| G10 | Dashboard alerts on the public tile do **not** acknowledge field reports | The public dashboard shows fleet counts; reports posted from `/trench-safety/report` don't surface to crews on the public dashboard. | Out of scope — should remain Safety-only by directive. Not a real gap, mentioned for completeness. |

---

## End-state of audit
- All 5 deliverable files created in `/app/memory/`.
- Zero code changes performed.
- Zero deployments performed.
