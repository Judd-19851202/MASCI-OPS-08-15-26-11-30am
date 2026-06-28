/**
 * TRACK 16.06 · Transportation Experience Layer · Top-level router.
 * Mounted at `/admin/transportation/*` in App.js.
 */
import React from "react";
import { Routes, Route } from "react-router-dom";
import { PortalShell } from "@/design-system";
import AdminSideNavV2 from "@/components/admin/sidebar/SideNavV2";
import { TransportationSubNav } from "./_shared";
import {
  TransportationDashboard, ComplianceDashboard, DocumentCenter,
  InspectionCenter, RateScheduleCenter, AuditTimeline, ReportsView,
} from "./_views";
import {
  CarriersList, DriversList, TrucksList,
  CarrierWorkspace, DriverWorkspace, TruckWorkspace,
} from "./_lists";
import { OrientationCenter } from "./_orientation";
import { CommandQueueCenter } from "./_command_queue";

export default function TransportationApp() {
  return (
    <PortalShell portalName="MASCI" portalSubtitle="Admin Console" sideNav={<AdminSideNavV2 />}>
      <div className="space-y-2" data-testid="admin-transportation-page">
        <TransportationSubNav />
        <Routes>
          <Route index element={<TransportationDashboard />} />
          <Route path="carriers" element={<CarriersList />} />
          <Route path="carriers/:id" element={<CarrierWorkspace />} />
          <Route path="drivers" element={<DriversList />} />
          <Route path="drivers/:id" element={<DriverWorkspace />} />
          <Route path="trucks" element={<TrucksList />} />
          <Route path="trucks/:id" element={<TruckWorkspace />} />
          <Route path="compliance" element={<ComplianceDashboard />} />
          <Route path="documents" element={<DocumentCenter />} />
          <Route path="inspections" element={<InspectionCenter />} />
          <Route path="orientation/*" element={<OrientationCenter />} />
          <Route path="command-queue/*" element={<CommandQueueCenter />} />
          <Route path="rate-schedules" element={<RateScheduleCenter />} />
          <Route path="audit" element={<AuditTimeline />} />
          <Route path="reports" element={<ReportsView />} />
        </Routes>
      </div>
    </PortalShell>
  );
}
