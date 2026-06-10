# AUTHORITY MISMATCH REPORT

_Phase GOVERNANCE-INFRA-1 · Workstream 1 · Authority Mismatch Probe._

* Generated: 2026-06-09 23:59:15 UTC
* Scan duration: 107 ms
* Frontend tree: `/app/frontend/src`
* Baseline: `/app/scripts/authority_pattern_baseline.json`

## Summary

* **New violations** (fail the gate): **0**
* **New warnings** (review): 8
* **Baselined** (previously approved): 52

## 🟡 New warnings

* `lib/constraintCapabilities.js:48` · ad-hoc canApprove variable · `const hasHr = isHr();`
* `lib/constraintCapabilities.js:49` · ad-hoc canApprove variable · `const hasAdmin = isAdmin();`
* `pages/NewIncident.jsx:313` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewIncident.jsx:335` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/ViewQaqcInspection.jsx:73` · ad-hoc canApprove variable · `label={isAdmin() ? "Admin · QA/QC" : "QA/QC"}`
* `pages/ViewQaqcInspection.jsx:80` · ad-hoc canApprove variable · `{isAdmin() && (`
* `pages/NewDailyReport.jsx:846` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`
* `pages/NewDailyReport.jsx:882` · ad-hoc canApprove variable · `if (publicMode || !isAdmin()) {`

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
* `components/HubBackLink.jsx:19` · ad-hoc canApprove variable
* `components/HubBackLink.jsx:36` · ad-hoc canApprove variable
* `components/ShopSignoffCard.jsx:34` · ad-hoc canApprove variable
* `components/RequireAdminPmOrSafety.jsx:30` · token-coexistence rendering · 2-way OR
* `components/RequireAdminPmOrSafety.jsx:30` · ad-hoc canApprove variable
* `components/RequireAdminOrPm.jsx:22` · ad-hoc canApprove variable
* `components/CompanyInfoDialog.jsx:37` · ad-hoc canApprove variable
* `components/CompanyInfoDialog.jsx:50` · ad-hoc canApprove variable
* `pages/ReturnEquipment.jsx:51` · ad-hoc canApprove variable
* `pages/HrEmployees.jsx:78` · token-coexistence rendering · 2-way OR
* `pages/HrEmployees.jsx:78` · ad-hoc canApprove variable
* `pages/HrEmployees.jsx:78` · ad-hoc canApprove variable
* `pages/HrEmployeeAccountabilityTimeline.jsx:114` · ad-hoc canApprove variable
* `pages/HrEmployeeAccountabilityTimeline.jsx:114` · ad-hoc canApprove variable
* `pages/ViewEquipmentInspection.jsx:145` · ad-hoc canApprove variable
* `pages/SafetyFormsHub.jsx:62` · ad-hoc canApprove variable
* `pages/ViewQaqcInspection.jsx:72` · ad-hoc canApprove variable
* `pages/TrainingPacketDownload.jsx:41` · ad-hoc canApprove variable
* `pages/FieldLeadershipRecords.jsx:36` · ad-hoc canApprove variable
* `pages/FieldLeadershipPortalLogin.jsx:18` · ad-hoc canApprove variable
* `pages/FieldLeadershipPortalLogin.jsx:65` · ad-hoc canApprove variable
* `pages/FieldLeadershipPortalLogin.jsx:108` · ad-hoc canApprove variable
* `pages/ViewSafetyForm.jsx:48` · ad-hoc canApprove variable
* `pages/TrainingQrPoster.jsx:48` · ad-hoc canApprove variable
* `pages/NewMeeting.jsx:260` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · token-coexistence rendering · 2-way OR
* `pages/TrainingTrack.jsx:86` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:87` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:88` · ad-hoc canApprove variable
* `pages/TrainingTrack.jsx:89` · ad-hoc canApprove variable
* `pages/FieldLeadershipView.jsx:31` · ad-hoc canApprove variable
* `pages/FieldLeadershipView.jsx:111` · ad-hoc canApprove variable
* `pages/FieldLeadershipView.jsx:116` · ad-hoc canApprove variable
* `pages/NewInspection.jsx:231` · ad-hoc canApprove variable
* `pages/NewInspection.jsx:250` · ad-hoc canApprove variable
* `pages/DocumentExpirations.jsx:70` · ad-hoc canApprove variable
* `pages/NewSafetyEquipmentTraining.jsx:54` · ad-hoc canApprove variable
* `pages/NewSafetyEquipmentIssuance.jsx:73` · ad-hoc canApprove variable
* `pages/NewEquipmentInspection.jsx:469` · ad-hoc canApprove variable
* `pages/FieldLeadershipFormPage.jsx:309` · ad-hoc canApprove variable
* `pages/TrainingHub.jsx:50` · ad-hoc canApprove variable
* `pages/TrainingHub.jsx:54` · ad-hoc canApprove variable
