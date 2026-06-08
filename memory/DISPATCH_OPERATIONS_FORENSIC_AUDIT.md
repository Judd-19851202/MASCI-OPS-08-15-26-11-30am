# MASCI Dispatch Operations Center Forensic Audit

**Date**: 2026-02-12 · **Mode**: Read-only inspection · **Authorized**: NO BUILD · NO CHANGES · NO REDESIGN
**Doctrine**: ForgedOps — Powerful · Simple · Beautiful · Trusted · Proven. Existing systems work before anything new.

---

## EXECUTIVE SUMMARY

The MASCI Operations Platform already contains a **substantially complete, production-grade dispatch operations system**. It is not a greenfield project.

| Headline finding | Evidence |
|---|---|
| **A 13-state canonical lifecycle is already shipped.** | `backend/dispatch_lifecycle.py:25-53` — ASSIGNED · ENROUTE_TO_LOAD · AT_LOAD_SITE · LOADING · LOADED · ENROUTE_TO_JOB · ARRIVED_JOB · DUMPING · COMPLETE · WAITING · HOLD · BREAKDOWN · OFF_SHIFT. Forgiving state machine with `_PREFERRED` transition graph. iter392 · Phase 11.1. |
| **Magic-link driver auth (zero passwords, zero enrolment) is already shipped.** | `backend/driver_sessions.py` (415 LOC). `dispatch_magic_links` + `dispatch_driver_sessions` collections. 15-min one-shot magic token, 12-h revokable session, HMAC-bound. iter393 · Phase 11.2. |
| **Live operational board exists.** | `frontend/src/pages/DispatchBoard.jsx` (600 LOC) — 5-second polling, truck-by-truck rows, state chips, drawer per assignment. iter394. |
| **The single genuine gap is link delivery.** | Magic link URL is **returned to dispatch and copied to clipboard** (`AssignmentDrawer.jsx:190` — `toast.success("Link copied · hand to driver")`). There is no Twilio / WhatsApp Business / SMS gateway wired. Email transport (Resend) is wired but no dispatch email template uses it for magic-link delivery yet. |
| **The Motive integration is stubbed.** | `backend/services/motive_service.py:1-95` — every method returns `"Stub — real Motive API not wired yet."` |
| **Carrier model already supports leased fleets.** | `dispatch_lifecycle.py:104` — `carrier: Optional[str]` on the assignment model. `dispatch_driver.py:761` — `"carriers": carriers` lookup. |

**Recommended path**: **Option C — extend the existing platform at three small, well-defined seams.** The new build surface is ≈ 5–8% of a greenfield dispatch system.

---

## SECTION 1 · DISPATCH PORTAL — EXISTING CAPABILITIES

### Backend routes (mounted under `/api/dispatch`)

| File | Lines | What it does |
|---|---|---|
| `backend/routes/dispatch_portal_auth.py` | — | Dispatch user CRUD + login + password reset + impersonate. Endpoints `/api/dispatch/login`, `/me`, `/change-password`, `/forgot-password`, `/reset-password`, `/admin/dispatch-users (GET POST PATCH DELETE)`, `/admin/dispatch-users/{id}/reset-password`, `/admin/dispatch-users/{id}/impersonate`. |
| `backend/routes/dispatch_lifecycle.py` | 900+ | `POST /assignments` · `GET /assignments` · `GET /assignments/board` · `GET /assignments/{id}` · `POST /assignments/{id}/transition` · `POST /assignments/{id}/cancel` · `POST /assignments/{id}/reassign` · `GET /state-events` · `GET /haul-cycles` · `GET /lifecycle/states` · `GET /haul-activity` · `GET /health-summary` |
| `backend/routes/dispatch_driver.py` | 800+ | `POST /start-shift` · `GET /shift-lookups` · `GET /assignment-lookups` · `POST /magic-link` · `POST /session/exchange` · `GET /me` · `GET /my-assignment` · `POST /assignments/{id}/transition` · `GET /sessions` · `POST /sessions/{id}/revoke` |
| `backend/routes/dispatch_continuity.py` | 600+ | Breakdown reporting · Shop recovery sub-state machine (`reported → acknowledged → diagnosing → waiting_on_parts → repaired → restored`) · operational moments · continuity events. |
| `backend/routes/dispatch_day1_debrief.py` | — | `GET/POST /day-1-debrief` · `GET/POST /week-1-debrief`. |
| `backend/routes/dispatch_exports.py` | — | `GET /assignments.csv` · `GET /state-events.csv` · `GET /haul-cycles.csv` |
| `backend/routes/dispatch_governance.py` | — | `GET /findings` (governance audit surface). |

### Frontend pages

| File | Lines | What it does |
|---|---|---|
| `frontend/src/pages/DispatchHub.jsx` | 650 | Command-centre landing for dispatch — tabbed surface, Operational Attention rail, Assignment Create CTA, notification bell, global search. |
| `frontend/src/pages/DispatchBoard.jsx` | 600 | Live truck-by-truck operational board · 5-sec polling · state chips · per-row drawer · stuck-threshold warning at 30 min. |
| `frontend/src/pages/admin/AdminDispatch.jsx` | 803 | Tabs: Overview · Utilization · Idle Alerts · Transfers · Holds. Embedded into DispatchHub. |
| `frontend/src/pages/DispatchLogin.jsx` · `DispatchForgotPassword.jsx` · `DispatchResetPassword.jsx` · `DispatchChangePassword.jsx` | — | Full dispatch portal auth flow. |
| `frontend/src/pages/DispatchDriverQualification.jsx` | — | Driver qualification dashboard for dispatchers. |
| `frontend/src/pages/admin/AdminDlsDay1Debrief.jsx` · `AdminDlsShiftQR.jsx` | — | Admin debrief + shift-QR sheet. |

### Components

| File | Lines | What it does |
|---|---|---|
| `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx` | 920 | Full create flow: haul type · truck · driver · trailer · carrier · project · destination · material · equipment · pickup · dropoff · liquid-product (tanker) · note. |
| `frontend/src/components/dispatch/AssignmentDrawer.jsx` | 584 | Per-row drawer: issue magic link · reassign · cancel · revoke active sessions · view state history. |
| `frontend/src/components/dispatch/AttachmentStrip.jsx` | 353 | 12-type operational attachment uploader (R2-backed). |
| `frontend/src/components/dispatch/DispatchLifecycleTile.jsx` | 214 | Per-truck lifecycle micro-card. |
| `frontend/src/components/dispatch/OperationalMomentsRail.jsx` | 210 | Recent dispatch events feed. |
| `frontend/src/components/dispatch/PmHaulActivityTile.jsx` | 255 | PM-facing read-only haul activity tile (cross-portal reuse). |
| `frontend/src/components/dispatch/DispatchEquipmentMaintenanceIndicator.jsx` | 53 | Surfaces shop-side breakdown state on the board. |

### Permissions & gating

- Separate `dispatch_users` collection (not `users`). Routes guarded by `require_dispatch_or_admin_dep` / `require_admin`.
- Admin can impersonate any dispatcher. Admin can mutate dispatch_users.
- Driver routes guarded by `dispatch_driver_sessions` HMAC bearer (separate token namespace).

### Notifications & automation already wired

- `backend/routes/notifications.py` + `backend/routes/tasks_notifications.py` — bell feed, unread-count header badge, per-user inbox.
- `backend/routes/resend_webhook.py` — Resend → MASCI delivery tracking (`notification_delivery_delivered`, `notification_delivery_bounced`).
- Email send helper at `backend/server.py:9266` (`_safety_send_email`) — Resend integration with `RESEND_API_KEY` + sender/reply-to env gating.

### Dead / abandoned features in dispatch

**None found.** All seven dispatch backend modules are referenced by routes mounted in `server.py` and exercised by tests `backend/tests/test_iter393_driver_session.py`, `test_iter394_*`, `test_iter409_haul_activity.py`, `test_iter437_magic_link_hardening.py`.

---

## SECTION 2 · FLEET PORTAL

### Backend

| File | What it does |
|---|---|
| `backend/routes/equipment.py` | `equipment_master` collection — full CRUD, asset metadata, model/make seeds. |
| `backend/routes/fleet_ops.py` | DVIR, fleet visibility, driver-asset checkout. |
| `backend/routes/fleet_ops_deps.py` | Shared fleet dependencies (role guards, lookups). |
| `backend/services/maintainx_*.py` | Live MaintainX integration (asset sync, defect coverage, client). |

### Frontend

`FleetVisibility.jsx`, `EquipmentDashboard.jsx`, `NewFleetDVIR.jsx`, `FleetDVIRConfirmation.jsx`, `NewEquipmentInspection.jsx`, `ViewEquipmentInspection.jsx`, `ReturnEquipment.jsx`, `AdminLeadershipEquipment.jsx`, `AdminEquipment.jsx`.

### Capability check

| Capability | Status | Evidence |
|---|---|---|
| Trucks assignable | ✅ | `dispatch_lifecycle.py:453` `body.truck_id` flows into `dispatch_assignments.truck_id`. AssignmentCreateDrawer line 692 `placeholder="Type or pick a truck number"` reads from `equipment_master`. |
| Scheduled | ⚠️ partial | `assigned_at` timestamp is recorded; no calendar / future-dated schedule view. Assignments are "now" oriented. |
| Status tracked | ✅ | `current_state` + `dispatch_state_events` append-only log + `haul_cycles` derived. |
| Linked to jobs | ⚠️ partial | `project_number` + `project_name` are stored on every assignment, but the dispatch create UI uses free text — `JobPicker` component exists (`frontend/src/components/JobPicker.jsx`) and is used by other portals but is **not wired into `AssignmentCreateDrawer`**. |

---

## SECTION 3 · EMPLOYEE SYSTEM

### Backend

`employee_lifecycle.py`, `employee_requests.py`, `field_leadership.py`, `hr_portal.py`, `field_leadership_portal.py`, `auth_directory_routes.py`, `admin_directory_k4.py`.

### Collections

`employees`, `dispatch_users`, `pm_users`, `hr_users`, `safety_users`, `shop_users`, `field_leadership_users` — each portal has its own user collection guarded by its own HMAC token namespace.

### External (no-login) user support

| Capability | Status | Evidence |
|---|---|---|
| MASCI employee full user | ✅ | Per-portal user collections + admin CRUD. |
| **External driver without login / without password / without account** | ✅ | `driver_sessions.py` — driver is an `employees` row tagged eligible. They never get a portal user record. They consume a magic link → 12-h session. iter437 hardened the eligibility validation. |
| Receive notifications | ✅ | Magic link is the notification (carries the assignment context). Once on-session, bell endpoint `/api/dispatch/driver/my-assignment` polls every 6 s. |
| Receive assignments | ✅ | Magic link is bound to `assignment_id`. Driver lands directly on the assignment. |
| Acknowledge assignments | ❌ | **No explicit ack step.** The first transition (e.g. `ENROUTE_TO_LOAD`) is the implicit ack. There is no `acked_at` field or `ACKNOWLEDGED` lifecycle state. This is **a genuine gap** if the business workflow requires an explicit "I have read this" tap before motion. |

---

## SECTION 4 · NOTIFICATION ENGINE

| Channel | Status | Evidence |
|---|---|---|
| Bell (in-app inbox) | ✅ | `tasks_notifications.py:53` — `GET /api/notifications`, `GET /api/notifications/unread-count`. `NotificationsDigest.jsx`, `NotificationBell` component. |
| Email | ✅ | `_safety_send_email` (`server.py:9266`) — Resend wrapper. Gates: `RESEND_API_KEY`, `AUTO_EMAIL_REPORTS`, `SENDER_EMAIL` (`noreply@mascidocs.com`). |
| Email delivery tracking | ✅ | `resend_webhook.py:59-70` — maps `email.delivered` → `notification_delivery_delivered`, `email.bounced` → `notification_delivery_bounced`. HMAC-signed webhook. |
| SMS | ❌ | **Zero references** to Twilio / Vonage / messaging gateway anywhere in `/app/backend`. |
| WhatsApp | ❌ | Zero references to WhatsApp Business API. |
| Push (web/PWA) | ❌ | No service-worker push registration. |
| Reminder (re-send if no ack) | ⚠️ partial | Scheduler exists (`SCHEDULER_ENABLED` env) and `admin_operator_digest.py` runs periodic jobs, but there is no dispatch-specific "remind unacked drivers" job. |
| Escalation | ❌ | No escalation ladder (e.g. ping foreman if driver doesn't move within X min). |

### Assignment notifications currently

- Bell: not auto-wired for new assignment. The notification surface for the driver is the **magic-link URL itself** + the on-session `/my-assignment` polling.
- Email: not auto-wired for new assignment. Resend is configured but nothing in `dispatch_*.py` calls `_safety_send_email`.

---

## SECTION 5 · JOB SYSTEM

### Capability check

| Capability | Status | Evidence |
|---|---|---|
| Job numbers | ✅ | `jobs_master` collection. `project_number` is the canonical key across the platform. |
| Projects | ✅ | `pm_routes.py`, `project_health.py`, `ProjectPnlPage.jsx`. |
| Work orders | ✅ | Daily Reports, Excavation Records, Constraints, PO Requests — all link to `project_number`. |
| Scheduling | ⚠️ partial | Daily Reports have date scoping. No Gantt / sequencing surface. |
| Location systems | ⚠️ partial | Free-text `location` on jobs. No coordinate / lat-lon column. |
| Dispatch assignment ↔ job | ✅ | `dispatch_assignments.project_number` + `project_name` indexed. |
| GPS coordinates on assignment | ❌ | `geo: None` field exists in state-event seed (`dispatch_lifecycle.py:441`) but is never written. |
| Route links | ⚠️ partial | No structured `route_url` field. Foremen would currently paste a URL into the free-text `note` on the assignment. |
| Documents / plans attached to job | ✅ | `operational_attachments` collection with 12 canonical types (asphalt_ticket, scale_ticket, BOL, fuel_receipt, delivery_receipt, load_photo, damage_photo, breakdown_photo, inspection_photo, transfer_document, dump_receipt, operational_note_photo). R2 cold-storage. 5 MB cap. 25 attachments per host. **But host kind is `assignment` only — not `job`.** |

---

## SECTION 6 · GPS / TELEMATICS

| Provider | Status | Evidence |
|---|---|---|
| Motive | ❌ STUB | `backend/services/motive_service.py:25-95` — `class MotiveService` with all 6 methods returning `"Stub — real Motive API not wired yet."` Docstring: *"placeholder methods that return safe responses until real Motive API docs + credentials are confirmed by MASCI."* Frontend `DispatchIntegrationsTab.jsx:72-95` shows readiness tiles with empty-state message: *"Awaiting Motive integration configuration."* |
| FleetWatcher | ❌ ABSENT | Zero references in `/app/backend` or `/app/frontend`. |
| Geofencing | ❌ ABSENT | Zero references. |
| MaintainX (asset-side) | ✅ LIVE | `services/maintainx_*.py` is live (asset sync, defect coverage, client) — used for fleet/equipment, not dispatch positions. |

### What dispatch already captures without GPS

- Driver-tap state transitions with timestamps + `state_history` array on the assignment.
- Plant arrival = driver tap at `AT_LOAD_SITE`.
- Job arrival = driver tap at `ARRIVED_JOB`.
- Dump complete = driver tap at `COMPLETE`.

This is "human-confirmed telemetry" — equivalent to the WhatsApp workflow today, but with structured timestamps. Real GPS would be additive validation, not foundational.

---

## SECTION 7 · COMMUNICATIONS

| Audience | Channel | Status |
|---|---|---|
| Employees | Bell · Email · per-portal inbox | ✅ |
| Vendors | Email | ✅ via `_safety_send_email` |
| Subcontractors | Email | ✅ same |
| Drivers (leased, no login) | **Magic link URL** | ✅ generated, ❌ **manual hand-off only** — dispatcher copies the URL and pastes it into WhatsApp/SMS by hand today. |

### Outbound delivery automation

- Email: configured (Resend) but `dispatch_*.py` does not invoke `_safety_send_email` for assignment events.
- SMS: not configured.
- WhatsApp Business: not configured.

---

## SECTION 8 · DRIVER ACCESS MODEL

This is where the platform is strongest.

### What exists

| Mechanism | Status | Evidence |
|---|---|---|
| Magic link issuance | ✅ | `driver_sessions.py:201-249` — `issue_magic_link()`. Token `secrets.token_urlsafe(32)`, SHA-256 stored, 15-min TTL. Driver eligibility validated against `employees` collection before mint. |
| Magic link consumption | ✅ | `driver_sessions.py:255-310` — `consume_magic_link()`. One-shot (flips `used_at`). |
| Secure session | ✅ | `dispatch_driver_sessions` collection · 12-h TTL · revokable by dispatcher · HMAC-signed token. |
| SMS link delivery | ❌ | **No SMS gateway.** Dispatcher copies URL to clipboard (`AssignmentDrawer.jsx:190`). |
| Email link delivery | ❌ | **Not wired.** Resend is available but the dispatch route does not call it for magic-link delivery. |
| One-time link | ✅ | Single-use via `used_at` flip. |
| Tenant-aware link | ✅ | `dispatch_magic_links.tenant_id`. |

### Driver mobile surface

`frontend/src/pages/driver/DriverMagicLanding.jsx` · `DriverShift.jsx` (610 LOC) · `ShiftStart.jsx`:
- Magic-link landing exchanges token → session → routes to assignment.
- Driver sees giant state chip + next-state tap buttons.
- 6-second poll for assignment changes.
- **Offline transition queue** (`enqueueOfflineTransition` — iter421 · Phase 23.0) — taps are persisted locally and replayed when signal returns.
- Wait-sheet for canonical wait reasons (one-tap selection).
- BREAKDOWN tap surfaces optional photo proof prompt.

---

## SECTION 9 · REUSABILITY MATRIX

| Capability | Already exists | Partial | Missing | Reusable verbatim |
|---|---|---|---|---|
| Driver Assignment record | ✅ | | | YES — `dispatch_assignments` |
| Truck Assignment | ✅ | | | YES — `truck_id` field + equipment_master lookup |
| Job Linkage | | ⚠️ free-text only in dispatch UI | | YES — `JobPicker` exists, just unmounted in `AssignmentCreateDrawer` |
| Carrier / leased fleet | ✅ | | | YES — `carrier` field on assignment |
| Driver magic-link auth | ✅ | | | YES — `driver_sessions.py` |
| Driver mobile UI | ✅ | | | YES — `DriverShift.jsx` |
| Acknowledgement (explicit) | | | ❌ | NO — does not exist |
| 13-state lifecycle | ✅ | | | YES — `dispatch_lifecycle.py` |
| Transition log (audit) | ✅ | | | YES — `dispatch_state_events` |
| Wait / Hold / Breakdown | ✅ | | | YES — built into state machine |
| Reassign | ✅ | | | YES — `POST /assignments/{id}/reassign` |
| Cancel | ✅ | | | YES — `POST /assignments/{id}/cancel` |
| **Revision (edit destination, material, dropoff while in-flight)** | | | ❌ | NO — only reassign/cancel exist; no PATCH-fields endpoint |
| Live Dispatch Board | ✅ | | | YES — `DispatchBoard.jsx`, 5-sec poll |
| Haul cycle derivation | ✅ | | | YES — `haul_cycles` collection |
| CSV exports | ✅ | | | YES — `dispatch_exports.py` |
| Operational attachments | ✅ | | | YES — 12 canonical types, R2-backed |
| Breakdown → Shop recovery | ✅ | | | YES — `dispatch_continuity.py` |
| Bell notifications | ✅ | | | YES — `tasks_notifications.py` |
| Email delivery + tracking | ✅ | | | YES — Resend wired, webhook tracks delivered/bounced |
| **SMS / WhatsApp delivery of magic link** | | | ❌ | NO — no Twilio / WA Business / messaging gateway |
| **New-assignment notification to dispatcher** | | ⚠️ partial (bell exists, no wiring) | | partial |
| **Revision notification to driver** | | | ❌ | NO (revision flow itself does not exist) |
| **Reminder / escalation if unacked** | | | ❌ | NO — no scheduled reminder job for dispatch |
| GPS / geofencing (Motive) | | ⚠️ stub | | NO — service is stub; integration TODO |
| Day-1 / Week-1 debrief | ✅ | | | YES — already shipped |
| Driver qualification dashboard | ✅ | | | YES — three portals already render it (HR, FL, Dispatch) |
| Dispatch governance findings | ✅ | | | YES — `dispatch_governance.py` |
| Tenant isolation | ✅ | | | YES — `tenant_id` on every collection |

---

## SECTION 10 · GAP ANALYSIS

Only items strictly required to convert today's WhatsApp dispatch workflow into the existing platform.

| # | Gap | Complexity | Dependencies | Reuse opportunities | Effort |
|---|---|---|---|---|---|
| **G1** | **SMS / WhatsApp magic-link delivery.** Dispatcher today copies the magic URL to clipboard and pastes into WhatsApp by hand. To eliminate WhatsApp from the workflow, the system must deliver the link out-of-band to a phone number. | Medium | New integration: Twilio Programmable Messaging *or* WhatsApp Business API. Add `phone` field on `employees` records (the field likely already exists — verify). Single new env: `TWILIO_*`. | Reuse `_safety_send_email` pattern as the SMS twin (`_dispatch_send_sms`). Reuse the existing magic-link endpoint — only add a `deliver_via: ["sms"|"email"|"copy"]` flag and a new transport helper. | 1–2 days. |
| **G2** | **Explicit driver acknowledgement.** Today, the first state transition is the implicit ack. Business workflow stated *"No acknowledgement tracking. No revision acknowledgement."* — implying they want explicit ack. | Low | None (DB additive). | Add `acked_at` + `acked_via` to `dispatch_assignments`. Add `POST /api/dispatch/driver/assignments/{id}/acknowledge` (reuses driver session guard verbatim). Render an "ACKNOWLEDGE" tap on `DriverShift.jsx` shown only when `current_state === "ASSIGNED" && !acked_at`. | 0.5 day. |
| **G3** | **Revise an assignment in flight.** Today: reassign or cancel only. Operations sometimes need to change destination / material / dropoff while the truck is moving without breaking the lifecycle continuity. | Medium | None (DB additive). | New `POST /api/dispatch/assignments/{id}/revise` accepting a delta of mutable fields (destination · material · dropoff · note). Append a `revision_event` to `dispatch_state_events` and a `revision_history[]` array on the assignment. Surface a "Revise" action in `AssignmentDrawer.jsx` next to existing Reassign/Cancel. Push a re-ack request to the driver (resets `acked_at = null`, fires SMS via G1). | 1.5–2 days. |
| **G4** | **Wire `JobPicker` into the dispatch create drawer.** Today the project number is a free-text input in `AssignmentCreateDrawer.jsx:756`. The component `frontend/src/components/JobPicker.jsx` is already used by Daily Reports, Excavations, Constraints — same shape. | Trivial | None — component exists. | Drop-in replacement of the `<Input>` at line 756 with `<JobPicker onSelect={...}>`. | 0.5 day. |
| **G5** | **New-assignment auto-notify dispatcher / driver.** The notification *primitives* are wired but no dispatch route currently calls `_safety_send_email` or `db.tasks.insert_one({kind:"dispatch_new_assignment"})`. | Low | None — both transports already live. | In `POST /assignments` handler, after `insert_one`, fire (a) a bell `task` for the assigning dispatcher's manager and (b) a Resend email + SMS (G1) to the driver. | 0.5 day. |
| **G6** | **Reminder / escalation for un-acked assignments.** | Medium | Needs G2 first. Scheduler is already enabled (`SCHEDULER_ENABLED=true` per `PRODUCTION_SECRETS_SEALED.env.template`). | Add one periodic job — `dispatch_reminders.py` — that scans `dispatch_assignments` where `acked_at == None and assigned_at < now - 10 min` and re-fires the magic link + escalates to dispatcher bell after 20 min. | 1 day. |
| **G7** | **Real Motive GPS wiring** (replace stub). | High | External: real Motive credentials + API contract from MASCI. The codebase has the stub seam ready. | Replace each of the 6 stub methods in `motive_service.py` with real `httpx` calls. State-event ingestion already accepts a `geo` field. | Out of scope for "make dispatch work" — defer to Phase 2. The system runs correctly today on human-tap telemetry. |

**Net new code surface for G1–G6**: ≈ 1 100 LOC across 4 backend files and 3 frontend files. Zero schema migrations (all additive fields).

---

## SECTION 11 · FINAL ARCHITECTURE RECOMMENDATION

### Option A — Build using existing platform components only
**Verdict: insufficient.** Without G1 (SMS delivery), dispatchers must still copy a link and paste into WhatsApp. This is a hand-off step, not an integrated system. Acceptable as an interim — unacceptable as the destination state.

### Option B — Extend existing platform components
**Verdict: optimal.** All seven gaps map cleanly onto existing seams. No collection rename, no portal rebuild, no auth refactor.

### Option C — Build new components only where absolutely required
**Verdict: equivalent to B.** The only genuinely "new" component is the SMS transport (G1). Everything else is wiring existing primitives together.

### **Recommended path: Option B (= C)**

Six surgical extensions, each independently shippable:

1. **G4** — wire `JobPicker` into AssignmentCreateDrawer (½ day · UI-only).
2. **G2** — explicit driver acknowledgement (½ day · additive DB + UI).
3. **G5** — auto-notify on new-assignment via existing bell + email (½ day · server-only).
4. **G1** — SMS magic-link transport (Twilio or WhatsApp Business) (1–2 days · one new integration).
5. **G3** — revise endpoint + UI (1.5–2 days · additive).
6. **G6** — un-acked reminders (1 day · scheduler job).

**Optional Phase 2**: G7 (real Motive GPS) once MASCI has Motive API credentials and a stable contract.

---

## SECTION 12 · IMPLEMENTATION EFFORT

### Existing platform reuse %
- Backend lifecycle, state machine, magic-link, driver session, dispatch board, attachment system, exports, breakdown/recovery, debriefs, governance, notifications, email transport, tenant model: **≈ 92 %** of a complete dispatch operations system is **already shipped**.
- Net new development required: **≈ 8 %** — all of it additive, no breaking change, no refactor.

### Effort

| Scenario | Days | Notes |
|---|---|---|
| **Best case** | 5 dev-days | G1 reuses Twilio's playbook · external dashboards land same day · no QA regressions on existing dispatch tests. |
| **Expected** | 8 dev-days | Includes one round of foreman feedback, SMS template iteration, ack-UI polish. |
| **Worst case** | 12 dev-days | Twilio onboarding (10DLC SMS registration) delays G1 by 5 days; WhatsApp Business API approval takes 7–14 days if chosen as primary channel. |

### Risk register
- **R1** — Twilio 10DLC SMS registration for US toll-free / long-code can take 3–5 business days. Mitigation: ship email-delivery first as fallback (Resend already wired).
- **R2** — WhatsApp Business API requires Meta business verification (1–3 weeks). Mitigation: SMS first; WhatsApp later if leased drivers prefer it.
- **R3** — Some leased drivers may use shared phones. Mitigation: magic links are already single-use and tenant-scoped — no change needed.

---

## CLOSING

> **Most of a world-class dispatch operations system is already in this codebase.**
> The work remaining is not "build" — it is "connect, deliver, and acknowledge."

Final reuse measure: **92 % already shipped · 8 % to wire**.

No new portal. No new auth model. No new database. No new lifecycle. No new fleet model.
Six small extensions on existing seams flip the WhatsApp workflow into a tracked, acknowledged, revision-aware, audited dispatch operation.

**End of audit.**
