# PLATFORM_PROGRESSIVE_DISCLOSURE_STANDARD

Status: PARTIAL PASS — PRE-C10 blocking standard remains open until the remaining denominator closes.

## Runtime rule

Primary work first, optional coaching second, diagnostics third, recovery last.

## Classification rule

- **Optional coaching** includes workflow tips, how-this-works guidance, why-this-matters explainers, next-step help, and similar operator coaching that improves confidence but is not required to safely complete the current action.
- **Required warnings stay visible**: safety blockers, legal/compliance notices, destructive or irreversible warnings, mandatory acknowledgements, and governed recovery-risk notices must never be collapsed as optional coaching.
- A route must not hide the main work area behind tutorial copy. The operator should see the task, form, list, or action surface before opening any extra guidance.

## Shared runtime pattern

- Shared disclosure primitive: `frontend/src/components/WorkflowCoachingDisclosure.jsx`
- Governing behavior:
  - collapsed by default;
  - trigger is a real focusable button;
  - `aria-expanded` truthfully reflects state;
  - optional panel is absent until opened;
  - all triggers carry unique `data-testid` values for runtime certification.
- Shared consumers now governed by this pattern in the current batch:
  - `HelpTipBlock`
  - `OperationalCoachingStrip`
  - `WhyItMattersPanel`
  - Dispatch Hub command coaching
  - Historical Records Intake “How this works” guidance

## Certified runtime evidence in this batch

- **Known Employee Lifecycle repair completed**: `/hr/employees` now keeps lifecycle coaching collapsed by default through `helptip-block-employee-lifecycle-trigger`.
- **Admin Daily Reports repair completed**: `/admin/daily` now keeps optional workflow coaching collapsed by default through `daily-reports-coaching-strip-trigger`.
- Additional shared-pattern spot certification completed on:
  - `/dispatch-portal`
  - `/hr/historical-records/intake`
  - `/safety-portal/corrective-actions`
- Targeted screenshot Product Quality subset passed with the upgraded coaching contract:
  - `scripts/runtime_screenshot_ledger_gate.py`
  - contract version `wp18db-product-quality-v4`
  - targeted rows: `20`
  - failures: `0`
  - languages: `EN` + `ES`
  - widths: `390 / 430 / 768 / 1024 / 1440`
- Frontend QA evidence:
  - `/app/test_reports/iteration_7.json` → PASS
  - `auto_frontend_testing_agent` final verification → PASS on HR Employee Lifecycle, Admin Daily Reports, Dispatch Hub, Historical Records Intake, and Safety Corrective Actions
- Backend smoke evidence:
  - `deep_testing_backend_v2` → `7 / 7 PASS`
  - auth continuity and guidance-tip endpoints showed no regression from the coaching refactor.

## Current certified findings

- Optional coaching expanded by default on the certified shared-pattern surfaces: `0`
- Required-warning visibility preserved on the certified Safety corrective-actions surface.
- No horizontal overflow on the certified coaching routes at the tested widths.
- English / Spanish coaching disclosure behavior verified on the targeted routes.

## Remaining open denominator

- **Unverified coaching surfaces are current PRE-C10 denominator, not backlog.**
- Any existing operator-facing route, dialog, drawer, mobile state, or shared component that still contains optional coaching/help/guidance remains open until it is explicitly inventoried and dispositioned.
- Preserve the shared disclosure rule while the remaining PRE-C10 register rows are reconciled.
- Continue route-by-route bookkeeping in `PRE_C10_MASTER_REMEDIATION_REGISTER.md`; no denominator row may silently disappear.
- Re-run the fresh full screenshot Product Quality ledger after the remaining PRE-C10 edits are complete so the upgraded coaching contract is carried by the full portfolio pass, not only the targeted coaching subset.
- Keep the prior open hierarchy sweeps active wherever a route still mixes helper copy, diagnostics, and recovery in the wrong order.

## Compact governance-only coaching inventory

| Route / surface | Role | Coaching surface / component | Trigger `data-testid` | Default state | Required-warning exception? | EN | ES | 390 | 430 | 768 | 1024 | 1440 | Accessibility | Screenshot evidence | Final disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `/hr/employees` | HR | `HelpTipBlock` (`employee-lifecycle`) | `helptip-block-employee-lifecycle-trigger` | collapsed | No | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | targeted v4 ledger + QA | **REPAIRED + RUNTIME CERTIFIED** |
| `/admin/daily` | Admin | `OperationalCoachingStrip` | `daily-reports-coaching-strip-trigger` | collapsed | No | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | targeted v4 ledger + QA | **REPAIRED + RUNTIME CERTIFIED** |
| `/dispatch-portal` | Dispatch | shared `WorkflowCoachingDisclosure` | `ds-section-command-trigger` | collapsed | No | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | frontend QA | **REPAIRED + RUNTIME CERTIFIED** |
| `/hr/historical-records/intake` | HR | shared `WorkflowCoachingDisclosure` | `intake-how-it-works-trigger` | collapsed | No | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | frontend QA | **REPAIRED + RUNTIME CERTIFIED** |
| `/safety-portal/corrective-actions` | Safety | `WhyItMattersPanel` + `HelpTipBlock` | `why-it-matters-panel-trigger` | collapsed | **Yes — required CAPA warnings stay visible outside optional coaching** | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | frontend QA | **REPAIRED + RUNTIME CERTIFIED** |
| `/admin/login` | Public | `PortalLoginHelp` | `portal-login-help-admin-trigger` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/pm/login` | Public | `PortalLoginHelp` | `portal-login-help-pm-trigger` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/hr/login` | Public | `PortalLoginHelp` | `portal-login-help-hr-trigger` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/safety-portal/login` | Public | `PortalLoginHelp` | `portal-login-help-safety-trigger` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/dispatch-portal/login` | Public | `PortalLoginHelp` | `portal-login-help-dispatch-trigger` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/shop/login` | Public | `PortalLoginHelp` | `portal-login-help-shop-trigger` | collapsed | No | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | not yet captured | CURRENT DENOMINATOR — runtime pending |
| `/field-leadership/portal/login`, `/leadership/login` | Public | `PortalLoginHelp` | `portal-login-help-leadership-trigger` | collapsed | No | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | not yet captured | CURRENT DENOMINATOR — runtime pending |
| `/operations-actions` | Cross-portal public workflow | `CoachingPanel` | `oa-coaching-panel-trigger` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/operations-actions/new` | Cross-portal public workflow | `CoachingPanel` | `oa-coaching-panel-trigger` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/operations-actions/:id` | Cross-portal public workflow | `CoachingPanel` | `oa-coaching-panel-trigger` | collapsed | No | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | OPEN | route fixture still needed | CURRENT DENOMINATOR — runtime pending |
| `/notifications` | Role-aware | `LifecycleGuide` | `lifecycle-guide-toggle-notifications-digest` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/admin/compliance-findings` | Admin | `LifecycleGuide` | `lifecycle-guide-toggle-admin-compliance-findings` | collapsed | No | IN PROGRESS | N/A (admin page convention remains English-first) | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/hr/incidents` | HR | `LifecycleGuide` | `lifecycle-guide-toggle-hr-incidents` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/pm/crew-compliance` | PM | `LifecycleGuide` | `lifecycle-guide-toggle-pm-crew-compliance` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/dispatch-portal/board` | Dispatch | `LifecycleGuide` | `lifecycle-guide-toggle-dispatch-operational-board` | collapsed | No | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |
| `/trench-safety/excavation/new` | Public | `OshaCoachingBlock` family | `coach-soil-toggle` + other `coach-*` triggers | collapsed | **Yes — stop-work / emergency / rated-depth warnings must stay visible outside optional OSHA coaching** | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | IN PROGRESS | wide coaching sweep | CURRENT DENOMINATOR — runtime sweep in progress |

### Shared-family denominator rows still open

- **Shared `HelpTipBlock` family** now inherits the collapsed-by-default repair, but these routes remain part of the active denominator until they are explicitly runtime-certified or factually exempted: `/document-expirations`, `/field/calculators`, `/field-leadership/portal`, `/field-leadership/portal/change-password`, `/leadership/records`, `/admin/leadership/records`, `/shop/fleet`, `/safety-portal/fleet`, `/hr/driver-qualification`, `/hr/employee-accountability`, `/hr/field-leadership`, `/hr/field-leadership-users`, `/hr/payroll-variance`, `/hr/time-off`, `/hr/time-verification`, `/safety/inspections/new`, `/qaqc/:slug/new`, `/safety/forms/equipment-issuance/new`, `/safety/forms/equipment-training/new`, `/safety-portal/documents`, `/safety-portal/fire-extinguishers`, `/safety-portal/library`, `/safety-portal/training`, `/admin/dispatch`, plus other route-specific `HelpTip` / `HelpTipBlock` consumers already mapped in source.
- **Shared `LifecycleGuide` family** now inherits the collapsed-by-default repair, but these routes remain part of the active denominator until explicitly closed: `/admin/dls/shift-qr`, `/admin/operational-language`, `/admin/incidents/:id`, `/pm/incidents/:id`, `/safety-portal/incidents/:id`, `/hr/employees/:id/accountability`.
- **Shared `HelpDrawer` family** is currently collapsed by explicit trigger (drawer closed until opened) on `/incidents/report`, `/equipment/new`, `/equipment/submit`, `/fleet/dvir/new`, `/fleet/dvir/submit`, `/fleet/weekly-lead/new`, `/fleet/weekly-emergency/new`, `/meetings/new`, `/meetings/submit`; these remain current denominator rows for route-by-route runtime spot certification.