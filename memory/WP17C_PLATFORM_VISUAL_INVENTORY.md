# WP17C Platform Visual Inventory

Last updated: 2026-08-01

## Scope
- Full ledger denominator: **1,190** surfaces from `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv`
- Reachable route inventory from `AppRoutes.jsx`: **445** route entries
- Active routed page components resolved: **104**

## Current Full-Ledger Survivor Snapshot
- Route/Shell survivors: **134**
- Navigation survivors: **68**
- Table survivors: **113**
- Dialog/Overlay survivors: **89**
- Form survivors: **39**
- Coaching survivors: **11**
- Waitlist/secondary-flow survivors: **10**

## Current Active-Route Code Scan Snapshot
- Header survivors: **41**
- Form-layout survivors: **3**
- Table survivors: **19**
- Dialog survivors: **0**
- Icon-library survivors: **0**
- Coaching survivors: **20**
- Navigation survivors: **6**
- Typography survivors: **3**
- Spacing/layout survivors: **1**

## Inventory Sources
- Route matrix: `/app/memory/WP17C_ROUTE_STYLE_MATRIX.csv`
- Drift register: `/app/memory/WP17C_DESIGN_DRIFT_REGISTER.csv`
- Zero-legacy board: `/app/memory/WP17C_WP17D_ZERO_LEGACY_SURVIVOR_BOARD.md`
- Survivor register: `/app/memory/WP17D_SURVIVOR_REGISTER.md`
- Token register: `/app/memory/WP17C_DESIGN_TOKEN_REGISTER.json`

## Current Method
1. Reconcile every survivor category against the full 1,190-surface ledger denominator.
2. Maintain a live active-route code scan against `AppRoutes.jsx` to select the next repair wave.
3. Verify each migrated route in browser automation before reducing survivor pressure.
4. Record unresolved drift in the design drift register instead of hiding it behind generic “migrated” status.

## Immediate Next Active Survivors
- `/` → `Hub`
- `/safety/forms/equipment-issuance/:id` → `ViewSafetyForm`
- `/safety/forms/equipment-training/:id` → `ViewSafetyForm`
- `/safety/cards` → `FieldSafetyCards`
- `/qaqc/:id` → `ViewQaqcInspection`
- `/trench-safety` → `trench_safety/PublicTrenchSafetyDashboard`
- `/trench-safety/tabulated-data` → `trench_safety/PublicTrenchSafetyTabulatedData`
- `/trench-safety/references` → `trench_safety/PublicTrenchSafetyReferences`
- `/trench-safety/report` → `trench_safety/PublicTrenchSafetyReport`
- `/trench-safety/assets/:assetId` → `trench_safety/TrenchSafetyQrLanding`
- `/transport-invite/:token` → `transportation/ExternalCarrierInvite`
- `/transport-verify/:cnum` → `transportation/CertificateVerify`
