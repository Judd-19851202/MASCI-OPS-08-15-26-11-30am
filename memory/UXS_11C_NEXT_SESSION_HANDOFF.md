# UXS-11C — Next Session Handoff

**Created**: 2026-02-14 (end-of-session)
**Read this first** in the next session before any UXS-11C work.

## Why this file exists

The user requested **Track 14.0-UXS-11C** — a full platform
operational reality certification — at the end of the current
session with insufficient context budget remaining to do it honestly.
The user accepted Option C ("Close this session and restart fresh ·
execute Sweep A → B → C → D properly across 4 sub-sessions") so the
work could be done correctly rather than faked.

## What is already done (state at session close)

### Five evidenced drift routes — FIXED + LOCKED
| Route                     | Component               | Sidebar             |
|--------------------------|-------------------------|---------------------|
| `/project-health`         | `ProjectHealth.jsx`     | `PmSideNavV2`       |
| `/asset-transfers`        | `AssetTransfers.jsx`    | `PmSideNavV2`       |
| `/admin/jha-plans`        | `JhaPlansAdmin.jsx`     | `SafetySideNavV2`   |
| `/admin/trench-boxes`     | `TrenchBoxesAdmin.jsx`  | `AdminSideNavV2`    |
| `/po-requests`            | `PoRequests.jsx`        | `PmSideNavV2`       |

Locked by `backend/tests/test_route_parity_uxs11.py` (10 guards,
parametrized × 5). Live preview screenshots captured.

### Drift inventory — complete
`/app/memory/TRACK_14_0_UXS_11_ROUTE_DRIFT_INVENTORY.md` catalogues
**all 103 pages** that still import the legacy
`MasciLogo` / `HubBackLink` chrome:

* **5 fixed** (this track · regression-locked)
* **47 legitimate exceptions** (auth · login · reset · public forms ·
  print views · posters · NotFound — must stay sidebar-less by design)
* **~49 remaining operational drifted pages** enumerated by portal
  for follow-on sweeps

### RC1 test surface — 99/99 PASS
* `test_route_parity_uxs11.py` — 10
* `test_hr_readiness_certification.py` — 9
* `test_integration_honesty_and_archive_origin.py` — 20
* `test_data_hygiene_sweep.py` — 6
* `test_pdf_lockup_sweep.py` — 10
* `test_nav_drift_guard.py` — 24
* `test_team_snapshot_embedding.py` + `test_ownership_producer_routing.py` — 20

## What the next session must do (in order)

### Sweep A — PM Portal (≈9 pages · ~1.5 hours)
1. `DailyReportsDashboard.jsx`
2. `IncidentsDashboard.jsx`
3. `MeetingsDashboard.jsx`
4. `JobPhotosLibrary.jsx`
5. `DocumentExpirations.jsx`
6. `ProjectPnlPage.jsx`
7. `PmQaqcList.jsx`
8. `Tasks.jsx`
9. `Hub.jsx`

**Workflow audit during Sweep A** — PM staffing workflow (Co-PM ·
Project Engineer · Project Administrator · Asset Administrator
assignment). Verify each role can be assigned, viewed, and revoked.
Document gaps.

### Sweep B — HR Portal (≈9 pages · ~1.5 hours)
1. `HrHub.jsx` (legacy — confirm whether to keep or delete given HrHubV2 exists)
2. `HrEmployees.jsx` — **critical**: surface `preferred_name` next to legal name as "James Fisher (Jimmy)"
3. `HrFieldLeadershipUsers.jsx`
4. `HrDailyReports.jsx`
5. `HrIncidents.jsx`
6. `HrTimeOff.jsx`
7. `HrEmployeeAccountabilityTimeline.jsx`
8. `HrDriverProfile.jsx`
9. `HrMotiveDrivers.jsx`

**Identity audit during Sweep B** — verify `preferred_name` is
surfaced in: Directory · Daily Reports · Pre-Ops · Safety Forms ·
FL · Crew Rosters · Notifications · Detail Views · Timeline · PDF ·
CSV · Approval Dialogs. The backend already persists the field
(Track 14.0-HR-READINESS); the UI surfacing is the remaining work.

### Sweep C — Safety + Shop + Dispatch + FL (≈15 pages · ~2 hours)
* Safety: `SafetyFormsHub.jsx` · `SafetyDriverProfile.jsx` ·
  `SafetySection.jsx` · `JhaPlansHub.jsx` · `QaqcSection.jsx`
* Shop: `ShopHub.jsx` (legacy) · `EquipmentDashboard.jsx` ·
  `FleetVisibility.jsx`
* Dispatch: `DispatchCommandCenter.jsx` · `DispatchDriverProfile.jsx` ·
  `DispatchDriverQualification.jsx`
* FL: `FieldLeadershipHub.jsx` · `FieldLeadershipPortalDashboard.jsx` ·
  `FieldLeadershipDriverQualification.jsx` · `FieldSection.jsx`

### Sweep D — Admin (≈16 pages · ~2 hours)
* `AdminGuide.jsx` · `AdminQaqcList.jsx` · `AdminTerminations.jsx` ·
  `AdminTrainingVideos.jsx` · `AdminLeadershipEquipment.jsx` ·
  `OperationsCenterCommand.jsx` · `Dashboard.jsx` ·
  `MaterialCalculators.jsx` · `OpsTrainingCenter.jsx` ·
  `OpsTrainingGuide.jsx` · `TrainingHub.jsx` · `TrainingTrack.jsx` ·
  `guidance/OperationalGuidanceCenter.jsx` ·
  `operations_actions/OperationsActions.jsx` · `OperationsActionNew.jsx` ·
  `OperationsActionDetail.jsx`

## Wrap pattern (the same one used for the 5 fixed routes)

```jsx
// 1. Imports
import { PortalShell } from "@/design-system";
import <SidebarComponent> from "@/components/<domain>/sidebar/...";
// remove any MasciLogo / HubBackLink imports

// 2. Return
return (
  <PortalShell
    portalName="MASCI" portalRole="<Portal> · <Page>"
    pageTitle="<Page Title>"
    subtitle="<one-line description>"
    primaryActions={<...primary action buttons...>}
    sideNav={<SidebarComponent />}
  >
    <div className="...existing layout...">
      ...existing body...
    </div>
  </PortalShell>
);
```

## Regression guard pattern

Extend `backend/tests/test_route_parity_uxs11.py` after each page:

```python
EVIDENCE_ROUTES = {
    "ProjectHealth.jsx":   ("PmSideNavV2",     "PM Portal"),
    ...
    "<NewPage>.jsx":       ("<Sidebar>",       "<Portal>"),
}
```

The parametrized guards will then automatically lock the new page.

## Verification cadence (per page)

1. Wrap the page in PortalShell (above pattern).
2. Lint clean (`mcp_lint_javascript`).
3. Webpack compile clean (check supervisor logs).
4. Live preview screenshot at 1920×800.
5. Add to `EVIDENCE_ROUTES` in the regression test.
6. Run the full RC1 test suite — must stay 100% pass.

## Definition of Done for Track 14.0-UXS-11C

* All ~49 enumerated operational pages wrapped + screenshotted +
  regression-locked.
* `test_route_parity_uxs11.py` has 49 × 2 = 98+ parametrized
  assertions.
* HR preferred-name surfacing audit complete with evidence.
* PM staffing workflow audit complete with evidence.
* Drift inventory updated — moves pages from §3 to §1.
* Closure ledger
  `/app/memory/TRACK_14_0_UXS_11_PLATFORM_ROUTE_PARITY_CERTIFICATION_CLOSURE.md`
  marked CLOSED with full evidence package.
* Five-Pillar Trusted ≥ 9.95, Proven ≥ 9.95.

## Why this cadence is the right path

* Wrapping 49 pages in one PR risks breaking working pages.
* The wrap pattern is mechanical but each page has unique body JSX
  that needs careful editing.
* Screenshots are essential — the user has explicitly stated
  "screenshots are evidence" — without them the certification is
  unfaithful.
* The regression guard pattern is parametrized so each sweep adds
  ~10 minutes of test work, not 10 minutes per page.

## What NOT to do in the next session

* Do not attempt all 4 sweeps in one session. Pick the highest-
  priority sweep, deliver fully, ask for the next sweep.
* Do not skip screenshots to save time. The user has explicitly
  rejected certification-by-assumption.
* Do not fake-certify pages that weren't actually wrapped.
* Do not move pages from §3 (operational drift) to §1 (fixed)
  without a screenshot + regression test entry.

— end handoff —
