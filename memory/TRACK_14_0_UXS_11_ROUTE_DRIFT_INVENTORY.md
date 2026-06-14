# Track 14.0-UXS-11 · Platform Route Drift Inventory

**Generated**: 2026-02-14 · `grep -rln "from \"@/components/MasciLogo\"|from \"@/components/HubBackLink\"" /app/frontend/src/pages/`

The grep returned **103 pages** still referencing the legacy chrome
imports. They fall into the following categories:

## 1 · ✅ FIXED THIS TRACK (5 pages, regression-locked)

These are the routes the user explicitly evidenced or called out, now
wrapped in PortalShell with the correct domain sidebar:

| Route                   | Component               | Portal sidebar      | Status |
|-------------------------|-------------------------|---------------------|--------|
| `/project-health`       | `ProjectHealth.jsx`     | `PmSideNavV2`       | ✅ Fixed |
| `/asset-transfers`      | `AssetTransfers.jsx`    | `PmSideNavV2`       | ✅ Fixed |
| `/admin/jha-plans`      | `JhaPlansAdmin.jsx`     | `SafetySideNavV2`   | ✅ Fixed |
| `/admin/trench-boxes`   | `TrenchBoxesAdmin.jsx`  | `AdminSideNavV2`    | ✅ Fixed |
| `/po-requests`          | `PoRequests.jsx`        | `PmSideNavV2`       | ✅ Fixed |

Locked by `test_route_parity_uxs11.py` — 10 parametrized assertions.

## 2 · 🟡 LEGITIMATE EXCEPTIONS — keep as-is (intentional)

These pages SHOULD NOT be wrapped in PortalShell. They are
authentication, public-form, or print-specific surfaces that must
stay sidebar-less by design.

### Auth / login / reset / change-password (24 pages)
* `SignIn.jsx`, `AdminLogin.jsx`, `PmLogin.jsx`, `HrLogin.jsx`,
  `SafetyLogin.jsx`, `ShopLogin.jsx`, `DispatchLogin.jsx`,
  `LeadershipLogin.jsx`, `FieldLeadershipPortalLogin.jsx`,
  `SafetyFormsLogin.jsx`
* `*ChangePassword.jsx` (Pm/Hr/Safety/Shop/Dispatch/FieldLeadership)
* `*ResetPassword.jsx` (Pm/Hr/Safety/Shop/Dispatch)
* `*ForgotPassword.jsx` (Safety/Dispatch)
* `AccessDenied.jsx`, `NotFound.jsx`, `ThankYou.jsx`
* `PublicTimeOff.jsx`

**Rationale**: directive explicitly excludes auth/public/error surfaces
from PortalShell — "Do not add authenticated portal sidebars to public
forms / auth screens".

### Print views (8 pages)
* `ViewIncident.jsx`, `ViewInspection.jsx`, `ViewDailyReport.jsx`,
  `ViewMeeting.jsx`, `ViewQaqcInspection.jsx`,
  `ViewEquipmentInspection.jsx`, `ViewSafetyForm.jsx`,
  `FieldLeadershipView.jsx`

**Rationale**: these are paired with `printReport()` and `no-print`
CSS so browser Save-as-PDF produces a clean record (audited in
Track 14.0-P1 PDF Lockup Sweep). Adding PortalShell would break the
PDF output — sidebar would print into the saved PDF.

### Print posters (3 pages)
* `AllPostersPrint.jsx`, `TrainingQrPoster.jsx`, `FieldSafetyCards.jsx`

**Rationale**: same as above — print-only surfaces.

### Public submission forms (8 pages)
* `NewDailyReport.jsx`, `NewIncident.jsx`, `NewInspection.jsx`,
  `NewMeeting.jsx`, `NewEquipmentInspection.jsx`, `NewFleetDVIR.jsx`,
  `NewQaqcInspection.jsx`, `NewSafetyEquipmentIssuance.jsx`,
  `NewSafetyEquipmentTraining.jsx`, `ReturnEquipment.jsx`,
  `FieldLeadershipFormPage.jsx`, `TrenchBoxes.jsx`,
  `FleetDVIRConfirmation.jsx`, `TrainingPacketDownload.jsx`

**Rationale**: tap-first public/field submission forms. Adding
PortalShell would clutter the small-screen / one-handed submission
flow.

## 3 · 🟠 REMAINING DRIFTED OPERATIONAL PAGES (~33 pages, follow-on sweep)

These are real operational dashboards / detail pages that SHOULD be
wrapped in PortalShell as a follow-on sweep. Listed in priority order
(highest user-facing traffic first):

### PM Portal
1. `DailyReportsDashboard.jsx`
2. `IncidentsDashboard.jsx`
3. `MeetingsDashboard.jsx`
4. `JobPhotosLibrary.jsx`
5. `DocumentExpirations.jsx`
6. `ProjectPnlPage.jsx`
7. `PmQaqcList.jsx`
8. `Tasks.jsx`
9. `Hub.jsx`

### HR Portal
10. `HrHub.jsx` (legacy — superseded by `HrHubV2.jsx` but still in routes)
11. `HrEmployees.jsx`
12. `HrFieldLeadershipUsers.jsx`
13. `HrDailyReports.jsx`
14. `HrIncidents.jsx`
15. `HrTimeOff.jsx`
16. `HrEmployeeAccountabilityTimeline.jsx`
17. `HrDriverProfile.jsx`
18. `HrMotiveDrivers.jsx`

### Safety Portal
19. `SafetyFormsHub.jsx`
20. `SafetyDriverProfile.jsx`
21. `SafetySection.jsx`
22. `JhaPlansHub.jsx`
23. `QaqcSection.jsx`

### Shop Portal
24. `ShopHub.jsx` (legacy — superseded by `ShopHubV2.jsx` but still routed)
25. `EquipmentDashboard.jsx`
26. `FleetVisibility.jsx`

### Dispatch Portal
27. `DispatchCommandCenter.jsx`
28. `DispatchDriverProfile.jsx`
29. `DispatchDriverQualification.jsx`

### Field Leadership
30. `FieldLeadershipHub.jsx`
31. `FieldLeadershipPortalDashboard.jsx`
32. `FieldLeadershipDriverQualification.jsx`
33. `FieldSection.jsx`

### Admin
34. `AdminGuide.jsx`
35. `AdminQaqcList.jsx`
36. `AdminTerminations.jsx`
37. `AdminTrainingVideos.jsx`
38. `AdminLeadershipEquipment.jsx`
39. `OperationsCenterCommand.jsx`
40. `Dashboard.jsx`
41. `MaterialCalculators.jsx`
42. `OpsTrainingCenter.jsx`
43. `OpsTrainingGuide.jsx`
44. `TrainingHub.jsx`
45. `TrainingTrack.jsx`
46. `guidance/OperationalGuidanceCenter.jsx`
47. `operations_actions/OperationsActions.jsx`
48. `operations_actions/OperationsActionNew.jsx`
49. `operations_actions/OperationsActionDetail.jsx`

## 4 · Recommended follow-on sweep cadence

Wrapping 49 pages in one PR risks breaking working pages. Recommended
cadence:

1. **Sweep A** — PM Portal (9 pages) — ~1 hour focused work · 1 PR.
2. **Sweep B** — HR Portal (9 pages) — ~1 hour · 1 PR.
3. **Sweep C** — Safety + Shop + Dispatch + FL (15 pages) — ~1.5 hours · 1 PR.
4. **Sweep D** — Admin (16 pages) — ~1.5 hours · 1 PR.

Each sweep:
* Wrap each page in PortalShell with the correct sidebar.
* Take live preview screenshot of each (or at least the highest-
  traffic 3-5 per sweep).
* Extend `test_route_parity_uxs11.py` with the new pages.
* Update this inventory ledger as pages move from §3 to §1.

This is the responsible path. Avoid the temptation of a single
49-page "rewrap everything" PR.

## 5 · How to verify a page is fixed

For each fixed page, the regression guard
`test_route_parity_uxs11.py` enforces:

1. Imports `PortalShell` from `@/design-system`.
2. Imports the correct domain sidebar (PmSideNavV2 / HrSideNavV2 /
   SafetySideNavV2 / AdminSideNavV2 / DispatchSideNavV2).
3. Opens `<PortalShell` JSX with `portalRole` matching the expected
   portal label.
4. Passes `sideNav={…}` prop.
5. Does NOT import `MasciLogo` or `HubBackLink` (which would
   duplicate PortalShell's brand bar).

Add each new fix to that parametrized test as you go.
