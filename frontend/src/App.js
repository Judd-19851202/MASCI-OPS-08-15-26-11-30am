import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
// AuthProvider removed 2026-04-28 — Crew Hub scrapped.
import Hub from "@/pages/Hub";
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
import NewIncident from "@/pages/NewIncident";
import ViewIncident from "@/pages/ViewIncident";
import DailyReportsDashboard from "@/pages/DailyReportsDashboard";
import NewDailyReport from "@/pages/NewDailyReport";
import ViewDailyReport from "@/pages/ViewDailyReport";
import EquipmentDashboard from "@/pages/EquipmentDashboard";
import NewEquipmentInspection from "@/pages/NewEquipmentInspection";
import NewFleetDVIR from "@/pages/NewFleetDVIR";
import FleetDVIRConfirmation from "@/pages/FleetDVIRConfirmation";
import FleetVisibility from "@/pages/FleetVisibility";
import ViewEquipmentInspection from "@/pages/ViewEquipmentInspection";
import AdminLogin from "@/pages/AdminLogin";
import AdminHub from "@/pages/AdminHub";
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
const AdminPeople = React.lazy(() => import("@/pages/admin/AdminPeople"));
const AdminMfa = React.lazy(() => import("@/pages/admin/AdminMfa"));
const AdminPromoAssets = React.lazy(() => import("@/pages/admin/AdminPromoAssets"));
const AdminJobs = React.lazy(() => import("@/pages/admin/AdminJobs"));
const AdminGeofenceReconciliation = React.lazy(() => import("@/pages/admin/AdminGeofenceReconciliation"));
const AdminOperationsDashboard = React.lazy(() => import("@/pages/admin/AdminOperationsDashboard"));
const AdminAssetMapping = React.lazy(() => import("@/pages/admin/AdminAssetMapping"));
// FORGEDOPS-P0.1 · Asset Spine Health dashboard.
const AdminAssetSpineHealth = React.lazy(() => import("@/pages/admin/AdminAssetSpineHealth"));
const AdminEquipment = React.lazy(() => import("@/pages/admin/AdminEquipment"));
const AdminEmail = React.lazy(() => import("@/pages/admin/AdminEmail"));
const AdminTraining = React.lazy(() => import("@/pages/admin/AdminTraining"));
const AdminCompliance = React.lazy(() => import("@/pages/admin/AdminCompliance"));
const AdminSystem = React.lazy(() => import("@/pages/admin/AdminSystem"));
const AdminDatabase = React.lazy(() => import("@/pages/admin/AdminDatabase"));
const AdminIntegrationCenter = React.lazy(() => import("@/pages/admin/AdminIntegrationCenter"));
const AssetProfile = React.lazy(() => import("@/pages/admin/AssetProfile"));
const AdminDriverIntel = React.lazy(() => import("@/pages/admin/AdminDriverIntel"));
const AdminDispatch = React.lazy(() => import("@/pages/admin/AdminDispatch"));
const AdminDlsShiftQR = React.lazy(() => import("@/pages/admin/AdminDlsShiftQR"));
const AdminDlsDay1Debrief = React.lazy(() => import("@/pages/admin/AdminDlsDay1Debrief"));
const AdminProfile = React.lazy(() => import("@/pages/admin/AdminProfile"));
const AdminOperationsEvents = React.lazy(() => import("@/pages/admin/AdminOperationsEvents"));
const AdminDigestConfig = React.lazy(() => import("@/pages/admin/AdminDigestConfig"));
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
const HrIncidents = React.lazy(() => import("@/pages/HrIncidents"));
const HrTrainingRecords = React.lazy(() => import("@/pages/HrTrainingRecords"));
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
const PmHomeRedirect = React.lazy(() => import("@/pages/PmHomeRedirect"));
import AccessDenied from "@/pages/AccessDenied";
import NotFound from "@/pages/NotFound";
import GlobalFooter from "@/components/GlobalFooter";
import ScrollToTop from "@/components/ScrollToTop";
import { RequireAdmin } from "@/components/RequireAdmin";
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
import { validateStoredTokens } from "@/lib/tokenValidation";
import EnforcePortalScope from "@/components/EnforcePortalScope";
import MultiPortalHydrator from "@/components/MultiPortalHydrator";
import IdleTimeout from "@/components/IdleTimeout";
import PosterErrorBoundary from "@/components/PosterErrorBoundary";

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

const A = (el) => <RequireAdmin>{el}</RequireAdmin>;
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

function App() {
  // Validate any locally-stored auth tokens against the backend on app
  // load. If a password got rotated (or the HMAC secret changed) the
  // user's old token no longer works server-side — but `isAdmin()` etc.
  // only check for presence, so the UI keeps rendering gated surfaces
  // as "unlocked". We ping the four /check endpoints once, clear any
  // token the backend rejects with 401, then bump `authTick` so the
  // router fully remounts and every page re-reads localStorage.
  const [authTick, setAuthTick] = React.useState(0);
  React.useEffect(() => {
    let mounted = true;
    validateStoredTokens().then((cleared) => {
      if (mounted && cleared) setAuthTick((t) => t + 1);
    });
    // iter146 — wire fire-and-forget usage analytics. Safe to call
    // multiple times (the binder guards itself with a one-shot flag).
    import("@/lib/usageTracker").then(({ bindRouteChangeTracker }) => {
      bindRouteChangeTracker();
    }).catch(() => { /* silent */ });
    // iter166 — Phase J · purge stale (>14d) IndexedDB drafts on boot.
    // Fire-and-forget, never blocks app render.
    import("@/lib/resiliency").then(({ purgeStaleDrafts }) => {
      purgeStaleDrafts();
    }).catch(() => { /* silent */ });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="App min-h-screen flex flex-col">
      <SplashOverlay />
      <Toaster position="bottom-right" richColors closeButton offset={16} />
      {/* R-BL-3 · Global queue visibility pill (visibility-only). */}
      <QueueStatusPill />
      <GlobalKeepalive />
      <BackendStatusBanner />
      <ClusterCapacityBanner />
      <EnvBanner />
      <BannerStrip />
      <BrowserRouter key={authTick}>
        <ScrollToTop />
        <EnforcePortalScope />
        <MultiPortalHydrator />
        <IdleTimeout />
        {/* TRUST-DIAGNOSTICS-001 · Global session/error overlay.
            Mounted inside BrowserRouter so it can read location +
            navigate to the right login route on "Log Back In". */}
        <SessionStatusOverlay />
        <div className="flex-1 flex flex-col">
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
            <Route path="/admin/qaqc" element={<AdminQaqcList />} />
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

            <Route path="/incidents/new" element={<NewIncident />} />
            <Route path="/incidents/submit" element={<NewIncident publicMode />} />

            <Route path="/daily/new" element={<NewDailyReport />} />
            <Route path="/daily/submit" element={<NewDailyReport publicMode />} />

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
            <Route path="/reports/daily/new" element={<Navigate to="/daily/new" replace />} />
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
            <Route path="/admin" element={A(<AdminHub />)} />
            <Route path="/admin/people" element={A(<AdminPeople />)} />
            <Route path="/admin/mfa" element={A(<AdminMfa />)} />
            <Route path="/admin/promo-assets" element={A(<AdminPromoAssets />)} />
            <Route path="/admin/jobs" element={A(<AdminJobs />)} />
            {/* M-3 · Geocode Foundation · Motive Geofence Reconciliation */}
            <Route path="/admin/geofence-reconciliation" element={A(<AdminGeofenceReconciliation />)} />
            {/* M-2 · Event Router · Operations dashboard (visibility only) */}
            <Route path="/admin/operations-dashboard" element={A(<AdminOperationsDashboard />)} />
            {/* MOTIVE-DATA-002 · Asset Mapping Admin Center */}
            <Route path="/admin/asset-mapping" element={A(<AdminAssetMapping />)} />
            <Route path="/admin/asset-spine" element={A(<AdminAssetSpineHealth />)} />
            <Route path="/admin/equipment" element={A(<AdminEquipment />)} />
            <Route path="/admin/email" element={A(<AdminEmail />)} />
            <Route path="/admin/training" element={A(<AdminTraining />)} />
            <Route path="/admin/compliance" element={A(<AdminCompliance />)} />
            <Route path="/admin/system" element={A(<AdminSystem />)} />
            <Route path="/admin/recovery" element={A(<AdminRecovery />)} />
            <Route path="/admin/recovery-stream" element={A(<AdminRecoveryStream />)} />
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
            <Route path="/admin/system-health" element={A(<SystemHealth />)} />
            <Route path="/admin/audit-log" element={A(<AdminAuditLog />)} />
            {/* iter445 · F-003 · operator-visible scheduler/digest history */}
            <Route path="/admin/scheduler-runs" element={A(<AdminSchedulerRuns />)} />
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
            <Route path="/admin/deploy-recovery" element={A(<DeployRecovery />)} />
            <Route path="/admin/assets/:assetId" element={A(<AssetProfile />)} />
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

            <Route path="/admin/incidents" element={AP(<IncidentsDashboard />)} />
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
            <Route path="/pm/hub" element={P(<PmHub />)} />
            {/* Track 13.6D · PM Hub V2 lives side-by-side with /pm/hub · same RequirePm auth · NO route swap. */}
            <Route path="/pm/hub_v2" element={P(<PmHubV2 />)} />
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
            {/* PM Command Center · Phase 4B · 2026-02-10.
                Backed by /api/pm/command-center/* (Phase 4A). One
                page · seven tabs · iPad-friendly. */}
            <Route path="/pm/command-center" element={P(<PmCommandCenter />)} />
            {/* Operations Center · Phase 4C · 2026-02-10.
                Cross-company command board · 9 layers · Specialty
                Asset normalization · backed by /api/operations-center/
                command/* (admin / any portal token). */}
            <Route path="/operations-center" element={A(<OperationsCenterCommand />)} />
            <Route path="/operations-map" element={A(<OperationsMapPage />)} />
            <Route path="/pm/field-leadership"   element={P(<PmFieldLeadership />)} />
            <Route path="/pm/fleet"              element={P(<PmFleet />)} />
            <Route path="/pm/people"             element={P(<PmPeople />)} />
            <Route path="/pm/suppliers"          element={P(<PmSuppliers />)} />
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
            {/* /pm/pnl removed 2026-05-07 per Justin — owners want P&L kept admin-only */}

            {/* ============================================================
                Shop Console — mechanics-only view, separate password
                ============================================================ */}
            <Route path="/shop/login" element={<ShopLogin />} />
            <Route path="/shop/reset/:token" element={<ShopResetPassword />} />
            <Route path="/shop/change-password" element={S(<ShopChangePassword />)} />
            <Route path="/shop" element={S(<ShopHub />)} />
            <Route path="/shop/trench-safety-repairs" element={S(<ShopTrenchSafetyRepairs />)} />
            <Route path="/shop/fleet" element={S(<FleetVisibility scope="shop" />)} />
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
            <Route path="/hr/forgot" element={<HrForgotPassword />} />
            <Route path="/hr/reset/:token" element={<HrResetPassword />} />
            <Route path="/hr/change-password" element={H(<HrChangePassword />)} />
            <Route path="/hr" element={H(<HrHub />)} />
            {/* Track 13.6C · HR Hub V2 lives side-by-side with /hr · same RequireHr auth gate · NO route swap. */}
            <Route path="/hr/hub_v2" element={H(<HrHubV2 />)} />
            <Route path="/hr/field-leadership" element={H(<HrFieldLeadership />)} />
            <Route path="/hr/field-leadership-users" element={H(<HrFieldLeadershipUsers />)} />
            <Route path="/hr/employee-accountability" element={H(<HrEmployeeAccountability />)} />
            <Route path="/hr/time-verification" element={H(<HrTimeVerification />)} />
            <Route path="/hr/time-off" element={H(<HrTimeOff />)} />
            <Route path="/hr/payroll-variance" element={H(<HrPayrollVariance />)} />
            <Route path="/hr/training-records" element={H(<HrTrainingRecords />)} />
            <Route path="/hr/driver-qualification" element={H(<HrDriverQualificationDashboard />)} />
            <Route path="/hr/driver-qualification/import" element={H(<HrDriverQualificationImport />)} />
            {/* iter332 · HR read-only Daily Reports Review */}
            <Route path="/hr/daily-reports" element={H(<HrDailyReports />)} />
            <Route path="/hr/daily-reports/:id" element={H(<HrDailyReportDetail />)} />
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
            <Route path="/safety-portal" element={SF(<SafetyHub />)} />
            <Route path="/safety-portal/fleet" element={SF(<FleetVisibility scope="safety" />)} />
            <Route path="/safety-portal/corrective-actions" element={SF(<SafetyCorrectiveActions />)} />
            <Route path="/safety-portal/fire-extinguishers" element={SF(<SafetyFireExtinguishers />)} />
            <Route path="/safety-portal/fire-extinguishers/import" element={SF(<SafetyFireExtImport />)} />
            <Route path="/safety-portal/documents" element={SF(<SafetyDocuments />)} />
            <Route path="/safety-portal/training" element={SF(<SafetyTrainingRecords />)} />
            <Route path="/safety-portal/incidents" element={SF(<SafetyIncidents />)} />
            <Route path="/safety-portal/audits" element={SF(<SafetyAudits />)} />
            <Route path="/safety-portal/forms-records" element={SF(<SafetyFormsRecords />)} />
            <Route path="/safety-portal/reports" element={SF(<SafetyReports />)} />
            <Route path="/safety-portal/library" element={SF(<SafetyTopicLibrary />)} />
            <Route path="/safety-portal/employees" element={SF(<SafetyEmployeeProfiles />)} />
            <Route path="/safety-portal/digest" element={SF(<SafetyDigest />)} />
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
                family as HR / Safety / PM / Shop / Dispatch.
                Legacy shared-password gate is preserved at /leadership/legacy-login
                for crews that still know only the shared MASCIGC code; the
                backend /api/field-leadership/login route is untouched. */}
            <Route path="/leadership/login" element={<FieldLeadershipPortalLogin />} />
            <Route path="/leadership/legacy-login" element={<LeadershipLogin />} />
            <Route path="/dispatch-portal/forgot-password" element={<DispatchForgotPassword />} />
            <Route path="/dispatch-portal/reset/:token" element={<DispatchResetPassword />} />
            <Route path="/dispatch-portal/change-password" element={DP(<DispatchChangePassword />)} />
            <Route path="/dispatch-portal" element={DP(<DispatchHub />)} />
            <Route path="/dispatch-portal/board" element={DP(<DispatchBoard />)} />
            <Route path="/dispatch-portal/command" element={DP(<DispatchCommandCenter />)} />
            <Route path="/dispatch-portal/fleet" element={DP(<FleetVisibility scope="dispatch" />)} />
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
            <Route path="/admin/deploy-readiness" element={A(<AdminDeployReadiness />)} />

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
            <Route path="/hr/employees" element={<HrEmployees />} />
            {/* OMEGA · Employee Governance Phase Alpha · G-5 · HR Queue */}
            <Route path="/hr/employee-requests" element={H(<HrEmployeeRequestsQueue />)} />
            {/* iter353c · Unified Employee Accountability Timeline (HR + Safety + Admin)
                The component does its own multi-role auth check (no H/SF wrapper). */}
            <Route path="/hr/employees/:id/accountability" element={<HrEmployeeAccountabilityTimeline />} />
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
            {/* iter401 · Phase 12.8 · Driver self-start operational entry */}
            <Route path="/shift" element={<ShiftStart />} />
            <Route path="/field-leadership" element={<Navigate to="/leadership" replace />} />
            {/* Phase V.1 · M0.3 · ODR surfaces. Public viewer is intentionally
                no-auth — the continuity engine gates access by doc_id + link_id. */}
            <Route path="/odr/new" element={<OdrNew />} />
            <Route path="/odr/center" element={<OdrCenter />} />
            <Route path="/pm/odr" element={<OdrPmPanel />} />
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
                pointing here from any portal. Authorized 2026-02 by operator. */}
            <Route path="/_internal/design-system" element={<DesignSystemDemo />} />
            <Route path="/_internal/pm-v2-preview" element={<PmV2Preview />} />
            <Route path="/_internal/hr-v2-preview" element={<HrV2Preview />} />
            <Route path="/_internal/v2-index" element={<V2Index />} />
            <Route path="/_internal/v2-compare/:portal" element={<V2Compare />} />
            <Route path="*" element={<NotFound />} />
            {/* (catch-all is final) */}
          </Routes></React.Suspense>
          <GlobalFooter />
        </div>
      </BrowserRouter>
    </div>
  );
}

function RedirectWithId({ base }) {
  const id = window.location.pathname.split("/").filter(Boolean).pop();
  return <Navigate to={`${base}/${id}`} replace />;
}

export default App;
