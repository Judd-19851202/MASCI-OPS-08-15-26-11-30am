import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
// AuthProvider removed 2026-04-28 — Crew Hub scrapped.
import Hub from "@/pages/Hub";
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
import NewInspection from "@/pages/NewInspection";
import ViewInspection from "@/pages/ViewInspection";
import ThankYou from "@/pages/ThankYou";
import MeetingsDashboard from "@/pages/MeetingsDashboard";
import NewMeeting from "@/pages/NewMeeting";
import ViewMeeting from "@/pages/ViewMeeting";
import JhaPlansHub from "@/pages/JhaPlansHub";
import JhaPlansAdmin from "@/pages/JhaPlansAdmin";
import TrenchBoxes from "@/pages/TrenchBoxes";
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
import AdminGuide from "@/pages/AdminGuide";
import AdminLeadershipEquipment from "@/pages/AdminLeadershipEquipment";
import AdminTerminations from "@/pages/AdminTerminations";
import ProjectPnlPage from "@/pages/ProjectPnlPage";
import PmLogin from "@/pages/PmLogin";
import PmChangePassword from "@/pages/PmChangePassword";
import PmResetPassword from "@/pages/PmResetPassword";
import PmHub from "@/pages/PmHub";
import PmFieldLeadership from "@/pages/PmFieldLeadership";
import {
  PmJobs, PmFleet, PmPeople, PmSuppliers, PmPosters, PmRouting, PmComplianceExport,
} from "@/pages/pm/PmSections";
import PmQaqcList from "@/pages/PmQaqcList";
import ShopLogin from "@/pages/ShopLogin";
import ShopHub from "@/pages/ShopHub";
import ShopChangePassword from "@/pages/ShopChangePassword";
import ShopResetPassword from "@/pages/ShopResetPassword";
import HrLogin from "@/pages/HrLogin";
import SignIn from "@/pages/SignIn";
import AdminPeople from "@/pages/admin/AdminPeople";
import AdminJobs from "@/pages/admin/AdminJobs";
import AdminEquipment from "@/pages/admin/AdminEquipment";
import AdminEmail from "@/pages/admin/AdminEmail";
import AdminTraining from "@/pages/admin/AdminTraining";
import AdminCompliance from "@/pages/admin/AdminCompliance";
import AdminSystem from "@/pages/admin/AdminSystem";
import AdminIntegrationCenter from "@/pages/admin/AdminIntegrationCenter";
import AssetProfile from "@/pages/admin/AssetProfile";
import AdminDispatch from "@/pages/admin/AdminDispatch";
import AdminOperationsEvents from "@/pages/admin/AdminOperationsEvents";
import AdminDigestConfig from "@/pages/admin/AdminDigestConfig";
import SystemHealth from "@/pages/admin/SystemHealth";
import AdminAuditLog from "@/pages/admin/AdminAuditLog";
import AdminLegacyImports from "@/pages/AdminLegacyImports";
import AdminSessions from "@/pages/admin/AdminSessions";
import AdminGuidanceCoverage from "@/pages/admin/AdminGuidanceCoverage";
import AdminOperationalInventory from "@/pages/admin/AdminOperationalInventory";
import OperationalGuidanceCenter from "@/pages/guidance/OperationalGuidanceCenter";
import DeployRecovery from "@/pages/admin/DeployRecovery";
import AdminMasterHistory from "@/pages/admin/AdminMasterHistory";
import AdminAnalytics from "@/pages/admin/AdminAnalytics";
import HrHub from "@/pages/HrHub";
import HrChangePassword from "@/pages/HrChangePassword";
import HrResetPassword from "@/pages/HrResetPassword";
import HrForgotPassword from "@/pages/HrForgotPassword";
import HrTimeVerification from "@/pages/HrTimeVerification";
import HrFieldLeadership from "@/pages/HrFieldLeadership";
import HrEmployeeAccountability from "@/pages/HrEmployeeAccountability";
import HrTrainingRecords from "@/pages/HrTrainingRecords";
import HrPayrollVariance from "@/pages/HrPayrollVariance";
import HrDriverQualificationDashboard from "@/pages/HrDriverQualificationDashboard";
import HrTimeOff from "@/pages/HrTimeOff";
import PublicTimeOff from "@/pages/PublicTimeOff";
import SafetyLogin from "@/pages/SafetyLogin";
import DispatchLogin from "@/pages/DispatchLogin";
import LeadershipLogin from "@/pages/LeadershipLogin";
import DispatchHub from "@/pages/DispatchHub";
import DispatchChangePassword from "@/pages/DispatchChangePassword";
import DispatchForgotPassword from "@/pages/DispatchForgotPassword";
import DispatchResetPassword from "@/pages/DispatchResetPassword";
import SafetyHub from "@/pages/SafetyHub";
import SafetyChangePassword from "@/pages/SafetyChangePassword";
import SafetyForgotPassword from "@/pages/SafetyForgotPassword";
import SafetyResetPassword from "@/pages/SafetyResetPassword";
import SafetyCorrectiveActions from "@/pages/SafetyCorrectiveActions";
import SafetyFireExtinguishers from "@/pages/SafetyFireExtinguishers";
import SafetyFireExtImport from "@/pages/SafetyFireExtImport";
import SafetyDocuments from "@/pages/SafetyDocuments";
import SafetyTrainingRecords from "@/pages/SafetyTrainingRecords";
import SafetyEmployeeProfiles from "@/pages/SafetyEmployeeProfiles";
import SafetyDigest from "@/pages/SafetyDigest";
import SafetyIncidents from "@/pages/SafetyIncidents";
import SafetyAudits from "@/pages/SafetyAudits";
import SafetyReports from "@/pages/SafetyReports";
import SafetyTopicLibrary from "@/pages/SafetyTopicLibrary";
import HrSafetyRecords from "@/pages/HrSafetyRecords";
import TrainingHub from "@/pages/TrainingHub";
import AdminDeployReadiness from "@/pages/AdminDeployReadiness";
import TrainingTrack from "@/pages/TrainingTrack";
import TrainingQrPoster from "@/pages/TrainingQrPoster";
import TrainingPacketDownload from "@/pages/TrainingPacketDownload";
import AdminTrainingVideos from "@/pages/AdminTrainingVideos";
import DevLogin from "@/pages/DevLogin";
import DevHub from "@/pages/DevHub";
import CheatSheet from "@/pages/CheatSheet";
import JobPhotosLibrary from "@/pages/JobPhotosLibrary";
import FieldLeadershipHub from "@/pages/FieldLeadershipHub";
import FieldLeadershipFormPage from "@/pages/FieldLeadershipFormPage";
import FieldLeadershipRecords from "@/pages/FieldLeadershipRecords";
import FieldLeadershipView from "@/pages/FieldLeadershipView";
import TermsOfService from "@/pages/legal/TermsOfService";
import PrivacyPolicy from "@/pages/legal/PrivacyPolicy";
import Tasks from "@/pages/Tasks";
import DocumentExpirations from "@/pages/DocumentExpirations";
import HrEmployees from "@/pages/HrEmployees";
import PoRequests from "@/pages/PoRequests";
import ProjectHealth from "@/pages/ProjectHealth";
import AssetTransfers from "@/pages/AssetTransfers";
import AccessDenied from "@/pages/AccessDenied";
import NotFound from "@/pages/NotFound";
import GlobalFooter from "@/components/GlobalFooter";
import ScrollToTop from "@/components/ScrollToTop";
import { RequireAdmin } from "@/components/RequireAdmin";
import { RequireAdminOrPm } from "@/components/RequireAdminOrPm";
import { RequirePm } from "@/components/RequirePm";
import { RequireShop } from "@/components/RequireShop";
import { RequireHr } from "@/components/RequireHr";
import { RequireSafety } from "@/components/RequireSafety";
import { RequireDispatch } from "@/components/RequireDispatch";
import { RequireDev } from "@/components/RequireDev";
import { FormPasswordGate } from "@/components/FormPasswordGate";
import GlobalKeepalive from "@/components/GlobalKeepalive";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import BannerStrip from "@/components/BannerStrip";
import SplashOverlay from "@/components/SplashOverlay";
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
const P = (el) => <RequirePm>{el}</RequirePm>;
const S = (el) => <RequireShop>{el}</RequireShop>;
const H = (el) => <RequireHr>{el}</RequireHr>;
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
      <Toaster position="top-center" richColors closeButton />
      <GlobalKeepalive />
      <BackendStatusBanner />
      <BannerStrip />
      <BrowserRouter key={authTick}>
        <ScrollToTop />
        <EnforcePortalScope />
        <MultiPortalHydrator />
        <IdleTimeout />
        <div className="flex-1 flex flex-col">
          <Routes>
            {/* MASCI Hub — public */}
            <Route path="/" element={<Hub />} />
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

            <Route path="/trench-boxes" element={<TrenchBoxes />} />

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
            <Route path="/admin/jobs" element={A(<AdminJobs />)} />
            <Route path="/admin/equipment" element={A(<AdminEquipment />)} />
            <Route path="/admin/email" element={A(<AdminEmail />)} />
            <Route path="/admin/training" element={A(<AdminTraining />)} />
            <Route path="/admin/compliance" element={A(<AdminCompliance />)} />
            <Route path="/admin/system" element={A(<AdminSystem />)} />
            <Route path="/admin/integrations" element={A(<AdminIntegrationCenter />)} />
            <Route path="/admin/dispatch" element={A(<AdminDispatch />)} />
            <Route path="/admin/operations-events" element={A(<AdminOperationsEvents />)} />
            <Route path="/admin/digest-config" element={A(<AdminDigestConfig />)} />
            <Route path="/admin/system-health" element={A(<SystemHealth />)} />
            <Route path="/admin/audit-log" element={A(<AdminAuditLog />)} />
            <Route path="/admin/legacy-imports" element={A(<AdminLegacyImports />)} />
            <Route path="/admin/sessions" element={A(<AdminSessions />)} />
            <Route path="/admin/guidance-coverage" element={A(<AdminGuidanceCoverage />)} />
            <Route path="/admin/operational-inventory" element={A(<AdminOperationalInventory />)} />
            {/* Operational Guidance Center (iter190 — Training/Help overhaul Phase A).
                Public route — backend enforces RBAC per article.
                The 3-slot route handles: hub home, section, article. */}
            <Route path="/guidance" element={<OperationalGuidanceCenter />} />
            <Route path="/guidance/section/:sectionId" element={<OperationalGuidanceCenter />} />
            <Route path="/guidance/:articleId" element={<OperationalGuidanceCenter />} />
            <Route path="/admin/deploy-recovery" element={A(<DeployRecovery />)} />
            <Route path="/admin/assets/:assetId" element={A(<AssetProfile />)} />
            <Route path="/admin/equipment/:id/history" element={A(<AdminMasterHistory kind="equipment" />)} />
            <Route path="/admin/employees/:id/history" element={A(<AdminMasterHistory kind="employee" />)} />
            <Route path="/admin/analytics" element={A(<AdminAnalytics />)} />
            <Route path="/admin/leadership-equipment" element={A(<AdminLeadershipEquipment />)} />
            <Route path="/admin/terminations" element={A(<AdminTerminations />)} />
            <Route path="/admin/guide" element={A(<AdminGuide />)} />
            <Route path="/admin/pnl" element={AP(<ProjectPnlPage />)} />

            <Route path="/admin/inspections" element={AP(<Dashboard />)} />
            <Route path="/admin/inspections/:id" element={AP(<ViewInspection />)} />

            <Route path="/admin/meetings" element={AP(<MeetingsDashboard />)} />
            <Route path="/admin/meetings/:id" element={AP(<ViewMeeting />)} />

            <Route path="/admin/jha-plans" element={AP(<JhaPlansAdmin />)} />
            <Route path="/admin/jha" element={<Navigate to="/admin/jha-plans" replace />} />
            <Route path="/admin/jha/:id" element={<Navigate to="/admin/jha-plans" replace />} />

            <Route path="/admin/trench-boxes" element={AP(<TrenchBoxesAdmin />)} />
            <Route path="/admin/trench-boxes/poster" element={AP(<PosterErrorBoundary><TrenchBoxPoster /></PosterErrorBoundary>)} />

            <Route path="/admin/jha-plans/poster" element={AP(<PosterErrorBoundary><JhaPlansPoster /></PosterErrorBoundary>)} />

            <Route path="/admin/posters/print-all" element={AP(<PosterErrorBoundary><AllPostersPrint /></PosterErrorBoundary>)} />

            <Route path="/admin/incidents" element={AP(<IncidentsDashboard />)} />
            <Route path="/admin/incidents/:id" element={AP(<ViewIncident />)} />

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
            <Route path="/pm" element={P(<PmHub />)} />
            {/* iter105 — PM Console sub-routes (mirrors AdminConsole layout) */}
            <Route path="/pm/jobs"               element={P(<PmJobs />)} />
            <Route path="/pm/field-leadership"   element={P(<PmFieldLeadership />)} />
            <Route path="/pm/fleet"              element={P(<PmFleet />)} />
            <Route path="/pm/people"             element={P(<PmPeople />)} />
            <Route path="/pm/suppliers"          element={P(<PmSuppliers />)} />
            <Route path="/pm/posters"            element={P(<PmPosters />)} />
            <Route path="/pm/routing"            element={P(<PmRouting />)} />
            <Route path="/pm/compliance-export"  element={P(<PmComplianceExport />)} />
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
            <Route path="/shop/fleet" element={S(<FleetVisibility scope="shop" />)} />
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
            <Route path="/hr/field-leadership" element={H(<HrFieldLeadership />)} />
            <Route path="/hr/employee-accountability" element={H(<HrEmployeeAccountability />)} />
            <Route path="/hr/time-verification" element={H(<HrTimeVerification />)} />
            <Route path="/hr/time-off" element={H(<HrTimeOff />)} />
            <Route path="/hr/payroll-variance" element={H(<HrPayrollVariance />)} />
            <Route path="/hr/training-records" element={H(<HrTrainingRecords />)} />
            <Route path="/hr/driver-qualification" element={H(<HrDriverQualificationDashboard />)} />
            <Route path="/time-off/public/:token" element={<PublicTimeOff />} />

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
            <Route path="/safety-portal/reports" element={SF(<SafetyReports />)} />
            <Route path="/safety-portal/library" element={SF(<SafetyTopicLibrary />)} />
            <Route path="/safety-portal/employees" element={SF(<SafetyEmployeeProfiles />)} />
            <Route path="/safety-portal/digest" element={SF(<SafetyDigest />)} />

            {/* HR cross-portal read-only safety view (uses X-HR-Token) */}
            <Route path="/hr/safety-records" element={H(<HrSafetyRecords />)} />

            {/* ============================================================
                Dispatch Portal — equipment movement command center.
                Mirrors Safety/HR/Shop/PM portal pattern.
                ============================================================ */}
            <Route path="/dispatch-portal/login" element={<DispatchLogin />} />
            <Route path="/leadership/login" element={<LeadershipLogin />} />
            <Route path="/dispatch-portal/forgot-password" element={<DispatchForgotPassword />} />
            <Route path="/dispatch-portal/reset/:token" element={<DispatchResetPassword />} />
            <Route path="/dispatch-portal/change-password" element={DP(<DispatchChangePassword />)} />
            <Route path="/dispatch-portal" element={DP(<DispatchHub />)} />
            <Route path="/dispatch-portal/fleet" element={DP(<FleetVisibility scope="dispatch" />)} />

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
            <Route path="/field-leadership" element={<Navigate to="/leadership" replace />} />
            {/* Catch-all — any path that doesn't match an explicit route
                renders the 404 NotFound page (Iter181). Previously such
                URLs rendered only the global navbar + footer with an
                empty middle (the "blank shell" the production
                verification sweep flagged). Backend authorization is
                untouched; this is purely the unmatched-route UX. */}
            <Route path="*" element={<NotFound />} />
          </Routes>
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
