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
import ViewEquipmentInspection from "@/pages/ViewEquipmentInspection";
import AdminLogin from "@/pages/AdminLogin";
import AdminHub from "@/pages/AdminHub";
import AdminGuide from "@/pages/AdminGuide";
import ProjectPnlPage from "@/pages/ProjectPnlPage";
import PmLogin from "@/pages/PmLogin";
import PmChangePassword from "@/pages/PmChangePassword";
import PmResetPassword from "@/pages/PmResetPassword";
import PmHub from "@/pages/PmHub";
import PmQaqcList from "@/pages/PmQaqcList";
import ShopLogin from "@/pages/ShopLogin";
import ShopHub from "@/pages/ShopHub";
import TrainingHub from "@/pages/TrainingHub";
import TrainingTrack from "@/pages/TrainingTrack";
import TrainingQrPoster from "@/pages/TrainingQrPoster";
import TrainingPacketDownload from "@/pages/TrainingPacketDownload";
import AdminTrainingVideos from "@/pages/AdminTrainingVideos";
import DevLogin from "@/pages/DevLogin";
import DevHub from "@/pages/DevHub";
import CheatSheet from "@/pages/CheatSheet";
import TermsOfService from "@/pages/legal/TermsOfService";
import PrivacyPolicy from "@/pages/legal/PrivacyPolicy";
import GlobalFooter from "@/components/GlobalFooter";
import ScrollToTop from "@/components/ScrollToTop";
import { RequireAdmin } from "@/components/RequireAdmin";
import { RequireAdminOrPm } from "@/components/RequireAdminOrPm";
import { RequirePm } from "@/components/RequirePm";
import { RequireShop } from "@/components/RequireShop";
import { RequireDev } from "@/components/RequireDev";
import { FormPasswordGate } from "@/components/FormPasswordGate";
import GlobalKeepalive from "@/components/GlobalKeepalive";
import BackendStatusBanner from "@/components/BackendStatusBanner";
import { validateStoredTokens } from "@/lib/tokenValidation";
import EnforcePortalScope from "@/components/EnforcePortalScope";
import IdleTimeout from "@/components/IdleTimeout";
import PosterErrorBoundary from "@/components/PosterErrorBoundary";

// Crew Hub (Basecamp-style /app section)
// Crew Hub pages removed 2026-04-28 — replaced by external Basecamp link.

const SITE_INSPECTION_CODE = "1982";
const GateInspection = ({ children }) => (
  <FormPasswordGate
    storageKey="masci.gate.site-inspection"
    password={SITE_INSPECTION_CODE}
    formLabel="Site Inspection"
  >
    {children}
  </FormPasswordGate>
);

const A = (el) => <RequireAdmin>{el}</RequireAdmin>;
const AP = (el) => <RequireAdminOrPm>{el}</RequireAdminOrPm>;
const P = (el) => <RequirePm>{el}</RequirePm>;
const S = (el) => <RequireShop>{el}</RequireShop>;
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
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="App min-h-screen flex flex-col">
      <Toaster position="top-center" richColors closeButton />
      <GlobalKeepalive />
      <BackendStatusBanner />
      <BrowserRouter key={authTick}>
        <ScrollToTop />
        <EnforcePortalScope />
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
            <Route path="/qaqc/:slug/new" element={<NewQaqcInspection />} />
            <Route path="/qaqc/:id" element={<ViewQaqcInspection />} />
            <Route path="/admin/qaqc" element={<AdminQaqcList />} />

            <Route path="/inspect/new" element={<GateInspection><NewInspection /></GateInspection>} />
            <Route path="/submit" element={<GateInspection><NewInspection publicMode /></GateInspection>} />
            <Route path="/inspections/submit" element={<GateInspection><NewInspection publicMode /></GateInspection>} />
            <Route path="/inspections/new" element={<Navigate to="/inspect/new" replace />} />

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

            <Route path="/admin/equipment" element={AP(<EquipmentDashboard />)} />
            <Route path="/admin/equipment/:id" element={AP(<ViewEquipmentInspection context="admin" />)} />

            {/* ============================================================
                Project Management Portal — same surface as admin minus
                backup/recovery. Backed by PM_PASSWORD; admin tokens are
                also accepted by the PM hub guard (RequirePm).
                ============================================================ */}
            <Route path="/pm/login" element={<PmLogin />} />
            <Route path="/pm/reset/:token" element={<PmResetPassword />} />
            <Route path="/pm/change-password" element={P(<PmChangePassword />)} />
            <Route path="/pm" element={P(<PmHub />)} />
            <Route path="/pm/qaqc" element={P(<PmQaqcList />)} />

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
            <Route path="/pm/pnl" element={AP(<ProjectPnlPage />)} />

            {/* ============================================================
                Shop Console — mechanics-only view, separate password
                ============================================================ */}
            <Route path="/shop/login" element={<ShopLogin />} />
            <Route path="/shop" element={S(<ShopHub />)} />
            <Route path="/shop/equipment/:id" element={S(<ViewEquipmentInspection context="shop" />)} />

            {/* ============================================================
                Training Hub — landing is public, tracks gate per audience
                (Field public, Shop/PM/Admin each require their own token).
                Admin video URL manager lives behind /admin/training-videos.
                ============================================================ */}
            <Route path="/training" element={<TrainingHub />} />
            <Route path="/training/:track" element={<TrainingTrack />} />
            <Route path="/training/:track/poster" element={<TrainingQrPoster />} />
            <Route path="/training/:track/packet" element={<TrainingPacketDownload />} />
            <Route path="/admin/training-videos" element={A(<AdminTrainingVideos />)} />

            {/* ============================================================
                Developer Portal — The Judd Group LLC vendor-internal only.
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
