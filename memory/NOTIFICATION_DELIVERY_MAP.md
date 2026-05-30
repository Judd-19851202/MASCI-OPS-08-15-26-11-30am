# NOTIFICATION_DELIVERY_MAP

**Date:** 2026-02-01 · Part of the Platform Truth Map
**Method:** Static trace of `pm_routing.py`, `lib/event_fanout.py`, `routes/tasks_notifications.py`, `safety_digest.py`, `health_monitor.py`, env-driven recipients in `/app/backend/.env`. Cross-checked against `WORKFLOW_LIFECYCLE_MAP.md`.

---

## 1 · Email routing — the canonical rule

Defined in `/app/backend/pm_routing.py`:

```
ALWAYS_CC = ["jaymn.judd@mascigc.com", "safety@mascigc.com"]
COMPLIANCE_KINDS = {"inspection", "meeting", "jha", "incident"}
PM_ONLY_KINDS    = {"daily-report", "equipment-inspection"}
```

Resolution flow (`recipients_for_record_async(db, record, kind)`):

1. Look up assigned PM from `db.jobs_master[project_number].pm_email`.
2. Fallback to `pm_email` matched by `project_manager` name through `db.project_managers`.
3. If kind ∈ `COMPLIANCE_KINDS` → CC includes `ALWAYS_CC` (office + safety).
4. If kind ∈ `PM_ONLY_KINDS` → ONLY the assigned PM (no always-CC).
5. If no PM resolvable → fallback `["jaymn.judd@mascigc.com"]` (super-admin sink — see `pm_routing.py` lines 216 / 293).

Auto-email gate: `auto_email_enabled()` returns true iff `RESEND_API_KEY` is set AND `AUTO_EMAIL_REPORTS=true`. Preview disables it; production enables it.

Classification: **🟢 KNOWN GOOD** — single source of truth, DB-backed, admin-introspectable via `/api/auto-email/preview` and `/api/auto-email/routing-table`.

---

## 2 · Email distribution recipients by kind

| Kind | To | CC | Trigger endpoint | Source module |
|------|----|----|------------------|---------------|
| `inspection` | assigned PM | `ALWAYS_CC` (jaymn.judd + safety@) | `POST /api/inspections` | `routes/safety.py:318` |
| `meeting` | assigned PM | `ALWAYS_CC` | `POST /api/meetings` | `routes/safety.py:464` |
| `jha` | assigned PM | `ALWAYS_CC` | `POST /api/jhas` | `routes/safety.py:518` |
| `incident` | assigned PM | `ALWAYS_CC` + `severe_incident_cc` (when high severity / OSHA) | `POST /api/incidents` | `routes/safety.py:579` |
| `daily-report` | assigned PM | — (no always-CC) | `POST /api/daily-reports` | `routes/daily_reports.py:218` |
| `equipment-inspection` | assigned PM (+ all active shop users on FAIL/OOS, fallback `SHOP_MANAGER_EMAIL`) | — | `POST /api/equipment-inspections` | `routes/equipment.py:199 + 247` |
| `qaqc` | assigned PM | `ALWAYS_CC` | `POST /api/qaqc-inspections` | `routes/qaqc.py:210` |
| `po-request` (event-driven) | approver chain; PM Manager digest | per `email_routing_config` | `POST /api/po-requests` | `routes/po_requests.py:220+242` |
| `leadership form (10 kinds)` | `leadership_always_to` (default safety@ + admin) | per DB override | `POST /api/field-leadership/portal/forms` | `routes/field_leadership_users.py` |
| `safety-form-issuance / training` | `SAFETY_FORMS_EMAIL_TO` (default safety@ + jaymn.judd) | — | `POST /api/safety-forms/...` | `routes/safety_forms_*.py` |
| `backup-failure` | `BACKUP_EMAIL_TO` (or safety@ fallback) | — | scheduler / `health_monitor` | `health_monitor.py:49+200`, `server.py:5299/5374/6003` |
| `payroll-variance-weekly-digest` | `PAYROLL_VARIANCE_EMAIL_TO` | — | weekly cron | `server.py:10241` + cron tick |
| `safety-digest-weekly` | `SAFETY_DIGEST_TO_EMAIL` (default safety@) | — | Monday 14:00 UTC cron | `safety_digest.py` |
| `system-red-alert` | admin emails | — | `health_monitor._send_alert` | `health_monitor.py:49` |
| `directory-welcome / reset` | recipient user | — | admin action | `server.py:10027 _directory_send_email` |
| `pm-welcome / shop-welcome / hr-welcome / safety-welcome / dispatch-welcome / fl-welcome` | recipient user | — | admin action | per-portal `_send_email` helpers in `server.py` |
| `job-photos-share` | designated PM/Safety | — | `server.py:8336 _job_photos_send_email` | server.py |
| `field-leadership-pdf-attachment` | recipients | — | `server.py:8376 _field_leadership_send_email` | server.py |
| `dispatch driver magic-link` | driver phone (SMS via Resend SMS bridge or email) | — | dispatch assignment | `dispatch_magic_links` |

The hard list of "where each email fires" is in `truth_map_data/notification_calls.csv` (helper function locations only) plus `routes/safety.py`, `routes/daily_reports.py`, `routes/equipment.py`, `routes/qaqc.py`, `routes/po_requests.py`, `routes/field_leadership_users.py`, `routes/safety_forms_*.py` for the `schedule_auto_email(...)` and `emit_task_and_notification(...)` call sites.

Classification: **🟢 KNOWN GOOD** for every confirmed kind. SOFT-gap kinds (`jha`, `leadership-form`, `safety-form`) ship email but lack in-app fan-out — see §4.

---

## 3 · In-app bell + task fan-out

Architecture (Phase E):

- Every operational write that wants to drive operator action calls **`lib.event_fanout.emit_task_and_notification(...)`** (or directly `task_service.create()` + `notification_service.fanout()`).
- `task_service.create()` writes to `db.tasks` AND emits a `task.assigned` notification automatically (one bell per assignee role).
- An additional topical notification can ride along (e.g. `incident.created`, `preop.failed`).
- Notifications surface in `NotificationBell.jsx` on every portal chrome via `GET /api/notifications` and the digest endpoints.

Call-sites confirmed:
- `routes/safety.py:331` (inspection / meeting fan-out)
- `routes/safety.py:585` (incident fan-out)
- `routes/equipment.py:234+247` (preop FAIL/OOS fan-out)
- `routes/qaqc.py:217+222` (qaqc fan-out)
- `routes/asset_transfers.py:161+173+214` (transfer fan-out)
- `routes/po_requests.py:220+242` (PO fan-out)
- `routes/document_expirations.py:232+237` (doc-expiry cron fan-out)
- `routes/employee_lifecycle.py:713` (HR onboard checklist fan-out)
- `routes/tasks_notifications.py:150/191/246/474` (task service primitives)

Classification: **🟢 KNOWN GOOD** — single canonical entry point.

---

## 4 · Per-portal digest endpoints

| Endpoint | Auth | Output |
|----------|------|--------|
| `GET /api/admin/notifications/digest` | admin | Admin operator digest |
| `GET /api/safety/notifications/digest` | safety | Safety operator digest |
| `GET /api/hr/notifications/digest` | HR | HR digest |
| `GET /api/pm/notifications/digest` | PM | PM digest |
| `GET /api/dispatch/notifications/digest` | dispatch | Dispatch digest |
| `GET /api/fl/notifications/digest` | FL | FL digest |
| `GET /api/field-leadership/portal/notifications-recent` | FL | FL "recent" feed for portal home |

Classification: **🟢 KNOWN GOOD** — wired in `routes/notifications.py`.

---

## 5 · Cron-driven notifications

| Cron | Owner | What it does |
|------|-------|-------------|
| Weekly Safety Digest (Mon 14:00 UTC) | `safety_digest.py` | Aggregates last-7-days safety surface → email `SAFETY_DIGEST_TO_EMAIL` |
| Nightly Backup Pipeline (target) | `lib/singleton_scheduler.py` + `server.py` | Atlas dump + R2 push + drift check + Backup Health write · 🔴 SCHEDULER DEAD (GAP-7) — manual run still works |
| Nightly Document Expirations | `routes/document_expirations.py` | Scan `employees` / `documents` → emit `task_service.create` for HR |
| Nightly PO Receipt-Missing | within PO endpoints | Flag rows > X days without receipt → bell + task |
| Periodic Health Monitor | `health_monitor.py` | Probe red/amber cards → `_send_alert` email + audit |
| Cluster Capacity Check | `routes/cluster_capacity.py` | Sample MongoDB cluster signal → admin badge |

Classification: **🟢 KNOWN GOOD** for cron registration paths. Live-firing of every cron in production cannot be verified from static analysis — that requires runtime trace (out of scope for this map).

---

## 6 · Notification gaps (consolidated)

From `NOTIFICATION_GAP_REGISTER.md` (2026-05-29) — re-validated 2026-02-01 against current code:

| # | Gap | Status this map |
|---|-----|-----------------|
| GAP-1 | FL 10 forms — no bell/task fan-out | 🟡 still present in `routes/field_leadership_users.py` |
| GAP-2 | Safety Forms — no bell/task fan-out | 🟡 still present in `routes/safety_forms_*.py` |
| GAP-3 | JHA submit — no task to Safety supervisor | 🟡 still present in `routes/safety.py:518` (only `schedule_auto_email`, no `emit_task_and_notification`) |
| GAP-4 | Training assigned — supervisor of trainee not notified | 🟡 still present in `routes/training_center.py` |
| GAP-5 | Payroll Variance manual — no fan-out | 🟡 still present |
| GAP-6 | Fleet DVIR — no notification path | ⚫ ORPHAN-1, awaiting operator |
| GAP-7 | Backup scheduler dead | 🔴 BROKEN, P0 HELD |
| GAP-8 | Daily Report Weather YES — no schedule-impact task | 🟡 P2 stop-list intentional |
| GAP-9 | Daily Report Equipment-Issue YES — no Pre-Op auto-link | 🟡 P2 |
| GAP-10 | Shop Equipment Trash button — 403 | 🟡 cosmetic |
| GAP-14 | Severe Incident — no no-response escalation | 🟡 P2 |
| GAP-15 | PO no-receipt > 30d — no higher-tier escalation | 🟡 P2 |

Classification rollup: 2 P0 (1 OPERATOR DECISION NEEDED, 1 HELD BROKEN), 5 P1, 5 P2, 3 P3 test-only (GAP-11/12/13).

---

## 7 · Notification ownership matrix (who acts when bell fires)

| Notification topic | Bell goes to | Email mirror to | Action expected |
|--------------------|--------------|-----------------|-----------------|
| `inspection.created` | PM assignee | PM + ALWAYS_CC | PM acknowledge |
| `incident.created` | PM + Safety | PM + ALWAYS_CC + severe-CC | Safety triage |
| `incident.severe` | Safety chain | severe-CC | Safety escalate |
| `preop.failed` / `preop.oos` | Shop role | All active shop users | Shop sign-off / repair |
| `po.submitted` | approver | approver | Approve / reject / clarify |
| `po.receipt-missing` (cron) | requester + PM | inherit | Upload receipt |
| `transfer.requested` | receiving location | receiving + Dispatch | Receive sign-off |
| `corrective-action.assigned` | assignee | assignee | Complete CA |
| `doc-expiring` (cron) | HR | HR | Renew |
| `training.assigned` | trainee | optional | Complete (supervisor not yet — GAP-4) |
| `backup.failed` (when scheduler alive) | Admin | BACKUP_EMAIL_TO | Investigate |
| `system.red` | Admin | admin emails | Investigate |
| `task.assigned` (generic Phase E) | assignee_role | — | Act per task body |

Classification: **🟢 KNOWN GOOD** — matrix matches code.

---

## 8 · What's missing / unmapped

- **Push notifications (FCM / APNs)**: NOT implemented (grep confirms zero references except an ops-manual aspirational mention).
- **WebSocket / SSE live push**: NOT implemented (zero references).
- All real-time signal is **poll-based**: every portal chrome polls `/api/notifications/unread-count` periodically. This is by design per the audit; the map records it for transparency.

Classification: ⚫ OPERATOR DECISION NEEDED — confirm whether real-time push is desired or current polling is intentional.
