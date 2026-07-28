import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
// AuthProvider removed 2026-04-28 — Crew Hub scrapped.
import Hub from "@/pages/Hub";
// DR-UNIFY-001 · internal-only Daily Report shell (pilot opt-in · not user-facing).
// DR-UNIFY-003: `DailyReportV2` shell import retired. The `/daily-report/v2` route now redirects to `/daily/submit`. The component file remains on disk for legacy tests but is no longer imported by the router.
import PmOperationalIntelligence from "@/pages/PmOperationalIntelligence";
// DR-UNIFY-002 · `/admin/ods-intelligence` + `/executive/ods-intelligence` now redirect
// to the canonical Admin OI surface — no separate imports required.
// Track 15.67 Phase 3 · tenant-safe branding context for the whole app.
import { BrandingProvider } from "@/lib/BrandingProvider";
// Track 13.5A · Phase B1 — Internal design-system showcase (lazy, isolated).
const DesignSystemDemo = React.lazy(() => import("@/pages/DesignSystemDemo"));
// Track 13.5A · Phase B2 — Internal PM Portal V2 preview lane (lazy, mock data only).
const PmV2Preview = React.lazy(() => import("@/pages/PmV2Preview"));
// Track 13.6A · Operational Recovery Phase 1 — Internal HR Portal V2 preview lane (lazy, mock data only).
const HrV2Preview = React.lazy(() => import("@/pages/HrV2Preview"));
// Track 13.6B · Operational Surface Conversion — Operator review hub + side-by-side comparison.
const V2Index = React.lazy(() => import("@/pages/V2Index"));
const V2Compare = React.lazy(() => import("@/pages/V2Compare"));
// ROUTE-SPLIT-001 Wave 3 — ODR + Operational Records + Operations Actions lazy.
const OdrNew = React.lazy(() => import("@/pages/odr/OdrNew"));
const OdrCenter = React.lazy(() => import("@/pages/odr/OdrCenter"));
const OdrPmPanel = React.lazy(() => import("@/pages/odr/OdrPmPanel"));
const OdrPublicViewer = React.lazy(() => import("@/pages/odr/OdrPublicViewer"));
const OdrDone = React.lazy(() => import("@/pages/odr/OdrDone"));
const OdrDetail = React.lazy(() => import("@/pages/odr/OdrDetail"));
const OperationalRecords = React.lazy(() => import("@/pages/operational_records/OperationalRecords"));
const OperationsActions = React.lazy(() => import("@/pages/operations_actions/OperationsActions"));
const OperationsActionNew = React.lazy(() => import("@/pages/operations_actions/OperationsActionNew"));
const OperationsActionDetail = React.lazy(() => import("@/pages/operations_actions/OperationsActionDetail"));
// ROUTE-SPLIT-001 Wave 4 — Driver mobile lazy.
const DriverMagicLanding = React.lazy(() => import("@/pages/driver/DriverMagicLanding"));
const DriverShift = React.lazy(() => import("@/pages/driver/DriverShift"));
// Track 13.6L — DriverHubV2 retired (existing /shift + /d/:token + /driver already satisfy ≤ 2 taps / ≤ 30 s).
// TRACK 13.6K — Admin / Leadership Hub V2 COMPANIONS (no swap). FL Hub V2 retired in 13.6L.
// TRACK 25 · SPRINT 1 — AdminHub / AdminHubV2 / AdminHubSwitcher imports removed:
// the /admin route now mounts AdminOS.jsx directly. The legacy files remain
// on disk but auto-redirect to /admin if any residual link ever loads them.
// TRACK 25.02 · Phase D · V3 hub renders behind masci.admin.nav.v3 flag
// TRACK 25 · SPRINT 1 · Canonical Admin Operating System landing (10 domains).
const AdminOS = React.lazy(() => import("@/pages/admin/AdminOS"));
// TRACK 25 · SPRINT 3 · Storage & Recovery domain landing.
const AdminStorageRecovery = React.lazy(() => import("@/pages/admin/AdminStorageRecovery"));
// TRACK 25 · SPRINT 4 · Four more domain landings — AI Ops, Communications, Identity, Governance.
const AdminAiOperations = React.lazy(() => import("@/pages/admin/AdminAiOperations"));
const AdminCommunications = React.lazy(() => import("@/pages/admin/AdminCommunications"));
const AdminIdentitySecurity = React.lazy(() => import("@/pages/admin/AdminIdentitySecurity"));
const AdminGovernanceTrust = React.lazy(() => import("@/pages/admin/AdminGovernanceTrust"));
// TRACK 25 · SPRINT 5/6 · Configuration, Diagnostics, Maintenance, Platform Overview redirect.
const AdminPlatformConfiguration = React.lazy(() => import("@/pages/admin/AdminPlatformConfiguration"));
const AdminDiagnostics = React.lazy(() => import("@/pages/admin/AdminDiagnostics"));
const AdminMaintenance = React.lazy(() => import("@/pages/admin/AdminMaintenance"));
const AdminPlatformOverview = React.lazy(() => import("@/pages/admin/AdminPlatformOverview"));
const AdminMaterialLedgerQuality = React.lazy(() => import("@/pages/AdminMaterialLedgerQuality"));
const LeadershipHubV2 = React.lazy(() => import("@/pages/LeadershipHubV2"));
const ExecutiveOverview = React.lazy(() => import("@/pages/ExecutiveOverview"));
const ShiftStart = React.lazy(() => import("@/pages/driver/ShiftStart"));
import SafetySection from "@/pages/SafetySection";
import SafetyFormsLogin from "@/pages/SafetyFormsLogin";
import SafetyFormsHub from "@/pages/SafetyFormsHub";
import NewSafetyEquipmentIssuance from "@/pages/NewSafetyEquipmentIssuance";
import NewSafetyEquipmentTraining from "@/pages/NewSafetyEquipmentTraining";
import ViewSafetyForm from "@/pages/ViewSafetyForm";
import ReturnEquipment from "@/pages/ReturnEquipment";
import FieldSafetyCards from "@/pages/FieldSafetyCards";
import FieldSection from "@/pages/FieldSection";
import MaterialCalculators from "@/pages/MaterialCalculators";
import QaqcSection from "@/pages/QaqcSection";
import NewQaqcInspection from "@/pages/NewQaqcInspection";
import ViewQaqcInspection from "@/pages/ViewQaqcInspection";
import AdminQaqcList from "@/pages/AdminQaqcList";
import AdminTransportation from "@/pages/AdminTransportation";
import ExternalCarrierInvite from "@/pages/transportation/ExternalCarrierInvite";
import CertificateVerify from "@/pages/transportation/CertificateVerify";
import Dashboard from "@/pages/Dashboard";
import Revise from "@/pages/Revise";
import NewInspection from "@/pages/NewInspection";
import ViewInspection from "@/pages/ViewInspection";
import ThankYou from "@/pages/ThankYou";
import MeetingsDashboard from "@/pages/MeetingsDashboard";
import NewMeeting from "@/pages/NewMeeting";
import ViewMeeting from "@/pages/ViewMeeting";
import JhaPlansHub from "@/pages/JhaPlansHub";
import JhaPlansAdmin from "@/pages/JhaPlansAdmin";
import TrenchBoxes from "@/pages/TrenchBoxes";
// ROUTE-SPLIT-001 Wave 3 — Trench Safety operational surfaces lazy.
const TrenchSafetyHub = React.lazy(() => import("@/pages/trench_safety/TrenchSafetyHub"));
const TrenchSafetyAssetsList = React.lazy(() => import("@/pages/trench_safety/TrenchSafetyAssetsList"));
const TrenchSafetyAssetDetail = React.lazy(() => import("@/pages/trench_safety/TrenchSafetyAssetDetail"));
const TrenchSafetyTabulatedData = React.lazy(() => import("@/pages/trench_safety/TrenchSafetyTabulatedData"));
const TrenchSafetyRepairReviewPage = React.lazy(() => import("@/pages/trench_safety/TrenchSafetyRepairReviewPage"));
const TrenchSafetyReports = React.lazy(() => import("@/pages/trench_safety/TrenchSafetyReports"));
import PublicExcavationForm from "@/pages/trench_safety/PublicExcavationForm";
const ExcavationOversight = React.lazy(() => import("@/pages/trench_safety/ExcavationOversight"));
const TrenchSafetyFieldReportsPage = React.lazy(() => import("@/pages/trench_safety/TrenchSafetyFieldReportsPage"));
import TrenchSafetyQrLanding from "@/pages/trench_safety/TrenchSafetyQrLanding";
import PublicTrenchSafetyDashboard from "@/pages/trench_safety/PublicTrenchSafetyDashboard";
import PublicTrenchSafetyTabulatedData from "@/pages/trench_safety/PublicTrenchSafetyTabulatedData";
import PublicTrenchSafetyReferences from "@/pages/trench_safety/PublicTrenchSafetyReferences";
import PublicTrenchSafetyReport from "@/pages/trench_safety/PublicTrenchSafetyReport";
import TrenchBoxesAdmin from "@/pages/TrenchBoxesAdmin";
import TrenchBoxPoster from "@/pages/TrenchBoxPoster";
import JhaPlansPoster from "@/pages/JhaPlansPoster";
import AllPostersPrint from "@/pages/AllPostersPrint";
import IncidentsDashboard from "@/pages/IncidentsDashboard";
// TRACK 19.16 · Closeout · retired NewIncident.jsx component. The file
// itself is retained on disk because several older lock tests
// (iter333/335/336) scan it as a cross-form pattern reference; removing
// it would break unrelated tests outside this closeout scope. The
// App.js import is removed because no <Route> or <Link> renders the
// component in production — historic URLs are <Navigate> redirects.
// import NewIncident from "@/pages/NewIncident"; // intentionally removed
import IncidentReport from "@/pages/IncidentReport";
import NearMissKiosk from "@/pages/NearMissKiosk";
import SafetyCaseWorkspace from "@/pages/SafetyCaseWorkspace";
// Track 19.58 · Incident Operational Thread PROMOTION — presentation
// layer over certified incident-case + safety_morning_digest endpoints.
import SafetyIncidentThread from "@/pages/SafetyIncidentThread";
import ExecutiveIntelligence from "@/pages/ExecutiveIntelligence";
import ExecutiveOperationalIntelligence from "@/pages/ExecutiveOperationalIntelligence";
import ExecutiveCaseReport from "@/pages/ExecutiveCaseReport";
import IncidentReportViewer from "@/pages/IncidentReportViewer";
import ViewIncident from "@/pages/ViewIncident";
import DailyReportsDashboard from "@/pages/DailyReportsDashboard";
import NewDailyReportV3 from "@/pages/NewDailyReportV3";
import ViewDailyReport from "@/pages/ViewDailyReport";
import EquipmentDashboard from "@/pages/EquipmentDashboard";
import NewEquipmentInspection from "@/pages/NewEquipmentInspection";
import NewFleetDVIR from "@/pages/NewFleetDVIR";
import FleetDVIRConfirmation from "@/pages/FleetDVIRConfirmation";
import FleetVisibility from "@/pages/FleetVisibility";
// Track 19.55 · Fleet Unit Operational Thread (pilot).
const FleetUnitThread = React.lazy(() => import("@/pages/fleet/FleetUnitThread"));
// TRACK 18.00 · Phase G · Transportation Operations branding on dispatch fleet.
import TransportationOpsTopBar from "@/components/transportation/TransportationOpsTopBar";
import ViewEquipmentInspection from "@/pages/ViewEquipmentInspection";
import AdminLogin from "@/pages/AdminLogin";
// TRACK 25 · SPRINT 1 — legacy AdminHub import removed; /admin now mounts AdminOS.
const AdminRecovery = React.lazy(() => import("@/pages/admin/AdminRecovery"));
const AdminRecoveryStream = React.lazy(() => import("@/pages/admin/AdminRecoveryStream"));
const AdminJhaAcknowledgements = React.lazy(() => import("@/pages/admin/AdminJhaAcknowledgements"));
const AdminCommandCenter = React.lazy(() => import("@/pages/admin/AdminCommandCenter"));
import AdminGuide from "@/pages/AdminGuide";
import AdminLeadershipEquipment from "@/pages/AdminLeadershipEquipment";
import AdminTerminations from "@/pages/AdminTerminations";
import ProjectPnlPage from "@/pages/ProjectPnlPage";
import PmLogin from "@/pages/PmLogin";
import PmChangePassword from "@/pages/PmChangePassword";
import PmResetPassword from "@/pages/PmResetPassword";
// ROUTE-SPLIT-001 Wave 4 — PM portal group lazy (PmSections named exports via wrapper).
const PmHub = React.lazy(() => import("@/pages/PmHub"));
const PmCrewCompliance = React.lazy(() => import("@/pages/PmCrewCompliance"));
const PmFieldLeadership = React.lazy(() => import("@/pages/PmFieldLeadership"));
const PmJobs = React.lazy(() => import("@/pages/pm/PmSections").then(m => ({ default: m.PmJobs })));
const PmFleet = React.lazy(() => import("@/pages/pm/PmSections").then(m => ({ default: m.PmFleet })));
const PmPeople = React.lazy(() => import("@/pages/pm/PmSections").then(m => ({ default: m.PmPeople })));
const PmSuppliers = React.lazy(() => import("@/pages/pm/PmSections").then(m => ({ default: m.PmSuppliers })));
// Track 19.60 · Vendor Operational Thread PROMOTION.
const AdminVendorThread = React.lazy(() => import("@/pages/AdminVendorThread"));
const AdminAssetThread  = React.lazy(() => import("@/pages/AdminAssetThread"));
const PmPosters = React.lazy(() => import("@/pages/pm/PmSections").then(m => ({ default: m.PmPosters })));
const PmQaqcList = React.lazy(() => import("@/pages/PmQaqcList"));
import ShopLogin from "@/pages/ShopLogin";
// ROUTE-SPLIT-001 Wave 4 — Shop portal group lazy.
const ShopHub = React.lazy(() => import("@/pages/ShopHub"));
const ShopTrenchSafetyRepairs = React.lazy(() => import("@/pages/shop/ShopTrenchSafetyRepairs"));
import ShopChangePassword from "@/pages/ShopChangePassword";
import ShopResetPassword from "@/pages/ShopResetPassword";
import HrLogin from "@/pages/HrLogin";
import SignIn from "@/pages/SignIn";
import DirectoryChangePassword from "@/pages/DirectoryChangePassword";
const AdminPeople = React.lazy(() => import("@/pages/admin/AdminPeople"));
const AdminMfa = React.lazy(() => import("@/pages/admin/AdminMfa"));
const AdminPromoAssets = React.lazy(() => import("@/pages/admin/AdminPromoAssets"));
const AdminJobs = React.lazy(() => import("@/pages/admin/AdminJobs"));
const AdminCostRegistry = React.lazy(() => import("@/pages/admin/AdminCostRegistry"));
const AdminJobTeam = React.lazy(() => import("@/pages/admin/AdminJobTeam"));
const PmJobTeam = React.lazy(() => import("@/pages/pm/PmJobTeam"));
// Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE — cross-project staffing.
const AdminProjectStaffing = React.lazy(() => import("@/pages/admin/AdminProjectStaffing"));
const PmProjectStaffing = React.lazy(() => import("@/pages/pm/PmProjectStaffing"));
const AdminGeofenceReconciliation = React.lazy(() => import("@/pages/admin/AdminGeofenceReconciliation"));
const AdminOperationsDashboard = React.lazy(() => import("@/pages/admin/AdminOperationsDashboard"));
// TRACK 24.17 · Operations Control Center — unified super-admin maintenance console.
const OperationsControlCenter = React.lazy(() => import("@/pages/OperationsControlCenter"));
const OperationsControlCasesRoute = React.lazy(() => import("@/pages/OperationsControlCasesRoute"));
const OperationsControlCaseDetail = React.lazy(() => import("@/pages/OperationsControlCaseDetail"));
const AdminAssetMapping = React.lazy(() => import("@/pages/admin/AdminAssetMapping"));
// FORGEDOPS-P0.1 · Asset Spine Health dashboard.
const AdminAssetSpineHealth = React.lazy(() => import("@/pages/admin/AdminAssetSpineHealth"));
const AdminEquipment = React.lazy(() => import("@/pages/admin/AdminEquipment"));
const AdminEmail = React.lazy(() => import("@/pages/admin/AdminEmail"));
const AdminTraining = React.lazy(() => import("@/pages/admin/AdminTraining"));
const AdminCompliance = React.lazy(() => import("@/pages/admin/AdminCompliance"));
const AdminSystem = React.lazy(() => import("@/pages/admin/AdminSystem"));
const AdminAIConfiguration = React.lazy(() => import("@/pages/admin/AdminAIConfiguration"));
const IntegrationTruth = React.lazy(() => import("@/pages/admin/IntegrationTruth"));
const PreviewValidationIdentities = React.lazy(() => import("@/pages/admin/PreviewValidationIdentities"));
const AdminDatabase = React.lazy(() => import("@/pages/admin/AdminDatabase"));
const AdminIntegrationCenter = React.lazy(() => import("@/pages/admin/AdminIntegrationCenter"));
const AssetProfile = React.lazy(() => import("@/pages/admin/AssetProfile"));
const AdminAssetAdmin = React.lazy(() => import("@/pages/admin/AdminAssetAdmin"));
const AdminDriverIntel = React.lazy(() => import("@/pages/admin/AdminDriverIntel"));
const AdminDispatch = React.lazy(() => import("@/pages/admin/AdminDispatch"));
const AdminDlsShiftQR = React.lazy(() => import("@/pages/admin/AdminDlsShiftQR"));
const AdminDlsDay1Debrief = React.lazy(() => import("@/pages/admin/AdminDlsDay1Debrief"));
const AdminProfile = React.lazy(() => import("@/pages/admin/AdminProfile"));
const AdminOperationsEvents = React.lazy(() => import("@/pages/admin/AdminOperationsEvents"));
const AdminDigestConfig = React.lazy(() => import("@/pages/admin/AdminDigestConfig"));
const AdminOperationalIntelligence = React.lazy(() => import("@/pages/admin/AdminOperationalIntelligence"));
const AdminOperationalIntelligenceRecipients = React.lazy(() => import("@/pages/admin/AdminOperationalIntelligenceRecipients"));
const SystemHealth = React.lazy(() => import("@/pages/admin/SystemHealth"));
const AdminAuditLog = React.lazy(() => import("@/pages/admin/AdminAuditLog"));
import AdminSchedulerRuns from "@/pages/AdminSchedulerRuns";  // iter445 · digest execution history
import AdminLegacyImports from "@/pages/AdminLegacyImports";
const AdminSessions = React.lazy(() => import("@/pages/admin/AdminSessions"));
const AdminGuidanceCoverage = React.lazy(() => import("@/pages/admin/AdminGuidanceCoverage"));
const AdminOperationalInventory = React.lazy(() => import("@/pages/admin/AdminOperationalInventory"));
const AdminGovernance = React.lazy(() => import("@/pages/admin/AdminGovernance"));
const AdminProjectIdentityGovernance = React.lazy(() => import("@/pages/admin/AdminProjectIdentityGovernance"));
const SelfProtection = React.lazy(() => import("@/pages/admin/SelfProtection"));
const AdminComplianceFindings = React.lazy(() => import("@/pages/admin/AdminComplianceFindings"));
const AdminOperationalLanguage = React.lazy(() => import("@/pages/admin/AdminOperationalLanguage"));
// ROUTE-SPLIT-001 Wave 4 — Notifications + Guidance lazy.
const NotificationsDigest = React.lazy(() => import("@/pages/NotificationsDigest"));
const OperationalGuidanceCenter = React.lazy(() => import("@/pages/guidance/OperationalGuidanceCenter"));
const DeployRecovery = React.lazy(() => import("@/pages/admin/DeployRecovery"));
const AdminMasterHistory = React.lazy(() => import("@/pages/admin/AdminMasterHistory"));
const AdminAnalytics = React.lazy(() => import("@/pages/admin/AdminAnalytics"));
// ROUTE-SPLIT-001 Wave 3 — HR portal pages lazy (excludes auth-adjacent + named-export pages).
const HrHub = React.lazy(() => import("@/pages/HrHub"));
// Track 13.6C · HR Hub V2 — first real portal migration (live data · same HR auth).
const HrHubV2 = React.lazy(() => import("@/pages/HrHubV2"));
// Track 13.6D · PM Hub V2 — second real portal migration (live data · same PM auth).
const PmHubV2 = React.lazy(() => import("@/pages/PmHubV2"));
// Track 13.6F · Phase 3 / 4 — PM-2 Unified Holds + PM-3 Due Today aggregators.
const PmHoldsV2 = React.lazy(() => import("@/pages/PmHoldsV2"));
const PmDueTodayV2 = React.lazy(() => import("@/pages/PmDueTodayV2"));
// Track 13.6G — Dispatch Recovery (preview, no route swap).
const DispatchHubV2 = React.lazy(() => import("@/pages/DispatchHubV2"));
// Track 13.6H · Phase 4 — Safety Recovery (preview, no route swap).
const SafetyHubV2 = React.lazy(() => import("@/pages/SafetyHubV2"));
// Track 13.6I · Phase 5 — Shop Recovery (preview, no route swap).
const ShopHubV2 = React.lazy(() => import("@/pages/ShopHubV2"));
const ShopAssetCare = React.lazy(() => import("@/pages/shop/ShopAssetCare"));
// Track 13.28 Phase 2 — Shop Workforce surfaces.
const ShopManagerQueue = React.lazy(() => import("@/pages/shop/ShopManagerQueue"));
const ShopMyAssignments = React.lazy(() => import("@/pages/shop/ShopMyAssignments"));
// Track 13.27 — Unit History Timeline (consumes Track 13.26 Asset Service Event Backbone).
const UnitHistoryLanding = React.lazy(() => import("@/pages/shop/UnitHistoryLanding"));
const UnitHistoryTimeline = React.lazy(() => import("@/pages/shop/UnitHistoryTimeline"));
// Track 13.29 — Fuel / Lube Visit Record.
const FuelLubeVisitForm = React.lazy(() => import("@/pages/shop/FuelLubeVisitForm"));
// Track 13.29 Phase 2 — Fuel / Lube Visit Records list + detail.
const FuelLubeVisitRecords = React.lazy(() => import("@/pages/shop/FuelLubeVisitRecords"));
const FuelLubeVisitDetail = React.lazy(() => import("@/pages/shop/FuelLubeVisitDetail"));
// Track 13.30 — Service Truck Daily Reconciliation.
const ServiceTruckReconciliationForm    = React.lazy(() => import("@/pages/shop/ServiceTruckReconciliationForm"));
const ServiceTruckReconciliationRecords = React.lazy(() => import("@/pages/shop/ServiceTruckReconciliationRecords"));
const ServiceTruckReconciliationDetail  = React.lazy(() => import("@/pages/shop/ServiceTruckReconciliationDetail"));
// Track 13.31 — PM Engine.
const PmDashboard   = React.lazy(() => import("@/pages/shop/PmDashboard"));
const PmTemplates   = React.lazy(() => import("@/pages/shop/PmTemplates"));
const PmSchedules   = React.lazy(() => import("@/pages/shop/PmSchedules"));
const PmWorkOrders  = React.lazy(() => import("@/pages/shop/PmWorkOrders"));
import HrChangePassword from "@/pages/HrChangePassword";
import FieldLeadershipPortalLogin from "@/pages/FieldLeadershipPortalLogin";
import FieldLeadershipPortalDashboard from "@/pages/FieldLeadershipPortalDashboard";
import FieldLeadershipDriverQualification from "@/pages/FieldLeadershipDriverQualification";
import FieldLeadershipPortalChangePassword from "@/pages/FieldLeadershipPortalChangePassword";
import { RequireFl } from "@/components/RequireFl";
import HrResetPassword from "@/pages/HrResetPassword";
import HrForgotPassword from "@/pages/HrForgotPassword";
const HrTimeVerification = React.lazy(() => import("@/pages/HrTimeVerification"));
const HrFieldLeadership = React.lazy(() => import("@/pages/HrFieldLeadership"));
const HrFieldLeadershipUsers = React.lazy(() => import("@/pages/HrFieldLeadershipUsers"));
const HrEmployeeAccountability = React.lazy(() => import("@/pages/HrEmployeeAccountability"));
const HrEmployeeAccountabilityTimeline = React.lazy(() => import("@/pages/HrEmployeeAccountabilityTimeline"));
// Track 19.56 · Employee Operational Thread PROMOTION.
const HrEmployeeThread = React.lazy(() => import("@/pages/HrEmployeeThread"));
const HrIncidents = React.lazy(() => import("@/pages/HrIncidents"));
const HrTrainingRecords = React.lazy(() => import("@/pages/HrTrainingRecords"));
const EmployeeLifecycleQualifications = React.lazy(() => import("@/pages/EmployeeLifecycleQualifications"));
// ROUTE-SPLIT-001 Wave 4 — HR Daily Reports (default + named-export wrapper) lazy.
const HrDailyReports = React.lazy(() => import("@/pages/HrDailyReports"));
const HrDailyReportDetail = React.lazy(() => import("@/pages/HrDailyReports").then(m => ({ default: m.HrDailyReportDetail })));
const HrMotiveDrivers = React.lazy(() => import("@/pages/HrMotiveDrivers"));
const HrDriverProfile = React.lazy(() => import("@/pages/HrDriverProfile"));
// ROUTE-SPLIT-001 Wave 2 — dispatch/* and safety-portal/* lazy-loaded.
const SafetyDriverProfile = React.lazy(() => import("@/pages/SafetyDriverProfile"));
const DispatchDriverProfile = React.lazy(() => import("@/pages/DispatchDriverProfile"));
const HrPayrollVariance = React.lazy(() => import("@/pages/HrPayrollVariance"));
const HrDriverQualificationDashboard = React.lazy(() => import("@/pages/HrDriverQualificationDashboard"));
const HrDriverQualificationImport = React.lazy(() => import("@/pages/HrDriverQualificationImport"));
const HrTimeOff = React.lazy(() => import("@/pages/HrTimeOff"));
import PublicTimeOff from "@/pages/PublicTimeOff";
import SafetyLogin from "@/pages/SafetyLogin";
import DispatchLogin from "@/pages/DispatchLogin";
import LeadershipLogin from "@/pages/LeadershipLogin";
const DispatchHub = React.lazy(() => import("@/pages/DispatchHub"));
const DispatchBoard = React.lazy(() => import("@/pages/DispatchBoard"));
const DispatchCommandCenter = React.lazy(() => import("@/pages/DispatchCommandCenter"));
const DispatchHaulLedger = React.lazy(() => import("@/pages/DispatchHaulLedger"));
const DispatchDriverQualification = React.lazy(() => import("@/pages/DispatchDriverQualification"));
import DispatchChangePassword from "@/pages/DispatchChangePassword";
import DispatchForgotPassword from "@/pages/DispatchForgotPassword";
import DispatchResetPassword from "@/pages/DispatchResetPassword";
const SafetyHub = React.lazy(() => import("@/pages/SafetyHub"));
import SafetyChangePassword from "@/pages/SafetyChangePassword";
import SafetyForgotPassword from "@/pages/SafetyForgotPassword";
import SafetyResetPassword from "@/pages/SafetyResetPassword";
const SafetyCorrectiveActions = React.lazy(() => import("@/pages/SafetyCorrectiveActions"));
const SafetyFireExtinguishers = React.lazy(() => import("@/pages/SafetyFireExtinguishers"));
const SafetyFireExtImport = React.lazy(() => import("@/pages/SafetyFireExtImport"));
const SafetyDocuments = React.lazy(() => import("@/pages/SafetyDocuments"));
const SafetyTrainingRecords = React.lazy(() => import("@/pages/SafetyTrainingRecords"));
const SafetyEmployeeProfiles = React.lazy(() => import("@/pages/SafetyEmployeeProfiles"));
const EmployeeProfile = React.lazy(() => import("@/pages/EmployeeProfile"));
const HistoricalRecordsIntake = React.lazy(() => import("@/pages/HistoricalRecordsIntake"));
const HistoricalRecordsQueue = React.lazy(() => import("@/pages/HistoricalRecordsQueue"));
const HistoricalRecordsBatches = React.lazy(() => import("@/pages/HistoricalRecordsBatches"));
const HistoricalRecordsBatchDetail = React.lazy(() => import("@/pages/HistoricalRecordsBatchDetail"));
const SafetyDigest = React.lazy(() => import("@/pages/SafetyDigest"));
const SafetyIncidents = React.lazy(() => import("@/pages/SafetyIncidents"));
const SafetyAudits = React.lazy(() => import("@/pages/SafetyAudits"));
const SafetyFormsRecords = React.lazy(() => import("@/pages/SafetyFormsRecords"));
const SafetyReports = React.lazy(() => import("@/pages/SafetyReports"));
const SafetyTopicLibrary = React.lazy(() => import("@/pages/SafetyTopicLibrary"));
const HrSafetyRecords = React.lazy(() => import("@/pages/HrSafetyRecords"));
// ROUTE-SPLIT-001 Wave 3 — Training surfaces lazy.
const TrainingHub = React.lazy(() => import("@/pages/TrainingHub"));
import AdminDeployReadiness from "@/pages/AdminDeployReadiness";
const TrainingTrack = React.lazy(() => import("@/pages/TrainingTrack"));
const TrainingQrPoster = React.lazy(() => import("@/pages/TrainingQrPoster"));
const TrainingPacketDownload = React.lazy(() => import("@/pages/TrainingPacketDownload"));
const AdminTrainingVideos = React.lazy(() => import("@/pages/AdminTrainingVideos"));
import DevLogin from "@/pages/DevLogin";
import DevHub from "@/pages/DevHub";
import CheatSheet from "@/pages/CheatSheet";
import JobPhotosLibrary from "@/pages/JobPhotosLibrary";
import FieldLeadershipHub from "@/pages/FieldLeadershipHub";
import FieldLeadershipFormPage from "@/pages/FieldLeadershipFormPage";
import FieldLeadershipRecords from "@/pages/FieldLeadershipRecords";
import FieldLeadershipView from "@/pages/FieldLeadershipView";
// ROUTE-SPLIT-001 Wave 4 — Legal + Tasks + DocumentExpirations lazy.
const TermsOfService = React.lazy(() => import("@/pages/legal/TermsOfService"));
const PrivacyPolicy = React.lazy(() => import("@/pages/legal/PrivacyPolicy"));
const Tasks = React.lazy(() => import("@/pages/Tasks"));
const DocumentExpirations = React.lazy(() => import("@/pages/DocumentExpirations"));
const HrEmployees = React.lazy(() => import("@/pages/HrEmployees"));
const HrEmployeeRequestsQueue = React.lazy(() => import("@/pages/HrEmployeeRequestsQueue"));
// ROUTE-SPLIT-001 Wave 4 — Workflow tool surfaces lazy.
const PoRequests = React.lazy(() => import("@/pages/PoRequests"));
const ProjectHealth = React.lazy(() => import("@/pages/ProjectHealth"));
const AssetTransfers = React.lazy(() => import("@/pages/AssetTransfers"));
// Phase V-Prelude · Wave 1 · Substrate — Operational Constraints.
import Constraints from "@/pages/Constraints";
import NewConstraint from "@/pages/NewConstraint";
import ConstraintDetail from "@/pages/ConstraintDetail";
// Phase V-Prelude · Wave 1.1 — PM Project Detail (hosts the
// Operational Timeline sidecar). Read-only, calm, single-project.
const PmProjectDetail = React.lazy(() => import("@/pages/PmProjectDetail"));
// Track 19.57 · Project Operational Thread PROMOTION — presentation
// layer over certified project / recent-context / project-day /
// material-movement / JHA / project_intelligence endpoints.
const PmProjectThread = React.lazy(() => import("@/pages/PmProjectThread"));
const PmProjectSchedule = React.lazy(() => import("@/pages/PmProjectSchedule"));
const PmMondayReviewWorkspace = React.lazy(() => import("@/pages/PmMondayReviewWorkspace"));
// PM Command Center · Phase 4B · 2026-02-10
// One operational command screen for the PM (resources · hauls ·
// materials · shop · safety · timeline). Reads strictly from the
// Phase 4A /api/pm/command-center/* endpoints. /pm/projects/:pn now
// redirects to /pm/command-center?project_number=:pn so there is no
// duplicate single-project surface.
const PmCommandCenter = React.lazy(() => import("@/pages/PmCommandCenter"));
const PmProjectRedirect = React.lazy(() => import("@/pages/PmProjectRedirect"));
// Operations Center · Phase 4C · 2026-02-10
// Cross-company command board. Composes Asset Spine + Dispatch CC +
// PM CC + Shop + Safety + Motive into 10 read-only endpoints. Uses
// Specialty Asset terminology (Phase 4C correction — road plates are
// ONE family member, NOT privileged).
const OperationsCenterCommand = React.lazy(() => import("@/pages/OperationsCenterCommand"));
const OperationsMapPage = React.lazy(() => import("@/pages/OperationsMapPage"));
const DispatchOperationsMapPage = React.lazy(() => import("@/pages/DispatchOperationsMapPage"));
const PlatformTrustDashboard = React.lazy(() => import("@/components/PlatformTrustDashboard"));
const PmHomeRedirect = React.lazy(() => import("@/pages/PmHomeRedirect"));
import AccessDenied from "@/pages/AccessDenied";
import NotFound from "@/pages/NotFound";
import GlobalFooter from "@/components/GlobalFooter";
import ScrollToTop from "@/components/ScrollToTop";
import { RequireAdmin } from "@/components/RequireAdmin";
import { RequireTransportationPortal } from "@/components/RequireTransportationPortal";
import { RequireAdminOrPm } from "@/components/RequireAdminOrPm";
import { RequireAdminPmOrSafety } from "@/components/RequireAdminPmOrSafety";
import { RequirePm } from "@/components/RequirePm";
import { RequireShop } from "@/components/RequireShop";
import { RequireHr } from "@/components/RequireHr";
import { RequireSafety } from "@/components/RequireSafety";
import { RequireDispatch } from "@/components/RequireDispatch";
import { RequireDev } from "@/components/RequireDev";
import { FormPasswordGate } from "@/components/FormPasswordGate";
import GlobalKeepalive from "@/components/GlobalKeepalive";
import BackendStatusBanner from "@/components/BackendStatusBanner";
// TRUST-DIAGNOSTICS-001 · Global session/error overlay. Renders ONE
// modal (Session Expired / Access Restricted / Connection Problem /
// Services Unavailable) when the central axios interceptor classifies
// a rejection — so a cascade of failing card-loaders never produces
// a multi-card storm or a misleading "SERVER UNREACHABLE" banner.
import SessionStatusOverlay from "@/components/SessionStatusOverlay";
import ClusterCapacityBanner from "@/components/ClusterCapacityBanner";
import BannerStrip from "@/components/BannerStrip";
import EnvBanner from "@/components/EnvBanner";
import SplashOverlay from "@/components/SplashOverlay";
// R-BL-3 · Global queue visibility pill + drawer (visibility-only).
import QueueStatusPill from "@/components/QueueStatusPill";
import OfflineBanner from "@/components/OfflineBanner";
import { validateStoredTokens } from "@/lib/tokenValidation";
import EnforcePortalScope from "@/components/EnforcePortalScope";
import MultiPortalHydrator from "@/components/MultiPortalHydrator";
import IdleTimeout from "@/components/IdleTimeout";
import PosterErrorBoundary from "@/components/PosterErrorBoundary";
// TRACK 25.01 · AOS Phase B — Legacy Moved banner rendered on
// consolidated admin routes that now live inside OCC.
import { WithLegacyBanner } from "@/components/admin/LegacyMovedBanner";

// Crew Hub (Basecamp-style /app section)
// Crew Hub pages removed 2026-04-28 — replaced by external Basecamp link.

// iter236 · Site Inspection moved into Safety portal ownership.
// The legacy public form-password gate (SITE_INSPECTION_CODE = "1982")
// and the public submission paths (/submit, /inspections/submit,
// /inspect/new) are removed. Site Inspection is now an authenticated
// Safety/Admin-only operation at /safety/inspections/new. Public/legacy
// URLs redirect to /safety-portal/login so anyone with a stale link
// reaches the right place.
const InspectionLegacyRedirect = () => (
  <Navigate
    to="/safety-portal/login?returnTo=/safety/inspections/new"
    replace
  />
);

// TRACK 25.02 · Phase D — CommandPaletteProvider wraps every admin
// route when `masci.admin.nav.v3` flag is on. Falls back to a plain
// pass-through when the flag is off, so the legacy nav is untouched.
import { CommandPaletteProvider } from "@/components/admin/CommandPalette";
import { isAdminNavV3Enabled as _isAdminNavV3Enabled } from "@/lib/featureFlags";
function AdminPaletteShell({ children }) {
  if (_isAdminNavV3Enabled()) {
    return <CommandPaletteProvider>{children}</CommandPaletteProvider>;
  }
  return children;
}
const A = (el) => (
  <RequireAdmin>
    <AdminPaletteShell>{el}</AdminPaletteShell>
  </RequireAdmin>
);
// TRACK 18.00E-FIX · Dispatch-accessible Transportation Operations shell.
// Wraps `/transportation-operations/*` so dispatchers reach Mission
// Control without an Admin Console gate. RBAC inside the shell is
// already enforced by the backend composers (Phase C/D + Track 16.16).
const TX = (el) => <RequireTransportationPortal>{el}</RequireTransportationPortal>;
const AP = (el) => <RequireAdminOrPm>{el}</RequireAdminOrPm>;
// iter322 — Admin · PM · Safety read-only review for the three
// Safety detail views (inspections / meetings / incidents). All
// other /admin/* routes stay on the stricter AP guard.
const APS = (el) => <RequireAdminPmOrSafety>{el}</RequireAdminPmOrSafety>;
const P = (el) => <RequirePm>{el}</RequirePm>;
const S = (el) => <RequireShop>{el}</RequireShop>;
const H = (el) => <RequireHr>{el}</RequireHr>;
const FL = (el) => <RequireFl>{el}</RequireFl>;
const SF = (el) => <RequireSafety>{el}</RequireSafety>;
const DP = (el) => <RequireDispatch>{el}</RequireDispatch>;
const D = (el) => <RequireDev>{el}</RequireDev>;

// TRACK 25.01 · AOS Phase B — prepend the LegacyMovedBanner to
// pages that were consolidated into the Operations Control Center.
// The original page still renders; the banner explains where the
// canonical home now lives and links there. Zero routes deleted.
const LB = (path, el) => (
  <WithLegacyBanner pathname={path}>{el}</WithLegacyBanner>
);

// ─────────────────────────────────────────────────────────────────
// Track 22.2 Phase B · route-group extraction.
// This file owns every <Route> declaration, every eager & lazy route
// target, every guard alias, and the inline redirect helpers used by
// routes. Route JSX preserved byte-identically from the pre-refactor
// App.js so the parity extractor sees identical `<Route path=... />`
// tokens after the move. Zero behavior change.
// ─────────────────────────────────────────────────────────────────

export function AppRoutes() {
  return (
    <React.Suspense fallback={null}><Routes>
            {/* MASCI Hub — public */}
            <Route path="/" element={<Hub />} />
            <Route path="/revise/:token" element={<Revise />} />
            <Route path="/safety" element={<SafetySection />} />
            <Route path="/safety/forms/login" element={<SafetyFormsLogin />} />
            <Route path="/safety/forms" element={<SafetyFormsHub />} />
            <Route path="/safety/forms/equipment-issuance/new" element={<NewSafetyEquipmentIssuance />} />
            <Route path="/safety/forms/equipment-issuance/:id" element={<ViewSafetyForm kind="issuance" />} />
            <Route path="/safety/forms/equipment-issuance/:id/return" element={<ReturnEquipment />} />
            <Route path="/safety/forms/equipment-training/new" element={<NewSafetyEquipmentTraining />} />
            <Route path="/safety/forms/equipment-training/:id" element={<ViewSafetyForm kind="training" />} />
            <Route path="/safety/cards" element={<FieldSafetyCards />} />
            <Route path="/field" element={<FieldSection />} />
            <Route path="/field/calculators" element={<MaterialCalculators />} />
            <Route path="/qaqc" element={<QaqcSection />} />
            <Route path="/qa-qc" element={<Navigate to="/qaqc" replace />} />
            <Route path="/qaqc/:slug/new" element={<NewQaqcInspection />} />
            <Route path="/qaqc/:id" element={<ViewQaqcInspection />} />
            <Route path="/admin/qaqc" element={A(<AdminQaqcList />)} />
            <Route path="/admin/transportation/*" element={A(<AdminTransportation />)} />
            {/* TRACK 18.00E-FIX — Dispatch-accessible Transportation
                Operations canonical route. Same shell, dispatch-safe
                gate. /admin/transportation/* remains an alias for
                admin-only oversight bookmarks. */}
            <Route path="/transportation-operations/*" element={TX(<AdminTransportation />)} />
            <Route path="/admin/photos" element={A(<JobPhotosLibrary portalKey="admin" />)} />

            {/* Phase V-Prelude · Wave 1 · Operational Constraints.
                Capability-scoped at the page level (constraintCapabilities.js).
                Backend gate accepts admin / pm / safety / fl / leadership / hr
                tokens. We don't wrap with a Require* component because the
                surface is cross-portal — same React tree renders for every
                operator role per the shared-surface doctrine. */}
            <Route path="/constraints" element={<Constraints />} />
            <Route path="/constraints/new" element={<NewConstraint />} />
            <Route path="/constraints/:id" element={<ConstraintDetail />} />

            {/* Field Leadership — supervisor docs gated by MASCIGC password */}
            <Route path="/leadership" element={<FieldLeadershipHub />} />
            {/* Track 13.6K · Phase 3 — Leadership Hub V2 COMPANION (cross-portal exec attention).
                Must be declared BEFORE the dynamic /leadership/:kind/new route. */}
            <Route path="/leadership/hub_v2" element={<LeadershipHubV2 />} />
            {/* Track 13.6L — /field-leadership/hub_v2 RETIRED.
                Existing /field-leadership/portal/dashboard already satisfies the
                intended field-leadership operational workflow. */}
            <Route path="/leadership/records" element={<FieldLeadershipRecords />} />
            <Route path="/leadership/records/:id" element={<FieldLeadershipView />} />
            <Route path="/leadership/:kind/new" element={<FieldLeadershipFormPage />} />

            {/* iter236 · Site Inspection moved into Safety portal ownership.
                Legacy URLs redirect to safety login; the authoritative
                authenticated entry is /safety/inspections/new. */}
            <Route path="/safety/inspections/new" element={SF(<NewInspection />)} />
            <Route path="/inspect/new" element={<InspectionLegacyRedirect />} />
            <Route path="/submit" element={<InspectionLegacyRedirect />} />
            <Route path="/inspections/submit" element={<InspectionLegacyRedirect />} />
            <Route path="/inspections/new" element={<InspectionLegacyRedirect />} />

            <Route path="/meetings/new" element={<NewMeeting />} />
            <Route path="/meetings/submit" element={<NewMeeting publicMode />} />

            <Route path="/jha" element={<JhaPlansHub />} />
            <Route path="/jha/submit" element={<Navigate to="/jha" replace />} />
            <Route path="/jha/new" element={<Navigate to="/jha" replace />} />

            <Route path="/trench-boxes" element={<Navigate to="/trench-safety/tabulated-data" replace />} />
            {/* Phase 3.5 · Public Trench Safety Dashboard (GAP-1) */}
            <Route path="/trench-safety" element={<PublicTrenchSafetyDashboard />} />
            {/* Sprint · Public Trench Safety UX Correction — distinct public surfaces */}
            <Route path="/trench-safety/tabulated-data" element={<PublicTrenchSafetyTabulatedData />} />
            <Route path="/trench-safety/references"     element={<PublicTrenchSafetyReferences />} />
            <Route path="/trench-safety/report"         element={<PublicTrenchSafetyReport />} />
            {/* Phase 3 · Trench Safety Operations System — public mobile QR landing */}
            <Route path="/trench-safety/assets/:assetId" element={<TrenchSafetyQrLanding />} />
            {/* TRACK 16.08 · Public External Carrier Invite Portal + Certificate Verify */}
            <Route path="/transport-invite/:token" element={<ExternalCarrierInvite />} />
            <Route path="/transport-verify/:cnum" element={<CertificateVerify />} />

            {/* TRACK 19.16 · LEGACY RETIREMENT — /incidents/new and
                /incidents/submit are retired. Any historical URL now
                redirects to the Incident Intelligence Engine.
                NewIncident component is no longer routed anywhere in
                production; kept in source only for admin-only recovery
                and as an unlinked backend-compatibility reference. */}
            <Route path="/incidents/new" element={<Navigate to="/incidents/report" replace />} />
            <Route path="/incidents/submit" element={<Navigate to="/incidents/report" replace />} />
            {/* TRACK 19.16 · Phase B1 — new engine-backed reporting flow. */}
            <Route path="/incidents/report" element={<IncidentReport />} />
            {/* TRACK 19.16 · Phase B2 — public no-auth Near-Miss Kiosk. */}
            <Route path="/near-miss" element={<NearMissKiosk />} />
            {/* TRACK 19.16 · Phase C — Safety Case Workspace (command center). */}
            <Route path="/safety/cases/:caseId" element={<SafetyCaseWorkspace />} />
            {/* Track 19.58 · Incident Operational Thread PROMOTION.
                Read-only Universal Thread shell over the certified
                incident-case endpoints. Auth inherited from the same
                Safety JWT the workspace already uses. */}
            <Route path="/safety/incidents/:caseId/thread" element={<SafetyIncidentThread />} />
            {/* TRACK 19.16 · Phase D — Executive Intelligence Center. */}
            <Route path="/safety/executive-intelligence" element={<ExecutiveIntelligence />} />
            {/* TRACK 19.16 · Phase E — Report Intelligence Engine viewer. */}
            <Route path="/safety/cases/:caseId/reports/:reportType" element={<IncidentReportViewer />} />
            {/* TRACK 19.36 · Executive Case Report — boardroom-grade single-screen view. */}
            <Route path="/safety/cases/:caseId/executive-report" element={<ExecutiveCaseReport />} />

            {/* DR-03 · Canonical Daily Report authoring route.
                `/daily/submit` is the only creation route. Legacy
                creation aliases redirect here and never mount a
                competing shell. */}
            <Route path="/daily/new" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/daily/submit" element={<NewDailyReportV3 publicMode />} />

            <Route path="/equipment/new" element={<NewEquipmentInspection />} />
            <Route path="/equipment/submit" element={<NewEquipmentInspection publicMode />} />
            <Route path="/equipment/:id" element={<RedirectWithId base="/admin/equipment" />} />

            {/* iter251 Phase 2 · Driver-facing Daily Vehicle Inspection */}
            <Route path="/fleet/dvir/new" element={<NewFleetDVIR />} />
            <Route path="/fleet/dvir/submit" element={<NewFleetDVIR />} />
            {/* Phase 5 · Weekly Lead + Emergency Equipment forms */}
            <Route path="/fleet/weekly-lead/new" element={<NewFleetDVIR kind="weekly_lead" />} />
            <Route path="/fleet/weekly-emergency/new" element={<NewFleetDVIR kind="weekly_emergency" />} />
            <Route path="/fleet/dvir/submitted/:id" element={<FleetDVIRConfirmation />} />

            <Route path="/thank-you" element={<ThankYou />} />
            <Route path="/cheatsheet" element={<PosterErrorBoundary><CheatSheet /></PosterErrorBoundary>} />
            <Route path="/cheat-sheet" element={<Navigate to="/cheatsheet" replace />} />

            {/* ------- Route aliases for old / printed QR codes ---------
                If a poster already out in the field points at an older
                URL pattern, redirect to the canonical route instead of
                404-ing. Matches the /cheat-sheet redirect pattern. */}
            <Route path="/reports/daily/new" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/daily-reports/new" element={<Navigate to="/daily/submit" replace />} />
            {/* TRACK 22.9C-FIX · Field Leadership Portal Dashboard historically
                pointed "Daily Reports" at the bare /daily-reports path (no
                portal prefix). That path had no route registered, causing
                a route-mismatch that surfaced to operators as a blank 404
                page mid-workflow. Fixed at the source (button target →
                /daily/new) AND redirected here so any legacy nav, poster,
                or bookmarked URL still lands on the canonical V3 form. */}
            <Route path="/daily-reports" element={AP(<DailyReportsDashboard />)} />
            <Route path="/daily-reports/:id" element={<RedirectWithId base="/pm/daily" />} />
            <Route path="/safety/jha" element={<Navigate to="/jha" replace />} />
            <Route path="/safety/trench-boxes" element={<Navigate to="/trench-boxes" replace />} />
            {/* Phase 3 · Trench Safety inside the Safety portal */}
            <Route path="/safety/trench-safety"                       element={SF(<TrenchSafetyHub />)} />
            <Route path="/safety/trench-safety/assets"                element={SF(<TrenchSafetyAssetsList />)} />
            <Route path="/safety/trench-safety/assets/:assetId"       element={SF(<TrenchSafetyAssetDetail />)} />
            <Route path="/safety/trench-safety/tabulated-data"        element={SF(<TrenchSafetyTabulatedData />)} />
            <Route path="/safety/trench-safety/reports"               element={SF(<TrenchSafetyReports />)} />
            <Route path="/safety/trench-safety/excavations"           element={SF(<ExcavationOversight />)} />
            <Route path="/admin/trench-safety/excavations"            element={AP(<ExcavationOversight />)} />
            <Route path="/trench-safety/excavation/new"               element={<PublicExcavationForm />} />
            {/* Phase 7.5B — Safety Repair Review + Field Reports inbox */}
            <Route path="/safety/trench-safety/repair-review"          element={SF(<TrenchSafetyRepairReviewPage />)} />
            <Route path="/safety/trench-safety/field-reports"          element={SF(<TrenchSafetyFieldReportsPage />)} />
            {/* Legacy alias inside the safety-portal namespace */}
            <Route path="/safety-portal/trench-safety"                element={<Navigate to="/safety/trench-safety" replace />} />
            <Route path="/safety-portal/trench-safety/assets"         element={<Navigate to="/safety/trench-safety/assets" replace />} />
            <Route path="/safety-portal/trench-safety/tabulated-data" element={<Navigate to="/safety/trench-safety/tabulated-data" replace />} />

            {/* ============================================================
                Crew Hub — REMOVED 2026-04-28 (replaced by Basecamp link).
                All /app/* routes now redirect to the Hub home so any old
                bookmark or stale token can't land users on the broken
                Basecamp-clone UI. The /api/auth/* and /api/projects backend
                routes are kept (used by the admin recovery panel).
                ============================================================ */}
            <Route path="/app/*" element={<Navigate to="/" replace />} />

            {/* ============================================================
                Safety Admin — unchanged
                ============================================================ */}
            <Route path="/admin/login" element={<AdminLogin />} />
            {/* Track 19.28 · P0-1 · Admin Hub V1 soft-retire.
                TRACK 25 · SPRINT 1 · /admin is now the canonical Admin
                Operating System landing (AdminOS.jsx · 10 domains ·
                live endpoints · SideNavV3). Legacy hubs (AdminHub,
                AdminHubV2, AdminHubSwitcher, AdminHubV3) still exist
                on disk for reference but every legacy URL immediately
                redirects to /admin so bookmarks keep working and no
                operator ever sees a deprecated dashboard. */}
            <Route path="/admin" element={A(<AdminOS />)} />
            <Route path="/admin/hub_v1" element={<Navigate to="/admin" replace />} />
            {/* Track 13.6K · Phase 1 — Admin Hub V2 preview (Operations Control Center). */}
            <Route path="/admin/hub_v2" element={<Navigate to="/admin" replace />} />
            <Route path="/admin/executive-overview" element={A(<ExecutiveOverview />)} />
            <Route path="/admin/executive-intelligence" element={A(<ExecutiveIntelligence />)} />
            {/* Track 13.22 · Phase D · Material Movement Ledger · Admin Data-Quality + CSV. */}
            <Route path="/admin/material-ledger-quality" element={A(<AdminMaterialLedgerQuality />)} />
            <Route path="/admin/people" element={A(<AdminPeople />)} />
            <Route path="/admin/mfa" element={A(<AdminMfa />)} />
            <Route path="/admin/promo-assets" element={A(<AdminPromoAssets />)} />
            <Route path="/admin/jobs" element={A(<AdminJobs />)} />
            <Route path="/admin/cost-registry" element={A(<AdminCostRegistry />)} />
            <Route path="/admin/jobs/:projectNumber/team" element={A(<AdminJobTeam />)} />
            {/* Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE */}
            <Route path="/admin/project-staffing" element={A(<AdminProjectStaffing />)} />
            {/* M-3 · Geocode Foundation · Motive Geofence Reconciliation */}
            <Route path="/admin/geofence-reconciliation" element={A(<AdminGeofenceReconciliation />)} />
            {/* M-2 · Event Router · Operations dashboard (visibility only) */}
            {/* TRACK 25.01 · Phase B · consolidated into OCC (integrations.probe_all). */}
            <Route path="/admin/operations-dashboard" element={A(LB("/admin/operations-dashboard", <AdminOperationsDashboard />))} />
            {/* TRACK 24.17 · Operations Control Center — unified maintenance console. */}
            <Route path="/admin/operations-control" element={A(<OperationsControlCenter />)} />
            <Route path="/admin/operations-control/cases/:caseId" element={A(<OperationsControlCaseDetail />)} />
            <Route path="/operations-control/cases" element={A(<OperationsControlCasesRoute />)} />
            <Route path="/operations-control/cases/:caseId" element={A(<OperationsControlCaseDetail />)} />
            {/* MOTIVE-DATA-002 · Asset Mapping Admin Center */}
            <Route path="/admin/asset-mapping" element={A(<AdminAssetMapping />)} />
            <Route path="/admin/asset-spine" element={A(<AdminAssetSpineHealth />)} />
            <Route path="/admin/equipment" element={A(<AdminEquipment />)} />
            <Route path="/admin/email" element={A(<AdminEmail />)} />
            <Route path="/admin/training" element={A(<AdminTraining />)} />
            <Route path="/admin/compliance" element={A(<AdminCompliance />)} />
            <Route path="/admin/system" element={A(LB("/admin/system", <AdminSystem />))} />
            <Route path="/admin/ai-configuration" element={A(<AdminAIConfiguration />)} />
            <Route path="/admin/integration-truth" element={A(LB("/admin/integration-truth", <IntegrationTruth />))} />
            <Route path="/admin/preview-validation-identities" element={A(<PreviewValidationIdentities />)} />
            <Route path="/admin/recovery" element={A(LB("/admin/recovery", <AdminRecovery />))} />
            {/* TRACK 25 · SPRINT 3 · Storage & Recovery domain landing. */}
            <Route path="/admin/storage-recovery" element={A(<AdminStorageRecovery />)} />
            {/* TRACK 25 · SPRINT 4 · Four more domain landings. */}
            <Route path="/admin/ai-operations" element={A(<AdminAiOperations />)} />
            <Route path="/admin/communications" element={A(<AdminCommunications />)} />
            <Route path="/admin/identity-security" element={A(<AdminIdentitySecurity />)} />
            <Route path="/admin/trust-spine" element={A(<PlatformTrustDashboard />)} />
            <Route path="/admin/governance-trust" element={A(<AdminGovernanceTrust />)} />
            {/* TRACK 25 · SPRINT 5/6 · Configuration · Diagnostics · Maintenance · Overview redirect. */}
            <Route path="/admin/platform-configuration" element={A(<AdminPlatformConfiguration />)} />
            <Route path="/admin/diagnostics" element={A(<AdminDiagnostics />)} />
            <Route path="/admin/maintenance" element={A(<AdminMaintenance />)} />
            <Route path="/admin/platform-overview" element={<AdminPlatformOverview />} />
            <Route path="/admin/recovery-stream" element={A(LB("/admin/recovery-stream", <AdminRecoveryStream />))} />
            <Route path="/admin/jha-acknowledgements" element={A(<AdminJhaAcknowledgements />)} />
            <Route path="/admin/command-center" element={A(<AdminCommandCenter />)} />
            <Route path="/admin/database" element={A(<AdminDatabase />)} />
            <Route path="/admin/integrations" element={A(<AdminIntegrationCenter />)} />
            <Route path="/admin/dispatch" element={A(<AdminDispatch />)} />
            <Route path="/admin/dls/shift-qr" element={A(<AdminDlsShiftQR />)} />
            <Route path="/admin/dls/day-1-debrief" element={A(<AdminDlsDay1Debrief variant="day-1" />)} />
            <Route path="/admin/dls/week-1-debrief" element={A(<AdminDlsDay1Debrief variant="week-1" />)} />
            <Route path="/admin/profile" element={A(<AdminProfile />)} />
            <Route path="/admin/operations-events" element={A(<AdminOperationsEvents />)} />
            <Route path="/admin/digest-config" element={A(<AdminDigestConfig />)} />
            <Route path="/admin/operational-intelligence" element={A(<AdminOperationalIntelligence />)} />
            <Route path="/admin/operational-intelligence/recipients" element={A(<AdminOperationalIntelligenceRecipients />)} />
            <Route path="/admin/system-health" element={A(LB("/admin/system-health", <SystemHealth />))} />
            <Route path="/admin/audit-log" element={A(<AdminAuditLog />)} />
            {/* iter445 · F-003 · operator-visible scheduler/digest history */}
            {/* TRACK 25.01 · Phase B · consolidated into OCC (queues.scheduler_runs). */}
            <Route path="/admin/scheduler-runs" element={A(LB("/admin/scheduler-runs", <AdminSchedulerRuns />))} />
            <Route path="/admin/legacy-imports" element={A(<AdminLegacyImports />)} />
            <Route path="/admin/sessions" element={A(<AdminSessions />)} />
            <Route path="/admin/guidance-coverage" element={A(<AdminGuidanceCoverage />)} />
            <Route path="/admin/operational-inventory" element={A(<AdminOperationalInventory />)} />
            {/* Phase 2 P1 · Operational Intelligence Notifications — role-aware in-platform digest */}
            <Route path="/notifications" element={<NotificationsDigest />} />
            {/* Phase 2 · Compliance Gap Detector + Governance Health (admin-strict) */}
            <Route path="/admin/governance" element={A(<AdminGovernance />)} />
            <Route path="/admin/project-identity" element={A(<AdminProjectIdentityGovernance />)} />
            <Route path="/admin/governance/self-protection" element={A(<SelfProtection />)} />
            <Route path="/admin/compliance-findings" element={A(<AdminComplianceFindings />)} />
            <Route path="/admin/operational-language" element={A(<AdminOperationalLanguage />)} />
            {/* Operational Guidance Center (iter190 — Training/Help overhaul Phase A).
                Public route — backend enforces RBAC per article.
                The 3-slot route handles: hub home, section, article. */}
            <Route path="/guidance" element={<OperationalGuidanceCenter />} />
            <Route path="/guidance/section/:sectionId" element={<OperationalGuidanceCenter />} />
            <Route path="/guidance/:articleId" element={<OperationalGuidanceCenter />} />
            <Route path="/admin/deploy-recovery" element={A(LB("/admin/deploy-recovery", <DeployRecovery />))} />
            <Route path="/admin/assets/:assetId" element={A(<AssetProfile />)} />
            <Route path="/admin/asset-admin" element={A(<AdminAssetAdmin />)} />
            <Route path="/admin/driver-intel/:driverKey" element={A(<AdminDriverIntel />)} />
            <Route path="/admin/equipment/:id/history" element={A(<AdminMasterHistory kind="equipment" />)} />
            <Route path="/admin/employees/:id/history" element={A(<AdminMasterHistory kind="employee" />)} />
            <Route path="/admin/analytics" element={A(<AdminAnalytics />)} />
            <Route path="/admin/leadership-equipment" element={A(<AdminLeadershipEquipment />)} />
            <Route path="/admin/terminations" element={A(<AdminTerminations />)} />
            <Route path="/admin/guide" element={A(<AdminGuide />)} />
            <Route path="/admin/pnl" element={AP(<ProjectPnlPage />)} />

            <Route path="/admin/inspections" element={AP(<Dashboard />)} />
            <Route path="/admin/inspections/:id" element={APS(<ViewInspection />)} />

            <Route path="/admin/meetings" element={AP(<MeetingsDashboard />)} />
            <Route path="/admin/meetings/:id" element={APS(<ViewMeeting />)} />

            <Route path="/admin/jha-plans" element={AP(<JhaPlansAdmin />)} />
            <Route path="/admin/jha" element={<Navigate to="/admin/jha-plans" replace />} />
            <Route path="/admin/jha/:id" element={<Navigate to="/admin/jha-plans" replace />} />

            <Route path="/admin/trench-boxes" element={AP(<TrenchBoxesAdmin />)} />
            <Route path="/admin/trench-boxes/poster" element={AP(<PosterErrorBoundary><TrenchBoxPoster /></PosterErrorBoundary>)} />
            {/* Phase 7.5A — Admin Portal mirror of Safety Portal Trench Safety
                Command Center. Admin Portal is a superset of Safety Portal;
                routes reuse the same components and the backend `safety_or_admin`
                gate accepts the X-Admin-Token. */}
            <Route path="/admin/trench-safety"                  element={AP(<TrenchSafetyHub />)} />
            <Route path="/admin/trench-safety/assets"           element={AP(<TrenchSafetyAssetsList />)} />
            <Route path="/admin/trench-safety/assets/:assetId"  element={AP(<TrenchSafetyAssetDetail />)} />
            <Route path="/admin/trench-safety/tabulated-data"   element={AP(<TrenchSafetyTabulatedData />)} />
            <Route path="/admin/trench-safety/reports"          element={AP(<TrenchSafetyReports />)} />
            <Route path="/admin/trench-safety/repair-review"    element={AP(<TrenchSafetyRepairReviewPage adminPortal={true} />)} />
            <Route path="/admin/trench-safety/field-reports"    element={AP(<TrenchSafetyFieldReportsPage adminPortal={true} />)} />

            <Route path="/admin/jha-plans/poster" element={AP(<PosterErrorBoundary><JhaPlansPoster /></PosterErrorBoundary>)} />

            <Route path="/admin/posters/print-all" element={AP(<PosterErrorBoundary><AllPostersPrint /></PosterErrorBoundary>)} />

            <Route path="/admin/incidents" element={A(<IncidentsDashboard />)} />
            <Route path="/admin/incidents/:id" element={APS(<ViewIncident />)} />

            <Route path="/admin/daily" element={AP(<DailyReportsDashboard />)} />
            <Route path="/admin/daily/:id" element={AP(<ViewDailyReport />)} />

            {/* iter95 — /admin/equipment-inspections explicit so the
                Admin KPI tile lands the user on the inspection LIST
                (the status board view at /admin/equipment is the
                "what's broken right now" view, not the historical record list). */}
            <Route path="/admin/equipment-inspections" element={AP(<EquipmentDashboard />)} />
            <Route path="/admin/equipment/:id" element={AP(<ViewEquipmentInspection context="admin" />)} />

            {/* Admin-namespaced aliases for cross-portal record views.
                These exist purely so the global doc-ID search can route
                without triggering EnforcePortalScope's admin-token wipe
                (which fires the moment the path leaves /admin/*). The
                underlying components are unchanged — they accept admin
                tokens via their own gates. */}
            <Route path="/admin/qaqc/:id" element={AP(<ViewQaqcInspection />)} />
            <Route path="/admin/leadership/records/:id" element={AP(<FieldLeadershipView />)} />
            <Route path="/admin/safety/issuance/:id" element={AP(<ViewSafetyForm kind="issuance" />)} />
            <Route path="/admin/safety/training/:id" element={AP(<ViewSafetyForm kind="training" />)} />

            {/* ============================================================
                Project Management Portal — same surface as admin minus
                backup/recovery. Backed by PM_PASSWORD; admin tokens are
                also accepted by the PM hub guard (RequirePm).
                ============================================================ */}
            <Route path="/pm/login" element={<PmLogin />} />
            <Route path="/pm/reset/:token" element={<PmResetPassword />} />
            <Route path="/pm/change-password" element={P(<PmChangePassword />)} />
            <Route path="/pm" element={P(<PmHomeRedirect />)} />
            {/* Track 13.6F · PM route swap — /pm/hub now renders PmHubV2 (live · real APIs · zero-drift verified). Rollback path preserved at /pm/hub_legacy. */}
            <Route path="/pm/hub" element={P(<PmHubV2 />)} />
            <Route path="/pm/hub_legacy" element={P(<PmHub />)} />
            {/* Track 13.6D · PM Hub V2 stable alias remains. */}
            <Route path="/pm/hub_v2" element={P(<PmHubV2 />)} />
            {/* Track 13.6F · PM-2 Unified Holds + PM-3 Due Today (live · real APIs). */}
            {/* Track 13.6G — admins can browse these triage surfaces too (matches /pm/daily, /pm/incidents). */}
            <Route path="/pm/holds" element={AP(<PmHoldsV2 />)} />
            <Route path="/pm/due-today" element={AP(<PmDueTodayV2 />)} />
            {/* iter353e-UI · PM Crew Compliance Lens (read-only) */}
            <Route path="/pm/crew-compliance" element={P(<PmCrewCompliance />)} />
            {/* iter105 — PM Console sub-routes (mirrors AdminConsole layout)
                iter437 P0 Auth Routing — `/pm/routing` and
                `/pm/compliance-export` removed: their panels hardcode
                `/api/admin/*` endpoints the PM token cannot satisfy.
                See PORTAL_AUTH_TOKEN_AUDIT.md.
                iter437 follow-up — `/pm/jobs` restored, now backed by
                PmJobsRead → /api/pm/jobs (non-admin namespace). */}
            <Route path="/pm/jobs"               element={P(<PmJobs />)} />
            <Route path="/pm/job/:projectNumber/team" element={P(<PmJobTeam />)} />
            {/* Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE */}
            <Route path="/pm/project-staffing"  element={P(<PmProjectStaffing />)} />
            <Route path="/pm/project-schedule"  element={P(<PmProjectSchedule />)} />
            <Route path="/pm/monday-review"  element={P(<PmMondayReviewWorkspace />)} />
            {/* Phase V-Prelude · Wave 1.1 · 2026-05-28.
                Calm per-project detail surface hosting the Operational
                Timeline sidecar. Mounted under /pm/* (PM portal
                surface, not a dashboard) per Wave 1.1 directive.
                PHASE 4B (2026-02-10) — this route now redirects to
                /pm/command-center?project_number=<pn> so there is one
                project operational surface, not two. The legacy
                PmProjectDetail page (timeline sidecar) is still
                rendered inside the Command Center timeline tab via
                /api/pm/command-center/timeline. */}
            <Route path="/pm/projects/:projectNumber" element={P(<PmProjectRedirect />)} />
            <Route path="/pm/projects-legacy/:projectNumber" element={P(<PmProjectDetail />)} />
            {/* Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE: also
                expose the inline project detail at /pm/project/{pn}
                (singular) so external links / search results resolve. */}
            <Route path="/pm/project/:projectNumber" element={P(<PmProjectDetail />)} />
            {/* Track 19.57 · Project Operational Thread PROMOTION.
                Same PM auth as the classic detail page. Presents the
                certified project payload through the Track 19.55
                OperationalThreadPage shell. Zero backend drift. */}
            <Route path="/pm/project/:projectNumber/thread" element={P(<PmProjectThread />)} />
            {/* PM Command Center · Phase 4B · 2026-02-10.
                Backed by /api/pm/command-center/* (Phase 4A). One
                page · seven tabs · iPad-friendly. */}
            <Route path="/pm/command-center" element={P(<PmCommandCenter />)} />
            {/* Operations Center · Phase 4C · 2026-02-10.
                Cross-company command board · 9 layers · Specialty
                Asset normalization · backed by /api/operations-center/
                command/* (admin / any portal token). */}
            <Route path="/operations-center" element={A(<OperationsCenterCommand />)} />
            <Route path="/admin/executive-operational-intelligence" element={A(<ExecutiveOperationalIntelligence />)} />
            <Route path="/operations-map" element={A(<OperationsMapPage />)} />
            <Route path="/pm/field-leadership"   element={P(<PmFieldLeadership />)} />
            <Route path="/pm/fleet"              element={P(<PmFleet />)} />
            <Route path="/pm/people"             element={P(<PmPeople />)} />
            <Route path="/pm/suppliers"          element={P(<PmSuppliers />)} />
            {/* Track 19.60 · Vendor Operational Thread PROMOTION.
                Admin-owned initial route. HR/Admin see everything;
                consumer role lenses (PM/Safety/Shop) deferred to a
                later track per Track 20.4 doctrine. */}
            <Route path="/admin/vendors/:vendorId/thread" element={A(<AdminVendorThread />)} />
            <Route path="/admin/assets/:assetRef/thread" element={A(<AdminAssetThread />)} />
            <Route path="/pm/posters"            element={P(<PmPosters />)} />
            <Route path="/pm/qaqc" element={P(<PmQaqcList />)} />
            <Route path="/pm/photos" element={P(<JobPhotosLibrary portalKey="pm" />)} />

            {/* PM-namespaced aliases for the shared dashboards. Same
                components as /admin/* — routing them under /pm/* keeps
                the EnforcePortalScope rule happy (PM session survives
                drill-down) AND lets useHubHome() return "/pm" so the
                back-link goes home to the PM portal, not to the public
                Hub. AP wrappers accept both admin and PM tokens so an
                admin who deep-links into a /pm/... URL still works. */}
            <Route path="/pm/daily" element={AP(<DailyReportsDashboard />)} />
            <Route path="/pm/daily/:id" element={AP(<ViewDailyReport />)} />
            <Route path="/pm/incidents" element={AP(<IncidentsDashboard />)} />
            <Route path="/pm/incidents/:id" element={AP(<ViewIncident />)} />
            <Route path="/pm/meetings" element={AP(<MeetingsDashboard />)} />
            <Route path="/pm/meetings/:id" element={AP(<ViewMeeting />)} />
            <Route path="/pm/inspections" element={AP(<Dashboard />)} />
            <Route path="/pm/inspections/:id" element={AP(<ViewInspection />)} />
            <Route path="/pm/jha-plans" element={AP(<JhaPlansAdmin />)} />
            <Route path="/pm/trench-boxes" element={AP(<TrenchBoxesAdmin />)} />
            <Route path="/pm/equipment" element={AP(<EquipmentDashboard />)} />
            <Route path="/pm/equipment/:id" element={AP(<ViewEquipmentInspection context="admin" />)} />
            {/* TRACK 14.0-DISCOVERABILITY · Wave B-P1 (D-A13) — PM Trench
                Safety entries. Same components as /admin/trench-safety
                under AP guard (PM tokens accepted). PMs need to see
                excavations, assets, repair status for their projects;
                backend probes already PM-scope via compute_pm_scope. */}
            <Route path="/pm/trench-safety"                  element={AP(<TrenchSafetyHub />)} />
            <Route path="/pm/trench-safety/assets"           element={AP(<TrenchSafetyAssetsList />)} />
            <Route path="/pm/trench-safety/assets/:assetId"  element={AP(<TrenchSafetyAssetDetail />)} />
            <Route path="/pm/trench-safety/tabulated-data"   element={AP(<TrenchSafetyTabulatedData />)} />
            <Route path="/pm/trench-safety/reports"          element={AP(<TrenchSafetyReports />)} />
            <Route path="/pm/trench-safety/excavations"      element={AP(<ExcavationOversight />)} />
            {/* /pm/pnl removed 2026-05-07 per Justin — owners want P&L kept admin-only */}

            {/* ============================================================
                Shop Console — mechanics-only view, separate password
                ============================================================ */}
            <Route path="/shop/login" element={<ShopLogin />} />
            <Route path="/shop/reset/:token" element={<ShopResetPassword />} />
            <Route path="/shop/change-password" element={S(<ShopChangePassword />)} />
            {/* Track 13.6J · Phase 1 — Shop route swap.
                /shop → Shop Hub V2 (action-queue surface).
                /shop/hub_legacy → classic Shop hub rollback.
                /shop/hub_v2 alias preserved.
                Shop has no map prominence concern — defects + recovery queues are the operational surface. */}
            <Route path="/shop" element={S(<ShopHubV2 />)} />
            <Route path="/shop/hub_legacy" element={S(<ShopHub />)} />
            <Route path="/shop/hub_v2" element={S(<ShopHubV2 />)} />
            {/* Track 13.33ABC · Asset Care & Readiness Command Center —
                operational home for the Asset Administrator. Mounted on the
                Shop side so asset_admin role lands here, not in Admin Console. */}
            <Route path="/shop/asset-care" element={S(<ShopAssetCare />)} />
            {/* Track 13.28 Phase 2 — Shop Workforce surfaces (Mechanic + Manager queues).
                Backend lifecycle: assign · accept · start · repair · manager-review.
                Repair Complete ≠ RTS preserved; Dispatch retains /clear. */}
            <Route path="/shop/manager/queue" element={S(<ShopManagerQueue />)} />
            <Route path="/shop/me" element={S(<ShopMyAssignments />)} />
            {/* Track 13.27 — Unit History Timeline (consumes Asset Service Event Backbone). */}
            <Route path="/shop/units/history" element={S(<UnitHistoryLanding />)} />
            <Route path="/shop/units/:unitNumber/history" element={S(<UnitHistoryTimeline />)} />
            {/* Track 13.29 — Fuel / Lube Visit Record (one job · many equipment lines). */}
            <Route path="/shop/fuel-lube/new" element={S(<FuelLubeVisitForm />)} />
            {/* Track 13.29 Phase 2 — Fuel / Lube Visit Records list + detail. */}
            <Route path="/shop/fuel-lube" element={S(<FuelLubeVisitRecords />)} />
            <Route path="/shop/fuel-lube/:visitId" element={S(<FuelLubeVisitDetail />)} />
            {/* Track 13.30 — Service Truck Daily Reconciliation. */}
            <Route path="/shop/service-truck-reconciliation/new"         element={S(<ServiceTruckReconciliationForm />)} />
            <Route path="/shop/service-truck-reconciliation"             element={S(<ServiceTruckReconciliationRecords />)} />
            <Route path="/shop/service-truck-reconciliation/:recId"      element={S(<ServiceTruckReconciliationDetail />)} />
            {/* Track 13.31 — PM Engine */}
            <Route path="/shop/pm"                              element={S(<PmDashboard />)} />
            <Route path="/shop/pm/templates"                    element={S(<PmTemplates />)} />
            <Route path="/shop/pm/schedules"                    element={S(<PmSchedules />)} />
            <Route path="/shop/pm/work-orders"                  element={S(<PmWorkOrders />)} />
            <Route path="/shop/pm/work-orders/:id"              element={S(<PmWorkOrders />)} />
            <Route path="/shop/trench-safety-repairs" element={S(<ShopTrenchSafetyRepairs />)} />
            <Route path="/shop/fleet" element={S(<FleetVisibility scope="shop" />)} />
            {/* Track 19.55 · Fleet Unit Operational Thread pilot.
                Reuses the same S() shop-portal auth gate as FleetVisibility
                so entry from Fleet Visibility unit cards is friction-free. */}
            <Route path="/fleet/unit/:unit_number" element={S(<FleetUnitThread />)} />
            {/* Phase V.5 · P0-2C — Shop pre-op visibility. The full pre-op list is
                now reachable from /shop/equipment (was previously buried as a
                disabled link in the ShopHub "More" footer). */}
            <Route path="/shop/equipment" element={S(<EquipmentDashboard />)} />
            <Route path="/shop/equipment/:id" element={S(<ViewEquipmentInspection context="shop" />)} />

            {/* ============================================================
                HR Portal — isolated read-only HR scope. Admin tokens do
                NOT satisfy these routes; HR users authenticate at
                /hr/login with their email + password and only see
                HR-scoped data (Field Leadership records, accountability,
                Daily-Report-derived time verification, training records).
                ============================================================ */}
            <Route path="/hr/login" element={<HrLogin />} />
            <Route path="/sign-in" element={<SignIn />} />
            <Route path="/change-password" element={<DirectoryChangePassword />} />
            <Route path="/hr/forgot" element={<HrForgotPassword />} />
            <Route path="/hr/reset/:token" element={<HrResetPassword />} />
            <Route path="/hr/change-password" element={H(<HrChangePassword />)} />
            {/* Track 13.6E · HR route swap — /hr now renders HrHubV2 (live · real APIs · zero-drift verified). Rollback path preserved at /hr/hub_legacy. */}
            <Route path="/hr" element={H(<HrHubV2 />)} />
            <Route path="/hr/hub_legacy" element={H(<HrHub />)} />
            {/* Track 13.6C · HR Hub V2 stable alias remains. */}
            <Route path="/hr/hub_v2" element={H(<HrHubV2 />)} />
            <Route path="/hr/field-leadership" element={H(<HrFieldLeadership />)} />
            <Route path="/hr/field-leadership-users" element={H(<HrFieldLeadershipUsers />)} />
            <Route path="/hr/employee-accountability" element={H(<HrEmployeeAccountability />)} />
            <Route path="/hr/time-verification" element={H(<HrTimeVerification />)} />
            <Route path="/hr/time-off" element={H(<HrTimeOff />)} />
            <Route path="/hr/payroll-variance" element={H(<HrPayrollVariance />)} />
            <Route path="/hr/training-records" element={H(<HrTrainingRecords />)} />
            <Route path="/hr/qualifications" element={H(<EmployeeLifecycleQualifications />)} />
            <Route path="/hr/driver-qualification" element={H(<HrDriverQualificationDashboard />)} />
            <Route path="/hr/driver-qualification/import" element={H(<HrDriverQualificationImport />)} />
            {/* iter332 · HR read-only Daily Reports Review.
                Track 15.13C — HR detail route now mounts the REAL
                `ViewDailyReport` component (the same view PM/admin
                use) so HR sees every field the field crew submitted
                — notes, photos, attachments, signatures, crews,
                subs, vendors — not the rebuilt summary that was
                shipping the broken "photo-0..3" placeholders. The
                read-only contract is enforced backend-side: HR's
                X-HR-Token is rejected on every mutating endpoint
                (`PATCH/DELETE/POST /api/daily-reports/*` and the
                office-review/print/email endpoints), so even without
                hiding the UI controls the user cannot mutate. UI
                guard for the mutation buttons lives in the same
                component via the `isHrReadOnly` pathname check
                added in 15.13C. */}
            <Route path="/hr/daily-reports" element={H(<HrDailyReports />)} />
            <Route path="/hr/daily-reports/:id" element={H(<ViewDailyReport />)} />
            {/* MCC-1 HR Access Extension · 2026-06-08 · HR-scoped driver cleanup */}
            <Route path="/hr/motive-drivers" element={H(<HrMotiveDrivers />)} />
            {/* DCP-1 · Driver Command Profile · per-portal landing */}
            <Route path="/hr/driver/:driverKey" element={H(<HrDriverProfile />)} />
            <Route path="/time-off/public/:token" element={<PublicTimeOff />} />

            {/* ============================================================
                Field Leadership Portal (iter314) · per-user governed identity.
                Distinct from /field-leadership/login which is the LEGACY
                shared-password document gate (preserved untouched).
                ============================================================ */}
            <Route path="/field-leadership/portal/login" element={<FieldLeadershipPortalLogin />} />
            <Route path="/field-leadership/portal/change-password" element={FL(<FieldLeadershipPortalChangePassword />)} />
            <Route path="/field-leadership/portal/dashboard" element={FL(<FieldLeadershipPortalDashboard />)} />
            <Route path="/field-leadership/portal" element={FL(<FieldLeadershipPortalDashboard />)} />
            {/* iter353b · FL read-only Driver Readiness view */}
            <Route path="/field-leadership/portal/driver-qualification" element={FL(<FieldLeadershipDriverQualification />)} />

            {/* ============================================================
                Safety Portal — isolated cyan-700 scope for Safety
                Manager / Coordinator / Officer. Independent JWT (X-Safety-Token);
                admin tokens do NOT satisfy these routes. Phase 1 ships
                overview KPIs (pulled from existing incident/inspection/
                meeting/leadership collections — no duplicate forms) and
                a corrective-action CRUD pipeline.
                ============================================================ */}
            <Route path="/safety-portal/login" element={<SafetyLogin />} />
            <Route path="/safety-portal/forgot-password" element={<SafetyForgotPassword />} />
            <Route path="/safety-portal/reset/:token" element={<SafetyResetPassword />} />
            <Route path="/safety-portal/change-password" element={SF(<SafetyChangePassword />)} />
            {/* Track 13.6I · Phase 4 — Safety route swap.
                /safety-portal → Safety Hub V2.
                /safety-portal/hub_legacy → classic Safety hub rollback.
                /safety-portal/hub_v2 alias preserved. */}
            <Route path="/safety-portal" element={SF(<SafetyHubV2 />)} />
            <Route path="/safety-portal/hub_legacy" element={SF(<SafetyHub />)} />
            <Route path="/safety-portal/hub_v2" element={SF(<SafetyHubV2 />)} />
            <Route path="/safety-portal/fleet" element={SF(<FleetVisibility scope="safety" />)} />
            <Route path="/safety-portal/corrective-actions" element={SF(<SafetyCorrectiveActions />)} />
            <Route path="/safety-portal/fire-extinguishers" element={SF(<SafetyFireExtinguishers />)} />
            <Route path="/safety-portal/fire-extinguishers/import" element={SF(<SafetyFireExtImport />)} />
            <Route path="/safety-portal/documents" element={SF(<SafetyDocuments />)} />
            <Route path="/safety-portal/training" element={SF(<SafetyTrainingRecords />)} />
            <Route path="/safety-portal/incidents" element={SF(<SafetyIncidents />)} />
            {/* SAFETY-CONTEXT-CERT (2026-06-15) · Safety users open incident
                detail in the Safety portal (was hardcoded to /admin/incidents/:id,
                which forced AdminShell + "Back to Admin Overview" copy).
                ViewIncident accepts X-Safety-Token via APS() already; here we
                wrap it in the Safety shell instead so the chrome is correct. */}
            <Route path="/safety-portal/incidents/:id" element={SF(<ViewIncident />)} />
            <Route path="/safety-portal/meetings/:id" element={SF(<ViewMeeting />)} />
            <Route path="/safety-portal/audits" element={SF(<SafetyAudits />)} />
            <Route path="/safety-portal/forms-records" element={SF(<SafetyFormsRecords />)} />
            <Route path="/safety-portal/reports" element={SF(<SafetyReports />)} />
            <Route path="/safety-portal/library" element={SF(<SafetyTopicLibrary />)} />
            <Route path="/safety-portal/employees" element={SF(<SafetyEmployeeProfiles />)} />
            <Route path="/safety-portal/digest" element={SF(<SafetyDigest />)} />
            {/* TRACK 14.0-DISCOVERABILITY · Wave B (2026-02-15) — Safety
                portal first-class entries for Site Inspections and JHA
                Plans. Both backends already accept X-Safety-Token via
                _read_gate; adding the SF-wrapped routes lets safety
                users list / review these records inside their portal
                shell instead of bouncing through AdminShell. */}
            <Route path="/safety-portal/inspections" element={SF(<Dashboard />)} />
            <Route path="/safety-portal/inspections/:id" element={SF(<ViewInspection />)} />
            <Route path="/safety-portal/jha-plans" element={SF(<JhaPlansAdmin />)} />
            {/* DCP-1 · Driver Command Profile · Safety scope */}
            <Route path="/safety-portal/driver/:driverKey" element={SF(<SafetyDriverProfile />)} />

            {/* HR cross-portal read-only safety view (uses X-HR-Token) */}
            <Route path="/hr/safety-records" element={H(<HrSafetyRecords />)} />

            {/* ============================================================
                Dispatch Portal — equipment movement command center.
                Mirrors Safety/HR/Shop/PM portal pattern.
                ============================================================ */}
            <Route path="/dispatch-portal/login" element={<DispatchLogin />} />
            {/* iter342 · /leadership/login now renders the MODERN per-user
                email+password portal (was iter314's FieldLeadershipPortalLogin,
                previously only reachable via /field-leadership/portal/login).
                This makes Field Leadership feel like part of the same platform
                family as HR / Safety / PM / Shop / Dispatch. */}
            <Route path="/leadership/login" element={<FieldLeadershipPortalLogin />} />
            <Route path="/dispatch-portal/forgot-password" element={<DispatchForgotPassword />} />
            <Route path="/dispatch-portal/reset/:token" element={<DispatchResetPassword />} />
            <Route path="/dispatch-portal/change-password" element={DP(<DispatchChangePassword />)} />
            {/* Track 13.6J · Dispatch Map Protection — REVERTED 13.6I swap.
                /dispatch-portal MUST keep the MapLibre operational map as the
                dominant operational surface. Dispatch Hub V2 remains available
                as a companion action-queue lane at /dispatch-portal/hub_v2 but
                does NOT replace the map-dominant classic surface. */}
            <Route path="/dispatch-portal" element={DP(<DispatchHub />)} />
            <Route path="/dispatch-portal/hub_legacy" element={DP(<DispatchHub />)} />
            <Route path="/dispatch-portal/hub_v2" element={DP(<DispatchHubV2 />)} />
            <Route path="/dispatch-portal/board" element={DP(<DispatchBoard />)} />
            <Route path="/dispatch-portal/command" element={DP(<DispatchCommandCenter />)} />
            <Route path="/dispatch-portal/fleet" element={DP(<><TransportationOpsTopBar /><FleetVisibility scope="dispatch" /></>)} />
            {/* TRACK 15.81 — Dispatch-owned alias for the Live Operations Map.
                Same `OperationsMapPage` component rendered under `RequireDispatch`
                so Dispatch users (and Super Admins signed in via Dispatch) can
                drill into asset detail / counts / "Open Full Live Map" without
                being thrown into the Admin Console route and getting a 403.
                Backend `/api/operations-map/*` already accepts any portal token
                (see make_require_any_portal_token), so no RBAC was broadened.
                TRACK 15.82 — Page now rendered through `DispatchOperationsMapPage`
                which wraps the same canvas with a Dispatch-themed breadcrumb so
                the "Back to Dispatch Hub" affordance is always visible. The
                Admin route `/operations-map` keeps the bare page. */}
            <Route path="/dispatch-portal/map" element={DP(<DispatchOperationsMapPage />)} />
            {/* Track 13.21 · Phase C · Material Movement Ledger · Dispatch Companion.
                Companion-only · OUTSIDE MapLibre canvas. /dispatch-portal remains map-first. */}
            <Route path="/dispatch-portal/haul-ledger" element={DP(<DispatchHaulLedger />)} />
            {/* iter353b · Dispatch read-only Approved Drivers / CDL Readiness */}
            <Route path="/dispatch-portal/driver-qualification" element={DP(<DispatchDriverQualification />)} />
            {/* DCP-1 · Driver Command Profile · Dispatch scope */}
            <Route path="/dispatch-portal/driver/:driverKey" element={DP(<DispatchDriverProfile />)} />

            {/* ============================================================
                Training Hub — landing is public, tracks gate per audience
                (Field public, Shop/PM/Admin each require their own token).
                Admin video URL manager lives behind /admin/training-videos.
                ============================================================ */}
            <Route path="/training" element={<TrainingHub />} />
            <Route path="/training-hub" element={<Navigate to="/training" replace />} />
            <Route path="/training/:track" element={<TrainingTrack />} />
            <Route path="/training/:track/poster" element={<TrainingQrPoster />} />
            <Route path="/training/:track/packet" element={<TrainingPacketDownload />} />
            <Route path="/admin/training-videos" element={A(<AdminTrainingVideos />)} />
            <Route path="/admin/deploy-readiness" element={A(LB("/admin/deploy-readiness", <AdminDeployReadiness />))} />

            {/* ============================================================
                Operations Training Center — system-wide operator guides
                (distinct from /training which is field-worker tracks).
                Public-read so any user in any portal can reach it.
                ============================================================ */}
            {/* ============================================================
                /ops-training — retired iter195. Was a duplicate, unrestricted
                operator-training surface ("public-read, no auth required").
                Operator directive: ONE coherent guidance ecosystem with
                strict RBAC. /ops-training and /ops-training/:slug now
                redirect to the unified Operational Guidance Center which
                inherits portal-access boundaries.
                ============================================================ */}
            <Route path="/ops-training" element={<Navigate to="/guidance" replace />} />
            <Route path="/ops-training/:slug" element={<Navigate to="/guidance" replace />} />

            {/* ============================================================
                Developer Portal — ForgedOps™ vendor-internal only.
                Hidden behind a tiny "Developer" link in the Hub footer;
                password-gated with X-Dev-Token (distinct namespace from
                admin/PM/shop tokens). Houses the System Owner & Operations
                Manual + snapshot archive. NOT visible to MASCI staff.
                ============================================================ */}
            <Route path="/dev/login" element={<DevLogin />} />
            <Route path="/dev" element={D(<DevHub />)} />

            {/* Legacy redirects */}
            <Route path="/inspections" element={<Navigate to="/admin/inspections" replace />} />
            <Route path="/inspect/:id" element={<RedirectWithId base="/admin/inspections" />} />
            <Route path="/inspections/:id" element={<RedirectWithId base="/admin/inspections" />} />
            <Route path="/meetings" element={<Navigate to="/admin/meetings" replace />} />
            <Route path="/meetings/:id" element={<RedirectWithId base="/admin/meetings" />} />
            <Route path="/incidents" element={<Navigate to="/admin/incidents" replace />} />
            <Route path="/incidents/:id" element={<RedirectWithId base="/admin/incidents" />} />
            <Route path="/daily" element={<Navigate to="/admin/daily" replace />} />
            <Route path="/daily/:id" element={<RedirectWithId base="/admin/daily" />} />
            {/* TRACK 14.0-ELITE-OPS-B · 5:30 AM iPad usability redirects (iter510)
                A tired user types the natural URL — don't 404, send them home.
                TRACK 14.0-DISCOVERABILITY (2026-02-15) — two of these landed users
                on AccessDenied because the destination guard rejected their portal
                token. Replaced with portal-correct destinations:
                  · /safety-portal/meetings is now a real SF-guarded list (was
                    redirecting to /admin/meetings which only AP-accepts).
                  · /admin/daily-reports now redirects to /admin/daily (was
                    redirecting to /hr/daily-reports which rejected admin tokens). */}
            <Route path="/safety-portal/meetings" element={SF(<MeetingsDashboard />)} />
            <Route path="/admin/daily-reports" element={<Navigate to="/admin/daily" replace />} />
            <Route path="/admin/trench-safety-assets" element={<Navigate to="/safety/trench-safety/assets" replace />} />

            {/* Legal */}
            <Route path="/legal/terms" element={<TermsOfService />} />
            <Route path="/legal/privacy" element={<PrivacyPolicy />} />

            {/* Tasks & Actions — Iter150 (Phase 2.5 · Phase A) ──────
                Shared accountability engine. Route is open to any
                signed-in portal user; the Tasks page itself shows
                AccessDenied to fully-anonymous visitors. */}
            <Route path="/tasks" element={<Tasks />} />
            {/* Document Expirations — Iter151 (Phase 2.5 · Phase B) */}
            <Route path="/document-expirations" element={<DocumentExpirations />} />
            {/* HR Employee Lifecycle — Iter152 (Phase 2.5 · Phase C) */}
            <Route path="/hr/employees" element={H(<HrEmployees />)} />
            {/* OMEGA · Employee Governance Phase Alpha · G-5 · HR Queue */}
            <Route path="/hr/employee-requests" element={H(<HrEmployeeRequestsQueue />)} />
            {/* iter353c · Unified Employee Accountability Timeline (HR + Safety + Admin)
                The component does its own multi-role auth check (no H/SF wrapper). */}
            <Route path="/hr/employees/:id/accountability" element={H(<HrEmployeeAccountabilityTimeline />)} />
            {/* Track 19.56 · Promoted Universal Operational Thread view.
               Renders the SAME certified accountability payload through
               the Track 19.55 OperationalThreadPage shell. Auth = same
               HR + Safety + Admin gate. Zero backend change. */}
            <Route path="/hr/employees/:id/thread" element={H(<HrEmployeeThread />)} />
            {/* Track 19.21 · Employee 360° · single-page consolidated profile */}
            <Route path="/hr/employees/:empId/profile" element={H(<EmployeeProfile />)} />
            {/* Track 19.21b · Historical Records Intake + Review Queue */}
            <Route path="/hr/historical-records/intake" element={H(<HistoricalRecordsIntake />)} />
            <Route path="/hr/historical-records/queue" element={H(<HistoricalRecordsQueue />)} />
            {/* Track 19.22 · Bulk Batches */}
            <Route path="/hr/historical-records/batches" element={H(<HistoricalRecordsBatches />)} />
            <Route path="/hr/historical-records/batches/:batchId" element={H(<HistoricalRecordsBatchDetail />)} />
            {/* iter353f · HR OSHA & Labor — read-only incidents list */}
            <Route path="/hr/incidents" element={H(<HrIncidents />)} />
            {/* PO Requests — Iter153 (Phase 2.5 · Phase D) */}
            <Route path="/po-requests" element={<PoRequests />} />
            {/* Project Health — Phase H · per-project friction view.
                Server-side role gate (403 for HR/Shop/Dispatch/FL). */}
            <Route path="/project-health" element={<ProjectHealth />} />
            {/* Asset Transfers — Phase I · lifecycle events keyed to
                equipment_master. Reuses Tasks · Notifications ·
                Signatures · Audit · PM scope. */}
            <Route path="/asset-transfers" element={<AssetTransfers />} />
            {/* Fallback — explicit 403 for any path we deliberately
                want to land on AccessDenied (kept hidden, used by
                tooling/diagnostics). */}
            <Route path="/access-denied" element={<AccessDenied />} />
            {/* Iter181 — UX consistency fixes (production verification 2026-05-17).
                Three legitimate-but-mistyped URLs previously rendered a
                blank-shell because no React Router pattern matched. Alias
                them to the canonical route so accidental tabs / external
                links / muscle-memory typos land somewhere real instead of
                an empty page. Each alias preserves the existing route's
                authorization gate — these are display redirects only. */}
            <Route path="/admin/audit" element={<Navigate to="/admin/audit-log" replace />} />
            <Route path="/admin/health" element={<Navigate to="/admin/system-health" replace />} />
            {/* iter393 · DLS Driver Mobile Surface — magic-link entry */}
            <Route path="/d/:token" element={<DriverMagicLanding />} />
            <Route path="/driver" element={<DriverShift />} />
            {/* Track 13.6L — /driver/hub_v2 RETIRED. Existing /shift + /d/:token + /driver
                already satisfy ≤ 2 taps / ≤ 30 seconds. Hub layer added friction · no operational lift. */}
            {/* iter401 · Phase 12.8 · Driver self-start operational entry */}
            <Route path="/shift" element={<ShiftStart />} />
            <Route path="/field-leadership" element={<Navigate to="/leadership" replace />} />
            {/* Phase V.1 · M0.3 · ODR surfaces. Public viewer is intentionally
                no-auth — the continuity engine gates access by doc_id + link_id. */}
            <Route path="/odr/new" element={<OdrNew />} />
            <Route path="/odr/center" element={<OdrCenter />} />
            <Route path="/pm/odr" element={P(<OdrPmPanel />)} />
            <Route path="/odr/public/:doc_id" element={<OdrPublicViewer />} />
            <Route path="/odr/:id/done" element={<OdrDone />} />
            <Route path="/odr/:id" element={<OdrDetail />} />
            {/* Phase V.1 · M1 · Option C · Unified Operational Records dashboard.
                One search · one timeline across ODR + frozen Daily Reports.
                Doctrine: M1_OPTION_C_IMPLEMENTATION_PLAN.md */}
            <Route path="/operational-records" element={<OperationalRecords />} />
            {/* OA-1 · Operations Actions · cross-portal CRUD coordination layer.
                Doctrine: OA1_OPERATIONS_ACTIONS_CONSTITUTION.md */}
            <Route path="/operations-actions" element={<OperationsActions />} />
            <Route path="/operations-actions/new" element={<OperationsActionNew />} />
            <Route path="/operations-actions/:id" element={<OperationsActionDetail />} />
            {/* Catch-all — any path that doesn't match an explicit route
                renders the 404 NotFound page (Iter181). Previously such
                URLs rendered only the global navbar + footer with an
                empty middle (the "blank shell" the production
                verification sweep flagged). Backend authorization is
                untouched; this is purely the unmatched-route UX. */}
            {/* Pass-7 · Design-system family mockups removed (unauthorized direction; reverted per operator stabilization directive) */}
            {/* Track 13.5A · Phase B1 — Internal-only design primitives showcase.
                Mounted under `_internal` to keep it out of operator nav. No links exist
                pointing here from any portal. Authorized 2026-02 by operator.
                Track 14.0-A1 · 2026-06-13 — wrapped in RequireDev() so that URL-guessing
                does not expose the showcase / V2 previews / comparison views to
                non-developers. Dev-token holders are unaffected. */}
            <Route path="/_internal/design-system" element={D(<DesignSystemDemo />)} />
            <Route path="/_internal/pm-v2-preview" element={D(<PmV2Preview />)} />
            <Route path="/_internal/hr-v2-preview" element={D(<HrV2Preview />)} />
            <Route path="/_internal/v2-index" element={D(<V2Index />)} />
            <Route path="/_internal/v2-compare/:portal" element={D(<V2Compare />)} />
            {/* DR-UNIFY-003 · internal-only Daily Report shell RETIRED. Any old link
                lands on the single canonical Daily Report at /daily/submit. */}
            <Route path="/daily-report/v2" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/daily/v1" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/daily/v2" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/daily/v3" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/daily-report/v1" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/daily-report/v3" element={<Navigate to="/daily/submit" replace />} />
            <Route path="/pm/operational-intelligence" element={<PmOperationalIntelligence />} />
            {/* DR-UNIFY-002 · orphaned duplicate collapsed into canonical Admin OI. */}
            <Route path="/admin/ods-intelligence" element={<Navigate to="/admin/operational-intelligence" replace />} />
            {/* DR-UNIFY-002 · speculative Executive surface — no real Executive Portal exists.
                Deferred to a future track. Redirected to Admin OI so any old link stays useful. */}
            <Route path="/executive/ods-intelligence" element={<Navigate to="/admin/operational-intelligence" replace />} />
            {/* TRACK 28.08 · Phase 0 · D1-ROUTE-OCC-404 — legacy alias for Operations Control Center.
                `/admin/occ` was historically documented but never routed; preserve bookmarks by
                redirecting to the canonical `/admin/operations-control`. Query params and hashes
                pass through automatically because Router matches the pathname only. */}
            <Route path="/admin/occ" element={<Navigate to="/admin/operations-control" replace />} />
            {/* TRACK 28.08 · Phase 0 · D2-ROUTE-EXECUTIVE-404 — legacy aliases for Executive Overview.
                `/executive`, `/executive-dashboard`, and `/admin/executive` all resolve to the
                canonical `/admin/executive-overview`. Preserves historical deep links. */}
            <Route path="/executive" element={<Navigate to="/admin/executive-overview" replace />} />
            <Route path="/executive-dashboard" element={<Navigate to="/admin/executive-overview" replace />} />
            <Route path="/admin/executive" element={<Navigate to="/admin/executive-overview" replace />} />
            {/* TRACK 28.08 · Phase 15 · additional legacy aliases discovered
                during the full device walk. `/fleet` had no root — align it
                with the Dispatch surface that owns fleet ops. `/admin/ai` and
                `/admin/storage` are historical shorthands for the canonical
                admin-domain landings. `/fl` is the shorthand for Field
                Leadership. All use Navigate replace so bookmarks continue
                to work without duplicating routes. */}
            <Route path="/fleet" element={<Navigate to="/dispatch-portal" replace />} />
            <Route path="/admin/ai" element={<Navigate to="/admin/ai-operations" replace />} />
            <Route path="/admin/storage" element={<Navigate to="/admin/storage-recovery" replace />} />
            <Route path="/fl" element={<Navigate to="/leadership" replace />} />
            <Route path="*" element={<NotFound />} />
            {/* (catch-all is final) */}
          </Routes></React.Suspense>
  );
}

function RedirectWithId({ base }) {
  const id = window.location.pathname.split("/").filter(Boolean).pop();
  // Track 15.12A · preserve `location.state` across this synthetic
  // redirect — without `state={location.state}` the `<Navigate replace>`
  // discards the caller's navigation context (used by PM photo lightbox
  // to set `{from:"pm-photos"}` so the daily-report back button can
  // return to /pm/command-center).
  return <Navigate to={`${base}/${id}`} replace state={window.history.state?.usr} />;
}
