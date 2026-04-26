import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import Hub from "@/pages/Hub";
import Dashboard from "@/pages/Dashboard";
import NewInspection from "@/pages/NewInspection";
import ViewInspection from "@/pages/ViewInspection";
import ThankYou from "@/pages/ThankYou";
import MeetingsDashboard from "@/pages/MeetingsDashboard";
import NewMeeting from "@/pages/NewMeeting";
import ViewMeeting from "@/pages/ViewMeeting";
import JhaDashboard from "@/pages/JhaDashboard";
import NewJha from "@/pages/NewJha";
import ViewJha from "@/pages/ViewJha";
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

// Helper: wrap any element in the admin gate.
const A = (el) => <RequireAdmin>{el}</RequireAdmin>;

function App() {
  return (
    <div className="App">
      <Toaster position="top-center" richColors closeButton />
      <BrowserRouter>
        <Routes>
          {/* ============================================================
              Public — field-crew Hub + form-fill flow only
              ============================================================ */}
          <Route path="/" element={<Hub />} />

          {/* New / public-submit forms (no auth) */}
          <Route path="/inspect/new" element={<NewInspection />} />
          <Route path="/submit" element={<NewInspection publicMode />} />
          <Route path="/inspections/submit" element={<NewInspection publicMode />} />
          <Route path="/inspections/new" element={<Navigate to="/inspect/new" replace />} />

          <Route path="/meetings/new" element={<NewMeeting />} />
          <Route path="/meetings/submit" element={<NewMeeting publicMode />} />

          <Route path="/jha/new" element={<NewJha />} />
          <Route path="/jha/submit" element={<NewJha publicMode />} />

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
              Admin login (no auth needed to reach the form itself)
              ============================================================ */}
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* ============================================================
              Admin — gated dashboards, view, delete
              All previous /inspections, /meetings, /jha, /incidents, /daily
              dashboards & view pages now live under /admin/*. The old
              top-level URLs redirect to /admin/login (which then bounces
              back) so any bookmarks the office already has keep working.
              ============================================================ */}
          <Route path="/admin" element={A(<AdminHub />)} />

          <Route path="/admin/inspections" element={A(<Dashboard />)} />
          <Route path="/admin/inspections/:id" element={A(<ViewInspection />)} />

          <Route path="/admin/meetings" element={A(<MeetingsDashboard />)} />
          <Route path="/admin/meetings/:id" element={A(<ViewMeeting />)} />

          <Route path="/admin/jha" element={A(<JhaDashboard />)} />
          <Route path="/admin/jha/:id" element={A(<ViewJha />)} />

          <Route path="/admin/incidents" element={A(<IncidentsDashboard />)} />
          <Route path="/admin/incidents/:id" element={A(<ViewIncident />)} />

          <Route path="/admin/daily" element={A(<DailyReportsDashboard />)} />
          <Route path="/admin/daily/:id" element={A(<ViewDailyReport />)} />

          <Route path="/admin/equipment" element={A(<EquipmentDashboard />)} />
          <Route path="/admin/equipment/:id" element={A(<ViewEquipmentInspection />)} />

          {/* Legacy URL → admin equivalents (admin gate redirects to login if needed) */}
          <Route path="/inspections" element={<Navigate to="/admin/inspections" replace />} />
          <Route path="/inspect/:id" element={<RedirectWithId base="/admin/inspections" />} />
          <Route path="/inspections/:id" element={<RedirectWithId base="/admin/inspections" />} />
          <Route path="/meetings" element={<Navigate to="/admin/meetings" replace />} />
          <Route path="/meetings/:id" element={<RedirectWithId base="/admin/meetings" />} />
          <Route path="/jha" element={<Navigate to="/admin/jha" replace />} />
          <Route path="/jha/:id" element={<RedirectWithId base="/admin/jha" />} />
          <Route path="/incidents" element={<Navigate to="/admin/incidents" replace />} />
          <Route path="/incidents/:id" element={<RedirectWithId base="/admin/incidents" />} />
          <Route path="/daily" element={<Navigate to="/admin/daily" replace />} />
          <Route path="/daily/:id" element={<RedirectWithId base="/admin/daily" />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

// Tiny adapter to forward /:id legacy URLs to their /admin/*/:id equivalents.
function RedirectWithId({ base }) {
  const id = window.location.pathname.split("/").filter(Boolean).pop();
  return <Navigate to={`${base}/${id}`} replace />;
}

export default App;
