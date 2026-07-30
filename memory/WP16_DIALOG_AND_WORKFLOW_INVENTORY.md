# WP16 Dialog & Workflow Inventory

Date: 2026-07-30

This inventory supplements the page/screen certification register. It lists major dialogs, drawers, sheets, and primary write workflows discovered in the active frontend codebase before any new Phase B page repairs begin.

## Major dialog / drawer / sheet inventory

- Dialog-bearing source files discovered: **56**

| Inventory ID | Component(s) | Source file |
| --- | --- | --- |
| WP16-DLG-001 | CreateUserDialog | `frontend/src/components/AdminAccessControlPanel.jsx` |
| WP16-DLG-002 | ComposeDialog | `frontend/src/components/AdminBannersPanel.jsx` |
| WP16-DLG-003 | AttendeeBulkAddDialog | `frontend/src/components/AttendeeBulkAddDialog.jsx` |
| WP16-DLG-004 | BannerAuditDialog | `frontend/src/components/BannerAuditDialog.jsx` |
| WP16-DLG-005 | CheatSheet | `frontend/src/components/CheatSheetCard.jsx` |
| WP16-DLG-006 | CompanyInfoDialog | `frontend/src/components/CompanyInfoDialog.jsx` |
| WP16-DLG-007 | EditProjectDialog | `frontend/src/components/EditProjectDialog.jsx` |
| WP16-DLG-008 | EmailReportDialog | `frontend/src/components/EmailReportDialog.jsx` |
| WP16-DLG-009 | AuditDrawer | `frontend/src/components/EmailRoutingV2Panel.jsx` |
| WP16-DLG-010 | RepairDrawer, RtsDrawer | `frontend/src/components/FleetRepairDrawer.jsx` |
| WP16-DLG-011 | HelpDrawer | `frontend/src/components/HelpDrawer.jsx` |
| WP16-DLG-012 | MissingDrawer | `frontend/src/components/HrCompletenessTile.jsx` |
| WP16-DLG-013 | SafetyFireExtManageDialog | `frontend/src/components/SafetyFireExtManageDialog.jsx` |
| WP16-DLG-014 | ShareFormDialog | `frontend/src/components/ShareFormDialog.jsx` |
| WP16-DLG-015 | PickerDialog | `frontend/src/components/admin/MappingCleanupTab.jsx` |
| WP16-DLG-016 | EvidenceDrawer | `frontend/src/components/admin/trust/TrustPrimitives.jsx` |
| WP16-DLG-017 | AddAssetDialog | `frontend/src/components/asset/AddAssetDialog.jsx` |
| WP16-DLG-018 | UploadDialog | `frontend/src/components/asset/AssetDocumentsTab.jsx` |
| WP16-DLG-019 | AssignmentCreateDrawer | `frontend/src/components/dispatch/AssignmentCreateDrawer.jsx` |
| WP16-DLG-020 | AssignmentDrawer | `frontend/src/components/dispatch/AssignmentDrawer.jsx` |
| WP16-DLG-021 | WhyDrawer | `frontend/src/components/dispatch/DispatchDecisionChip.jsx` |
| WP16-DLG-022 | OverrideRequiredModal | `frontend/src/components/dispatch/TransportationGate.jsx` |
| WP16-DLG-023 | IamUserDetailDrawer | `frontend/src/components/iam/IamUserDetailDrawer.jsx` |
| WP16-DLG-024 | AssetCardSheet | `frontend/src/components/operations-map/AssetCardSheet.jsx` |
| WP16-DLG-025 | AssignmentHistoryDrawer | `frontend/src/components/team/AssignmentHistoryDrawer.jsx` |
| WP16-DLG-026 | RemoveReasonDialog | `frontend/src/components/team/RemoveReasonDialog.jsx` |
| WP16-DLG-027 | AlertDialog | `frontend/src/components/ui/alert-dialog.jsx` |
| WP16-DLG-028 | CommandDialog | `frontend/src/components/ui/command.jsx` |
| WP16-DLG-029 | ReviewModal | `frontend/src/pages/AdminLegacyImports.jsx` |
| WP16-DLG-030 | CreateTransferDialog, TransferDetailDrawer | `frontend/src/pages/AssetTransfers.jsx` |
| WP16-DLG-031 | CheatSheet | `frontend/src/pages/CheatSheet.jsx` |
| WP16-DLG-032 | AddDialog | `frontend/src/pages/DocumentExpirations.jsx` |
| WP16-DLG-033 | EmailCardDialog | `frontend/src/pages/FieldSafetyCards.jsx` |
| WP16-DLG-034 | AddDialog, EmployeeDrawer | `frontend/src/pages/HrEmployees.jsx` |
| WP16-DLG-035 | HrFlDetailDrawer | `frontend/src/pages/HrFieldLeadership.jsx` |
| WP16-DLG-036 | PublicLinkDialog, ReviewDialog | `frontend/src/pages/HrTimeOff.jsx` |
| WP16-DLG-037 | EmailDialog | `frontend/src/pages/JobPhotosLibrary.jsx` |
| WP16-DLG-038 | DetailDrawer | `frontend/src/pages/PmFieldLeadership.jsx` |
| WP16-DLG-039 | AddDialog, PoDrawer | `frontend/src/pages/PoRequests.jsx` |
| WP16-DLG-040 | TaskDrawer | `frontend/src/pages/Tasks.jsx` |
| WP16-DLG-041 | DrilldownModal | `frontend/src/pages/admin/AdminCommandCenter.jsx` |
| WP16-DLG-042 | CreateHoldDialog, CreateTransferDialog | `frontend/src/pages/admin/AdminDispatch.jsx` |
| WP16-DLG-043 | EditDialog, PreviewDialog, UploadDialog | `frontend/src/pages/admin/AdminPromoAssets.jsx` |
| WP16-DLG-044 | MintedTokenModal | `frontend/src/pages/admin/PreviewValidationIdentities.jsx` |
| WP16-DLG-045 | AffectedDrawer | `frontend/src/pages/transportation/_intelligence.jsx` |
| WP16-DLG-046 | FleetBulkAdoptionModal, FleetOverlayEditModal | `frontend/src/pages/transportation/_lists.jsx` |
| WP16-DLG-047 | AddCarrierModal, AddLeasedDriverModal, EditCarrierModal, LinkHRDriverModal | `frontend/src/pages/transportation/_modals.jsx` |
| WP16-DLG-048 | RateCreateDialog | `frontend/src/pages/transportation/_widgets.jsx` |
| WP16-DLG-049 | ReviewDialog | `frontend/src/pages/trench_safety/ExcavationOversight.jsx` |
| WP16-DLG-050 | PublicReportModal | `frontend/src/pages/trench_safety/PublicReportModal.jsx` |
| WP16-DLG-051 | ClearHoldDialog, CreateAssetDialog, CreateInspectionDialog, EditAssetDialog, OpenHoldDialog, RetireAssetDialog, StatusChangeDialog, UploadCertificationDialog | `frontend/src/pages/trench_safety/TrenchSafetyActions.jsx` |
| WP16-DLG-052 | AssignToProjectDialog, ReturnFromProjectDialog | `frontend/src/pages/trench_safety/TrenchSafetyAssignDialogs.jsx` |
| WP16-DLG-053 | PhotoUploadDialog, VerifyRepairDialog | `frontend/src/pages/trench_safety/TrenchSafetyOpsCenter.jsx` |
| WP16-DLG-054 | CSVImportDialog, QuickAddAssetDialog | `frontend/src/pages/trench_safety/TrenchSafetyPolish.jsx` |
| WP16-DLG-055 | PulseHistoryDialog, PulseViewerDialog | `frontend/src/pages/trench_safety/TrenchSafetyPulse.jsx` |
| WP16-DLG-056 | SubscriptionManagerDialog | `frontend/src/pages/trench_safety/TrenchSafetyReportDistribution.jsx` |

## Primary workflow inventory

- Page/workflow files with mutating API calls discovered: **83**

| Workflow ID | Source file | Likely route(s) | Mutating endpoints discovered |
| --- | --- | --- | --- |
| WP16-WF-001 | `frontend/src/pages/AdminLeadershipEquipment.jsx` | /admin/leadership-equipment | PATCH /field-leadership/admin/equipment-catalog/${editing.id}; POST /field-leadership/admin/equipment-catalog; PATCH /field-leadership/admin/equipment-catalog/${item.id}; PATCH /field-leadership/admin/equipment-makes/${editingMake.id}; POST /field-leadership/admin/equipment-makes; PATCH /field-leadership/admin/equipment-makes/${m.id} |
| WP16-WF-002 | `frontend/src/pages/AdminLegacyImports.jsx` | /admin/legacy-imports | POST /legacy-imports/upload; POST /legacy-imports/${importId}/approve; POST /legacy-imports/${importId}/reject; POST /legacy-imports/${importId}/retry-ocr |
| WP16-WF-003 | `frontend/src/pages/AdminLogin.jsx` | /admin/login | POST /auth/multi-login |
| WP16-WF-004 | `frontend/src/pages/AdminTrainingVideos.jsx` | /admin/training-videos | PUT /admin/training/videos |
| WP16-WF-005 | `frontend/src/pages/AssetTransfers.jsx` | /asset-transfers | POST /asset-transfers; POST /asset-transfers/${id}/${action} |
| WP16-WF-006 | `frontend/src/pages/DailyReportsDashboard.jsx` | /daily-reports, /admin/daily, /pm/daily | DELETE /daily-reports/${id} |
| WP16-WF-007 | `frontend/src/pages/Dashboard.jsx` | /admin/inspections, /pm/inspections, /safety-portal/inspections | DELETE /inspections/${id} |
| WP16-WF-008 | `frontend/src/pages/DevHub.jsx` | /dev | POST /dev/ops-manual/snapshot; DELETE /dev/ops-manual/snapshots/${id} |
| WP16-WF-009 | `frontend/src/pages/DevLogin.jsx` | /dev/login | POST /dev/login |
| WP16-WF-010 | `frontend/src/pages/DirectoryChangePassword.jsx` | /change-password | POST /auth/change-master-password |
| WP16-WF-011 | `frontend/src/pages/EquipmentDashboard.jsx` | /admin/equipment-inspections, /pm/equipment, /shop/equipment | DELETE /equipment-inspections/${id} |
| WP16-WF-012 | `frontend/src/pages/ExecutiveOperationalIntelligence.jsx` | /admin/executive-operational-intelligence | POST /oppc/enterprise/monday-briefing/${path} |
| WP16-WF-013 | `frontend/src/pages/FieldLeadershipFormPage.jsx` | /leadership/:kind/new | POST /field-leadership/employees |
| WP16-WF-014 | `frontend/src/pages/FieldLeadershipPortalChangePassword.jsx` | /field-leadership/portal/change-password | POST /field-leadership/portal/change-password |
| WP16-WF-015 | `frontend/src/pages/FieldLeadershipPortalLogin.jsx` | /field-leadership/portal/login, /leadership/login | POST /field-leadership/portal/forgot-password; POST /field-leadership/portal/login |
| WP16-WF-016 | `frontend/src/pages/FieldLeadershipRecords.jsx` | /leadership/records, /admin/leadership/records | DELETE /field-leadership/${id} |
| WP16-WF-017 | `frontend/src/pages/HrChangePassword.jsx` | /hr/change-password | POST /hr/change-password |
| WP16-WF-018 | `frontend/src/pages/HrDriverQualificationImport.jsx` | /hr/driver-qualification/import | POST /hr/driver-qualification/import/preview; POST /hr/driver-qualification/import/apply |
| WP16-WF-019 | `frontend/src/pages/HrLogin.jsx` | /hr/login | POST /hr/forgot-password; POST /hr/login |
| WP16-WF-020 | `frontend/src/pages/HrPayrollVariance.jsx` | /hr/payroll-variance | POST /hr/payroll-variance/upload; POST /hr/payroll-variance/${batch.id}/decision |
| WP16-WF-021 | `frontend/src/pages/HrResetPassword.jsx` | /hr/reset/:token | POST /hr/reset/${token} |
| WP16-WF-022 | `frontend/src/pages/IncidentsDashboard.jsx` | /admin/incidents, /pm/incidents | DELETE /incidents/${id} |
| WP16-WF-023 | `frontend/src/pages/JhaPlansAdmin.jsx` | /admin/jha-plans, /pm/jha-plans, /safety-portal/jha-plans | POST /job-hazard-files; DELETE /job-hazard-files/${file.id} |
| WP16-WF-024 | `frontend/src/pages/JobPhotosLibrary.jsx` | /admin/photos, /pm/photos | POST /job-photos/zip; POST /job-photos/email; POST /job-photos/admin/reindex |
| WP16-WF-025 | `frontend/src/pages/MaterialCalculators.jsx` | /field/calculators | POST /calculators/save |
| WP16-WF-026 | `frontend/src/pages/MeetingsDashboard.jsx` | /admin/meetings, /pm/meetings, /safety-portal/meetings | DELETE /meetings/${id} |
| WP16-WF-027 | `frontend/src/pages/NewDailyReport.jsx` | Nested / unbound / helper surface | POST /daily-reports |
| WP16-WF-028 | `frontend/src/pages/NewDailyReportV3.jsx` | /daily/submit | POST /daily-reports |
| WP16-WF-029 | `frontend/src/pages/NewEquipmentInspection.jsx` | /equipment/new, /equipment/submit | POST /equipment-inspections |
| WP16-WF-030 | `frontend/src/pages/NewInspection.jsx` | /safety/inspections/new | POST /inspections |
| WP16-WF-031 | `frontend/src/pages/NewMeeting.jsx` | /meetings/new, /meetings/submit | POST /meetings |
| WP16-WF-032 | `frontend/src/pages/NewQaqcInspection.jsx` | /qaqc/:slug/new | POST /qaqc-inspections |
| WP16-WF-033 | `frontend/src/pages/NewSafetyEquipmentIssuance.jsx` | /safety/forms/equipment-issuance/new | POST /safety-forms/equipment-issuances |
| WP16-WF-034 | `frontend/src/pages/NewSafetyEquipmentTraining.jsx` | /safety/forms/equipment-training/new | POST /safety-forms/equipment-trainings |
| WP16-WF-035 | `frontend/src/pages/PmChangePassword.jsx` | /pm/change-password | POST /pm/change-password |
| WP16-WF-036 | `frontend/src/pages/PmLogin.jsx` | /pm/login | POST /pm/forgot-password; POST /pm/login |
| WP16-WF-037 | `frontend/src/pages/PmMondayReviewWorkspace.jsx` | /pm/monday-review | POST /oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/start; PUT /oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/meta; PUT /oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/activities/${encodeURIComponent(code)}; POST /oppc/projects/${encodeURIComponent(projectNumber)}/monday-review/complete; PUT /oppc/projects/${encodeURIComponent(projectNumber)}/variances/${encodeURIComponent(varianceKey)}; POST /oppc/projects/${encodeURIComponent(projectNumber)}/monday-briefing/${path} |
| WP16-WF-038 | `frontend/src/pages/PmProjectSchedule.jsx` | /pm/project-schedule | PUT /cost-codes/projects/${encodeURIComponent(projectNumber)}/schedule; POST /cost-codes/projects/${encodeURIComponent(projectNumber)}/planning-lifecycle/publish; POST /cost-codes/projects/${encodeURIComponent(projectNumber)}/weekly-rollover/apply; POST /cost-codes/projects/${encodeURIComponent(projectNumber)}/forecast/snapshots; PUT /cost-codes/projects/${encodeURIComponent(projectNumber)}/forecast/overrides/${encodeURIComponent(overrideDraft.cost_code)} |
| WP16-WF-039 | `frontend/src/pages/PmResetPassword.jsx` | /pm/reset/:token | POST /pm/reset-password |
| WP16-WF-040 | `frontend/src/pages/ReturnEquipment.jsx` | /safety/forms/equipment-issuance/:id/return | POST /safety-forms/equipment-issuances/${id}/return |
| WP16-WF-041 | `frontend/src/pages/SafetyFormsLogin.jsx` | /safety/forms/login | POST /safety-forms/login |
| WP16-WF-042 | `frontend/src/pages/ShopChangePassword.jsx` | /shop/change-password | POST /shop/change-password |
| WP16-WF-043 | `frontend/src/pages/ShopLogin.jsx` | /shop/login | POST /shop/forgot-password; POST /shop/login |
| WP16-WF-044 | `frontend/src/pages/ShopResetPassword.jsx` | /shop/reset/:token | POST /shop/reset-password |
| WP16-WF-045 | `frontend/src/pages/SignIn.jsx` | /sign-in | POST /auth/multi-login; POST /auth/mfa/verify-login |
| WP16-WF-046 | `frontend/src/pages/TrenchBoxesAdmin.jsx` | /admin/trench-boxes, /pm/trench-boxes | PUT /trench-boxes/${editingId}; POST /trench-boxes; DELETE /trench-boxes/${b.id} |
| WP16-WF-047 | `frontend/src/pages/ViewDailyReport.jsx` | /admin/daily/:id, /pm/daily/:id, /hr/daily-reports/:id | DELETE /daily-reports/${id} |
| WP16-WF-048 | `frontend/src/pages/ViewEquipmentInspection.jsx` | /admin/equipment/:id, /pm/equipment/:id, /shop/equipment/:id | DELETE /equipment-inspections/${id} |
| WP16-WF-049 | `frontend/src/pages/ViewIncident.jsx` | /admin/incidents/:id, /pm/incidents/:id, /safety-portal/incidents/:id | DELETE /incidents/${id} |
| WP16-WF-050 | `frontend/src/pages/ViewInspection.jsx` | /admin/inspections/:id, /pm/inspections/:id, /safety-portal/inspections/:id | DELETE /inspections/${id} |
| WP16-WF-051 | `frontend/src/pages/ViewMeeting.jsx` | /admin/meetings/:id, /pm/meetings/:id, /safety-portal/meetings/:id | DELETE /meetings/${id} |
| WP16-WF-052 | `frontend/src/pages/ViewQaqcInspection.jsx` | /qaqc/:id, /admin/qaqc/:id | DELETE /qaqc-inspections/${id} |
| WP16-WF-053 | `frontend/src/pages/admin/AdminAIConfiguration.jsx` | /admin/ai-configuration | PUT /admin/ai/tenants/${encodeURIComponent(activeTenant)}/capabilities |
| WP16-WF-054 | `frontend/src/pages/admin/AdminAssetAdmin.jsx` | /admin/asset-admin | PATCH /asset-spine/assets/${item.id}; POST /asset-spine/taxonomy/apply-legacy-crosswalk?dry_run=true&limit=2000; POST /asset-spine/taxonomy/apply-legacy-crosswalk?dry_run=false&limit=2000 |
| WP16-WF-055 | `frontend/src/pages/admin/AdminAssetMapping.jsx` | /admin/asset-mapping | POST /admin/asset-mapping/scan; POST /admin/asset-mapping/${id}/approve; POST /admin/asset-mapping/${id}/reject; POST /admin/asset-mapping/bulk-approve |
| WP16-WF-056 | `frontend/src/pages/admin/AdminAssetSpineHealth.jsx` | /admin/asset-spine | POST /asset-spine/health/scan |
| WP16-WF-057 | `frontend/src/pages/admin/AdminComplianceFindings.jsx` | /admin/compliance-findings | POST /admin/compliance/findings/${finding.id}/${mode} |
| WP16-WF-058 | `frontend/src/pages/admin/AdminCostRegistry.jsx` | /admin/cost-registry | POST /cost-codes/registry |
| WP16-WF-059 | `frontend/src/pages/admin/AdminDigestConfig.jsx` | /admin/digest-config | PATCH /admin/digest-settings; POST /admin/digest-settings/send-now |
| WP16-WF-060 | `frontend/src/pages/admin/AdminDispatch.jsx` | /admin/dispatch | POST /operations/transfers/${xid}/decide; POST /operations/transfers; POST /operations/holds/${hid}/release; POST /operations/holds/${hid}/approve; POST /operations/holds/${hid}/dismiss; POST /operations/holds |
| WP16-WF-061 | `frontend/src/pages/admin/AdminGeofenceReconciliation.jsx` | /admin/geofence-reconciliation | POST /admin/locations/import-geofences; POST /admin/locations/reconcile; POST /api/admin/locations/${id}/approve; POST /admin/locations/${id}/reject; POST /admin/locations/${reassignFor}/reassign; POST /admin/locations/bulk-approve |
| WP16-WF-062 | `frontend/src/pages/admin/AdminGovernance.jsx` | /admin/governance/legacy-health | POST /admin/compliance/scan; POST /admin/compliance/backfill-employee-links |
| WP16-WF-063 | `frontend/src/pages/admin/AdminIntegrationCenter.jsx` | /admin/integrations | POST /admin/integrations/${p.provider}/test; PATCH /admin/integrations/${provider}; PATCH ${listUrl}/${dlg.id}; DELETE ${listUrl}/${m.id}; POST /admin/integrations/error-logs/${r.id}/resolve; POST /admin/integrations/import-csv; POST /admin/integrations/mappings/wizard/preview; POST /admin/integrations/mappings/wizard/commit |
| WP16-WF-064 | `frontend/src/pages/admin/AdminMfa.jsx` | /admin/mfa | POST /admin/mfa/enroll/start; POST /admin/mfa/enroll/verify; POST /admin/mfa/disable; POST /admin/mfa/regenerate-recovery |
| WP16-WF-065 | `frontend/src/pages/admin/AdminOperationalIntelligence.jsx` | /admin/operational-intelligence | POST /operational-intelligence/${p.product_id}/dispatch |
| WP16-WF-066 | `frontend/src/pages/admin/AdminOperationalIntelligenceRecipients.jsx` | /admin/operational-intelligence/recipients | POST /operational-intelligence/recipients/bulk-import; POST /operational-intelligence/groups; POST /operational-intelligence/groups/${group.group_id}/members; POST /operational-intelligence/recipients; PATCH /operational-intelligence/recipients/${editing.id}; DELETE /operational-intelligence/recipients/${r.id}; PATCH /operational-intelligence/recipients/${r.id} |
| WP16-WF-067 | `frontend/src/pages/admin/AdminOperationsDashboard.jsx` | /admin/operations-dashboard | POST /admin/operational-events/materialize |
| WP16-WF-068 | `frontend/src/pages/admin/AdminPromoAssets.jsx` | /admin/promo-assets | POST /admin/promo-assets; DELETE /admin/promo-assets/${asset.id}; PATCH /admin/promo-assets/${asset.id} |
| WP16-WF-069 | `frontend/src/pages/admin/AssetProfile.jsx` | /admin/assets/:assetId | PATCH /asset-spine/assets/${assetId} |
| WP16-WF-070 | `frontend/src/pages/admin/PreviewValidationIdentities.jsx` | /admin/preview-validation-identities | POST /admin/preview-validation-identities/mint; POST /admin/preview-validation-identities/${id}/revoke |
| WP16-WF-071 | `frontend/src/pages/transportation/ExternalCarrierInvite.jsx` | /transport-invite/:token | POST /transportation/invite/${token}/submit |
| WP16-WF-072 | `frontend/src/pages/transportation/_command_queue.jsx` | Nested / unbound / helper surface | PATCH /admin/transportation/automation/actions/${aid} |
| WP16-WF-073 | `frontend/src/pages/transportation/_intelligence.jsx` | Nested / unbound / helper surface | POST /admin/transportation/intelligence/cleanup-signals/${openSignal}/materialize-actions?days=30 |
| WP16-WF-074 | `frontend/src/pages/transportation/_orientation.jsx` | Nested / unbound / helper surface | PATCH /admin/transportation/orientation/modules/${mid}/placeholder; POST /admin/transportation/orientation/modules/${mid}/questions; PATCH /admin/transportation/email-routes/${routeKey} |
| WP16-WF-075 | `frontend/src/pages/transportation/_widgets.jsx` | Nested / unbound / helper surface | POST /admin/transportation/rate-schedules; POST /admin/transportation/rate-schedules/${result.id}/activate; POST /admin/transportation/trucks/${truckId}/inspections; PATCH /admin/transportation/inspections/${inspection.id}; POST /admin/transportation/inspections/${inspection.id}/complete; POST /admin/transportation/carriers/${carrierId}/packet; PATCH /admin/transportation/packets/${p.id} |
| WP16-WF-076 | `frontend/src/pages/trench_safety/ExcavationOversight.jsx` | /safety/trench-safety/excavations, /admin/trench-safety/excavations, /pm/trench-safety/excavations | POST /trench-safety/excavations/${rec.id}/review; POST /trench-safety/excavations/${rec.id}/reinspection-trigger; POST /trench-safety/excavations/${rec.id}/translate-notes; POST /trench-safety/excavations/${rec.id}/rated-depth-acknowledge |
| WP16-WF-077 | `frontend/src/pages/trench_safety/PublicExcavationForm.jsx` | /trench-safety/excavation/new | POST /trench-safety/excavations/public/submit; POST /trench-safety/excavations/${done.id}/public/reinspection-request |
| WP16-WF-078 | `frontend/src/pages/trench_safety/TrenchSafetyActions.jsx` | Nested / unbound / helper surface | POST /trench-safety/assets; PUT /trench-safety/assets/${asset.asset_id}; POST /trench-safety/assets/${asset.asset_id}/retire; POST /trench-safety/assets/${asset.asset_id}/status; POST /trench-safety/assets/${asset.asset_id}/holds; POST /trench-safety/assets/${assetId}/holds/${hold.id}/clear; POST /trench-safety/assets/${asset.asset_id}/inspections; POST /trench-safety/assets/${asset.asset_id}/certifications |
| WP16-WF-079 | `frontend/src/pages/trench_safety/TrenchSafetyAssignDialogs.jsx` | Nested / unbound / helper surface | POST /trench-safety/assets/${encodeURIComponent(asset.asset_id)}/assign; POST /trench-safety/assets/${encodeURIComponent(asset.asset_id)}/return |
| WP16-WF-080 | `frontend/src/pages/trench_safety/TrenchSafetyOpsCenter.jsx` | Nested / unbound / helper surface | POST /trench-safety/repairs/${repair.id}/verify; PATCH /trench-safety/repairs/${r.id}; POST /trench-safety/assets/${asset.asset_id}/qr-label/audit; POST /trench-safety/assets/${asset.asset_id}/photos; DELETE /trench-safety/photos/${p.id} |
| WP16-WF-081 | `frontend/src/pages/trench_safety/TrenchSafetyPolish.jsx` | Nested / unbound / helper surface | POST /trench-safety/assets; POST /trench-safety/assets/import/preview; POST /trench-safety/assets/import |
| WP16-WF-082 | `frontend/src/pages/trench_safety/TrenchSafetyPulse.jsx` | Nested / unbound / helper surface | POST /trench-safety/pulse/generate?send=${send ? ; POST /trench-safety/pulse/generate?send=false |
| WP16-WF-083 | `frontend/src/pages/trench_safety/TrenchSafetyReportDistribution.jsx` | Nested / unbound / helper surface | POST /trench-safety/reports/subscriptions; PUT /trench-safety/reports/subscriptions/${sub.id}; POST /trench-safety/reports/subscriptions/${sub.id}/run; DELETE /trench-safety/reports/subscriptions/${sub.id}; POST /trench-safety/reports/subscriptions/install-road-plate-package; POST /trench-safety/reports/digest/generate?send=false; POST /trench-safety/reports/digest/generate?send=true |