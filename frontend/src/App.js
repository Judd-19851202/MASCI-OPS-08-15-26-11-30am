import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/lib/authContext";
import Hub from "@/pages/Hub";
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
import CheatSheet from "@/pages/CheatSheet";
import { RequireAdmin } from "@/components/RequireAdmin";
import { FormPasswordGate } from "@/components/FormPasswordGate";

// Crew Hub (Basecamp-style /app section)
import { RequireUser } from "@/components/RequireUser";
import Login from "@/pages/app/Login";
import ChangePassword from "@/pages/app/ChangePassword";
import AppLayout from "@/pages/app/AppLayout";
import AppHome from "@/pages/app/AppHome";
import ProjectHome from "@/pages/app/ProjectHome";
import ProjectMembers from "@/pages/app/ProjectMembers";
import UsersAdmin from "@/pages/app/UsersAdmin";
import MessageBoard from "@/pages/app/MessageBoard";
import TodosPage from "@/pages/app/TodosPage";
import SchedulePage from "@/pages/app/SchedulePage";
import DocsPage from "@/pages/app/DocsPage";
import HillChartsPage from "@/pages/app/HillChartsPage";

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
const U = (el, roles) => <RequireUser requireRole={roles}>{el}</RequireUser>;

function App() {
  return (
    <div className="App">
      <Toaster position="top-center" richColors closeButton />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Safety Hub — unchanged */}
            <Route path="/" element={<Hub />} />

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
                Crew Hub — Phase 1 Basecamp-style per-user workspaces
                ============================================================ */}
            <Route path="/app/login" element={<Login />} />
            <Route path="/app/change-password" element={U(<ChangePassword />)} />

            <Route path="/app" element={U(<AppLayout />)}>
              <Route index element={<AppHome />} />
              <Route path="users" element={U(<UsersAdmin />, ["owner", "admin"])} />
              <Route path="projects/:projectId" element={<ProjectHome />} />
              <Route path="projects/:projectId/members" element={<ProjectMembers />} />
              <Route path="projects/:projectId/messages" element={<MessageBoard />} />
              <Route path="projects/:projectId/todos" element={<TodosPage />} />
              <Route path="projects/:projectId/schedule" element={<SchedulePage />} />
              <Route path="projects/:projectId/docs" element={<DocsPage />} />
              <Route path="projects/:projectId/hills" element={<HillChartsPage />} />
            </Route>

            {/* ============================================================
                Safety Admin — unchanged
                ============================================================ */}
            <Route path="/admin/login" element={<AdminLogin />} />
            <Route path="/admin" element={A(<AdminHub />)} />

            <Route path="/admin/inspections" element={A(<Dashboard />)} />
            <Route path="/admin/inspections/:id" element={A(<ViewInspection />)} />

            <Route path="/admin/meetings" element={A(<MeetingsDashboard />)} />
            <Route path="/admin/meetings/:id" element={A(<ViewMeeting />)} />

            <Route path="/admin/jha-plans" element={A(<JhaPlansAdmin />)} />
            <Route path="/admin/jha" element={<Navigate to="/admin/jha-plans" replace />} />
            <Route path="/admin/jha/:id" element={<Navigate to="/admin/jha-plans" replace />} />

            <Route path="/admin/trench-boxes" element={A(<TrenchBoxesAdmin />)} />
            <Route path="/admin/trench-boxes/poster" element={A(<TrenchBoxPoster />)} />

            <Route path="/admin/jha-plans/poster" element={A(<JhaPlansPoster />)} />

            <Route path="/admin/posters/print-all" element={A(<AllPostersPrint />)} />

            <Route path="/admin/incidents" element={A(<IncidentsDashboard />)} />
            <Route path="/admin/incidents/:id" element={A(<ViewIncident />)} />

            <Route path="/admin/daily" element={A(<DailyReportsDashboard />)} />
            <Route path="/admin/daily/:id" element={A(<ViewDailyReport />)} />

            <Route path="/admin/equipment" element={A(<EquipmentDashboard />)} />
            <Route path="/admin/equipment/:id" element={A(<ViewEquipmentInspection />)} />

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
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

function RedirectWithId({ base }) {
  const id = window.location.pathname.split("/").filter(Boolean).pop();
  return <Navigate to={`${base}/${id}`} replace />;
}

export default App;
