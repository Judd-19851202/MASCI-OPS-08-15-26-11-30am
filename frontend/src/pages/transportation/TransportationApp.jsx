/**
 * TRACK 16.06 · Transportation Experience Layer · Top-level router.
 * TRACK 18.00 Phase A · Universal shell + grouped nav + compat redirects.
 *
 * Mounted at `/admin/transportation/*` in App.js.
 */
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
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
import { IntelligenceCenter } from "./_intelligence";
import DispatchBridgeWorkspace from "./_dispatch_bridge";
import LiveOperationsWorkspace from "./_live_operations";
import TransportationSearch from "./TransportationSearch";
import { useTxOpsSlashShortcut } from "@/components/transportation/TransportationOpsTopBar";

export default function TransportationApp() {
  // TRACK 18.00 · Phase E — `/` keyboard shortcut focuses the Phase C
  // search rail input wherever it's mounted in the shell.
  useTxOpsSlashShortcut();
  return (
    <PortalShell portalName="MASCI" portalSubtitle="Transportation Operations" sideNav={<AdminSideNavV2 />}>
      <div className="space-y-2" data-testid="admin-transportation-page">
        <div
          data-testid="txops-search-rail"
          className="flex justify-end mb-1"
        >
          <TransportationSearch />
        </div>
        <TransportationSubNav />
        <Routes>
          {/* Overview · Mission Control */}
          <Route index element={<TransportationDashboard />} />

          {/* Operations group */}
          <Route path="dispatch" element={<DispatchBridgeWorkspace />} />
          <Route path="live-operations" element={<LiveOperationsWorkspace />} />
          <Route path="trucks" element={<TrucksList />} />
          <Route path="trucks/:id" element={<TruckWorkspace />} />

          {/* People group */}
          <Route path="drivers" element={<DriversList />} />
          <Route path="drivers/:id" element={<DriverWorkspace />} />
          <Route path="carriers" element={<CarriersList />} />
          <Route path="carriers/:id" element={<CarrierWorkspace />} />

          {/* Compliance group */}
          <Route path="compliance" element={<ComplianceDashboard />} />
          <Route path="orientation/*" element={<OrientationCenter />} />

          {/* Operations Intelligence group */}
          <Route path="intelligence/*" element={<IntelligenceCenter />} />
          <Route path="command-queue/*" element={<CommandQueueCenter />} />

          {/* Administration group */}
          <Route path="reports" element={<ReportsView />} />
          <Route path="audit" element={<AuditTimeline />} />

          {/* TRACK 18.00 Phase A · Compatibility redirects. Every old
              URL still resolves so admin bookmarks never break. */}
          <Route path="documents" element={<DocumentCenter />} />
          <Route path="inspections" element={<InspectionCenter />} />
          <Route path="rate-schedules" element={<RateScheduleCenter />} />
          <Route
            path="compliance/documents"
            element={<Navigate to="/admin/transportation/documents" replace />}
          />
          <Route
            path="compliance/rate-schedules"
            element={<Navigate to="/admin/transportation/rate-schedules" replace />}
          />
          <Route
            path="fleet"
            element={<Navigate to="/admin/transportation/trucks" replace />}
          />
          <Route
            path="fleet/trucks"
            element={<Navigate to="/admin/transportation/trucks" replace />}
          />
          <Route
            path="fleet/inspections"
            element={<Navigate to="/admin/transportation/inspections" replace />}
          />
          <Route
            path="administration/audit"
            element={<Navigate to="/admin/transportation/audit" replace />}
          />
        </Routes>
      </div>
    </PortalShell>
  );
}
