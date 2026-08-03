/**
 * TRACK 16.06 · Transportation Experience Layer · Top-level router.
 * TRACK 18.00 Phase A · Universal shell + grouped nav + compat redirects.
 *
 * Mounted at `/admin/transportation/*` in App.js.
 */
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { PortalShell } from "@/design-system";
import { renderAdminRouteSideNav } from "@/components/admin/AdminRouteShell";
import TransportationSideNavV2, { isTxSidebarV2Enabled } from "@/components/transportation/sidebar/TransportationSideNavV2";
import { isAdmin } from "@/lib/adminAuth";
import { useT } from "@/lib/i18n";
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

function TxAliasRedirect({ to }) {
  const prefix = window.location.pathname.startsWith("/admin/transportation")
    ? "/admin/transportation"
    : "/transportation-operations";
  return <Navigate to={`${prefix}/${to}`} replace />;
}

export default function TransportationApp() {
  const { t } = useT();
  // TRACK 18.00 · Phase E — `/` keyboard shortcut focuses the Phase C
  // search rail input wherever it's mounted in the shell.
  useTxOpsSlashShortcut();
  // TRACK 18.00E-FIX — dispatch-authenticated users now reach this
  // shell through `/transportation-operations/*` without holding the
  // admin token. Suppress the admin-only side nav when admin is not
  // signed in so the experience never reads as "Admin Console".
  //
  // TRACK 19.32 — Transportation / Fleet Sidebar V2 rollout. When the
  // Sidebar V2 flag is ON (default), render the new domain-grouped
  // TransportationSideNavV2 for BOTH admin and dispatch users
  // (permission gating is inside `visibleTxOpsNavGroups()`). When the
  // flag is OFF (escape hatch: `?txSidebarV2=0`), preserve the pre-19.32
  // behavior — admin sees Admin V2 sidebar, dispatch sees no sidebar.
  const showAdminSideNav = isAdmin();
  const txSidebarV2 = isTxSidebarV2Enabled();
  const effectiveSideNav = txSidebarV2
    ? <TransportationSideNavV2 />
    : (showAdminSideNav ? renderAdminRouteSideNav() : null);
  return (
    <PortalShell
      portalName="MASCI"
      portalRole={t("Transportation Operations")}
      portalSwitcherCurrent="dispatch"
      pageTitle={t("Transportation Operations")}
      subtitle={t("Mission control, live operations, carriers, drivers, fleet, compliance, and onboarding in one place.")}
      sideNav={effectiveSideNav}
      experienceTone="transportation"
    >
      <div className="wp17-transport-shell" data-testid="admin-transportation-page">
        <section className="wp17-mission-banner" data-testid="txops-mission-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">{t("Today's focus")}</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">{t("Run hauling operations with clear assignments, live exceptions, and direct next steps.")}</h2>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                {t("See carriers, drivers, fleet, and compliance work in one place with the right access for each role.")}
              </p>
            </div>
          </div>
        </section>
        <div
          data-testid="txops-search-rail"
          className="wp17-transport-toolbar flex flex-wrap items-center justify-between gap-3"
        >
          <div>
            <div className="wp17-kicker">{t("Navigation")}</div>
            <div className="mt-1 text-sm font-semibold text-slate-900">{t("Use the sidebar for primary movement. Search is for direct access and detail discovery.")}</div>
          </div>
          <TransportationSearch />
        </div>
        <div className="xl:hidden">
          <TransportationSubNav />
        </div>
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
            element={<TxAliasRedirect to="documents" />}
          />
          <Route
            path="compliance/rate-schedules"
            element={<TxAliasRedirect to="rate-schedules" />}
          />
          <Route
            path="fleet"
            element={<TxAliasRedirect to="trucks" />}
          />
          <Route
            path="fleet/trucks"
            element={<TxAliasRedirect to="trucks" />}
          />
          <Route
            path="fleet/inspections"
            element={<TxAliasRedirect to="inspections" />}
          />
          <Route
            path="administration/audit"
            element={<TxAliasRedirect to="audit" />}
          />
        </Routes>
      </div>
    </PortalShell>
  );
}
