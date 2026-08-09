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

- Preserve the shared disclosure rule while the remaining PRE-C10 register rows are reconciled.
- Continue route-by-route bookkeeping in `PRE_C10_MASTER_REMEDIATION_REGISTER.md`; no denominator row may silently disappear.
- Re-run the fresh full screenshot Product Quality ledger after the remaining PRE-C10 edits are complete so the upgraded coaching contract is carried by the full portfolio pass, not only the targeted coaching subset.
- Keep the prior open hierarchy sweeps active wherever a route still mixes helper copy, diagnostics, and recovery in the wrong order.