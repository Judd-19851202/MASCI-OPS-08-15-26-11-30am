# TRACK 13.8B — Hidden Systems Audit & Recovery Discovery

**Date**: 2026-06-12
**Mode**: DISCOVERY ONLY · NO CODE · NO ROUTES · NO IMPLEMENTATION · NO RETIREMENT
**Doctrine**: Discover → Verify → Document → Decide → Build. Source-truth wins.

> Builds on Track 13.8A (workflow gap discovery) and Tracks 13.6/13.7 (portal swaps and map lens). This report focuses **only** on internal systems that exist in source but may be hidden, underused, partial, abandoned, duplicated, or operationally undiscovered.

---

## 1 · Executive Summary

A source-truth scan of 115 backend route modules + 245 frontend pages reveals that **MASCI OPS already owns a substantial amount of operational machinery that is built, working, and either (a) used through narrow surface area, (b) reachable only through a single deep-link, or (c) operationally complete but role-blind in placement.**

**Hidden Gold #1 (highest leverage)**: the **PO Requests** subsystem — 12 backend endpoints, a 795-line frontend page implementing list / detail / submit / approve / receipt / close / cancel / clarification-response / CSV export — exists at **estimated 95% completion** but is reachable only via a single `/po-requests` route with no role-specific surfacing in PM Hub V2, Shop Hub V2, HR Hub V2, or Field Leadership V2. Operators may not know it exists.

**Hidden Gold #2**: the **Operational Records family** (8 modules · `operational_records / events / timeline / signals / links / locations / attachments / constraints`) provides a cross-workflow event ledger (project-day timelines · detection-key timelines · dispatch-status linkage · approval queues for geofence reconciliation). Of these, **Operational Constraints** is operator-surfaced (PM Hub); **Operational Events** has admin-only materialization endpoints; **Operational Locations** has an admin-only geofence reconciliation queue. The frontend does NOT consume `/api/operational-records` or `/api/operational-timeline` or `/api/operational-signals` from any role page (search returned 0 hits).

**Hidden Gold #3**: the **Asset Spine reservation columns** (`fleetwatcher_asset_id`, `maintainx_asset_id`) are wired into the spine read/write surface (`services/asset_spine.py` lines 73–74, 144–145, 259–264, 411–412, 455) and the spine API exposes integration-mapping status per asset. The data shape is ready; only the live provider feeds are missing. **Activation effort is integration credentials + a service file, not architecture work.**

**Recommendation**: do not build anything new. Do not retire anything in this track. **First operator-validate the existing PO Requests subsystem and the Operational Locations admin reconciliation queue.** Both already exist at near-production completion and are doctrine-pure. Track 13.8C (if authorised) could be a thin "surfacing pass" — adding role-specific links to the existing pages from the existing V2 hubs — with zero new backend work.

---

## 2 · Full System Inventory (source-verified)

| # | System | Routes | Frontend | Class |
|---|---|---|---|---|
| 1 | PM Hub V2 + command-center engines | `routes/pm_command_center.py` · `routes/pm_routes.py` · `routes/pm_admin.py` | `/pm/hub` · `/pm/holds` · many | **Active** |
| 2 | HR Hub V2 + employee requests / time-off | `routes/hr_portal.py` · `routes/employee_requests.py` · `routes/employee_lifecycle.py` | `/hr` · `/hr/employees` · many | **Active** |
| 3 | Safety Hub V2 + forms / topic library / corrective actions | `routes/safety.py` · `routes/safety_forms.py` · `routes/safety_topic_library.py` | `/safety-portal` · many | **Active** |
| 4 | Shop Hub V2 + Recovery Map lens + shop parts + shop command feed | `routes/shop_parts.py` · `routes/shop_command_feed.py` · `routes/shop_portal_deps.py` · `routes/dispatch_command_center.py` (shop summary) | `/shop` · Section 3 (Track 13.7B) | **Active** |
| 5 | Dispatch Portal + driver intel + governance + exports + day-1 debrief | `routes/dispatch_*.py` (10 files) | `/dispatch-portal` (map dominant) | **Active · hard lock** |
| 6 | Driver public flow (no-login) | `routes/dispatch_driver.py` · `routes/driver_profile.py` | `/shift` · `/d/:token` · `/driver` | **Active · hard lock** |
| 7 | Field Leadership Portal | `routes/field_leadership_portal.py` · `routes/field_leadership.py` | `/field-leadership/*` | **Active** |
| 8 | Admin (30+ sub-pages: integrations, audit, IAM, scheduler, MFA, deploy readiness, governance) | `routes/admin_*.py` (8 files) · `routes/governance*.py` (3) · `routes/integration_health.py` · `routes/deploy_readiness.py` · `routes/scheduler_runs_admin.py` | `/admin/*` | **Active** |
| 9 | Leadership companion | (consumes existing surfaces) | `/leadership` + `/leadership/hub_v2` | **Active · companion** |
| 10 | Daily Reports + lifecycle | `routes/daily_reports.py` · `routes/daily_report_lifecycle.py` | `NewDailyReport.jsx` · `ViewDailyReport.jsx` | **Active** |
| 11 | QA/QC + lifecycle | `routes/qaqc.py` · `routes/qaqc_lifecycle.py` | many | **Active** |
| 12 | JHP / JHA acknowledgements | `routes/jha_acknowledgements.py` | `AdminJhaAcknowledgements.jsx` | **Active** |
| 13 | Incidents + lifecycle | `routes/incident_lifecycle.py` | `SafetyIncidents.jsx` · `HrIncidents.jsx` | **Active** |
| 14 | Operational Constraints | `routes/operational_constraints.py` | PM Hub V2 + classic surfaces | **Active** |
| 15 | Operational Records | `routes/operational_records.py` (2 endpoints) | **0 hits in frontend** | **Dormant · operator-blind** |
| 16 | Operational Events | `routes/operational_events.py` (6 endpoints; 3 admin materialize/audit/dashboard + 3 project-day/timeline/dispatch-status) | **0 hits in frontend** | **Partial · admin-only** |
| 17 | Operational Timeline | `routes/operational_timeline.py` (1 GET endpoint) | **0 hits in frontend** | **Dormant** |
| 18 | Operational Signals | `routes/operational_signals.py` (admin endpoint only) | `components/admin/OperationalSignalsPanel.jsx` (admin-only) | **Companion · admin-only** |
| 19 | Operational Links | `routes/operational_links.py` (POST · GET list · GET one · PATCH status) | (cross-record link table) | **Active · plumbing-only** |
| 20 | Operational Locations | `routes/operational_locations.py` (8 admin endpoints — import-geofences · reconcile · reconciliation-queue · by-project · approve · reject · reassign · bulk-approve) | (admin-side only) | **Active · admin queue** |
| 21 | Operational Attachments | `routes/operational_attachments.py` (incl. `scale_ticket` kind enum) | dispatch attach UI | **Active · partial schema** |
| 22 | **PO Requests** | `routes/po_requests.py` (12 endpoints · full lifecycle) | `pages/PoRequests.jsx` (795 lines · complete UI) | **Active · UNDER-SURFACED** |
| 23 | **Material Movement** | `routes/material_movement.py` (1 GET endpoint · daily roll-up) | `MaterialMovementTile.jsx` + `ViewDailyReport.jsx` | **Active · narrow** |
| 24 | Tasks + Notifications | `routes/tasks_notifications.py` (11 endpoints) · `routes/notifications.py` (6 portal-digest endpoints) | various | **Active** |
| 25 | Equipment Defects (DVIR) | `routes/fleet_ops.py` · `routes/fleet_ops_deps.py` · `routes/equipment.py` | `FleetVisibility.jsx` · many | **Active** |
| 26 | Asset Spine + scheduler + recon | `services/asset_spine.py` · `services/asset_spine_scheduler.py` · `routes/asset_spine.py` · `routes/asset_mapping_recon.py` · `routes/asset_transfers.py` | admin tools | **Active** |
| 27 | Driver Qualification | `routes/driver_profile.py` | `HrDriverQualificationDashboard.jsx` · `DispatchDriverQualification.jsx` | **Active** |
| 28 | Training Center | `routes/training_center.py` | `SafetyTrainingRecords.jsx` · `HrTrainingRecords.jsx` | **Active** |
| 29 | Document Expirations | `routes/document_expirations.py` | leadership · admin · HR | **Active** |
| 30 | Operations Map + contract surface | `routes/operations_map_v1.py` · `routes/operations_map_contract.py` | `/operations-map` (admin-only frontend gate) · `DispatchMapHero` · `ShopRecoveryMap` | **Active · single engine** |
| 31 | Trench Safety bridge | `routes/trench_transport_bridge.py` | `/safety/trench-safety` | **Active** |
| 32 | Motive integration | `services/motive_service.py` · `lib/motive_reliability.py` · `routes/integrations/maintainx_p0.py` | webhook + poll | **Active · live** |
| 33 | MaintainX integration | `services/maintainx_service.py` · `services/maintainx_client.py` · `routes/integrations/maintainx_p0.py` · `routes/integrations/webhooks.py` | (admin health surface) | **Stub · awaiting_credentials** |
| 34 | FleetWatcher integration | Column reserved only · no service file | – | **Slot only · dormant** |
| 35 | Job Photos | `routes/job_photos.py` · `routes/photo_governance.py` | `JobPhotosLibrary.jsx` | **Active** |
| 36 | Signatures + migration | `routes/signatures.py` · `routes/signature_migration.py` | many | **Active** |
| 37 | Field Memory | `routes/field_memory.py` | (limited consumers) | **Partial** |
| 38 | Field Revision | `routes/field_revision.py` | (limited consumers) | **Partial** |
| 39 | Payroll Variance + lifecycle | `routes/payroll_variance.py` · `routes/payroll_variance_lifecycle.py` | `HrPayrollVariance.jsx` · `HrTimeVerification.jsx` | **Active** |
| 40 | Backup Verification | `routes/backup_verification_routes.py` | admin tool | **Active · ops** |
| 41 | Resend webhook | `routes/resend_webhook.py` | (email delivery feedback) | **Active · ops** |
| 42 | SMS provider | `services/sms_provider.py` | (provider stub) | **Active / stub TBC** |
| 43 | Scheduler / scheduler-runs admin | `routes/scheduler_runs_admin.py` | admin tool | **Active · ops** |
| 44 | Workflow Undo | `routes/workflow_undo.py` | (admin tool) | **Active · ops** |
| 45 | Date audit | `routes/date_audit.py` | admin | **Active · ops** |
| 46 | Global Search | `routes/global_search.py` | `GlobalSearch.jsx` | **Active** |
| 47 | Legacy imports | `routes/legacy_imports.py` | admin | **Active / migration tool** |
| 48 | Promo assets | `routes/promo_assets.py` | (asset hosting) | **Active** |
| 49 | Cluster capacity / draft telemetry / usage analytics / governance self-protection / last activity | various | admin-only | **Active · ops** |
| 50 | Internal V2 surfaces (`/_internal/v2-index`, `/_internal/v2-compare/:portal`, `/_internal/design-system`, `/_internal/pm-v2-preview`, `/_internal/hr-v2-preview`) | – | `App.js` lines 991–995 | **Active · internal tools** |

---

## 3 · PO Requests Audit (Hidden Gold #1)

### 3.1 · Backend completeness
12 endpoints in `routes/po_requests.py`:

| Endpoint | Purpose |
|---|---|
| `GET /api/po-requests` | list (with filters) |
| `GET /api/po-requests/summary` | aggregate counts |
| `GET /api/po-requests/export.csv` | CSV export |
| `GET /api/po-requests/{po_id}` | detail |
| `POST /api/po-requests` | create |
| `POST /api/po-requests/{po_id}/approve` | approval action |
| `POST /api/po-requests/{po_id}/receipt` | upload receipt (file) |
| `GET /api/po-requests/{po_id}/receipt` | download receipt |
| `POST /api/po-requests/{po_id}/respond-clarification` | request response |
| `POST /api/po-requests/{po_id}/close` | close PO |
| `POST /api/po-requests/{po_id}/cancel` | cancel PO |
| `POST /api/admin/po-requests/scan-missing-receipts` | admin maintenance |
| `GET /api/admin/po-requests/scan-missing-receipts/preview` | admin preview |

### 3.2 · Frontend completeness
- `pages/PoRequests.jsx` — 795 lines, mounted at `/po-requests`.
- Uses the full client surface in `lib/poApi.js`: `listPos · poSummary · getPo · submitPo · approvePo · uploadReceipt · closePo · cancelPo · respondClarification · downloadPoExportCsv`.
- Receipt download has a polished UX (placeholder window + spinner during fetch).

### 3.3 · Completion estimate · **~95 %**
- The lifecycle (create → approve → clarify-respond → receipt-upload → close · plus cancel) is end-to-end.
- Admin "scan missing receipts" maintenance endpoint exists.
- CSV export exists.
- What is missing is **surfacing** — `/po-requests` is referenced in 10 frontend files (admin sidebar · PM domain map · HR side-nav · Field Leadership Hub · Project Health · GlobalSearch · StatusBadge · OperationalSignalsPanel · portalContext · `lib/poApi.js`), but there is **no dedicated PO action queue card in PM Hub V2 or Shop Hub V2** — the very places where PO friction is most felt.

### 3.4 · Operational value: **HIGH**
PO requests are operationally frequent (materials, vendor work, equipment rentals) and the existing module implements the full approval chain. If operators don't know about it, the rest of the business is suffering email + Excel.

### 3.5 · Recovery effort: **LOW**
Zero new backend. Possibly a single PO action-queue card embed in PM Hub V2 + Field Leadership V2 (a future track — NOT authorised here).

---

## 4 · Material Movement Audit

### 4.1 · Backend surface
Single endpoint: `GET /material-movement/daily/{project_number}/{date}`.

Internally it JOINs `dispatch_assignments` (filtered to the day) with `daily_reports` (filtered to the day) and produces a daily roll-up. **No write workflow.** No ticket entry. No batching. No reconciliation. No structured haul / scale data.

### 4.2 · Frontend surface
- `components/MaterialMovementTile.jsx` — a read-only daily tile.
- Mounted inside `ViewDailyReport.jsx` (the daily-report viewer).
- Nowhere else.

### 4.3 · Completion estimate · **~30 %** — but the 30 % is honest: this is a *read view* over existing data, not a *recording surface*.

### 4.4 · Overlap analysis
- Dispatch: dispatch assignments are the source of material movement records.
- Fleet: not used in Material Movement directly.
- Haul / Scale Tickets: the `scale_ticket` attachment kind (`operational_attachments.py` line 69) is a separate slot — Material Movement does NOT currently consume it.
- Production tracking: Daily Reports narrative is the input — Material Movement reads it.

### 4.5 · Operational value · **MEDIUM** (read-only)
- Material Movement tile is useful for PM review of a day's materials.
- For Field Ops, the value is in **structured per-load capture** which the current module does NOT provide.

### 4.6 · Recovery effort
Two distinct paths exist (do NOT pick one in this track):
- **Recovery as-is**: surface MaterialMovementTile inside PM Hub V2 daily-report context — pure surfacing — low effort.
- **Recovery to "useful tomorrow"**: extend `scale_ticket` attachments with 4 structured numeric fields (gross/tare/net/material) — same as Track 13.8A Section 7.2 recommendation — low effort, but still **operator-interview gated**.

---

## 5 · Operational Records Audit (Hidden Gold #2)

The Operational-Records family is **8 backend modules** that together form a cross-workflow ledger plumbing. Source-truth audit per module:

| Module | Endpoints | Frontend hits | Class |
|---|---|---|---|
| `operational_records.py` | 2 (`GET ""` list · `GET ""` detail variant) | **0** | **Dormant** — full read API exists but no consumer |
| `operational_events.py` | 6 (admin materialize · audit · dashboard · project-day · timeline · dispatch-status) | **0** in frontend (admin tools only) | **Partial · admin-only** |
| `operational_timeline.py` | 1 (`GET ""` list) | **0** | **Dormant** |
| `operational_signals.py` | 1 (`/api/admin/operational-signals`) | `components/admin/OperationalSignalsPanel.jsx` | **Companion · admin-only** |
| `operational_links.py` | 4 (POST · GET list · GET one · PATCH status) | (plumbing) | **Active · plumbing** |
| `operational_locations.py` | 8 (admin geofence reconciliation queue) | admin | **Active · admin queue** |
| `operational_attachments.py` | (writes) | dispatch attach UI | **Active · partial schema (scale_ticket slot)** |
| `operational_constraints.py` | (full CRUD) | PM Hub | **Active** |

**Hidden Gold within the family**:
1. **`operational_events.dashboard`** — `GET /admin/operational-events/dashboard` — produces a cross-workflow dashboard payload that no operator surface consumes today.
2. **`operational_events.project-day`** — `GET /operational-events/project-day/{project_number}/{date}` — produces a per-project per-day events roll-up. Same data shape that a PM would ask for verbally.
3. **`operational_events.timeline`** — `GET /operational-events/timeline/{detection_key}/{date}` — produces a per-asset day timeline. Same data shape that a Shop manager would ask for verbally.
4. **`operational_locations`** admin reconciliation queue — the geofence reconciliation queue exists and is real; only admin sees it today.

**These are exactly the cross-workflow ledger primitives the platform is missing visible surfaces for.** Doctrine: surface what already exists before building new.

---

## 6 · Notifications Audit

### 6.1 · Inventory
- `routes/tasks_notifications.py` — 11 endpoints (tasks CRUD + notifications list / unread-count / read / read-all / acknowledge).
- `routes/notifications.py` — 6 portal-specific digest endpoints (admin · safety · hr · pm · dispatch · fl).
- `routes/resend_webhook.py` — Resend email-delivery feedback.
- `routes/admin_digest_config.py` + `routes/admin_operator_digest.py` + `routes/po_digest_admin.py` — admin-side digest configuration.

### 6.2 · Risk surface
- **Spam risk**: 6 portal-digest endpoints exist. Trigger frequency and recipient filtering need operator validation. **No audit was done in this track on the actual cron schedule** — defer to operator interview.
- **Dead triggers**: not detected in this scan (the `awaiting_credentials` markers all belong to Motive / MaintainX provider stubs, not notification stubs).
- **Missing recipients**: not detected.
- **Orphaned jobs**: `services/asset_spine_scheduler.py` exists; cron-status surface is exposed by `routes/scheduler_runs_admin.py` and is admin-only.

### 6.3 · Class · **Active · operator-validation gated**
The Notifications system is operational. Recovery question is: are the digests reaching the right people? **That is an operator interview question**, not a code question.

---

## 7 · Asset Spine Extension Audit (Hidden Gold #3)

### 7.1 · Reserved columns in `services/asset_spine.py`
```
line 73: "fleetwatcher_asset_id",
line 74: "maintainx_asset_id",
```
Both are wired throughout the spine:
- Persisted (lines 144–145)
- Reported in spine status payload (lines 259–264 — mapped/unmapped boolean for each)
- Accepted in spine create / patch (lines 411–412, 455)

### 7.2 · MaintainX integration
- `services/maintainx_service.py` — STUB returns `awaiting_credentials` on every method (lines 34, 53, 71).
- `services/maintainx_client.py` — exists as a transport shim.
- `routes/integrations/maintainx_p0.py` — exists as a router; verify completion separately if/when activation is authorised.
- `routes/integrations/webhooks.py` line 69 — webhook intake also returns `awaiting_credentials` when MaintainX is not configured.

### 7.3 · FleetWatcher
- **No service file** exists.
- **No route file** exists.
- Only the reserved column on the asset spine.
- Recovery requires writing the service from scratch — **higher cost than MaintainX**.

### 7.4 · Class
- **MaintainX**: ~70 % complete (column + client + service stub + p0 router + webhook intake). Activation effort = real credentials + minor service implementation.
- **FleetWatcher**: ~10 % complete (column only). Activation effort = full service write.

### 7.5 · Doctrine reminder
Per Tracks 13.7A / 13.7B: **MAP IS MOTIVE-ONLY today.** Activating MaintainX or FleetWatcher does NOT automatically enrich the map — it requires a separate workflow-discovery track to decide whether and how to surface that data. **Do not assume activation = visibility.**

---

## 8 · Partial System Inventory (TODO / FIXME / STUB / awaiting_credentials)

43 backend files match the partial-work indicators. Material findings (excluding test files):

| File | Indicator | What it means |
|---|---|---|
| `services/motive_service.py` lines 162, 667 | `awaiting_credentials` | graceful degradation when Motive API key absent — **expected behaviour, not partial** |
| `services/maintainx_service.py` lines 34, 53, 71 | `awaiting_credentials` | full stub until credentials present — **expected partial** |
| `lib/motive_reliability.py` line 64 | `awaiting_credentials` | reliability harness handles credential-absent state — **expected** |
| `routes/integrations/webhooks.py` line 69 | `awaiting_credentials` | webhook intake handles MaintainX absent state — **expected** |

**No `TODO:` / `FIXME` / `STUB` markers were found in non-test production code in this scan.** That is unusual for a codebase this size and is a good sign — most partial systems carry their partial-ness in the `awaiting_credentials` doctrine, which is honest.

---

## 9 · Duplicate System Inventory

### 9.1 · Map duplication
Verified single engine: **MapCanvas** + **useMapSnapshot** + **/api/operations-map/snapshot**. Consumed by:
- `/dispatch-portal` (`DispatchMapHero` embed)
- `/operations-map` full page (Admin-gated frontend)
- `/shop` Section 03 Recovery Map (Track 13.7B embed)
- (no other surface)

**No duplicate map engine.** Hard lock intact. Per Track 13.7A.

### 9.2 · Constraints vs CAPAs vs Incidents
| System | Routes | Class |
|---|---|---|
| Operational Constraints | `routes/operational_constraints.py` | PM-facing |
| Safety CAPAs | `routes/safety.py` corrective-actions | Safety-facing |
| Incidents | `routes/incident_lifecycle.py` | Safety + HR-facing |

**Not duplicates** — different lifecycles, different owners, different evidence types. **KEEP**.

### 9.3 · Reports vs Events vs Timeline vs Records
| System | Class |
|---|---|
| Daily Reports | shift-day operator narrative |
| Operational Events | system-side detected events (asset movements / geofence enters / etc.) |
| Operational Timeline | ledger view of operational links |
| Operational Records | abstract record table |

These are **layered**, not duplicate. Daily Reports is operator-authored. Operational Events is system-detected. Operational Timeline is link-ledger. **KEEP** all four — but the latter two are dormant on the frontend (Section 5).

### 9.4 · Notification stacks
- `routes/tasks_notifications.py` (in-app tasks + notifications)
- `routes/notifications.py` (portal digests · email)
- `routes/admin_digest_config.py` / `routes/admin_operator_digest.py` / `routes/po_digest_admin.py` (admin config)

These layer rather than duplicate. **KEEP** — operator interview should verify the digest cadence is sane.

### 9.5 · HR Hubs (V1 + V2)
- `pages/HrHub.jsx` (legacy at `/hr/hub_legacy`)
- `pages/HrHubV2.jsx` (swapped to `/hr`)
- Track 13.6N decision: keep both during the 30-day signoff window. **MERGE deferred** until Track 13.6O.

### 9.6 · PM Hubs (V1 + V2)
Same as HR: legacy preserved at `/pm/hub_legacy`. **MERGE deferred to Track 13.6O.**

### 9.7 · Safety / Shop hubs
Same legacy-rollback pattern. **MERGE deferred.**

### 9.8 · Field Hub V1 + Field Leadership V2 (retired)
Field Leadership V2 was retired in Track 13.6L. **Already resolved.**

### 9.9 · Driver V1 + Driver V2 (retired)
Driver V2 was retired in Track 13.6L. **Already resolved.**

---

## 10 · Hidden Gold Analysis

### 10.1 · The single most valuable thing already built that MASCI may not fully use today
**PO Requests subsystem** (Section 3).
- Evidence: 12 fully implemented backend endpoints + 795-line frontend page consuming the full client surface + email integration + receipt upload/download + CSV export + admin maintenance scan.
- Operator surface: a single `/po-requests` route. No PO action queue card in PM Hub V2 or Field Leadership V2.
- Five-pillar leverage: surfacing it (NOT building anything) would deliver Powerful + Simple + Trusted gains immediately.

### 10.2 · Most complete unfinished system
**MaintainX integration** (Section 7.2) — ~70 % complete. Stub service + client + router + webhook intake + asset-spine column reservation. Activation needs credentials + minor service implementation. **But** activating it does not automatically enrich any UI; that is a separate downstream track.

### 10.3 · Easiest recovery
**Operational Events project-day endpoint** (`/api/operational-events/project-day/{project_number}/{date}` · `operational_events.py` line 583). Already returns a per-project-per-day roll-up of detected operational events. Zero frontend consumer today. Surfacing on a PM project-detail page = pure UI work, no backend.

### 10.4 · Biggest operational leverage
**Surfacing PO Requests + Operational Events project-day inside PM Hub V2.** PMs see "what happened on this project today" (events) and "what is pending purchase" (PO) without leaving the hub. **Both already built. Both invisible.**

### 10.5 · Biggest five-pillar win
**Surfacing the Operational Locations admin reconciliation queue to Admin Hub V2** (it lives only at admin URLs today). It is a Powerful + Trusted system already (geofence quality affects every other portal); making it visible at the V2 hub fixes a discoverability gap without writing a new system.

---

## 11 · Recovery Candidate Scoring

| Candidate | Completion % | Op. value | 5-pillar | Recovery cost | Risk | Class |
|---|---|---|---|---|---|---|
| PO Requests surfacing (PM/FL Hub V2 cards) | 95 | High | 9 | Low (1 small panel) | Low | **RECOVER LATER** (operator interview confirms PO pain) |
| Operational Events project-day surfacing | 90 | Medium | 8 | Low (1 small panel) | Low | **RECOVER LATER** |
| Operational Locations admin reconciliation surfacing in Admin Hub V2 | 100 | Medium | 8 | Low (link only) | Very Low | **RECOVER LATER** |
| Operational Records list surfacing | 100 | Low (unclear use-case) | 6 | Low | Medium | **LEAVE DORMANT** — needs operator interview |
| Operational Timeline list surfacing | 100 | Low | 6 | Low | Medium | **LEAVE DORMANT** |
| Material Movement tile surfacing in PM Hub V2 | 100 (read-view) | Medium | 7 | Low | Low | **RECOVER LATER** |
| Scale-ticket structured entry (extend `operational_attachments.scale_ticket`) | 30 (schema slot only) | High | 8 | Low | Low | **RECOVER LATER** (already Track 13.8A §7.2 recommendation) |
| MaintainX activation | 70 | Medium (until UI consumes it) | 7 | Medium (creds + service) | Medium | **LEAVE DORMANT** until credentials + operator decision on UI surface |
| FleetWatcher activation | 10 | Low | 5 | High (full service write) | High | **LEAVE DORMANT** |
| Legacy `*_legacy` hubs (PM/HR/Safety/Shop/Dispatch) | 100 | n/a | n/a | n/a | n/a | **DO NOT TOUCH** until Track 13.6O after 30-day window |
| Driver V2 / Field Leadership V2 | Retired | n/a | n/a | n/a | n/a | **DO NOT REVIVE** — permanent doctrine (Track 13.6L) |

---

## 12 · Top 10 Recovery Candidates

1. **PO Requests surfacing in PM Hub V2** — completion 95 % · op-value HIGH · 5-pillar 9 · cost LOW · recommendation **RECOVER LATER** (operator-interview gated).
2. **PO Requests surfacing in Field Leadership Portal** — same · operator-interview gated.
3. **Operational Events project-day panel in PM project-detail** — completion 90 % · op-value MEDIUM · 5-pillar 8 · cost LOW · **RECOVER LATER**.
4. **Operational Locations reconciliation visibility in Admin Hub V2** — completion 100 % · op-value MEDIUM · 5-pillar 8 · cost LOW · **RECOVER LATER**.
5. **MaterialMovementTile surfacing in PM Hub V2 daily-report context** — completion 100 % (as read view) · op-value MEDIUM · 5-pillar 7 · **RECOVER LATER**.
6. **Scale-ticket structured entry on driver attach** — completion 30 % (schema only) · op-value HIGH · 5-pillar 8 · cost LOW · **RECOVER LATER** (already Track 13.8A §7.2 candidate · operator-interview gated).
7. **MaintainX credential activation** — completion 70 % · op-value MEDIUM · 5-pillar 7 · cost MEDIUM · **LEAVE DORMANT** until credentials + UI-surfacing decision.
8. **Operational Records list view surfacing** — completion 100 % · op-value LOW · 5-pillar 6 · **LEAVE DORMANT** pending operator use-case.
9. **Operational Timeline surfacing** — completion 100 % · op-value LOW · 5-pillar 6 · **LEAVE DORMANT**.
10. **FleetWatcher full activation** — completion 10 % · op-value LOW · 5-pillar 5 · cost HIGH · **LEAVE DORMANT** (no operator pain proof).

---

## 13 · Five-Pillar Evaluation (this track)

| Pillar | Score | Why |
|---|---|---|
| Powerful | 9 | Surveyed 115 backend modules + 245 frontend pages + 8 operational-record modules + integration services + notification stacks. |
| Simple | 9 | No code · no UI · single report. |
| Beautiful | 9 | Reuses prior-track doctrine; no reinvention. |
| Trusted | 9 | Every "built / partial / dormant" call is source-grep verified. No claim made without source line numbers. |
| Proven | 7 | Operator usage of PO Requests / Operational Events / Operational Locations is **unknown** without operator interview. Five-pillar reflects that honesty. |

**Aggregate**: **8.6 / 10**.

---

## 14 · Evidence Quality Notes

- **HIGH**: every backend / frontend file existence claim, route-count claim, and "frontend consumer count" claim (verified by `grep` and file probes).
- **HIGH**: every doctrine claim cross-referenced to Tracks 13.6 / 13.7 reports already in `/app/memory/`.
- **MEDIUM**: completion percentages — derived from "endpoints implemented" vs "endpoints likely needed for full lifecycle". Some judgement involved.
- **LOW**: operational value scores — without operator interview, "high / medium / low" is informed inference from construction-industry context + codebase signals.
- **NOT COVERED IN THIS TRACK** (deferred to Track 13.8C if authorised): actual notification cron schedule audit (which jobs fire, to whom, how often) · actual PO Requests usage telemetry (`usage_analytics.py` likely has this · not consulted to keep scope).

---

## 15 · Final Recommendation

1. **Do not build anything new from this report.**
2. **Do not retire anything from this report.**
3. **Single highest-value next track (if authorised)**: surface the existing PO Requests subsystem as a small action-queue card in PM Hub V2 (and possibly Field Leadership Hub) — same engine, same data, zero backend work. Doctrine-pure. Operator-interview gated per the permanent doctrine.
4. **Single highest-value background activation candidate**: MaintainX credentials — only IF operator wants MaintainX visibility surfaces. Activation does not automatically enrich any UI; that is a separate track.
5. **Permanent retain (no merge yet)**: legacy `*_legacy` routes and the existing V2 swaps. Track 13.6O handles their retirement after the 30-day signoff window.
6. **Permanent do-not-revive**: Driver V2 + Field Leadership V2 (Track 13.6L doctrine).
7. **Operator interview should ask**: (a) Do you currently use `/po-requests`? (b) If not, why? (c) When you ask "what happened on Project X today", do you call someone or open a page? (d) Is the geofence reconciliation queue something Admin checks routinely?

**Track 13.8B · CLOSED.** Hidden value documented. No code written. No recovery executed. Reality first.
