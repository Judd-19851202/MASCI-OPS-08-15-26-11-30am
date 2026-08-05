# AUTHORITY MISMATCH REPORT

_Phase GOVERNANCE-INFRA-1 · Workstream 1 · Authority Mismatch Probe._

* Generated: 2026-08-05 02:39:43 UTC
* Scan duration: 204 ms
* Frontend tree: `/app/frontend/src`
* Baseline: `/app/scripts/authority_pattern_baseline.json`

## Summary

* **New violations** (fail the gate): **0**
* **New warnings** (review): 62
* **Baselined** (previously approved): 15

## 🟡 New warnings

* `lib/constraintCapabilities.js:48` · ad-hoc canApprove variable · `const hasHr = isHr();`
* `lib/constraintCapabilities.js:49` · ad-hoc canApprove variable · `const hasAdmin = isAdmin();`
* `components/BackLink.jsx:32` · ad-hoc canApprove variable · `if (isAdmin()) return { to: "/admin", label: "Administration" };`
* `components/BackLink.jsx:34` · ad-hoc canApprove variable · `if (isHr()) return { to: "/hr", label: "Human Resources" };`
* `components/RequireTransportationPortal.jsx:32` · ad-hoc canApprove variable · `if (isAdmin() || isDispatch()) return true;`
* `components/ComplianceExportPanel.jsx:316` · ad-hoc canApprove variable · `{!hideBackupTools && isAdmin() && (`
* `components/ComplianceExportPanel.jsx:360` · ad-hoc canApprove variable · `{!hideBackupTools && isAdmin() && (`
* `components/RequireAdmin.jsx:24` · ad-hoc canApprove variable · `const hasToken = isAdmin();`
* `components/RequireHr.jsx:31` · ad-hoc canApprove variable · `const hasToken = isHr();`
* `components/HubBackLink.jsx:23` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `components/HubBackLink.jsx:44` · ad-hoc canApprove variable · `if (isAdmin()) return "/admin";`
* `components/ShopSignoffCard.jsx:36` · ad-hoc canApprove variable · `const canSignOff = isShop() || isAdmin();`
* `components/RequireAdminOrPm.jsx:25` · ad-hoc canApprove variable · `const hasAdminToken = isAdmin();`
* `components/transportation/TransportationOpsTopBar.jsx:72` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/PmLogin.jsx:59` · token-coexistence rendering · 2-way OR · `if (isPm() || isAdmin()) {`
* `pages/PmLogin.jsx:67` · token-coexistence rendering · 2-way OR · `useRedirectIfDirectoryGrant("pm", isPm() || isAdmin(), "/pm");`
* `pages/PmLogin.jsx:59` · ad-hoc canApprove variable · `if (isPm() || isAdmin()) {`
* `pages/PmLogin.jsx:67` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("pm", isPm() || isAdmin(), "/pm");`
* `pages/ReturnEquipment.jsx:50` · ad-hoc canApprove variable · `const authed = isSafety() || isSafetyForms() || isAdmin();`
* `pages/HrEmployees.jsx:88` · token-coexistence rendering · 2-way OR · `const allowed = isHr() || isAdmin();`
* `pages/HrEmployees.jsx:88` · ad-hoc canApprove variable · `const allowed = isHr() || isAdmin();`
* `pages/HrEmployees.jsx:88` · ad-hoc canApprove variable · `const allowed = isHr() || isAdmin();`
* `pages/NewIncident.jsx:322` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewIncident.jsx:355` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/AdminAssetThread.jsx:507` · ad-hoc canApprove variable · `const allowed = isAdmin();`
* `pages/ViewEquipmentInspection.jsx:157` · ad-hoc canApprove variable · `{isAdmin() && (`
* `pages/HrLogin.jsx:65` · token-coexistence rendering · 2-way OR · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:71` · token-coexistence rendering · 2-way OR · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/HrLogin.jsx:65` · ad-hoc canApprove variable · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:65` · ad-hoc canApprove variable · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:71` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/HrLogin.jsx:71` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/AdminVendorThread.jsx:250` · ad-hoc canApprove variable · `const allowed = isAdmin();`
* `pages/SafetyFormsHub.jsx:58` · ad-hoc canApprove variable · `if (!isSafety() && !isAdmin() && !isSafetyForms()) {`
* `pages/ViewQaqcInspection.jsx:190` · ad-hoc canApprove variable · `{isAdmin() ? (`
* `pages/HrEmployeeThread.jsx:206` · ad-hoc canApprove variable · `const allowed = isHr() || isSafety() || isAdmin();`
* `pages/HrEmployeeThread.jsx:206` · ad-hoc canApprove variable · `const allowed = isHr() || isSafety() || isAdmin();`
* `pages/HrEmployeeThread.jsx:223` · ad-hoc canApprove variable · `if (!isHr()) {`
* `pages/FieldLeadershipRecords.jsx:37` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/ShopLogin.jsx:58` · ad-hoc canApprove variable · `isShop() || isAdmin(),`
* `pages/FieldLeadershipPortalLogin.jsx:67` · ad-hoc canApprove variable · `setAdminAware(isAdmin());`
* `pages/FieldLeadershipPortalLogin.jsx:111` · ad-hoc canApprove variable · `// token (the Hub gate accepts admin via isAdmin()). Do NOT mint`
* `pages/PmProjectThread.jsx:330` · token-coexistence rendering · 2-way OR · `const allowed = isPm() || isAdmin();`
* `pages/PmProjectThread.jsx:330` · ad-hoc canApprove variable · `const allowed = isPm() || isAdmin();`
* `pages/ViewSafetyForm.jsx:135` · ad-hoc canApprove variable · `const authed = isSafety() || isSafetyForms() || isAdmin();`
* `pages/NewMeeting.jsx:365` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/FieldLeadershipView.jsx:94` · ad-hoc canApprove variable · `if (!getFlToken() && !isAdmin() && !getPmToken()) {`
* `pages/NewInspection.jsx:237` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewInspection.jsx:256` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/DocumentExpirations.jsx:71` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/SafetyIncidentThread.jsx:281` · ad-hoc canApprove variable · `const allowed = isSafety() || isAdmin();`
* `pages/NewSafetyEquipmentTraining.jsx:51` · ad-hoc canApprove variable · `const authed = isSafety() || isAdmin() || isSafetyForms();`
* `pages/NewSafetyEquipmentIssuance.jsx:70` · ad-hoc canApprove variable · `const authed = isSafety() || isAdmin() || isSafetyForms();`
* `pages/NewEquipmentInspection.jsx:614` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/FieldLeadershipFormPage.jsx:310` · ad-hoc canApprove variable · `if (!getFlToken() && !isAdmin() && !getPmToken()) {`
* `pages/TrainingHub.jsx:49` · ad-hoc canApprove variable · `if (isAdmin()) return true;`
* `pages/TrainingHub.jsx:53` · ad-hoc canApprove variable · `if (track.audience === "hr") return isHr();`
* `pages/transportation/_shared.jsx:429` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/transportation/TransportationApp.jsx:55` · ad-hoc canApprove variable · `const showAdminSideNav = isAdmin();`
* `pages/transportation/_command_queue.jsx:35` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/transportation/_orientation.jsx:67` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/transportation/_intelligence.jsx:65` · ad-hoc canApprove variable · `const admin = isAdmin();`

## ⚪ Baselined (already reviewed)

* `lib/tokenValidation.js:4` · ad-hoc canApprove variable
* `components/RequireAdminPmOrSafety.jsx:30` · token-coexistence rendering · 2-way OR
* `components/RequireAdminPmOrSafety.jsx:30` · ad-hoc canApprove variable
* `components/CompanyInfoDialog.jsx:37` · ad-hoc canApprove variable
* `components/CompanyInfoDialog.jsx:50` · ad-hoc canApprove variable
* `pages/HrEmployeeAccountabilityTimeline.jsx:114` · ad-hoc canApprove variable
* `pages/HrEmployeeAccountabilityTimeline.jsx:114` · ad-hoc canApprove variable
* `pages/TrainingPacketDownload.jsx:41` · ad-hoc canApprove variable
* `pages/FieldLeadershipPortalLogin.jsx:18` · ad-hoc canApprove variable
* `pages/TrainingQrPoster.jsx:48` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · token-coexistence rendering · 2-way OR
* `pages/TrainingTrack.jsx:86` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:88` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:89` · ad-hoc canApprove variable
