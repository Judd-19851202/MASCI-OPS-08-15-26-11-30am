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

function App() {
  return (
    <div className="App">
      <Toaster position="top-center" richColors closeButton />
      <BrowserRouter>
        <Routes>
          {/* Hub landing */}
          <Route path="/" element={<Hub />} />

          {/* Inspections */}
          <Route path="/inspections" element={<Dashboard />} />
          <Route path="/inspect/new" element={<NewInspection />} />
          <Route path="/inspections/new" element={<Navigate to="/inspect/new" replace />} />
          <Route path="/submit" element={<NewInspection publicMode />} />
          <Route path="/inspections/submit" element={<NewInspection publicMode />} />
          <Route path="/inspect/:id" element={<ViewInspection />} />
          <Route path="/inspections/:id" element={<ViewInspection />} />

          {/* Safety Meetings */}
          <Route path="/meetings" element={<MeetingsDashboard />} />
          <Route path="/meetings/new" element={<NewMeeting />} />
          <Route path="/meetings/submit" element={<NewMeeting publicMode />} />
          <Route path="/meetings/:id" element={<ViewMeeting />} />

          {/* JHA */}
          <Route path="/jha" element={<JhaDashboard />} />
          <Route path="/jha/new" element={<NewJha />} />
          <Route path="/jha/submit" element={<NewJha publicMode />} />
          <Route path="/jha/:id" element={<ViewJha />} />

          {/* Shared */}
          <Route path="/thank-you" element={<ThankYou />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
