// Dispatch Portal hub — the dedicated dispatcher workspace.
// Reuses the proven tab components from AdminDispatch (re-exported)
// so the dispatcher and admin views show identical data, but renders
// inside its own portal chrome (no AdminShell sidebar).
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Truck, Send, ShieldAlert, Activity, LogOut, Clock, Home, ArrowLeft, Plug, BookOpen,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { ForgedOpsAttribution } from "@/components/ForgedOpsAttribution";
import PortalSwitcher from "@/components/PortalSwitcher";
import NotificationBell from "@/components/NotificationBell";
import GlobalSearch from "@/components/GlobalSearch";
import { OfflineIndicator } from "@/lib/resiliency";
import OperationsCenter from "@/components/OperationsCenter";
import {
  DispatchOverviewTab, DispatchUtilizationTab, DispatchIdleAlertsTab,
  DispatchTransfersTab, DispatchHoldsTab,
} from "@/pages/admin/AdminDispatch";
import DispatchIntegrationsTab from "@/components/DispatchIntegrationsTab";
import { clearDispatchToken, getDispatchUser } from "@/lib/dispatchAuth";
import { clearAllSessions } from "@/lib/sessionReset";
import { paletteFor } from "@/lib/portalPalette";
import { usePageTitle } from "@/lib/usePageTitle";

const DISPATCH_PAL = paletteFor("dispatch");

export default function DispatchHub() {
  usePageTitle("Dispatch · MASCI");
  const nav = useNavigate();
  const [tab, setTab] = useState("overview");
  const user = getDispatchUser() || {};

  const logout = async () => {
    // P0 (iter179): wipe every auth artifact, not just Dispatch.
    await clearAllSessions();
    nav("/dispatch-portal/login", { replace: true });
  };

  return (
    <div className="min-h-screen blueprint-bg flex flex-col" data-testid="dispatch-hub">
      <div className="caution-stripe" />
      <header className={`bg-slate-900 text-white border-b-4 ${DISPATCH_PAL.hubHeaderBar}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
          <Link
            to="/"
            className={`inline-flex items-center text-white ${DISPATCH_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`}
            data-testid="dispatch-nav-home"
            title="Public Hub"
          >
            <Home className="w-4 h-4 sm:mr-1" />
            <span className="hidden sm:inline">Home</span>
          </Link>
          <button
            onClick={() => nav(-1)}
            className={`inline-flex items-center text-white ${DISPATCH_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`}
            data-testid="dispatch-nav-back"
            title="Back"
          >
            <ArrowLeft className="w-4 h-4 sm:mr-1" />
            <span className="hidden sm:inline">Back</span>
          </button>
          <MasciLogo variant="mark" size="md" className="hidden sm:block" homeLink="/" />
          <div className="flex-1 min-w-0">
            <div className={`font-mono text-[10px] uppercase tracking-[0.22em] ${DISPATCH_PAL.hubKickerStatic} font-bold`}>
              Dispatch Portal
            </div>
            <div className="font-display text-lg sm:text-xl font-black leading-tight truncate">
              {user.name || "Dispatcher"}
            </div>
          </div>
          {/* iter321 — Mobile header collapse: hide PortalSwitcher,
              GlobalSearch, Transfers, Fleet, Guides on <sm. Keep
              visible: NotificationBell, OfflineIndicator, SignOut. */}
          <div className="hidden sm:flex items-center gap-2">
            <PortalSwitcher current="dispatch" />
            <GlobalSearch accent="dark" />
          </div>
          <NotificationBell accent="white" />
          <OfflineIndicator />
          <Link
            to="/asset-transfers"
            className="hidden sm:inline-flex items-center h-9 px-3 rounded-md border-2 border-white/30 text-white hover:bg-white/10 text-xs font-bold uppercase tracking-wide"
            data-testid="dispatch-asset-transfers-link"
          >
            <Truck className="w-3.5 h-3.5 sm:mr-1" />
            <span className="hidden sm:inline">Transfers</span>
          </Link>
          <Link
            to="/dispatch-portal/fleet"
            className="hidden sm:inline-flex items-center h-9 px-3 rounded-md border-2 border-white/30 text-white hover:bg-white/10 text-xs font-bold uppercase tracking-wide"
            data-testid="dispatch-fleet-link"
          >
            <Truck className="w-3.5 h-3.5 sm:mr-1" />
            <span className="hidden sm:inline">Fleet</span>
          </Link>
          <Link
            to="/guidance?from=dispatch"
            className="hidden sm:inline-flex items-center h-9 px-3 rounded-md border-2 border-white/30 text-white hover:bg-white/10 text-xs font-bold uppercase tracking-wide"
            data-testid="dispatch-training-link"
          >
            <BookOpen className="w-3.5 h-3.5 sm:mr-1" />
            <span className="hidden sm:inline">Guides</span>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={logout}
            className="bg-transparent text-white border-white/30 hover:bg-white/10"
            data-testid="dispatch-logout"
          >
            <LogOut className="w-3.5 h-3.5 sm:mr-1" />
            <span className="hidden sm:inline">Sign out</span>
          </Button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-6 space-y-4 flex-1 w-full">
        {/* iter321 · calm title card replaces the prior hot
            `border-2 border-slate-300` block. Left-edge orange stripe
            preserves the Dispatch identity color while the chrome stays
            on the platform-family contract. */}
        <div className="bg-white border border-slate-200 border-l-4 border-l-orange-500 rounded-md p-5">
          <div className="flex items-start gap-3">
            <Truck className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
            <div>
              <span className="font-mono text-xs uppercase tracking-[0.22em] text-orange-700 font-bold">
                Dispatch Portal
              </span>
              <h1 className="font-display text-3xl sm:text-4xl font-black tracking-tight text-slate-900 mt-1">
                Equipment Movement Command Center
              </h1>
              <p className="text-sm text-slate-600 mt-2 max-w-2xl">
                Availability · transfers · holds · utilization · idle alerts · Motive + MaintainX readiness.
              </p>
            </div>
          </div>
        </div>

        <OperationsCenter compact className="mb-4" />

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="overview" data-testid="dh-tab-overview"><Activity className="w-3.5 h-3.5 mr-1" /> Overview</TabsTrigger>
            <TabsTrigger value="utilization" data-testid="dh-tab-utilization"><Activity className="w-3.5 h-3.5 mr-1" /> Utilization</TabsTrigger>
            <TabsTrigger value="idle" data-testid="dh-tab-idle"><Clock className="w-3.5 h-3.5 mr-1" /> Idle Alerts</TabsTrigger>
            <TabsTrigger value="transfers" data-testid="dh-tab-transfers"><Send className="w-3.5 h-3.5 mr-1" /> Transfers</TabsTrigger>
            <TabsTrigger value="holds" data-testid="dh-tab-holds"><ShieldAlert className="w-3.5 h-3.5 mr-1" /> Holds</TabsTrigger>
            <TabsTrigger value="integrations" data-testid="dh-tab-integrations"><Plug className="w-3.5 h-3.5 mr-1" /> Integrations</TabsTrigger>
          </TabsList>
          <TabsContent value="overview"><DispatchOverviewTab /></TabsContent>
          <TabsContent value="utilization"><DispatchUtilizationTab /></TabsContent>
          <TabsContent value="idle"><DispatchIdleAlertsTab /></TabsContent>
          <TabsContent value="transfers"><DispatchTransfersTab /></TabsContent>
          <TabsContent value="holds"><DispatchHoldsTab /></TabsContent>
          <TabsContent value="integrations"><DispatchIntegrationsTab /></TabsContent>
        </Tabs>
      </main>

      <footer className="max-w-6xl mx-auto px-5 sm:px-8 py-6 w-full flex flex-col items-center gap-2">
        <ForgedOpsAttribution variant="footer" />
      </footer>
    </div>
  );
}
