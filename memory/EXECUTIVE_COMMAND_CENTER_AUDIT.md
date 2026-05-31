# Executive Command Center — Platform Audit (Pillar 2 · Batch 1 of N)

**Classification:** OMEGA Pillar 2 · DESIGN / AUDIT / SPEC ONLY · No code · No DB changes · No endpoints · No UI · No notifications · No workflow changes
**Generated:** 2026-05-31 UTC
**Author:** E1
**Scope:** Inventory every existing executive-relevant surface (metrics, workflows, dashboards, reports, notifications, task systems, accountability systems) and surface the gaps the MASCI Executive Operations Command Center must close.
**Audience:** Operations Leadership · Executive Leadership Team (Jaymn primary)
**Companion docs:** `EXECUTIVE_COMMAND_CENTER_SPEC.md` · `EXECUTIVE_HEATMAP_SPEC.md` · `EXECUTIVE_DATA_SOURCE_MAP.md` · `EXECUTIVE_IMPLEMENTATION_ROADMAP.md`

---

## 1 · Audit method

Read-only triangulation across three sources:
- **Memory (M):** anchor docs in `/app/memory/` — `PLATFORM_OPERATIONAL_TRUTH_MAP_v1.md`, `DASHBOARD_DESTINATION_MAP.md`, `WORKFLOW_OWNERSHIP_MATRIX.md`, `NOTIFICATION_DELIVERY_MAP.md`, `APPROVAL_PERMISSION_MATRIX.md`, `OMEGA_GAP_REGISTER.md`, `PLATFORM_GAP_LEDGER_FINAL.md`.
- **Code (C):** 80 route files under `/app/backend/routes/`, ~30 admin pages under `/app/frontend/src/pages/admin/`, ~120 top-level pages.
- **Runtime (R):** preview/prod `/api/admin/*` probes from recent OMEGA batches.

No write actions. No probes that mutate state.

---

## 2 · What executive-level information ALREADY EXISTS

### 2.1 Operational data sources (already captured)

| Domain | Collection(s) | Owner workflow | Already surfaced where? |
|---|---|---|---|
| Jobs / Projects | `jobs_master` (12), `projects` (2) | Admin → PM | `/admin/jobs`, `/admin/pnl` |
| Daily field activity | `daily_reports` (23), `field_memory_notes` (7) | Foreman → PM | `/admin/daily`, per-PM scope |
| Safety records | `incidents` (22), `meetings` (6), `jhas` (4), `inspections` (7), `corrective_actions` (18) | Safety, PM | `/admin/incidents`, `/admin/meetings`, `/admin/jha`, `/admin/inspections`, `/safety-portal/corrective-actions` |
| Equipment / Fleet | `equipment_master` (39), `equipment_inspections` (25), `fleet_defects` (19), `fleet_status` (5), `equipment_parts` (9), `haul_cycles` (8) | Shop, Dispatch | `/admin/equipment`, `/shop/*`, `/admin/equipment-inspections` |
| Dispatch | `dispatch_assignments` (40), `dispatch_state_events` (10), `dispatch_driver_sessions` (7), `dispatch_continuity_events` (4) | Dispatch | `/admin/dispatch`, `/dispatch-portal/*` |
| Procurement (POs) | `po_requests` (31) | Approvers (admin/leadership/hr per routing) | `/admin/po-requests`, per-portal PO digests |
| Asset lifecycle | `asset_holds` (20), `asset_transfers` (14), `asset_assignments` (10), `transfer_requests` (11) | Admin · Shop · Dispatch | `/admin/operational-inventory`, `/admin/assets/:id` |
| HR / People | `employees` (75), `user_directory` (22), `field_leadership_records` (24), `document_expirations` (23), `payroll_variance_batches` (7) | HR · Admin | `/hr/*`, `/admin/people`, `/admin/terminations` |
| Tasks (action items) | `tasks` (26) | dynamic — per workflow | `/api/tasks` (per-portal), no admin master list |
| Notifications (bell) | `notifications` (13) | dynamic — per workflow | `/api/notifications` (per user) |
| Audit / Accountability | `audit_events` (4), `admin_audit` (3), `fleet_audit` (4) | system | `/admin/audit`, `/admin/audit-log` |
| Operations events (cross-portal) | `operations_events` (24) | any portal | `/admin/operations-events` |
| Operational constraints | `operational_constraints` (13), `operational_links` (15) | Admin · PM | `/constraints`, `/admin/operational-inventory` |
| QA/QC | `qaqc_inspections` (9) | Safety, PM | `/admin/qaqc` |
| Training / Compliance | `safety_training_records` (15), `training_track_records` (4), `training_guides` (14), `compliance_findings` (via routes) | Safety · HR | `/admin/training`, `/admin/compliance`, `/admin/compliance-findings` |
| Backup / Recoverability | `backup_health` (23), `drill_runs`, `backup_drift_history` (7) | system | `/admin/recovery` ✅ (Pillar 0 — FROZEN) |

**Verdict:** the underlying data exists. The platform has 132+ collections, 80 route files, and 30+ admin pages. **Raw data availability is not a blocker.**

### 2.2 Operations-relevant dashboards that already exist

Per `DASHBOARD_DESTINATION_MAP.md` and live `ls /app/frontend/src/pages/admin/`:

| Dashboard | Audience today | Operational angle | Executive-relevant fields available |
|---|---|---|---|
| `/admin/system` + `/admin/recovery` | super-admin | Backup, RPO, RTO | RPO pill · RTO pill · last backup · scheduler.alive |
| `/admin/jobs` | Admin · PM | Job master | Active job count · per-job assignees |
| `/admin/dispatch` | Admin · Dispatch | Dispatch state | Active assignments · OOS equipment count |
| `/admin/equipment` + `/admin/equipment-inspections` | Admin · Shop | Equipment health | Pre-op trends · open-items count · OOS units |
| `/admin/incidents` | Admin · Safety · PM | Safety severity | Open incidents · severity tier · acknowledged/resolved status |
| `/admin/meetings` + `/admin/inspections` + `/admin/jha` | Admin · Safety | Safety cadence | Last-X-days submission rates per PM scope |
| `/admin/qaqc` | Admin · Safety · PM | QA cadence | Per-project QAQC counts |
| `/admin/po-requests` | Admin · approvers | Procurement | PO state · approval age · receipt-missing |
| `/admin/compliance-findings` | Admin · Safety | Compliance | Open/Acknowledged/Resolved tiers · severity |
| `/admin/operations-events` | Admin · all portals (read) | Cross-portal events | Severity · status · source_module |
| `/admin/analytics` (AdminAnalytics.jsx) | Admin | Usage analytics | Route hits per portal |
| `/admin/audit` + `/admin/audit-log` | Admin | Accountability trail | Every state change in `audit_events` |
| `/admin/sessions` | Admin | Active tokens | Currently signed-in users per portal |
| `/admin/operational-inventory` | Admin | Asset roster | Asset class · status |
| HR cross-views (`/hr/safety-records`, `/hr/employee-accountability`, `/hr/time-verification`) | HR | Workforce | Hours · accountability events |
| PM panel (`/pm`) | PM | Per-project scope | PM-scoped reports/incidents/inspections |
| Field Leadership Portal dashboard (`/field-leadership/portal/dashboard`) | FL | Operational visibility | DR · safety meetings · JHA · PO · DVIR · dispatch (today/tomorrow) |

**Total existing admin surfaces ≈ 30.** They are domain-specific, deep, and each tells a *vertical* story (safety, dispatch, equipment, HR…). **There is no horizontal "single-glass" surface today.**

### 2.3 Accountability / notification primitives (already exist)

- **Tasks system** (`tasks_notifications.py`, collection `db.tasks`): generic action-item store. Surfaced per-portal at `/api/tasks`, no master executive view.
- **Notification bell** (`db.notifications`): per-user inbox. Each portal exposes its own `/api/{portal}/notifications/digest`.
- **Per-portal digests** (`routes/admin_operator_digest.py`, `pm_routes.py`, `hr_portal.py`, `safety.py`, `dispatch_portal_auth.py`): exist as separate, scoped digests. **No executive roll-up.**
- **Operational events** (`db.operations_events` with indexes on `severity`, `status`, `source_module`, `event_type`, `asset_id`, `employee_id`, `project_id`, `created_at`): the **closest existing primitive to an executive heat-map substrate** — see §3.1.
- **Audit log** (`db.audit_events`, `db.admin_audit`, `db.fleet_audit`): immutable accountability trail. Already mature; can supply "who did what when".

### 2.4 Known existing surface that *resembles* the executive view

`/app/backend/routes/operations_center.py` already exists. It exposes summary counts (per quick grep, `operations_events.count_documents` aggregations on line ~200). **This is the most likely landing zone for executive widgets** — but its current scope is operations-events-only, not the cross-domain roll-up the operator described. See `EXECUTIVE_DATA_SOURCE_MAP.md` for the proposed widget-by-widget reuse pattern.

---

## 3 · What executive-level information is MISSING

The gap is **not raw data**. The gap is **horizontal synthesis, scoring, and a single landing surface**.

### 3.1 Missing single-glass primitives

| # | Missing capability | Why operator needs it | Closest existing primitive |
|---|---|---|---|
| EXV-1 | Single horizontal Command Center surface | One screen to answer the 10 operator questions; today requires hunting across 30 admin pages | none (this batch's blueprint) |
| EXV-2 | Cross-domain RAG (Red/Amber/Green) scorer | Today every dashboard renders raw counts/lists; no normalized health score per domain | partial — `/admin/recovery/snapshot` returns `pill: AMBER` |
| EXV-3 | "Top-N priorities for the day" reducer | Today operator must mentally rank thousands of records; success criterion is "identify top 5 in 5 minutes" | none — but `tasks.priority` + `operations_events.severity` fields exist |
| EXV-4 | PM / Superintendent load index | Today PMs are visible per-project (`/admin/project-managers`) but not aggregated as a workload heat | partial — `/admin/project-managers/activity` returns `reports_7d`, `job_count` per PM |
| EXV-5 | Approval-aging cross-portal index | PO digests exist per-portal; no executive "approvals N+ days old" view | `po_requests.status` + cron in `po_digest_admin.py` |
| EXV-6 | Project-risk index (red/yellow/green per project) | Today PM scope shows raw reports; no rolled-up "this project is trending red" signal | `project_health.py` has scaffolding; not surfaced executively |
| EXV-7 | Operational bottleneck detector | No single view of "what is jammed up right now" — stuck dispatch assignments, expiring DVIRs, aging tasks | partial — `dispatch_state_events` + `tasks.due_at` |
| EXV-8 | "What should I focus on next?" recommender | Currently leadership decides priority by gut feel; the question requires a scoring engine | none |
| EXV-9 | Executive-grade audit drill-down from widget | Today every dashboard has audit, but no "click red square → see why it's red → see who owns it → see ETA" trail | partial — audit collections exist; drill UX does not |
| EXV-10 | Time-to-information SLA | No telemetry today measuring "did leadership identify the issue before it became a crisis?" | none |

### 3.2 Missing scoring methodology

Today **no shared, objective Red/Yellow/Green scoring exists across domains.** Each dashboard surfaces raw counts:
- Safety: "X open incidents" (no severity-weighted score)
- Equipment: "Y units OOS" (no impact-weighted score)
- PM: "Z reports filed this week" (no compliance-vs-expected score)
- PO: "N requests pending" (no aging-tier score)

`/admin/recovery/snapshot` is the **only existing surface with normalized RAG output** (`pill: GREEN/AMBER/RED`). Its pattern should be adopted across the Command Center. See `EXECUTIVE_HEATMAP_SPEC.md`.

### 3.3 Missing executive workflow questions

Of the 10 operator-mandated questions, here is the audit of what can be answered today *with hunting*:

| # | Question | Today's answer path | Effort today | Gap class |
|---|---|---|---|---|
| 1 | What jobs need attention today? | `/admin/jobs` + manual scan of recent `daily_reports` + `incidents` linked to job | 15–30 min hunting | **synthesis** |
| 2 | What safety issues need attention today? | `/admin/incidents` + `/admin/compliance-findings` + `corrective_actions` collection | 10–20 min | **synthesis** |
| 3 | What equipment issues need attention today? | `/admin/equipment-inspections` (open-items) + `fleet_defects` + `asset_holds` | 10–15 min | **synthesis** |
| 4 | What accountability items are overdue? | scan `tasks` per portal + `notifications` unread + `corrective_actions` open | 15–25 min | **synthesis** |
| 5 | What PMs are overloaded? | `/admin/project-managers/activity` only shows reports/jobs — no overload score | 5 min + judgment | **scoring** |
| 6 | What supervisors are overloaded? | no dedicated view today | not answerable | **collection + scoring** |
| 7 | What approvals are aging? | `/admin/po-requests` filter by status + age (manual mental math) | 5–10 min | **scoring** |
| 8 | What projects are at risk? | no rolled-up signal — must inspect each project's safety/equipment/cost manually | 30–60 min per project | **scoring + synthesis** |
| 9 | What operational bottlenecks exist? | no surface today | not answerable | **detection** |
| 10 | What should the Operations Director focus on next? | no surface today | not answerable | **recommender** |

**Net:** of 10 executive questions, **3 are not answerable today, 5 require ≥10 min of hunting, 2 require scoring engines that don't yet exist.**

### 3.4 Missing time-to-insight target

The operator's measurable goal: *"log in each morning and within 5 minutes know the top operational priorities."* Today this takes ≥60 minutes of cross-portal navigation. The Command Center's stop-condition is therefore a **measurable ≥80% reduction in time-to-insight** (60 min → ≤5 min).

---

## 4 · Audit verdict

| Statement | Verdict |
|---|---|
| The raw data exists across 132+ MongoDB collections and is consistently captured | ✅ TRUE |
| Domain-specific dashboards exist and are operationally healthy | ✅ TRUE |
| A single-glass horizontal executive surface exists | ❌ MISSING (EXV-1) |
| A cross-domain RAG scoring methodology exists | ❌ MISSING (EXV-2) |
| Time-to-insight for executive priorities meets operator target (5 min) | ❌ MISSING — current ≥60 min |
| The platform can ANSWER all 10 operator questions today | ❌ MISSING — 3 not answerable, 5 require hunting, 2 require scoring |
| The frozen Backup & Recoverability `recovery/snapshot` pattern is a viable blueprint to extend | ✅ TRUE — RAG + warnings list + computed_at pattern is reusable |

**Conclusion:** All inputs needed to build the Command Center are present in the platform. The required work is **synthesis, scoring, and presentation**, not data acquisition. The next four deliverables specify exactly what to build, how to score it, where each datum comes from, and the implementation sequence.
