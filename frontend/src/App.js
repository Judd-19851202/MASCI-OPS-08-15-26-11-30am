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
import JhaPlansHub from "@/pages/JhaPlansHub";
import JhaPlansAdmin from "@/pages/JhaPlansAdmin";
import TrenchBoxes from "@/pages/TrenchBoxes";
import TrenchBoxesAdmin from "@/pages/TrenchBoxesAdmin";
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

// Site Inspections are gated behind a foreman-only access code
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
          <Route path="/inspect/new" element={<GateInspection><NewInspection /></GateInspection>} />
          <Route path="/submit" element={<GateInspection><NewInspection publicMode /></GateInspection>} />
          <Route path="/inspections/submit" element={<GateInspection><NewInspection publicMode /></GateInspection>} />
          <Route path="/inspections/new" element={<Navigate to="/inspect/new" replace />} />

          <Route path="/meetings/new" element={<NewMeeting />} />
          <Route path="/meetings/submit" element={<NewMeeting publicMode />} />

          {/* Job Hazard Plans — read-only file repository (replaces the old fillable JHA form) */}
          <Route path="/jha" element={<JhaPlansHub />} />
          <Route path="/jha/submit" element={<Navigate to="/jha" replace />} />
          <Route path="/jha/new" element={<Navigate to="/jha" replace />} />

          {/* Trench Box Tabulated Data — read-only fleet reference */}
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
              Admin login (no auth needed to reach the form itself)
              ============================================================ */}
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* ============================================================
              Admin — gated dashboards, view, delete
              ============================================================ */}
          <Route path="/admin" element={A(<AdminHub />)} />

          <Route path="/admin/inspections" element={A(<Dashboard />)} />
          <Route path="/admin/inspections/:id" element={A(<ViewInspection />)} />

          <Route path="/admin/meetings" element={A(<MeetingsDashboard />)} />
          <Route path="/admin/meetings/:id" element={A(<ViewMeeting />)} />

          {/* Job Hazard Plans admin manager (PDF uploads) */}
          <Route path="/admin/jha-plans" element={A(<JhaPlansAdmin />)} />
          {/* Old JHA admin URLs now point at the file manager */}
          <Route path="/admin/jha" element={<Navigate to="/admin/jha-plans" replace />} />
          <Route path="/admin/jha/:id" element={<Navigate to="/admin/jha-plans" replace />} />

          {/* Trench Box admin */}
          <Route path="/admin/trench-boxes" element={A(<TrenchBoxesAdmin />)} />

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
