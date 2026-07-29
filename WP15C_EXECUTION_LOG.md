# WP-15C Execution Log

Date opened: 2026-07-29
Status: In progress

## Constitutional Guardrails
- Enterprise Governance architecture frozen for WP-15C.
- No new product features unrelated to governance convergence.
- No temporary compatibility shortcuts that bypass governance.
- Every migration must reduce repository governance drift.
- WP-16 remains blocked until WP-15C reaches VERIFIED certification.

## Approved Phase Order
1. Constitutional Guardrails
2. Repository Governance Convergence Scanner expansion
3. Repository Migration batches
4. Governance Coverage Dashboard
5. CI/CD Constitutional Gate
6. Constitutional Certification suites
7. Independent Constitutional Audit
8. Frontend & UX Verification
9. Baseline Generation

## Current Batch
- Expand scanner classification and coverage metrics.
- Migrate legacy authorization in priority cluster order:
  1. Operations Center
  2. Tasks & Notifications
  3. Safety
  4. Cost Codes
  5. PO Requests
  6. Global Search

## Convergence Rule
Every non-compliant authorization decision must be classified as one of:
- Canonical Governance
- Legacy Migratable
- Infrastructure Adapter
- Constitutionally Approved Exception
- Dead Code

## Certification Blockers
- Legacy Migratable > 0
- Duplicate Business Authorization > 0
- Inline Business Authorization > 0
- Coverage Dashboard missing
- CI/CD governance gate not yet enforcing constitutional failure conditions
- Independent Constitutional Audit not yet executed

## Batch WP15C-2026-07-29-B2
- Timestamp: 2026-07-29 UTC
- Scope:
  - Normalize scanner findings into durable constitutional decision points
  - Add frontend request-lifecycle surface scanning
  - Generate existing identity continuity inventory
  - Document canonical request lifecycle and identity continuity guardrails
- Findings before:
  - Backend-centric scan with raw occurrence emphasis
  - Cross-portal 401 root cause already traced to incomplete directory-session context forwarding
- Findings after:
  - Scanner model upgraded with schema/version metadata and baseline expansion labeling
  - Existing identity inventory captured without exposing secrets
  - Canonical lifecycle and continuity documents created
- Migrations completed:
  - Shared governance scope helper introduced in `lib.enterprise_governance`
  - Additional `compute_pm_scope` consumers migrated in `project_health.py`, `operational_kpis.py`, `asset_transfers.py`, `trench_project_intelligence.py`, `dr_v2_pdf.py`, and `pm_routes.py`
- Tests:
  - `pytest /app/backend/tests/test_wp15_enterprise_governance.py -q` → `5 passed`
- Remaining risks:
  - Manual governed-request header construction remains widespread in frontend code
  - Category F findings still require individual disposition
  - Existing-user regression matrix still needs broader portal login coverage
- Next batch:
  - Finish scanner normalization outputs and use them as the new constitutional baseline
  - Converge the highest-volume manual frontend header builders onto the canonical scoped builder
  - Add existing-user login/session continuity tests for HR, Dispatch, Shop, and Field Leadership

## Batch WP15C-2026-07-29-B3
- Timestamp: 2026-07-29 UTC
- Scope:
  - Eliminate highest-volume shared governed header-builder families (`admin_dispatch`, safety-only, FL-only, cross-portal shop/dispatch views)
  - Continue `compute_pm_scope` burn-down in `daily_reports`, `equipment`, `job_photos`, `pm_command_center`, and `project_team_assignments`
  - Burn down Category F with scanner-rule refinement and concrete code cleanup
- Files changed:
  - Frontend shared clients/pages: `DispatchHub.jsx`, `DispatchBoard.jsx`, `MotivePostureRibbon.jsx`, `AssignmentDrawer.jsx`, `AttachmentStrip.jsx`, `AssignmentCreateDrawer.jsx`, `TransportationGate.jsx`, `DispatchDecisionChip.jsx`, `oa.js`, `FleetVisibility.jsx`, `FlAccountabilityWidget.jsx`, `HrSafetyRecords.jsx`, `SafetyCorrectiveActions.jsx`, `SafetyDigest.jsx`, `SafetyDocuments.jsx`, `SafetyEmployeeProfiles.jsx`, `SafetyFormsRecords.jsx`, `SafetyTrainingRecords.jsx`
  - Backend governance scope families: `daily_reports.py`, `equipment.py`, `job_photos.py`, `pm_command_center.py`, `project_team_assignments.py`, `lib/enterprise_governance.py`, `tools/wp15_governance_convergence_scan.py`
- Shared patterns changed:
  - `admin_dispatch` → converged onto `buildScopedPortalAuthHeaders`
  - safety-only page auth builders → converged onto `buildScopedPortalAuthHeaders`
  - FL-only widget auth builder → converged onto `buildScopedPortalAuthHeaders`
  - legacy PM scope helper families → moved to governance-applied scope helpers / `GovernanceProjectScope`
- Consumers affected:
  - dispatch command/board/drawer/gate flows
  - operations actions helper consumers
  - fleet visibility shared views
  - safety document/digest/forms/profiles/training/corrective-actions pages
  - PM command center and staffing summary scope consumers
- Previous scanner metrics (baseline from B2 normalized model):
  - Legacy: `82`
  - Manual governed builders: `37`
  - Canonical builder adoption: `18.99%`
  - Category F: `1`
- Current scanner metrics:
  - Legacy: `71`
  - Manual governed builders: `29`
  - Canonical builder adoption: `21.13%`
  - Category F: `0`
- Deltas:
  - Legacy delta: `-11`
  - Builder-adoption delta: `+2.14%`
  - Manual-builder delta: `-8`
  - Category F delta: `-1`
- Existing-user tests:
  - Multi-login continuity preserved for Admin, PM, Safety, HR, Dispatch, Shop, and Field Leadership (`200`)
  - Standalone portal login continuity preserved for PM, HR, Dispatch, Field Leadership, and Shop (`200`)
  - Incorrect PM password still denied (`401`)
  - Disabled directory user fixture remains denied (`401`)
- Session-continuity tests:
  - PM portal token + mismatched HR directory session → `401`
  - PM portal token + matching PM directory session → `200`
  - PM portal token without directory context → `401`
- Governance tests:
  - `pytest /app/backend/tests/test_wp15_enterprise_governance.py -q` → `5 passed`
- Remaining risks:
  - Manual governed builders still remain outside the converged shared families
  - Disabled-user and explicit session-expiry live verification remain incomplete
- Additional note:
  - `backend/tests/test_full_cert_auth_sweep.py` contains stale assumptions about retired admin/legacy login surfaces and list payload shapes; it is not currently a reliable WP-15C certification suite without refresh.
- Next planned batch:
  - Resolve the final Category F path with structural scanner refinement or code simplification
  - Burn down remaining manual builders, especially infrastructure/bootstrap vs governed-path distinctions
  - Add disabled-user and broader session-expiry/recovery verification
