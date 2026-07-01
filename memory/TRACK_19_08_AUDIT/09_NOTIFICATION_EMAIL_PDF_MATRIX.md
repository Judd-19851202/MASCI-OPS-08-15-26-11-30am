# TRACK 19.08 · Notification / Email / PDF Matrix

Every notification fired by an operational form. Every PDF rendered. Every email routing key.

**Snapshot count**: 105 email/PDF hook occurrences across `backend/routes/*.py` + `backend/server.py` (`grep -c schedule_auto_email/weasyprint`). Full audit locked by drift-detection tests.

---

## 1 · Email routing table

Backing collection: `email_routes`. Each row is `{workflow_key, project_number (optional), recipient_kind, recipient_ref, severity_min (optional), enabled}`. Resolved at fire-time by `schedule_auto_email(key, doc, context)`.

| Workflow key | Fires when | Typical recipients (severity varies) | Where set |
| --- | --- | --- | --- |
| `daily-report` | DR submit | PM · Safety-Manager · Optional Executive on flagged content | `routes/daily_reports.py:404` |
| `equipment-inspection` | Equipment Pre-Op submit | Shop-foreman · PM · Safety (on FAIL) | `routes/equipment.py` |
| `equipment-inspection-signoff` | Admin sign-off | Inspector · PM | `server.py` admin signoff route |
| `dvir` | DVIR submit | Shop · Dispatch · Safety · Fleet-Manager · PM | `routes/fleet_ops.py` |
| `defect_open` | Fleet-defect insert (any severity) | Same, per severity | `routes/fleet_ops.py` |
| `defect_acknowledged` | Shop acknowledges | Assigned mechanic · Foreman | `routes/shop_*` |
| `defect_accepted` | Shop accepts assignment | Mechanic · Foreman | Same |
| `defect_assigned` | Shop assigns | Mechanic | Same |
| `defect_reassigned` | Shop reassigns | New mechanic · Prior mechanic | Same |
| `defect_repair_started` | Shop starts repair | Foreman | Same |
| `defect_repaired` | Shop marks repaired | Dispatch · Fleet-Manager | Same |
| `defect_manager_reviewed` | Manager review pass | Shop manager | Same |
| `defect_review_rejected` | Manager review reject | Mechanic · Foreman | Same |
| `defect_cleared` | Defect cleared / OOS lifted | Dispatch · Fleet-Manager · Safety CC on OOS | Same |
| `fleet-unit-oos` | Unit set OOS | Dispatch · Fleet-Manager · Safety · PM | Same |
| `fleet-unit-return-to-service` | Unit back available | Same list | Same |
| `meeting` | Meeting submit | Safety-Manager · PM | `routes/safety_portal/*` |
| `incident` | Incident submit | Safety · HR · Executive (on ≥high) · PM | `routes/incidents_*` |
| `incident-transition` | State change | Same | Same |
| `jha-submit` | JHA publish | Safety · PMs of tagged projects | `routes/jha_*` |
| `jha-acknowledgement` | Employee acknowledges | Rolled into weekly digest (no per-event fire) | Same |
| `corrective-action-open` | CA created | Assignee · Safety · HR | `routes/safety_portal/*` |
| `corrective-action-due` | Due-date reminder cron | Assignee · Safety | Weekly cron |
| `corrective-action-closed` | CA closed | Requestor · Safety | Same |
| `equipment-issuance` | Issuance submit | HR-accountability · Safety | `routes/safety_portal/*` |
| `equipment-training` | Training submit | HR-accountability · Safety · Assignee | Same |
| `trench-excavation` | Excavation open | Safety · Competent-person · PM | `routes/*` |
| `trench-inspection` | Daily trench inspection | Safety · PM | Same |
| `safety-digest` | Weekly cron | Safety subscribers | `routes/safety_portal/digest.py` |
| `operator-digest` | Weekly cron | Field-leadership subscribers | `routes/operator_digest.py` |
| `po-digest` | Weekly cron | Admins · PM leads | `routes/po_digest.py` |
| `pm-welcome-pdf` | PM onboarding | New PMs | `pm_welcome_pdf.py` |
| `field-leadership-*` | Field leadership form submits | FL subscribers | `field_leadership_pdf.py` + `routes/field_leadership*.py` |

Audit trail: every fired email → `email_routing_audit_v` insert with `correlation_id`, `to_hash`, `key`, `template_id`, `dispatched_at`.

---

## 2 · PDF matrix

Backing engine: **WeasyPrint** via `pdf_render.py` (2,773 LOC — the platform's largest single module). Each family uses a dedicated template block within the same module (branded, deterministic, no remote-font dependency).

| Form | PDF renderer | Called from | Storage |
| --- | --- | --- | --- |
| Daily Report | `render_daily_report_pdf` | `routes/daily_reports.py` on submit + on view | R2 bucket, key = `daily-reports/{id}.pdf` |
| Equipment Pre-Op | `render_equipment_inspection_pdf` | `routes/equipment.py` | R2, `equipment-inspections/{id}.pdf` |
| DVIR | `render_dvir_pdf` | `routes/fleet_ops.py` | R2, `dvir/{id}.pdf` |
| Meeting | `render_meeting_pdf` | `routes/safety_portal/*` | R2 |
| Incident | `render_incident_pdf` | `routes/incidents_*` | R2 |
| JHA | `render_jha_pdf` (+ poster variant) | `routes/jha_*` | R2 |
| Equipment Issuance | `render_equipment_issuance_pdf` | `routes/safety_portal/*` | R2, +`/return/pdf` variant |
| Equipment Training | `render_equipment_training_pdf` | Same | R2 |
| Field Leadership form | `field_leadership_pdf.py` (separate module) | `routes/field_leadership*.py` | R2 |
| PM welcome | `pm_welcome_pdf.py` | Admin action | R2 |
| Fleet severity ref card | admin PDF | `admin_fleet_*` | Rendered ad-hoc |
| Cultural banner calendar | `cultural_banner_calendar.py` | Admin | Rendered ad-hoc |

**Branding**: All PDFs use `pdf_branding.py` / `pdf_branding_rl.py` for logo, colors, footer. Consistent look across families.

**Failure mode**: If WeasyPrint fails (rare), `export_pdf_fallback.py` produces a text-only fallback and flags the render with `pdf_render_failed=True`. Submit still succeeds.

---

## 3 · Notification collection (`notifications`)

Separate from email — this is in-app notifications rendered by `<NotificationBell>`.

| Producer | Notification kind |
| --- | --- |
| DVIR FAIL | `fleet-defect-created` — for shop portal |
| Incident submit (≥medium) | `incident-reported` — for safety + HR portals |
| Corrective action assignment | `ca-assigned` — for assignee |
| Meeting completion | `meeting-submitted` — for PM portal |
| Fleet OOS | `unit-oos-applied` — for dispatch + shop |
| Payroll variance detected | `payroll-variance` — for HR |

Read via `GET /api/notifications` scoped by portal token.

---

## 4 · Digest cadence

| Digest | Cron | Cron file | Recipients |
| --- | --- | --- | --- |
| Safety digest | Weekly Mon 06:00 | `routes/safety_portal/digest.py` | Safety subscribers |
| Operator digest | Weekly Mon 07:00 | `routes/operator_digest.py` | FL subscribers |
| PO digest | Weekly Fri 15:00 | `routes/po_digest.py` | Admin · PM |
| Backup verification | Weekly Sun 03:00 | `backup_verification.py` | Admin |
| Transport automation digest | Daily | `routes/transportation_automation.py` | Dispatch admin |

All gated by `SCHEDULER_ENABLED=true` on singleton worker.

---

## 5 · Audit correlation

Every notification / email / PDF carries a `correlation_id` = the submit's idempotency key. Auditors trace an operator action through email → PDF → notification with a single id search.

---

## 6 · Drift-detection

Locked by `test_track_19_08_forms_audit_snapshots.py`:
* Count of `schedule_auto_email(` invocations across the backend.
* Count of `weasyprint` imports.
* Presence of the 6 primary PDF renderer function names.
* Presence of the workflow keys enumerated in §1.

Any drift after 2026-07-01 fails the audit lock until this document is updated.
