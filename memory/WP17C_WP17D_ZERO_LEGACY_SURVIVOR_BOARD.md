# WP17C + WP17D Zero-Legacy Survivor Board

Last updated: 2026-08-01

## Executive Rule
A survivor is open until it is either:
- removed,
- migrated to the canonical implementation and visually verified, or
- retained as a documented approved exception.

## Full-Ledger Survivor Counts
- Route/Shell: **102**
- Navigation: **62**
- Tables: **100**
- Dialogs/Overlays: **89**
- Forms: **38**
- Coaching: **10**

## Batch Certification Ledger
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

## Active-Route Survivor Queue
### Header survivors (17)

### Form survivors (2)
- `/revise/:token` · `Revise` · move to canonical FormShell or canonical public auth shell
- `/sign-in` · `SignIn` · move to canonical FormShell or canonical public auth shell

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
