# Track 18.00 · Transportation Operations 2.0 — Master Platform Unification

**Status:** 📐 ARCHITECTURE PROPOSAL · AWAITING APPROVAL · ZERO CODE WRITTEN
**Date:** 2026-02-10
**Doctrine:** Reorganize the experience, never the business logic.
**Source of truth:** Track 17.00 platform-wide audit
(`/app/memory/TRACK_17_00_PLATFORM_WIDE_TRUCKING_TRANSPORTATION_AUDIT.md`).

---

## 0 · One-line summary

Wrap every existing transportation, dispatch, fleet, orientation,
intelligence, automation, and cleanup surface inside a single
**Transportation Operations** parent shell — one nav, one header,
one timeline engine, one search bar — without touching backend
business logic, schemas, RBAC, or Dispatch lifecycle code.

---

## 1 · Six-pillar alignment (the bar)

Every decision below has been pressure-tested against these:

| Pillar | What it means here |
|---|---|
| **Powerful** | All 110 transportation endpoints + 68 dispatch endpoints + 15 fleet endpoints remain accessible. Nothing loses capability. |
| **Simple** | One landing page. One nav. Five-second readiness comprehension. Progressive disclosure. |
| **Beautiful** | One consistent page template (Header · Health · Quick Actions · Body · Timeline · Audit). No visual drift. |
| **Trusted** | Every value is composed from existing engines. Source-of-truth ownership is documented. RBAC unchanged. |
| **Proven** | 600+ existing regression tests stay green. Every existing UI continues to work at its existing URL. |
| **Operational** | A dispatcher, admin, fleet manager, PM, HR rep, or safety lead can answer "what needs attention?" from any workspace within one screen. |

---

## 2 · Hard constraints (locked)

1. **No new backend collections.**
2. **No new scoring engines / business logic.**
3. **No data migrations.**
4. **No URL break.** Every existing route keeps working
   (compatibility redirects where helpful).
5. **No dispatch rewrite.** Dispatch state machine, magic-link,
   driver shift, Twilio callbacks, command center, board, ledger,
   maps — all **untouched**.
6. **No HR / Safety / PM / Operations / Shop surface rewrites.**
   Track 16.16 cross-portal read pattern is reused.
7. **Every new screen is a composer** — fetches existing
   endpoints, never duplicates logic.
8. **Tablet-first responsive.** No mobile-only chrome that breaks
   desktop. No desktop-only chrome that breaks tablet.
9. **Deployment gate stays green.** Every new test additive.

---

## 3 · Information architecture (the navigation tree)

### Parent shell

The existing `/admin/transportation/*` SPA route is the
Transportation Operations shell. The shell delivers:

* Single persistent header (logo · global search · portal
  switcher · profile)
* Single persistent left rail (workspace nav)
* Single persistent right rail (notifications · action queue
  badge)
* Single page body (the active workspace)

### Workspace tree

```
Transportation Operations  (/admin/transportation)
├── Command Center           (index — REPLACES current dashboard)
├── Dispatch                 (deep-link out to /dispatch-portal/*)
│   ├── Board                  → /dispatch-portal/board
│   ├── Command Center         → /dispatch-portal/command
│   ├── Map                    → /dispatch-portal/map
│   ├── Haul Ledger            → /dispatch-portal/haul-ledger
│   └── Driver Qualification   → /dispatch-portal/driver-qualification
├── Fleet
│   ├── Trucks list            (reuses existing TrucksList)
│   ├── Truck workspace        (reuses existing TruckWorkspace)
│   ├── Inspections            (reuses existing InspectionCenter)
│   ├── DVIR queue             (reuses existing DVIR routes)
│   └── Fleet visibility       (reuses existing FleetVisibility scope="admin")
├── Drivers
│   ├── Drivers list           (reuses existing DriversList)
│   ├── Driver workspace       (reuses existing DriverWorkspace)
│   └── HR driver qualification (link out → /hr/driver-qualification)
├── Carriers
│   ├── Carriers list          (reuses existing CarriersList)
│   ├── Carrier workspace      (reuses existing CarrierWorkspace)
│   └── External invites       (reuses existing invite mgmt)
├── Compliance
│   ├── Compliance dashboard   (reuses existing ComplianceDashboard)
│   ├── Documents queue        (reuses existing DocumentCenter)
│   ├── Eligibility states     (reuses existing eligibility v2)
│   └── Rate schedules         (reuses existing RateScheduleCenter)
├── Orientation
│   ├── Modules                (reuses existing OrientationCenter)
│   ├── Assignments
│   ├── Certificates
│   └── Public invites         (link to admin invite mgmt)
├── Intelligence
│   ├── Executive dashboard    (reuses existing IntelligenceCenter)
│   ├── Operational health
│   ├── Driver intel
│   ├── Carrier intel
│   ├── Truck intel
│   ├── Recommendations
│   ├── Predictions
│   └── Dispatch learning
├── Automation
│   ├── Automation runs        (reuses Track 16.10)
│   ├── Forecast
│   ├── Command digest
│   └── HR sync                (reuses Track 16.11A)
├── Cleanup
│   ├── Signals list           (reuses Track 16.15 Cleanup Companion)
│   └── Action items           (reuses transport_action_items queue)
├── Operations                 (cross-portal awareness — Track 16.16 mirror)
│   ├── Project readiness      (composed view of all Track 16.16 widgets)
│   └── Operations bridge      (links into PmCommandCenter, OperationsCenterCommand)
├── Reports                    (reuses existing ReportsView)
└── Administration
    ├── Audit timeline         (reuses existing AuditTimeline)
    ├── Email routes           (reuses Track 16.05)
    └── Settings
```

### Why this tree (not the current 13 flat tabs)

* The current nav is **13 flat tabs**: Dashboard · Carriers ·
  Drivers · Trucks · Compliance · Documents · Inspections ·
  Orientation · Command Queue · Intelligence · Rate Schedules ·
  Audit · Reports. All equal weight.
* The proposed tree clusters by **operator mental model**:
  - *Who* the operator works on (Drivers · Carriers · Fleet)
  - *What* the operator is doing (Dispatch · Compliance ·
    Orientation · Cleanup)
  - *Why* the operator is looking (Intelligence · Operations)
  - *How* the system runs (Automation · Reports · Administration)
* Dispatch becomes a **first-class workspace** with deep links
  back to the existing Dispatch portal — Dispatch URLs do not
  change.

---

## 4 · Universal page template (the design language)

Every workspace renders the **same skeleton**:

```
┌───────────────────────────────────────────────────────────────┐
│ HEADER STRIP                                                  │
│  • Workspace title + entity context                           │
│  • Health chip(s)  • Quick action(s)  • "View related →"      │
├───────────────────────────────────────────────────────────────┤
│ BRIEF / SUMMARY (top-of-fold)                                 │
│  • 3–6 tiles · count-based · operator-first                   │
├───────────────────────────────────────────────────────────────┤
│ BODY                                                          │
│  • Workspace-specific (list, drawer, drilldown, timeline)     │
├───────────────────────────────────────────────────────────────┤
│ RIGHT RAIL (sticky)                                           │
│  • Action Queue (workspace-scoped)                            │
│  • Related Records                                            │
│  • Operational Insights (recent activity)                     │
└───────────────────────────────────────────────────────────────┘
```

Implementation: one new shared component
`TransportationWorkspaceShell` that wraps existing pages with
header + brief + right rail. Existing page bodies render
unchanged inside the shell.

---

## 5 · Universal services

These are **single-implementation** services exposed to every
workspace.

### 5.1 · Global transportation search

A single search-bar component mounted in the header. Search
target = local index of:

* Drivers (`transport_persons` · `transport_employees`)
* Carriers (`carriers`)
* Trucks (`transport_trucks`) — by unit · VIN
* Projects (`projects`) — by project_number
* Assignments (`dispatch_assignments`)
* Certificates (`transport_certificates`)
* Documents (`carrier_documents` · `driver_documents`)

**Implementation strategy:** add ONE thin read-only composer
endpoint `GET /api/admin/transportation/search?q=...` that
fans out to existing collections with a 500ms debounce + limit.
NO new index, NO new collection — direct queries with sensible
`$regex` projections. (≈ 60 LOC.)

### 5.2 · Universal timeline

Already exists. `transport_intelligence_audit` +
`audit_events` + `transport_dispatch_recommendation_audit` +
`email_routing_audit_v2` are aggregated by the existing
`/api/admin/transportation/audit-timeline` endpoint (Track 16.07).
Every workspace right-rail consumes this **unchanged**.

A new **per-entity timeline drawer** reuses the existing
`/api/admin/transportation/timeline/{entity_type}/{entity_id}`
endpoint (Track 16.07) — already supports `carrier`, `driver`,
`truck`. **Zero new backend.**

### 5.3 · Universal relationships

When viewing **Driver X**, the right rail loads one composer
call that returns:

* dispatch assignments (last 10) — `dispatch_assignments`
* current truck assignment (if active)
* carrier of record
* HR linkage (`transport_employees` projection)
* orientation status (`transport_orientation_assignments`)
* certificates (`transport_certificates`)
* documents (`driver_documents`)
* safety holds (existing safety eligibility)
* intelligence score (Track 16.12 cached payload)
* cleanup mentions
* recent audit rows

**Implementation:** ONE new thin composer endpoint
`GET /api/admin/transportation/related/{entity_type}/{entity_id}`
that wraps existing queries (no new business logic). Same
pattern for `carrier` and `truck` entity types.

### 5.4 · Universal action queue

Already exists — `transport_action_items` (Track 16.10) is
already the queue for cleanup actions + automation tasks. Every
workspace right rail filters this queue by workspace scope.
**Zero new backend.**

### 5.5 · Notifications

Already exists — `transport_notifications` + the existing
NotificationBell. Reused unchanged.

---

## 6 · Workspace specs (composition only)

### Workspace 0 · Command Center (index)

**Goal:** answer in 5 seconds — *Is Transportation healthy?*

**Composition (no new endpoints):**

* **Top strip:** Overall band chip (from Track 16.16 composer,
  reused).
* **Health quartet:** Driver / Truck / Carrier / Dispatch
  readiness bands (Track 16.16 composer).
* **Operational tiles (4):** Pending reviews · Expiring 30d ·
  Blocked dispatch · Open action items (Track 16.16 composer).
* **Risk banner:** Track 16.16 risk list (silent when healthy).
* **Top cleanup signal:** existing `TopCleanupOpportunityCard`
  (Track 16.15A) — already wired.
* **Active operations widget:** count of active hauls today +
  link to Dispatch Board — uses
  `/api/dispatch/lifecycle/states` (existing).
* **Intelligence highlights:** top 3 recommendations from
  `/api/admin/transportation/intelligence/recommendations` (existing).
* **Morning brief:** one-line summary from existing command
  digest (Track 16.10A).
* **Recent activity feed:** last 10 rows from
  `/api/admin/transportation/audit-timeline` (existing).

**Net new code:** 1 shell component + 1 layout composer (no
backend). All data sourced from existing endpoints.

### Workspace 1 · Dispatch

Deep-link panel that **embeds nothing** but provides:

* Brief: live dispatch readiness + blocked count + active hauls
  (existing endpoints).
* Quick links into the existing Dispatch portal (Board · Command
  Center · Map · Haul Ledger · Driver Qualification).
* Recent dispatch activity (from `dispatch_state_events`).
* Recommendation summary (from
  `/api/dispatch/recommendation` if dispatch token present).

**Dispatch URLs do not change.** `/dispatch-portal/*` remains
authoritative for live dispatch work.

### Workspace 2 · Fleet

Reuses existing TrucksList + TruckWorkspace + InspectionCenter
inside the shared shell. Adds **right-rail relationships** via
the new `related/truck/{id}` composer.

### Workspace 3 · Drivers

Reuses existing DriversList + DriverWorkspace inside the shared
shell. Adds right-rail relationships via `related/driver/{id}`.

### Workspace 4 · Carriers

Reuses existing CarriersList + CarrierWorkspace inside the
shared shell. Adds right-rail relationships via
`related/carrier/{id}`.

### Workspace 5 · Compliance

Reuses existing ComplianceDashboard + DocumentCenter +
RateScheduleCenter under one nav child. **Zero new code.**

### Workspace 6 · Orientation

Reuses existing OrientationCenter unchanged.

### Workspace 7 · Intelligence

Reuses existing IntelligenceCenter unchanged.

### Workspace 8 · Automation

Reuses existing automation surfaces from `_command_queue.jsx`
+ HR sync widget unchanged.

### Workspace 9 · Cleanup

Reuses existing Cleanup Companion (Track 16.15) +
`TopCleanupOpportunityCard` (Track 16.15A).

### Workspace 10 · Operations

Reuses existing Track 16.16 widgets
(`TransportationReadinessCard` ·
`OperationsTransportationHealthWidget` ·
`TransportationCloseoutAwareness`) — they already render
inside other portals. This workspace is the **single
admin-side mirror** of those PM/Operations awareness widgets,
so an admin can see what PMs see.

### Workspace 11 · Reports

Reuses existing ReportsView unchanged.

### Workspace 12 · Administration

Reuses existing AuditTimeline + Track 16.05 email routes +
existing dispatch user management (link to `/admin/dispatch`).

---

## 7 · Cross-module integration matrix

Where Transportation surfaces inside other portals:

| Consumer portal | Surface | Mount point | Source | Net new code |
|---|---|---|---|---|
| PM portal | Readiness card + risk banner + closeout | `PmProjectDetail.jsx` | Track 16.16 composer | none (already shipped) |
| PM Command Center | Health widget | Overview tab | Track 16.16 composer | none (already shipped) |
| Operations Center | Health widget | Below Project Health | Track 16.16 composer | none (already shipped) |
| HR portal | HR readiness chip on employee drawer | `HrEmployees.jsx` | Track 16.11A (`/admin/hr/transportation-readiness`) | none (already shipped) |
| Safety portal | Safety driver hold view | `/safety-portal/driver/:driverKey` | existing eligibility gate read | none (already shipped) |
| Shop portal | Fleet visibility | `/shop/fleet` | existing FleetVisibility | none (already shipped) |
| Dispatch portal | Decision surface drawer | `/dispatch-portal/board` | Track 16.13 | none (already shipped) |

**Conclusion:** all cross-portal integrations already exist
following the Track 16.11A / 16.16 read-only composer pattern.
Nothing new needed.

---

## 8 · Source-of-truth matrix

For every entity, who writes and who reads:

| Entity | Writer (single) | Readers (many) |
|---|---|---|
| Carrier master | Transportation Compliance Center (`/api/admin/transportation/carriers`) | Dispatch · Intelligence · Cleanup · PM (via 16.16) · HR (via 16.11A) |
| Driver master | Transportation Compliance Center | Dispatch · Intel · Cleanup · HR · Safety |
| Truck master | Transportation Compliance Center | Dispatch · Intel · Cleanup · Shop · Fleet |
| Eligibility state | Track 16.06 recompute + Track 16.09 gate | Everyone read |
| Documents | Compliance Center + carrier invite portal | Compliance · Cleanup |
| Truck inspections | Compliance Center + Fleet DVIR | Compliance · Dispatch readiness · Cleanup |
| Orientation modules | Compliance Center (Track 16.08) | Orientation Center · invite portal |
| Orientation assignments | Compliance Center + carrier invite portal | Orientation Center · public certificate |
| Certificates | Track 16.08 (issued) | Public verify · Orientation Center |
| Dispatch assignments | DispatchCommandCenter + lifecycle routes | Read-only mirrors in Track 16.13 decision surface |
| Dispatch state events | Dispatch lifecycle | Timeline · audit |
| Dispatch overrides | Track 16.09 (create) + admin (revoke) | Compliance Center · Cleanup |
| Action items | Track 16.10 + Track 16.15 materializer + Track 16.11A sync | Command Queue · Cleanup · Workspace right rail |
| Automation runs | Track 16.10 scheduler | Automation workspace |
| Command digest | Track 16.10A | Administration |
| HR sync runs | Track 16.11A scheduler | Automation workspace |
| Intelligence audit | Track 16.12 + 16.13 | Intelligence workspace + Learning loop |
| Email routing audit | Track 16.05 | Administration · email-routes view |
| Audit events (unified) | every domain mutator | Universal timeline · Right rail |

**Lock:** **Transportation Operations 2.0 introduces ZERO new
writers.** Every new screen reads only.

---

## 9 · Deep-link strategy

Every workspace exposes deep links so QA / product / scripts
can route directly without manual nav:

```
/admin/transportation                                  (Command Center)
/admin/transportation/dispatch
/admin/transportation/fleet/trucks
/admin/transportation/fleet/trucks/:id
/admin/transportation/fleet/inspections
/admin/transportation/drivers
/admin/transportation/drivers/:id                      (existing)
/admin/transportation/carriers                         (existing)
/admin/transportation/carriers/:id                     (existing)
/admin/transportation/compliance
/admin/transportation/compliance/documents             (was /documents)
/admin/transportation/compliance/rate-schedules        (was /rate-schedules)
/admin/transportation/orientation/*                    (existing)
/admin/transportation/intelligence/*                   (existing)
/admin/transportation/automation
/admin/transportation/automation/runs
/admin/transportation/automation/digest
/admin/transportation/automation/hr-sync
/admin/transportation/cleanup                          (was /intelligence/cleanup)
/admin/transportation/operations
/admin/transportation/reports                          (existing)
/admin/transportation/administration/audit             (was /audit)
/admin/transportation/administration/email-routes
/admin/transportation/administration/settings
```

**Compatibility redirects** (zero-break):

* `/admin/transportation/documents` → `/admin/transportation/compliance/documents`
* `/admin/transportation/inspections` → `/admin/transportation/fleet/inspections`
* `/admin/transportation/rate-schedules` → `/admin/transportation/compliance/rate-schedules`
* `/admin/transportation/command-queue` → `/admin/transportation/automation/runs`
* `/admin/transportation/audit` → `/admin/transportation/administration/audit`
* `/admin/transportation/intelligence/cleanup` → `/admin/transportation/cleanup`

All implemented via React Router `<Navigate replace>` — no
backend changes, no broken bookmarks.

---

## 10 · Performance budget (per workspace)

| Budget | Target |
|---|---|
| First contentful paint | < 1.5 s |
| Time to readiness chip | < 1.5 s (server-side cold) |
| Right-rail relationships | < 800 ms (composer) |
| Search debounce | 500 ms |
| Workspace switch (already-loaded shell) | < 200 ms |
| Total parallel requests per workspace | ≤ 4 |

**Enforcement:** module-level shared cache (proven by Track
16.16's 30s in-memory cache) for the readiness envelope.

---

## 11 · RBAC mapping

* Parent shell + all workspaces inside `/admin/transportation/*`
  remain **admin-only** (existing `require_admin_dep` gate).
* Cross-portal awareness widgets continue to use
  `make_require_any_portal_token` (Track 16.16 pattern).
* Dispatch deep links still require dispatch portal auth on
  arrival — Transportation Operations does not bypass dispatch
  RBAC.
* The new search + related composers are admin-only.
* **No new role tokens.** No new RBAC paths.

---

## 12 · Phased implementation roadmap

**Architecture is approved → implementation begins, never
before.**

### Phase A · Universal shell (small · isolated)

* Build `TransportationWorkspaceShell` component (Header · Brief
  · Body slot · Right Rail).
* Wrap existing `_views.jsx` `TransportationDashboard` in the
  shell.
* Land compatibility redirects.
* **Net new code:** ~150 LOC. **Net new backend:** 0.
* **Tests:** 8 regression tests (shell renders · redirects work
  · all old testids preserved · admin-only · zero new endpoint).

### Phase B · Command Center upgrade (medium · isolated)

* Compose existing widgets into the new Command Center
  layout (Track 16.16 envelope + Track 16.15A card + existing
  recommendation list + automation digest preview).
* **Net new code:** ~250 LOC frontend. **Net new backend:** 0.
* **Tests:** 10 tests (composition · testids · band logic ·
  performance bound).

### Phase C · Universal search (medium · isolated)

* One thin composer endpoint
  `GET /api/admin/transportation/search?q=...`.
* Header search bar component + result drawer.
* **Net new code:** ~200 LOC frontend + ~60 LOC backend.
* **Tests:** 8 tests (RBAC · indexes used · debounce · no new
  collection).

### Phase D · Universal relationships (medium · isolated)

* One thin composer endpoint
  `GET /api/admin/transportation/related/{entity_type}/{entity_id}`.
* Right-rail "Related Records" component for Driver / Truck /
  Carrier workspaces.
* **Net new code:** ~250 LOC frontend + ~100 LOC backend
  (composer only).
* **Tests:** 12 tests.

### Phase E · Nav reshape + deep-link compat (small · isolated)

* New nav clusters (Fleet · Drivers · Carriers · Compliance ·
  Automation · Cleanup · Operations · Administration).
* Compatibility redirects for old URLs.
* **Net new code:** ~120 LOC. **Net new backend:** 0.
* **Tests:** 10 tests (every old URL still navigable; every new
  URL renders correct workspace).

### Phase F · Dispatch workspace bridge (small · isolated)

* New `Dispatch` workspace inside Transportation Operations
  with brief + deep links + recent activity.
* No changes to `/dispatch-portal/*`.
* **Net new code:** ~150 LOC. **Net new backend:** 0.
* **Tests:** 8 tests (deep links route correctly · dispatch
  portal unchanged).

### Phase G · Operations workspace mirror (tiny · isolated)

* New `Operations` workspace inside Transportation Operations
  that renders the three Track 16.16 widgets so admins see
  what PMs see.
* **Net new code:** ~80 LOC. **Net new backend:** 0.
* **Tests:** 6 tests.

### Phase H · Polish + governance (small · isolated)

* Loading skeletons across the shell.
* Keyboard shortcuts (`/` opens search · `g d` goes to
  Dashboard · etc.).
* Telemetry: which workspace is most used.
* **Net new code:** ~120 LOC. **Net new backend:** 0.
* **Tests:** 6 tests.

**Total budget (≈ Phase A → H):** ~1,300 LOC frontend + ~160
LOC backend (only 2 thin composer endpoints: search + related).

**No collections. No scoring. No new audit kinds. No new RBAC.**

---

## 13 · Testing discipline (regression-first)

* Every phase ships with its own
  `test_track_18_xx_*.py` regression file.
* Wired into `/app/scripts/deployment_gate.py`.
* **Mandatory smoke:** every existing transportation testid
  (`tx-*`, `ops-tx-*`, `pm-project-tx-*`, dispatch tests, HR
  driver-qualification, fleet visibility) must continue to
  resolve.
* **Mandatory live test:** `testing_agent_v3_fork` after each
  phase, cross-portal (admin · pm · dispatch · hr) to confirm
  nothing regressed.
* **Pre-existing flakes accepted as-is:** the Track 15.79B test
  pollution is not in scope here.

---

## 14 · Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| URL bookmark break for existing admins | Med | Compatibility redirects in Phase E (every old URL still resolves) |
| Dispatch operators lose their muscle memory | High | Dispatch URLs do NOT change. Transportation Operations is additive nav, never a replacement |
| Shell increases page weight | Med | Lazy-load every workspace · share Track 16.16 cache · no new backend on Command Center |
| Cross-portal token cleared during navigation | Low | Already solved by existing `EnforcePortalScope` + `useTransportationReadiness` cache |
| Search performance degrades | Low | Limit 25 results · 500ms debounce · indexes already exist on `transport_persons.name` · `carriers.name` · `transport_trucks.unit_number` |
| Regression in any prior test | Critical | Phase-by-phase regression; do not begin next phase until current phase deployment-gate green |

---

## 15 · Acceptance criteria (program-level)

The program is done when **all** of these hold:

* [ ] An admin lands on `/admin/transportation` and sees a single
      Command Center that answers Transportation health in 5
      seconds.
* [ ] The 13 workspaces all share the same shell, header, search,
      right rail.
* [ ] Every existing transportation URL still resolves
      (compatibility redirects in place).
* [ ] Dispatch URLs are unchanged and dispatch lifecycle code is
      untouched.
* [ ] HR / Safety / PM / Operations / Shop continue to see their
      existing Track 16.16 / 16.11A widgets unchanged.
* [ ] Driver workspace shows related dispatch / truck / carrier
      / HR / orientation / certificates / documents / safety /
      intelligence / cleanup in one right-rail.
* [ ] Truck workspace shows related driver / carrier / dispatch
      / maintenance / DVIR / inspection / intelligence.
* [ ] Carrier workspace shows related drivers / fleet / insurance
      / packets / orientation / dispatch / performance.
* [ ] Global search returns drivers · carriers · trucks · VIN ·
      unit · projects · assignments · loads · certificates ·
      documents · orientation · inspections.
* [ ] Universal timeline contributes from every module.
* [ ] Every phase has regression tests; deployment gate green.
* [ ] No new collections; no new scoring; no new RBAC paths.

---

## 16 · Decisions required from product / leadership

Before Phase A begins, please confirm:

1. **Landing URL** — keep `/admin/transportation` as the
   Transportation Operations root? (Recommendation: yes.)
2. **Search composer endpoint** — admin-only, or cross-portal
   read like Track 16.16? (Recommendation: admin-only — search
   touches PII like driver names.)
3. **Compatibility-redirect retention period** — keep
   redirects forever, or sunset after 12 months? (Recommendation:
   keep forever — they cost nothing.)
4. **Phase order** — start with Phase A (shell) or jump to
   Phase B (Command Center upgrade) for a fast visible win?
   (Recommendation: Phase A → B in order so the shell exists
   before content drops into it.)
5. **Dispatch workspace** — embed dispatch live data, or only
   deep-link out? (Recommendation: deep-link only — preserves
   dispatch as the operational system of record.)

---

## 17 · Final word

This document is the entire blueprint. Once approved, each
phase ships independently with its own regression file and
deployment-gate green. The implementation is intentionally
small per phase, large in aggregate — exactly because **the
hard work was already done across Tracks 16.04 → 16.16**. This
program is a thin, intentional re-skin that unifies them into
one operating system without disturbing a single line of the
business logic underneath.

**Awaiting approval to begin Phase A.**
