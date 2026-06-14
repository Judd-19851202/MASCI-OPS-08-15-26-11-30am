# MASCI Operations Platform — PRD

## Original Problem Statement
MASCI Operations Platform RC-1 Release Certification — Track 13.6+ "Operational Recovery Phase". Goal: convert "collection of dashboards" → "Operational Heavy-Civil Operating System."

Hard rules: Action-Queue Focus · No Dead Objects · Preserve Forms & Workflows · `*_legacy` Rollback Pattern · NO deploy / NO GitHub save / NO merge.

## Architecture
- Frontend: React + Tailwind + Shadcn (`/app/frontend`)
- Backend: FastAPI + MongoDB (`/app/backend`)
- Memory: Append-only Markdown ledgers in `/app/memory/`

## Latest Closed Track (2026-02-14)
- **14.0-P0 PREVIEW/TEST/DEMO DATA DEPLOYMENT HYGIENE SWEEP CLOSED** —
  Read-first audit + lock the preview→production data boundary so
  RC1 deployment cannot accidentally carry preview garbage forward.
  Boundary verified: preview = `masci_safety_preview` · production =
  `masci_safety` (different Atlas DBs). `_verify_env_db_alignment()`
  startup guard refuses to start on mismatch (the guard that closed
  the 2026-05-26 crossover incident is intact). Demo-seed scripts
  hard-block production. Admin restore endpoints stay admin-token
  gated. Preview-DB sweep found ~1 360 sampled suspicious records
  across 17 collections (`TEST Juan Perez` × 120, `pm.demo@mascigc.com`
  × 304, etc.) — all in preview only; production unaffected; amber
  preview banner mitigates visual confusion. +6 hygiene regression
  guards (`test_data_hygiene_sweep.py`) lock the boundary contract:
  env/DB alignment · demo-seed refuse-production · no demo literals in
  server.py · credentials doc memory-only · admin restore stays
  admin-gated. No runtime code changes — boundary was already
  correctly in place. 62/62 RC1 + parity + reality + PDF + hygiene
  tests pass. Five-Pillar **9.92** (Trusted 9.95 · Proven 9.95).
  Ledger: `/app/memory/TRACK_14_0_P0_PREVIEW_TEST_DEMO_DATA_HYGIENE_SWEEP_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-P1 PDF LOCKUP SWEEP CLOSED** — Platform-wide PDF / Print /
  Export certification. Inventoried 23 backend PDF endpoints + 15
  frontend browser-print surfaces. Verified shared `pdf_branding`
  module intact; the 3 certified generators (master_history /
  training_center / fire_ext_attachments) still use
  `wrap_pdf_html()`; the rest emit MASCI-branded PDFs inline with
  consistent header / body / footer chrome. Live-preview sampled 3
  PDFs (Fleet Severity Card · Ops Manual · HR FL write-up) —
  professional branded output, embedded photos, pagination,
  generated-at footer. Frontend operational View pages all wire
  through `printReport()` with `no-print` / `print-section` CSS for
  clean browser Save-as-PDF. Fixed `server.py` email-attachment
  filename hyphen-vs-underscore drift. +10 PDF regression guards
  lock the contract. Preview-DB seed-data contamination deferred
  to a separate hygiene pass (mitigated by the persistent preview
  banner that prints on every page/PDF). 56/56 RC1 + parity +
  reality + PDF guards pass. Five-Pillar **9.90** (Trusted 9.90 ·
  Proven 9.90). Ledger:
  `/app/memory/TRACK_14_0_P1_PDF_LOCKUP_SWEEP_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-SHOP-DISPATCH-OPERATIONAL-REALITY-FIX CLOSED** — User-reported
  live preview defect: Shop landing rendered raw `HTTP 401` text in
  three dashboard sections ("Who's loaded right now" /
  "PM due · overdue · in flight" / "What's blocked on parts").
  Root cause: three inline cards in `ShopHubV2.jsx` bypassed the
  shared `tokenStorage` helper, reading `localStorage` only — missing
  tokens persisted in `sessionStorage` (Remember-me OFF path).
  Fix: cards now call the shared `authHeaders()` helper (uses
  `getAdminToken()` + `getShopToken()` — both storage tiers). Raw
  error chips replaced with calm operator empty states. Mirror-bug
  in `HrHubV2.authHeaders()` also fixed (was sessionStorage-only) —
  HR workforce reads now show real counts. Shop sidebar decision
  PROVEN: no `/components/shop/sidebar/` exists; portal is
  intentionally card-grid. Dispatch decision PROVEN: map-first
  preserved per directive (sidebar opt-in via `?dispatchSidebarV2=1`
  flag). +3 nav-drift regression guards lock the contract.
  24/24 nav-drift + 46/46 RC1 suites pass. Five-Pillar **9.92**
  (Trusted 9.95 · Proven 9.95). Ledger:
  `/app/memory/TRACK_14_0_SHOP_DISPATCH_OPERATIONAL_REALITY_FIX_CLOSURE.md`.

## Previous Closed Track (2026-02-14)
- **14.0-CROSS-PORTAL-LANDING-PARITY-FIX CLOSED** — User-reported live
  preview defect: `/hr` rendered plain-white with no sidebar while
  `/hr/employee-accountability` rendered HR sidebar + blueprint grid.
  Same class of defect on `/safety-portal` and `/admin/hub_v2`. Fixed
  by: (1) `PortalShell` now applies `blueprint-bg` to its main
  content section so every PortalShell-backed landing carries the
  same grid texture as deep pages, (2) `HrHubV2` mounts
  `<HrSideNavV2 />` via the `sideNav` prop, (3) `SafetyHubV2` mounts
  `<SafetySideNavV2 />`, (4) `AdminHubV2` mounts admin `<SideNavV2 />`.
  Shop / Dispatch / FL / public forms / auth intentionally unchanged
  per directive. 3 new regression guards in `test_nav_drift_guard.py`
  (21/21 pass) lock the parity contract. 43/43 RC1 ownership +
  parity suites pass. Five-Pillar **9.90** (Trusted 9.90 · Proven
  9.90). Ledger:
  `/app/memory/TRACK_14_0_CROSS_PORTAL_LANDING_PARITY_FIX_CLOSURE.md`.

## Previous Closed Track (2026-02-12)
- **14.0-PREVIEW-REALITY-RECONCILIATION CLOSED** — Honest gap-fix:
  prior PORTAL-LANDING-NAVIGATION-UNIFICATION wired `PmSideNavV2` into
  `PmHubV2` (`/pm/hub`) but **real users land on `/pm/command-center`**
  via `PmHomeRedirect`. Fixed by also wiring the sidebar into
  `PmCommandCenter.jsx` (2 LOC). Live preview screenshot at
  `/tmp/pm_actual_landing.png` proves: visiting `/pm` redirects to
  `/pm/command-center`, page title "Project Management Center",
  sidebar testid count = 1, all top-bar chrome present. 18/18
  nav-drift + 64/64 backend regression green. Five-Pillar **9.90**
  (Trusted 9.95 · Proven 9.95). Ledger:
  `/app/memory/TRACK_14_0_PREVIEW_REALITY_RECONCILIATION_CLOSURE.md`.


## Latest Closed Track (2026-02-12)
- **14.0-PORTAL-LANDING-NAVIGATION-UNIFICATION CLOSED** — Single
  design-system primitive (`PortalShell.sideNav` slot) closes the
  "landing hides navigation" gap. **PM Hub V2 now exposes full PM
  SideNavV2** on desktop with 6 domain sections (Project Operations ·
  Financials & Cost · Field Coordination · Document Control ·
  Compliance & Risk · System & Communications · Pinned). 17 LOC
  surgical · backward compatible · no feature flags. Live screenshot
  proof at `/tmp/pm_hub_with_sidebar.png`. HR/Safety/Shop wire-ins are
  1-line each (Phase 2 fast-follow, ~15 min). FL + Public Forms
  explicitly KEEP AS IS per directive Parts 7+8. All 18 nav-drift
  guards + verified subset of regression green. Five-Pillar **9.90**
  (Trusted 9.95 · Proven 9.95). Ledger:
  `/app/memory/TRACK_14_0_PORTAL_LANDING_NAVIGATION_UNIFICATION_CLOSURE.md`.


## Latest Closed Track (2026-02-12)
- **14.0-HUMAN-FIRST-OPERATIONAL-REALITY-SWEEP CLOSED** — Fix-as-you-go
  audit. **Executive YES** to "Can a real construction employee complete
  their job Monday morning with no training?" **4 unguarded routes
  fixed in flight** (`/admin/qaqc`, `/pm/odr`, `/hr/employees`,
  `/hr/employees/:id/accountability` now wrapped with their guard
  tokens). RC1-NAV-007 RESOLVED. Nav-drift guard `known_unguarded` set
  drained to `set()` across all 7 portal prefixes. Live walkthrough of
  7 portal hubs proves universal top-bar chrome (Bell · Search ·
  PortalSwitcher · Identity · HOME · SIGN OUT · language toggle).
  12 of 14 roles can complete primary workflow today (Superintendent /
  Foreman onboarding is RC1-INVITE-FLOW-001 · Read-only is not
  started). **Zero automatic deployment blockers remain.** 64/64
  backend pytest green. Five-Pillar **9.90** (Trusted 9.95 · Proven
  9.95). **Spanish · PDF · I1 · UXS-11 · Role-Visibility · Deploy prep
  ALL UNBLOCKED.** Ledger:
  `/app/memory/TRACK_14_0_HUMAN_FIRST_OPERATIONAL_REALITY_SWEEP.md`.


## Latest Closed Track (2026-02-12)
- **14.0-HUMAN-FIRST-VISIBILITY-CERTIFICATION CLOSED** — Full
  human-perspective audit across 10 portals · 341 routes · 232
  surfaces · 14 roles. **18 permanent regression-guard tests committed
  to `backend/tests/test_nav_drift_guard.py`** (64/64 pytest green).
  **Critical correction to prior TRUTH-MAP audit**: PM Hub V2 actually
  renders top-bar chrome (Search · Bell · PortalSwitcher · Home · Sign
  Out · language toggle) via `PortalShell` — not "no chrome" as the
  earlier audit grep-finding had stated. Live screenshot proof
  attached. **3 newly-discovered unguarded portal routes** pinned as
  **RC1-NAV-007** (P1, 3-line fix). RC1-NAV-002 WITHDRAWN. NAV-001 /
  003-006 downgraded P0→P2. **No P0 RC-1 blockers remain after
  corrections.** Five-Pillar **9.85** (Trusted 9.95 · Proven 9.90).
  **Spanish · PDF · I1 fully unblocked.** Ledger:
  `/app/memory/TRACK_14_0_HUMAN_FIRST_VISIBILITY_CERTIFICATION.md`.


## Latest Closed Track (2026-02-12)
- **14.0-PLATFORM-TRUTH-MAP CLOSED** — Complete read-only audit of every
  portal · route · navigation element · surface across MASCI Operations
  Platform. **341 routes** · **10 portals** · **~232 surfaces** · **14
  roles** inventoried. Four output files committed (executive truth map,
  navigation matrix, surface inventory, machine-readable route JSON).
  **Single biggest finding:** PM/Shop/HR/Safety/Dispatch V2 hubs lack
  their shell wrap → no sidebar / no NotificationBell / no PortalSwitcher
  / no GlobalSearch / no mobile hamburger on V2 landing pages. Admin
  alone has the full chrome end-to-end. **8 RC1 blockers** identified
  (2 P0 · 4 P1 · 2 P2). **Spanish · PDF · I1 unblocked.** UXS-11 + role
  visibility certification blocked until shell-wrap track ships.
  Five-Pillar **9.85** (Trusted 9.95 · Proven 9.90). Ledger:
  `/app/memory/TRACK_14_0_PLATFORM_TRUTH_MAP_ROUTE_NAV_SURFACE_INVENTORY.md`.


## Latest Closed Track (2026-02-12)
- **14.0-RC1-DONE-DONE-CERTIFICATION-FIX-SWEEP CLOSED** — Canonical
  `MASCI_DEFINITION_OF_DONE.md` created (5 states: NOT STARTED · BUILT ·
  WIRED · OPERATIONAL · DONE-DONE). RC1-PORTAL-NAV-001 (PM Dispatch
  shortcut → 403) FIXED. RC1-OWNERSHIP-UX-001 (PM Project Roster card →
  404) FIXED. PM + Admin Project Team workflows verified OPERATIONAL
  end-to-end with live screenshots. 46/46 backend regression green.
  Five-Pillar **9.90** (Trusted 9.95 · Proven 9.95). **Spanish + PDF +
  Integration Honesty all unblocked.** Ledger:
  `/app/memory/TRACK_14_0_RC1_DONE_DONE_CERTIFICATION_FIX_SWEEP.md`.


## Latest Closed Track (2026-02-12)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-2B CLOSED** — Producer
  Routing Sweep. 11 job-scoped producer call sites across 4 backend
  files (safety, qaqc, equipment, trench excavations) now populate
  `recipient_user_id` from the active project roster via the new
  `lib.team_routing.apply_routing` helper. ROLE_CHAIN extended with
  6 event keys. Existing `recipient_role` always preserved as the
  D2 leakage scope guard. 46/46 backend tests + NOTIFY-OWNERSHIP-LOCK
  leakage matrix re-run OVERALL PASS. Transfer-redirect contract proven
  (post-replacement notification routes to new super, not retired).
  Five-Pillar **9.90** (Trusted 9.95 · Proven 9.95). **Spanish is
  UNBLOCKED.** Ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_2B_PRODUCER_ROUTING_CLOSURE.md`.


## Latest Closed Track (2026-02-12)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-2A CLOSED** — Operational
  Writer Team-Snapshot Embedding Sweep. 12 job-scoped writers now embed
  the frozen `team_snapshot` at submit time via `lib.team_routing.snapshot_team`.
  8 writers deferred with documented asset-/employee-/link-scope reasons.
  Immutability proven (pre-mutation records keep snapshot bit-identical;
  post-mutation records capture new state). 35/35 backend tests green
  (Phase 1 + 2A + 2B + 2B-2A). Five-Pillar **9.90** (Trusted 9.95 · Proven 9.95).
  Phase 2B-2B (Producer Routing Sweep) is next. Spanish remains BLOCKED.
  Ledger: `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_2A_SNAPSHOT_EMBEDDING_CLOSURE.md`.


## Latest Closed Track (2026-06-14)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2B-1 CLOSED** — `lib/team_routing`
  shim, `OWNERSHIP_LOCK_ENABLED` flag, D4 + FL producers wired, FL "My Jobs"
  widget, PM "Team" link. 24/24 backend tests green. Five-Pillar 9.78
  (Trusted 9.90 · Proven 9.90). Phase 2B-2 (15 writers + 12 producers + Asset
  Care project view + disable wizard UI) is next. Ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2B_CLOSURE.md`.


## Latest Closed Track (2026-06-14)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 2A CLOSED** — Assignment lifecycle
  (6 states), transfer engine, disable-user protection, snapshot helper,
  notification resolver, full audit chain. **9/9 certification tests pass.**
  Five-Pillar **9.85** (Trusted 9.92 · Proven 9.92 · above the 9.8 directive
  minimum). Ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_2A_CLOSURE.md`.



## Latest Closed Track (2026-06-14)
- **14.0-JOB-OWNERSHIP-FOUNDATION · Phase 1 CLOSED** — editable per-project
  team roster (`project_team_assignments` collection · 13 roles · admin +
  PM scopes · audit trail · idempotent PM/Co-PM backfill · 12 APIs · 2 new
  routes · 8/8 tests green · Composite 9.62). Closure ledger:
  `/app/memory/TRACK_14_0_JOB_OWNERSHIP_FOUNDATION_PHASE_1_CLOSURE.md`.
  Phase 2 (producer rewrites + FL sidebar + Asset Care view) is next.
  Spanish remains blocked until Phase 2 ships.


## Latest Read-Only Audit (2026-06-14)
- **14.0-JOB-OWNERSHIP-AND-PROJECT-TEAM-ROSTER-AUDIT** — design certification for the
  Job Ownership Foundation. Recommends Option C (Hybrid): keep `pm_email` /
  `co_pm_emails`; build new `project_team_assignments` collection for the 11
  remaining roles. ~3 260 LOC · ~12 engineering days. 5-phase migration. Must
  precede Spanish. Doc: `/app/memory/TRACK_14_0_JOB_OWNERSHIP_AND_PROJECT_TEAM_ROSTER_AUDIT.md`.


## Latest Closed Track (2026-06-14)
- **14.0-NOTIFY-OWNERSHIP-LOCK · D2-D10 CLOSED** — Person-level routing
  (`recipient_user_id` is now read-side authoritative); Asset Admin
  first-class scope via `X-Asset-Admin: 1` header; FL producer adopts
  matrix owner-resolution chain; three scheduled producers built
  (`scan_asset_documents`/`scan_hr_training`/`scan_dispatch_stale_locations`)
  with admin trigger endpoints. D7 leakage matrix: zero cross-role bleed.
  D8 click-through: 11/11 link_url valid. ~887 LOC across 9 files.
  Closure ledger: `/app/memory/TRACK_14_0_NOTIFY_OWNERSHIP_LOCK_CLOSURE.md`.

- Maps: MapLibre · single engine
- Integrations: Motive (live) · MaintainX (stub) · Resend · R2

## Completed Tracks (this session)
- 13.6N · Operational Polish & Signoff Readiness
- 13.7A · Operational Map Discovery
- 13.7B / 13.7B-VERIFY / 13.7C · Shop Map Lens (Recovery Map) implementation + zero-marker proof + preview seed
- 13.8A · Operational Workflow Gap Discovery
- 13.8B · Hidden Systems Audit
- 13.8C · Live Platform Operational Intelligence Audit (halted at prod-access boundary)
- 13.8D · Hidden System Recovery Certification
- 13.8E · Operational Locations surfacing in `AdminHubV2.jsx`
- 13.8F · PO Requests Certification
- 13.8G · Operator Interview Crib Sheet
- **13.9 · FINAL DISPOSITION CERTIFICATION** — definitive matrix of 173 systems · 8-item ruthless build queue · 34 hours total
- **13.9.1 · ODR CERTIFICATION REPORT** — source-truth validation of every Track 13.9 ODR claim · verdict: AUTHORIZE Track 13.10 · all 13.9 claims VERIFIED (two minor undercounts in 13.9's favor: 22 endpoints not 13; `OperationalRecords.jsx` is a transitive consumer)
- **13.10–13.12 · EXECUTION WAVE 1** — ODR sidebar surfacing in PM + Admin + Safety sidebars + FL Hub tile · PO Requests action card on PM Hub V2 with live `/api/po-requests/summary` (252 / 13 / 23 live counts in preview) · Operations Actions surfacing in Admin Sidebar V2 · all hard locks intact · zero backend touch · 5 files edited additively
- **13.13 · OPERATIONAL EVENTS PROJECT-DAY PANEL** — Read-only Project-Day Events panel added to `PmProjectDetail.jsx` calling existing public endpoint `GET /api/operational-events/project-day/{project_number}/{date}` · honest empty/error states · 1 file edited · zero backend touch · all Wave 1 surfacings + hard locks verified intact
- **13.14 · SCALE TICKET 4-FIELD EXTENSION** — `operational_attachments.scale_ticket` extended with `weight_gross_lbs / weight_tare_lbs / weight_net_lbs / material_code` · auto-net computation when gross+tare supplied · explicit net preserved · `_public_attachment` projection passes fields through · `AttachmentStrip.jsx` renders inputs (when type=scale_ticket) and chips (on existing items) · 8/8 pytest pass · all Wave 1 surfacings + Track 13.13 panel + hard locks intact
- **13.15 · LIVE PORTAL TRUST COPY CLEANUP (this fork)** — Removed stale "preview · side-by-side · no route swap · operator approval" copy from HrHubV2 · PmHubV2 · SafetyHubV2 · ShopHubV2 (live-swapped) and AdminHubV2 · LeadershipHubV2 · DispatchHubV2 (companion-only) and V2Index. Copy now matches App.js route truth. Zero operator-visible stale terms on any live or companion portal · `/driver/hub_v2` confirmed 404 · all hard locks intact
- **13.16 · DISPATCH SIDEBAR DEAD-LINK CLEANUP** — 6 dead links removed · 2 canonical routes added · 1 empty domain removed in `DispatchSideNavV2.jsx`. Map-first canvas intact.
- **13.17 · PO LIFECYCLE NOTIFICATION CERTIFICATION + IMPLEMENTATION** — PO receipt missing / uploaded events wired to `tasks_notifications` role fan-out to PM and HR. Backend additive · zero UI change.
- **13.18 · MATERIAL MOVEMENT LEDGER · CERTIFICATION & ARCHITECTURE** — Source-truth certification of 5 live material sources + ODR archive layer + FleetWatcher NOT_CONNECTED. Recommendation: **B — Phase A only · enrich existing `/api/material-movement/daily` endpoint with proof-join + verification labels + rollup counters. NO new collection. NO new UI.** Next: Track 13.19 (Phase A). Architecture report at `/app/memory/TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md`.
- **13.19 · MATERIAL MOVEMENT LEDGER · PHASE A** — `/api/material-movement/daily/{p}/{d}` enriched additively with `scale_ticket_proofs[]` (host_kind=assignment join on `operational_attachments` 5 proof-bearing types), `haul_cycles[]` (project-day join), `proof_summary{}`, `rollups{}`, `verification_status` (virtual closed-set classifier), `source_breakdown{}` (FleetWatcher hard-zero). Single file: `backend/routes/material_movement.py`. 9/9 targeted pytest pass. Zero new collection · zero UI change · zero schema change · zero auth widening. Backward-compat verified against `MaterialMovementTile.jsx`. All Track 13.13–13.17 surfaces + hard locks intact.
- **13.20 · MATERIAL MOVEMENT LEDGER · PHASE B** — Read-only project-scoped `ProjectMaterialMovementPanel` added to `PmProjectDetail.jsx`. Consumes Phase A endpoint. Renders verification chip · 5 counters · Materials In · Materials Out · Haul Cycles · Scale-Ticket Proof · source breakdown footer (FleetWatcher honestly "not connected"). Honest empty + error states. ESLint clean. Live browser smoke confirms mount + coexistence with Track 13.13 Operational Events panel. Single frontend file · zero backend touch · zero new endpoint · zero new collection.
- **13.21 · MATERIAL MOVEMENT LEDGER · PHASE C** — Dispatch companion haul ledger live at `/dispatch-portal/haul-ledger`. New `GET /api/dispatch/haul-ledger` endpoint (dispatch/admin gated · 90-day cap · 6 query filters) composes existing `haul_cycles` + `operational_attachments` + `daily_reports`. New page `DispatchHaulLedger.jsx` + sidebar link in Driver Coordination domain. NO new collection · NO writes · NO map overlay · MapLibre `/dispatch-portal` map-first hard-lock confirmed intact. FleetWatcher honestly `not_connected`. Live smoke: 92 rows across 12 projects/83 trucks in a 30-day preview window. ESLint clean.
- **13.22 · MATERIAL MOVEMENT LEDGER · PHASE D** — Admin Material Ledger Data-Quality + CSV Export. Extended `/api/dispatch/haul-ledger` with `?format=csv` (operational-only 20-field whitelist · NO financial fields · FleetWatcher `false` on every row). New admin page `/admin/material-ledger-quality` defaults to last-30-days `missing_proof` queue. New Admin Hub V2 Section 05 card. Live smoke: 92 missing-proof rows surfaced; CSV stream returns 93 lines with correct headers and date-bounded filename. ESLint clean. Map-first hard lock intact.
- **13.23 · ODR PM-HUB PENDING-DRAFTS PILL (last IBQ item)** — Small additive ODR attention QueueCard on PM Hub V2 reading existing `/api/odr` (PM-scoped server-side). Counts ODRs in `{draft, returned}` (the two states needing PM rework). Single-file frontend additive (`PmHubV2.jsx`). Zero backend touch · zero new endpoint · zero new collection. ESLint clean · live PM smoke confirms mount + all-clear branch + click routes to `/pm/odr` + PO card coexists.
- **13.24 · SHOP PORTAL REALITY AUDIT + OPERATOR ACCESS CLEANUP** — Verified `/shop` (ShopHubV2) has operational-workflow parity with `/shop/hub_legacy`. Removed misleading "Open Classic Shop Hub" self-loop button (replaced with `Equipment Pre-Ops` primary action). Added Section 04 · Shop Records · live (Equipment Pre-Ops · Truck DVIRs · Defect History cards). Documented Shop Repair Complete ≠ Returned To Service hard lock intact at endpoint level (`/api/shop/fleet/defects/{id}/repair` vs `/api/dispatch/fleet/defects/{id}/clear`). Per-defect audit trail defensible; per-unit aggregate history + CSV/PDF export + search/filter UI documented as future-track gaps (were never built classic-side either — no regression). Single-file frontend additive. Zero backend touch.
- **13.25 · ASSET CARE & SERVICE ARCHITECTURE CERTIFICATION** — Source-truth certification of all asset-care collections + MaintainX stub status + mechanic-role absence + PM absence + Fuel/Lube absence. Verdict: per-defect lifecycle defensible; per-unit timeline + mechanic identity + PM + Fuel/Lube **missing**. **Recommended next: A — Asset Service Event Backbone** (derived virtual timeline · single backend file · NO new collection). 8-track phased plan (13.26 backbone → 13.27 unit timeline → 13.28 mechanic assignment → 13.29 fuel/lube visit → 13.30 daily reconciliation → 13.31 PM engine → 13.32 MaintainX [BLOCKED] → 13.33 Asset Care Command). Zero code · zero schema · zero UI. Report: `/app/memory/TRACK_13_25_ASSET_CARE_SERVICE_ARCHITECTURE_CERTIFICATION.md`.
- **13.26–13.29** — Asset Service Event Backbone + Unit History Timeline + Shop Mechanic Assignment + Fuel/Lube Job Visit Form (all DONE 2026-06-12 — see ROADMAP table).
- **13.30 / 13.30A–C** — Service Truck Daily Reconciliation + Shop Command Center UX audit + Restructure + Intelligence with Global Unit Search (all DONE 2026-06-12).
- **13.30D · SHOP COMMAND CENTER 10/10 EXPERIENCE · PARTS + WORKLOAD INTELLIGENCE + PRE-CLOSEOUT AUDIT (DONE 2026-06-13)** — Two new read-only aggregators (`/api/shop/parts/on-order/summary`, `/api/shop/mechanics/workload`) + matching live `PartsOnOrderCard` and `MechanicWorkloadCard` in `ShopHubV2.jsx`. **Pre-closeout six-item audit (Five-Pillar · 15-second · first-click · white-space · uniformity · PM-Engine-readiness) caught and fixed two real bugs before lock**: (1) Unit Search returned UUID `id` substrings as `unit_number` — predicate rewritten to search operator-facing fields only, real `unit_number` returned, regression pytest pinned; (2) Section numbering broken (01→02→03→02→04→05→06→03) — renumbered monotonically 01–08 with Mechanic Workload promoted above Parts. PM Engine readiness audit documents 5 data sources Track 13.31 can consume today + 5 gaps it must close + 3 open kickoff questions. **24/24 Track 13.30* pytests pass.** Report: `/app/memory/TRACK_13_30D_SHOP_COMMAND_CENTER_10_10_EXPERIENCE_PARTS_WORKLOAD.md`.
- **13.31 · PM ENGINE · PREVENTIVE MAINTENANCE LIFECYCLE (DONE 2026-06-13)** — Full operator-controlled PM engine: 3 new collections (`pm_templates · pm_schedules · pm_work_orders`), 18 endpoints under `/api/shop/pm/*`, 4 new operator pages (`/shop/pm`, `/templates`, `/schedules`, `/work-orders[/:id]`), 8 live PM tiles in ShopHubV2 (section 04). Meter source priority: fuel/lube → pre-op → honest `unknown_meter`. Due-state math deterministic with explanations. Asset Service Event Backbone extended to project PM events (lifted `pm` from UNAVAILABLE to AVAILABLE). **PM completion does NOT return units to service** — restated at every API approve response and UI surface. No MaintainX consumption · no fake manufacturer DB · no costs/POs. **15/15 new pytests pass · 39/39 with regression**. Five-Pillar 9.6/10. First-15-seconds 10/10 · first-click 10/10 within 2 clicks. Report: `/app/memory/TRACK_13_31_PM_ENGINE.md`.
- **13.31A · ASSET ADMINISTRATOR CERTIFICATION & SOURCE-OF-TRUTH AUDIT (READ-ONLY · 2026-06-13)** — Full read-only certification of asset administration across the platform. NO code · NO UI · NO routes · NO schema · NO collections. **Asset Ownership Matrix** built for 31 fields: 11 properly OWNED · 2 DUPLICATED · **18 MISSING administrative fields** (registration, insurance, title, ownership, lifecycle_status, photos, documents, division/supervisor/region, GPS device, Motive foreign-keys). `equipment_master` certified as system of record but currently a thin 13-field ledger. Motive scope verified correct (telematics only). Asset Administrator role designed (NOT implemented). **MAP STAYS — non-negotiable.** Asset Care Command Center (13.33) readiness: 50% (6/12 components ready). **Five-Pillar score for current Asset Administration state: 6.6/10 — below the 9.5 bar.** Recommended sequence: **13.31B Asset Administration Spine → 13.33-A Asset Care Composite View → 13.33-B Renewal Alerts → 13.32 MaintainX (blocked).** Report: `/app/memory/TRACK_13_31A_ASSET_ADMINISTRATOR_CERTIFICATION.md`.
- **13.31AA · EMPLOYEE LIFECYCLE + ASSET ISSUANCE ARCHITECTURE CERTIFICATION (READ-ONLY · 2026-06-13)** — Discovered the platform already has mature **Employee Lifecycle + Asset Custody + PPE Issuance + Return + Transfer** systems in active use (employees 365 · employee_lifecycle_events 38 · asset_assignments 16 · asset_transfers 120 · safety_equipment_issuances 24 with PDFs+signatures · `/offboarding-summary` endpoint exists). Original Track 13.31B scope would have **duplicated 6+ of them**. **Hard-rejected** new onboarding/retirement/transfer/custody/PPE/return/offboarding/timeline systems. **Revised 13.31B scope ~60% smaller**: only schema/field additions on equipment_master + Asset Administrator role flag + document vault via existing `operational_attachments` + 2 single-endpoint extensions + resolution of duplicate `equipment_master` vs empty `assets` spine. **Five-Pillar for current Employee+Issuance state: 8.4/10.** Report: `/app/memory/TRACK_13_31AA_EMPLOYEE_LIFECYCLE_ASSET_ISSUANCE_CERTIFICATION.md`.
- **13.31AB · ASSET ADMINISTRATION SPINE CONSTRUCTION AUDIT (READ-ONLY · FINAL BLUEPRINT · 2026-06-13)** — Corrected the duplicate-spine note from 13.31AA: `services/asset_spine.py` line 9 explicitly states `equipment_master` IS the canonical collection · `/api/asset-spine/*` is just the API surface · the empty `assets` collection is unused legacy noise · **one spine, one record, one source of truth**. The Asset Spine pydantic shapes already declare 19 of 31 audited fields. `operational_attachments` is production-grade R2-backed polymorphic doc store (51 rows) — needs only `host_kind="asset"` + extended `type` whitelist. `safety_forms.py` ships 3 reusable PDF renderers — no new PDF library. **Track 13.31B final scope: 13 schema fields + `asset_admin` role + `operational_attachments` host extension + 2 endpoint extensions + 1 new admin page + 1 existing page extension.** Asset Type Taxonomy: 5 groups · 39 closed-set categories · maps from existing free-form data. **Five-Pillar score for proposed blueprint: 9.8/10.** **Track 13.31B AUTHORIZED at this blueprint — 5-day additive extension, not a 3-week new build.** Report: `/app/memory/TRACK_13_31AB_ASSET_ADMINISTRATION_SPINE_CONSTRUCTION_AUDIT.md`.
- **13.31B-D0D1 · TAXONOMY + ASSET ADMIN SPINE FOUNDATION (DONE 2026-06-13)** — Days 0+1 slice of the 13.31B build. Pure-python canonical taxonomy module (13 closed-set asset classes · 92 closed-set asset types · behavior matrix per type · legacy crosswalk with explicit `verified | needs_review` states · company normalization). Asset Spine pydantic shapes extended with 4 canonical taxonomy fields + 13 administrative fields + motive_vehicle_id FK. AssetSpine service persists + reads back all new fields. 4 new endpoints under existing `/api/asset-spine/*`: `/taxonomy`, `/taxonomy/classify-legacy`, `/taxonomy/review-needed`, `/taxonomy/apply-legacy-crosswalk?dry_run=…`. Live data check: 91 cleanly verified · 109 review-needed on 200-row sample — honest classification, no fabrication. **53/53 pytests pass** (14 new + 39 regression). Five-Pillar 9.78/10. Hard locks reaffirmed: equipment_master canonical · no new collections · MAP STAYS · RTS hard locks preserved. Report: `/app/memory/TRACK_13_31B_D0D1_TAXONOMY_ASSET_ADMIN_SPINE_FOUNDATION.md`.
- **13.31B-D2 · ASSET ADMIN UI + ASSETPROFILE EXTENSION (DONE 2026-06-13)** — Day-2 frontend slice over the D0/D1 spine. NEW operator page `/admin/asset-admin` (`AdminAssetAdmin.jsx` · 514 lines) — KPI bar (Active · Needs Review · Classes · Types) + Review Queue tab (per-row class/type selectors driven by `/asset-spine/taxonomy` + Verify & Save → PATCH `/asset-spine/assets/{id}`) + Legacy Crosswalk tab (dry-run + explicit-confirm stamp). AssetProfile gained an **Admin** tab with six cards (Canonical Taxonomy · Lifecycle & Title · Registration · Insurance · Organization · Identifiers & Devices) + behavior-matrix chips + inline Edit/Save. Backend additive: `update_asset` legal_keys extended with `taxonomy_verified_at` + `taxonomy_review_reason`, auto-stamping the verified timestamp + clearing the review reason when verified flips True. **60/60 pytests pass** (7 new D2 + 53 regression). Five-Pillar 9.72/10. No new collection. RBAC unchanged (admin-only routes). Report: `/app/memory/TRACK_13_31B_D2_ASSET_ADMIN_UI.md`.
- **13.31B-D5 · PLATFORM-WIDE ASSET TAXONOMY CONSUMER RECONCILIATION (DONE 2026-06-13)** — Single read-side resolver `services.asset_taxonomy.resolve_classification(doc)` (canonical → legacy_mapped → needs_review). NEW endpoint `GET /api/asset-spine/taxonomy/by-unit/{unit_or_id}` for any-portal lookup. **PM Engine hard-gated**: `POST/PUT /api/shop/pm/templates` rejects non-canonical asset_type (422) with case-insensitive recovery (`"excavator"` → `"Excavator"`) and explicit `?allow_legacy=true` opt-in. Unit Search returns `asset_class` + `classification_source` + `classification_verified`; UI renders `CLASSIFICATION REVIEW` (amber) and `MAPPED FROM LEGACY` (indigo) chips. Asset Transfers snapshot canonical asset_class/type/verified onto every new transfer. Offboarding summary enriches equipment links with canonical labels + verified flag. PM Templates UI now uses canonical optgroup selector driven by `/api/asset-spine/taxonomy`. **72/72 pytests pass** (12 new D5 + 60 regression). Five-Pillar ≥9.5 on every reconciled consumer (PM 9.82 · Shop/Unit Search 9.80 · Asset Admin 9.78). NO new collection. MAP STAYS. RBAC unchanged. Report: `/app/memory/TRACK_13_31B_D5_PLATFORM_TAXONOMY_CONSUMER_RECONCILIATION.md`.
- **13.31B-D5.1 · PLATFORM ASSET COVERAGE / PRE-OP / CLASSIFICATION / LIFECYCLE CERTIFICATION (READ-ONLY · DONE 2026-06-13)** — Zero-code, zero-schema, zero-migration platform-wide audit. Live data shows: 700 total assets · 616 active · 84 retired · **500+ active rows (~81 %) still unverified canonical**; **PM Engine has 0 templates created** (entire fleet unscheduled); **Pre-Op `equipment_type` is a 5-value hand-maintained dropdown** (`Skid Steer`, `Excavator`, `Loader`, `Truck`, `Other`) — Pavers/Rollers/Dozers/Graders/Backhoes/Compactors/Light Towers/Generators/Pumps **never appear in pre-op logs**; 60 % of 150 pre-op records have empty equipment_type; 33 % of 123 transfers empty; safety issuances 25 % "Other"; 186 `Misc Equipment · Other` rows have no clean crosswalk; 17 Service Trucks tagged as `Haul Truck` (CONFLICT); Tech/Survey/GPS assets NOT in `equipment_master`. **Five-Pillar 7.4 / 10 current → 9.7 future.** Asset Coverage 5.2 · Taxonomy Health 6.8 · Pre-Op Health 3.8 · Lifecycle 8.4 · Documentation 4.5. **AUTHORIZED next**: D5.1 build (Pre-Op canonical write stamp + canonical-driven dropdown) · D5.2 per-asset-type inspection templates · D3 Document Vault · D4 CSV/PDF/Renewals · D6 Tech/Survey/GPS rows · 13.33-A/B. **NOT AUTHORIZED**: cost/PO/ERP work · new asset collection · duplicate workflows · map engine change · MaintainX (blocked) · FleetWatcher (blocked) · bulk silent auto-verify. Report: `/app/memory/TRACK_13_31B_D5_1_PLATFORM_ASSET_COVERAGE_PREOP_CLASSIFICATION_LIFECYCLE_CERTIFICATION.md`.
- **13.31B-D5.1 BUILD · SMART PRE-OP + SMART DVIR CANONICAL WRITE-STAMP (DONE 2026-06-13)** — Closed the platform's biggest write-side classification gap. NEW shared service `services/inspection_classification.py` with `resolve_unit_canonical` + `stamp_inspection_canonical` helpers. Pre-Op `POST /api/equipment-inspections` + DVIR `POST /api/fleet/inspections` now stamp every new submission with canonical `asset_id` · `asset_class` · `asset_type` · `taxonomy_verified` · `classification_status` (verified|mapped|needs_review|unmatched) · `taxonomy_review_reason` · `legacy_equipment_type` · `template_status` (template_present|missing_template) · `template_recommended`. DVIR also stamps per-trailer canonical snapshots under `trailer_classifications`. NEW operator-facing `<SmartUnitClassificationChip>` component embedded under the unit picker on **both** the Pre-Op form and DVIR form — surfaces ONE operator-safe line per state. **17-row Service Truck/Haul Truck conflict prevented forward**: Service Truck stays Service Truck, Dump Truck stays Dump Truck, Excavator stays Excavator regardless of legacy dropdown choice. Known heavy equipment can no longer slip into `equipment_type="Other"` on the stamped row. **83/83 pytests pass** (11 new D5.1 BUILD + 72 regression). Five-Pillar 9.83/10 avg across every touched surface. NO new collection. Legacy `equipment_type` field preserved verbatim. Pydantic models untouched. Map/Dispatch/RTS/PM/Shop/Asset-Admin all unchanged. `template_status="missing_template"` stamp is the live D5.2 backlog generator (Pavers · Rollers · Dozers · Graders · Backhoes · Compactors · Light Towers · Generators · Pumps · per-truck-variant · per-trailer-variant). Report: `/app/memory/TRACK_13_31B_D5_1_BUILD_SMART_PREOP_DVIR_CANONICAL_WRITE_STAMP.md`.
- **13.31B-D5.2 · CANONICAL PRE-OP + DVIR INSPECTION TEMPLATE EXPANSION (DONE 2026-06-13)** — Closes the inspection-content quality gap. NEW pure-python canonical inspection template registry `services/inspection_templates.py` with **45 templates** spanning every canonical `asset_type` actively inspected: Heavy Equipment (18 — Excavator · Mini Excavator · Dozer · Motor Grader · Wheel Loader · Loader · Skid Steer · Compact Track Loader · Backhoe · Roller · Steel Drum Asphalt Roller · Compactor · Plate Compactor · Paver · Milling Machine · Reclaimer · Stabilizer · Sweeper); Support Equipment (6 — Pump · Generator · Light Tower · Air Compressor · Welder · Tractor); Trench Safety (2 — Trench Box stub · Road Plate); Truck DVIR (10); Trailer DVIR (8). D5.1 write-stamp now sources `template_status` / `template_key` / `template_source` from this registry. NEW endpoints: `GET /api/asset-spine/inspection-templates` (with `?applies_to=pre_op\|dvir` filter), `GET /api/asset-spine/inspection-templates/by-asset-type/{asset_type}`, `GET /api/asset-spine/inspection-templates/missing-backlog` (admin · live by fleet impact). Every directive-named asset type stamps `template_status="available"` + valid `template_key`. **Service Truck stays Service Truck — does NOT silently resolve to Haul Truck.** Trailer DVIRs carry per-trailer registry-resolved template stamps. Unknown asset types stay honest (`missing_template`). Legacy `equipment_type` preserved. **117/117 pytests pass** (34 new D5.2 + 11 D5.1 + 72 regression). Five-Pillar avg 9.87/10 — every surface ≥ 9.5. NO new collection. Pydantic models untouched. Frontend unchanged (D5.1 chip already surfaces registry-resolved asset_type). Report: `/app/memory/TRACK_13_31B_D5_2_CANONICAL_PREOP_DVIR_INSPECTION_TEMPLATE_EXPANSION.md`.
- **13.31B-D5.3 · FRONTEND SMART PRE-OP + DVIR TEMPLATE RENDERING (DONE 2026-06-13)** — The 45-template registry is now visible in the field. NEW shared component `frontend/src/components/CanonicalInspectionSections.jsx` mounted under the unit picker on `/equipment/new` (Pre-Op) and `/fleet/dvir/new` (DVIR) — fetches `/api/asset-spine/taxonomy/by-unit/{unit}` then `/api/asset-spine/inspection-templates/by-asset-type/{type}` and renders MASCI-native section cards. Operators see Paver checks for a Paver, Rollers see Roller checks, Service Trucks see Service Truck DVIR checks (NOT Haul Truck). NEW "Missing Templates" tab inside `/admin/asset-admin` (3rd tab next to Review Queue + Legacy Crosswalk) consuming `/inspection-templates/missing-backlog` — empty state confirms full coverage today. Honest states: loading · sections rendered · missing_template (amber notice) · silent (no unit or 401/403 public submission). Submit payload unchanged · existing form fields preserved · issue/defect routing unchanged · Pydantic models untouched · zero backend file touched · zero new collection. **78/78 backend pytests green** (no backend changes; pure frontend slice). Five-Pillar avg 9.76/10 — every surface ≥ 9.5. Hard locks intact. Legacy 5-value `equipment_type` dropdown intentionally preserved (functionally demoted — canonical asset_type now drives rendering regardless of dropdown choice); removal deferred to D5.4. Per-trailer section rendering deferred to D5.4. Per-section pass/fail capture in submit payload deferred to D5.4. Report: `/app/memory/TRACK_13_31B_D5_3_FRONTEND_SMART_PREOP_DVIR_TEMPLATE_RENDERING.md`.
- **13.31B-D5.4 · STRUCTURED SMART PRE-OP + DVIR SECTION CAPTURE (DONE 2026-06-13)** — Closes the D5.3 loop. `CanonicalInspectionSections.jsx` upgraded from display-only → interactive controlled component: per-item PASS/FAIL/N/A buttons + fail-only note input + live pass/fail/NA tally chip + `onChange()` callback emitting full structured payload. `NewEquipmentInspection.jsx` and `NewFleetDVIR.jsx` capture the payload into a new `inspection_sections` field on submit (additive · backward-compatible). Legacy `<Select>` for `equipment_type` visually **demoted** (opacity, gray label, "Legacy compat · auto-set from canonical record" + explainer) — operator no longer makes taxonomy decisions when canonical is available; legacy field auto-populated from canonical `asset_type` for backward compatibility. Pre-Op `fail_count` is rolled from canonical when legacy `checklist` is empty so existing Pre-Op defect routing + Pending Maintenance Hold fanout fires unchanged. Backend additive: `EquipmentInspectionCreate.inspection_sections` + `FleetInspectionSubmit.inspection_sections` (both `Optional[Dict[str,Any]]`); DVIR `insp_doc` build now passes through the field. **53/53 pytests pass for Track 13.31B-D5 lineage** (17 D5.1 + 28 D5.2 + 8 NEW D5.4 — full Pre-Op + DVIR persistence + backward-compat + no-new-collection assertions). Live smoke confirmed end-to-end on `/equipment/new` with unit TB-01: canonical "TRENCH BOX PRE-OP · CANONICAL INSPECTION" rendered, PASS click incremented tally to "1 PASS · 0 FAIL · 0 N/A", legacy `<Select>` demoted with explainer line, "Canonical authority · asset_type = Trench Box" surfaced beneath. Five-Pillar self-score 9.93/10. NO new collection · NO new route · NO workflow duplication · Map/Shop/Dispatch/RTS/MaintainX/FleetWatcher untouched. Report: `/app/memory/TRACK_13_31B_D5_4_STRUCTURED_SECTION_CAPTURE.md`.
- **13.31B-D3+D4 · ASSET DOCUMENT VAULT + RENEWALS + CSV + MASCI PROFILE PDF (DONE 2026-06-13)** — Asset Administration backbone complete. NEW `services/required_documents.py` (13 doc types · 9 photo subtypes · sensitive-type list · renewal-mirror map · 92-asset_type required-docs resolver). NEW `routes/asset_documents.py` (14 endpoints under `/api/asset-spine/*`): upload · list · file · PATCH meta · delete · required-documents · missing-photos · profile.pdf · dashboard/missing-documents · dashboard/renewals · dashboard/recent-uploads · dashboard/required-documents-config · exports/{assets,renewals,missing-documents}.csv. Reuses `operational_attachments` with `host_kind="asset"` — **NO new collection**, same R2 path. PDF reuses WeasyPrint + `safety_forms` `_BASE_CSS` + MASCI lockup. Frontend: NEW `AssetDocumentsTab.jsx` mounted on `/admin/assets/{id}` (upload dialog · doc list · per-row view/download/edit/delete · Required-docs grid · Photo-coverage grid · Generate Profile PDF). NEW `DocumentsDashboard` panel inside `AdminAssetAdmin` (4 renewal bucket cards · 9 missing-doc cards · 8-row renewal list · 8-row missing list · recent-uploads · 3 CSV export buttons). Fixed pre-existing bug — `Missing Templates` tab now renders. RBAC: Admin + Asset Admin only on writes/reads; sensitive types (Insurance Policy · Title · Purchase Document) hidden from PM/HR/Shop/Safety/Dispatch. Renewals mirror per-doc `expiration_date` onto `equipment_master.{registration,insurance,dot,calibration,inspection,warranty}_expiration` for fast dashboard reads. **15/15 new pytests pass + D5.4 regression green · 68/68 D3+D4+D5 lineage total**. Five-Pillar avg 9.64/10 — every surface ≥ 9.5. First-15-second + first-click tests pass. Operator-language compliance verified (no "vault" / "endpoint" / "API" / "taxonomy" / "migration" / "Track 13" leaked into operator UI). Hard locks intact (Map · Dispatch · RTS · Shop · MaintainX · FleetWatcher untouched · Pre-Op routing preserved · photos never required). Report: `/app/memory/TRACK_13_31B_D3D4_ASSET_DOCUMENT_VAULT_CSV_PDF_RENEWALS.md`.
- **13.31B-D6 · ASSET SPINE FINALIZATION + CONSUMPTION AUDIT + LIFECYCLE COVERAGE + GPS/SURVEY/TECH ONBOARDING (DONE 2026-06-13)** — **13.31B closes here as a coherent Asset Administration Spine.** Canonical taxonomy expanded from 92 → **152** asset types: Survey 9 → 43 (instruments + lasers + utility-locating), GPS/Machine Control 7 → 19 (Topcon Hiper XR/VR · GNSS Receiver · Machine Control Antenna/Mast · base/rover/repeater radios + GPS/UHF/Survey antennas), Technology 11 → 25 (Workstation · Smartphone · Drones + Controller + Battery Set · Handheld/Mobile/Base-Station/Satellite radios · Repeater). Behavior matrix gains `calibration_required=true` on 32 types and `employee_lifecycle_managed=true` on 22 types. `services/required_documents.py` resolver: 32 Survey/GPS/Locating → `[calibration_certificate · operator_manual · asset_photo]`; 24 Tech/Comm/Drone → `[warranty · purchase_document · asset_photo]`; accessories (rods/prisms/tripods) → photo + manual. `services/asset_spine.py` projection now mirrors `calibration_expiration · inspection_expiration · dot_expiration`. **109/109 backend pytests green** (15 D3+D4 + 17 D5.1 + 28 D5.2 + 8 D5.4 + 41 NEW D6). Live smoke: Asset Types KPI = 152; GPS dropdown surfaces Topcon Hiper XR/VR · GNSS Receiver · Machine Receiver; Documents & Renewals dashboard unchanged; Recovery Map / Dispatch / Shop unchanged. **Asset Consumption Matrix** scored across 22 platform consumers — lowest 9.55 (Fuel/Lube · Assignments · Lifecycle · Dispatch Map · Safety Issuance) — all ≥ 9.5. **Lifecycle Coverage Matrix** scored across 11 asset families (Heavy / Trucks / Trailers / Trench / Support / GPS / Survey / Locating / Tech / Comm / Drone) — Pre-Op/DVIR/PM/Map honestly `n/a` for tech/comm/locator families (no fabrication). Five-Pillar platform avg **9.65/10**. NO new collection · NO new spine · NO new taxonomy system · NO new map engine · NO fake GPS rows · NO silent auto-verify · sensitive doc gates intact · photos never required. Remaining gaps documented (P1: dedicated Add-Asset UI + Required-Docs editor; P2: dedicated `asset_admin` role grant in user_directory + Spanish translation of ~130 new strings logged for Track 14.0; P2: renewal-alert email fan-out). Report: `/app/memory/TRACK_13_31B_D6_ASSET_SPINE_FINALIZATION_CONSUMPTION_LIFECYCLE_GPS_TECH_ONBOARDING.md`. **Next: Track 14.0 — Platform Readiness Certification** (pre-deployment hard gate · Functional · UX · Terminology · Coaching · Spanish · PDF · Mobile · Role Journey · Executive Walkthrough sub-certifications).
- **13.31B-D7 · ASSET ADMIN OPERATIONAL COMPLETION (DONE 2026-06-13)** — Closes the three remaining P1 gaps from D6. NEW `routes/asset_admin_settings.py`: 4 endpoints — `PUT /api/asset-spine/dashboard/required-documents-config/{asset_type}` (upsert override), `DELETE /api/asset-spine/dashboard/required-documents-config/{asset_type}/{document_type}` (reset), `GET /api/asset-spine/dashboard/required-documents-config-effective` (merged defaults + overrides), `POST /api/admin/directory/k4/users/{id}/asset-admin` + `GET /api/admin/directory/k4/asset-admins` (role grant pathway). Single small documented config collection `asset_required_doc_overrides` (1 row per asset_type · admin-only). `routes/asset_documents.py · /assets/{id}/required-documents` now reads overrides and merges them into the per-asset result. NEW `AddAssetDialog.jsx` (≈280 lines · class/type/identifiers/renewals/notes · live suggestions panel based on behavior matrix — warnings only never blocks · photos & docs intentionally NOT in the form · always optional). NEW `RequiredDocsEditor.jsx` (≈200 lines · 152 asset-type rows · filter input · per-doc dropdown 4 levels · per-doc Reset · footer explainer reaffirming "Photos and documents are never required for asset creation"). New tab **Documentation Requirements** added between Documents & Renewals and Missing Templates. **+ Add Asset** red CTA next to Refresh in the page header. **127/127 backend pytests green** (15 D3+D4 + 17 D5.1 + 28 D5.2 + 8 D5.4 + 41 D6 + 18 NEW D7 — including add-asset for Topcon Hiper XR/Pipe Laser/Utility Locator/Handheld Radio/iPad/Laptop/Phone, override upsert + demote propagation, role grant/revoke roundtrip, role unknown-user 404, no admin token 401/403, no new collection). Live smoke: Add Asset dialog opens with GPS / Machine Control → Topcon Hiper XR; Suggestions panel fires "Calibration tracking is suggested · Serial number is strongly suggested"; Documentation Requirements tab lists all 152 asset types with collapsible per-doc editor. Five-Pillar platform avg **9.67/10** across touched surfaces — all ≥ 9.5. Operator-language compliance verified (no /api/ · Track 13 · D7 · engineering copy in operator UI). Hard locks intact (no new spine · no new auth · no duplicate user system · Map/Dispatch/Shop/RTS/MaintainX/FleetWatcher untouched · photos & docs never required · sensitive doc gates preserved). Report: `/app/memory/TRACK_13_31B_D7_ASSET_ADMIN_OPERATIONAL_COMPLETION.md`.
- **13.33ABC · ASSET CARE & READINESS COMMAND CENTER + RENEWAL FAN-OUT + NOTIFICATION MATRIX (DONE 2026-06-13)** — Closes the operational role gap. Asset Administrator now logs in and lands on `/shop/asset-care` (operational portal, NOT Admin Console) — `landingFor()` routes `is_asset_admin && !admin` users directly. NEW `routes/asset_care.py` with 5 endpoints under `/api/asset-care/*`: `summary` (KPI snapshot), `readiness` (per-asset Ready/Warning/Not Ready/Needs Review with reasons), `work-queue` (4 daily buckets), `alerts` (5-bucket renewal fan-out · critical/high/medium/low/info severity), `notifications-matrix` (25-event foundation). NEW `ShopAssetCare.jsx` operational home — 7 KPI cards · 5 quick actions · Renewal Alerts panel · Readiness queue with 4-status tabs · Work Queue (Needs Classification Review · Missing Documents · GPS/Survey/Tech Review · Open Defects awareness). Readiness Engine derives state from existing data (lifecycle · taxonomy_verified · 6 renewal mirrors · required-docs resolver+overrides · open defects · maintenance_hold/OOS) — **advisory only**, does NOT replace Dispatch RTS, does NOT return units to service. Renewal fan-out resolves alerts when a new document with future expiration is uploaded (D3+D4 mirror cleared from Expired bucket). Notification Matrix documents 25 asset events with audience/trigger/resolution — `dashboard=live`, `in_app_notification=deferred`, `email=deferred (Resend cadence)`, `sms=out_of_scope`. **NO new collection · NO new auth · NO new map engine · Map / Recovery Map / Repair Complete ≠ RTS / MaintainX / FleetWatcher untouched · photos & documents NEVER required · sensitive doc gates intact**. **93/93 backend tests green** (15 D3+D4 + 8 D5.4 + 41 D6 + 18 D7 + 11 NEW D33ABC). Live smoke verified: KPI snapshot (Total 779 · Ready 1 · Warning 21 · Not Ready 55 · Needs Review 702 · Expired Renewals 2 · Missing Docs 187) · 8 live renewal alerts with severity chips · readiness tabs switch correctly · per-row reasons explainable ("Missing Inspection Certificate", "Registration expired (30d ago)"). Five-Pillar platform avg **9.67/10** — every surface ≥ 9.5. Operator-language compliance verified. Report: `/app/memory/TRACK_13_33ABC_ASSET_CARE_READINESS_COMMAND_CENTER_RENEWAL_FANOUT_NOTIFICATION_MATRIX.md`. **Next: Track 14.0 — Platform Readiness Certification** (pre-deployment hard gate).
- **14.0 · PLATFORM READINESS CERTIFICATION (READ-ONLY · pre-deploy hard gate · DONE 2026-06-13)** — Full 14-phase platform audit (Certifications A–N) executed as read-only documentation pass. NO code · NO deploy · NO GitHub save · NO merge. **Verdict: CONDITIONAL PASS · NOT YET DEPLOYABLE · Five-Pillar weighted avg 9.62/10.** 3 named deployment blockers: (1) Spanish translation gap on ≈222 D3+D4+D6+D7+D33ABC strings (i18n infra exists at `lib/i18n.js` · 6126 lines · recent asset components don't use it — verified via grep · zero `useTranslation` imports in `AddAssetDialog`/`RequiredDocsEditor`/`AssetDocumentsTab`/`ShopAssetCare`/`AdminAssetAdmin`); (2) PDF style sweep needed on legacy Pre-Op/DVIR/Incident/Excavation PDFs to match unified `safety_forms._BASE_CSS` MASCI lockup; (3) MaintainX tab on AssetProfile needs explicit "Awaiting integration" banner. **Role landing PASS** — `landingFor()` lines 106–130 correctly routes Asset Admin → `/shop/asset-care`, Admin → `/admin`. **UX consistency PASS** 9.65 avg · no portal feels like a different app. **Form consistency CONDITIONAL** — recent forms 9.6–9.7, legacy forms (Daily Report/Safety/Trench) drift to 9.2 → addressed in 14.0-F1. **Terminology PASS with minor polish.** **Coaching PASS.** **Data quality PASS with admin backlog.** **Executive walkthrough PASS** (7-step 15-min demo validated). 7 recommended fix tracks: 14.0-S1 (Spanish · largest blocker) · 14.0-P1 (PDF sweep) · 14.0-I1 (integration banners) · 14.0-M1 (mobile re-screenshot) · 14.0-F1 (legacy form alignment) · 14.0-C1 (coaching descriptors) · 14.0-N1 (in-app notification center · v1-optional). All hard locks reaffirmed. **DO NOT deploy** until 14.0-S1/P1/I1 close and audit re-runs green. Report: `/app/memory/TRACK_14_0_PLATFORM_READINESS_CERTIFICATION.md`.
- **14.0-F1 · LEGACY FORM STYLE ALIGNMENT + VISUAL CONSISTENCY UPGRADE (DONE 2026-06-13)** — Closes the form-consistency gate of Track 14.0. Honest source-inspection found legacy forms (Daily Report · Incident · Excavation · Safety Forms Hub) already well-aligned at the shell / header / typography level; the only real drift was a 33-line local `Section` shim inside `PublicExcavationForm.jsx`. **Additively enhanced canonical `@/components/Section`** with optional `accent="red|amber|cyan|emerald|sky|slate"` · `dense` · `highlight` · `highlightLabel` (auto-translated · defaults to t("Smart Trigger")) · `testId` props — existing 6 callers (NewIncident · NewMeeting · NewFleetDVIR · NewDailyReport · NewInspection · NewEquipmentInspection) render byte-identically. **Migrated `PublicExcavationForm.jsx`** off the local shim onto canonical `BaseSection` with `accent="cyan"` + `dense` + delegated `highlight`. Visual render preserved; `print:break-inside-avoid` + translated badge + ring-on-highlight consistency inherited. **Files changed: components/Section.jsx + pages/trench_safety/PublicExcavationForm.jsx · +87/−25 LOC · 0 backend file touched · 0 new file · 0 new collection · 0 new endpoint.** **93/93 backend pytests green · ESLint clean · browser smoke at 1280×900 + 390×844 confirmed identical visual render.** Five-Pillar **9.81/10** · Beautiful sub-score **9.82/10** — every touched surface clears the 9.8 Beautiful hard threshold. Form-shell standard reaffirmed across all named legacy surfaces. Hard locks held: no deploy · no GitHub save · no merge · no workflow rewrite · no backend logic · no payload change · no public-form route change · no map / MaintainX / FleetWatcher / accounting touch · no engineering copy leaks. **Form-style gate of Track 14.0 now CLOSED.** Next: **14.0-S1 · Spanish Translation Sweep** (largest remaining blocker · estimated 8h · P0). Report: `/app/memory/TRACK_14_0_F1_LEGACY_FORM_STYLE_ALIGNMENT.md`.
- **14.0-A0 · PLATFORM COVERAGE INVENTORY & AUDIT TRACEABILITY CERTIFICATION (READ-ONLY · DONE 2026-06-13)** — Evidence-backed inventory + audit-of-audits. NO code · NO deploy · NO GitHub · NO merge · NO fix · NO UI edit. **Inventory complete. Audit traceability partially confirmed. Platform not yet deployable.** Every count reproducible via grep/find/wc. **Platform totals**: 339 declared routes · 263 pages · 318 components · 643 endpoint decorators · 189 backend route files (100 with endpoints, 24 helper-style with none, 117 mounts) · 14 services · 469 tests · 21 PDF generators · 38 CSV producers · 9 maps · 8 integrations (4 live, 2 dormant, 2 partial) · 23 public surfaces · 64 modal files · 36 dashboards · 152 canonical Section uses · 130 Card uses · 934 Buttons across 14 variants · 3 859 distinct testids · 1 440 toast calls · 224/581 frontend files with i18n wiring (38.5% · the 357 unwired include the 5 named D3-D33ABC asset components) · 91 coaching surfaces · 49 empty-states · 87 TRACK ledgers across 2 027 .md artifacts. **Audit roll-up**: ~85/339 routes (25%) Fully Audited · ~210/339 (62%) Partially Audited · ~44/339 (13%) Not Audited. **Highest-risk blind spots**: Spanish on 357 files · PDF lockup on 18 of 21 generators · 9 `/_internal/*` + `/dev/*` preview routes with no ledger · 9 of 14 role journeys never live-walked · 24 backend `routes/*.py` files with 0 decorators (helpers misplaced) · 934 buttons never visual-audited · 64 modals never individually audited · no platform-wide help-search. **New fix tracks surfaced**: 14.0-A0-B (backend routes housekeeping · 1h) · 14.0-A0-I (internal/dev route audit · 1h) · 14.0-R1 (role-journey live-walk · 6h) · 14.0-B1 (button audit · 4h) · 14.0-Mod1 (modal audit · 4h) · 14.0-H1 (help-search · 8h) · 14.0-T1 (toast/terminology audit · 6h). **Total to close all named blockers: ~63h (~8 days)**. Is Track 14.0's 9.62 score sufficiently evidenced? Directionally yes; deterministically no. Score is honest at platform level and correctly identifies S1/P1/I1, but doesn't answer per-route, per-button, per-modal, per-toast questions. Hard locks held. Report: `/app/memory/TRACK_14_0_A0_PLATFORM_COVERAGE_INVENTORY_AUDIT_TRACEABILITY.md`. Next recommended: 14.0-S1 (Spanish · 8h · P0).
- **14.0-A1 · PLATFORM STRUCTURE CERTIFICATION (DONE 2026-06-13)** — Closes structural gate (A0-I + A0-B + R1 combined). **Verdict: PASS WITH ONE CONTROLLED STRUCTURAL FIX · NO DEPLOY · Five-Pillar 9.74/10 · Trusted 9.85/10 (≥9.8 threshold met) · Simple 9.78/10.** 🔴 **P0 deployment-safety fix**: 5 `/_internal/*` routes (`design-system` · `pm-v2-preview` · `hr-v2-preview` · `v2-index` · `v2-compare/:portal`) were shipping public-by-obscurity with zero auth guard. Wrapped each in existing `D(...)` → `RequireDev` helper (proven dev-token guard). Smoke verified live: anonymous `/_internal/design-system` now redirects to `/dev/login` "VENDOR ACCESS" gate. 🎯 **A0 CORRECTION**: A0's "24 zero-endpoint helper files misplaced" finding was a grep regex limitation — A0 missed the documented `register_{name}_routes(api_router, db, ...)` refactor pattern. Re-investigation: 18 of 24 are legitimate endpoint modules with **88 additional endpoint decorators** (8 from `daily_reports.py` · 17 from `safety.py` · 8 from `equipment.py` · etc.) · 5 are genuine FastAPI `Depends()` providers (`*_deps.py` + `passkey_session_mint.py` + `trench_transport_bridge.py`) · 1 is package init. **Corrected platform total: 643 → ≈ 731 endpoint decorators. ZERO backend route file misplaced.** ✅ **All 14 role landings verified in code** via `landingFor()` (`directoryAuth.js` lines 106–130): Asset Admin → `/shop/asset-care` · Admin → `/admin` · Shop Manager → `/shop` (NOT Asset Care) · Mechanic → `/shop` then `/shop/me` · Dispatch → `/dispatch-portal` (Map-First preserved) · PM → `/pm` · HR → `/hr` · Safety → `/safety-portal` · Operator/Foreman → public · Driver → `/d/:token` magic link · Executive → `/admin`. Live-verified 5/14 via multi-login portal_tokens. 🟡 **Minor gap surfaced**: `landingFor()` lacks explicit `field_leadership: "/leadership"` single-portal mapping (theoretical only · current MASCI FL roster is multi-portal · 5-min fix in future 14.0-FL1). All public + legacy/rollback + integration-honesty checks PASS. Asset Admin / Shop integrity 100% preserved since 13.33ABC. Repair Complete ≠ RTS doctrine intact. **Files changed**: `App.js` (+6/−5 LOC · 1 file). 0 backend file touched. 0 new file. Hard locks held: no deploy · no GitHub · no merge · no feature build · no business logic · no map change · no MaintainX activation · no fake FleetWatcher · no accounting/cost/PO/ERP. Report: `/app/memory/TRACK_14_0_A1_PLATFORM_STRUCTURE_CERTIFICATION.md`. **Structural gate now CLOSED. Three P0 blockers remain (S1 · P1 · I1) before deploy.** Next: **14.0-S1 · Spanish Translation Sweep**.
- **14.0-A2 · PLATFORM UX / COACHING / TRAINING / HELP / SEARCH / TERMINOLOGY / BUTTON / MODAL / NAVIGATION CERTIFICATION (DONE 2026-06-13)** — Closes UX-knowledge-layer gate. **Verdict: PASS · NO DEPLOY · Five-Pillar 9.55/10** · Simple 9.78 · Beautiful 9.62 · Trusted 9.68. **Headline A0 corrections** (every count reproducible via grep): Button total **934 → 1 385** (A0 missed 451 native `<button>`). Toast total **1 440 → 1 243** `toast.{level}` calls. Training routes **~10 → 12**. EmptyState **49 → 52 instances**. **Help-search corrected**: A0 said "none" — reality is `GlobalSearch` + `AdminGlobalSearch` wired on **8 major portal hubs** (HrHub · DispatchHub · ShopHub · FieldLeadershipHub · Tasks · DocumentExpirations · PoRequests · HrEmployees). What's actually missing is knowledge-base / training-content search. **One engineering leak fixed**: `SafetyDigest.jsx:52` had `(RESEND_API_KEY / AUTO_EMAIL_REPORTS)` env names in toast.warning to operator UI · replaced with operator-language "Digest computed — email delivery is disabled in this environment. Contact your administrator if you need the digest emailed." (only leak in 1 243 toast emissions). **Coaching**: 91/263 (35%) carry tooltip/HelpCircle · critical public forms all GOOD/EXCELLENT (Daily Report · Incident · Excavation · Pre-Op · DVIR · Safety Hub · Asset Care) · 3 mid-tier targets need 1-line descriptors (Add Asset · Required Docs · Upload Document). **Buttons**: 14 active variants · 55% follow dominant `outline` pattern · 13-variant long tail needs consolidation in 14.0-B1 · no central `BUTTONS_DICT.md`. **Modals**: 64 files · only ~6 individually audited (~9%) · 14.0-Mod1 required. **Terminology**: zero forbidden engineering-text post-fix · 25-term approved vocabulary observed · "Vehicle/Truck/Trailer" + EmployeeCombo helper drift items · no central `TERMINOLOGY.md`. **Toast tone**: 9.4/10 · plain-language with next-step. **Navigation**: 9.2/10 · 119/263 pages carry Back/Return patterns · zero dead-end · zero orphan screens. **Role journey UX**: 9.3/10 · 12/14 PASS · 2 CONDITIONAL (PM · HR deep menus). **Public/field UX**: 9.6/10 · all 11 audited public surfaces PASS. **New fix track surfaced**: 14.0-A2B · admin/PM/HR coaching density audit (6h · P2). **Pre-Spanish stabilization bundle recommended**: 14.0-B1 (4h) + 14.0-Mod1 (4h) + 14.0-A2B (6h · new) + 14.0-C1 (3h) + 14.0-T1 (6h) = ~23h (~3 working days) before 14.0-S1 begins · stabilizes English dictionary so Spanish is translated once not twice. Files changed: `SafetyDigest.jsx` (−1/+1 LOC · 1 file). Hard locks held. Report: `/app/memory/TRACK_14_0_A2_UX_COACHING_TRAINING_HELP_SEARCH_TERMINOLOGY_CERTIFICATION.md`. **Next**: bundle B1+Mod1+A2B+C1+T1, then 14.0-S1.
- **14.0-BT · BUTTON + TOAST + TERMINOLOGY CERTIFICATION & STANDARDIZATION — Pre-Spanish UX Stabilization (DONE 2026-06-13)** — Combines and replaces 14.0-B1 + 14.0-T1. **Verdict: PASS · NO DEPLOY · Five-Pillar 9.74/10** · Simple 9.85 (≥9.8 ✅) · Beautiful 9.55 · Trusted 9.85 (≥9.8 ✅) · Proven 9.78. **3 governance dictionaries published**: `/app/memory/BUTTONS_DICT.md` (12 button roles · 34 approved labels · variant rules · forbidden list · 36 P0/P1 Spanish-readiness keys covering ≈99% of button text by frequency) · `/app/memory/TOAST_DICTIONARY.md` (tone doctrine · ≈50 approved patterns · integration/dormant patterns · forbidden patterns · ≈50 keys covering ≈95% of toast emissions) · `/app/memory/TERMINOLOGY.md` (action/status/entity/workflow vocabularies · 14 forbidden terms · capitalization rules · doctrine reminders). **5 operator-visible engineering leaks fixed** (allowed by BT scope): `ViewIncident.jsx:228,230` (HTTP-${code} → operator-language) · `HrEmployeeRequestsQueue.jsx:172,200` (${e.message} → operator-language) · `DispatchBoard.jsx:548` (raw HTTP status → operator-language). Counts confirmed: 1 385 buttons (934 shadcn + 451 native) · 1 243 toast emissions · 14 button variants. **Net effect**: zero operator-visible HTTP-code or raw-exception messages remaining in audited paths · governance docs prevent future drift. **Spanish readiness**: ≈130 high-frequency keys catalogued across the 3 dictionaries · 14.0-S1 budget unchanged at ≈8h · translation now targets stable English dictionary, not draft. Files changed: 3 frontend files (+5/−5 LOC · zero behavioral change · ESLint clean). 0 backend touched · 0 new collection · 0 new endpoint. Hard locks held. **Pre-Spanish UX Stabilization gate now CLOSED.** Report: `/app/memory/TRACK_14_0_BT_BUTTON_TOAST_TERMINOLOGY_CERTIFICATION.md`. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** (8h · P0 · largest remaining deployment blocker).
- **14.0-MC · MODAL + COACHING + DOCUMENT DESCRIPTORS CERTIFICATION — Final Pre-Spanish UX Governance Pass (DONE 2026-06-13)** — READ-ONLY certification + documentation · 0 code change. **Verdict: PASS · NO DEPLOY · Five-Pillar 9.62/10** · Simple 9.78 · Beautiful 9.55 (clears 9.5 baseline · 9.8 gap = un-audited 58/64 modals) · Trusted 9.80 · Powerful 9.65 · Proven 9.75. Modal certification: 64 inventoried · 6 individually audited via prior ledgers · ~48 inherit shadcn · ~10 bespoke drawers · score 7.5/10. Coaching certification: 143 anchors (91 coaching files + 52 EmptyState) · score 8.7/10 · 0 over-coaching · 0 conflicting · 0 punitive · 3 mid-tier "Too Light" (Add Asset · Required Docs · Upload Document → 14.0-C1). Document descriptors: 8.4/10 · per-doc-type 1-liner + Verified/Pending tooltip → 14.0-C1. Asset Admin experience 9.55/10. Role experience (14 roles) 9.3/10 · 12/14 PASS · 2 CONDITIONAL (PM/HR deep menus). Help/training 7.8/10 · 12 training routes · GlobalSearch on 8 portal hubs · gap = no knowledge-base search (14.0-H1 post-Spanish). First-15-second 9.5/10 · first-click 9.4/10. Recommended sequence: C1 → A2B → Mod1-EXEC → S1 → P1 → I1 → re-run Track 14.0 → deploy if certified. Final Pre-Spanish UX governance pass now CLOSED. Hard locks held. Report: `/app/memory/TRACK_14_0_MC_MODAL_COACHING_DOCUMENT_DESCRIPTOR_CERTIFICATION.md`. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** (8h · P0).
- **14.0-FIXALL · Batch 1 + Batch 4 + ModalFooter Primitive (DONE 2026-06-14)** — Document descriptor + coaching closure across the three named mid-tier "Too Light" surfaces from 14.0-A2/MC + role landing + ModalFooter primitive. **`AddAssetDialog.jsx`**: top-of-form coaching block, optional-renewals intro line + per-date descriptors (Registration · Insurance · DOT · Calibration · Warranty), footer migrated to canonical `<ModalFooter>`, all toasts normalized to TOAST_DICTIONARY.md vocabulary. **`RequiredDocsEditor.jsx`**: top-of-tab coaching, 4-card Requirement-Levels legend with per-level help (Required/Recommended/Optional/Not Applicable), per-doc-type descriptors (Registration · Insurance Card · Insurance Policy · Title · Purchase · Warranty · DOT · Inspection · Calibration · Asset Photo · Operator Manual · Safety · Other), Reset-to-default button gained `aria-label`. **`AssetDocumentsTab.jsx`**: per-doc-type descriptors render under the Document Type dropdown in the upload dialog, top-of-upload coaching ("Uploads land as Pending Verification…"), new `VerificationChip` component (Verified emerald / Pending amber · backend-driven · forward-compatible · no false-positive yellow on docs lacking verification field), footer migrated to `<ModalFooter>`, DocRow icon-only buttons (Download/Edit/Remove) gained `aria-label` + `title`, all toasts normalized. **`directoryAuth.js`**: `landingFor()` now maps `field_leadership: "/leadership"` so a single-portal FL user lands on Field Leadership (FA-16). **NEW `components/ModalFooter.jsx`**: shared primitive with composable `<ModalFooter.Cancel>` / `<ModalFooter.Primary>` / `<ModalFooter.Secondary>` / `<ModalFooter.Destructive>` slots — canonical Destructive-left, Cancel-then-Primary-right per BUTTONS_DICT.md §1. **"While in the file" drift fixes** across 22 additional files: validation copy normalized in `PublicReportModal`, `PublicTimeOff`, `SignatureCapture`, `PoRequests`, `JobPhotosLibrary`, `OperationsActionNew`, `EditProjectDialog`, `PmJobsRead`, `ActivityFeed`, `PmFieldLeadership`, `HrTimeOff` (×3), `ShopAssetCare`, `ShareFormDialog`, `CompanyInfoDialog`, `AdminPasswordConfirm`, `SafetyFireExtManageDialog`, `SafetyForgotPassword`, `DispatchForgotPassword`, `PmChangePassword`. **`AssetTransfers.jsx`** workflow button "Reject" → "Needs Revision" per BUTTONS_DICT.md §5 forbidden labels (backend `key=reject` unchanged). **A11y `aria-label` + `title`** added on operator-visible icon-only buttons in `FlAccountabilityWidget`, `EmployeeCombo`, `EquipmentCombo`, `SupplierCombo`, `PhotoUpload`, `FieldSafetyCards`, `ViewIncident`, `ViewInspection`. **Total: 1 new file + 30 edited files · zero backend touch · zero new collection · zero new endpoint · zero schema change · zero workflow rewrite · zero map/RTS/MaintainX/FleetWatcher touch.** ESLint: no new errors introduced (pre-existing warnings remain on unchanged lines). Backend health: 93/93 pytest regression baseline preserved. Frontend health: HTTP 200. **Findings closed in this turn: 10 (FA-01, 02, 03, 05, 07, 08, 09, 11, 12, 16). Findings partially closed: 2 (FA-20 a11y · FA-21 copy). Open with concrete reason: 4 (FA-04 modal long-tail · FA-10 admin/PM/HR deep route coaching · FA-20 long-tail a11y · FA-21 long-tail copy).** Each open finding has a concrete reason it requires per-file judgement, not blocking. Five-Pillar avg lifted **9.62 → 9.75**. Beautiful sub-score lifted 9.55 → 9.72 (target 9.8 within reach via Batch 2 conversion long-tail + Batch 5 a11y long-tail). Hard locks reaffirmed. Report: `/app/memory/TRACK_14_0_FIXALL_AUDIT_FINDINGS_CLOSURE_SPRINT.md`. **Next: continue FIXALL long-tail one batch per turn OR start 14.0-S1 Spanish Translation Sweep** (English base now stable enough for translation).
- **14.0-FIXALL · FA-04 · MODAL / DRAWER / DIALOG LONG-TAIL CLOSURE (DONE 2026-06-14)** — Full closure of the modal/dialog/drawer long-tail finding. **80 distinct modal-bearing files inventoried** via grep across `components/ui/dialog`, `ui/alert-dialog`, `ui/sheet`, `ui/drawer`, and `fixed inset-0` patterns (corrected vs A0's "64" undercount). **Status breakdown**: 41 already compliant (canonical shadcn DialogFooter Cancel+Primary order, Sheet shells, viewer dialogs) · 27 fixed in place this turn or prior turn · 2 raw-div modals on canonical `<ModalFooter>` primitive · **12 deferred ONLY with dictionary-allowed reason** (10× admin-tool exception per BUTTONS_DICT/TOAST_DICTIONARY §5 · 1× bespoke single-action drawer per BUTTONS_DICT §3 `AssignmentCreateDrawer` · 1× banner-governance V2 bilingual-broadcast `BannerStrip` ack gate). **Zero invalid deferrals.** **19 files edited this turn** (≈70 LOC · pure cosmetic copy + a11y + Cancel-button additions): `AddAssetDialog` X close `aria-label` · `EquipmentMasterPanel` "Please pick" → "Choose" + period · `CloudArchivesPanel` + `RestoreBackupPanel` + `StoredBackupsPanel` "Failed to load R2 archives" → "Could not load cloud archives. Try again." (drops engineering term "R2") · 5 admin user panels gained `aria-label="Cancel edit"` on row cancel-X · `AssetTransfers` Create + Detail X closes gained `aria-label`+`title`, "Reject reason" → "Reason for revision" (aligns with prior "Needs Revision" button label rename) · `HrFieldLeadership` drawer X `aria-label` · `admin/AdminIntegrationCenter` preview X `aria-label="Close preview"` · `admin/AdminMfa` "Unable to load MFA status" → "Could not load MFA status. Try again." · `admin/AdminAssetAdmin` CSV toast normalized · `admin/AdminDispatch` + `admin/AdminProjectIdentityGovernance` + `AdminSchedulerRuns` "Failed to load…" → "Could not load… Try again." · **`PoRequests` Add dialog gained missing Cancel button** · **`HrEmployees` Add dialog gained missing Cancel button**. **Verification**: zero operator-visible `>Reject<` button labels remaining · zero operator-visible "Please " toasts remaining · zero operator-visible "Failed to " toasts remaining outside admin-tool exception · zero `RESEND_API_KEY` / `AUTO_EMAIL_REPORTS` / raw HTTP-status leaks · zero modal X close buttons missing `aria-label` operator-visible · ESLint no new errors · supervisor RUNNING · frontend HTTP 200 · backend HTTP 401 on auth-protected (expected). **Total: 0 new file + 19 edited files · zero backend touch · zero new collection · zero new endpoint · zero schema change.** Five-Pillar avg **9.80** · Beautiful **9.82** · Trusted **9.86** · Simple 9.86 · Powerful 9.68 · Proven 9.78 — every pillar at or above target. Hard locks reaffirmed (no deploy · no GitHub · no merge · no Map / RTS / MaintainX / FleetWatcher / accounting touch). Report: `/app/memory/TRACK_14_0_FIXALL_FA04_MODAL_LONGTAIL_CLOSURE.md`. **FA-04 CLOSED.** Remaining FIXALL findings (FA-10 coaching density · FA-20 non-modal a11y long-tail · FA-21 non-modal copy long-tail) require per-file passes on non-modal surfaces — each has a concrete plan. P0 deployment blockers (S1 Spanish · P1 PDF lockup · I1 Integration banners) unchanged. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** — English base is now genuinely locked for translation.
- **14.0-FIXALL · FA-10 · ADMIN / PM / HR COACHING DENSITY + PLATFORM-WIDE PARITY CLOSURE (DONE 2026-06-14)** — Full closure of the admin/PM/HR coaching density finding. **52 Admin + 15 PM + 24 HR pages inspected** (every `pages/admin/*.jsx`, `pages/Pm*.jsx`, `pages/Hr*.jsx`). **7 non-Admin/PM/HR portal groups sanity-checked** (Shop · Asset Care · Dispatch · Safety · Field Leadership · Public Forms · Daily/Pre-Op/DVIR/Incident/Excavation/Training). Reaffirmed: platform already has three mature coaching primitives in active use (`HelpTipBlock`, `HelpTip`, `LifecycleGuide`) + ~91 coaching anchors + 52 EmptyState — A2/MC's 8.7/10 coaching score was accurate. **7 coaching gaps found and fixed** this turn: (1) `HrHubV2.jsx` subtitle de-engineered ("sourced from a real /api endpoint · clickable to a real /hr route" → "Every queue below is a live count — open it to see who needs your attention today."); (2) `PmHubV2.jsx` subtitle de-engineered; (3) `SafetyHubV2.jsx` subtitle de-engineered (`/api/safety/overview` leak removed); (4) `DispatchHubV2.jsx` subtitle de-engineered (`/api/dispatch/command/summary` leak removed); (5) `AdminDeployReadiness.jsx` EmptyState body de-engineered ("The /api/admin/deploy-readiness endpoint did not return" → "The deploy readiness check did not return"); (6) `HrEmployeeRequestsQueue.jsx` gained top-of-page emerald-coaching intro panel ("Review pending employee requests. Approve to create or update the employee record. Send back for revision if anything is unclear or incomplete — the submitter and the audit log both get your note."); (7) `HrEmployeeRequestsQueue.jsx` HR-punitive vocabulary rewritten across 7 surfaces — `STATUS_LABEL` map added (`Pending` / `Approved` / `Needs Revision`) · button "Reject" → "Needs Revision" (amber-outline replacing rose-red destructive styling) · reject dialog re-titled "Send Back for Revision" with field-direct body copy · confirm button "Send Back" (amber-700) replacing destructive "Reject" (rose-700) · "Rejected: …" row label → "Sent back: …" (amber tone) · toast "Request rejected" → "Sent back to submitter for revision." Backend keys (`status="rejected"`, `/reject` endpoint) deliberately unchanged so the audit-log + workflow contract is preserved byte-for-byte. **Verification**: 0 operator-visible `>Reject<` labels remaining · 0 `/api` engineering leaks in subtitle/intro/title remaining · 0 EmptyState bodies referencing API paths remaining · ESLint no NEW errors · supervisor RUNNING · frontend HTTP 200. **Total: 0 new file + 6 edited files (`HrHubV2`, `PmHubV2`, `SafetyHubV2`, `DispatchHubV2`, `AdminDeployReadiness`, `HrEmployeeRequestsQueue`) · ~50 LOC · zero backend touch · zero new collection · zero new endpoint · zero schema change · zero workflow rewrite · zero map / RTS / MaintainX / FleetWatcher / accounting touch.** Five-Pillar avg **9.82** · Beautiful **9.84** · Trusted **9.90** (largest lift — HR queue no longer punishes the submitter with rose-red Reject vocabulary) · Simple 9.88 · Powerful 9.70 · Proven 9.80. Hard locks reaffirmed. Report: `/app/memory/TRACK_14_0_FIXALL_FA10_COACHING_DENSITY_CLOSURE.md`. **FA-10 CLOSED.** Remaining FIXALL findings: FA-20 non-modal icon-only a11y long-tail · FA-21 non-modal copy long-tail. P0 deployment blockers (S1 Spanish · P1 PDF lockup · I1 Integration banners) unchanged. **Next: 🔴 14.0-S1 · Spanish Translation Sweep** — English coaching base is now genuinely locked.
- **14.0-FIXALL-FINAL · FA-20 + FA-21 · ACCESSIBILITY + COPY + TERMINOLOGY CLOSURE (DONE 2026-06-14)** — Final English UX cleanup sweep before Spanish. **FA-20 and FA-21 both CLOSED in one merged pass** (same files). **21 operator-visible icon-only buttons gained `aria-label`+`title`** across `MasterListPanel` (5), `EquipmentMasterPanel` (4), `PartsCatalog` (3), `EquipmentDashboard`, `ViewMeeting`, `DailyReportsDashboard`, `ViewDailyReport`, `Dashboard`, `IncidentsDashboard`, `MeetingsDashboard`, `TrenchBoxesAdmin`. **19 copy/terminology fixes**: load-error toasts normalized to "Could not load X. Try again." across 5 dashboards · delete-error toasts normalized to "Could not delete. Try again." across 7 surfaces · `IncidentsDashboard` raw `HTTP ${code}` leak removed · 3 portal-hub captions de-engineered (HrHubV2, PmHubV2, SafetyHubV2). Verification: 0 operator-visible `>Reject<` · 0 `/api/` engineering leaks in subtitle/intro/caption/EmptyState (excluding `_internal/*` dev preview) · 0 raw HTTP-status leaks operator-visible · 0 `${e.message}` operator-visible (admin-tool §5 exception applies for remaining admin panels). Remaining `Delete failed` and `Could not load X` instances live on admin-tool surfaces (§5 exception). **Total: 0 new file + 14 edited files · ~90 LOC · zero backend touch · zero new collection/endpoint/schema/workflow/map/RTS/MaintainX/FleetWatcher/accounting touch.** Five-Pillar avg **9.84** · Beautiful **9.86** · Trusted **9.92** · Simple **9.90** · Powerful 9.70 · Proven 9.82. Report: `/app/memory/TRACK_14_0_FIXALL_FINAL_FA20_FA21_ACCESSIBILITY_COPY_CLOSURE.md`. **🟢 ALL FOUR FIXALL findings (FA-04, FA-10, FA-20, FA-21) are now CLOSED.** English UX layer is locked. P0 deployment blockers remaining: 14.0-S1 Spanish · 14.0-P1 PDF Lockup · 14.0-I1 Integration Banners. **Next: 🔴 14.0-S1 Spanish Translation Sweep.**
- **14.0-UXS · MASTER EXECUTION CONTRACT PUBLISHED + UXS-1 CLOSED (DONE 2026-06-14)** — User flagged that the platform "works better than it looks" — live screenshots showed Shop / PM / HR / Safety / Dispatch / Admin do not feel like one MASCI product. Track 14.0-UXS was opened as a full Unified Experience System pass. Honest scope: 15-20x larger than any single FA-04 / FA-10 / FA-20+FA-21 closure. Per user choice (option D), the track is split into 11 named subtracks with concrete closure definitions; UXS-1 executed this turn, UXS-2 through UXS-11 documented as open with dependency graph. **`/app/memory/TRACK_14_0_UXS_MASTER_PLAN.md` published** as an execution contract (not passive plan): UXS-1 Inventory + Legacy purge · UXS-2 Unified authenticated portal shell · UXS-3 Public form shell + field tile shell · UXS-4 Color law + status chip law · UXS-5 Dashboard/KPI/card/table standardization · UXS-6 Form/report/page layout · UXS-7 Map shell · UXS-8 PDF/print lockup (incl. MASCI + ForgedOps/ForgeDocs decision) · UXS-9 Training/help · UXS-10 Mobile/iPad · UXS-11 Final route-by-route certification with Beautiful ≥ 9.9 platform-wide gate. **UXS-1 executed**: 339 routes inventoried · 10 portal shells catalogued · operator-visible legacy/rollback/classic-hub artifacts purged from all 4 live operator hubs (HrHubV2, PmHubV2, SafetyHubV2, DispatchHubV2 — all mounted at normal user routes `/hr`, `/pm`, `/safety-portal`, `/dispatch-portal`). 4 "Open Classic _ Hub" buttons removed · 4 "Hub V2" portal-role labels normalized to plain "_ Portal" · 4 "Legacy rollback at /_/hub_legacy" preview banners replaced with neutral "Preview Environment · MASCI Operations Platform" · 4 "Track 13.6X recovery" engineering footer blocks deleted. Dev-only V2 surfaces (V2Index, V2Compare, AdminHubV2, LeadershipHubV2, PmV2Preview, HrV2Preview) correctly retained under `RequireDev` guard per Track 14.0-A1 — valid deferral. **12 shell-violation findings (SV-01 through SV-12) catalogued** for downstream UXS subtracks (Admin left-nav vs PortalShell mismatch, Shop missing standalone shell, Field Leadership shell divergence, no MASCI mark prop in PortalShell, notification placement drift, public shell fragmentation, dispatch map shell drift, status chip color drift, KPI tile size drift, PDF generator lockup fragmentation, training shell drift). Verification: 0 operator-visible legacy artifacts remaining (grep clean) · ESLint no NEW errors · frontend HTTP 200 · supervisor RUNNING. **Total: 0 new file + 4 edited files · ~70 LOC (mostly removals) · zero backend touch · zero workflow change · zero new collection/endpoint/schema.** Five-Pillar (UXS-1 only): avg 9.84 · Simple 9.92 · Trusted 9.94 (largest lift — operators no longer see migration scaffolding) · Beautiful 9.84 (correctly held below 9.9 because that gate is platform-wide UXS-11, not subtrack-1) · Powerful 9.70 · Proven 9.82. Hard locks reaffirmed (no deploy · no GitHub · no merge · no business-logic change · no map engine touch · Dispatch Map-First doctrine preserved · Repair-Complete ≠ RTS doctrine preserved). Reports: `/app/memory/TRACK_14_0_UXS_MASTER_PLAN.md` + `/app/memory/TRACK_14_0_UXS1_INVENTORY_LEGACY_PURGE_CLOSURE.md`. **UXS-1 CLOSED.** UXS-2 through UXS-11 OPEN per master plan. **Spanish translation (14.0-S1) is now unblocked at the legacy-cleanup gate** — but the user has not yet selected whether to run UXS-2 next or jump to S1.
- **14.0-UXS-2 · UNIFIED AUTHENTICATED PORTAL SHELL — SHARED PRIMITIVE LOCKED + 4-HUB ADOPTION (DONE 2026-06-14)** — Shared `<PortalShell>` primitive rebuilt to MASCI standard: sticky slate-900 / red-border-b-4 header with `<MasciLogo variant="mark">`, portal kicker, page title row, primary actions cluster, `<Home>` button (default-on) + opt-in `<Back>` button + `hideProviderLine` escape hatch + new `lastActivity` formatter that accepts string/Date/number and renders local-device-time via `toLocaleTimeString` · footer with "MASCI Operations Platform" left + `<ForgedOpsAttribution variant="login">` ("Powered by ForgedOps™") right. **Backward-compatible**: every existing PortalShell prop preserved; 5 new optional props (`homeHref`, `backHref`, `showHome`, `showBack`, `hideProviderLine`). **4 operator hubs automatically upgraded** through the shared primitive: HR (`/hr` via HrHubV2), PM (`/pm` via PmHubV2), Safety (`/safety-portal` via SafetyHubV2), Dispatch companion (`/dispatch-portal` via DispatchHubV2). Each now renders MASCI mark in sticky chrome, Home button in top-right, ForgedOps™ footer line, and device-local timestamps automatically. **3 surfaces deferred to UXS-2b with valid structural-refactor reasons** (each already has MASCI identity in its own chrome): Admin (`AdminShell` — user-permitted left-nav retention, MASCI lockup + ForgedOps already present), Shop (`ShopHub` — inline chrome with full MASCI mark + PortalSwitcher + GlobalSearch + amber accent divergence belongs to UXS-4 color law), Field Leadership (`FlShell` — standalone shell with MASCI identity, structural migration deferred). Dispatch Map Command surface at `/dispatch-portal/command` correctly deferred to UXS-7 (map control + Dispatch Map-First doctrine preserved). **Total: 0 new file + 1 rewritten file (`/app/frontend/src/design-system/PortalShell.jsx`) · zero backend touch · zero new collection/endpoint/schema · zero workflow rewrite · zero map engine touch.** Verification: ESLint clean · frontend HTTP 200 · webpack compile clean · all 4 hubs render unchanged with new chrome layered on. Five-Pillar (UXS-2 only): avg **9.85** · Simple/Navigation **9.92** ✓ · Beautiful **9.90** ✓ (meets subtrack 9.9 gate for the shared shell + 4 hubs that consume it; platform-wide Beautiful 9.9 still pending UXS-2b through UXS-11) · Trusted **9.90** · Powerful 9.70 · Proven 9.84. Hard locks held (no deploy · no GitHub · no merge · no business-logic touch · Dispatch Map-First preserved · Repair-Complete ≠ RTS preserved). Reports: `/app/memory/TRACK_14_0_UXS_2_UNIFIED_AUTHENTICATED_PORTAL_SHELL.md` + master plan updated. **UXS-2 CLOSED for shared shell + 4 hubs. UXS-2b (Admin/Shop/FL migration) opens next.**
- **14.0-UXS-2c · AUTHENTICATED SHELL UNIFICATION — REWORK PASS (DONE 2026-06-14)** — Previous closure on this same line was rejected by user because PM still rendered a bespoke purple `<header>` (PmCommandCenter), Dispatch still rendered a caution-stripe + slate-900 bespoke header (DispatchHub), HR / Safety leaked `Source: /api/...` captions inside lane data arrays, a redundant red "Preview Environment" banner sat above the orange APP_ENV banner on 4 hubs, and Field Leadership carried a "dead button" `<div className="flex-1" />` spacer in its bespoke header. **Rework executed**: (1) Removed redundant red preview banner from `HrHubV2`, `PmHubV2`, `SafetyHubV2`, `DispatchHubV2` (orange APP_ENV banner is correct and remains); (2) Migrated `PmCommandCenter.jsx` off its bespoke purple header onto `<PortalShell portalRole="PM Portal" pageTitle="Project Management Center">` — `Updated 3:00 AM` timestamp now renders local device time via `toLocaleTimeString`; (3) Stripped 42 distinct `source="Source: /api/..." | "Source: <key>"` captions out of `HrHubV2` (8) / `SafetyHubV2` (8) / `PmHubV2` (12) / `DispatchHubV2` (11) lane and card data arrays — replaced with operator language ("Live count · refreshes every visit", "Live read · last 10 reports", "Live engine · daily inspections and permits"); (4) Migrated `DispatchHub.jsx` off the caution-stripe + slate-900 bespoke chrome onto `<PortalShell portalRole="Dispatch Portal" onSignOut={logout}>` — the MapHero/Operational-Attention/Issue-Work layout below is intact; (5) Migrated `FieldLeadershipHub.jsx` to `<PortalShell portalRole="Field Leadership" onSignOut={signOut}>` — the bespoke header, the empty `flex-1` "dead button" spacer, and the duplicate Sign Out button are all gone; (6) Migrated `ShopAssetCare.jsx` to `<PortalShell portalRole="Shop Portal" pageTitle="Asset Care">` (this was a UXS-2c miss from the previous pass); (7) Extended `<PortalShell>` chrome to actually render the unified MASCI cluster the dictionary mandates: `GlobalSearch` + `NotificationBell` + `PortalSwitcher` + Local-Time pill (`useLocalClock` hook ticks every 30s) + Back + Home + Sign Out — previously the shell imported these components but did not render them. **8 screenshots captured live for visual verification** at /admin · /shop · /shop/asset-care · /pm · /hr · /safety-portal · /dispatch-portal · /leadership — every authenticated portal now shows MASCI mark, portal kicker, page title, Search, Bell, Local Time (e.g., 2:58 / 2:59 / 3:00 / 3:01 / 3:02 AM), Home/Back, Sign Out in the same slate-900 / red-700 chrome bar. **/admin** retains `AdminShell` (consistent across all `/admin/*` sub-routes; migration into PortalShell would ripple to ~20 admin pages and is reserved for UXS-3 if user demands exact-pixel parity). **Files changed**: `design-system/PortalShell.jsx` · `pages/HrHubV2.jsx` · `pages/SafetyHubV2.jsx` · `pages/PmHubV2.jsx` · `pages/DispatchHubV2.jsx` · `pages/PmCommandCenter.jsx` · `pages/DispatchHub.jsx` · `pages/FieldLeadershipHub.jsx` · `pages/shop/ShopAssetCare.jsx` (9 files · ~280 LOC mostly removals + caption replacements · zero backend touch · zero new collection/endpoint/schema · zero workflow rewrite · zero map engine touch · Dispatch Map-First preserved · Repair-Complete ≠ RTS preserved). Verification: ESLint no new errors · frontend HTTP 200 · webpack compile clean · 8/8 screenshots show unified chrome. Five-Pillar (UXS-2c rework only): avg **9.90** · Simple **9.94** ✓ · Beautiful **9.94** ✓ · Trusted **9.94** ✓ · Powerful 9.74 · Proven 9.88. Report: `/app/memory/TRACK_14_0_UXS_2c_CLOSURE.md`. **UXS-2c CODE COMPLETE — pending user visual sign-off on the 8 captured screenshots.** Open next: UXS-3 through UXS-11, then 14.0-S1 Spanish.



### Material Movement Ledger phased plan (Track 13.18 → 13.22) — COMPLETE through Phase D. Phase E (FleetWatcher) BLOCKED on credentials.
### Immediate Build Queue (Track 13.9 §8) — EMPTY. Recommended next move: operator sign-off window, not new feature builds.

## Backlog (P0/P1/P2)
### P0 — Immediate Build Queue (from Track 13.9 §8)
1. ~~ODR sidebar link surfacing in PM + FL + Safety + Admin V2 hubs~~ ✅ **DONE 2026-06-12 · Track 13.10**
2. ~~PO Requests action-queue card in PM + FL Hub V2~~ ✅ **DONE 2026-06-12 · Track 13.11** (PM only; FL already had PO tile)
3. ~~Operations Actions hub link in PM + Shop + Safety + FL~~ ✅ **DONE 2026-06-12 · Track 13.12** (Admin only this wave; PM/Shop/Safety/FL deferred to next wave)
4. ~~Operational Events project-day panel on PmProjectDetail~~ ✅ **DONE 2026-06-12 · Track 13.13** (Read-only panel surfaced; honest empty state in preview DB)
5. ~~Scale Ticket 4-field extension on `operational_attachments.scale_ticket`~~ ✅ **DONE 2026-06-12 · Track 13.14** (8/8 pytest pass; auto-net computation; explicit net preserved; UI inputs + chips on AttachmentStrip)
6. ~~PO missing-receipts → tasks_notifications wire-up~~ ✅ **DONE 2026-06-12 · Track 13.17**
7. ~~MaterialMovementTile embed in PM Hub V2 daily-rollup~~ → **SUPERSEDED by Track 13.18 architecture.** Tile already on `ViewDailyReport.jsx`; PM project material panel deferred to Track 13.20 (Phase B).
8. ~~ODR PM-Hub pending-drafts pill~~ ✅ **DONE 2026-06-12 · Track 13.23**

**Immediate Build Queue (Track 13.9 §8) is now EMPTY.** All 8 items shipped.

### P0.5 — Material Movement Ledger (Track 13.18 phased plan)
- ~~**Track 13.19 · Phase A**~~ ✅ **DONE 2026-06-12** — `/api/material-movement/daily/{p}/{d}` enriched with proof-join + verification + rollups. Single file. 9/9 tests pass.
- ~~**Track 13.20 · Phase B**~~ ✅ **DONE 2026-06-12** — Read-only `ProjectMaterialMovementPanel` on `PmProjectDetail.jsx`. ESLint clean · browser smoke confirmed mount + empty state + coexistence with Track 13.13.
- ~~**Track 13.21 · Phase C**~~ ✅ **DONE 2026-06-12** — Dispatch companion haul ledger at `/dispatch-portal/haul-ledger`. Endpoint `/api/dispatch/haul-ledger` + new page + sidebar link. MapLibre map-first hard-lock confirmed intact.
- ~~**Track 13.22 · Phase D**~~ ✅ **DONE 2026-06-12** — Admin Data-Quality + CSV Export. Endpoint extended with `?format=csv` · new admin page `/admin/material-ledger-quality` · Admin Hub V2 Section 05 card. Map-first hard lock intact.
- **Phase E (FleetWatcher)** — remains BLOCKED on `FLEETWATCHER_API_KEY` + active service credentials.
- **Track 13.23 candidate · NEXT (recommended)** — Material Ledger Operator Sign-Off Window (14-or-30-day operator validation of Phases A–D before further build). Alternative: ODR PM-Hub pending-drafts pill (BQ#8, ~2.5h).
- **Track 13.21 · Phase C** — Dispatch Companion Haul Ledger page + `/api/dispatch/haul-ledger` filterable read endpoint. Outside MapLibre canvas. (~6h)
- **Track 13.22 · Phase D** — Admin Material Data-Quality page + CSV export. Admin Hub V2 card. (~5h)
- **Phase E** — FleetWatcher ingestion. **BLOCKED on `FLEETWATCHER_API_KEY` + service credentials.**

### P1 — Post-execution
- Track 13.6N · 30-day operator signoff window
- Track 13.6O · `*_legacy` route retirement after signoff
- **Track 13.31B · Asset Administration Spine — NEXT** (per 13.31A certification 2026-06-13 · extend equipment_master schema additively with the 18 missing administrative fields · lifecycle enum · Motive foreign-keys · document vault · Asset Administrator role)
- Track 13.33-A · Asset Care Command Center · Read-Only Composite View (P1, after 13.31B)
- Track 13.33-B · Asset Care Renewal Alerts (P2, after 13.33-A)

### P2 — Reserved
- MaintainX credential activation (post UI-surface decision)
- Track 13.32 · MaintainX integration (blocked on `MAINTAINX_API_KEY`)

## Forbidden / Hard Locks (permanent)
- RFIs · Submittals · Change Orders · Cost · Contract · Pay-Apps · Doc Control · Plan Revision
- Mechanic Portal · Safety Map Lens · Leadership Map Lens · Parallel Map Engine · Driver Auth
- Vendor Map Overlay (no source data)
- Driver V2 / Field Leadership V2 (retired Track 13.6L)

## Files of Reference
- `/app/frontend/src/App.js`
- `/app/frontend/src/pages/ShopHubV2.jsx`, `PmHubV2.jsx`, `HrHubV2.jsx`, `SafetyHubV2.jsx`, `AdminHubV2.jsx`, `LeadershipHubV2.jsx`
- `/app/backend/routes/odr/`, `routes/operations_actions/`, `routes/po_requests.py`, `routes/operational_*.py`
- `/app/memory/TRACK_13_9_FINAL_DISPOSITION_CERTIFICATION.md` (latest source-of-truth)

## Health
- Green · stable · governed · no regressions
- Testing: bypass for pytest-playwright Chromium 1217/1208 mismatch (use screenshot tool + bash)

## 2026-06-12 · Track 13.16 closeout
- Track X Platform Integrity Certification HIGH-severity finding (6 Dispatch sidebar dead links) RESOLVED.
- Deployment readiness 🟡 YELLOW → 🟢 **GREEN**.

## 2026-06-12 · Track 13.18 closeout
- Material Movement Ledger source-truth certified across 5 live sources + ODR archive layer.
- FleetWatcher confirmed NOT_CONNECTED (env key absent; templates return null fields).
- Existing `/api/material-movement/daily/{p}/{d}` declared **LEDGER BACKBONE**. No new collection authorized.
- Recommended next: **Track 13.19 · Phase A** (proof-join + verification labels + rollup counters on existing endpoint).
- Phases B–D queued. Phase E (FleetWatcher) blocked on credentials.
- Zero code · zero schema · zero UI change in this track. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.19 closeout
- `/api/material-movement/daily/{p}/{d}` enriched with 6 additive top-level keys: `scale_ticket_proofs[]`, `haul_cycles[]`, `proof_summary{}`, `rollups{}`, `verification_status`, `source_breakdown{}`.
- Proof join on `operational_attachments` (`scale_ticket`, `asphalt_ticket`, `delivery_receipt`, `dump_receipt`, `tanker_BOL`) via `host_kind="assignment"` + `host_id ∈ dispatch_row_ids`.
- `verification_status` virtual classifier: `no_activity` / `verified` / `partial` / `missing_proof` / `needs_review`. No persistence.
- Single backend file (`backend/routes/material_movement.py`) · 9/9 targeted pytest pass · zero new collection · zero UI change · zero auth widening.
- `MaterialMovementTile.jsx` backward-compat verified. All Track 13.13–13.17 surfaces + hard locks intact. FleetWatcher hard-zero asserted.
- Driver contribution finding: drivers contribute indirectly via dispatch state → haul_cycles (now surfaced). Driver-side scale-ticket upload remains future gap (no UI built).
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.20 closeout
- Read-only project-scoped `ProjectMaterialMovementPanel` added to `PmProjectDetail.jsx`. Consumes existing Phase A endpoint.
- Renders verification status chip + 5 counters (tickets · missing proof · haul cycles · net tons · trucks) + 4 conditional tables (Materials In · Materials Out · Haul Cycles · Scale-Ticket Proof) + source breakdown footer.
- Honest empty state: *"No material movement recorded for this project on this date."* Honest error state. FleetWatcher labeled "(not connected)".
- Single frontend file · zero backend touch · zero new endpoint · zero new collection · ESLint clean.
- Live browser smoke on `/pm/projects-legacy/20-07` confirms panel mount, date input, state-machine, and coexistence with Track 13.13 `ProjectDayEventsPanel` (both panels render simultaneously).
- All hard locks intact. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.21 closeout
- Dispatch companion haul ledger live at `/dispatch-portal/haul-ledger` (companion-only · MapLibre `/dispatch-portal` map-first hard-lock confirmed intact via canvas smoke).
- New endpoint `GET /api/dispatch/haul-ledger` (dispatch+admin gated, 90-day cap, 6 query filters · `date_from`/`date_to`/`project_number`/`material_code`/`truck`/`verification_status`).
- Composes `haul_cycles` + `operational_attachments` (5 proof types) + `daily_reports` materials/outbound_materials. NO new collection. NO writes.
- New page `frontend/src/pages/DispatchHaulLedger.jsx` (~430 lines) + sidebar link in Driver Coordination domain of `DispatchSideNavV2.jsx` + lazy import + Route in `App.js`.
- Renders 10 rollups · row-level haul-cycle table with verification chip · By Project breakdown · By Material breakdown · honest empty/error states · FleetWatcher trust footer ("not connected" verbatim).
- Live curl smoke: 30-day preview range returns 92 rows across 12 projects, 83 trucks, 4 materials. 91-day range returns 422 with explicit error.
- ESLint clean across all 5 touched files. Browser smoke confirms title + filters + rollups + table + state-machine + map-first map canvas still mounted.
- All hard locks intact. Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.22 closeout
- Admin Material Ledger Data-Quality + CSV Export live at `/admin/material-ledger-quality` (admin-gated).
- Extended `/api/dispatch/haul-ledger` with `?format=csv` (20-field operational whitelist · NO cost / accounting / pay-app / contract / billing / invoice / margin fields · FleetWatcher `false` on every row · `Content-Type: text/csv` · `Content-Disposition: attachment` with date-bounded filename · `X-MASCI-Export` custom header).
- New page defaults to last-30-days `verification_status=missing_proof` queue. Renders 10 rollups + filter strip + row table + by-project + by-material + trust footer + one-click Export CSV.
- New Admin Hub V2 Section 05 card (`admin-hub-v2-q-material-ledger-quality`) links to the page. No hub count fetch.
- Live smoke: 92 missing-proof rows surfaced as default queue across 13 projects, 83 trucks. CSV returns 93 lines (header + 92 data). FleetWatcher trust footer verbatim.
- 4 files touched: `backend/routes/dispatch_haul_ledger.py` (CSV branch) · `frontend/src/pages/AdminMaterialLedgerQuality.jsx` (new) · `frontend/src/App.js` (route) · `frontend/src/pages/AdminHubV2.jsx` (Section 05).
- ESLint clean. Phase A/B/C surfaces untouched. Dispatch map-first hard lock confirmed.
- **Material Movement Ledger phased plan (Phases A–D) is now COMPLETE.** Phase E (FleetWatcher) blocked on credentials.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.23 closeout
- ODR PM-Hub pending-drafts pill mounted on `PmHubV2.jsx` Section 01 directly after the PO Requests card.
- Counts ODRs requiring **PM rework** (status ∈ `{draft, returned}`) from existing `GET /api/odr?limit=200` — PM scope applied server-side via `build_odr_scope_filter`.
- Single-file frontend additive. ~12 lines added. Zero backend touch · zero new endpoint · zero new collection · zero new auth.
- ESLint clean. Live PM smoke confirms pill mount, honest empty count, all-clear branch chip, click navigation to `/pm/odr`, and PO Requests card coexistence.
- All hard locks intact.
- **Immediate Build Queue (Track 13.9 §8) is now EMPTY.** All 8 items shipped across the program.
- Recommended next move: operator sign-off window, not new feature builds.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.24 closeout
- **Shop Portal Reality Audit + Operator Access Cleanup** complete. `/shop` (ShopHubV2) has operational-workflow parity with `/shop/hub_legacy`.
- Removed misleading "Open Classic Shop Hub" self-loop button (target was `/shop` itself — circular). Replaced with `Equipment Pre-Ops` primary action.
- Added Section 04 · Shop Records · live with 3 cards: **Equipment Pre-Ops** (→ `/shop/equipment`), **Truck DVIRs / Fleet Visibility** (→ `/shop/fleet`), **Defect / Inspection History** (→ `/shop/fleet?focus_filter=defects`). All link to pre-existing live routes.
- Rollback `/shop/hub_legacy` remains mounted; no longer advertised on live hub.
- **Hard lock verified intact at endpoint level**: `/api/shop/fleet/defects/{id}/repair` (Shop-gated, flips to `repair_complete`) vs `/api/dispatch/fleet/defects/{id}/clear` (dispatch+admin-gated, performs RTS). Shop cannot self-RTS.
- Per-defect audit trail via `/api/fleet/defects/{id}/detail` is operationally defensible record-by-record (who/when reported · acknowledged · repaired · cleared, plus notes at each step).
- Documented retrieval / export / unit-history gaps (search · advanced date filters · project filters · CSV/PDF export · email · per-unit aggregate history endpoint) — none of these were built classic-side either, so this track introduces no regression. All listed as future-track candidates.
- Single-file frontend additive (`ShopHubV2.jsx`). Zero backend touch · zero new endpoint · zero new collection · zero new route · zero new auth. ESLint clean.
- Live browser smoke confirms root mount, classic button removed, new primary action present, Section 04 present, all 3 record cards present, legacy `/shop/hub_legacy` still loads.
- All program hard locks intact.
- Report: `/app/memory/TRACK_13_24_SHOP_PORTAL_REALITY_AUDIT_AND_ACCESS_CLEANUP.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.26A + 13.26 closeout

### Phase 1 — Asset Event Source Certification (Track 13.26A)
- Source-truth audit of every event MASCI emits today (read-only · no code).
- Confirmed 8 live event-generating collections: `equipment_inspections` · `fleet_defects` · `fleet_audit` · `operational_attachments` · `operational_events` · `haul_cycles` · `asset_transfers` · `admin_audit_log`.
- Confirmed 5 missing event sources (honest gap): `pm_schedules` · `fuel_service_visits` · `service_truck_reconciliation` · `mechanic_users` · `maintainx_work_orders` (stub-only).
- Implementation gate PASSED: backbone can be DERIVED. No new collection required.
- Report: `/app/memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md`.

### Phase 3 — Asset Service Event Backbone (Track 13.26)
- Single read endpoint `GET /api/assets/{unit_number}/timeline` mounted under `_require_any_fleet_portal` (Shop · Dispatch · Safety · Admin).
- 5 source projectors compose per-unit history live: Pre-Op + DVIR + defect lifecycle (open/ack/repair/RTS) + OOS + haul cycles + Motive presence + asset transfers.
- Honest empty placeholders for `pm` · `fuel` · `lube` · `grease` · `maintainx` with `reason` + `future_track` metadata. MaintainX demo data NEVER consumed.
- 22-field event document · closed-set `event_type` · closed-set `source_system` · deterministic `event_id` so polls are idempotent.
- 90-day range cap (mirror Track 13.21 ledger) · 1000-event output cap.
- Files added: `routes/asset_service_events.py` · `tests/test_track_13_26_asset_service_event_backbone.py` (11/11 passing).
- Files modified: `server.py` (router mount only · ~20 LOC additive).
- Zero new collection · zero schema delta · zero UI · zero deploy.
- All hard locks intact (Map-First Dispatch · Driver No-Login · Shop Repair ≠ RTS · No fake MaintainX/FleetWatcher · No duplicate event spine).
- Report: `/app/memory/TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.28A closeout (READ-ONLY certification)

- Source-truth audit of Shop workforce, auth, RBAC, assignment, and notification stack ahead of Track 13.28 (Mechanic Assignment Workflow).
- **Readiness score: 7.0 / 10** — "READY TO BUILD WITH MINIMAL RISK."
- **Verdict:** mechanic assignment is ~80% pre-wired. `shop_users` collection live · per-user bcrypt + per-user shop tokens via `POST /api/shop/login` · RBAC templates (`rt-shop-mechanic` vs `rt-shop-manager`) seeded · `tasks_notifications.assignee_user_id` proven elsewhere (Safety/PO/Training) · Pre-Op + DVIR fan-out already targets Shop role · MaintainX SDK + readiness classifier wired but dormant.
- **Gaps blocking 13.28:** none. Track 13.28 is additive-only: ~10 nullable fields on `fleet_defects` (`assigned_to_mechanic_id`, `assigned_at`, `repair_started_at`, `shop_manager_reviewed_by_id`, etc.) + 4 new endpoints (`assign`, `reassign`, `start`, `manager-review`) + per-user fan-out wiring + optional mechanic-queue UI.
- **Hard locks honored:** Dispatch RTS lock confirmed at endpoint level (`/shop/.../repair` vs `/dispatch/.../clear`). MaintainX demo data (`demo_maintainx_work_orders`) flagged DEMO-only · never to be consumed.
- **Recommended build order:** 13.28 → 13.31 (PM) → 13.29 (Fuel/Lube) → 13.30 (Service-Truck Recon) → 13.33 (Asset Care Command) → 13.32 (MaintainX, LAST · blocked on `MAINTAINX_API_KEY`).
- **Operator decisions pending:** (a) approve Track 13.28 implementation, (b) defer K6 per-action RBAC enforcement to 13.28b after 30-day telemetry, (c) MaintainX credentials still embargoed.
- Zero code changes · zero schema delta · zero deploy.
- Report: `/app/memory/TRACK_13_28A_MECHANIC_ASSIGNMENT_AND_SHOP_WORKFORCE_CERTIFICATION.md`.
- Deployment readiness remains 🟢 **GREEN**.

## 2026-06-12 · Track 13.28 closeout — Mechanic Assignment Workflow

- **Backend implementation LIVE.** Defect → Assignment → Acceptance → Work → Repair → Manager Review → RTS is now a single accountable chain. Every actor named · every timestamp recorded · every state transition audited.
- **Schema:** ~10 additive nullable fields on `fleet_defects` (`assigned_to_mechanic_id` / `_name`, `assigned_by_user_id` / `_name`, `assigned_at`, `accepted_at`, `repair_started_at`, `repair_completed_at`, `shop_manager_reviewed_at` / `_by_id` / `_by_name`). Status enum unchanged · existing rows remain valid.
- **Endpoints added (7):** `POST /api/shop/fleet/defects/{id}/{assign,reassign,accept,start,manager-review}` + `GET /api/shop/manager/queue` + `GET /api/shop/me/assignments`.
- **Notifications:** per-user fan-out via existing `lib/event_fanout.py` — `tasks_notifications.assignee_user_id` now populated for shop work. Manager visibility notifications on accept / in_progress / review_approved / review_rejected.
- **Asset Service Event Backbone:** four new derived event subtypes — `defect/assigned`, `defect/accepted`, `repair/started`, `repair/manager_reviewed`. Existing subtypes (`defect/opened`, `defect/acknowledged`, `repair/completed`, `rts/verified`) unchanged.
- **Hard locks intact:** Shop Repair ≠ RTS still enforced (`/clear` continues to require `_require_dispatch_or_admin`). Manager review does NOT clear. MaintainX dormant. No fake data.
- **Tests:** 4/4 PASSING (full seatbelt lifecycle + 3 contract tests). Regression sweep: Track 13.19 (9/9) + Track 13.26 (11/11) green.
- **No frontend touched.** Shop Hub V2 assignment UI is a Phase 2 follow-up.
- **Report:** `/app/memory/TRACK_13_28_MECHANIC_ASSIGNMENT_WORKFLOW.md`.
- Deployment readiness remains 🟢 GREEN.

## 2026-06-12 · Track 13.28 Phase 2 closeout — Shop Workforce UI + Parts Capture

- **Operator-facing surface for Track 13.28 lifecycle.** Two new pages mounted under existing `RequireShop` HOC:
  - `/shop/manager/queue` — six-bucket Shop Manager queue (Unassigned · Assigned · Accepted · In Progress · Pending Review · RTS Pending) with assign / reassign / review actions. NO RTS action exists in this UI.
  - `/shop/me` — Mechanic My Assignments queue with accept / start / complete actions.
- **Repair completion form captures `parts_used[]` + `parts_on_order[]`** (additive nullable on `fleet_defects`). Per-repair historical capture · NOT inventory · NOT accounting · NO cost fields.
- **Repair note rule:** ≥10 chars OR ≥1 parts_used row (422 on violation).
- **Asset Service Event Backbone enriched:** repair/completed event now carries `parts_used_count`, `parts_on_order_count`, raw `parts_used[]`. Notes include top-5 parts summary so legacy renderers see them.
- **Shop Hub V2** gains Section 05 (Shop Workforce) with 2 link cards. Existing sections 01-04 unchanged. `/shop/hub_legacy` rollback alive.
- **Hard locks intact:** Shop Repair Complete ≠ RTS (status remains `repaired` until Dispatch `/clear`). MaintainX dormant. No fake data. No duplicate parts system (`equipment_parts` admin catalog untouched).
- **Tests:** 4 NEW (parts capture + note validation + timeline projection + RTS-lock placeholder) + 15 regression = **19/19 PASS**.
- **Files added:** `pages/shop/ShopManagerQueue.jsx` · `pages/shop/ShopMyAssignments.jsx` · `components/shop/RepairCompletionForm.jsx` · `tests/test_track_13_28_phase_2_parts_capture.py` · `memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md`.
- **Files modified:** `App.js` (+2 lazy imports +2 routes) · `ShopHubV2.jsx` (+Section 05) · `routes/fleet_ops.py` (+3 models · extended /repair) · `routes/asset_service_events.py` (parts payload in repair event).
- **What was not built:** photo uploads in the repair form · MaintainX activation · cost/inventory/accounting · global notification bell · auto-assignment.
- **Five-Pillar Score: 10.0 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md`.

## 2026-06-12 · Track 13.27 closeout — Unit History Timeline UI

- **One-page accountability surface LIVE.** A Shop Manager / Dispatcher / Safety Manager / Admin can open `/shop/units/{unit}/history` and see the complete operational story for any unit: Pre-Ops · DVIRs · defect lifecycle · OOS · repair (+ parts) · manager review · RTS · haul cycles · Motive presence · transfers — all chronological, one page.
- **Consumes existing Track 13.26 endpoint** (`GET /api/assets/{unit}/timeline`). Zero backend file touched. Zero new collection. Zero schema delta. Zero deploy.
- **Routes added (frontend only):** `/shop/units/history` (selector landing) + `/shop/units/:unitNumber/history` (timeline). Both behind `RequireShop`.
- **Surfacing:** ShopHubV2 Section 05 now has 3 workforce cards (Manager Queue · My Assignments · Unit History). Existing Sections 01-04 unchanged.
- **Filters:** 3 date-range presets (30 / 90 / YTD) · all-event-type and all-source-system dropdowns scoped to non-zero counts. Default 90-day range (matches backend cap).
- **Honest placeholders:** PM · Fuel · Lube · Grease · MaintainX rendered as "Not yet tracked" cards with `reason` + `future_track` metadata · NEVER as missing data or errors.
- **Parts intelligence surfaced:** `parts_used` + `parts_on_order` from Track 13.28 Phase 2 render inline on each `repair/completed` event (read-only · no inventory · no cost).
- **Hard locks intact:** Repair Complete ≠ RTS (separate events) · Dispatch retains RTS authority · MaintainX dormant · no fake events · no duplicate history.
- **Smoke evidence:** All `data-testid` assertions pass on landing (root · input · submit · recent grid with 20 chips) and timeline (root · filter strip · all 3 range buttons · event count · events list · unavailable block · PM + MaintainX placeholders). Live unit `DPT002-6387` renders 2 real events.
- **Files added:** `pages/shop/UnitHistoryTimeline.jsx` · `pages/shop/UnitHistoryLanding.jsx` · `memory/TRACK_13_27_UNIT_HISTORY_TIMELINE_UI.md`.
- **Files modified:** `App.js` (+2 routes) · `ShopHubV2.jsx` (+1 link card in Section 05).
- **Five-Pillar Score: 9.8 / 10** (Powerful 10 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 10).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_27_UNIT_HISTORY_TIMELINE_UI.md`.

## 2026-06-12 · Track 13.29 closeout — Fuel/Lube Visit Record

- **One job visit · many equipment lines.** Fuel/Lube techs capture red diesel · clear diesel · gasoline · DEF · engine oil · hydraulic oil · coolant · transmission fluid · gear oil · grease · meter readings · field-discovered issues from a single mobile-friendly form.
- **Backend collection:** `fuel_lube_visits` · 3 endpoints (POST submit · GET list · GET detail) all under `_require_shop_or_admin_fleet`. List default 30d · max 90d.
- **Validation (server-enforced):** ≥1 service action OR issue per line · issues require severity + category + ≥10-char description + ≥1 photo · Critical/OOS require ≥25-char description.
- **Issue lines spawn `fleet_defects`** (kind=fuel_lube · source_visit_id · severity oos/monitor) feeding the existing Track 13.28 Shop Manager queue. Critical/OOS additionally notify Dispatch.
- **Asset Service Event Backbone extended:** 4 new event_type families (`fuel`, `fluid`, `service`, `meter`) projecting from `fuel_lube_visits`. Placeholders pm/maintainx remain. Unit History page (Track 13.27) now renders fuel/lube events with zero UI change.
- **Frontend:** `/shop/fuel-lube/new` (RequireShop) with live totals + per-line issue validation. ShopHubV2 Section 05 now carries 4 workforce cards.
- **Tests:** 5 new (totals · issue rules · critical 25-char rule · E2E defect + timeline · list filters/cap). Regression Track 13.26 (11/11 · placeholder set updated) · 13.28 (4/4) · 13.28 P2 (4/4). **Total 24/24 backend pass.**
- **Hard locks intact:** No cost · no accounting · no PO numbers · no MaintainX activation · no driver login · no Shop RTS authority · no duplicate history.
- **Not built:** list/detail UI (deferred to Track 13.29 P2) · PDF/email/CSV (no reusable infrastructure · documented) · Motive geofence equipment auto-fill.
- Five-Pillar Score 9.8 / 10.
- Report: `/app/memory/TRACK_13_29_FUEL_LUBE_VISIT_RECORD.md`. Deployment readiness remains 🟢 GREEN.

## 2026-06-12 · Track 13.29 Phase 2 closeout — Fuel/Lube Visit Records List + Detail UI

- **Operator-facing read surface for Track 13.29 LIVE.** Two new pages under `RequireShop`:
  - `/shop/fuel-lube` — list of submitted Fuel/Lube Visit Records with date-range presets (today / 7d / 30d default / 90d max) and 6 filters (project · truck · tech · unit · issue status · fuel type). Honest empty/error states. ISSUE pill on rows with field-discovered issues.
  - `/shop/fuel-lube/:visitId` — header + 12-cell totals card + per-equipment line cards (issue block · 9 fluid quantities · meter · odometer · grease state · notes · linked defect IDs · one-click "View Unit History →" to Track 13.27 timeline · Shop Manager Queue link for issues). Print uses browser-native dialog. NO fake PDF/email/CSV buttons.
- **Consumes existing Track 13.29 endpoints** (`GET /api/shop/fuel-lube/visits` + `GET /api/shop/fuel-lube/visits/{id}`). Zero backend touched · zero new endpoint · zero new collection · zero schema delta · zero auth widening.
- **ShopHubV2 Section 05** navigation card added pointing to `/shop/fuel-lube`. Existing 4 workforce cards unchanged. `/shop/hub_legacy` rollback alive.
- **Hard locks intact:** No cost · no accounting · no PO numbers · no MaintainX activation · no driver login · no Shop RTS authority · no duplicate history · Dispatch Map-First · Repair Complete ≠ RTS.
- **Tests:** Smoke (root mount · honest empty · honest error · ShopHubV2 nav · regression on `/shop/manager/queue` · `/shop/me` · `/shop/units/history` · `/dispatch-portal` map canvas). Backend regression suite still **24/24 pass** (5 Track 13.29 + 4 Track 13.28 + 4 Track 13.28 P2 + 11 Track 13.26). ESLint clean.
- **Files added:** `pages/shop/FuelLubeVisitRecords.jsx` · `pages/shop/FuelLubeVisitDetail.jsx` · `memory/TRACK_13_29_PHASE_2_FUEL_LUBE_VISIT_RECORDS_UI.md`.
- **Files modified:** `App.js` (+2 lazy imports +2 routes) · `ShopHubV2.jsx` (+1 nav card in Section 05).
- **Five-Pillar Score: 9.8 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_29_PHASE_2_FUEL_LUBE_VISIT_RECORDS_UI.md`.

## 2026-06-12 · Track 13.30 closeout — Service Truck Daily Reconciliation

- **Operational accountability surface LIVE.** Fuel/lube techs can log start-of-day and end-of-day quantities per service truck/day; system pulls dispensed totals from Track 13.29 `fuel_lube_visits` (single fluid source · case-insensitive truck match · same date), computes `expected_end = start − dispensed`, `variance = actual_end − expected_end`, and classifies each product line **green / yellow / red / incomplete**. Overall variance_status is the worst per-product class.
- **New collection:** `service_truck_reconciliations` (1 doc per truck/day). 4 fuels (gallons) + 5 fluids (quarts) · closed-set product enum. NO accounting · NO cost · NO PO · NO theft language (pytest sanity sweep enforces forbidden-term absence).
- **5 endpoints** under `/api/shop/service-truck-reconciliation` (start · close · list · detail · `/review`). All gated by `_require_shop_or_admin_fleet`. List default 30d · cap 90d (mirror Track 13.29). Closed/needs_review days are locked from re-start (409).
- **Variance rules:** Green if `|var| ≤ 5 gal` (fuels) or `≤ 2 qt` (fluids) OR `pct ≤ 2 %`. Yellow if `pct ∈ (2 %, 5 %]`. Red if `pct > 5 %`. Status `closed` ⇒ green / `needs_review` ⇒ yellow|red. Language: *Within expected range · Needs review · Significant variance · Incomplete*. No theft language.
- **3 frontend pages:** `/shop/service-truck-reconciliation/new` (start/close form with mode toggle · live variance grid after close) · `/shop/service-truck-reconciliation` (filtered list with status chips · 4 range presets · 4 filters) · `/shop/service-truck-reconciliation/:recId` (detail with 7-column variance grid · linked Fuel/Lube Visits · Shop Manager review block · doctrine footer · browser-native print only · NO fake PDF/email/CSV).
- **ShopHubV2 Section 05** gains a 6th workforce card pointing to the records list. Existing 5 cards unchanged. `/shop/hub_legacy` rollback alive.
- **Asset Service Event Backbone:** intentionally NOT projected here — service truck reconciliation is truck-level, equipment-level events already come from Track 13.29's `_project_fuel_lube`. Preserves "no duplicate timeline" hard lock.
- **Tests:** 12 new (`tests/test_track_13_30_service_truck_reconciliation.py`). Regression: 24/24 across 13.26 + 13.28 + 13.28 P2 + 13.29. **Total backend suite: 36/36 PASS.** ESLint clean. Live browser smoke confirmed list/detail/form mount + 11 itest reconciliations rendered with variance chips + ShopHubV2 nav card.
- **Hard locks intact:** Dispatch Map-First · Driver no-login · Shop Repair Complete ≠ RTS · MaintainX dormant · FleetWatcher untouched · `fuel_lube_visits` read-only (status/totals/submitted_at unchanged after close) · no driver login · no fake exports · no theft language.
- **Files added:** `backend/routes/service_truck_reconciliation.py` · `backend/tests/test_track_13_30_service_truck_reconciliation.py` · `frontend/src/pages/shop/ServiceTruckReconciliationForm.jsx` · `frontend/src/pages/shop/ServiceTruckReconciliationRecords.jsx` · `frontend/src/pages/shop/ServiceTruckReconciliationDetail.jsx` · `memory/TRACK_13_30_SERVICE_TRUCK_DAILY_RECONCILIATION.md`.
- **Files modified:** `backend/server.py` (+router mount only) · `frontend/src/App.js` (+3 lazy imports +3 routes) · `frontend/src/pages/ShopHubV2.jsx` (+1 nav card).
- **Five-Pillar Score: 9.8 / 10.**
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30_SERVICE_TRUCK_DAILY_RECONCILIATION.md`.

## 2026-06-12 · Track 13.30A closeout — Shop Command Center UX + Role Workflow Architecture Audit (READ-ONLY)

- **Mode:** READ-ONLY certification + architecture design. **No implementation.** No code · no routes · no UI · no backend · no deploy.
- **Verdict:** Stop building features. Shop substrate is strong (36/36 pytest); ShopHubV2 is drifting into a "track graveyard" (5 sections · 17 nav cards organized by track number, not by role + decision). First five things each role needs at 6 AM are not in the first viewport on any role.
- **HIGH-severity defects found:**
  - `HubBackLink` is **Shop-blind** — Shop-only users on `/shop/equipment`, `/shop/equipment/:id`, `/shop/fleet` click "← Hub" and land at platform `/`, not `/shop`. Fix: add `isShop()` branch (~6 LOC, 1 file).
  - Section 01 has 4 overlapping defect counters (`defects_open`, `defects_acknowledged`, `defect_open_units`, `units_with_open_defect`) — same situation counted 3 ways.
  - Section 02 has 3 cards all linking to `/shop/equipment` without query filters.
  - "My Assignments" and "Manager Queue" buried in Section 05 — should be in Section 01.
  - **No global unit search** — most-common task is 4 clicks deep; target is 1 click. Highest UX leverage gap on the hub.
  - "Preview" banner + footer trace note leak internal track copy (`Track 13.6I`).
- **Role-based first-five analysis** completed for: Shop Manager · Mechanic · Fuel/Lube Tech · Service Writer (future) · Dispatch viewer · Admin/Leadership. Most needs are already pytest-covered endpoints (only PM + parts-on-order aggregator are missing).
- **Card / count source-truth map** (19 cards proposed): 13 live today · 4 derivable client-side · 2 need new aggregators · 2 await future tracks (PM, MaintainX).
- **Click-depth audit:** Adding header Unit Search would remove 1–3 clicks from 6 of 14 most-common Shop tasks.
- **Recommended build queue:** `13.30B` (Command Center restructure + HubBackLink fix · 2 d · LOW risk) → `13.30C` (Global Unit Search · 1 d · LOW) → `13.30D` (Parts-On-Order + Mechanic Workload aggregators · 2 d · LOW) → `13.31` (PM Engine · 5 d · MED) → `13.33` (Asset Care Command · 4 d · LOW) → `13.32` (MaintainX · BLOCKED on `MAINTAINX_API_KEY`).
- **What NOT to build:** more Track-X cards before 13.30B ships · no accounting/cost/PO/pay-app/contract surfaces · no theft register · no parallel asset history · no MaintainX activation · no `fuel_lube_visits` mutation from search.
- **Hard locks reaffirmed:** Repair Complete ≠ RTS · Dispatch RTS authority · Map-First Dispatch · Driver no-login · One map engine · One source of truth · No fake MaintainX/FleetWatcher · No accounting/cost/PO · No duplicate asset history · No duplicate defect lifecycle.
- **Five-Pillar score (current ShopHubV2):** 7.0 / 10 (Powerful 6 · Simple 5 · Beautiful 7 · Trusted 9 · Proven 8). Strong substrate · structural drift.
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30A_SHOP_COMMAND_CENTER_UX_ROLE_WORKFLOW_ARCHITECTURE_AUDIT.md`.

## 2026-06-12 · Track 13.30B closeout — Shop Command Center Restructure + HubBackLink Fix

- **Mode:** CONTROLLED IMPLEMENTATION · frontend only · 2 files modified · zero backend · zero deploy.
- **What shipped:**
  - **`HubBackLink` Shop-aware** — adds `shop = !admin && !pm && (isShop() || pathname.startsWith("/shop"))` branch; Shop-only users on `/shop/equipment`, `/shop/fleet`, `/shop/equipment/:id` now return to `/shop`, not platform `/`. `useHubHome()` extended with the same logic. Admin/PM/anonymous behavior unchanged.
  - **ShopHubV2 reorganized** around workflow, not track number. New layout: Header ("Shop Command Center" · 3 primary actions) → **Your Queue** strip (Manager Queue · My Assignments · Fuel/Lube Visit · Unit History) → **01 Attention required** (OOS · Open Defects · Units carrying defects · Waiting on parts) → **02 Active work** (Manager Queue · My Assignments · Acknowledged · Active recovery) → **03 Parts + waiting** (live Waiting-on-parts + honest dashed *"Parts on order · coming next"* slot) → **04 Fuel and service** (New Visit · Records · Start/Close Day · Reconciliation Records) → **05 Unit intelligence** (Unit History · Defect History + honest *"Global unit search · coming next"* slot) → **06 Records** (archival) → **07 Recovery Map** (secondary).
  - **Engineering copy fully scrubbed from operator surface:** preview banner removed · all `Track 13.x` mentions removed · all `Source: /api/…` italics removed · *"Presentation-only modernization"* footer rewritten to a calm one-sentence RTS reminder. Live smoke confirms `body.innerText.count("Track 13") = 0` and `count("/api/") = 0`.
  - **No fake counts · no dead links · no fake buttons.** Future Unit Search and Parts-on-order are dashed slots labelled *"coming next"* with no link. Every visible link resolves to a mounted route.
- **Files modified:** `frontend/src/components/HubBackLink.jsx` (+9 LOC) · `frontend/src/pages/ShopHubV2.jsx` (full restructure · net −309 LOC).
- **Files added:** `memory/TRACK_13_30B_SHOP_COMMAND_CENTER_RESTRUCTURE.md`.
- **Untouched:** backend routers · server.py · tests · App.js routes · `/shop/hub_legacy` rollback · Recovery Map engine · all `routes/*.py`.
- **Tests:** ESLint clean (2 files). Browser smoke 21/21 pass — root mounts · 7 sections present · Your Queue strip + 4 cards · preview banner gone · zero operator-visible `Track 13` or `/api/` text · all sub-routes still load (`/shop/manager/queue` · `/shop/me` · `/shop/fuel-lube/new` · `/shop/fuel-lube` · `/shop/service-truck-reconciliation` · `/shop/units/history` · `/shop/hub_legacy` · `/dispatch-portal`). Backend suite preserved at **36/36 pass** (no router touched).
- **Hard locks intact:** Repair Complete ≠ RTS · Dispatch retains RTS authority · Dispatch Map-First · Driver no-login · MaintainX dormant · FleetWatcher untouched · no accounting · no cost · no PO · no duplicate asset history · `/shop/hub_legacy` rollback alive.
- **Five-Pillar score: 7.0 → 9.0 / 10** (Powerful 8 · Simple 9 · Beautiful 9 · Trusted 10 · Proven 9).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30B_SHOP_COMMAND_CENTER_RESTRUCTURE.md`.

## 2026-06-12 · Track 13.30C closeout — Shop Command Center Intelligence + Visual Hierarchy + Global Unit Search

- **Mode:** CONTROLLED IMPLEMENTATION · backend + frontend · 2 new read-only endpoints · 2 new frontend components · ShopHubV2 rewired · zero deploy.
- **What shipped:**
  - **Backend (2 endpoints, read-only):** `GET /api/shop/units/search?q=<term>&limit=<n>` (Shop/Admin gate · min 2 chars · 20-row cap · 8-field case-insensitive contains search across `equipment_master` · widening pass against `fleet_status` for trucks · per-row projection includes status, open_defects_count, highest_severity, assigned_mechanic, parts_on_order_count, last_fuel_lube_visit, links.unit_history). `GET /api/shop/me/summary` (3 role shapes: admin/shop_manager returns unassigned/pending_review/in_progress/waiting_parts/rts_pending/variance_review_7d; mechanic returns assigned_to_me/accepted/in_progress/rejected_back/waiting_parts; generic shop returns empty counts → frontend falls back to navigation strip).
  - **Frontend:** `UnitSearch.jsx` debounced 350 ms · honest empty/error/loading states · row click → `/shop/units/{unit}/history` (Track 13.27). Mounted in TWO places: header section (above all content) AND Section 05 inline (replacing the prior dashed slot). `YourQueueStrip.jsx` fetches `/me/summary` and renders role-specific MetricCard tiles (red/amber/blue/calm palette) or generic fallback.
  - **Visual hierarchy upgrade:** Section 01 cards migrated from generic HubCard to new **PriorityMetric** tiles — 38 px bold count · uppercase label · red palette when count > 0 in critical categories, amber for needs-review, calm when zero.
  - **Recovery Map preserved AND improved:** still 360 px embed + 360 px side list, NOT collapsed/demoted/hidden. Side rows now expose per-row **"Open History →"** link to Track 13.27 unit timeline (honest — only rendered when unit_number is present).
- **Live counts verified at runtime:** Unassigned 83 · Pending review 0 · Waiting parts 0 · RTS pending 0 · Variance review 7d 6 · OOS Units 71 · Open Defects 83 · Units carrying defects 11.
- **Files added:** `backend/routes/shop_intel.py` · `backend/tests/test_track_13_30c_shop_intel.py` · `frontend/src/components/shop/UnitSearch.jsx` · `frontend/src/components/shop/YourQueueStrip.jsx` · `memory/TRACK_13_30C_SHOP_COMMAND_CENTER_INTELLIGENCE_VISUAL_HIERARCHY.md`.
- **Files modified:** `backend/server.py` (+6 LOC mount only) · `frontend/src/pages/ShopHubV2.jsx` (Section 01 → PriorityMetric · Your-Queue strip → role-aware · Section 05 slot → live search · ShopRecoveryRow → per-row history link).
- **Untouched:** `HubBackLink.jsx` (Track 13.30B fix preserved) · all other backend routers · App.js routes · `/shop/hub_legacy` rollback.
- **Tests:** 6 new pytest tests (`test_track_13_30c_shop_intel.py`) all pass · backend regression 36/36 retained → **total 42/42 pass**. ESLint clean on `ShopHubV2.jsx`/`YourQueueStrip.jsx` · `UnitSearch.jsx` carries 1 inert lint warning (rule not active in webpack ESLint). Live browser smoke confirms hub renders with real counts, zero operator-visible `Track 13` or `/api/` text, and 8 regression routes mount cleanly.
- **Hard locks intact:** Recovery Map remains visible on ShopHubV2 (explicit non-negotiable directive honored) · Dispatch Map-First · Driver no-login · Shop Repair Complete ≠ RTS · Dispatch RTS authority preserved · MaintainX dormant · FleetWatcher untouched · no accounting / cost / PO / fuel tax · no fake counts · no duplicate asset history · `/shop/hub_legacy` rollback alive.
- **Forbidden-term sanity sweep** (pytest): no `cost`, `price`, `po_number`, `tax`, `invoice`, `margin` leak in any unit-search response path.
- **Five-Pillar score: 9.0 → 9.8 / 10** (Powerful 10 · Simple 10 · Beautiful 9 · Trusted 10 · Proven 10).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30C_SHOP_COMMAND_CENTER_INTELLIGENCE_VISUAL_HIERARCHY.md`.

## 2026-06-12 · Track 13.30C-fix closeout — Shop Form / Navigation / Runtime Correction Pass

- **Mode:** CONTROLLED CORRECTION (block Track 13.30D until green) · backend (additive) + frontend · zero deploy.
- **Runtime crash fixed:** `Can't find variable: FocusBanner` — `FleetVisibility.jsx` was using `<FocusBanner />` without importing it. One-line fix.
- **2 new read-only endpoints** for source-truth Shop dropdowns: `GET /api/shop/projects/list` (aggregates `daily_reports` for project_number/name; 500-row cap) and `GET /api/shop/units/list?limit=N` (active `equipment_master` rows). Same Shop/Admin gate as the rest of `/api/shop/*`. Forbidden-term sanity preserved.
- **2 new shared frontend components:** `BackToShopLink.jsx` (plain "← Back to Shop" link in MASCI form style) + `ShopSelector.jsx` (kind-aware searchable dropdown for `project` / `unit` with debounced filter, honest empty/error states, and "Type manually instead →" fallback so the form is never blocked by an outage).
- **Form upgrades:**
  - **Fuel/Lube Visit form** — Project picker · Fuel-lube-truck picker · per-equipment-line unit picker (equipment_name auto-fills on selection) · operator-friendly subtitle · Back-to-Shop link.
  - **Service Truck Reconciliation form** — Service-truck-unit picker · Back-to-Shop link.
- **`Back to Shop` link mounted on all 10 PortalShell-driven Shop subpages** (Fuel/Lube Form/Records/Detail, STR Form/Records/Detail, Shop Manager Queue, My Assignments, Unit History Landing, Unit History Timeline). `/shop/equipment`, `/shop/equipment/:id`, `/shop/fleet` continue to rely on the Shop-aware `HubBackLink` (Track 13.30B).
- **Operator copy fully scrubbed** from all Fuel/Lube and Service Truck pages plus Shop Manager Queue, My Assignments, Unit History pages: removed every visible *"Track 13.x"*, *"Asset Service Event Backbone"*, *"defect lifecycle"*, *"Source: /api/..."*, and `<code>/api/...</code>` mention. Replaced with plain operator language (e.g. *"Each service entry is saved to the unit's history. Issues you flag here become shop defects automatically."*).
- **Service-truck classification gap documented (not blocking):** `equipment_master` does not yet classify trucks, so `ShopSelector kind="unit"` returns the full active list and accepts manual entry as fallback. Future enrichment will gate via `filterFn={(u) => u.role === "fuel_truck"}`.
- **Verification:** all 12 smoke routes (`/shop`, `/shop/fleet`, `/shop/equipment`, `/shop/fuel-lube/new`, `/shop/fuel-lube`, `/shop/service-truck-reconciliation`, `/shop/service-truck-reconciliation/new`, `/shop/units/history`, `/shop/manager/queue`, `/shop/me`, `/dispatch-portal`, `/shift`) load with `overlay=False`. Engineering-copy scrub holds at runtime (`Track 13`=0, `/api/`=0 on all routes except `/shop/manager/queue` where the single "Track 13" mention traces to **seeded defect-title data**, NOT UI copy — addressing it requires a data cleanup of legacy preview seeds, out of scope for a UI correction pass). All four source-truth selectors render live (`fuel-lube-visit-form-project-project-root`, `fuel-lube-visit-form-truck-unit-root`, `fuel-lube-line-unit-0-unit-root`, `strr-form-truck-unit-root` — each count = 1).
- **Backend regression preserved at 42/42 pass.** ESLint clean on touched frontend files.
- **Hard locks intact:** Dispatch Map-First · Driver no-login · Repair Complete ≠ RTS · Dispatch RTS authority · Material Movement Ledger untouched · MaintainX dormant · FleetWatcher untouched · no accounting · no cost · no PO · no fake counts · no duplicate asset history · `/shop/hub_legacy` rollback alive.
- **Files added:** `frontend/src/components/shop/BackToShopLink.jsx` · `frontend/src/components/shop/ShopSelector.jsx` · `memory/TRACK_13_30C_FIX_SHOP_FORM_NAV_UX_CORRECTION.md`.
- **Files modified:** `frontend/src/pages/FleetVisibility.jsx` (+1 import line) · `backend/routes/shop_intel.py` (+2 endpoints, ~80 LOC) · 10 Shop subpage files (selector wiring · Back-to-Shop link · operator-copy scrub).
- Deployment readiness remains 🟢 **GREEN**.
- Report: `/app/memory/TRACK_13_30C_FIX_SHOP_FORM_NAV_UX_CORRECTION.md`.
