# AUTHORITY MISMATCH REPORT

_Phase GOVERNANCE-INFRA-1 · Workstream 1 · Authority Mismatch Probe._

* Generated: 2026-07-17 01:54:32 UTC
* Scan duration: 276 ms
* Frontend tree: `/app/frontend/src`
* Baseline: `/app/scripts/authority_pattern_baseline.json`

## Summary

* **New violations** (fail the gate): **0**
* **New warnings** (review): 60
* **Baselined** (previously approved): 22

## 🟡 New warnings

* `lib/constraintCapabilities.js:48` · ad-hoc canApprove variable · `const hasHr = isHr();`
* `lib/constraintCapabilities.js:49` · ad-hoc canApprove variable · `const hasAdmin = isAdmin();`
* `components/RequireTransportationPortal.jsx:32` · ad-hoc canApprove variable · `if (isAdmin() || isDispatch()) return true;`
* `components/ComplianceExportPanel.jsx:314` · ad-hoc canApprove variable · `{!hideBackupTools && isAdmin() && (`
* `components/ComplianceExportPanel.jsx:358` · ad-hoc canApprove variable · `{!hideBackupTools && isAdmin() && (`
* `components/RequireShop.jsx:25` · ad-hoc canApprove variable · `const hasToken = isShop() || isAdmin();`
* `components/RequireAdmin.jsx:24` · ad-hoc canApprove variable · `const hasToken = isAdmin();`
* `components/RequireHr.jsx:31` · ad-hoc canApprove variable · `const hasToken = isHr();`
* `components/RequirePm.jsx:27` · token-coexistence rendering · 2-way OR · `const hasToken = isPm() || isAdmin();`
* `components/RequirePm.jsx:27` · ad-hoc canApprove variable · `const hasToken = isPm() || isAdmin();`
* `components/HubBackLink.jsx:23` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `components/HubBackLink.jsx:44` · ad-hoc canApprove variable · `if (isAdmin()) return "/admin";`
* `components/ShopSignoffCard.jsx:36` · ad-hoc canApprove variable · `const canSignOff = isShop() || isAdmin();`
* `components/transportation/TransportationOpsTopBar.jsx:71` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/PmLogin.jsx:59` · token-coexistence rendering · 2-way OR · `if (isPm() || isAdmin()) {`
* `pages/PmLogin.jsx:67` · token-coexistence rendering · 2-way OR · `useRedirectIfDirectoryGrant("pm", isPm() || isAdmin(), "/pm");`
* `pages/PmLogin.jsx:59` · ad-hoc canApprove variable · `if (isPm() || isAdmin()) {`
* `pages/PmLogin.jsx:67` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("pm", isPm() || isAdmin(), "/pm");`
* `pages/ReturnEquipment.jsx:52` · ad-hoc canApprove variable · `const authed = isSafety() || isSafetyForms() || isAdmin();`
* `pages/HrEmployees.jsx:87` · token-coexistence rendering · 2-way OR · `const allowed = isHr() || isAdmin();`
* `pages/HrEmployees.jsx:87` · ad-hoc canApprove variable · `const allowed = isHr() || isAdmin();`
* `pages/HrEmployees.jsx:87` · ad-hoc canApprove variable · `const allowed = isHr() || isAdmin();`
* `pages/NewIncident.jsx:324` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewIncident.jsx:357` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/AdminAssetThread.jsx:508` · ad-hoc canApprove variable · `const allowed = isAdmin();`
* `pages/ViewEquipmentInspection.jsx:146` · ad-hoc canApprove variable · `{isAdmin() && (`
* `pages/HrLogin.jsx:65` · token-coexistence rendering · 2-way OR · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:71` · token-coexistence rendering · 2-way OR · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/HrLogin.jsx:65` · ad-hoc canApprove variable · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:65` · ad-hoc canApprove variable · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:71` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/HrLogin.jsx:71` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/AdminVendorThread.jsx:250` · ad-hoc canApprove variable · `const allowed = isAdmin();`
* `pages/SafetyFormsHub.jsx:58` · ad-hoc canApprove variable · `if (!isSafety() && !isAdmin() && !isSafetyForms()) {`
* `pages/ViewQaqcInspection.jsx:73` · ad-hoc canApprove variable · `label={isAdmin() ? "Admin · QA/QC" : "QA/QC"}`
* `pages/ViewQaqcInspection.jsx:80` · ad-hoc canApprove variable · `{isAdmin() && (`
* `pages/HrEmployeeThread.jsx:209` · ad-hoc canApprove variable · `const allowed = isHr() || isSafety() || isAdmin();`
* `pages/HrEmployeeThread.jsx:209` · ad-hoc canApprove variable · `const allowed = isHr() || isSafety() || isAdmin();`
* `pages/FieldLeadershipRecords.jsx:35` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/ShopLogin.jsx:58` · ad-hoc canApprove variable · `isShop() || isAdmin(),`
* `pages/FieldLeadershipPortalLogin.jsx:67` · ad-hoc canApprove variable · `setAdminAware(isAdmin());`
* `pages/FieldLeadershipPortalLogin.jsx:110` · ad-hoc canApprove variable · `// token (the Hub gate accepts admin via isAdmin()). Do NOT mint`
* `pages/PmProjectThread.jsx:329` · token-coexistence rendering · 2-way OR · `const allowed = isPm() || isAdmin();`
* `pages/PmProjectThread.jsx:329` · ad-hoc canApprove variable · `const allowed = isPm() || isAdmin();`
* `pages/ViewSafetyForm.jsx:50` · ad-hoc canApprove variable · `const authed = isSafety() || isSafetyForms() || isAdmin();`
* `pages/NewMeeting.jsx:366` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/FieldLeadershipView.jsx:32` · ad-hoc canApprove variable · `if (!getLeadershipToken() && !isAdmin() && !getPmToken()) {`
* `pages/FieldLeadershipView.jsx:112` · ad-hoc canApprove variable · `to={isAdmin() ? "/admin" : getPmToken() ? "/pm" : "/leadership"}`
* `pages/FieldLeadershipView.jsx:117` · ad-hoc canApprove variable · `{isAdmin() ? t("Administration") : getPmToken() ? t("Project Management") : t("F`
* `pages/NewInspection.jsx:238` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewInspection.jsx:257` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/DocumentExpirations.jsx:71` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/SafetyIncidentThread.jsx:281` · ad-hoc canApprove variable · `const allowed = isSafety() || isAdmin();`
* `pages/NewEquipmentInspection.jsx:608` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/TrainingHub.jsx:49` · ad-hoc canApprove variable · `if (isAdmin()) return true;`
* `pages/TrainingHub.jsx:53` · ad-hoc canApprove variable · `if (track.audience === "hr") return isHr();`
* `pages/transportation/_shared.jsx:389` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/transportation/TransportationApp.jsx:46` · ad-hoc canApprove variable · `const showAdminSideNav = isAdmin();`
* `pages/transportation/_command_queue.jsx:35` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/transportation/_orientation.jsx:67` · ad-hoc canApprove variable · `const admin = isAdmin();`

## ⚪ Baselined (already reviewed)

* `lib/tokenValidation.js:4` · ad-hoc canApprove variable
* `components/BackLink.jsx:31` · ad-hoc canApprove variable
* `components/BackLink.jsx:33` · ad-hoc canApprove variable
* `components/RequireAdminPmOrSafety.jsx:30` · token-coexistence rendering · 2-way OR
* `components/RequireAdminPmOrSafety.jsx:30` · ad-hoc canApprove variable
* `components/RequireAdminOrPm.jsx:22` · ad-hoc canApprove variable
* `components/CompanyInfoDialog.jsx:37` · ad-hoc canApprove variable
* `components/CompanyInfoDialog.jsx:50` · ad-hoc canApprove variable
* `pages/HrEmployeeAccountabilityTimeline.jsx:114` · ad-hoc canApprove variable
* `pages/HrEmployeeAccountabilityTimeline.jsx:114` · ad-hoc canApprove variable
* `pages/ViewQaqcInspection.jsx:72` · ad-hoc canApprove variable
* `pages/TrainingPacketDownload.jsx:41` · ad-hoc canApprove variable
* `pages/FieldLeadershipPortalLogin.jsx:18` · ad-hoc canApprove variable
* `pages/TrainingQrPoster.jsx:48` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · token-coexistence rendering · 2-way OR
* `pages/TrainingTrack.jsx:86` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:88` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:89` · ad-hoc canApprove variable
* `pages/NewSafetyEquipmentTraining.jsx:54` · ad-hoc canApprove variable
* `pages/NewSafetyEquipmentIssuance.jsx:73` · ad-hoc canApprove variable
* `pages/FieldLeadershipFormPage.jsx:309` · ad-hoc canApprove variable
