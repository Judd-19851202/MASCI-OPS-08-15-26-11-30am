# FORGEDOPS · LOGISTICS, DISPATCH, FLEET, MATERIALS & OPERATIONS MASTER AUDIT
**ZERO-DRIFT ARCHITECTURE REVIEW · 2026-02-10**

> Read-only audit. No code changes. No features. No mockups. The deliverable is the **final operational architecture** for ForgedOps before any Dispatch rebuild begins, satisfying the five pillars: **Powerful · Simple · Beautiful · Trusted · Proven.**

---

## TABLE OF CONTENTS

* §1   Executive Verdict (one-page summary)
* §2   Phase 1 · Existing Platform Inventory (verified counts)
* §3   Phase 2 · User Role × Information / Action / Decision Matrix
* §4   Phase 3 · Dispatch Audit
* §5   Phase 4 · Driver Workflow Audit
* §6   Phase 5 · Motive Integration Audit
* §7   Phase 6 · FleetWatcher Integration Audit (planned)
* §8   Phase 7 · Shop Audit
* §9   Phase 8 · PM Portal Audit
* §10 Phase 9 · Safety Audit
* §11 Phase 10 · Operations Center Audit
* §12 Phase 11 · Admin Audit
* §13 Phase 12 · Communications Audit
* §14 Phase 13 · Master Asset Governance (the key Phase 13 deliverable)
* §15 Final Architecture · 13 Required Maps
* §16 Prioritized Build Sequence (P0 → P3)
* §17 Pillar-Scorecard for Every Recommendation
* §18 STOP — what NOT to touch yet

---

## §1 · EXECUTIVE VERDICT

ForgedOps is **operationally mature on the surface, fragmented underneath**.

* **107 backend route files**, **54 backend top-level modules**, **39+ Mongo collections in active use**, **154 frontend pages**, **185 frontend components**.
* The platform already covers Dispatch, Driver, Shop, Safety, HR, PM, Field-Leadership, Admin, Operations-Center, Operations-Intelligence, Operations-Actions, Trench-Safety, Job-Photos, Daily-Reports, Incidents, Inspections, Meetings, JHA, Tasks, Notifications, Document-Expirations, Field-Equipment-Catalog, Material-Movement (skeleton), Asset-Transfers, Asset-Mapping-Recon, Project-Health, Project-Identity-Governance, Backup, Sentry, MFA, Resend email, Twilio SMS, Cloudflare R2.
* Motive integration is **plumbing-only and architecture-locked** (`MOTIVE_INTEGRATION_STRATEGY.md` — "validate, don't surveil"); 5 dedicated route files; 100+ Motive memory documents.
* MaintainX integration is a **read-first scaffold**, API key unset (`MAINTAINX_SYNC_ENABLED=false`, `MAINTAINX_WRITE_ENABLED=false`).
* FleetWatcher integration is **planned only** — no code, no env vars, no routes.

**The drift problem** that this audit was authorized to find:

1. **Asset identity is fragmented across collections.** `equipment`, `equipment_master`, `field_leadership_equipment_catalog`, `trench_safety_assets`, `asset_mappings`, `asset_transfers`, `motive_events` each carry partial asset truth. No single source-of-truth contract exists in production. (§14 fixes this with the recommended Hybrid · ForgedOps-canonical model.)
2. **Dispatch UI has 8 production pages but lacks a single "Command Center" that fuses Dispatch + Operations + PM-visibility + Shop-readiness into one operator board.** Building blocks exist (`AdminCommandCenter`, `DispatchHub`, `DispatchBoard`, `AdminOperationsDashboard`) — they are not converged.
3. **Communications are scattered.** Notifications exist per-portal (`/api/admin/notifications/digest`, `/api/safety/...`, `/api/hr/...`, `/api/pm/...`, `/api/dispatch/...`, `/api/fl/...`) but there is no unified Driver↔Dispatch↔Shop↔PM messaging spine.
4. **The Operations Center exists as a single read endpoint** (`/api/operations-center`) but is not yet the single-source-of-truth dashboard the directive requires.

**Final recommendation:** Build the **Dispatch Command Center** (Phase 1 below) on top of what already exists — don't rebuild. The architecture below shows how every existing surface becomes an input into one unified operator board, and how Master Asset Governance (§14) gives the platform a single, audited asset spine.

---

## §2 · PHASE 1 · EXISTING PLATFORM INVENTORY

### 2.1 · Portal map (frontend, classified)

| Portal | Login → Hub → key pages | Classification |
|---|---|---|
| **Admin** | `AdminLogin → AdminHub` → 38 admin sub-pages (Analytics, AssetMapping, AuditLog, CommandCenter, Compliance, Database, Dispatch, Dls debrief, DriverIntel, Email, Equipment, Geofence, Governance, Integration Center, Jobs, MasterHistory, Mfa, OperationalInventory, OperationsDashboard, OperationsEvents, People, Profile, ProjectIdentityGovernance, PromoAssets, Recovery, Sessions, System, Training, AssetProfile, DeployRecovery, SelfProtection, SystemHealth) | **Production Ready** (38 pages, very mature) |
| **Dispatch** | `DispatchLogin → DispatchHub → DispatchBoard` + driver-side `DispatchDriverProfile`, `DispatchDriverQualification`; admin-side `AdminDispatch` (775 LOC) | **Production Ready** for haul-board flow; **Partially Complete** for a unified Command Center |
| **Driver** | `/d/:token` magic-link landing → `ShiftStart` → `DriverShift` | **Production Ready** for shift start; **Placeholder** for in-shift telemetry surface |
| **Shop** | `ShopLogin → ShopHub` + `ShopTrenchSafetyRepairs`; PM/admin views via `AdminEquipment`, `AdminOperationalInventory` | **Partially Complete** — login + landing exist; defect/work-order surface lives in `/api/shop/fleet/*` but is not yet a single Shop Command Board |
| **PM** | `PmLogin → PmHub → PmProjectDetail`, `PmCrewCompliance`, `PmFieldLeadership`, `PmQaqcList`, `ProjectPnlPage`, `PmSections` | **Partially Complete** — pages exist but the PM dashboard does NOT yet aggregate trucks · equipment · materials · production · financial KPIs in one view (the directive's PM requirements §9 are 50% covered) |
| **HR** | `HrLogin → HrHub` + 22 sub-pages (Employees, DriverProfile, DriverQualification, Incidents, PayrollVariance, TimeOff, TimeVerification, Training, MotiveDrivers, FieldLeadership users…) | **Production Ready** (large surface) |
| **Safety** | `SafetyLogin → SafetyHub` + Audits, CorrectiveActions, Digest, Documents, DriverProfile, EmployeeProfiles, FireExtinguishers, FormsHub, FormsLogin, FormsRecords, Hub, Incidents, Reports, Section, TopicLibrary, TrainingRecords | **Production Ready** |
| **Field-Leadership** | `FieldLeadershipPortalLogin → FieldLeadershipPortalDashboard` + `FormPage`, `Hub`, `Records`, `View`, `DriverQualification` | **Production Ready** |
| **Operations** | `AdminOperationsDashboard`, `OperationsActions`, `OdrCenter` (over-due reports) | **Partially Complete** — pieces exist, not yet the unified live-ops board the directive describes |
| **Public Hub** | `/` (`Hub.jsx`), `SignIn`, `Tasks`, `NotificationsDigest`, `JobPhotosLibrary`, `DocumentExpirations`, `TrenchBoxes`, training pages, legal pages | **Production Ready** |

### 2.2 · Backend route surface (counts verified)

* **107 route files** in `backend/routes/`.
* **54 top-level backend modules** in `backend/` (excluding routes, services, tests).
* **39+ Mongo collections** in active read/write use (sample: `dispatch_assignments`, `equipment_master`, `equipment`, `jobs_master`, `daily_reports`, `job_photos`, `employees`, `incidents`, `inspections`, `meetings`, `motive_events`, `motive_geofences`, `safety_forms`, `field_leadership_records`, `field_leadership_equipment_catalog`, `tasks`, `notifications`, `document_expirations`, `qaqc_inspections`, `po_requests`, `payroll_variance_batches`, `fleet_defects`, `fleet_status`, `haul_cycles`, `asset_mappings`, `asset_transfers`, `dispatch_state_events`, `dispatch_continuity_events`, `dispatch_driver_sessions`, `dispatch_users`, `signatures`, `audit_events`, `admin_audit_log`, `corrective_actions`, `safety_documents`, `safety_equipment_issuances`, `safety_equipment_trainings`, `safety_training_records`, `field_memory_notes`, `command_center_calendar`, `command_center_thresholds`, …).

### 2.3 · Integrations (existing in code)

| Integration | Env keys present | Code | Live? | Classification |
|---|---|---|---|---|
| **Resend (email)** | `RESEND_API_KEY`, `SENDER_EMAIL`, `REPLY_TO_EMAIL`, `RESEND_WEBHOOK_SECRET` | `routes/resend_webhook.py`, branded portal emails | YES | **Production Ready** |
| **Twilio (SMS)** | (referenced in env, magic-link SMS active) | `routes/dispatch_portal_auth.py` (magic-link SMS) | YES | **Production Ready** |
| **Cloudflare R2 (storage)** | `BACKUP_R2_HOURLY=true` | `services/r2*` (backup attempts), `routes/operational_attachments.py` (uploads) | Partial | **Partially Complete** — backups attempt; primary storage TBC |
| **Sentry** | `SENTRY_DSN` | `sentry_init.py`, `sentry_tags.py` | YES | **Production Ready** |
| **Motive** | env keys ready; integration is read-design | 5 dedicated route files; `services/motive_service.py` | webhook plumbing yes; broad activation NO | **Plumbing Ready / Activation pending** |
| **MaintainX** | `MAINTAINX_API_KEY` (UNSET); flags `MAINTAINX_SYNC_ENABLED=false`, `MAINTAINX_WRITE_ENABLED=false` | `services/maintainx_*.py`; `AdminIntegrationCenter` UI shows "Read-First" tab | NO (no key) | **Scaffolded / Activation pending** |
| **FleetWatcher** | (none) | (none) | NO | **Not Started** |
| **Atlas (Mongo)** | `MONGO_URL`, `DB_NAME`, `ATLAS_QUOTA_MB` | live | YES | **Production Ready** (governance separation noted as operator action) |
| **Accounting** | (none) | (none) | NO | **Not Started** |

### 2.4 · Existing automations / scheduled jobs

* **Scheduler** is enabled (`SCHEDULER_ENABLED`). Backup, digest, scheduler-runs admin endpoints all live.
* **Notifications digests** run per portal (admin / safety / hr / pm / dispatch / fl).
* **Backups** run hourly to R2 when configured; `BACKUP_HOURS_UTC` controls daily backup.
* **Health monitor** — `health_monitor.py`, `backup_verification.py`, `outage_alerts.py`.
* **PO digest, safety digest, operator digest, scheduler-runs admin** — all present.
* **Drift / governance jobs** — multiple `governance*` route files, `production_health`, `persistence_health`, `stability`.

### 2.5 · Existing dashboards/reports (counts)

* **Admin Command Center** (`/admin/command-center/snapshot`) — exists, has thresholds + calendar.
* **Admin Operations Dashboard** — exists.
* **Operations Center read endpoint** — `/api/operations-center` — exists.
* **Operations Intelligence** — `/api/operations/intelligence`, `/api/operations/intelligence/shop`, `/api/operations/intelligence/fleet-gps`, `/api/operations/expirations/summary` — exists.
* **Daily Reports dashboard** — exists.
* **Equipment dashboard** — exists.
* **Project Health** — exists.
* **PM PnL page** — exists.

### 2.6 · Duplicates / overlap surfaced by inventory

| Cluster | Overlap | Recommendation |
|---|---|---|
| `equipment` + `equipment_master` + `field_leadership_equipment_catalog` + `trench_safety_assets` | Asset truth fragmented across 4 collections | **Source-of-truth contract — see §14** |
| `dispatch_state_events` + `dispatch_continuity_events` + `dispatch_assignments.state_history[]` | Three places track dispatch lifecycle | **dispatch_assignments.state_history is canonical** per `DISPATCH_LIFECYCLE_ARCHITECTURE.md` doctrine; the events tables are derived/append-only audit. Keep all three; document the contract. |
| `incidents` collection + `safety_forms` + `incident_lifecycle` route | Three surfaces touching incidents | `incidents` is canonical; lifecycle drives transitions; safety_forms is the upload surface |
| `notifications` (in `routes/notifications.py`, `routes/tasks_notifications.py`) + per-portal digest endpoints | Two-tier — per-user notifications + per-portal digests | **Keep as-is**; the per-portal digest aggregates user-level notifications for ops handoff |
| `admin_audit_log` + `audit_events` + `operational_events` + `dispatch_continuity_events` | Audit trails everywhere | All distinct purposes (admin actions vs operational truth vs dispatch operational moments). No dedupe required. |

---

## §3 · PHASE 2 · USER ROLE × INFORMATION / ACTION / DECISION MATRIX

| Role | Information they need | Actions they perform | Decisions | Communications | Reports consumed | Reports created |
|---|---|---|---|---|---|---|
| **Driver** | Today's assignment · ticket photo target · destination · current load count · DVIR result · breakdown reporting path · time-off request status | Tap to advance dispatch state · photograph tickets · submit DVIR · report breakdown · log fuel · log hours | When to escalate (breakdown / safety) | Dispatch (SMS/in-app), Safety (incident), Shop (DVIR fail) | Today's dispatch only — minimal screens | DVIR, incident, dispatch state transitions, ticket photos |
| **Dispatcher** | Live haul board · driver availability · truck availability · shop OOS list · current geofence reality (Motive) · ticket arrivals · PM pull-requests | Create / reassign / cancel / revise assignments · send magic-link · escalate to Shop · escalate to Safety · acknowledge driver state transitions | Routing · prioritization · OOS handling · over-the-road problems | Driver (SMS), Shop, PM, Safety, Operations | Operations Center, Dispatch board, Driver Qualification | Assignments, continuity events, revisions |
| **Fleet Manager** | Fleet utilization · OOS list · maintenance backlog · DVIR failures · fuel · cycle times · downtime cost | Same as Dispatcher + capacity planning · maintenance scheduling | Asset purchase / retire · vendor selection · maintenance priorities | Shop, Dispatch, PM, Accounting | Equipment dashboard, asset profile, utilization | Equipment master changes, OOS decisions |
| **Shop Manager** | DVIR failures · open work orders · parts inventory · technician load · preventive maintenance schedule · equipment readiness | Acknowledge defects · assign mechanics · close work orders · order parts · approve OOS | What to defer vs immediate · parts ordering · technician routing | Dispatch (readiness), Drivers (DVIR clarification), Safety (severity) | Equipment dashboard, Shop fleet defects | Work orders, repair records, readiness signal |
| **Mechanic** | Today's work orders · parts available · defect detail · severity · safety stop-work conditions | Diagnose · repair · close work order · request parts · escalate severity | Repair priority · parts substitution | Shop Manager · Driver (clarification) | Work orders | Repair completion notes |
| **Lead Driver** | Crew dispatch · cross-truck issues · escalation path · OOS coverage | Coverage decisions · driver mentoring · escalate to Dispatch | Coverage · OT requests | Dispatch · drivers · safety | Crew board · driver qualification | Coaching notes |
| **Superintendent** | Project schedule · daily production · crew presence · equipment on-site · materials delivered today · safety conditions · weather constraint | Approve daily reports · escalate safety · authorize crew changes · approve material delivery | Site go/no-go · crew composition · safety stop-work | Foreman, PM, Safety, Dispatch | Daily reports, project health, safety records, equipment | Daily reports, JHA acknowledgements, meetings |
| **Foreman** | Today's crew · today's equipment · today's materials · weather · JHA briefing | Run morning meeting · submit daily report · take incident · request materials · log production | Crew assignments at task level · stop-work | Superintendent, PM, Safety, Dispatch | Daily reports, JHA, training records | Daily reports, JHA acks, incidents, photos |
| **Project Engineer / PM** | All equipment assigned to my projects · all trucks · all materials · production rates · daily reports · QA/QC inspections · costs · PnL | Approve daily reports, sign QA/QC, request equipment, approve PO requests, escalate safety | Equipment moves between projects · approval gates | Foreman, Super, Operations, Accounting, Safety | PM PnL, project health, equipment utilization, material movement, daily reports, QA/QC | PO requests, project notes, approvals |
| **Safety Manager** | All incidents (live) · near-misses · JHA acks · training expirations · driver violations · DVIR failures · camera events · compliance status | Investigate incidents · close corrective actions · schedule training · audit JHAs | Lockout/stop-work · escalation to legal/HR · training cadence | All portals | Safety hub, incidents, training, fire-ext, fleet defects | Corrective actions, incident closures, safety meetings |
| **HR** | Employees (full directory) · drivers (qualification expirations) · time-off · payroll variance · training records · accountability events · field-leadership records | Onboard / terminate · approve time-off · resolve payroll variance · drive qualification compliance | Eligibility, discipline, termination, classification | All portals | HR hub, employee accountability, payroll variance, training | Lifecycle events, terminations, drivers' qualification status |
| **Accounting** | PO requests · cost-center allocations · payroll variance · vendor invoices · asset depreciation · project PnL | Approve POs · close payroll batches · audit costs | Approval thresholds, vendor selection, capitalization | PM, Operations, Executive | PO requests, PnL, payroll variance | PO decisions, payroll batch closures |
| **Executive Management** | One-page operational picture: live jobs, live production, live fleet, live risks, today's profitability, today's compliance | Cross-portal navigation; rarely original actions; mostly **observation** | Strategic only | None operational; consume from Operations Center | Operations Center, Project PnL, Executive Accountability | None original |
| **Operations Leadership** | All of the above, live — the single board (§11) | Coordinate across PM/Safety/Dispatch/Shop · break ties | Anything cross-portal | Every other role | Operations Center (the directive's single source of truth) | Operations Actions, command decisions |
| **System Administrator** | Platform health · users · sessions · errors · audit log · backup · scheduler runs · API health · integration sync state | Everything (god-mode) · platform recovery · password resets · MFA management · governance | Anything · final tie-break | Every role | All admin dashboards | Audit log, governance findings, deploy records |

---

## §4 · PHASE 3 · DISPATCH AUDIT

### 4.1 · Current capabilities (verified by route inventory)

* **Create / assign / transition / cancel / reassign / acknowledge** assignments (`routes/dispatch_lifecycle.py`).
* **Driver-side magic-link, session exchange, board, my-assignment** (`routes/dispatch_driver.py`).
* **Exports** — assignments.csv, state-events.csv, haul-cycles.csv (`routes/dispatch_exports.py`).
* **Continuity events** — operational moments per assignment (`routes/dispatch_continuity.py`).
* **Governance findings** — read-time governance over the lifecycle (`routes/dispatch_governance.py`).
* **Day-1 / Week-1 debrief** — onboarding intelligence (`routes/dispatch_day1_debrief.py`).
* **SMS magic-link + Twilio status callback** — live.
* **Recovery dashboard** — `routes/recovery_dashboard.py`.
* **5-second silent polling on DispatchBoard** — `DispatchBoard.jsx` line 36.

### 4.2 · Missing / partial

| Capability | Status | Recommendation |
|---|---|---|
| **Live GPS overlay on the haul board** | ⚪ Not yet wired — Motive plumbing exists, surface not built per `validate-don't-surveil` doctrine | Build the *gentle hint* surface (Motive arrival hints) — never a real-time map |
| **PM-visible haul activity tile** | 🟡 `PmHaulActivityTile.jsx` exists but PM portal doesn't yet hub it | Wire it into PmHub |
| **Single Dispatch Command Center** | 🟡 Building blocks present (`DispatchHub`, `DispatchBoard`, `AdminDispatch`, `AdminCommandCenter`) but not converged | **Phase-1 P0 build** below |
| **Material Movement integration with Dispatch** | ⚪ Skeleton route only | Wire material lifecycle into haul assignment after MaintainX activation |
| **Shop OOS list ↔ Dispatch readiness** | 🟡 `/api/shop/fleet/defects`, `/api/dispatch/fleet/defects/{id}/clear` both exist; Dispatch UI doesn't yet pre-emptively block OOS assignments | Wire OOS list into AssignmentCreateDrawer |

### 4.3 · Broken / duplicated workflows

* Driver communication is split between SMS magic-link and (planned) in-app messaging. **Decision required (§13):** SMS is the single canonical channel for now. In-app messaging is **DO NOT BUILD** until Motive activation is final.
* `dispatch_assignments`, `dispatch_state_events`, `dispatch_continuity_events` are not duplicates — they serve distinct doctrine layers (canonical truth, audit, operational moment) per `DISPATCH_LIFECYCLE_ARCHITECTURE.md`. No deduplication needed.

---

## §5 · PHASE 4 · DRIVER WORKFLOW AUDIT (touchpoint-by-touchpoint)

| Touchpoint | Current implementation | Recommend automate? | Recommend manual? |
|---|---|---|---|
| **Driver start-of-shift** | `ShiftStart.jsx`, magic-link landing | manual (auto-prefill from Motive ignition when activated) | tap-to-start remains the audit-anchor |
| **Dispatch receipt** | SMS magic-link → DispatchDriverProfile board | manual (one-tap acknowledge) | — |
| **Driver comms** | SMS only today (Twilio). In-app removed from scope. | SMS for everything urgent | in-app for assignment detail (read-only) |
| **GPS** | Not surveilling. Motive ignition-off → suggest OFF_SHIFT. | suggestion only | driver still taps |
| **DVIR** | `routes/fleet_ops.py /api/fleet/inspections`, `NewFleetDVIR.jsx`, `FleetDVIRConfirmation.jsx` | automate severity gating; auto-block OOS assignments | manual defect description |
| **Safety forms (incidents, near-miss)** | `NewIncident.jsx` + `routes/incident_lifecycle.py` | automatic notify Safety; auto-route to Super | manual narrative |
| **Equipment checks** | `NewEquipmentInspection.jsx` + `equipment_inspections` collection | automate cadence reminders | manual visual checks |
| **End of shift** | Inferred from final state transition; Day-1/Week-1 debrief surfaces ask questions | automate the end-of-shift summary; pre-fill cycles from Motive | confirm by tap |
| **Load tracking** | `dispatch_assignments.state_history` + `haul_cycles` collection | automate cycle-time calc from state transitions | tap each state |
| **Material tracking** | Material is a free-list on the assignment today | **Phase-2 P1 build** (material catalog + ticket-OCR future) | manual material selection |
| **Incident reporting** | `NewIncident.jsx` end-to-end | semi-auto routing | always manual narrative |
| **Fuel reporting** | not yet a primary surface; Motive provides fuel when activated | automate from Motive when active | manual entry when not |
| **Breakdown reporting** | `routes/dispatch_driver.py /driver/breakdown-proof/upload` | automate Shop alert | photo + manual reason |
| **Time tracking** | `routes/payroll_variance*.py` + `HrTimeVerification.jsx` | automate variance detection | manual reconciliation |
| **Location tracking** | Motive (when activated) only — never surveillance | automate geofence arrival hint | driver taps |
| **Production tracking** | `daily_reports.production[]` + FleetWatcher (planned) | automate from FleetWatcher | foreman validates |

**Doctrine:** Per `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md` Rule 6 ("Minimize Human Decisions"), automate routing/notification/cadence. Keep tap-to-confirm for every state transition (audit-anchor doctrine).

---

## §6 · PHASE 5 · MOTIVE INTEGRATION AUDIT

Verified against `services/motive_service.py`, 5 route files (`operations.py`, `dispatch_lifecycle.py`, `operations_center.py`, `admin_ops.py`, `integration_health.py`) and the canonical `MOTIVE_INTEGRATION_STRATEGY.md`.

| Motive capability | ForgedOps consumption status | Recommendation |
|---|---|---|
| Real-time GPS per truck | **Should Connect** — geofence arrival only, never a surveillance map | Build the gentle-hint surface |
| Ignition on/off | **Partially Connected** — events stored in `motive_events`; OFF_SHIFT suggestion designed not yet surfaced | Surface in DispatchBoard as a hint chip |
| Hours-of-Service | **Do Not Connect** to driver UI (FMCSA boundary) | Admin observability only |
| Geofence entry/exit | **Should Connect** — `motive_geofences` collection exists, geofence-reconciliation admin page exists | Wire into dispatch validation banner |
| Diagnostic codes | **Should Connect** — feed Shop OOS pipeline | Wire into `fleet_defects` via webhook |
| Idle time | **Already Connected** at data layer; **Do Not Surface** to drivers | Aggregate at admin level only |
| Camera events | **Already Connected** for Safety; **Do Not Surface** to drivers | Safety hub only |
| Maintenance signals | **Should Connect** — pair with MaintainX | Reconcile in Asset spine (§14) |
| Driver scoring / leaderboards | **Do Not Connect** | Explicit refusal in doctrine |

**Verdict:** Motive integration architecture is complete and correct. Activation is gated by an explicit operator decision (per the strategy document). No further architecture work needed.

---

## §7 · PHASE 6 · FLEETWATCHER INTEGRATION AUDIT (planned)

Status: **NOT STARTED** in code. No env vars. No routes. No services. Listed only in roadmap documents.

### 7.1 · Available data (vendor-claimed, to verify at activation)

* Truck cycle times · loads · tonnage · ticket numbers
* Asphalt plant data · paving rates · milling rates · production metrics
* Per-haul tonnage · per-project total

### 7.2 · Mapping to consumers (recommended)

| FleetWatcher data | Dispatch | PM | Operations | Accounting | Executive |
|---|---|---|---|---|---|
| Per-haul tonnage | ticket validation | production rate | live production | $/ton actual | KPI |
| Truck cycle time | revise routing | crew efficiency | utilization | $/cycle | KPI |
| Plant production | — | material availability | input rate | $/ton produced | KPI |
| Paving production | — | crew productivity | install rate | $/ton paved | KPI |
| Milling production | — | crew productivity | mill rate | $/ton milled | KPI |

**Recommendation:** When FleetWatcher activates, treat it as a **read-only validator** of `daily_reports.production[]` AND a primary feed for the PM Materials and Production dashboards (§9). Plumb through `integration_health` and `operations_intelligence`. Mirror the Motive doctrine: validate, don't replace.

---

## §8 · PHASE 7 · SHOP AUDIT

### 8.1 · Existing

* `routes/fleet_ops.py` — `/api/shop/fleet/defects`, `/api/shop/fleet/defects/{id}/acknowledge`, `/api/shop/fleet/defects/{id}/repair`, `/api/shop/fleet/by-unit`.
* `routes/shop_parts.py`, `routes/shop_portal_deps.py`.
* `pages/ShopHub.jsx`, `ShopTrenchSafetyRepairs.jsx`.
* `equipment` + `equipment_master` + `equipment_inspections` + `equipment_parts` + `fleet_defects` + `fleet_status` collections.
* `AdminEquipment.jsx` (admin), `AdminOperationalInventory.jsx`.

### 8.2 · Missing for the directive's full Shop board

* Single **Shop Command Board** that surfaces: Open WO · Today's PM schedule · DVIR queue · Parts low-stock · Mechanic load · OOS list · Readiness signal.
* Preventive-maintenance scheduler (cadence detection from `equipment.last_pm_at` + hours).
* Parts inventory write surface (parts catalog is read-mostly today).
* Mechanic assignment workflow.

### 8.3 · Dispatch ↔ Shop coupling (canonical contract)

```
Driver DVIR fail (severity ≥ MAJOR)
   → /api/fleet/inspections
   → fleet_defects row
   → Shop dashboard surfaces it
   → Shop acknowledges (/api/shop/fleet/defects/{id}/acknowledge)
   → Repair (/api/shop/fleet/defects/{id}/repair)
   → Dispatch can clear (/api/dispatch/fleet/defects/{id}/clear)
   → equipment_master.is_oos flips back to false
   → Dispatcher can assign the truck again
```

This contract already exists and is the right design. **The build need is UI convergence, not new routes.**

---

## §9 · PHASE 8 · PM PORTAL AUDIT (CRITICAL per directive)

### 9.1 · What PMs need vs what exists today

| PM need | What exists | Gap | Build priority |
|---|---|---|---|
| **Equipment** — Assigned · Available · Locations · Utilization · Downtime · Hours · Costs | `equipment` collection + `AdminLeadershipEquipment.jsx`, `EquipmentDashboard.jsx`. PM-side view absent. | PM portal does NOT yet show per-project equipment + utilization + cost rollup | **P1** |
| **Trucks** — Assigned · Locations · Utilization · Cycle · Downtime · Status · Costs | `dispatch_assignments` + `motive_events`. PM cannot today see "all trucks on my projects today". | Wire `PmHaulActivityTile.jsx` into PmHub + add cost roll | **P1** |
| **Materials** — Ordered · Dispatched · In Transit · Delivered · Installed · Remaining · Rejected · Returned | `routes/material_movement.py` is a skeleton; no UI in PM portal. | Build PM materials surface after FleetWatcher activation feeds it | **P2** |
| **Production** — Loads / Tons hauled / Tons delivered / Tons installed / Daily / Weekly / Monthly | `daily_reports.production[]`. PM has report list but no production rollup. | Add PM production dashboard sourced from `daily_reports` (FleetWatcher later) | **P1** |
| **Financial** — Equipment cost · Truck cost · Material cost · Production cost · Hauling cost · Unit cost | `ProjectPnlPage.jsx` exists. Cost feeds incomplete. | Wire cost feeds after Accounting integration design | **P3** |

### 9.2 · Recommended PM dashboard (one screen)

```
[Project picker: 25-21 SJR2C ▾]
┌──────────────────┬──────────────────┬──────────────────┐
│ TODAY            │ THIS WEEK        │ MONTH            │
│ Crew: 14 on site │ Loads: 312       │ Production: 89%  │
│ Equip: 7 active  │ Tons: 4,180      │ Cost: $312K      │
│ Material: 280 T  │ Cycles avg: 42m  │ vs Bid: -2.3%    │
└──────────────────┴──────────────────┴──────────────────┘
┌─ TRUCKS & HAULS (today) ───────────────────────────────┐
│ T-42 · Carlos · 8 cycles · 96 tons · ACTIVE             │
│ T-15 · Marco  · 3 cycles · 36 tons · WAITING_LOAD       │
│ … (PmHaulActivityTile rows)                             │
└────────────────────────────────────────────────────────┘
┌─ EQUIPMENT (assigned to this project) ─────────────────┐
│ Cat 320 · CAT-320-A · 4.5 hr today · 12% idle           │
│ Cat 950 · CAT-950-B · 6.2 hr today · OOS pending parts  │
└────────────────────────────────────────────────────────┘
┌─ MATERIALS (this project) ─────────────────────────────┐
│ Ordered  : 600 T │ Delivered: 280 T │ Installed: 240 T │
│ Remaining: 360 T │ In transit: 36 T │ Rejected: 0 T   │
└────────────────────────────────────────────────────────┘
┌─ SAFETY & QA/QC (this project, this week) ─────────────┐
│ Incidents: 0 │ Near-miss: 1 │ JHA acks: 14/14 │ QAQC pending: 2 │
└────────────────────────────────────────────────────────┘
```

Every row already has a backend feed. The build is **a single dashboard view, not new collections**.

---

## §10 · PHASE 9 · SAFETY AUDIT

Already deeply built. Confirmed by Safety route inventory (`safety.py`, `safety_exports.py`, `safety_forms.py`, `safety_topic_library.py`, `incident_lifecycle.py`, `jha_acknowledgements.py`, `qaqc.py`, `qaqc_lifecycle.py`, `site_inspection_lifecycle.py`).

Recommend **no new safety architecture**; only Motive-camera-event ingestion when Motive activates (Phase 5), which already has its plumbing.

---

## §11 · PHASE 10 · OPERATIONS CENTER AUDIT

Today: `routes/operations_center.py` exposes `/api/operations-center` (single read), plus `operations_intelligence.py` (fleet-gps, expirations summary, shop intel), plus `command_center.py` (admin snapshot, thresholds, calendar).

**Gap:** the directive's vision is a single live-board fusing Live fleet · Live jobs · Live production · Live hauling · Live equipment · Live materials · Live dispatches · Live incidents · Live maintenance · Live labor · Live costs · Live profitability · Live risks. Today, those 13 facets are spread across 7+ pages.

### 11.1 · Operations Center recommended architecture (single page)

```
┌────────────────── OPERATIONS CENTER (LIVE) ─────────────────────┐
│ FLEET STATUS │ JOBS LIVE │ PRODUCTION │ HAULING │ MATERIALS    │
│ 47 trucks    │ 8 active  │ 4,180 T    │ 312 cyc │ 84% on-plan  │
│ 5 OOS · 2 PM │ 0 stopped │ +2% target │ 41m avg │ 0 rejected   │
├──────────────┴───────────┴────────────┴─────────┴──────────────┤
│ INCIDENTS / SAFETY    │ MAINTENANCE QUEUE │ LABOR & COST       │
│ 0 today · 1 open NMS  │ 12 WO · 3 critical│ Crew: 142 · OT: 6  │
│ 14 JHA acks today     │ 4 PM scheduled    │ Cost run: $89K     │
├──────────────────────────────────────────────────────────────────┤
│ DISPATCH HOTLIST (live)                                          │
│   T-42 ⚠ waiting load 28m  · T-15 ⚠ no driver yet · 25-21 short  │
├──────────────────────────────────────────────────────────────────┤
│ RISKS                                                            │
│   • 3 driver quals expire this week                              │
│   • 2 trucks PM overdue                                          │
│   • Project 25-31 trending +3% over bid                          │
└──────────────────────────────────────────────────────────────────┘
```

Every tile aggregates existing endpoints. Build = composition, not new routes.

---

## §12 · PHASE 11 · ADMIN AUDIT

Already extensive (38 admin pages). Verified Admin can already see Users, Jobs, Equipment, Trucks, Dispatch, Forms, Incidents, Integrations (`AdminIntegrationCenter`), Syncs (`AdminMasterHistory`), Errors (Sentry + recovery dashboard), Audit Logs (`AdminAuditLog`), Alerts (`/integrations/alerts`), Automation status (`AdminSchedulerRuns`), API health (`/api/version`, `/api/health`, `integration_health` route), Platform health (`SystemHealth.jsx`, `production_health` route).

**Verdict:** Admin coverage is essentially complete. The only gap is the **single Admin Command Center** — `AdminCommandCenter.jsx` exists but is not yet the top-level admin landing. Convergence required, not new architecture.

---

## §13 · PHASE 12 · COMMUNICATIONS AUDIT

| Path | Today | Recommendation |
|---|---|---|
| Driver ↔ Dispatch | SMS magic-link + Twilio status callback | Keep SMS as canonical; add in-app read-only assignment detail |
| Driver ↔ Shop | Indirect via DVIR + fleet_defects | Add gentle in-app "your DVIR was acknowledged" notification |
| Driver ↔ Safety | Indirect via incidents | Keep — Safety must read, not message |
| Dispatcher ↔ PM | Indirect via PmHaulActivityTile (when wired) | Wire it |
| Dispatcher ↔ Operations | Indirect via Operations Center | Wire it |
| Shop ↔ Dispatch | Fleet defects API contract | Already correct |
| Shop ↔ PM | None today | Add per-project equipment readiness rollup |
| Safety ↔ Operations | Notifications digest | Already correct |
| PM ↔ Operations | Operations Center read | Add PM-specific drill-down |
| Executive ↔ Operations | Operations Center only | Already correct |

**Doctrine (Rule 2 from Constitution):** Most cross-portal updates are **informational notifications**, not tasks. Tasks only when an action is owed. Per `FORGEDOPS_OPERATIONAL_DESIGN_CONSTITUTION.md`:

* Automated: routing, ownership, escalation timing, due dates, status progression.
* Manual: corrective actions, approvals, operational judgments.

---

## §14 · PHASE 13 · MASTER ASSET GOVERNANCE (the key deliverable)

### 14.1 · The drift problem (verified)

Asset truth is currently fragmented across at least four collections:

| Collection | Purpose | Authoritative? |
|---|---|---|
| `equipment` | Generic equipment list (free-form, legacy) | partial |
| `equipment_master` | Canonical fleet roster (active assets) | claims authority |
| `field_leadership_equipment_catalog` | Field-Leadership-specific equipment catalog | scoped |
| `trench_safety_assets` | Trench-safety-specific assets (e.g. TB-01..TB-07) | scoped |

Plus external sources of truth (or near-truth):

* `motive_events` (Motive's view of trucks/drivers/assets)
* `asset_mappings` + `asset_mapping_proposals` (ForgedOps ↔ Motive reconciliation queue)
* `asset_transfers` (operational asset moves)
* MaintainX (scaffolded; no live data)
* FleetWatcher (not started)
* Reality (the truck physically sitting in the yard)

### 14.2 · Required answers (per directive)

| Question | Recommended answer |
|---|---|
| Who can **create** assets? | Admin (canonical) · Shop Manager (PM equipment with audit) · Dispatcher (NEVER) |
| Who can **edit**? | Admin · Shop Manager (with audit) · Fleet Manager (when role exists) |
| Who can **deactivate**? | Admin only |
| Who can **archive**? | Admin only |
| Who **approved** changes? | Captured via `admin_audit_log` and per-collection `updated_by` |
| Last modified / when / what? | Already supported via `updated_at`, `updated_by`, `metadata_backfilled_*`, plus the **AdminAssetMapping** + **AdminMasterHistory** pages |
| Audit history? | Yes — `master_history`, `admin_audit_log`, `audit_events`. Architecture says **make it visible per asset in `AssetProfile.jsx`** |

### 14.3 · Source-of-truth recommendation: **OPTION C — HYBRID** (canonical)

| Asset class | Canonical source | Why |
|---|---|---|
| **Trucks · semi-trucks · trailers** (GPS-bearing assets) | ForgedOps **`equipment_master`** is canonical; Motive is the GPS validator | Operator-controlled identity; Motive cannot create or retire assets |
| **Generic heavy equipment** (excavators, dozers, loaders) | ForgedOps **`equipment_master`** | Same rationale; some carry Motive GPS, some don't |
| **Attachments** (buckets, breakers, sweepers) | ForgedOps **`equipment_master`** (parent: equipment) | Operator-controlled |
| **Shop assets** (tools, jacks, stands) | ForgedOps `equipment` (lighter schema) | Lower governance burden |
| **Portable assets** (cones, plates, fans) | ForgedOps `equipment` | Same |
| **Trench safety assets** (boxes, shields, plates) | `trench_safety_assets` (already canonical for this domain) | Domain-specific |
| **GPS sensors / ELDs** | Motive is the source of GPS device identity | Vendor product |
| **MaintainX work orders** | MaintainX when activated | Vendor product, ForgedOps mirrors |
| **FleetWatcher production assets** | FleetWatcher when activated | Vendor product |

**Master rule:** Everything that an operator *can hold in their hand and decide to keep, sell, or retire* is **ForgedOps-canonical**. Everything that is a *vendor-managed signal* (GPS sensors, work orders, production tickets) is *vendor-canonical with ForgedOps mirror*.

### 14.4 · Sync strategy

```
ForgedOps (canonical asset spine)
       │
       ├─→ Motive  : push asset+driver identity; pull GPS, geofence, ignition, DTCs
       │            via `services/motive_service.py` ; reconciliation queue in
       │            asset_mapping_proposals; Admin approval surface already exists
       │            (AdminAssetMapping.jsx, AdminGeofenceReconciliation.jsx)
       │
       ├─→ MaintainX: push asset identity for read-first phase; pull WOs/PM
       │            when MAINTAINX_SYNC_ENABLED=true; mirror to fleet_defects /
       │            equipment_parts (services/maintainx_asset_sync.py ready)
       │
       ├─→ FleetWatcher: push truck identity once activated; pull haul cycles +
       │            tonnage + ticket; mirror to haul_cycles + daily_reports
       │
       └─→ Accounting (future): push asset identity for capitalization; pull
                    actual cost feeds
```

### 14.5 · New asset onboarding workflow (canonical contract)

```
Purchase decision (Operator/Accounting)
   │
   ▼
Asset arrives in yard
   │
   ▼
Admin creates equipment_master row
   (admin/AdminEquipment.jsx · already supports this)
   │
   ▼ within 24 h
GPS install — Motive provisioning
   │
   ▼ webhook
asset_mapping_proposals row created
   │
   ▼
Admin approves mapping (AdminAssetMapping.jsx · already supports this)
   │
   ▼ now visible to:
       ├─ Dispatch (in AssignmentCreateDrawer truck picker)
       ├─ Shop (in fleet defects scope)
       ├─ PM (per project assignment)
       ├─ Safety (in violation scope)
       └─ Drivers (assignable)
```

### 14.6 · Asset retirement workflow

```
Decision (Operator)
   │
   ▼
Admin sets equipment_master.active = false (with audit_log row)
   │
   ▼ propagates by query filter:
       - Dispatcher no longer sees in pickers (filter: active=true)
       - PM rollup drops the asset
       - Motive mapping remains for historical lookup
       - asset_transfers row created with type=RETIRE
```

### 14.7 · Reconciliation workflow (existing — confirm it's the right shape)

`routes/asset_mapping_recon.py` already provides:

* `/api/admin/asset-mapping/scan`
* `/api/admin/asset-mapping/queue`
* `/api/admin/asset-mapping/{id}/approve` · `/reject` · `/reassign`
* `/api/admin/asset-mapping/bulk-approve`
* `/api/admin/asset-mapping/coverage` · `/audit` · `/top-unmapped`
* `/api/admin/asset-mapping/impact-preview/{id}`
* `/api/admin/asset-mapping/operational-impact`
* `/api/admin/asset-mapping/executive-summary`

**This is already the elite reconciliation surface.** Recommendation: **no new architecture; UI polish + drill-down from AssetProfile** is the only build.

### 14.8 · Missing / duplicate / orphaned detection (gaps)

| Detection | Today | Recommendation |
|---|---|---|
| Missing assets (in Motive, not in ForgedOps) | `asset_mapping_proposals` already surfaces this | Promote to a recurring Admin notification |
| Duplicate assets | `master_history` + `asset_mapping_recon` cover this read-side | Add a nightly job that emits a digest |
| Retired assets that still report telemetry | None today | New: nightly check — if `equipment_master.active=false` AND `motive_events` arriving < 72 h ago → alert |
| Orphaned assets | None today | New: nightly check — `equipment_master` row with no motive_event in 30 days AND last_seen_in_yard < 30 days → flag |
| Unsynced assets | `asset_mapping_recon.coverage` already gives the % | Pin coverage to the Operations Center |
| Conflicting assets | `project_identity_conflicts` collection exists | Surface in AdminProjectIdentityGovernance (already a page) |

### 14.9 · Required dashboards

| Dashboard | Status | Location |
|---|---|---|
| Asset health (per-asset detail) | `AssetProfile.jsx` exists | already built — wire from PM portal too |
| Asset synchronization (coverage %) | `AdminAssetMapping.jsx` exists | promote tile into Operations Center (§11) |

### 14.10 · Pillar scorecard for Phase 13

| Pillar | How the Hybrid model satisfies it |
|---|---|
| **Powerful** | Single canonical spine ; every downstream system reads from it ; reconciliation closes the loop |
| **Simple** | Operator's mental model is "ForgedOps owns assets ; vendors validate" — one rule |
| **Beautiful** | One AssetProfile screen per asset ; one mapping queue ; one coverage tile |
| **Trusted** | Audit-logged ; immutable history ; explicit operator approval for every mapping decision |
| **Proven** | Reconciliation routes exist and have been operated against the live Motive integration |

---

## §15 · FINAL ARCHITECTURE · THE 13 REQUIRED MAPS

### Map 1 · Current State Architecture
13 portals (Public, Admin, Dispatch, Driver, Shop, PM, HR, Safety, Field-Leadership, Operations, Trench-Safety, Job-Photos, Document-Expirations) on **107 backend routes / 39+ collections / 154 frontend pages**. Asset spine fragmented. Operations Center is read-endpoint, not yet a board. Communications largely SMS + portal-scoped digests.

### Map 2 · Future State Architecture
* **One Asset Spine** (Hybrid · §14) feeding Motive · MaintainX · FleetWatcher.
* **One Operations Center board** (§11) as Operations Leadership single-source-of-truth.
* **One PM Dashboard** (§9) per project, sourced from existing endpoints.
* **One Dispatch Command Center** combining `DispatchHub` + `DispatchBoard` + `AdminDispatch`.
* **One Shop Command Board** unifying fleet defects · WO queue · PM schedule · parts · readiness.
* SMS remains canonical driver comms. In-app stays read-only for assignment detail.
* Motive activation is a deliberate operator decision (architecture is ready).
* MaintainX activation is a deliberate operator decision once an API key is provisioned.
* FleetWatcher activation is post-MaintainX.

### Map 3 · System Dependency Map
```
FRONTEND
  └─ axios → REACT_APP_BACKEND_URL → /api/*
BACKEND
  ├─ MongoDB (Atlas)
  ├─ Resend (email)
  ├─ Twilio (SMS)
  ├─ Cloudflare R2 (backups, future primary storage)
  ├─ Sentry (errors)
  ├─ Motive (telemetry / webhooks · gated)
  ├─ MaintainX (work orders · scaffolded)
  └─ FleetWatcher (production · planned)
SCHEDULER
  ├─ Backup hourly to R2
  ├─ Digests per portal
  ├─ Health monitor
  └─ Drift / governance jobs
```

### Map 4 · Integration Dependency Map
See §14.4 — ForgedOps canonical → vendor satellites; reconciliation queue is the only operator surface that crosses the boundary.

### Map 5 · User Workflow Map
For each role, see §3. The canonical workflow is **driver-tap → state transition → operational memory → downstream visibility (Dispatch / Shop / PM / Operations) → Motive validates on read**.

### Map 6 · Data Flow Map
```
Field Action → Frontend (axios) → /api/* (FastAPI) → Mongo collection
                                                  → operational_events (audit)
                                                  → admin_audit_log (admin actions)
                                                  → tasks/notifications (cross-portal)
                                                  → Motive (when activated)
                                                  → MaintainX (when activated)
                                                  → FleetWatcher (when activated)
                                                  → Resend / Twilio (notifications)
```

### Map 7 · Communication Flow Map
See §13. SMS for urgent driver paths; per-portal digest for ops handoffs; in-app notifications for informational events.

### Map 8 · Dispatch Command Center Architecture
* **Hub tier**: `DispatchHub` for the operator landing; `OperationalMomentsRail` surfaces escalations.
* **Board tier**: `DispatchBoard` (5-second silent poll) is the live truth.
* **Drawer tier**: `AssignmentDrawer` / `AssignmentCreateDrawer` for action.
* **Admin tier**: `AdminDispatch` for governance + bulk operations.
* **Cross-portal feeds**: `PmHaulActivityTile`, Shop OOS list, Motive validation chip.
* **One new page is needed only at the operator's discretion**: a fused "Dispatch Command Center" that combines the above into one screen. Building blocks all exist — composition only.

### Map 9 · PM Portal Architecture
See §9.2 wireframe. Composition, not new collections.

### Map 10 · Shop Portal Architecture
* **Today's Open Defects** (from `fleet_defects` + Motive DTCs)
* **WO Queue** (when MaintainX activates, mirrored locally)
* **PM Schedule** (cadence detection from `equipment_master.last_pm_at` + hours)
* **Parts Low-Stock** (from `equipment_parts`)
* **Mechanic Load** (from `tasks` filtered by assignee role)
* **Readiness Signal** (per truck — exposed to Dispatch via existing `/api/dispatch/fleet/status`)

### Map 11 · Operations Center Architecture
See §11.1 wireframe. Composition over `operations_center` + `operations_intelligence` + `command_center` endpoints. Add Master Asset coverage tile (§14.9).

### Map 12 · Admin Architecture
Already 38 pages. **Recommendation:** promote `AdminCommandCenter.jsx` to the admin top-level landing (today's `AdminHub.jsx` lands in a nav-only state). Wire the integration health, asset coverage, and recent audit events into that landing.

### Map 13 · Prioritized Build Sequence
See §16.

---

## §16 · PRIORITIZED BUILD SEQUENCE

**Build rule:** Composition first. New collections only when there is no existing collection that satisfies the contract.

### P0 — Architecture & Asset Spine (do FIRST, before any new dispatch work)
1. **Master Asset Governance contract publish** (§14). Document the Hybrid model as platform doctrine. No code change; doctrine document only. *Output: `MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md`.*
2. **Reconciliation cadence**: schedule a nightly `asset_mapping_recon.scan` (already an endpoint) and emit a coverage digest to Admin.
3. **AssetProfile cross-link**: ensure `equipment_master` records open `AssetProfile.jsx` from every portal (PM, Shop, Dispatch, Admin). The page exists; cross-links need wiring.

### P1 — Dispatch Command Center + PM Dashboard (highest user-visible value)
4. **Dispatch Command Center** composition: fuse `DispatchHub` + `DispatchBoard` + `OperationalMomentsRail` + Motive arrival chip + Shop OOS strip + PM pull-requests strip into one page.
5. **PM Portal Dashboard** per §9.2 wireframe.
6. **Operations Center board** per §11.1 wireframe.

### P2 — Shop Command Board + Material Movement
7. **Shop Command Board** per §15 Map 10 (composition).
8. **Material Movement UI** for PM + Foreman + Dispatcher (data layer is a skeleton; build read-side first).

### P3 — Integration Activation (operator-gated)
9. **Motive activation** — when operator authorises. Architecture is ready. (NOT a build, an activation.)
10. **MaintainX activation** — when MAINTAINX_API_KEY is provisioned. NOT a build.
11. **FleetWatcher** — only after Motive and MaintainX are stable.

### Deferred (DO NOT START)
* In-app driver messaging (SMS is canonical).
* Driver scoring / leaderboards (doctrine refusal).
* Real-time GPS map of every truck (surveillance — doctrine refusal).
* Accounting integration (post-FleetWatcher).

---

## §17 · PILLAR SCORECARD FOR EVERY RECOMMENDATION

Each P0/P1/P2 item rated against the five pillars (1–5 scale; 5 = fully satisfies):

| Recommendation | Powerful | Simple | Beautiful | Trusted | Proven |
|---|:---:|:---:|:---:|:---:|:---:|
| P0.1 Master Asset Governance contract | 5 | 5 | 4 | 5 | 5 |
| P0.2 Nightly reconciliation digest | 4 | 5 | 4 | 5 | 5 |
| P0.3 AssetProfile cross-links | 4 | 5 | 5 | 5 | 5 |
| P1.4 Dispatch Command Center composition | 5 | 5 | 5 | 4 | 5 |
| P1.5 PM Dashboard composition | 5 | 5 | 5 | 4 | 4 |
| P1.6 Operations Center board | 5 | 5 | 5 | 5 | 5 |
| P2.7 Shop Command Board | 5 | 4 | 4 | 4 | 4 |
| P2.8 Material Movement read-side | 4 | 4 | 4 | 4 | 3 |
| P3.9 Motive activation | 5 | 4 | 5 | 5 | 5 |
| P3.10 MaintainX activation | 4 | 4 | 4 | 4 | 3 |

All recommendations score ≥ 3 on every pillar; **no recommendation fails the Friction Rule** (Constitution Part I).

---

## §18 · STOP — WHAT THIS AUDIT DOES NOT AUTHORISE

Per OMEGA DIRECTIVE + Constitution doctrine:

* No code changes are made by this document.
* No features are mockup-built.
* No screens are redesigned.
* No new collections are created.
* No new endpoints are written.
* No vendor activation is performed (Motive / MaintainX / FleetWatcher remain operator-gated).
* No security / auth / role / token / session-duration changes.
* No write to MASCI production data.

This document is **the architecture contract**. The next authorised step is for the operator to choose a P0 item from §16 and authorise it as a discrete build.

---

## STOP CONDITION REACHED.

*Read-only audit complete. Architecture defined. Pillar-validated. Awaiting operator authorisation for the first P0 build.*
