# WP18CZ.1 Submission Final Test Report

Date: 2026-08-06

## Scope of this pass

This pass focused on the currently active WP-18CZ.1 submission closeout blockers that still needed runtime truth after the shared confirmation rollout:

- Fuel / Lube Visit
- Service Truck Reconciliation
- Operational Constraints
- Asset Transfers
- Transportation External Carrier Invite
- JHA Acknowledgement
- Shared confirmation contract regressions already covered by `/app/test_reports/iteration_144.json`

## Code repairs applied in this pass

1. `frontend/src/pages/shop/FuelLubeVisitForm.jsx`
   - Fixed partial row patching so unit/equipment picker changes merge into the current line instead of replacing the row shape.
   - Added missing critical `data-testid` coverage for fuel/lube line inputs and totals.
2. `frontend/src/components/shop/ShopSelector.jsx`
   - Added keyboard navigation support.
   - Fixed mouse-click dropdown selection using `onMouseDown` to avoid blur-timing loss.
3. `frontend/src/pages/AssetTransfers.jsx`
   - Removed duplicate create POST.
   - Bound shared portal auth headers explicitly for create/list/detail/action calls.
4. `frontend/src/lib/constraintCapabilities.js`
   - Added shared-route portal-context seeding for PM/Admin/Safety/FL/HR token holders.
5. `frontend/src/pages/NewConstraint.jsx`
6. `frontend/src/pages/Constraints.jsx`
7. `frontend/src/pages/ConstraintDetail.jsx`
   - Applied shared-route portal-context seeding so direct visits to the shared constraint routes do not lose capabilities or auth scope.

## Runtime evidence used

- `/app/test_reports/iteration_144.json`
  - Shared confirmation contract pass.
  - Governed near-miss numbering and confirmation proof.
- `/app/test_reports/iteration_145.json`
  - Discovered the active blockers for fuel/lube selector binding, shared asset-transfer auth, and shared constraint access.
- `auto_frontend_testing_agent` runs on 2026-08-06
  - Verified Asset Transfers page load/create path stability.
  - Verified Constraints shared-route accessibility after the portal-context fix.
  - Verified Transportation External Carrier Invite page load remains intact.
  - Verified Fuel / Lube mouse + keyboard selection plus successful submission confirmation with governed number `FLV-2026-00179`.
- `/app/backend_test_results.json`
  - `20 / 20` backend checks passed.
  - Asset Transfer create + retrieve by id/doc number passed.
  - Constraint PM create/list/detail + Admin list passed.
  - Service Truck start/close plus linked fuel/lube aggregation structure passed.
  - Transportation public invite endpoints returned truthful already-submitted behavior for the used preview token.
  - JHA acknowledgement endpoints were reachable, but fixture data was insufficient for full create/read proof.

## Results by workflow

### Fully runtime verified in this pass

1. **Fuel / Lube Visit**
   - Confirmation screen: verified
   - Governed document number: verified (`FLV-2026-00179`)
   - Mouse and keyboard selection: verified
   - Detail/list/search trail: verified to preview-closeout standard

2. **Near Miss Public Submission**
   - Runtime verification inherited from `/app/test_reports/iteration_144.json`

### Partially runtime verified in this pass

1. **Asset Transfers**
   - Shared auth and duplicate create regression fixed.
   - Backend create/detail/search traceability verified.
   - Fresh browser confirmation-to-detail evidence still pending.

2. **Operational Constraints**
   - Shared-route access fixed.
   - PM/Admin backend create/list/detail verified.
   - Fresh browser confirmation-to-detail evidence still pending.

3. **Service Truck Reconciliation**
   - Backend start/close/detail truth verified.
   - Fresh browser confirmation/list/detail evidence still pending.

4. **Transportation External Carrier Invite**
   - Page load and public token endpoint behavior verified.
   - Current preview token is already consumed; a fresh unused token is still required to re-prove new submission confirmation on the current build.

### Still open in this pass

1. **JHA Acknowledgement**
   - Missing valid `employee_email` + `jha_file_id` fixture prevented full runtime proof.

2. **All confirmation-adoption-only workflows inherited from iteration 144**
   - Shared confirmation contract is present and previously smoke-verified.
   - Full workflow-level filing/detail/list/search/output proof was not rerun in this pass.

## Executive test conclusion

This pass **closed the active preview regressions** found in `/app/test_reports/iteration_145.json` and materially improved the submission closeout evidence set.

However, the platform-wide WP-18CZ.1 bar is still **NO-GO** because the pass does **not** yet contain complete workflow-family coverage, full role/device coverage at `390 / 430 / 768 / 1024 / 1440`, or complete output-channel proof for every governed submission family.