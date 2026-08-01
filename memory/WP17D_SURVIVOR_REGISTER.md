# WP-17D Survivor Register

Last updated: 2026-08-01

## Denominator Rule
- Master platform denominator: **1,190** audited surfaces from `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv`
- Operational fixing order: **active route code scan first**, then reconcile back into the full ledger denominator

## Platform-Wide Ledger Counts (1,190-surface register)
These counts come from the ledger taxonomy prefixes and status columns, so they reconcile to the full WP-17D inventory.

- Legacy route/shell survivors remaining: **134** `ROUTE-*` surfaces still `MIGRATING`
- Legacy navigation survivors remaining: **68** `NAV-*` surfaces still `MIGRATING`
- Legacy table survivors remaining: **113** `TABLE-*` surfaces still `MIGRATING`
- Legacy dialog/overlay survivors remaining: **89** `OVERLAY-*` surfaces still `MIGRATING`
- Legacy form survivors remaining: **39** `FORM-*` surfaces still `MIGRATING`
- Legacy coaching survivors remaining: **11** `COACH-*` surfaces still provisionally implemented and still require executive recertification
- Waitlist/secondary flow survivors remaining: **10** `WL-*` surfaces still `MIGRATING`

## Active Route Code Scan (live repo scan of routed pages)
These counts are used to choose the next engineering wave from the currently active user-facing routes in `AppRoutes.jsx`.

- Active routed page components scanned: **104**
- Legacy header survivors remaining: **31**
- Legacy form-layout survivors remaining: **4**
- Legacy table survivors remaining: **13**
- Legacy dialog survivors remaining: **0**
- Legacy icon-library survivors remaining: **0**
- Legacy coaching survivors remaining: **14**
- Legacy navigation survivors remaining: **7**
- Legacy typography survivors remaining: **3**
- Legacy spacing/layout survivors remaining: **3**

## Highest-Priority Active Survivors (next route wave)

### Header / shell survivors
- `/sign-in` → `SignIn.jsx`
- `/near-miss` → `NearMissKiosk.jsx`
- `/field/calculators` → `MaterialCalculators.jsx`
- `/safety/cards` → `FieldSafetyCards.jsx`
- `/jha` → `JhaPlansHub.jsx`
- `/fleet/dvir/submitted/:id` → `FleetDVIRConfirmation.jsx`
- `/thank-you` → `ThankYou.jsx`
- `/access-denied` → `AccessDenied.jsx`

### Form-layout survivors
- `/sign-in` → `SignIn.jsx`
- `/near-miss` → `NearMissKiosk.jsx`
- `/revise/:token` → `Revise.jsx`
- `/safety/forms/equipment-issuance/:id/return` → `ReturnEquipment.jsx`

### Table survivors
- `/admin/guide` → `AdminGuide.jsx`
- `/admin/leadership-equipment` → `AdminLeadershipEquipment.jsx`
- `/admin/scheduler-runs` → `AdminSchedulerRuns.jsx`
- `/admin/terminations` → `AdminTerminations.jsx`
- `/dev` → `DevHub.jsx`
- `/admin/pnl` → `ProjectPnlPage.jsx`

### Navigation survivors
- `/safety/cards` → `FieldSafetyCards.jsx`
- `/field/calculators` → `MaterialCalculators.jsx`
- `/jha` → `JhaPlansHub.jsx`
- `/fleet/dvir/submitted/:id` → `FleetDVIRConfirmation.jsx`

## Recently Cleared In This Wave
- Auth convergence survivors cleared: safety forgot/reset/change, HR reset, dispatch reset/change, shop reset/change, PM change, dev login
- FormShell survivors cleared: `NewSafetyEquipmentIssuance.jsx`, `NewSafetyEquipmentTraining.jsx`, `NewEquipmentInspection.jsx`, `NewFleetDVIR.jsx`
- Section shell survivors cleared: `/field`, `/qaqc`, `/safety`
- HUNT MODE Field survivors cleared:
  - `NewDailyReportV3.jsx` public custom-job path no longer calls private cost-code assignment endpoints without a portal token
  - `sections.jsx` Daily Report signature now emits the governed `dr-v3-signature-canvas` test surface correctly
  - `/thank-you` no longer mixes English preview-capture body copy in Spanish success states
  - `FieldLeadershipView.jsx` now restores Spanish-original detail content through bilingual sidecar evidence
  - `FieldLeadership*` and Equipment/DVIR public flows no longer emit unsupported notification/asset lookup console noise on reopened routes

## Method Notes
- The ledger counts are the authoritative platform-wide denominator counts.
- The active-route scan is the engineering work queue for the next survivor hunt.
- A surface is not complete until it passes functional, responsive, visual, and executive certification.