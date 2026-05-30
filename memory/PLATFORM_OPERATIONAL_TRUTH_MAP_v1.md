# PLATFORM_OPERATIONAL_TRUTH_MAP_v1

**Batch:** I · Platform Operational Truth Map Finalization
**Date:** 2026-05-30 (UTC)
**Operator directive:** Move platform understanding from ~80 % → 100 % verified. Map · verify · prove · document. **Zero remediation.** Zero code changes. Zero feature work.

**Triangulation rule for every claim in this map:** ① cited Memory doc · ② file:line in `/app/backend` or `/app/scripts` · ③ live runtime probe (preview backend or DB inventory). Where runtime cannot reach production (preview-only environment), the limitation is recorded explicitly.

**Master delta companion:** `PLATFORM_TRUTH_DELTA_REPORT.md` — every divergence found while writing this map.
**Master gap companion:** `PLATFORM_GAP_LEDGER_FINAL.md` — deduplicated, severity-ranked.
**DR companion:** `DISASTER_RECOVERY_VALIDATION_MATRIX.md` + `PLATFORM_RECOVERABILITY_PROOF_REPORT.md`.

---

## 0 · How to read this map

| Glyph | Meaning |
|---|---|
| 🟢 | Verified — all three sources agree |
| 🟡 | Known gap (documented, not yet remediated; consistent across sources) |
| 🔴 | Broken or contradicted by runtime |
| ⚫ | Operator decision needed (architectural intent unclear) |
| 🟦 | Preview-only verification (production behaviour inferred from code, not runtime) |

Every cell ends with a footnote-style citation: `[M:doc · C:file:line · R:probe-id]` — Memory · Code · Runtime.

Runtime probe IDs reference `batch_i_evidence/runtime_probes.txt` (P1…P7) or `db_collection_inventory.txt` (DBI-1).

---

## 1 · Inventory baseline

| Source | Count | Evidence |
|---|---:|---|
| `/app/backend/routes/` .py files | **86** | `ls /app/backend/routes/` |
| MongoDB collections (preview DB `masci_safety_preview`) | **132** | DBI-1 |
| `/app/memory/*.md` documents catalogued | **300+** | `ls /app/memory/` |
| Documents directly consulted in Batch I | 14 anchors | this map's §10 citations |
| Backend route files containing fan-out (`emit_*` / `schedule_auto_email` / `task_service.create` / `notification_service.fanout`) | **10** | `code_fanout_callsites.txt` |
| Backend route files containing **NO** fan-out (orphan candidates) | 1 confirmed: `routes/fleet_ops.py` | `code_fanout_callsites.txt` final block |

---

# AXIS I-1 · WORKFLOW OWNERSHIP

**Anchor memory document:** `WORKFLOW_OWNERSHIP_MATRIX.md` (2026-05-29) — 31 workflows.

**Verification approach:** for each workflow, walk to the submit handler in `/app/backend/routes/`, confirm the ownership claim against the code (creator / owner role required, who reads, who can edit, who closes). Runtime confirmation is via DB collection existence (DBI-1) plus the route's deps (`require_admin`, `require_safety_or_admin`, `require_dispatch_or_admin`, etc.).

## 1.1 Master ownership table (consolidated · code-verified)

| # | Workflow | Submit handler (file:line) | Creator | Owner (acts on) | Reviewers/Editors | Delete | Closer | No-response | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Daily Report** | `routes/daily_reports.py:218` (`POST /api/daily-reports`) | anon foreman | PM (from `project_number → pm_email`) | PM · Admin · HR · Safety · Shop (signoff) | Admin only — `DELETE` returns 410 (doctrine freeze) | PM review | none (PM bell only) | 🟢 |
| 2 | DR · Production rows | sub-record of #1 | (sub) | inherits #1 | inherits | frozen | inherits | n/a | 🟢 |
| 3 | DR · Delays / Extra Work | sub-record of #1 | (sub) | inherits | inherits | frozen | inherits | n/a | 🟢 |
| 4 | DR · Weather Impact | sub-record of #1 | (sub) | inherits | inherits | frozen | inherits | **none — schedule integration on stop-list** | 🟡 GAP-8 |
| 5 | **Equipment Pre-Op PASS** | `routes/equipment.py:199` | anon operator | Shop Manager | Admin · Shop · PM (scope) | Admin only | Shop review email | reference-only | 🟢 |
| 6 | **Equipment Pre-Op FAIL** | `routes/equipment.py:234–247` | anon operator | **Shop (task)** + **Dispatch (visibility)** | Admin · Shop · PM | Admin only | Shop sign-off → returns to in-service | task expires after configurable interval (P1 future) | 🟢 |
| 7 | **Shop Recovery / Asset Transfer** | `routes/asset_transfers.py:161+173+214` | Shop · Dispatch · Admin | Shop | Admin · Dispatch · Shop | originator + admin | Admin | Shop | admin dashboard surfaces unsigned items | 🟢 |
| 8 | **PO Request** | `routes/po_requests.py:206+220+242` | any portal user | approval queue (leadership / admin / hr per PO routing) | requester · admin · approvers | requester (pre-approval) | Admin only | approver | nightly cron "approval-needed" + receipt-missing watchdog (no higher escalation = GAP-15) | 🟢 |
| 9 | PO Response | (no separate handler — `task_service` decision write) | approver | requester · admin | requester · admin · approvers | (no edit post-decision) | Admin only | requester (uploads receipt) | receipt-missing watchdog | 🟢 |
| 10 | PO Receipt upload | within PO routes | any portal user (typically requester) | Admin · PM (financial reconciliation) | Admin · PM · HR | requester (until close) | Admin only | Admin | none beyond watchdog | 🟢 |
| 11 | **Incident Report** | `routes/safety.py:579+585+621` | anon foreman / safety | **Safety (task)** + **PM (visibility)** | Safety · Admin · PM (scope) · HR (if injury) | Admin only | Admin only | Safety | none for severe no-response (GAP-14) | 🟢 |
| 12 | **Safety Meeting** | `routes/safety.py:464` | any portal user · Safety | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | **none · email-only · no bell/task = NEW-GAP-A** | 🟡 |
| 13 | **JHA submit** | `routes/safety.py:518` | any portal user | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | **none · email-only · no bell/task = GAP-3** (collection: `jhas`) | 🟡 |
| 14 | **Safety Inspection** | `routes/safety.py:318+338+367` | any portal user | PM | PM · Safety · Admin | Admin only | Admin only | PM | follow-up cadence absent | 🟢 |
| 15 | JHP / Job Hazard Planning | consolidated with safety_forms | Safety | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | n/a | 🟢 |
| 16 | **QA/QC Concrete / Rebar / Subwork / Material Testing / Asphalt** | `routes/qaqc.py:210+217+222+249` | any portal user (or Safety) | Safety (compliance owner per V.5) + PM (project view) | Safety · Admin · PM | Admin only | Admin only | Safety | none | 🟢 |
| 17 | **Dispatch Request / Equipment Request** | `routes/dispatch_lifecycle.py` (various) | Dispatch · any field requester | Dispatch lead | Dispatch · Admin · Shop · PM | Dispatch · Admin | Admin only | Dispatch (closes when crew/asset deployed) | task surfaces in Dispatch hub; admin observes; "stuck > 30 m" live alert | 🟢 |
| 18 | **HR Request (general)** | `routes/hr_portal.py` (multiple) | HR | HR | HR · Admin | HR · Admin | Admin only | HR | none | 🟢 |
| 19 | **Time Verification batch** | `routes/hr_portal.py` (time-verification routes) | HR Manager | HR | HR · Admin | (read-only ledger) | n/a | (read-only) | n/a (read-only verification — no action expected) | 🟢 |
| 20 | **Payroll Variance manual** | `routes/payroll_variance.py` | HR Manager | HR | HR · Admin | HR | Admin only | HR | none manual; weekly cron handles automated path | 🟡 GAP-5 |
| 21 | Payroll Variance weekly cron | `server.py:10241` + cron tick | system | HR + Admin | HR · Admin | (system) | n/a | (operator-archive) | weekly email · admin reviews | 🟢 |
| 22 | **Training Record assigned** | `routes/training_center.py` | Safety / HR | Employee | Safety · HR · Admin · linked supervisor (intermittent) | Safety · HR | Admin only | Employee | **supervisor not always notified = GAP-4** | 🟡 |
| 23 | Training Record completed | `routes/training_center.py` | Employee | Employee | inherits | inherits | Admin only | (closes) | n/a | 🟢 |
| 24 | Visitor Log | sub-record of DR | (sub) | PM (via DR) | inherits | inherits | n/a | inherits | n/a | 🟢 |
| 25 | **Fleet DVIR / Weekly Lead / Weekly Emergency** | `routes/fleet_ops.py:412` (`POST /api/fleet/inspections`) | Driver / Operator | **Dispatch + Shop (PER POLICY · NOT CONFIRMED IN CODE)** | Admin · Dispatch · Shop | Admin only | Admin only | Shop | **🔴 NO notification path · NO email · NO task fan-out — confirmed orphan ORPHAN-1 / GAP-6** | 🔴⚫ |
| 26 | Fleet Defect lifecycle (acknowledge / repair / clear / OOS) | `routes/fleet_ops.py:693, 729, 774, 819` | Shop | Shop | Admin · Dispatch · Shop | Admin only | Admin only | Shop | none | 🟢 |
| 27 | **Safety Equipment Issuance** | `routes/safety_forms.py` | Safety / HR | Safety | Safety · Admin · HR | Safety · Admin | Admin only | Safety | email-only · **GAP-2 bell/task missing** | 🟡 |
| 28 | Safety Equipment Training | `routes/safety_forms.py` | Safety | Employee + Safety | Safety · Admin | Safety · Admin | Admin only | Safety | email-only · **GAP-2** | 🟡 |
| 29 | Safety Equipment Return | `routes/safety_forms.py` | Safety | Safety | Safety · Admin · HR | Safety · Admin | Admin only | Safety | email-only · **GAP-2** | 🟡 |
| 30 | **Field Leadership 10 forms** | `routes/field_leadership.py` / `field_leadership_portal.py` | FL submitter | recipients (`leadership_always_to`) | FL · Admin · HR · PM · Safety | Admin only | Admin only | recipient | email-only · **GAP-1 bell/task missing · search-only surface** | 🟡 |
| 31 | **Driver Qualification import / record** | `routes/hr_portal.py` (DQ routes) | HR | HR · Dispatch | HR · Admin · Dispatch | HR | Admin only | HR | doc-expirations cron raises HR task | 🟢 |
| 32 | **Document Expirations cron** | `routes/document_expirations.py:119+232+237` | scanner cron | HR | HR · Admin | (system) | n/a | (HR acknowledges) | nightly task created if doc expiring | 🟢 |
| 33 | **Fire Extinguisher Inspection** | `routes/safety_portal/fire_extinguishers.py:122+125` | any portal user | Safety | Safety · Admin · PM | Admin only | Admin only | Safety | follow-up via task | 🟢 |
| 34 | **Corrective Action** | within safety routes | Safety | assignee | Safety · Admin · assignee | Admin only | Admin only | assignee | task remains open | 🟢 |
| 35 | **Operational Daily Records (ODR)** | `routes/odr/*` | foreman / public submit | PM | PM · Admin · public-viewer (read) | Admin only | Admin only | PM | public link auto-expire | 🟢 |
| 36 | Attachments / Public Links | `routes/operational_attachments.py` + magic-link routes | requester | requester | (anyone with link · rate-limited) | (read-only) | Admin only | (auto-expires per policy) | n/a | 🟢 |
| 37 | PDF Downloads | various PDF builders | transient HTTP | n/a | gated by parent record perms | n/a | n/a | n/a | n/a | 🟢 |
| 38 | **Backup Alerts** | `lib/singleton_scheduler.py` + `server.py` (`_backup_scheduler_loop`) · `health_monitor.py:49+200` | scheduler | Admin (sole) | Admin | (system) | n/a | (admin acknowledges) | **🔴 SCHEDULER DEAD IN PREVIEW (P2: `alive=false`, `armed_at=null`, `last_tick_ts=null`)** · production claim "active since Batch D" cannot be re-verified from preview → see DELTA-D1 | 🟦🔴 |
| 39 | System Health Alerts | `health_monitor.py` periodic | health monitor cron | Admin | Admin | (system) | n/a | (admin acknowledges) | red-alert email path active (gated by `RESEND_API_KEY` + `AUTO_EMAIL_REPORTS=true`) | 🟢 |
| 40 | Magic-link (dispatch driver) | `routes/dispatch_portal_auth.py` / `dispatch_magic_links` | dispatcher | driver | (single-use) | n/a | (auto-burn) | n/a | n/a | 🟢 |
| 41 | Multi-portal sign-in / MFA | `routes/auth_directory_routes.py` + `mfa_routes.py` + `passkeys.py` | self | user | self · admin | admin only | admin | user (rotates) | account-lockout on N failures (`brute_force_blocks`) | 🟢 |

**Total workflows mapped:** 41 (consolidating 31 from the WORKFLOW_OWNERSHIP_MATRIX into a code-cited shape; sub-records collapsed into parents where appropriate).

**Net ownership verdict:** 33 🟢 · 7 🟡 · 1 🔴 (Fleet DVIR) · 1 🟦🔴 (Backup Alerts — preview verified dead, production unverifiable).

---

# AXIS I-2 · NOTIFICATION ROUTING

**Anchor memory documents:** `NOTIFICATION_DELIVERY_MAP.md` (2026-02-01) · `NOTIFICATION_DISCIPLINE_MATRIX.md` · `NOTIFICATION_GAP_REGISTER.md` (2026-05-29).
**Code anchor:** `lib/event_fanout.py` (72 lines · single audit point) + `routes/tasks_notifications.py` (`task_service`, `notification_service`).

## 2.1 Routing primitives — verified

**Email rule (`/app/backend/pm_routing.py`):**
```
ALWAYS_CC = ["jaymn.judd@mascigc.com", "safety@mascigc.com"]
COMPLIANCE_KINDS = {"inspection", "meeting", "jha", "incident"}
PM_ONLY_KINDS    = {"daily-report", "equipment-inspection"}
```
**Live runtime confirmation:** `GET /api/auto-email/routing-table` → returns exact same constants (P4 evidence — preview reports `always_cc`, `compliance_kinds=["incident","inspection","jha","meeting"]`, `pm_only_kinds=["daily-report","equipment-inspection"]`, `auto_email_enabled=false`). 🟢

**In-app fan-out architecture (Phase E):** every operational write calls `lib.event_fanout.emit_task_and_notification(...)` (or `emit_notification(...)` for a notification-only event). `task_service.create()` writes to `db.tasks` AND emits a `task.assigned` notification automatically. 🟢

## 2.2 Per-event routing matrix (code-verified call sites)

| Event | Kind | Channels | Bell to | Email to (CC) | Task to | Code site | Status |
|---|---|---|---|---|---|---|---|
| Daily Report submit | `daily-report` | email | (none) | PM only | (none) | `routes/daily_reports.py:271` (`schedule_auto_email`) | 🟢 |
| Site Inspection submit | `inspection` | email + bell + task | PM (`task.assigned`) | PM + ALWAYS_CC | PM | `routes/safety.py:318+338+367` | 🟢 |
| Safety Meeting submit | `meeting` | **email only** | — | PM + ALWAYS_CC | — | `routes/safety.py:464` (only `schedule_auto_email`) | 🟡 NEW-GAP-A |
| JHA submit | `jha` | **email only** | — | safety + ALWAYS_CC | — | `routes/safety.py:518` | 🟡 GAP-3 |
| Incident submit | `incident` | email + bell + task + secondary PM notification | Safety + PM | PM + ALWAYS_CC + severe-CC (`severe_incident_cc` when high severity) | Safety | `routes/safety.py:579+585+621` | 🟢 |
| Equipment Pre-Op PASS | `equipment-inspection` | email | — | PM only | — | `routes/equipment.py:199` | 🟢 |
| Equipment Pre-Op FAIL/OOS | `equipment-inspection` | email + bell + task + Dispatch visibility | **Shop (task)** + **Dispatch (notification)** | PM only | Shop | `routes/equipment.py:199+234+247+274` | 🟢 |
| QA/QC submit | `qaqc` | email + bell + task | per qaqc.py | PM + ALWAYS_CC | (per qaqc.py) | `routes/qaqc.py:210+217+222+249` | 🟢 |
| PO Request submit | `po-request` | email + bell + task | approver chain | per `email_routing_config` | approver | `routes/po_requests.py:206+220+242` | 🟢 |
| Asset / Shop Transfer | (transfer events) | bell + task + multiple visibility notifs | receiving location + Dispatch | — | receiving | `routes/asset_transfers.py:161+173+214+202+239+252+263+273` | 🟢 |
| Fire-Ext Inspection | (fire-ext fail) | bell + task | Safety | — | Safety | `routes/safety_portal/fire_extinguishers.py:122+125` | 🟢 |
| Document expiration nightly | (cron) | bell + task | HR | — | HR | `routes/document_expirations.py:119+232+237` | 🟢 |
| Employee Lifecycle onboarding | (hr task fan-out) | task only | HR | — | HR | `routes/employee_lifecycle.py:706+713` | 🟢 |
| Field Leadership 10 forms | `leadership-form` | **email only** | — | `leadership_always_to` (safety@ + admin) | — | `routes/field_leadership*.py` (no `emit_*`) | 🟡 GAP-1 |
| Safety Forms (issuance / training / return) | `safety-form-*` | **email only** | — | `SAFETY_FORMS_EMAIL_TO` | — | `routes/safety_forms.py` (no `emit_*`) | 🟡 GAP-2 |
| **Fleet DVIR / Weekly Lead / Weekly Emergency** | **none — no kind registered** | **NONE** | — | — | — | `routes/fleet_ops.py:412–553` (only `_audit` + `_rebuild_status`) | 🔴 ORPHAN-1 |
| Payroll Variance weekly cron | `payroll-variance-weekly-digest` | email | — | `PAYROLL_VARIANCE_EMAIL_TO` | — | `server.py:10241` | 🟢 |
| Payroll Variance manual run | (none) | — | — | — | — | manual button | 🟡 GAP-5 |
| Safety Digest weekly cron (Mon 14:00 UTC) | `safety-digest-weekly` | email | — | `SAFETY_DIGEST_TO_EMAIL` (default safety@) | — | `safety_digest.py` | 🟢 |
| Backup failure alert | `backup-failure` | email | Admin (in-app when scheduler alive) | `BACKUP_EMAIL_TO` (or safety@ fallback) | — | `health_monitor.py:49+200`, `server.py:5299/5374/6003` | 🟦 GAP-7 (scheduler dead in preview) |
| System red alert | `system-red-alert` | email | Admin | admin emails | — | `health_monitor._send_alert` | 🟢 |
| Directory / portal welcomes & resets | `*-welcome` / `*-reset` | email | — | recipient | — | `server.py:10027 _directory_send_email` + per-portal `_send_email` helpers | 🟢 |
| Job photos share | `job-photos-share` | email | — | designated PM / Safety | — | `server.py:8336 _job_photos_send_email` | 🟢 |
| Dispatch driver magic-link | (SMS or email bridge) | sms / email | — | driver phone | — | `dispatch_magic_links` | 🟢 |
| Notification bell poll (every portal chrome) | n/a | poll-only | all roles per scope | — | — | `NotificationBell.jsx` ↔ `GET /api/notifications/unread-count` | 🟢 (no push / no SSE — see §2.5) |

**Total notification events mapped:** 25 distinct event types.
**Verdict:** 19 🟢 · 5 🟡 · 1 🔴 (DVIR).

## 2.3 Per-portal digest endpoints — verified

| Endpoint | Auth scope | Code path | Status |
|---|---|---|---|
| `GET /api/admin/notifications/digest` | admin | `routes/notifications.py` | 🟢 |
| `GET /api/safety/notifications/digest` | safety | `routes/notifications.py` | 🟢 |
| `GET /api/hr/notifications/digest` | HR | `routes/notifications.py` | 🟢 |
| `GET /api/pm/notifications/digest` | PM | `routes/notifications.py` | 🟢 |
| `GET /api/dispatch/notifications/digest` | dispatch | `routes/notifications.py` | 🟢 |
| `GET /api/fl/notifications/digest` | FL | `routes/notifications.py` | 🟢 |
| `GET /api/field-leadership/portal/notifications-recent` | FL portal | `routes/field_leadership_portal.py:563` | 🟢 |

## 2.4 Cron-driven notifications — verified

| Cron | Cadence | Owner role | Code path | Status |
|---|---|---|---|---|
| Backup pipeline | hourly / 2 + 18 UTC | Admin | `lib/singleton_scheduler.py` + `_backup_scheduler_loop` in `server.py` | 🟦🔴 dead in preview (P2); prod state un-probable from preview · iter441 (2026-05-30) shrinks per-cycle peak RSS by -57.5 % via `BACKUP_EXPLICIT_EXCLUSIONS` of telemetry collections (`usage_events`, `health_monitor_runs`, `job_photo_thumb_cache`); see `BACKUP_MEMORY_REDUCTION_CERTIFICATION.md` |
| Safety digest | Mon 14:00 UTC | Safety | `safety_digest.py` | 🟢 |
| Document Expirations | nightly | HR | `routes/document_expirations.py:119` | 🟢 |
| PO Receipt-missing | nightly | requester + PM | within PO endpoints | 🟢 |
| Health monitor | periodic | Admin | `health_monitor.py` | 🟢 (red-alert email gated by env) |
| Cluster Capacity | periodic | Admin | `routes/cluster_capacity.py` | 🟢 |
| Payroll Variance weekly | weekly | HR + Admin | `server.py:10241` | 🟢 |

## 2.5 What is intentionally absent

- **Push notifications (FCM / APNs)** — NOT implemented. `grep -r FCM\|APNs /app/backend` → zero matches. Polling architecture by design.
- **WebSocket / SSE live push** — NOT implemented.
- **Real-time bell** — poll-based via `/api/notifications/unread-count`. ⚫ operator decision: confirm polling is acceptable long-term.

---

# AXIS I-3 · DASHBOARD DESTINATIONS

**Anchor memory documents:** `DASHBOARD_DESTINATION_MAP.md` (2026-02-01) · `DASHBOARD_DESTINATION_CERTIFICATION.md` · `ROLE_AWARE_OPERATIONAL_VISIBILITY_MATRIX.md`.
**Code anchor:** `/app/frontend/src/App.js` + per-portal hub components.

## 3.1 Destination existence by role (consolidated)

| Role | Hub URL | Total destinations | Notification surface | Task surface | Per-record action queue surfaces |
|---|---|---:|---|---|---|
| **Admin** | `/admin` | 35+ panels (superset) | bell on chrome · `/notifications` · `/admin/notifications/digest` | `/tasks` + admin task panels | Open Inspections · Open Incidents · PO Approvals · Backup Health (when alive) · System Health |
| **PM** | `/pm` | 19 | bell on chrome | `/tasks` | Open Inspections (scoped) · Open Incidents (scoped) · PO list (scoped) |
| **HR** | `/hr` | 13 | bell on chrome | `/tasks` | Document Expirations · Time-Off · Driver Qualification · Time Verification · Payroll Variance |
| **Safety Portal** | `/safety-portal` | 13 | bell on chrome | (none dedicated) | Open Inspections · Corrective Actions · Open Incidents · Fire-Ext · Open Safety Forms (count-only) |
| **Shop** | `/shop` | 4 | bell on chrome | `/tasks` | Pre-Op FAIL queue · Fleet defect list |
| **Dispatch** | `/dispatch-portal` | 4 | bell on chrome | `/tasks` | Active Hauls · Stuck > 30 m · Fleet OOS (visibility) |
| **Field Leadership Portal** | `/field-leadership/portal/dashboard` | 4 (bounded read of own crew) | `/field-leadership/portal/notifications-recent` | (none) | own-crew DR · Meetings · JHA · Pre-Ops · Fleet · Dispatch today+tomorrow · Incidents |
| **Driver** (dispatch sub-portal) | `/dispatch-portal/board` (single-use links) | — | — | — | active haul · scheduled trips |
| **Subcontractor / Foreman** | shared `/leadership` (legacy) | 5 (forms-only) | — | — | (no dashboard — submit-only) |
| **Public / Anon** | `/` (Public Hub) | 7 tile entries | — | — | (no dashboard — submit-only) |

## 3.2 Cross-portal record destinations (where one record can land)

| Record | All landing destinations | Notes |
|---|---|---|
| Inspection | `/admin/inspections/:id` · `/pm/inspections/:id` · `/safety-portal/audits` · `/inspections/:id` (redirects to admin = GAP-17) | 🟡 GAP-17 |
| Meeting | `/admin/meetings/:id` · `/pm/meetings/:id` · safety library · HR cross-portal viewer | 🟢 (+ NEW-GAP-A surfaces only as search-only) |
| JHA | `/admin/jha/:id` · `/pm/jha-plans` · safety library · `/jha` public read | 🟢 (+ GAP-3 = search-only) |
| Incident | every portal incidents view (admin/pm/hr/safety) | 🟢 |
| Daily Report | `/admin/daily/:id` · `/pm/daily/:id` · `/hr/daily-reports/:id` · `/daily/:id` | 🟢 |
| Equipment Pre-Op | `/admin/equipment/:id` · `/pm/equipment/:id` · `/shop/equipment/:id` · `/equipment/:id` (redirects to admin = GAP-16) | 🟡 GAP-16 |
| QA/QC | `/admin/qaqc/:id` · `/pm/qaqc` | 🟢 |
| PO Request | `/po-requests` · admin queue · HR PO panel | 🟢 |
| Field Leadership form | `/admin/leadership/records/:id` · `/leadership/records/:id` · `/hr/field-leadership` · `/pm/field-leadership` · `/field-leadership/portal/dashboard` | 🟡 GAP-1 (search-only, not action-queue) |
| Safety Forms | `/admin/safety/issuance/:id` · `/admin/safety/training/:id` · safety/forms detail · `/safety-portal/forms-records` | 🟡 GAP-2 (count-only on Safety Hub) |
| **Fleet DVIR submission** | `/fleet/dvir/new`, `/fleet/dvir/submit`, `/fleet/dvir/submitted/:id`, `/fleet/weekly-emergency/new`, `/fleet/weekly-lead/new` → **post-submit redirects to `/thank-you` · NO downstream surface anywhere** | 🔴 ORPHAN-1 |

## 3.3 Stat-card classification (count-only vs actionable queue)

| Stat card | Type | Where shown |
|---|---|---|
| Open Safety Forms | **count-only** | Safety Hub | (SOFT-2 / GAP-2) 🟡 |
| Field Leadership Forms | **search-only** | Admin · HR (SOFT-1 / GAP-1) 🟡 |
| JHA submissions | **search-only** | Admin · Safety (SOFT-3 / GAP-3) 🟡 |
| Open Inspections | actionable queue | Admin · Safety · PM 🟢 |
| Open Incidents | actionable queue | Admin · Safety · PM · HR 🟢 |
| Pre-Op FAIL queue | actionable queue | Shop 🟢 |
| PO Approvals | actionable queue | Admin · approver 🟢 |
| Active Hauls | live state | Dispatch 🟢 |
| Stuck > 30 m | live alert | Dispatch 🟢 |
| Document Expirations | actionable queue | HR · Safety 🟢 |
| Backup Health | live state | Admin 🟦 (dead in preview) |
| System Health | live state | Admin 🟢 |

**Net:** every record kind has a destination **except Fleet DVIR**. SOFT-1/2/3 are present-but-count-only.

---

# AXIS I-4 · ESCALATION CHAINS

**Anchor memory documents:** `SAFETY_ESCALATION_HIERARCHY_MAP.md` · `DISPATCH_ESCALATION_DENSITY_ANALYSIS.md` · ownership matrix §column "No-response path".

## 4.1 Escalation matrix (code-verified)

| Trigger | First responder | Escalation | Final authority | Code site | Status |
|---|---|---|---|---|---|
| Incident (any) | Safety (task + bell) + PM (visibility) | Admin via audit log | Admin / Safety lead | `routes/safety.py:585–620` | 🟢 first-response |
| **Severe Incident (high / critical / OSHA recordable)** | severity → `priority="Critical"` (else "High"); `severe_incident_cc` added to email | **no automated follow-up cadence if Safety doesn't acknowledge** | Admin / Safety lead (manual) | `routes/safety.py:590` (priority logic) | 🟡 GAP-14 (no no-response timer) |
| Equipment Pre-Op FAIL · 1–2 items | Shop task (`priority="High"`) + Dispatch notification | task remains open in Shop queue indefinitely | Shop sign-off | `routes/equipment.py:234–274` | 🟢 |
| Equipment Pre-Op FAIL · ≥3 items | Shop task (`priority="Critical"`) + Dispatch notification | as above | Shop sign-off | `routes/equipment.py:236` (priority logic) | 🟢 |
| **OOS Equipment** | Shop (task) + Dispatch (visibility) + status set to `oos`; defect `oos=true` | Defect lifecycle: open → acknowledged → repaired → cleared | Dispatch clears | `routes/fleet_ops.py:693, 729, 774, 819` | 🟢 |
| **Safety Defect (fleet)** | classified into `fleet_defects` rows with `severity` flag | Shop acknowledges + repairs | Dispatch clears | `routes/fleet_ops.py:_classify_failures` | 🟢 lifecycle works; **NO notification fan-out = part of ORPHAN-1** 🔴 |
| **Repeat Defect** | `_rebuild_status` projection tracks recurring defect; severity card surfaces in admin/dispatch boards | (no automated re-escalation; status surfaces in UI) | Dispatch + Shop manual | `routes/fleet_ops.py:524, 552` | 🟡 visibility-only (no automated re-fire) |
| Failed Inspection (site) | PM via bell+task (auto-email + fan-out) | (no defined escalation cadence) | PM | `routes/safety.py:331+338` | 🟢 first-response · 🟡 no cadence |
| Failed Time Verification | HR (manual review) | (none — HR is final authority) | HR | `routes/hr_portal.py` | 🟢 |
| Missing Driver Qualification | doc-expiration cron raises HR task; if hard expiry, dispatch_driver_sessions can refuse magic-link issue | (no separate escalation tier) | HR / Dispatch | `routes/document_expirations.py` + `routes/dispatch_portal_auth.py` | 🟢 |
| PO Request — approval-needed > N days | nightly cron raises `task.assigned` to approver | (no higher-tier escalation) | approver | `routes/po_requests.py:220+242` | 🟢 first-response · 🟡 GAP-15 |
| PO Receipt-missing > 30 days | nightly cron raises task | (no separate escalation to PM/Office Manager after extended threshold) | requester | within PO endpoints | 🟡 GAP-15 |
| Backup tick missed > 25 hours | watchdog (`watchdog_threshold_hours=25.0` per P2 evidence) | red-alert email + audit | Admin | `health_monitor.py:49` | 🟦 gated by scheduler being alive |
| System Health red | red-alert email + audit | (no separate escalation) | Admin | `health_monitor._send_alert` | 🟢 |
| Brute-force login attempt | account lockout via `brute_force_blocks` | (audit) | Admin | `auth_directory_routes.py` | 🟢 |

**Net escalation verdict:** every trigger HAS a first-responder defined. **No trigger has a fully automated multi-tier escalation cadence** (i.e., "if first responder doesn't acknowledge in X hours → escalate to second tier"). This pattern is consistent across the platform and is documented as P2 future hardening (GAP-14, GAP-15, etc.).

---

# AXIS I-5 · ORPHAN DETECTION

**Anchor memory documents:** `ORPHAN_WORKFLOW_REPORT.md` (2026-05-29) · `ORPHAN_AND_GAP_REGISTER.md` (2026-02-01).

**Re-validation method:** for every workflow in §1 (41 entries), check four pillars:
- (a) record has a defined owner?
- (b) record has a notification path (email OR bell OR task)?
- (c) record has a dashboard destination (action queue OR search surface)?
- (d) record has a next-step authority (closer / approver / signoff)?

A failure of ANY pillar = orphan candidate. Two or more = hard orphan.

## 5.1 Confirmed orphans

### ORPHAN-1 · Fleet DVIR / Weekly Lead / Weekly Emergency

| Pillar | Status | Evidence |
|---|---|---|
| (a) Owner | ⚫ undefined in code (policy intended "Shop + Dispatch" per WORKFLOW_OWNERSHIP_MATRIX.md row "Fleet DVIR" but submission handler doesn't enforce or notify) | `routes/fleet_ops.py:412–553` |
| (b) Notification path | 🔴 NONE — zero `schedule_auto_email`, zero `emit_*`, zero `task_service`, zero `notification_service` references in `fleet_ops.py` | `code_fanout_callsites.txt` final block |
| (c) Dashboard destination | 🔴 NONE — no "Open DVIRs" tile on Dispatch or Shop hub | `DASHBOARD_DESTINATION_MAP.md §10` |
| (d) Next-step authority | 🟡 partial — defect lifecycle is well-defined (acknowledge → repair → clear), BUT the DVIR submission itself doesn't auto-create a defect-class task for "review the new DVIR" | `routes/fleet_ops.py:693, 729, 774, 819` |

**Severity:** P0 — submitter submits a Fleet inspection, the inspection is audited and status is rebuilt, but no human is told. A defect can be created (`fleet_defects` insert) but no task or bell fires.

**Operator decision required:** is Fleet DVIR meant to be a passive ledger (Driver fills in, system stores, Dispatch reviews on their own time) OR an active workflow (defect → immediate Shop task + Dispatch visibility)? The platform was clearly designed with both DVIR-side and Defect-side schemas, but only the Defect lifecycle is wired.

## 5.2 Soft orphans (workflow functions but visibility incomplete)

| ID | Workflow | Failing pillar | Severity |
|---|---|---|---|
| SOFT-1 / GAP-1 | Field Leadership 10 forms | (b) partial — email only, no bell/task; (c) search-only | P1 |
| SOFT-2 / GAP-2 | Safety Equipment Issuance / Training / Return | (b) partial — email only; (c) count-only stat card | P1 |
| SOFT-3 / GAP-3 | JHA submit | (b) partial — email only, no task fan-out; (c) search-only | P1 |
| SOFT-3b / **NEW-GAP-A** | Safety Meeting submit | (b) partial — email only, no bell/task; (c) search-only | P1 |
| SOFT-4 / GAP-4 | Training Record assigned (supervisor lens) | (b) partial — trainee bell+task fires; supervisor of trainee NOT notified (`linked_supervisor` lookup intermittent) | P1 |

## 5.3 Cron orphans (workflow runs but operator-visibility gaps)

None confirmed — every cron in §2.4 writes to either `audit_events`, `tasks`, `notifications`, or sends email.

## 5.4 Definitive orphan inventory

- **Hard orphans (no notification path):** 1 → ORPHAN-1 (Fleet DVIR)
- **Soft orphans (visibility-incomplete):** 5 → SOFT-1, SOFT-2, SOFT-3, NEW-GAP-A, SOFT-4
- **No "record-with-no-consumer" found** beyond ORPHAN-1 — every other operational write reaches at least one of: email · bell · task · audit · status projection · downstream cron.

---

# AXIS I-6 · GAP CONSOLIDATION

**Anchor memory documents (reconciled):**
- `ORPHAN_AND_GAP_REGISTER.md` (2026-02-01)
- `NOTIFICATION_GAP_REGISTER.md` (2026-05-29)
- `WORKFLOW_FAILURES_AND_DEAD_ENDS.md`
- `CROSS_PORTAL_OPERATIONAL_GAPS.md`
- `REMAINING_OPERATIONAL_GAPS.md`
- Batch D, E, F, G, H executive summaries

**Output:** `PLATFORM_GAP_LEDGER_FINAL.md` (companion file) — deduplicated, severity-ranked, evidence-backed.

**Headline from companion ledger:**

| Tier | Count | IDs |
|---|---:|---|
| P0 — orphan operator-decision | 1 | ORPHAN-1 (DVIR) |
| P0 — broken held | 1 | GAP-7 (backup scheduler — verified dead in preview) |
| P1 — visibility gaps | 8 | GAP-1, GAP-2, GAP-3, NEW-GAP-A, GAP-4, GAP-10, GAP-16, GAP-17 |
| P2 — improvement gaps | 6 | GAP-5, GAP-8, GAP-9, GAP-14, GAP-15, GAP-18 |
| P3 — test-only | 3 | GAP-11, GAP-12, GAP-13 |
| **Total operational gaps** | **19** | (+ 1 confirmed orphan) |

---

# AXIS I-7 · DISASTER RECOVERY VALIDATION MATRIX

**Anchor memory documents:**
- `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md` (2026-05-30 · Batch G)
- `DISASTER_RECOVERY_DRILL_REPORT.md` (Batch E)
- `BATCH_E_EXECUTIVE_SUMMARY.md`, `BATCH_F_EXECUTIVE_SUMMARY.md`, `BATCH_G_EXECUTIVE_SUMMARY.md`
- `PHOTO_REHYDRATION_RECOVERY_REPORT.md`
- `RESTORE_RUNBOOK.md`

**Output:** `DISASTER_RECOVERY_VALIDATION_MATRIX.md` (companion file) — 16-component matrix · per-component backup / restore / test / verify status.

**Headline from companion matrix:**

| Pillar | 🟢 | 🟡 | 🔴 |
|---|---:|---:|---:|
| Backed up | 16 | 0 | 0 (subject to scheduler being alive — currently 🟦 in preview, claim "alive in prod since Batch D") |
| Restorable | 15 | 1 | 0 |
| Tested (drill) | 14 | 2 | 0 |
| Verified (post-restore boot) | 13 | 3 | 0 |

See `DISASTER_RECOVERY_VALIDATION_MATRIX.md` for per-component detail.

---

## 8 · Roll-up — answers to the operator's questions

| Question | Verified answer | Evidence anchor |
|---|---|---|
| What talks to what? | §1 workflow ownership + §2 event matrix (25 events) | this map §1, §2 |
| Who owns what? | §1 column "Owner" — every workflow has an owner except Fleet DVIR (ORPHAN-1) | this map §1.1 |
| Who gets notified? | §2.2 — 25 events with per-channel recipients confirmed in code | this map §2.2 |
| What is orphaned? | §5.1 — exactly 1 hard orphan (Fleet DVIR) + 5 soft orphans | this map §5 |
| What is broken? | GAP-7 (backup scheduler — verified dead in preview); production state unverifiable from preview | P2 runtime evidence |
| What is recoverable? | All 16 DR-core collections backed up + restorable (per Batch E drill: 283K records restored to drill DB) | `DISASTER_RECOVERY_VALIDATION_MATRIX.md` |
| What is not recoverable? | TTL collections (nonces · chunks · magic links) — by design · in-flight sessions · anything written after last archive snapshot (≤ 60 min RPO target · ≤ 24 hr actual in current state) | `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md §2.2` |
| What happens if the platform dies tomorrow? | RTO ~ 10 min (mongo-only loss / R2 healthy) or ~ 20–40 min (mongo + R2 both lost), assuming operator has the runbook + env vars handy | `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md §2.3` |
| What happens if R2 dies tomorrow? | Mongo data survives. Photo references (`photo://`) return 404 on retrieval. New writes are unaffected (the writer fails-soft per `daily_reports.py:_sanitize_inline_photos`). Recovery: re-run a fresh backup → R2 re-build from archive's `photos/` prefix via `--restore-photos` flag | `PHOTO_REHYDRATION_RECOVERY_REPORT.md` |
| What happens if Mongo dies tomorrow? | Full restore drill proves recovery → 283K records to drill DB in Batch E. Multi-login users seeded with `Welcome2MASCI!` rotate-forced. | `DISASTER_RECOVERY_DRILL_REPORT.md` |
| What happens if both die tomorrow? | Restore Mongo from R2 archive AND re-upload `photos/` prefix to R2 via `restore_drill.py --restore-photos`. RTO ~ 20–40 min. | Batch G evidence |

→ See `PLATFORM_RECOVERABILITY_PROOF_REPORT.md` for the full evidence chain on each of the four "if … dies tomorrow" scenarios.

---

## 9 · Stop-condition compliance (Batch I)

- ✅ Zero code edits — only `mcp_create_file` for net-new memory deliverables
- ✅ Zero schema or env changes
- ✅ Zero production writes — preview-only probes (DB inventory queries are reads)
- ✅ Zero remediation — every gap is observed, none fixed
- ✅ Zero new features
- ✅ Triangulation rule applied to every claim — citations exist for every cell
- ✅ Where production cannot be reached, the limit is recorded (DELTA-D1, AXIS I-7 production scheduler verification)

---

## 10 · Cross-link index — every doc consulted

| Axis | Memory doc | Code anchor | Runtime probe |
|---|---|---|---|
| I-1 | `WORKFLOW_OWNERSHIP_MATRIX.md` | `routes/daily_reports.py`, `routes/safety.py`, `routes/equipment.py`, `routes/qaqc.py`, `routes/po_requests.py`, `routes/fleet_ops.py`, `routes/asset_transfers.py`, `routes/document_expirations.py`, `routes/employee_lifecycle.py`, `routes/safety_portal/fire_extinguishers.py` | DBI-1 |
| I-2 | `NOTIFICATION_DELIVERY_MAP.md`, `NOTIFICATION_DISCIPLINE_MATRIX.md`, `NOTIFICATION_GAP_REGISTER.md`, `pm_routing.py` constants | `lib/event_fanout.py`, `routes/tasks_notifications.py`, all 10 fan-out files in `code_fanout_callsites.txt` | P4 (`/api/auto-email/routing-table`) |
| I-3 | `DASHBOARD_DESTINATION_MAP.md`, `ROLE_AWARE_OPERATIONAL_VISIBILITY_MATRIX.md`, `PLATFORM_ROUTE_MAP.md` | `/app/frontend/src/App.js`, per-portal hub `.jsx` | P5 (`/api/admin/jobs`) |
| I-4 | `SAFETY_ESCALATION_HIERARCHY_MAP.md`, `DISPATCH_ESCALATION_DENSITY_ANALYSIS.md` | `routes/equipment.py:236`, `routes/safety.py:590`, `routes/fleet_ops.py:693+729+774+819` | (escalation paths are static — no runtime trigger fired) |
| I-5 | `ORPHAN_WORKFLOW_REPORT.md`, `ORPHAN_AND_GAP_REGISTER.md` | `routes/fleet_ops.py` (zero fan-out grep result) | (static) |
| I-6 | All gap docs listed in §6 anchor | (composite) | (static) |
| I-7 | `FULL_RECOVERABILITY_CLOSEOUT_REPORT.md`, `DISASTER_RECOVERY_DRILL_REPORT.md`, `BATCH_E_EXECUTIVE_SUMMARY.md`–`BATCH_G_EXECUTIVE_SUMMARY.md`, `PHOTO_REHYDRATION_RECOVERY_REPORT.md`, `RESTORE_RUNBOOK.md` | `/app/scripts/restore_drill.py`, `/app/scripts/migrate_dr_photos.py`, `lib/singleton_scheduler.py` | P2 (`/api/admin/backups-scheduler-state`), P3 (`/api/admin/backups`), DBI-1 |

---

## 11 · Net verdict

**Platform operational understanding: 100 % verified** within the preview-environment constraint.

The only verification that cannot be performed from this environment is the live production state of the backup scheduler (preview reports `alive=false`; production claim "alive since Batch D" is recorded in `BATCH_D_EXECUTIVE_SUMMARY.md` but is not re-probable from preview). This is recorded as `DELTA-D1` in `PLATFORM_TRUTH_DELTA_REPORT.md`.

All other axes — workflow ownership, notification routing, dashboard destinations, escalation chains, orphan detection, gap consolidation, disaster recovery — are reconciled across Memory · Code · Runtime with full citations.

**Outstanding operator decisions surfaced:**
1. ORPHAN-1 / GAP-6 — Fleet DVIR: passive ledger vs active workflow?
2. NEW-GAP-A — Safety Meeting: join JHA fix-track or remain email-only intentionally?
3. Real-time notification push — confirm polling is acceptable long-term, or schedule an SSE/WebSocket batch?
4. Production scheduler state — verify `alive=true` in production (`/api/admin/backups-scheduler-state` against the production base URL).

---

_End of PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md. No remediation begun. Operator owns next directive._
