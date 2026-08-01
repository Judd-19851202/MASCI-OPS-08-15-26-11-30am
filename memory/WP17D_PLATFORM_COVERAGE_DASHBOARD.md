# WP-17D Platform Coverage Dashboard

Last updated: 2026-08-01

## Governing Denominator
- Total audited surfaces: **1,190 / 1,190** discovered in `WP17D_PLATFORM_CONVERGENCE_LEDGER.csv`
- Locked route denominator: **481**
- Locked hidden/detail denominator: **113**
- Locked forms denominator: **66**
- Locked PDF sources denominator: **15**
- Locked email/template denominator: **14**
- Locked navigation denominator: **253**
- Locked component-family denominator: **64**
- Locked terminology-conflict denominator: **8**
- Locked coaching/help denominator: **11**

## Discovery Completeness Status

### Route Discovery
- Route definitions discovered directly in `AppRoutes.jsx`: **447 / 481**
- Discovery gap still open: **34 routes**
- Current discovery confidence: **NOT CERTIFIED**
- Verified status: direct route-definition scan is incomplete against the locked route denominator and cannot be treated as 100% discovery.

### Hidden / Detail Discovery
- Locked hidden/detail denominator: **113**
- Source-verified hidden/detail state rows currently found in the platform ledger (`DETAIL` + `HIDDEN`): **140**
- Discovery discrepancy: **+27 surfaces**
- Current discovery confidence: **NOT CERTIFIED**
- Verified status: denominator reconciliation is still open and must be resolved before hidden-surface discovery can be considered complete.

### Form Discovery
- Form surfaces discovered in the locked ledger: **66 / 66**
- Current discovery confidence: **PROVISIONAL — registry present, route/context reconciliation pending**

### PDF / Template Discovery
- PDF sources discovered in the locked ledger: **15 / 15**
- Email/template sources discovered in the locked ledger: **14 / 14**
- Current discovery confidence: **PROVISIONAL — invocation-path reconciliation pending**

### Navigation Discovery
- Navigation items discovered in the locked ledger: **253 / 253**
- Current discovery confidence: **PROVISIONAL — reachability mapping pending**

### Component Discovery
- Locked component-family denominator: **64**
- Component-family route consumers actively traced in current hunt: **started, not yet reconciled to 64 / 64**
- Verified shared hero families currently under audit:
  - `OperationalPageFrame`
  - `OperationalOutcomeFrame`
  - `DetailPageHero`
  - `wp17-mission-banner`
- Current discovery confidence: **NOT CERTIFIED**

## Platform-Wide Discovery Snapshot
- Locked ledger rows discovered: **1,190 / 1,190**
- App router path definitions discovered: **447**
- Existing route entries with a prior `CERTIFIED` disposition in the locked ledger: **40**
- Existing route entries with `IMPLEMENTED` disposition in the locked ledger: **617**
- Existing route entries with `MIGRATING` disposition in the locked ledger: **436**
- Existing route entries with `REDIRECTED` disposition in the locked ledger: **53**
- Existing route entries with `HIDDEN` disposition in the locked ledger: **44**

## Current Executive Certification Status
- Platform discovery complete: **No**
- Route discovery confidence = 100%: **No**
- Hidden-surface discovery confidence = 100%: **No**
- Component-family discovery confidence = 100%: **No**
- Platform can begin final executive certification math: **No**

## First Reachability Deliverable
- Route-to-entry-point ledger created: `/app/memory/WP17D_PLATFORM_REACHABILITY_LEDGER.csv`
- Current ledger row count: **447** route definitions
- Current fields:
  - `route`
  - `family`
  - `role`
  - `visible_entry_point`
  - `navigation_path`
  - `reachability_status`
  - `hidden_surface_disposition`
  - `certification_status`
  - `route_kind`
  - `source_line`

## Route-to-Entry Reachability Snapshot
- `DISCOVERED_ENTRY_REVIEW_PENDING`: **293**
- `DISCOVERED_NEEDS_REACHABILITY_PROOF`: **106**
- `DISCOVERED_ALIAS`: **48**

## Hidden Surface Disposition Snapshot
- `EXPOSED_OR_NAV_REVIEW`: **293**
- `JUSTIFIED_HIDDEN_REVIEW`: **89**
- `REDIRECT`: **48**
- `MERGE_OR_RETIRE_REVIEW`: **17**

## Current Family Distribution in Reachability Ledger
- Administration: **147** routes
- Safety Operations: **54** routes
- Project Management: **47** routes
- Human Resources: **32** routes
- Shop Operations: **26** routes
- Transportation Operations: **17** routes
- Field Leadership: **12** routes
- Training / Guidance / Coaching: **8** routes
- Field Operations: **3** routes directly mapped at current family granularity
- Shared Operational Home / Public Entry: **101** routes

## Open Discovery Survivors
1. **Route denominator mismatch** — 447 route definitions found vs locked denominator 481
2. **Hidden/detail mismatch** — 140 source-verified hidden/detail surfaces vs locked denominator 113
3. **Family normalization drift** — locked 13-family model still needs explicit reconciliation for dispatch/driver/executive rows into the governing family taxonomy
4. **Component-family denominator unreconciled** — 64 locked families not yet individually mapped to consuming surfaces
5. **Reachability proof incomplete** — ledger exists, but click-path validation is not yet proven for most discovered routes

## Immediate Next Discovery Actions
1. Reconcile the **34-route gap** between `AppRoutes.jsx` and the locked 481-route denominator
2. Reconcile the **140 vs 113** hidden/detail discrepancy and classify each variance
3. Expand the reachability ledger from route definitions into **click-path evidence**
4. Create primitive-family ledgers for:
   - Hero
   - Card
   - Button
   - Form controls
   - Tables
   - Dialogs
   - Navigation
   - Icons
   - Alerts
   - Empty states
   - Success states
   - Loading states
5. Continue active closure already in progress:
   - Daily Report review/detail/edit/return
   - DVIR public submit and return path
   - queued/failed `/thank-you` states