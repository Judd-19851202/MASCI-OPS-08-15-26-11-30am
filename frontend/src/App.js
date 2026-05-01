import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
// AuthProvider removed 2026-04-28 — Crew Hub scrapped.
import Hub from "@/pages/Hub";
import SafetySection from "@/pages/SafetySection";
import FieldSection from "@/pages/FieldSection";
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
import PmHub from "@/pages/PmHub";
import ShopLogin from "@/pages/ShopLogin";
import ShopHub from "@/pages/ShopHub";
import TrainingHub from "@/pages/TrainingHub";
import TrainingTrack from "@/pages/TrainingTrack";
import AdminTrainingVideos from "@/pages/AdminTrainingVideos";
import CheatSheet from "@/pages/CheatSheet";
import TermsOfService from "@/pages/legal/TermsOfService";
import PrivacyPolicy from "@/pages/legal/PrivacyPolicy";
import GlobalFooter from "@/components/GlobalFooter";
import { RequireAdmin } from "@/components/RequireAdmin";
import { RequireAdminOrPm } from "@/components/RequireAdminOrPm";
import { RequirePm } from "@/components/RequirePm";
import { RequireShop } from "@/components/RequireShop";
import { FormPasswordGate } from "@/components/FormPasswordGate";
import GlobalKeepalive from "@/components/GlobalKeepalive";
import BackendStatusBanner from "@/components/BackendStatusBanner";

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

function App() {
  return (
    <div className="App min-h-screen flex flex-col">
      <Toaster position="top-center" richColors closeButton />
      <GlobalKeepalive />
      <BackendStatusBanner />
      <BrowserRouter>
        <div className="flex-1 flex flex-col">
          <Routes>
            {/* MASCI Hub — public */}
            <Route path="/" element={<Hub />} />
            <Route path="/safety" element={<SafetySection />} />
            <Route path="/field" element={<FieldSection />} />

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
            <Route path="/cheatsheet" element={<CheatSheet />} />
            <Route path="/cheat-sheet" element={<Navigate to="/cheatsheet" replace />} />

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
            <Route path="/admin/trench-boxes/poster" element={AP(<TrenchBoxPoster />)} />

            <Route path="/admin/jha-plans/poster" element={AP(<JhaPlansPoster />)} />

            <Route path="/admin/posters/print-all" element={AP(<AllPostersPrint />)} />

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
            <Route path="/pm" element={P(<PmHub />)} />

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
            <Route path="/admin/training-videos" element={A(<AdminTrainingVideos />)} />

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
