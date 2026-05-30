# SYSTEM_TALK_MAP

**Date:** 2026-02-01 · Part of the Platform Truth Map
**Purpose:** Document which subsystems FEED which other subsystems — i.e., inter-system data flow. For each link: source · trigger · downstream consumer · channel (DB read · derived collection · API call · email · bell · cron).

> Static-evidence pass. Live runtime tracing is out of scope.

---

## Legend
- **`→`** = active feed (source writes; downstream reads or is notified)
- **`⇢`** = aspirational feed (would happen if a gap closes — currently NOT wired)
- Classification (per link): 🟢 / 🟡 / 🔴 / ⚪ / ⚫

---

## 1 · Submission Forms → Records / Notifications layer

```
Public Form Submit (rate-limited)
   │
   ├── POST /api/inspections        → db.inspections            → schedule_auto_email("inspection")      → PM + ALWAYS_CC      → emit_task_and_notification (Safety + PM bell)
   ├── POST /api/meetings           → db.safety_meetings        → schedule_auto_email("meeting")         → PM + ALWAYS_CC      → emit_task_and_notification
   ├── POST /api/jhas               → db.job_hazard_plans       → schedule_auto_email("jha")             → PM + ALWAYS_CC      ⇢ emit_task (NOT wired — GAP-3)
   ├── POST /api/incidents          → db.incidents              → schedule_auto_email("incident")        → PM + ALWAYS_CC + severe-CC → emit_task_and_notification + corrective_actions seed
   ├── POST /api/daily-reports      → db.daily_reports          → schedule_auto_email("daily-report")    → PM only             → db.daily_reports_audit
   ├── POST /api/equipment-inspections → db.equipment_inspections → schedule_auto_email("equipment-inspection") → PM (PASS) OR PM + every shop user (FAIL/OOS)  → emit_task_and_notification on FAIL/OOS
   ├── POST /api/qaqc-inspections   → db.qaqc_inspections       → schedule_auto_email("qaqc")            → PM + ALWAYS_CC      → emit_task_and_notification
   ├── POST /api/po-requests        → db.po_requests            → task_service.create + notification_service.fanout → approver
   ├── POST /api/asset-transfers    → db.asset_transfers        → emit_task_and_notification → receiving location + Dispatch
   ├── POST /api/safety-forms/...   → db.safety_equipment_*     → schedule email to SAFETY_FORMS_EMAIL_TO ⇢ NO bell/task (GAP-2)
   ├── POST /api/field-leadership/portal/forms → db.field_leadership_records → email to leadership_always_to ⇢ NO bell/task (GAP-1)
   └── POST /api/fleet/dvir/*       → db.fleet_dvirs (presumed) ⇢ NO confirmed notification or dashboard (ORPHAN-1 / GAP-6)
```

Classification: 🟢 for the wired chains. 🟡 / ⚫ for the ⇢ aspirational paths.

---

## 2 · Records → Project Health / Cross-collection feeds

```
db.daily_reports         → project_health probe (aggregated)
db.equipment_inspections → asset_holds (when out_of_service=yes) → Dispatch board
db.incidents             → db.corrective_actions (when Safety opens CA)
db.qaqc_inspections      → admin compliance findings
db.po_requests           → finance ledger digest
db.dispatch_assignments  → fleet utilization + project health (haul activity)
db.dispatch_state_events → live Dispatch board state machine
db.field_leadership_records → per-employee accountability timeline (employees collection)
db.training_records      → document_expirations (cron computes expiry)
db.employees + db.documents → db.document_expirations (nightly cron)
```

Classification: 🟢 for every link traced from `routes/*.py` code paths.

---

## 3 · Records → Dashboard surfaces

For per-record dashboard mapping see `DASHBOARD_DESTINATION_MAP.md`. High-level:

```
db.inspections, db.safety_meetings, db.job_hazard_plans, db.incidents
  → Admin Hub · Safety Portal · PM Hub Compliance row · HR cross-portal viewer

db.daily_reports
  → Admin Daily · PM Daily · HR Daily Reports cross-portal viewer

db.equipment_inspections
  → Shop Equipment · Admin Pre-Op trends · PM Equipment

db.qaqc_inspections
  → Admin QA/QC · PM QA/QC · Safety library

db.po_requests
  → /po-requests · Admin queue · HR PO panel

db.field_leadership_records
  → HR Field Leadership · Admin People history · FL Portal dashboard · PM (own crew)

db.dispatch_*
  → Dispatch Board · Admin Dispatch

db.tasks + db.notifications
  → NotificationBell on every portal chrome · per-portal digest endpoint
```

Classification: 🟢.

---

## 4 · Auth / Directory feed

```
db.user_directory (multi-portal accounts)
  └── /api/auth/multi-login  → returns up to 6 portal_tokens
       ├── admin token  → /api/admin/*          (require_admin / require_admin_strict)
       ├── pm token     → /api/pm/*             (require_actor / PM-scoped reads)
       ├── shop token   → /api/shop/*           (require_shop_or_admin)
       ├── hr token     → /api/hr/*             (require_hr_user / require_hr_or_admin)
       ├── safety token → /api/safety/*         (require_safety_token / require_safety_or_hr_or_admin)
       └── dispatch tok → /api/dispatch/*       (require_dispatch_or_admin_dep)

db.directory_sessions → audit row in db.admin_audit on every login
```

Cross-portal token interop:
- `/operations/*` READ accepts any portal token
- Safety doc / training / employee-profile READ accepts safety / HR / admin

Classification: 🟢.

---

## 5 · External integrations

| Outbound system | Endpoint / channel | Purpose | Classification |
|-----------------|--------------------|---------|----------------|
| Resend (email) | `RESEND_API_KEY` | All transactional emails (auto-emails + digests + welcomes + alerts) | 🟢 |
| Cloudflare R2 (object storage) | `R2_*` env | Photo / attachment cold storage; backup mirror | 🟢 |
| MongoDB Atlas | `MONGO_URL` | Primary data + backup target (`masci_safety` prod / `masci_safety_preview` preview) | 🟢 |
| Sentry | `REACT_APP_SENTRY_DSN` | Frontend error capture | 🟢 |
| (Optional) SMS via Resend | dispatch magic links | Driver shift-start magic link | ⚪ — confirmed present in `dispatch_magic_links` but live SMS provider not 100% verifiable from static |
| WebAuthn / passkey | `webauthn_challenges` + `user_passkeys` | Optional passkey login | 🟢 |

Classification: 🟢 for confirmed; ⚪ for SMS pathway pending runtime trace.

---

## 6 · Cron feeds

```
Safety Digest (Mon 14:00 UTC) → safety@mascigc.com weekly summary email
Document Expirations nightly  → HR task creation + digest email
PO Request receipt-missing    → flag + task creation
Payroll Variance weekly       → HR digest email (PAYROLL_VARIANCE_EMAIL_TO)
Backup pipeline nightly       → Atlas dump + R2 push + drift compute · 🔴 DEAD (GAP-7)
Cluster capacity periodic     → admin cluster badge update
Health monitor probe          → _send_alert email when red cards detected
```

Classification: 🟢 for registration paths. Live tick verification = runtime concern.

---

## 7 · Notification fan-out central path

```
caller (route file)
  │
  └── lib.event_fanout.emit_task_and_notification(db, task=..., notification=...)
        │
        ├── routes.tasks_notifications.task_service.create(db, task)
        │      └── db.tasks   ←──── writes
        │            └── auto-emits task.assigned notification via internal call
        │
        └── routes.tasks_notifications.notification_service.fanout(db, notification)
               └── db.notifications ←──── writes (resolved per recipient role)
                        ↓
              GET /api/notifications (per portal)
                        ↓
              NotificationBell.jsx drawer in portal chrome
```

Classification: 🟢 KNOWN GOOD — single canonical entry point. Anti-pattern: any new module writing directly to `db.tasks` or `db.notifications` (`routes/training_center.py:340-346` explicitly documents this rule).

---

## 8 · Audit feed

```
Admin action (any /api/admin/* write)
  → admin_audit row (db.admin_audit + db.admin_audit_log + db.audit_events)
  → surfaces in /admin/audit and /admin/audit-log

Login event
  → db.admin_audit
  → surfaces in /admin/audit-log + /admin/sessions
```

Classification: 🟢.

---

## 9 · What feeds nothing (potential black holes)

| Source | Notes |
|--------|-------|
| `db.fleet_dvirs` (if exists) | No confirmed downstream — ORPHAN-1 / GAP-6 |
| `db.draft_telemetry` | Drafts collection — feeds Admin draft-recovery panel; otherwise terminal |
| `db.usage_events` | Usage telemetry — feeds Admin operations-events + analytics; otherwise terminal |
| `db.r2_degraded_events` | R2 degradation log — feeds Admin Integration Center health card |
| `db.calculator_runs` | Field calculator usage — terminal ledger |
| `db.session_activity` | Session activity log — feeds Admin Sessions |
| `db.deploy_version_history` | Deploy log — feeds `/admin/deploy-readiness` + `/admin/deploy-recovery` |

Classification: 🟢 (terminal ledgers are intentionally terminal) except Fleet DVIR ⚫.

---

## 10 · Aspirational feeds that should exist but don't

| Source | Should feed | Why missing | Gap ID |
|--------|-------------|-------------|--------|
| Daily Report Weather=YES | Constraint / Schedule task | Schedule integration on stop-list | GAP-8 |
| Daily Report Equipment-Issue=YES | Pre-Op auto-link | Cross-link logic not built | GAP-9 |
| JHA submit | Safety Hub action card + task to Safety supervisor | No `emit_task_and_notification` call in `routes/safety.py:518` JHA branch | GAP-3 |
| Field Leadership 10 forms | Safety/Admin Hub per-record action queue + bell | No `emit_task` call in `routes/field_leadership_users.py` | GAP-1 |
| Safety Forms (issuance/training) | Safety Hub per-record action queue + bell | Email-only, no bell/task | GAP-2 |
| Training assignment | Supervisor of trainee bell | `linked_supervisor` not resolved | GAP-4 |
| Severe Incident | Re-ping cadence escalation | No timed escalation framework | GAP-14 |
| PO no-receipt > 30d | Office Manager / PM escalation | No higher-tier cron tier | GAP-15 |
| Fleet DVIR defect | Shop / Dispatch task | No path wired | GAP-6 / ORPHAN-1 |

Classification: 🟡 / ⚫ per row.

---

## Summary

- **22 confirmed feed links** between subsystems (DB write → downstream collection / API / email / bell)
- **8 aspirational feed links** identified as missing (matches the gap register)
- **2 ⚫ OPERATOR DECISION NEEDED** flags (Fleet DVIR downstream; real-time push vs. polling — see `NOTIFICATION_DELIVERY_MAP.md` §8)
- **0 silent broken feeds** discovered beyond the already-tracked Backup Scheduler (GAP-7)

Classification rollup: **🟢 22 · 🟡 6 · 🔴 1 · ⚪ 1 · ⚫ 2**
