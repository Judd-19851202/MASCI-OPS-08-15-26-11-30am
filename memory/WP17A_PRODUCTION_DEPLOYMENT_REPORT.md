# WP17A Production Deployment Report

Date: 2026-07-31
Result: **NOT DEPLOYED / VALIDATION FAILED**

## Deployment result

- Production site checked: `https://mascidocs.com`
- Current live build remains:
  - commit `fd89cfe673d61292075a4f6668a2d0e71dcdd5f4`
  - source hash `ec85d311da889befeb222f6ee3bf1931`
- Proposed WP-17A build remains preview-only:
  - commit `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc`
  - source hash `665ea6071d75dd046905a35dfe8dcea4`

## Live validation findings

- Pre-deployment release gate decision in preview: PASS
- `/api/admin/wp17a/kpi-dictionary` → `404`
- `/api/admin/wp17a/reconciliation` → `404`
- `/api/admin/wp17a/certification` → `404`
- `/api/admin/wp17a/deployment-package` → `404`
- Existing baseline health endpoints remain healthy on production (`/api/health`, `/api/version`, `/api/ready`)
- Existing production app remains live but is not serving the WP-17A package

## Repairs completed during gate

- Restored release-gate regressions for daily-report / QAQC PM empty-scope short-circuits
- Removed route-level env reads from admin persistence health
- Updated build stamp and release identity artifact
- Added secret-scan allow-line annotations for governed fixture-only Mongo examples

## Remaining blocker

- Native Emergent production deployment was not executed in this run, so the validated WP-17A code never reached `mascidocs.com`.

## Recommendation

- Do not lock WP-17A.
- Execute the native production deploy for build `bd9bdd2012c4f2e31b57d7390218b20c361c6dcc` / source `665ea6071d75dd046905a35dfe8dcea4`, then rerun live validation immediately.