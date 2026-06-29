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
import { isAdmin } from "@/lib/adminAuth";
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
import { TransportationAcademy, TransportationAcademyModule } from "./TransportationAcademy";
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
  // TRACK 18.00E-FIX — dispatch-authenticated users now reach this
  // shell through `/transportation-operations/*` without holding the
  // admin token. Suppress the admin-only side nav when admin is not
  // signed in so the experience never reads as "Admin Console".
  const showAdminSideNav = isAdmin();
  return (
    <PortalShell portalName="MASCI" portalSubtitle="Transportation Operations" sideNav={showAdminSideNav ? <AdminSideNavV2 /> : null}>
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
          <Route path="academy" element={<TransportationAcademy />} />
          <Route path="academy/:moduleKey" element={<TransportationAcademyModule />} />

          {/* Operations Intelligence group */}
          <Route path="intelligence/*" element={<IntelligenceCenter />} />
          <Route path="command-queue/*" element={<CommandQueueCenter />} />

          {/* Administration group */}
          <Route path="reports" element={<ReportsView />} />
          <Route path="audit" element={<AuditTimeline />} />

          {/* TRACK 18.00 Phase A · Compatibility redirects. Every old
              URL still resolves so admin bookmarks never break.
              TRACK 18.09C · Made `relative="path"` so the redirects
              keep the active prefix (`/admin/transportation` for
              admin oversight, `/transportation-operations` for
              dispatch-authenticated operational use) and never
              bounce an operational user into the admin shell. */}
          <Route path="documents" element={<DocumentCenter />} />
          <Route path="inspections" element={<InspectionCenter />} />
          <Route path="rate-schedules" element={<RateScheduleCenter />} />
          <Route
            path="compliance/documents"
            element={<Navigate to="../documents" replace relative="path" />}
          />
          <Route
            path="compliance/rate-schedules"
            element={<Navigate to="../rate-schedules" replace relative="path" />}
          />
          <Route
            path="fleet"
            element={<Navigate to="../trucks" replace relative="path" />}
          />
          <Route
            path="fleet/trucks"
            element={<Navigate to="../../trucks" replace relative="path" />}
          />
          <Route
            path="fleet/inspections"
            element={<Navigate to="../../inspections" replace relative="path" />}
          />
          <Route
            path="administration/audit"
            element={<Navigate to="../audit" replace relative="path" />}
          />
        </Routes>
      </div>
    </PortalShell>
  );
}
