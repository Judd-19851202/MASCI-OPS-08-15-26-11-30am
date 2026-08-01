# WP17C + WP17D Zero-Legacy Survivor Board

Last updated: 2026-08-01

## Executive Rule
A survivor is open until it is either:
- removed,
- migrated to the canonical implementation and visually verified, or
- retained as a documented approved exception.

## Executive Amendment #2 Override · 2026-08-01
- All prior route certifications are **provisional** wherever they conflict with the new operator-first header constitution.
- Shared header architecture is now the first-class P0 system: two-tier canonical header, utility controls moved below the sticky shell, duplicate identity removed, and long workflow names protected at `390px`.
- Internal engineering language is now prohibited in the product UI. The admin governance tool was renamed to **Operations Readiness Center** at `/admin/platform-readiness`; old internal route aliases may remain for continuity but must never leak engineering wording in the rendered product.
- Header-related survivor counts are now in **active recount**. Treat the denominators below as the last audited baseline, and reopen every previously closed header route until it is re-certified under this amendment.

## Full-Ledger Survivor Counts
- Route/Shell: **99**
- Navigation: **59**
- Tables: **99**
- Dialogs/Overlays: **89**
- Forms: **38**
- Coaching: **10**

## Batch Certification Ledger
### 2026-08-01 · Shared Shell Identity Propagation + Field Calculators Wave · CLOSED / ACTIVE NEXT
- Closed shared architecture correction: platform-wide header identity now propagates through `CanonicalHeader.jsx`, `PortalShell.jsx`, `FormShell.jsx`, `PortalLoginShell.jsx`, `PublicShell.jsx`, and `OperationalPageFrame.jsx`
- Closed route in active Field wave: `/field/calculators`
- Shared fixes:
  - portal/workflow names no longer replace MASCI product identity in applicable shared shells
  - `/field/calculators` now shows MASCI / Operations Platform + a single `Material Calculators` context label
  - duplicate calculators shell subtitle strip removed
  - calculators summary/tabs/panels moved onto governed shared surfaces
- Evidence: responsive screenshot review for `/`, `/field`, and `/field/calculators`; `/app/test_reports/iteration_102.json`; final `auto_frontend_testing_agent` verification on all three routes
- Certification result: shared brand identity consistent across Home, Field, and calculators; no portal-specific replacement identity; zero console errors; zero horizontal overflow at `390`, `430`, `768`, `1024`, `1440`
- Carry-forward note: Field Operations wave remains ACTIVE with field daily-report list/detail surfaces and equipment interiors next before Transportation begins

### 2026-08-01 · Executive Brand-Hierarchy Correction + Field Operations Wave 01 · CLOSED / ACTIVE NEXT
- Closed correction: `/` Home header identity hierarchy
- Closed route in propagation order: `/field`
- Shared fixes:
  - `CanonicalHeader.jsx` now renders the Home brand hierarchy as **MASCI** over **Operations Platform**
  - Home hero no longer repeats the product identity above `One System. Every Crew. Every Job.`
  - `wp17d_constitution_guard.py` now enforces duplicate-identity, brand-block, hierarchy-style, and logo-home-behavior checks
  - `FieldSection.jsx` now uses governed `InformationCard`, `ModuleCard`, `WorkflowCard`, and shared `SectionHeading` instead of route-local tile styling
  - duplicate shell summary block removed from `/field`
- Evidence: responsive screenshot review on `/` at `390`, `430`, `768`, `1024`, `1440`; responsive smoke review on `/field`; `/app/test_reports/iteration_101.json`; final `auto_frontend_testing_agent` verification on `/` + `/field`
- Certification result: Home hierarchy corrected, logo returns Home, one visible sign-in entry, Field entry route moved onto shared cards with zero overflow / console noise
- Carry-forward note: Field Operations propagation remains ACTIVE with `/field/calculators` and remaining field-family surfaces next before Transportation begins

### 2026-08-01 · Executive Constitution Hardening · Home Correction + Anti-Drift Start · CLOSED
- Closed route: `/` as **Operations Platform Home** (internal filename may still remain `Hub.jsx` for continuity only)
- Constitutional fixes shipped:
  - Home header now owns the single primary sign-in / resume control through `CanonicalHeader.headerControlsSlot`
  - shared `LangToggle.jsx` now uses the governed premium header treatment required at `390px`
  - explanatory navy panel removed from Home
  - hero now uses governed CTA buttons instead of decorative chips
  - Home operations cards no longer repeat `Sign in` as footer copy
  - shared card governance hardened into named families (`ModuleCard`, `WorkflowCard`, `ActionCard`, `InformationCard`, `ExternalPlatformCard`, `DetailCard`, `FormSectionCard`, `AlertCard`)
- New anti-drift guard activated: `/app/scripts/wp17d_constitution_guard.py`
- Evidence: responsive screenshot review at `390`, `430`, `768`, `1024`, and `1440`; `/app/test_reports/iteration_100.json`; local constitutional guard pass
- Certification result: Home now preserves MASCI navy/frosted identity, presents one clear sign-in entry point, keeps the EN/ES control visibly interactive at `390px`, and stays runtime/overflow clean
- Carry-forward note: the next locked wave is **Field Operations** propagation under the same constitution and guarded shared-component system

### 2026-08-01 · Governed Design Primitives + Hub Canonical Implementation · CLOSED
- Shared primitives completed: canonical `CanonicalCard.jsx`, `SectionHeading.jsx`, governed CTA/button treatment in `components/ui/button.jsx`, governed badges/chips in `OperationalStatusBadge.jsx`, and governed empty/loading/error/success/warning states in `components/ui/PortalStates.jsx` + `components/EmptyState.jsx`
- Shared support fix: `CanonicalHeader.jsx` home-mode fallback now renders **Operations Platform** for Shared Operational Home instead of the generic **Operational workflow** label
- Closed route: `/` (`Hub`) rebuilt from shared primitives only; local BigTile / PortalPill / reference-card drift was removed so all Hub cards now inherit one governed card system
- Evidence: responsive screenshot certification at `390`, `430`, `768`, `1024`, and `1440`; `/app/test_reports/iteration_99.json`; final `auto_frontend_testing_agent` pass (**19/19 PASS**)
- Certification result: zero horizontal overflow, unified 15-card Hub surface, working Company Info dialog trigger, zero console errors
- Denominator movement: shared primitive foundation closed; full-ledger survivor counts held pending the next platform-wide card/icon recount during propagation
- Carry-forward note: Hub is now the first complete implementation of the design system; next work is platform propagation in the locked order `Field Operations → Transportation → Safety → QA/QC → Shop → Project Management → Human Resources → Administration`

### 2026-08-01 · Shared Tables Batch 01 · CLOSED
- Closed routes: `/admin/scheduler-runs`, `/admin/leadership-equipment`, `/admin/terminations`, `/admin/guide`, `/admin/executive-operational-intelligence`, `/pm/operational-intelligence`
- Shared fixes: canonical `DataTable` upgrade, `wp17.css` table shell styling, scheduler legacy-banner removal, `LastActivityLine` portal guard
- Evidence: `/app/test_reports/iteration_95.json` plus responsive screenshot sets at `390`, `768`, `1024`, and `1440`
- Denominator movement: full-ledger table survivors `113 → 107`; active-route table queue `19 → 13`
- Carry-forward note: dual-nav coexistence on some wider shells remains a Navigation-batch cleanup item; it did not block table certification

### 2026-08-01 · Platform Shell Sub-Batch 01 · CLOSED
- Closed routes: `/admin/daily/:id`, `/pm/daily/:id`, `/admin/inspections/:id`, `/admin/meetings/:id`, `/admin/incidents/:id`
- Shared fixes: `DetailPageHero` rollout, stacked `PageHeader` mode, `AdminRouteShell` duplicate-header suppression, and incident CAPA fetch gating outside Safety Portal
- Evidence: `/app/test_reports/iteration_96.json` plus responsive screenshot sets at `390`, `768`, `1024`, and `1440`
- Denominator movement: full-ledger route/shell survivors `134 → 129`; full-ledger navigation survivors `68 → 66`; active header queue `41 → 36`; active navigation queue `6 → 4`
- Carry-forward note: PM incident/meeting/inspection, Safety Portal incident/meeting/inspection, and HR daily-report variants share the new header architecture but still require portal-specific visual certification before closure

### 2026-08-01 · Public & Off-Shell Convergence Batch · CLOSED
- Closed routes: `/safety/cards`, `/qaqc/:id`, `/admin/qaqc/:id`, `/trench-safety`, `/trench-safety/tabulated-data`, `/trench-safety/references`, `/trench-safety/report`, `/trench-safety/assets/:assetId`, `/trench-safety/excavation/new`, `/transport-invite/:token`, `/transport-verify/:cnum`
- Shared fixes: new `OperationalPageFrame` + `OperationalStatusBadge`, `PublicTrenchHeader` rebuilt onto the shared `OperationalTopbar`, trench-public shell cleanup, transportation invite/verify shell convergence, `FieldSafetyCards` full-page repair, `PublicReportModal`/`PublicAssetLookup` polish, and QAQC detail migration onto `DetailPageHero`
- Evidence: `/app/test_reports/iteration_97.json` plus responsive screenshot sets at `390`, `768`, `1024`, and `1440`
- Denominator movement: full-ledger route/shell survivors `129 → 118`; full-ledger navigation survivors `66 → 63`; active header queue `36 → 26`; active navigation queue `4 → 1`
- Carry-forward note: `/qaqc/:id` remains auth-gated by design, and `/api/trench-safety/excavations/public/asset-roster` still returns `401` on the public excavation route while the form itself remains usable; policy-level backend follow-up can be handled in a later batch if that endpoint is intended to stay public

### 2026-08-01 · Highest-Visibility Platform Experience Batch · CLOSED
- Closed routes: `/`, `/guidance`, `/guidance/section/:sectionId`, `/guidance/:articleId`, `/near-miss`, `/thank-you`, `/cheatsheet`, `/admin/trench-boxes/poster`, `/admin/jha-plans/poster`, `/admin/posters/print-all`, `/hr/daily-reports/:id`
- Shared fixes: new `OperationalPrintPageFrame` + `OperationalOutcomeFrame`, Hub and Guidance shell convergence onto the shared operational topbar, NearMiss/ThankYou public outcome cleanup, print-route header unification, and `ViewDailyReport` migration onto canonical `DataTable`
- Evidence: responsive screenshot sets at `390`, `768`, `1024`, and `1440`, `auto_frontend_testing_agent` pass, and `/app/test_reports/iteration_98.json`
- Denominator movement: full-ledger route/shell survivors `118 → 107`; full-ledger navigation survivors `63 → 62`; full-ledger table survivors `107 → 104`; full-ledger form survivors `39 → 38`; active header queue `26 → 19`; active navigation queue `1 → 0`; active-route table queue `13 → 10`
- Carry-forward note: icon convergence continues during each remaining route migration; poster/Hub overlay survivors remain open until their internal drawers/sheets are fully reconciled

### 2026-08-01 · Canonical Header Constitution Correction · IN FORCE
- Shared system fix: `CanonicalHeader.jsx` now defines the permanent MASCI navy/frosted header standard and is wired through `OperationalPageFrame`, `PortalShell`, `FormShell`, `PortalLoginShell`, `PublicShell`, `SignIn`, `Revise`, and `FormPasswordGate`
- Executive rules enforced in code: one header height, one logo size/location, one language selector treatment, one Home/Back treatment, logo always returns to Shared Operational Home, and portal colors act only as accents instead of recoloring the shell
- Evidence: targeted responsive smoke screenshots for `/`, `/sign-in`, and `/guidance`, plus `auto_frontend_testing_agent` verification across `/`, `/guidance`, `/sign-in`, `/revise/example-invalid-token`, and `/admin`
- Survivor impact: counts unchanged for this constitution pass; remaining direct-header routes must be reopened and routed into `CanonicalHeader` during their next migration pass

### 2026-08-01 · Shared Operational Home Header Reopened + RECERTIFIED
- Route reopened: `/` (`Hub`) after executive rejection of the first home-header composition despite passing navy-header regression checks
- Root cause corrected: `CanonicalHeader` now supports a governed `home` variant, the Home header is logo-first with no competing platform-name copy, sign-in/resume remains the only auth control, the language selector was compacted, and repeated Home messaging was removed from the header/hero relationship
- Evidence: direct screenshot review at `390`, `430`, `768`, `1024`, and `1440`, authenticated smoke at `390` and `1440`, Spanish toggle verification at `390`, manual logo-to-home behavior check, and focused `auto_frontend_testing_agent` pass for the Home header restoration
- Certification note: Home route visual certification is restored and propagation may continue; counts unchanged because this was a reopened correction inside an already-counted route

### 2026-08-01 · Safety Records + JHA Convergence Batch · CLOSED
- Closed routes: `/safety/forms/equipment-issuance/:id`, `/safety/forms/equipment-training/:id`, `/jha`
- Shared fixes: `ViewSafetyForm.jsx` rebuilt onto `PortalShell`/`AdminRouteShell` + `DetailPageHero` + canonical `DataTable`, `PortalShell` gained a governed `showPageHeader` switch to prevent duplicate title stacks, and `JhaPlansHub.jsx` reduced coaching drift and mobile overflow while keeping the MASCI navy/glass shell intact
- Evidence: live smoke screenshots on JHA and safety record fixtures, focused `auto_frontend_testing_agent` pass on JHA and both safety detail routes, plus JHA mobile re-verification at `390` and `430`
- Denominator movement: full-ledger route/shell survivors `107 → 104`; full-ledger table survivors `104 → 102`; full-ledger coaching survivors `11 → 10`; active header queue `19 → 17`; active-route table queue `10 → 8`; active coaching queue `20 → 19`
- Carry-forward note: `/dev` now shares the converged shell and DataTable architecture, but the authenticated DevHub surface still awaits full visual certification because only the gated login state was available during this batch

### 2026-08-01 · Admin Safety Aliases + Admin Libraries Batch · CLOSED
- Closed routes: `/admin/safety/issuance/:id`, `/admin/safety/training/:id`, `/admin/jha-plans`, `/admin/trench-boxes`
- Shared fixes: admin safety detail aliases were visually certified on the governed `AdminRouteShell` + `DetailPageHero` architecture; `JhaPlansAdmin.jsx` was migrated off `LegacyAdminModernShell`, duplicate title stacks were removed, and the admin JHA refetch loop was fixed by memoizing admin auth headers; `TrenchBoxesAdmin.jsx` was moved onto `AdminRouteShell` + `DetailPageHero` and its Add Box dialog was rebuilt onto the governed navy/glass modal treatment with canonical icon usage.
- Evidence: responsive screenshot certification captured at `390`, `430`, `768`, `1024`, and `1440` for all four routes plus focused `auto_frontend_testing_agent` pass (**4/4 PASS**) covering safety aliases, admin JHA, trench dialog behavior, and DevHub blocker handling.
- Denominator movement: full-ledger route/shell survivors `104 → 102`; full-ledger table survivors `102 → 100`; active header queue `17 → 15`; active-route table queue `8 → 5`
- Carry-forward note: remaining trench/detail aliases, direct-header survivors, and shared overlay/card/coaching convergence remain in active WP-17D scope and should continue from this certified baseline

### 2026-08-01 · DevHub Authenticated Visual Certification · BLOCKED_CREDENTIALS
- Blocked routes: `/dev/login`, `/dev`
- Exact evidence captured by main agent: `GET /api/dev/check` returned `404 Not Found`; `POST /api/dev/login` returned `404 Not Found` in Preview on `https://backup-forensics.preview.emergentagent.com`
- Backend code evidence: `/app/backend/server.py` lines `2237-2251` fail closed when developer endpoints are disabled or `DEV_PASSWORD` is missing; the route explicitly raises `404` when `_dev_endpoints_enabled()` is false or `DEV_PASSWORD` is empty
- Why certification cannot continue: authenticated entry into `/dev` is impossible in this environment, so the actual DevHub surface cannot be opened, visually reviewed, or certified. Only the disabled login shell can be seen.
- Required environment to unblock: backend Preview environment must define `DEV_PASSWORD` and enable the dev endpoints gate consumed by `_dev_endpoints_enabled()`; only after that can authenticated `/dev` certification proceed.

### 2026-08-01 · Trench Shell Convergence + Executive Dashboard Batch · CLOSED
- Closed routes: `/admin/trench-safety/reports`, `/safety/trench-safety/reports`, `/admin/trench-safety/assets/:assetId`
- New executive tool: `/admin/wp17d-certification`
- Shared fixes: `SafetyShell.jsx` and `PmShell.jsx` now support governed suppression of duplicate page headers and mission banners; `TrenchSafetyShell.jsx` now renders a canonical MASCI trench navigation surface that preserves portal boundaries; `TrenchSafetyAssetsList.jsx` and `TrenchSafetyHub.jsx` now keep trench links inside the correct admin/safety/PM portal; `TrenchSafetyAssetDetail.jsx` now uses `DetailPageHero`, the governed admin route architecture, and canonical `DataTable` treatment for deployment history; the executive dashboard now exposes survivor counts, certification status, blocker state, completion %, and GO / NO-GO readiness.
- Evidence: responsive screenshot certification captured at `390`, `430`, `768`, `1024`, and `1440` for `/admin/trench-safety/reports`, `/safety/trench-safety/reports`, `/admin/trench-safety/assets/:assetId`, and `/admin/wp17d-certification`; focused `auto_frontend_testing_agent` pass returned **7/7 PASS** with zero defects, zero critical console errors, and no portal-hop regressions.
- Denominator movement: full-ledger route/shell survivors `102 → 99`; full-ledger navigation survivors `62 → 59`; full-ledger table survivors `100 → 99`; active header queue `15 → 12`
- Carry-forward note: the trench shared shell is now governed, but remaining trench detail aliases, trench dialogs/overlays, and non-trench direct-header survivors still require route-by-route certification and convergence.

### 2026-08-01 · Shared Header Constitution + Product Language Cleanup · CLOSED
- Shared fixes: `CanonicalHeader.jsx` now enforces the two-tier operator-first header (global controls only on row one, workflow identity only on row two); `PortalShell.jsx` now moves search / switcher / profile utilities into a separate utility rail below the sticky header; `AdminRouteShell.jsx`, `SafetyShell.jsx`, `PmShell.jsx`, `PublicShell.jsx`, and `PortalLoginShell.jsx` now inherit the governed header behavior automatically; `DetailPageHero.jsx` now hands workflow identity to the shell header so detail pages no longer need duplicate large titles below the header.
- Product-language cleanup: the admin governance surface now renders as **Operations Readiness Center** at `/admin/platform-readiness`, with all leaked engineering labels removed from visible UI; the legacy `/admin/wp17d-certification` alias may remain for continuity but must render the same product-safe surface.
- Evidence: responsive header review captured at `390px` on `/admin/login`, `/admin/platform-readiness`, and `/admin/trench-safety/assets/:assetId`; banned-term scan returned zero UI hits; focused `auto_frontend_testing_agent` pass returned **4/4 PASS** for shared header architecture, product-language cleanup, detail-header integration, and legacy alias hygiene.
- Denominator movement: **none yet** — Amendment #2 forces a route-by-route header recount before new header-closure numbers can be trusted.
- Carry-forward note: all previously closed header routes remain provisional until reopened and re-certified under the amendment-driven route audit.

### 2026-08-01 · Shared Field Form Workflow Convergence · CLOSED
- Reopened and re-cleared workflows: `/fleet/dvir/new`, `/equipment/submit`, `/daily/submit`, `/meetings/submit`
- Shared fixes: `FormShell.jsx` now uses the governed utility card below the sticky header, strips duplicated MASCI wording from row-two identity, and suppresses redundant home-only back behavior; `FormSection.jsx`, `ProgressRail.jsx`, and `SubmitReviewPanel.jsx` now share normalized spacing, hierarchy, and action emphasis; `JobPicker.jsx` now uses operator-safe job wording; Daily Report now has a governed sticky submit footer with the inline duplicate submit CTA removed.
- Evidence: responsive screenshots captured at `390`, `430`, `768`, `1024`, and `1440` for DVIR, Equipment Pre-Op, Daily Report, and Meeting workflows; focused `auto_frontend_testing_agent` pass returned **4/4 PASS** with zero horizontal overflow, zero console/runtime defects, and verified sticky-footer behavior on Daily Report.
- Denominator movement: keep the full-ledger counts above as the working baseline while the Amendment #2 / #3 route recount continues; these four workflows are now re-cleared under the updated operator-first standard.
- Carry-forward note: Daily field forms now share the governed shell foundation, but QA/QC, material calculators, inspections, incident flows, and the remaining daily-use workflows still need their route-by-route reopen pass.

## Active-Route Survivor Queue
### Header survivors (active recount · provisional baseline 17)

### Form survivors (2)
- `/revise/:token` · `Revise` · move to canonical FormShell or canonical public auth shell
- `/sign-in` · `SignIn` · move to canonical FormShell or canonical public auth shell

### Card/system propagation survivors (active rollout begins with Field Operations)
- `/field` family · continue after `/field` and `/field/calculators` closeout by migrating field-family list/detail surfaces, equipment interiors, and remaining helper/icon drift onto governed shared systems
- `/transportation` family · replace remaining local command/launcher cards with governed shared variants and external-platform rules
- `/safety` family · continue converging mixed safety cards, state treatments, and legacy icon contexts

### Table survivors (5)
- `/leadership/records/:id` · `FieldLeadershipView` · move to canonical data table shell
- `/safety/cases/:caseId/reports/:reportType` · `IncidentReportViewer` · move to canonical data table shell
- `/safety/cases/:caseId/executive-report` · `ExecutiveCaseReport` · move to canonical data table shell
- `/admin/pnl` · `ProjectPnlPage` · move to canonical data table shell
- `/admin/leadership/records/:id` · `FieldLeadershipView` · move to canonical data table shell

### Blocked authenticated certification (1)
- `/dev` · `DevHub` · `BLOCKED_CREDENTIALS` until backend Preview has `DEV_PASSWORD` plus the dev endpoint gate enabled; evidence logged above (`/api/dev/check` 404, `/api/dev/login` 404)

### Coaching survivors (19)
- `/safety/forms/equipment-issuance/new` · `NewSafetyEquipmentIssuance` · collapse stacked helper text into canonical coaching treatment
- `/safety/forms/equipment-training/new` · `NewSafetyEquipmentTraining` · collapse stacked helper text into canonical coaching treatment
- `/field/calculators` · `MaterialCalculators` · collapse stacked helper text into canonical coaching treatment
- `/qaqc/:slug/new` · `NewQaqcInspection` · collapse stacked helper text into canonical coaching treatment
- `/leadership/records` · `FieldLeadershipRecords` · collapse stacked helper text into canonical coaching treatment
- `/leadership/:kind/new` · `FieldLeadershipFormPage` · collapse stacked helper text into canonical coaching treatment
- `/safety/inspections/new` · `NewInspection` · collapse stacked helper text into canonical coaching treatment
- `/fleet/dvir/submitted/:id` · `FleetDVIRConfirmation` · collapse stacked helper text into canonical coaching treatment
- `/daily-reports` · `DailyReportsDashboard` · collapse stacked helper text into canonical coaching treatment
- `/admin/daily` · `DailyReportsDashboard` · collapse stacked helper text into canonical coaching treatment
- `/admin/leadership/records` · `FieldLeadershipRecords` · collapse stacked helper text into canonical coaching treatment
- `/pm/daily` · `DailyReportsDashboard` · collapse stacked helper text into canonical coaching treatment
- `/shop/fleet` · `FleetVisibility` · collapse stacked helper text into canonical coaching treatment
- `/field-leadership/portal/change-password` · `FieldLeadershipPortalChangePassword` · collapse stacked helper text into canonical coaching treatment
- `/field-leadership/portal/dashboard` · `FieldLeadershipPortalDashboard` · collapse stacked helper text into canonical coaching treatment
- `/field-leadership/portal` · `FieldLeadershipPortalDashboard` · collapse stacked helper text into canonical coaching treatment
- `/safety-portal/fleet` · `FleetVisibility` · collapse stacked helper text into canonical coaching treatment
- `/dispatch-portal/fleet` · `FleetVisibility` · collapse stacked helper text into canonical coaching treatment
- `/admin/deploy-readiness` · `AdminDeployReadiness` · collapse stacked helper text into canonical coaching treatment

### Navigation survivors (0)
