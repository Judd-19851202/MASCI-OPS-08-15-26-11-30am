/**
 * DispatchCommandCenter.jsx · FORGEDOPS Dispatch Command Center V1 · Phase 2.
 *
 * Route: /dispatch-portal/command (dispatch + admin gated by RequireDispatch).
 *
 * One operational picture. Seven tabs (Overview / Fleet / Drivers / Jobs
 * / Hauls / Shop Feed / Communications). No drilling, no hunting. The
 * 8-tile command strip is visible on every tab.
 *
 * Powerful · Simple · Beautiful · Trusted · Proven.
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, LayoutDashboard, Truck, User, Briefcase, Activity,
  Wrench, MessageSquare,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePageTitle } from "@/lib/usePageTitle";
import { paletteFor } from "@/lib/portalPalette";
import CommandStrip from "@/components/dispatch/command/CommandStrip";
import FleetBoard from "@/components/dispatch/command/FleetBoard";
import DriverBoard from "@/components/dispatch/command/DriverBoard";
import JobBoard from "@/components/dispatch/command/JobBoard";
import HaulBoard from "@/components/dispatch/command/HaulBoard";
import ShopFeedBoard from "@/components/dispatch/command/ShopFeedBoard";
import CommunicationsTab from "@/components/dispatch/command/CommunicationsTab";
import { commandApi } from "@/components/dispatch/command/commandApi";

const DISPATCH_PAL = paletteFor("dispatch");
const SUMMARY_POLL_MS = 30000;

export default function DispatchCommandCenter() {
  usePageTitle("Dispatch Command Center · MASCI");
  const nav = useNavigate();

  const [tab, setTab] = useState("overview");
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  const loadSummary = useCallback(async () => {
    try {
      const d = await commandApi.summary();
      setSummary(d);
    } catch (_e) {
      // Trust contract: SessionStatusOverlay / global toasts handle
      // network-class errors. We just leave summary null and the strip
      // renders em-dashes.
    } finally { setLoadingSummary(false); }
  }, []);

  useEffect(() => {
    loadSummary();
    const id = setInterval(loadSummary, SUMMARY_POLL_MS);
    return () => clearInterval(id);
  }, [loadSummary]);

  return (
    <div
      className="min-h-screen bg-slate-50"
      data-testid="dispatch-command-center"
    >
      {/* Header */}
      <header className={`${DISPATCH_PAL.bg} text-white border-b border-slate-800`}>
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 sm:gap-4 min-w-0">
            <button
              type="button"
              onClick={() => nav(-1)}
              className="text-white/80 hover:text-white p-1"
              data-testid="dcc-back"
              aria-label="Back"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <MasciLogo className="w-6 h-6 shrink-0" />
            <div className="min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/60 truncate">
                Dispatch · Command Center · V1
              </div>
              <h1 className="font-display text-base sm:text-xl font-black truncate">
                Operational Heartbeat
              </h1>
            </div>
          </div>
          <Link
            to="/dispatch-portal"
            className="text-xs text-white/80 hover:text-white font-mono uppercase tracking-widest"
            data-testid="dcc-back-hub"
          >
            Dispatch Hub
          </Link>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6 space-y-4">
        {/* Always-on command strip */}
        <CommandStrip
          summary={summary}
          loading={loadingSummary}
          onJumpTo={setTab}
        />

        <Tabs value={tab} onValueChange={setTab} className="space-y-4">
          <TabsList
            className="w-full h-auto flex flex-wrap justify-start bg-white border border-slate-200 p-1 rounded-md gap-1"
            data-testid="dcc-tabs"
          >
            <TabsTrigger value="overview" data-testid="dcc-tab-overview" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <LayoutDashboard className="w-3.5 h-3.5 mr-1.5" /> Overview
            </TabsTrigger>
            <TabsTrigger value="fleet" data-testid="dcc-tab-fleet" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Truck className="w-3.5 h-3.5 mr-1.5" /> Fleet
            </TabsTrigger>
            <TabsTrigger value="drivers" data-testid="dcc-tab-drivers" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <User className="w-3.5 h-3.5 mr-1.5" /> Drivers
            </TabsTrigger>
            <TabsTrigger value="jobs" data-testid="dcc-tab-jobs" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Briefcase className="w-3.5 h-3.5 mr-1.5" /> Jobs
            </TabsTrigger>
            <TabsTrigger value="hauls" data-testid="dcc-tab-hauls" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Activity className="w-3.5 h-3.5 mr-1.5" /> Hauls
            </TabsTrigger>
            <TabsTrigger value="shop" data-testid="dcc-tab-shop" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <Wrench className="w-3.5 h-3.5 mr-1.5" /> Shop
            </TabsTrigger>
            <TabsTrigger value="comms" data-testid="dcc-tab-comms" className="data-[state=active]:bg-slate-900 data-[state=active]:text-white">
              <MessageSquare className="w-3.5 h-3.5 mr-1.5" /> Comms
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" data-testid="dcc-tab-content-overview">
            <OverviewPane summary={summary} loading={loadingSummary} onJumpTo={setTab} />
          </TabsContent>
          <TabsContent value="fleet"   data-testid="dcc-tab-content-fleet"><FleetBoard /></TabsContent>
          <TabsContent value="drivers" data-testid="dcc-tab-content-drivers"><DriverBoard /></TabsContent>
          <TabsContent value="jobs"    data-testid="dcc-tab-content-jobs"><JobBoard /></TabsContent>
          <TabsContent value="hauls"   data-testid="dcc-tab-content-hauls"><HaulBoard /></TabsContent>
          <TabsContent value="shop"    data-testid="dcc-tab-content-shop"><ShopFeedBoard /></TabsContent>
          <TabsContent value="comms"   data-testid="dcc-tab-content-comms"><CommunicationsTab /></TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────── */
function OvRow({ k, v, mono = true, testId }) {
  return (
    <div
      className="flex justify-between text-xs sm:text-sm py-1.5 border-b border-slate-100 last:border-b-0"
      data-testid={testId}
    >
      <span className="text-slate-600">{k}</span>
      <span className={`text-slate-900 font-bold ${mono ? "font-mono" : ""}`}>{v ?? "—"}</span>
    </div>
  );
}

function OverviewPane({ summary, loading, onJumpTo }) {
  const fleet = summary?.fleet?.counts || {};
  const drivers = summary?.drivers?.counts || {};
  const haul = summary?.haul?.counts || {};
  const shop = summary?.shop || {};
  const ah = summary?.asset_health || {};
  const ir = summary?.integration_readiness || {};

  if (loading && !summary) {
    return (
      <div className="space-y-2" data-testid="overview-skeleton">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-12 bg-slate-100 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 sm:gap-4" data-testid="overview-pane">
      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="overview-fleet-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5 flex items-center justify-between">
          <span>Fleet</span>
          <button className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-900" onClick={() => onJumpTo("fleet")}>Open →</button>
        </h3>
        <OvRow k="Total assets" v={fleet.total} testId="ov-fleet-total" />
        <OvRow k="Active" v={fleet.active} testId="ov-fleet-active" />
        <OvRow k="Out of service" v={fleet.oos} testId="ov-fleet-oos" />
        <OvRow k="In shop" v={fleet.in_shop} testId="ov-fleet-in-shop" />
        <OvRow k="Unmapped (Motive)" v={fleet.unmapped} testId="ov-fleet-unmapped" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="overview-driver-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5 flex items-center justify-between">
          <span>Drivers</span>
          <button className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-900" onClick={() => onJumpTo("drivers")}>Open →</button>
        </h3>
        <OvRow k="Shifted now" v={drivers.shifted} testId="ov-drv-shifted" />
        <OvRow k="Un-acked" v={drivers.un_acked} testId="ov-drv-unacked" />
        <OvRow k="Waiting" v={drivers.waiting} testId="ov-drv-waiting" />
        <OvRow k="In breakdown" v={drivers.in_breakdown} testId="ov-drv-breakdown" />
        <OvRow k="Off-shift today" v={drivers.off_shift_today} testId="ov-drv-off-shift" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="overview-haul-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5 flex items-center justify-between">
          <span>Hauls Today</span>
          <button className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-900" onClick={() => onJumpTo("hauls")}>Open →</button>
        </h3>
        <OvRow k="Active hauls" v={haul.active_hauls} testId="ov-haul-active" />
        <OvRow k="Loads completed" v={haul.loads_completed_today} testId="ov-haul-loads" />
        <OvRow k="Equip moves" v={haul.equipment_moves_completed_today} testId="ov-haul-equip" />
        <OvRow k="Waiting on plant" v={haul.waiting_on_plant} testId="ov-haul-plant" />
        <OvRow k="Waiting on dump" v={haul.waiting_on_dump} testId="ov-haul-dump" />
        <OvRow k="Breakdown impacts" v={haul.breakdown_impacts} testId="ov-haul-breakdown" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="overview-shop-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5 flex items-center justify-between">
          <span>Shop</span>
          <button className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-900" onClick={() => onJumpTo("shop")}>Open →</button>
        </h3>
        <OvRow k="Open defects" v={shop.defects_open} testId="ov-shop-open" />
        <OvRow k="Acknowledged" v={shop.defects_acknowledged} testId="ov-shop-ack" />
        <OvRow k="OOS units" v={shop.oos_units} testId="ov-shop-oos" />
        <OvRow k="Active recovery" v={shop.active_recovery} testId="ov-shop-recovery" />
        <OvRow k="Waiting parts" v={shop.waiting_on_parts} testId="ov-shop-parts" />
        <OvRow k="Returned 7d" v={shop.returned_to_service_7d} testId="ov-shop-returned" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="overview-asset-health-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5">Asset Spine Health</h3>
        <OvRow k="Total" v={ah.total_assets} testId="ov-ah-total" />
        <OvRow k="Active" v={ah.active} testId="ov-ah-active" />
        <OvRow k="Retired" v={ah.retired} testId="ov-ah-retired" />
        <OvRow k="Motive coverage" v={ah.motive_coverage_pct != null ? `${ah.motive_coverage_pct}%` : "—"} testId="ov-ah-coverage" />
        <OvRow k="Conflicts" v={ah.conflicts} testId="ov-ah-conflicts" />
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4" data-testid="overview-integration-card">
        <h3 className="font-display text-sm font-black text-slate-900 mb-1.5">Integrations</h3>
        <OvRow k="Motive" v={ir.motive || "—"} mono={false} testId="ov-int-motive" />
        <OvRow k="FleetWatcher" v={ir.fleetwatcher === "not_connected" ? "Pending Integration" : ir.fleetwatcher} mono={false} testId="ov-int-fleetwatcher" />
        <OvRow k="MaintainX" v={ir.maintainx === "not_connected" ? "Pending Integration" : ir.maintainx} mono={false} testId="ov-int-maintainx" />
        <OvRow k="SMS provider" v={ir.sms_provider === "active" ? "Active" : "Not Configured"} mono={false} testId="ov-int-sms" />
      </div>
    </div>
  );
}
