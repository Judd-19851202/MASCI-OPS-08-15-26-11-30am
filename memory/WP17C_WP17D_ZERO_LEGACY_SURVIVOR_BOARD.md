# WP17C + WP17D Zero-Legacy Survivor Board

Last updated: 2026-08-01

## Executive Rule
A survivor is open until it is either:
- removed,
- migrated to the canonical implementation and visually verified, or
- retained as a documented approved exception.

## Full-Ledger Survivor Counts
- Route/Shell: **134**
- Navigation: **68**
- Tables: **107**
- Dialogs/Overlays: **89**
- Forms: **39**
- Coaching: **11**

## Batch Certification Ledger
### 2026-08-01 · Shared Tables Batch 01 · CLOSED
- Closed routes: `/admin/scheduler-runs`, `/admin/leadership-equipment`, `/admin/terminations`, `/admin/guide`, `/admin/executive-operational-intelligence`, `/pm/operational-intelligence`
- Shared fixes: canonical `DataTable` upgrade, `wp17.css` table shell styling, scheduler legacy-banner removal, `LastActivityLine` portal guard
- Evidence: `/app/test_reports/iteration_95.json` plus responsive screenshot sets at `390`, `768`, `1024`, and `1440`
- Denominator movement: full-ledger table survivors `113 → 107`; active-route table queue `19 → 13`
- Carry-forward note: dual-nav coexistence on some wider shells remains a Navigation-batch cleanup item; it did not block table certification

## Active-Route Survivor Queue
### Header survivors (41)
- `/` · `Hub` · replace legacy/local header with canonical shell
- `/safety/forms/equipment-issuance/:id` · `ViewSafetyForm` · replace legacy/local header with canonical shell
- `/safety/forms/equipment-training/:id` · `ViewSafetyForm` · replace legacy/local header with canonical shell
- `/safety/cards` · `FieldSafetyCards` · replace legacy/local header with canonical shell
- `/qaqc/:id` · `ViewQaqcInspection` · replace legacy/local header with canonical shell
- `/trench-safety` · `trench_safety/PublicTrenchSafetyDashboard` · replace legacy/local header with canonical shell
- `/trench-safety/tabulated-data` · `trench_safety/PublicTrenchSafetyTabulatedData` · replace legacy/local header with canonical shell
- `/trench-safety/references` · `trench_safety/PublicTrenchSafetyReferences` · replace legacy/local header with canonical shell
- `/trench-safety/report` · `trench_safety/PublicTrenchSafetyReport` · replace legacy/local header with canonical shell
- `/trench-safety/assets/:assetId` · `trench_safety/TrenchSafetyQrLanding` · replace legacy/local header with canonical shell
- `/transport-invite/:token` · `transportation/ExternalCarrierInvite` · replace legacy/local header with canonical shell
- `/transport-verify/:cnum` · `transportation/CertificateVerify` · replace legacy/local header with canonical shell
- `/near-miss` · `NearMissKiosk` · replace legacy/local header with canonical shell
- `/thank-you` · `ThankYou` · replace legacy/local header with canonical shell
- `/cheatsheet` · `CheatSheet` · replace legacy/local header with canonical shell
- `/trench-safety/excavation/new` · `trench_safety/PublicExcavationForm` · replace legacy/local header with canonical shell
- `/admin/inspections/:id` · `ViewInspection` · replace legacy/local header with canonical shell
- `/admin/meetings/:id` · `ViewMeeting` · replace legacy/local header with canonical shell
- `/admin/trench-boxes/poster` · `TrenchBoxPoster` · replace legacy/local header with canonical shell
- `/admin/jha-plans/poster` · `JhaPlansPoster` · replace legacy/local header with canonical shell

### Form survivors (3)
- `/revise/:token` · `Revise` · move to canonical FormShell or canonical public auth shell
- `/near-miss` · `NearMissKiosk` · move to canonical FormShell or canonical public auth shell
- `/sign-in` · `SignIn` · move to canonical FormShell or canonical public auth shell

### Table survivors (13)
- `/safety/forms/equipment-issuance/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/safety/forms/equipment-training/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/leadership/records/:id` · `FieldLeadershipView` · move to canonical data table shell
- `/safety/cases/:caseId/reports/:reportType` · `IncidentReportViewer` · move to canonical data table shell
- `/safety/cases/:caseId/executive-report` · `ExecutiveCaseReport` · move to canonical data table shell
- `/admin/pnl` · `ProjectPnlPage` · move to canonical data table shell
- `/admin/daily/:id` · `ViewDailyReport` · move to canonical data table shell
- `/admin/leadership/records/:id` · `FieldLeadershipView` · move to canonical data table shell
- `/admin/safety/issuance/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/admin/safety/training/:id` · `ViewSafetyForm` · move to canonical data table shell
- `/pm/daily/:id` · `ViewDailyReport` · move to canonical data table shell
- `/hr/daily-reports/:id` · `ViewDailyReport` · move to canonical data table shell
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

### Navigation survivors (6)
- `/safety/cards` · `FieldSafetyCards` · remove local back controls and duplicate navigation affordances
- `/transport-invite/:token` · `transportation/ExternalCarrierInvite` · remove local back controls and duplicate navigation affordances
- `/transport-verify/:cnum` · `transportation/CertificateVerify` · remove local back controls and duplicate navigation affordances
- `/admin/daily/:id` · `ViewDailyReport` · remove local back controls and duplicate navigation affordances
- `/pm/daily/:id` · `ViewDailyReport` · remove local back controls and duplicate navigation affordances
- `/hr/daily-reports/:id` · `ViewDailyReport` · remove local back controls and duplicate navigation affordances
