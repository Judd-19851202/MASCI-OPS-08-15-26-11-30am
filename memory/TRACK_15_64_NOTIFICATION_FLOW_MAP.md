# TRACK 15.64 — Notification Flow Map (Phase 2)

**Date:** 2026-06-22  
**Mode:** documentation-only

For every workflow that emits email, the chain is: `trigger event → recipient resolver → Resend send call → audit row (where applicable)`. Recipient resolvers fall into three families:

* **DB-overridable** (`email_routing.py.load(db)`) — admin-editable in `/admin/email`.
* **Env-only** — set in `backend/.env`, requires redeploy to change.
* **Collection-driven** — recipients read from a Mongo collection (`project_managers`, `shop_users`, `hr_users`, `safety_users`, `dispatch_users`, `field_leadership_users`).

All sends are gated on `AUTO_EMAIL_REPORTS=true` (preview default `false`).

## 1. Compliance workflows (DB-overridable today)

```
Inspection Submitted
  → To:  PM resolved from jobs_master.pm_email or project_managers collection
  → CC:  email_routing.always_cc  (default: jaymn.judd + safety)
  → Send: backend/pm_routing.py.fanout()  ·  Resend send
  → Audit: db.email_audit (PM_FANOUT kind)

Safety Meeting Submitted             same chain as Inspection
JHA Submitted                        same chain
Daily Report Submitted               same chain
Incident Submitted (non-severe)      same chain
QA/QC Inspection Submitted           same chain
Equipment Inspection Submitted       same chain
Pre-Op Inspection (pass)             same chain (PM only)

Incident Submitted (SEVERE / WV / PI)
  → To:  PM + Safety + Superintendent + Operations + Executive + HR
  → CC:  email_routing.always_cc + email_routing.severe_incident_cc
  → Side-effects: 3-task aftercare chain · 14-day retraining task · 17 notifications
  → File: backend/routes/safety.py  · `emit_task_and_notification × N`

Pre-Op Inspection (FAIL · OOS)
  → To:  Every active row in shop_users collection
  → Fallback: email_routing.shop_manager_fallback  (default: shopmanager@)
  → File: backend/routes/safety_forms.py
```

## 2. Safety Forms workflows (DB-overridable today)

```
Equipment Issuance / Equipment Training / Equipment Return
  → To:  email_routing.safety_forms_to  (default: safety + jaymn)
  → CC:  email_routing.always_cc
  → File: backend/routes/safety_forms.py
```

## 3. Field Leadership forms (DB-overridable today)

```
10 FL forms (write_up, verbal_coaching, attendance, recognition,
  equipment_checkout, new_employee_eval, crew_eval,
  promotion_recommendation, training_deficiency, supervisor_notes)
  → To: assigned PM + dynamic FL user list  ·  CC: email_routing.leadership_always_to
  → File: backend/routes/field_leadership.py
```

## 4. PM / Shop / HR / Safety / Dispatch / FL Welcome + Password Reset

```
"Email to user" welcome:
  → To: target user (collection-driven)
  → Sender: SENDER_EMAIL  ·  Reply-to: REPLY_TO_EMAIL
  → Workflow: admin clicks "Email to user" in the per-portal user panel
  → Files: routes/pm_admin.py · server.py (shop/HR/safety/dispatch/FL)
  → Audit: db.email_audit (PORTAL_WELCOME kind)

"Forgot password" reset link:
  → To: requester (verified against the portal's user collection)
  → Token: 30-min HMAC bound to password_hash[:16]
  → Per-portal endpoints: /api/{pm,shop,hr,safety,dispatch,fl}/forgot-password
```

## 5. Scheduled digests + alerts (env-only — Phase 4 gap)

```
Weekly Safety Digest
  → To: SAFETY_DIGEST_TO_EMAIL (default safety@mascigc.com)
  → Cron: Monday 14:00 UTC
  → File: backend/safety_digest.py

Daily Operator Digest
  → To: OPERATOR_DIGEST_RECIPIENTS or SAFETY_DIGEST_TO_EMAIL fallback
  → File: backend/lib/operator_digest.py

Payroll Variance Email
  → To: PAYROLL_VARIANCE_EMAIL_TO
  → Cron: PAYROLL_VARIANCE_EMAIL_HOUR_UTC + PAYROLL_VARIANCE_EMAIL_DOW
  → File: backend/server.py:12525-

Backup-Pipeline Email (daily + manual)
  → To: email_routing.backup_email_to (DB-overridable) → BACKUP_EMAIL_TO env
  → File: backend/server.py:6440-7430

Health Alert Email
  → To: HEALTH_ALERT_RECIPIENTS or BACKUP_EMAIL_TO or safety@ fallback
  → Trigger: scheduler_loop detects scheduler_alive=false OR backup_recent=false
  → File: backend/health_monitor.py

Outage Alert Email
  → To: OUTAGE_ALERT_TO env (single recipient, no DB override)
  → File: backend/outage_alerts.py

Backup Verification Email
  → To: BACKUP_EMAIL_TO env override (force-recipients body-supported) → fallback to safety@
  → File: backend/backup_verification.py · routes/backup_verification_routes.py

Admin Dead-Letter
  → To: ADMIN_DEAD_LETTER_EMAIL env
  → Trigger: field submitter identity could not be resolved
  → File: backend/lib/field_submitter_identity.py
```

## 6. Workflow-by-workflow routing source table

| Workflow | Recipient source | DB-overridable? | Env-fallback | Audit row written? | Notes |
|---|---|---|---|---|---|
| Inspection / Meeting / JHA / Daily Report / Incident (non-severe) / QAQC / Equip Insp | PM resolved → `email_routing.always_cc` | YES (always_cc) | always_cc env | YES (`email_audit`) | PM is collection-driven (jobs_master / project_managers) |
| Severe Incident | PM + Safety + Sup + Ops + Exec + HR + `severe_incident_cc` | YES (CC layer) | env | YES | WV/PI auto-CAPA |
| Pre-Op FAIL/OOS | `shop_users` collection + `shop_manager_fallback` | YES (fallback) | env (SHOP_MANAGER_EMAIL) | YES | New deploy seeds shop_users from env |
| Safety Forms | `safety_forms_to` | YES | SAFETY_FORMS_EMAIL_TO | YES | |
| Field Leadership forms | PM + dynamic FL list + `leadership_always_to` | YES | LEADERSHIP_ALWAYS_TO_1/2 | YES | |
| Portal welcome / reset | Single target user | n/a (per-user) | SENDER_EMAIL / REPLY_TO_EMAIL | YES | |
| Safety Digest | env-only | **NO** | SAFETY_DIGEST_TO_EMAIL | YES | Phase 4 gap |
| Operator Digest | env-only | **NO** | OPERATOR_DIGEST_RECIPIENTS | partial | Phase 4 gap |
| Payroll Variance | env-only | **NO** | PAYROLL_VARIANCE_EMAIL_TO | YES | Phase 4 gap |
| Backup Email | DB-overridable | YES | BACKUP_EMAIL_TO | YES | |
| Health Alert | env-only | **NO** | HEALTH_ALERT_RECIPIENTS | partial | Phase 4 gap |
| Outage Alert | env-only | **NO** | OUTAGE_ALERT_TO | NO | Phase 4 gap (also: audit gap) |
| Backup Verification | env + body override | partial | BACKUP_EMAIL_TO | YES | |
| Admin Dead-Letter | env-only | **NO** | ADMIN_DEAD_LETTER_EMAIL | YES | Phase 4 gap |
| Trench Safety pulse / excavations / report dist | env-only (separate role map) | **NO** | per-role env | partial | Parallel routing layer, see Phase 3 |

## 7. Audit row coverage
* `db.email_audit` is written for: PM fanout, portal welcome, password reset, safety forms send, FL fanout, backup email, payroll variance email.
* Missing audit rows: outage alert, health alert, operator digest (partial), trench safety role fan-out.

## 8. Visualisation

```
                       ┌──────────────────────────────────┐
                       │   AUTO_EMAIL_REPORTS kill-switch │
                       └────────────┬─────────────────────┘
                                    ▼
   ┌──────────────────────────────────────────────────────────┐
   │             email_routing.load(db)  (60-s cache)         │
   │   ──────── DB-OVERRIDABLE TODAY ────────                 │
   │   • always_cc                  • safety_forms_to         │
   │   • leadership_always_to       • shop_manager_fallback   │
   │   • severe_incident_cc         • backup_email_to         │
   │                                                          │
   │   ──────── ENV-ONLY (Phase 4 GAP) ────────               │
   │   • safety_digest_to    • operator_digest_recipients     │
   │   • health_alert_recipients · outage_alert_to            │
   │   • payroll_variance_email_to · admin_dead_letter_email  │
   │   • dispatch_email · super_admin_email                   │
   │   • trench_safety role map                               │
   └──────────────────────────────┬───────────────────────────┘
                                    ▼
                       ┌──────────────────────────────────┐
                       │   Resend (40 send sites)          │
                       │   Sender: SENDER_EMAIL            │
                       │   Reply-to: REPLY_TO_EMAIL        │
                       └────────────┬─────────────────────┘
                                    ▼
                       ┌──────────────────────────────────┐
                       │  db.email_audit  (partial coverage)│
                       └──────────────────────────────────┘
```

## 9. Hard-rule compliance (Phase 2)
* ✅ Documentation only. Zero code change.
* ✅ Every workflow row anchored to a backend file/line in Phase 1 inventory.
* ✅ DB-overridable vs env-only categorisation is empirically verified by grepping `email_routing` imports.
