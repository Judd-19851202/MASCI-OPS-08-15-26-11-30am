# AUTHORITY MISMATCH REPORT

_Phase GOVERNANCE-INFRA-1 · Workstream 1 · Authority Mismatch Probe._

* Generated: 2026-06-16 10:50:31 UTC
* Scan duration: 283 ms
* Frontend tree: `/app/frontend/src`
* Baseline: `/app/scripts/authority_pattern_baseline.json`

## Summary

* **New violations** (fail the gate): **0**
* **New warnings** (review): 38
* **Baselined** (previously approved): 33

## 🟡 New warnings

* `lib/constraintCapabilities.js:48` · ad-hoc canApprove variable · `const hasHr = isHr();`
* `lib/constraintCapabilities.js:49` · ad-hoc canApprove variable · `const hasAdmin = isAdmin();`
* `components/HubBackLink.jsx:23` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `components/HubBackLink.jsx:44` · ad-hoc canApprove variable · `if (isAdmin()) return "/admin";`
* `pages/PmLogin.jsx:57` · token-coexistence rendering · 2-way OR · `if (isPm() || isAdmin()) {`
* `pages/PmLogin.jsx:65` · token-coexistence rendering · 2-way OR · `useRedirectIfDirectoryGrant("pm", isPm() || isAdmin(), "/pm");`
* `pages/PmLogin.jsx:57` · ad-hoc canApprove variable · `if (isPm() || isAdmin()) {`
* `pages/PmLogin.jsx:65` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("pm", isPm() || isAdmin(), "/pm");`
* `pages/ReturnEquipment.jsx:52` · ad-hoc canApprove variable · `const authed = isSafety() || isSafetyForms() || isAdmin();`
* `pages/HrEmployees.jsx:82` · token-coexistence rendering · 2-way OR · `const allowed = isHr() || isAdmin();`
* `pages/HrEmployees.jsx:82` · ad-hoc canApprove variable · `const allowed = isHr() || isAdmin();`
* `pages/HrEmployees.jsx:82` · ad-hoc canApprove variable · `const allowed = isHr() || isAdmin();`
* `pages/NewIncident.jsx:313` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewIncident.jsx:346` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/ViewEquipmentInspection.jsx:146` · ad-hoc canApprove variable · `{isAdmin() && (`
* `pages/HrLogin.jsx:63` · token-coexistence rendering · 2-way OR · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:69` · token-coexistence rendering · 2-way OR · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/HrLogin.jsx:63` · ad-hoc canApprove variable · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:63` · ad-hoc canApprove variable · `if (isHr() || isAdmin()) {`
* `pages/HrLogin.jsx:69` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/HrLogin.jsx:69` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("hr", isHr() || isAdmin(), "/hr");`
* `pages/SafetyFormsHub.jsx:58` · ad-hoc canApprove variable · `if (!isSafety() && !isAdmin() && !isSafetyForms()) {`
* `pages/ViewQaqcInspection.jsx:73` · ad-hoc canApprove variable · `label={isAdmin() ? "Admin · QA/QC" : "QA/QC"}`
* `pages/ViewQaqcInspection.jsx:80` · ad-hoc canApprove variable · `{isAdmin() && (`
* `pages/FieldLeadershipRecords.jsx:35` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/ShopLogin.jsx:47` · ad-hoc canApprove variable · `useRedirectIfDirectoryGrant("shop", isShop() || isAdmin(), "/shop");`
* `pages/NewMeeting.jsx:306` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/FieldLeadershipView.jsx:32` · ad-hoc canApprove variable · `if (!getLeadershipToken() && !isAdmin() && !getPmToken()) {`
* `pages/FieldLeadershipView.jsx:112` · ad-hoc canApprove variable · `to={isAdmin() ? "/admin" : getPmToken() ? "/pm" : "/leadership"}`
* `pages/FieldLeadershipView.jsx:117` · ad-hoc canApprove variable · `{isAdmin() ? t("Admin Console") : getPmToken() ? t("PM Hub") : t("Field Leadersh`
* `pages/NewDailyReport.jsx:846` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewDailyReport.jsx:895` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewInspection.jsx:238` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewInspection.jsx:257` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/DocumentExpirations.jsx:71` · ad-hoc canApprove variable · `const admin = isAdmin();`
* `pages/NewEquipmentInspection.jsx:527` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/TrainingHub.jsx:49` · ad-hoc canApprove variable · `if (isAdmin()) return true;`
* `pages/TrainingHub.jsx:53` · ad-hoc canApprove variable · `if (track.audience === "hr") return isHr();`

## ⚪ Baselined (already reviewed)

* `lib/tokenValidation.js:4` · ad-hoc canApprove variable
* `components/BackLink.jsx:31` · ad-hoc canApprove variable
* `components/BackLink.jsx:33` · ad-hoc canApprove variable
* `components/ComplianceExportPanel.jsx:315` · ad-hoc canApprove variable
* `components/ComplianceExportPanel.jsx:359` · ad-hoc canApprove variable
* `components/RequireShop.jsx:24` · ad-hoc canApprove variable
* `components/RequireAdmin.jsx:23` · ad-hoc canApprove variable
* `components/RequireHr.jsx:24` · ad-hoc canApprove variable
* `components/RequirePm.jsx:26` · token-coexistence rendering · 2-way OR
* `components/RequirePm.jsx:26` · ad-hoc canApprove variable
* `components/ShopSignoffCard.jsx:34` · ad-hoc canApprove variable
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
* `pages/FieldLeadershipPortalLogin.jsx:65` · ad-hoc canApprove variable
* `pages/FieldLeadershipPortalLogin.jsx:108` · ad-hoc canApprove variable
* `pages/ViewSafetyForm.jsx:48` · ad-hoc canApprove variable
* `pages/TrainingQrPoster.jsx:48` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · token-coexistence rendering · 2-way OR
* `pages/TrainingTrack.jsx:86` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:88` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:89` · ad-hoc canApprove variable
* `pages/NewSafetyEquipmentTraining.jsx:54` · ad-hoc canApprove variable
* `pages/NewSafetyEquipmentIssuance.jsx:73` · ad-hoc canApprove variable
* `pages/FieldLeadershipFormPage.jsx:309` · ad-hoc canApprove variable
