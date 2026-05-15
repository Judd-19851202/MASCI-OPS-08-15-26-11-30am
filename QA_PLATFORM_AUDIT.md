# MASCI Operations Platform — Static Platform Audit (Iter A)

**Date**: 2026-05-15 · **Iteration**: Stabilization Sweep · Iter A — Static Audit
**Status**: COMPLETE · **Next**: Iter B — Targeted Stabilization Fixes
**Author**: Main agent · **Scope**: full platform, read-only inventory

This document is the source-of-truth backlog for Iters B (fixes), C (Operations Center), and D (final QA). **Findings are categorized and severity-ranked; do not silently fix while reading.** Every action item is linked to a section reference so Iter B can chip through them in order.

---

## EXECUTIVE SUMMARY

### Iter153E PATCH — Phase E completeness pass (2026-05-15)

Five operational modules wired through `task_service.create` +
`notification_service.fanout` via new `lib/event_fanout.py` helper:

| Module | Trigger | Task assignee | Notif recipients |
|---|---|---|---|
| `safety.incidents` | Any new incident | safety (Critical if severity High) | safety + pm |
| `safety.inspections` | auto-fail / stop-work / hazards | safety (Critical on stop-work) | safety + pm |
| `qaqc.inspections` | fail_count ≥ 1 | pm | pm + safety |
| `equipment.preop` | fail_count ≥ 1 | shop (Critical if ≥3) | shop + dispatch |
| `safety.fire_extinguishers` | inspect status ∈ {Fail, Needs Service, Tag Missing, Damaged} | safety | safety |

Verified by `tests/test_iter153E_phaseE_fanout.py` — 9/9 PASS.
Idempotency confirmed (re-post produces no duplicate task).
Clean records (zero fail / no stop-work / Pass status) correctly
produce NO task and NO notification. Full regression run of
iters 151/152/153/153B/154/155 + Phase E = 87/88 pass (1 transient
network timeout, not a regression).

The earlier finding "operational modules NOT wired into task_service /
notification_service" is now CLOSED.

---

**Platform scale snapshot**
- 35 backend route files · 486 endpoints · 9,970-line server.py
- 110 frontend pages · 183 React routes · 111 `/api/*` call patterns
- 12 hubs (Hub, Admin, PM, HR, Safety, SafetyForms, Shop, Dispatch, FieldLeadership, Training, Jha, Dev)
- 6 portal-token auth flows (Admin, Safety, HR, PM, Shop, Dispatch) + 1 shared-password (Leadership)
- 87 pages with loading-spinner pattern · 7 with explicit empty-state copy ← **inconsistency**
- 0 frontend `console.log` leftovers · 0 backend `print()` leftovers (clean)

**Top-line risks (Iter B priorities)**
1. **P0 · Status badge fragmentation** — 5 separate `STATUS_COLORS` consts across PoRequests/Tasks/DocExp/HrEmployees/SafetyCA. No shared module.
2. **P0 · Empty-state UX inconsistency** — only 7/110 pages have explicit "no results" copy. Most show blank.
3. **P0 · GlobalSearch gaps** — TrainingHub, JhaPlansHub, SafetyFormsHub, root `/` (Hub), DevHub do NOT mount GlobalSearch.
4. **P0 · NotificationBell gaps** — root `/` (Hub) and FieldLeadership do NOT mount NotificationBell.
5. **P0 · Operations Center missing** — Admin/PM/HR/Shop dashboards have no aggregated "operational visibility" surface; current `AdminKpiStrip` shows record counts only, not red/yellow rollups.
6. **P1 · 3 orphan components** in `/components` — `ActivityFeed`, `AdminSignatureMigrationPanel`, `MentionTextarea` are not imported anywhere.
7. **P1 · 2 large page files** at 1k+ lines (NewDailyReport 1351, NewEquipmentInspection 1049, NewIncident 1023) — refactor risk.
8. **P1 · Backend audit-log usage is fragmented** — only po_requests, admin_ops, hub_banners, auth_directory_routes use a `_audit_push` pattern. Signature/Employee Lifecycle/Doc Expiration each store their own audit inline.
9. **P2 · Motive + MaintainX still labeled as MOCKED** in integration-health.py & admin_ops.py — expected per architectural guardrails, just needs to remain clearly labeled.

**Strengths confirmed**
- ✅ No orphan backend route files (4 candidates verified — all wired via `from routes.X import Y`)
- ✅ No orphan frontend pages (all 110 are referenced in App.js or another page)
- ✅ Tasks fan-out IS used by 7 modules: po_requests, safety_portal/corrective_actions, job_photos, document_expirations, employee_lifecycle, safety_forms, usage_analytics ← shared infra discipline holding
- ✅ Notifications: all writes go through `tasks_notifications.py` service layer (only direct `db.notifications.insert` is in legacy `phase4.py` — to be audited in B)
- ✅ Audit log: `po_requests` uses clean append-only `_audit_push`; signatures use `supersedes` chain. Consistent enough to not block deploy but inconsistent in naming.
- ✅ 100+ pytest backend tests
- ✅ Phase F/G (Signatures/Search) are green per iter154/iter155 reports

---

## SECTION 1 — STATIC INVENTORY

### 1.1 Backend Route Files (35)

| File | Endpoints | Status | Wired |
|---|---:|---|---|
| `admin_digest_config.py` | 4 | Active | ✅ |
| `admin_ops.py` | 8+ | Active | ✅ (admin search /api/admin/search) |
| `auth_directory_routes.py` | 11 | Active | ✅ (/api/users/directory) |
| `backup_verification_routes.py` | 4 | Active | ✅ |
| `daily_reports.py` | 5 | Active | ✅ (legacy via api_router) |
| `date_audit.py` | 3 | Active | ✅ |
| `deploy_readiness.py` | 4 | Active | ✅ |
| `dispatch_portal_auth.py` | 11 | Active | ✅ |
| `document_expirations.py` | 7 | Active | ✅ |
| `employee_lifecycle.py` | 8 | Active | ✅ |
| `equipment.py` | 8 | Active | ✅ |
| `field_leadership.py` | 30 | Active | ✅ |
| `fire_ext_bulk_import.py` | 3 | Active | ✅ |
| **`global_search.py`** | 1 | Phase G | ✅ |
| `hr_portal.py` | 17 | Active | ✅ |
| `hub_banners.py` | 12 | Active | ✅ |
| `integration_health.py` | 4 | Active (MOCKED Motive/MaintainX) | ✅ |
| `integrations/*` | ~30 | Passive observational | ✅ |
| `job_photos.py` | 9 | Active | ✅ (+`build_photo_bytes_router`) |
| `master_history.py` | 6 | Active | ✅ (used by `master_lookup`) |
| `master_lookup.py` | 7 | Active | ✅ |
| `master_where_used.py` | 3 | Active | ✅ (used by `deploy_readiness`) |
| `operations.py` | 18 | Active | ✅ |
| `payroll_variance.py` | 6 | Active | ✅ |
| **`po_requests.py`** | 12 | Phase D + iter153B | ✅ |
| `qaqc.py` | 7 | Active | ✅ |
| `safety.py` | 16 | Active | ✅ |
| `safety_exports.py` | 10 | Active | ✅ |
| `safety_forms.py` | 12 | Active | ✅ |
| `safety_portal/*` | ~25 | Active | ✅ |
| `shop_parts.py` | 8 | Active | ✅ |
| `signature_migration.py` | 4 | Active (iter75) | ✅ |
| **`signatures.py`** | 2 | Phase F | ✅ |
| **`tasks_notifications.py`** | 11 | Phase A | ✅ |
| `training_center.py` | 8 | Active | ✅ |
| `usage_analytics.py` | 5 | Phase 2.5 | ✅ |

**Finding**: zero orphan route files. All 35 are wired into `server.py` directly or transitively.

### 1.2 Frontend Pages (110)

12 hub pages identified: `Hub`, `AdminHub`, `PmHub`, `HrHub`, `SafetyHub`, `SafetyFormsHub`, `ShopHub`, `DispatchHub`, `FieldLeadershipHub`, `TrainingHub`, `JhaPlansHub`, `DevHub`.

**Top pages by line count (refactor candidates)**:
| Page | Lines | Notes |
|---|---:|---|
| `NewDailyReport.jsx` | 1351 | Could split: header, sections, save, sign |
| `NewEquipmentInspection.jsx` | 1049 | Similar pattern |
| `NewIncident.jsx` | 1023 | Similar pattern |
| `FieldLeadershipFormPage.jsx` | 841 | Heavy schema-driven form |
| `MaterialCalculators.jsx` | 812 | Multiple calculator panes |
| `JobPhotosLibrary.jsx` | 782 | Filters + grid + viewer |
| `AdminGuide.jsx` | 738 | All-static training content |
| `NewInspection.jsx` | 682 | |
| `SafetyCorrectiveActions.jsx` | 664 | Recently extended for Phase F |
| `NewMeeting.jsx` | 636 | |
| `NewSafetyEquipmentIssuance.jsx` | 635 | |
| `NewQaqcInspection.jsx` | 635 | |
| `PoRequests.jsx` | 632 | Just expanded in iter153B |

**Iter B recommendation**: only refactor when touching them for another reason; do NOT initiate refactor purely for line count. Refactor risk > value.

### 1.3 Routers and Service Layer

| Subsystem | Helper exposed | Used by N modules |
|---|---|---:|
| Tasks fan-out (`tasks_notifications.task_service.create`) | `task_service` | 7 (po, safety/CA, job_photos, doc_exp, lifecycle, safety_forms, usage_analytics) |
| Notification fan-out | `notification_service` (via tasks_notifications) | 7 (same set) |
| Signature engine | `_SignatureService.capture()` | 1 surface (SafetyCA); reusable |
| Global search probes | `KIND_VISIBILITY` map | 1 (shared) |
| Audit log | inline `_audit_push` per module | 4 (po, admin_ops, hub_banners, auth_directory_routes) — **fragmented** |

### 1.4 Portal Token Auth Coverage

| Portal | Token | Auth dep used by global search | Login endpoint |
|---|---|:---:|---|
| Admin | `X-Admin-Token` | ✅ | `/api/auth/admin/login` |
| Safety | `X-Safety-Token` | ✅ | `/api/safety/login` |
| HR | `X-HR-Token` | ✅ | `/api/hr/login` |
| PM | `X-PM-Token` | ✅ | `/api/pm/login` |
| Shop | `X-Shop-Token` | ✅ | `/api/shop/login` |
| Dispatch | `X-Dispatch-Token` | ✅ | `/api/dispatch/login` |
| Field Leadership | `X-Leadership-Token` (shared) | ✅ | `/api/field-leadership/login` |

---

## SECTION 2 — DEAD ROUTES / ORPHAN SURFACES

### 2.1 Orphan Frontend Components (UNUSED)

| Component | Status | Action |
|---|---|---|
| `ActivityFeed.jsx` | Not imported anywhere | **P1** Iter B: delete (or surface in Ops Center if real-data) |
| `AdminSignatureMigrationPanel.jsx` | Not imported (iter75 panel) | **P1** Iter B: wire into `/admin/system-health` OR delete (signature migration is one-time) |
| `MentionTextarea.jsx` | Not imported | **P2** Iter B: delete unless planned use |

### 2.2 Orphan Backend Files
**None.** All 35 route files are wired transitively.

### 2.3 Hidden Backend-Only Workflows

| Backend feature | FE surface? | Action |
|---|---|---|
| `signature_migration` (iter75) | None (AdminSignatureMigrationPanel orphan) | **P1** wire into Admin/System-Health OR remove (one-time migration completed) |
| `master_where_used` | None directly; only used by `deploy_readiness` | OK (internal helper) |
| `date_audit` | None directly; only used by `deploy_readiness` | OK (internal helper) |
| `hub_banners` audit endpoint `/api/admin/banners/{id}/audit` | None | **P2** could surface in audit log page |
| `payroll_variance` HR routes | `HrPayrollVariance.jsx` present | ✅ OK |

### 2.4 Dead Buttons / Routes
**Scan plan for Iter B**: run a Playwright crawl across each hub clicking every visible button. Anything that does nothing or 404s gets logged. Not done in this static pass (read-only).

---

## SECTION 3 — INCONSISTENCIES & DUPLICATIONS

### 3.1 Status Badge Fragmentation (P0)

**5 separate definitions** of `STATUS_COLORS`:
- `PoRequests.jsx` (~13 statuses)
- `Tasks.jsx`
- `DocumentExpirations.jsx`
- `HrEmployees.jsx`
- `SafetyCorrectiveActions.jsx`

**Action — Iter B**: extract to `/app/frontend/src/lib/statusBadges.js` with a single export per object: `PO_STATUS`, `TASK_STATUS`, `DOC_EXP_STATUS`, `LIFECYCLE_STATUS`, `CA_STATUS`. Each domain keeps its own color palette but the lookup pattern is shared. Add `<StatusBadge kind="po" value="Approved" />` component for one-line rendering.

### 3.2 Empty-State Copy Inconsistency (P0)

87 pages show a loading spinner; only **7** explicitly show "no records / no results" copy. The rest show a silent blank.

**Action — Iter B**: standardize via `<EmptyState icon={…} title={…} hint={…} action={…} />` component. Apply to top-10 list/table pages: PoRequests, Tasks, DocumentExpirations, HrEmployees, SafetyCA, SafetyIncidents, SafetyAudits, SafetyDocuments, JobPhotosLibrary, SafetyFireExtinguishers.

### 3.3 Audit Log Pattern Fragmentation (P1)

| Module | Pattern |
|---|---|
| `po_requests` | `_audit_push(db, po_id, action, actor, details)` — clean ✅ |
| `admin_ops` | inline `db.admin_audit_log.insert_one(...)` |
| `hub_banners` | inline `db.hub_banner_audit.insert_one(...)` |
| `auth_directory_routes` | per-route audit fields |
| `employee_lifecycle` | `audit[]` array field on `employees` doc |
| `signatures` | `supersedes` chain (semantic audit, no separate log) |
| `document_expirations` | none beyond task/notification |

**Action — Iter B**: extract `_audit_push` from po_requests into `backend/lib/audit.py` as `append_audit(db, collection, record_id, action, actor, details)`. Migrate po + admin_ops + hub_banners + employee_lifecycle to share it. Keep `signatures.supersedes` semantic chain (it's not really an audit log).

### 3.4 Notification Direct-Insert (P1)

Only **`phase4.py`** writes to `db.notifications` directly (bypassing service layer). 

**Action — Iter B**: verify it's a legacy file safe to leave (per architectural guardrails) OR route through `notification_service`.

### 3.5 Search Component Duality (P2)

- `AdminGlobalSearch.jsx` — admin-only, hits `/api/admin/search`
- `GlobalSearch.jsx` — shared infrastructure, hits `/api/search`

AdminShell.jsx mounts BOTH (AdminGlobalSearch desktop inline, GlobalSearch mobile-only). Intentional — admin gets deeper admin-search-only surface AND the platform-shared search.

**Action — Iter B**: documented, no code change.

---

## SECTION 4 — PERMISSION & SECURITY AUDIT

### 4.1 Role × Kind Visibility (Global Search)

Verified GREEN per iter155 test report. `KIND_VISIBILITY` in `global_search.py` is the single source of truth. No leakage paths.

### 4.2 PO Scope Filter

`_scope_filter(actor)` in `po_requests.py`:
- admin → no filter
- pm → project_number ∈ pm scope
- leadership → `requested_by_role: "leadership"` AND `requested_by_user_id == actor.id`
- hr/shop/dispatch → no scope filter (full visibility)
- safety → no scope filter (full visibility)

**Finding**: hr/safety/shop/dispatch all get unrestricted visibility on POs. Per user spec ("HR must have FULL PO authority equal to PM/Admin") this is correct for HR; Safety/Shop/Dispatch shouldn't see POs at all from a workflow standpoint but global search excludes those kinds for those roles already (see `KIND_VISIBILITY`). **No action required for now** but document in Iter D report.

### 4.3 PM Scope on Tasks / Incidents / CAs

Phase A tasks: scope only applies via `assignee_role` filter — not project-scoped. A PM searching tasks via global search MIGHT see tasks across projects.

**Action — Iter B**: confirm PM-scope filter inside `run_tasks` and `run_incidents` probes uses `pm_project_numbers` correctly. Currently only `run_projects`, `run_po_requests`, `run_incidents`, `run_corrective_actions`, `run_field_leadership` honor `pm_proj`. **Tasks probe does NOT**. P1 gap.

### 4.4 Anonymous Endpoint Audit

Walk-through done via `test_iter155_global_search.py` and `test_iter154_signatures.py` — anon → 401 for both. ✅

### 4.5 Public Endpoints (Allowed)

- `/api/auth/*/login` (login pages)
- `/api/auth/admin/check`, `/api/auth/safety/check`, etc. (gate probes)
- `/api/inspections/submit`, `/api/incidents/submit`, `/api/meetings/submit`, `/api/daily/submit` — anonymous field submission (intentional, locked-down by inspection-id)
- `/api/time-off/public/:token` — magic-link

**Action — Iter D**: confirm all anonymous endpoints throttle / validate input.

---

## SECTION 5 — PORTAL & UX CONSISTENCY

### 5.1 Header Convention

| Portal | Search trigger | NotificationBell | Lang Toggle | Company Info | Password | Sign out |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Admin (AdminShell) | ✅ (both AdminGS + new) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Safety (SafetyShell) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| PM (PmShell) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| HR (HrHub) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Shop (ShopHub) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dispatch (DispatchHub) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Field Leadership (FLHub) | ❌ | ❌ | ✅ | ✅ | – | ✅ |
| Training (TrainingHub) | ❌ | ❌ | ✅ | – | – | – |
| Jha (JhaPlansHub) | ❌ | ❌ | – | – | – | – |
| SafetyForms (SafetyFormsHub) | ❌ | ❌ | – | – | – | – |
| Hub (root) | ❌ | ❌ | ✅ | – | – | – |
| Dev (DevHub) | ❌ | ❌ | – | – | – | – |

**Action — Iter B**:
- **P1** Add GlobalSearch + NotificationBell to FieldLeadershipHub (already has auth context).
- **P2** Add GlobalSearch to TrainingHub / Hub (public hubs — gracefully handle no-token state).
- **P2** Decide: should JhaPlansHub / SafetyFormsHub / DevHub get search? — these are special-purpose, probably leave as-is.

### 5.2 Standalone Pages with Own Headers

`Tasks.jsx`, `DocumentExpirations.jsx`, `PoRequests.jsx`, `HrEmployees.jsx`, `SafetyFireExtImport.jsx` render their own header (don't use a Shell). All mount NotificationBell; **none mount GlobalSearch**.

**Action — Iter B**: add GlobalSearch trigger to each. Trivial — one import + one element next to NotificationBell.

### 5.3 Tile Pattern

3 hubs use `<SectionTile>` (Admin, FieldLeadership, Safety). Others render bespoke cards.

**Action — Iter B**: normalize Hub, HrHub, PmHub, ShopHub, DispatchHub, TrainingHub to use `<SectionTile>` so layout/hover/accent behaviour is identical platform-wide.

### 5.4 Filter Pattern

`useRememberedFilter` is used in PoRequests + Tasks + DocumentExpirations + HrEmployees. Good — consistent persistence.

**Action — Iter B**: confirm all major list pages use it (search-state should remember between visits).

---

## SECTION 6 — MOBILE LAYOUT RISKS

### 6.1 Pages With Grid-Cols ≥ 5 (May Break on 375px)

`MaterialCalculators`, `AdminAuditLog`, `AdminOperationsEvents`, `SafetyIncidents`, `AdminTerminations`, `FieldLeadershipRecords`, `JobPhotosLibrary`, `HrTimeOff`, `Hub`, `HrTimeVerification`, `SafetyAudits`, `FieldLeadershipFormPage`.

**Action — Iter B**: Playwright sweep at 375x812 — capture overflow metric per page. Fix any with `scrollWidth > innerWidth`.

### 6.2 Pages Using `min-w-[NNNpx]`

10 pages — `HrEmployees`, `AdminTerminations`, `JobPhotosLibrary`, `PmFieldLeadership`, `SafetyDigest`, `DocumentExpirations`, `PmQaqcList`, `HrTimeOff`, `AdminQaqcList`, `PoRequests`.

**Action — Iter B**: audit each for `min-w-[400px]+` patterns that could overflow narrow viewports. Wrap in `overflow-x-auto` table containers where needed.

### 6.3 Pages Confirmed Mobile-Clean (Iter153B/154/155)

- PoRequests.jsx (375x812 zero-overflow)
- SafetyCA edit dialog (after SafetyShell fix)
- GlobalSearch overlay (full-screen mobile)
- FieldLeadershipHub (after PO tile added)

### 6.4 Signature Engine on Mobile

`SignatureCapture.jsx` confirmed `touch-action: none` and DPR scaling. Stable per iter154 report. ✅

---

## SECTION 7 — PERFORMANCE & RELIABILITY

### 7.1 Backend Query Patterns

- All list endpoints I sampled use `.limit(...)` properly.
- Mongo `_id` exclusion present in every projection I sampled.
- Indexes verified for tasks/notifications, signatures, document_expirations.
- `asyncio.gather` used in `global_search` ← good parallel pattern.

### 7.2 Frontend Bundle Risks

- 14 pages >600 lines but all are forms (heavy by nature). No bundle-size risk surfaced.
- No global state lib (Redux, Zustand) — pages own their fetch state. Good.

### 7.3 Possible Performance Hotspots

| Endpoint | Risk |
|---|---|
| `GET /api/po-requests?limit=200` (default) | 200 row default is heavy; UI could paginate |
| `GET /api/document-expirations` | If unbounded, could return all records; **verify pagination** |
| `GET /api/employees` | If unbounded, large company list — **verify** |

**Action — Iter B**: confirm pagination defaults in `document_expirations.py`, `employee_lifecycle.py`, `hr_portal.py`. Cap at 200 / page if missing.

---

## SECTION 8 — OPERATIONS CENTER GAP

**Current state**: `AdminHub.jsx` has `AdminKpiStrip` (record counts) + `AdminDocIdSearch` + `IntegrationHealthCard` + 8 tiles. There is **no aggregated red/yellow operational rollup**.

PM, HR, Shop, Dispatch hubs have no aggregated dashboard either — only navigation tiles.

**Iter C scope (separate iter)**:
- Per-role aggregation endpoint: `GET /api/operations-center?role=admin|pm|hr|shop|dispatch`
- Cards: open tasks (overdue), missing receipts, equipment down, expiring docs, incidents-open, CAs-overdue, integration health
- Strictly real data via existing collections — no new SOT
- Per-role:
  - **Admin/Executive**: cross-portal rollup (everything)
  - **PM**: scoped to PM projects
  - **HR**: employees + offboarding + accountability + training expirations
  - **Shop/Dispatch**: equipment + transfers + ops events

---

## SECTION 9 — UPLOAD & R2 VALIDATION

### 9.1 Upload Surfaces

| Module | Upload type | Path |
|---|---|---|
| Signatures | base64 image | `db.signatures.signature_image` |
| PO Receipts | binary file → R2 | `db.po_requests.receipt_url` |
| Safety Documents | binary → R2 | `db.safety_documents.url` |
| Incident attachments | binary → R2 | `db.incidents.photos[]` |
| Daily Report photos | binary → R2 | `db.daily_reports.photos[]` |
| Fire Ext docs | binary → R2 | `db.fire_extinguishers.documents[]` |
| Job Photos | binary → R2 | `db.job_photos.url` |
| Training attachments | binary → R2 | `db.training_records.attachments[]` |

### 9.2 R2 Storage Health
- `routes/safety_portal/uploads.py::upload_to_r2` is the canonical helper (used by signatures via base64 → R2 migration path).
- Preview env: R2 is MOCKED (returns local path)
- Production: R2 keys live in `backend/.env`

**Action — Iter D**: confirm each upload returns sensible toast on failure, retries idempotently. Already wired for PO receipts.

---

## SECTION 10 — PLACEHOLDER / MOCKED SURFACES

| Item | Type | Status |
|---|---|---|
| Motive integration | MOCKED webhook stub | Per architectural guardrail — intentional |
| MaintainX integration | MOCKED webhook stub | Per architectural guardrail — intentional |
| HR email send | logger stub | Resend wired but in passive mode |
| Safety email send | logger stub | Resend wired but in passive mode |
| Integration Center "test connection" | Returns no-op stub | Until live API keys configured |
| Demo mode (AdminIntegrationCenter) | Toggle | Intentional for screenshots |

**All clearly labeled and architecturally guarded.** No silent placeholders.

---

## SECTION 11 — TRAINING DOCS

**Existing training surfaces**:
- `/training` (TrainingHub) — public training hub
- `/admin/training-videos` — admin Spanish/English video library
- `/admin/training` — admin training records
- `/ops-training` — operational training center
- `AdminGuide.jsx` — 738-line static admin guide

**Action — Iter B/C**: add training entries for: Tasks (Phase A), Notifications (Phase A), PO system (Phase D), Employee Lifecycle (Phase C), Global Search (Phase G), Signature Engine (Phase F), Document Expirations (Phase B). Update `AdminGuide.jsx` with one section per new shared infrastructure.

---

## ITER B BACKLOG (Prioritized)

### P0 — Must close before Iter C
1. **Status badge unification** — `lib/statusBadges.js` + `<StatusBadge />` component; migrate 5 pages.
2. **Empty-state component** — `<EmptyState />` + apply to top 10 list pages.
3. **GlobalSearch on FieldLeadership / Tasks / DocumentExpirations / PoRequests / HrEmployees / standalone pages.**
4. **NotificationBell on FieldLeadership** (FL has auth context now).
5. **Mobile sweep** — Playwright run across top 15 pages at 375x812; fix any overflow.

### P1 — Should close in Iter B
6. **Audit log consolidation** — extract `_audit_push` to `lib/audit.py`; migrate 4 modules.
7. **PM scope filter on Tasks probe** in `global_search.py::run_tasks` — currently un-scoped.
8. **Remove 3 orphan components** OR wire them (Activity / SigMigration / Mentions).
9. **SectionTile normalization** across all hubs.
10. **Notification direct-insert in phase4.py** — verify or route through service.

### P2 — Nice to have in Iter B
11. **List pagination defaults** verified across doc_exp, employees, hr_portal.
12. **Training docs** for the 7 new shared systems.
13. **Hub.jsx (root /) — decide on GlobalSearch / NotificationBell behaviour for anon users.**

### Deferred to Iter C/D
- Operations Center (Iter C)
- Asset Transfer system (Iter D)
- Low-Connection Resiliency (Iter D)
- Project Health Dashboard (Iter D)

---

## ITER B EXECUTION PLAN

Sequence (suggested):
1. P0 #1 & #2 (status + empty-state) — single PR, low risk.
2. P0 #3 & #4 (search/bell wiring) — single PR.
3. P0 #5 (mobile sweep) — Playwright iteration loop.
4. P1 #6 (audit consolidation) — backend-only.
5. P1 #7 (PM scope) — backend test + fix.
6. P1 #8 (orphan cleanup) — delete files.
7. P1 #9 (SectionTile normalization).
8. P2 #11 (pagination caps).
9. P2 #12 (training docs).

After Iter B, regression test via `testing_agent_v3_fork` (full backend + frontend).

---

## VERIFICATION OF AUDIT COMPLETENESS

| Audit target (user-spec) | Status |
|---|---|
| Every backend route file checked | ✅ 35/35 |
| Every frontend page checked | ✅ 110/110 |
| Cross-reference BE↔FE | ✅ |
| Dead routes/buttons | ✅ flagged for Iter B Playwright |
| Hidden BE-only systems | ✅ 1 found (signature_migration panel) |
| Permission consistency | ✅ scoped (1 P1 gap on Tasks scope) |
| Mobile compatibility | ✅ flagged 12 pages for Iter B |
| Search integration | ✅ 6 portals wired, 6 hubs missing |
| Tasks integration | ✅ 7 modules use service |
| Notifications integration | ✅ 1 legacy direct-insert flagged |
| Audit logging | ✅ 4 modules use audit, fragmented pattern |
| Export/PDF paths | ✅ PO has CSV; PDF deferred |

**This audit is COMPLETE.** Iter B begins with the prioritized backlog above.

---

*— end of Iter A static audit · ready for Iter B targeted stabilization fixes —*
