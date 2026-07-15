// IntegrationHealthCard — cross-portal status card.
//
// Reads /api/integrations/health using whichever portal token the
// caller has (X-Safety-Token / X-HR-Token / X-Admin-Token — server
// resolves via multi-role gate). Shows Motive + MaintainX connection
// status, mapping counts, and last-sync deltas. Used on SafetyHub,
// ShopHub, HrHub, and AdminHub.
import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import {
  Activity, Cable, AlertTriangle, RefreshCcw, Loader2, ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_COLOR = {
  Connected:             "bg-emerald-100 text-emerald-900 border-emerald-300",
  "Ready for Credentials": "bg-amber-100 text-amber-900 border-amber-300",
  Syncing:               "bg-blue-100 text-blue-900 border-blue-300",
  Error:                 "bg-red-100 text-red-900 border-red-300",
  Disabled:              "bg-slate-200 text-slate-700 border-slate-300",
  "Not Connected":       "bg-slate-100 text-slate-600 border-slate-200",
};

/**
 * Props:
 *  - tokenHeader: { "X-Admin-Token": "..." } | { "X-Safety-Token": "..." } | { "X-HR-Token": "..." }
 *  - title: optional override
 *  - showAdminLink: if true, shows "Open Integration Center →"
 *  - accent: "slate" | "cyan" | "purple" | "orange" (matches portal accent)
 */
export default function IntegrationHealthCard({
  tokenHeader, title = "Integrations", showAdminLink = false, accent = "slate",
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${API}/integrations/health`, { headers: tokenHeader });
      setData(r.data);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [tokenHeader]);
  useEffect(() => { refresh(); }, [refresh]);

  const accentBorder = {
    slate:  "border-slate-700",
    cyan:   "border-cyan-700",
    purple: "border-purple-700",
    orange: "border-orange-700",
    indigo: "border-indigo-700",
  }[accent] || "border-slate-700";

  return (
    <div className={`bg-white border-2 ${accentBorder} rounded-md p-5`} data-testid="integration-health-card">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white shrink-0">
            <Cable className="w-5 h-5" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">Platform Integrations</div>
            <h3 className="font-display text-lg font-black text-slate-900 leading-tight mt-0.5">{title}</h3>
          </div>
        </div>
        <Button size="sm" variant="outline" onClick={refresh} disabled={loading} className="h-8" data-testid="integration-health-refresh">
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
        </Button>
      </div>

      {loading && !data ? (
        <div className="text-center text-slate-500 py-6"><Loader2 className="w-5 h-5 animate-spin mx-auto" /></div>
      ) : !data ? (
        <div className="text-sm text-slate-500 italic flex items-center gap-1">
          <AlertTriangle className="w-4 h-4 text-amber-500" /> Could not load integration health.
        </div>
      ) : (
        <div className="space-y-2">
          <ProviderRow
            label="Motive"
            sub="Telematics · GPS · driver safety"
            settings={data.motive}
          />
          <ProviderRow
            label="MaintainX"
            sub="Work orders · PMs · downtime"
            settings={data.maintainx}
          />
          <div className="mt-3 pt-3 border-t border-slate-100 grid grid-cols-2 gap-3 text-xs">
            <div className="font-mono">
              <div className="text-slate-500 uppercase tracking-[0.15em]">Assets mapped</div>
              <div className="text-slate-900 font-bold text-base">
                {data.counts?.asset_mappings_mapped ?? 0}
                <span className="text-slate-400 text-xs ml-1">/ {data.counts?.asset_mappings_total ?? 0}</span>
              </div>
            </div>
            <div className="font-mono">
              <div className="text-slate-500 uppercase tracking-[0.15em]">Drivers mapped</div>
              <div className="text-slate-900 font-bold text-base">
                {data.counts?.employee_mappings_mapped ?? 0}
                <span className="text-slate-400 text-xs ml-1">/ {data.counts?.employee_mappings_total ?? 0}</span>
              </div>
            </div>
          </div>
          {showAdminLink && (
            <a
              href="/admin/integrations"
              className="inline-flex items-center text-xs font-mono uppercase tracking-[0.18em] text-slate-700 hover:text-slate-900 mt-3 font-bold"
              data-testid="integration-health-admin-link"
            >
              Open Integration Center <ExternalLink className="w-3 h-3 ml-1" />
            </a>
          )}
        </div>
      )}
    </div>
  );
}

function ProviderRow({ label, sub, settings }) {
  const status = settings?.status || "Not Connected";
  const cls = STATUS_COLOR[status] || STATUS_COLOR["Not Connected"];
  return (
    <div className="flex items-center justify-between gap-3 py-2 border-b border-slate-100 last:border-b-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-display font-black text-sm">{label}</span>
          {settings?.demo_mode && (
            <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-700 text-[9px] font-mono uppercase tracking-[0.18em] font-bold">Demo</span>
          )}
        </div>
        <div className="text-[11px] text-slate-500">{sub}</div>
      </div>
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-mono uppercase tracking-[0.15em] font-bold ${cls}`}>
        <Activity className="w-2.5 h-2.5" /> {status}
      </span>
    </div>
  );
}
