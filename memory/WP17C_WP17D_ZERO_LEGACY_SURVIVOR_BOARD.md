# WP17C + WP17D Zero-Legacy Survivor Board

Last updated: 2026-08-01

## Executive Rule
A survivor is open until it is either:
- removed,
- migrated to the canonical implementation and visually verified, or
- retained as a documented approved exception.

## Full-Ledger Survivor Counts
- Route/Shell: **107**
- Navigation: **62**
- Tables: **104**
- Dialogs/Overlays: **89**
- Forms: **38**
- Coaching: **11**

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

## Active-Route Survivor Queue
### Header survivors (19)
- `/safety/forms/equipment-issuance/:id` · `ViewSafetyForm` · replace legacy/local header with canonical shell
- `/safety/forms/equipment-training/:id` · `ViewSafetyForm` · replace legacy/local header with canonical shell

### Form survivors (2)
- `/revise/:token` · `Revise` · move to canonical FormShell or canonical public auth shell
- `/sign-in` · `SignIn` · move to canonical FormShell or canonical public auth shell

### Table survivors (10)
- `/safety/forms/equipment-issuance/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/safety/forms/equipment-training/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/leadership/records/:id` · `FieldLeadershipView` · move to canonical data table shell
- `/safety/cases/:caseId/reports/:reportType` · `IncidentReportViewer` · move to canonical data table shell
- `/safety/cases/:caseId/executive-report` · `ExecutiveCaseReport` · move to canonical data table shell
- `/admin/pnl` · `ProjectPnlPage` · move to canonical data table shell
- `/admin/leadership/records/:id` · `FieldLeadershipView` · move to canonical data table shell
- `/admin/safety/issuance/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/admin/safety/training/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/dev` · `DevHub` · move to canonical data table shell

### Coaching survivors (20)
- `/safety/forms/equipment-issuance/new` · `NewSafetyEquipmentIssuance` · collapse stacked helper text into canonical coaching treatment
- `/safety/forms/equipment-training/new` · `NewSafetyEquipmentTraining` · collapse stacked helper text into canonical coaching treatment
- `/field/calculators` · `MaterialCalculators` · collapse stacked helper text into canonical coaching treatment
- `/qaqc/:slug/new` · `NewQaqcInspection` · collapse stacked helper text into canonical coaching treatment
- `/leadership/records` · `FieldLeadershipRecords` · collapse stacked helper text into canonical coaching treatment
- `/leadership/:kind/new` · `FieldLeadershipFormPage` · collapse stacked helper text into canonical coaching treatment
- `/safety/inspections/new` · `NewInspection` · collapse stacked helper text into canonical coaching treatment
- `/jha` · `JhaPlansHub` · collapse stacked helper text into canonical coaching treatment
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
