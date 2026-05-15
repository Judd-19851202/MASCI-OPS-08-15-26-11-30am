// Dispatch Portal hub — the dedicated dispatcher workspace.
// Reuses the proven tab components from AdminDispatch (re-exported)
// so the dispatcher and admin views show identical data, but renders
// inside its own portal chrome (no AdminShell sidebar).
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Truck, Send, ShieldAlert, Activity, LogOut, Clock,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import PortalSwitcher from "@/components/PortalSwitcher";
import {
  DispatchOverviewTab, DispatchUtilizationTab, DispatchIdleAlertsTab,
  DispatchTransfersTab, DispatchHoldsTab,
} from "@/pages/admin/AdminDispatch";
import { clearDispatchToken, getDispatchUser } from "@/lib/dispatchAuth";

export default function DispatchHub() {
  const nav = useNavigate();
  const [tab, setTab] = useState("overview");
  const user = getDispatchUser() || {};

  const logout = () => {
    clearDispatchToken();
    nav("/dispatch-portal/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="dispatch-hub">
      <header className="bg-slate-950 text-white border-b-4 border-orange-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-3 flex-wrap">
          <MasciLogo className="h-8 w-auto" />
          <div className="flex-1 min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-orange-300 font-bold">
              Dispatch Portal
            </div>
            <div className="font-display text-lg sm:text-xl font-black leading-tight">
              {user.name || "Dispatcher"}
            </div>
          </div>
          <PortalSwitcher />
          <Button variant="outline" size="sm" onClick={logout} className="bg-transparent text-white border-white/30 hover:bg-white/10" data-testid="dispatch-logout">
            <LogOut className="w-3.5 h-3.5 mr-1" /> Sign out
          </Button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-4">
        <div className="bg-white border-2 border-slate-300 rounded-md p-5">
          <div className="flex items-start gap-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-orange-600 text-white shrink-0">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
                Dispatch Portal · iter126
              </span>
              <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
                Equipment Movement Command Center
              </h1>
              <p className="text-sm text-slate-600 mt-1">
                Availability · transfers · holds · utilization · idle alerts. Signed in as
                a dispatch user — admin escalation is NOT required.
              </p>
            </div>
          </div>
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="flex-wrap h-auto">
            <TabsTrigger value="overview" data-testid="dh-tab-overview"><Activity className="w-3.5 h-3.5 mr-1" /> Overview</TabsTrigger>
            <TabsTrigger value="utilization" data-testid="dh-tab-utilization"><Activity className="w-3.5 h-3.5 mr-1" /> Utilization</TabsTrigger>
            <TabsTrigger value="idle" data-testid="dh-tab-idle"><Clock className="w-3.5 h-3.5 mr-1" /> Idle Alerts</TabsTrigger>
            <TabsTrigger value="transfers" data-testid="dh-tab-transfers"><Send className="w-3.5 h-3.5 mr-1" /> Transfers</TabsTrigger>
            <TabsTrigger value="holds" data-testid="dh-tab-holds"><ShieldAlert className="w-3.5 h-3.5 mr-1" /> Holds</TabsTrigger>
          </TabsList>
          <TabsContent value="overview"><DispatchOverviewTab /></TabsContent>
          <TabsContent value="utilization"><DispatchUtilizationTab /></TabsContent>
          <TabsContent value="idle"><DispatchIdleAlertsTab /></TabsContent>
          <TabsContent value="transfers"><DispatchTransfersTab /></TabsContent>
          <TabsContent value="holds"><DispatchHoldsTab /></TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
