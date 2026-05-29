// DispatchIntegrationsTab — Iter132. Motive + MaintainX readiness
// cards inside the Dispatch Portal. Reads /api/admin/integrations/overview
// when admin token is available; otherwise renders a clean empty
// state pointing at the Admin Integration Center. NEVER mutates
// equipment_master — purely visibility.
import React, { useEffect, useState } from "react";
import {
  Cable, MapPin, Wrench, AlertCircle, CheckCircle2, Loader2, ExternalLink,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { getDispatchToken } from "@/lib/dispatchAuth";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function dispatchHeaders() {
  const t = getDispatchToken();
  return t ? { "X-Dispatch-Token": t } : {};
}

const STATUS_CHIP = {
  green:  "bg-emerald-700 text-white",
  yellow: "bg-amber-600 text-white",
  red:    "bg-red-700 text-white",
  off:    "bg-slate-500 text-white",
};

export default function DispatchIntegrationsTab() {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        // Cross-portal endpoint; accepts dispatch + admin tokens.
        const r = await axios.get(`${API}/operations/integration-readiness`, {
          headers: dispatchHeaders(),
        });
        setOverview(r.data);
      } catch {
        setOverview(null);
      } finally { setLoading(false); }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="text-center py-12 text-slate-500" data-testid="dispatch-integrations-loading">
        <Loader2 className="w-6 h-6 animate-spin mx-auto" />
      </div>
    );
  }

  const motive = overview?.motive || {};
  const maintainx = overview?.maintainx || {};

  return (
    <div className="space-y-4" data-testid="dispatch-integrations-tab">
      <div className="bg-white border border-slate-200 rounded-md p-5">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
            <Cable className="w-6 h-6" />
          </div>
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              Integration Readiness · iter132
            </span>
            <h2 className="font-display text-xl font-black tracking-tight mt-0.5">
              Motive + MaintainX Visibility
            </h2>
            <p className="text-sm text-slate-600 mt-1">
              Read-only operational readiness. Live data appears once Admin enables the integration.
              Master equipment records are never overwritten by external systems.
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
        <IntegrationCard
          provider="Motive"
          icon={MapPin}
          accent="bg-blue-700"
          settings={motive}
          rows={[
            { label: "Tracked Assets",        value: motive.tracked_assets,          tip: "Equipment with a Motive mapping." },
            { label: "Last Telemetry Sync",   value: motive.last_sync_at || "—",     tip: "Most recent location/telemetry pull." },
            { label: "Idle Assets",           value: motive.idle_count,              tip: "Reporting but no movement >7d." },
            { label: "Not Reporting",         value: motive.not_reporting,           tip: "Mapped but no recent telemetry." },
            { label: "Unmapped Motive Units", value: motive.unmapped_external,       tip: "External units not yet tied to a MASCI asset." },
          ]}
          emptyLabel="Awaiting Motive integration configuration. GPS, telematics, and asset tracking data will appear here once Admin enables the integration."
          adminLink="/admin/integrations"
          dataTestId="dispatch-card-motive"
        />

        <IntegrationCard
          provider="MaintainX"
          icon={Wrench}
          accent="bg-amber-700"
          settings={maintainx}
          rows={[
            { label: "Equipment Down",         value: maintainx.equipment_down,       tip: "Open critical-repair work orders." },
            { label: "Open Work Orders",       value: maintainx.open_work_orders,     tip: "Any open WO (PM + corrective)." },
            { label: "Overdue PMs",            value: maintainx.overdue_pms,          tip: "Preventive maintenance past due." },
            { label: "Maintenance Holds",      value: maintainx.maintenance_holds,    tip: "Active MASCI maintenance holds." },
            { label: "Unmapped MaintainX",     value: maintainx.unmapped_external,    tip: "External MaintainX assets not yet linked." },
          ]}
          emptyLabel="Awaiting MaintainX integration configuration. Maintenance, PM, repair, and equipment-down status will appear here once Admin enables the integration."
          adminLink="/admin/integrations"
          dataTestId="dispatch-card-maintainx"
        />
      </div>

      <div className="bg-slate-50 border-2 border-dashed border-slate-300 rounded-md p-4 text-xs text-slate-600">
        <strong className="block mb-1 font-mono uppercase tracking-[0.15em] text-slate-700">How this works</strong>
        Mapping records live in <code>asset_mappings</code> / <code>employee_mappings</code> — they tie MASCI master IDs to
        external Motive / MaintainX IDs without ever mutating <code>equipment_master</code> or <code>employees</code>.
        Dispatch reads the live numbers here; Admin manages the mappings at <Link to="/admin/integrations" className="font-bold text-slate-900 underline">/admin/integrations</Link>.
      </div>
    </div>
  );
}

function IntegrationCard({ provider, icon: Icon, accent, settings, rows, emptyLabel, adminLink, dataTestId }) {
  const enabled = !!settings?.enabled;
  const demo = !!settings?.demo_mode;
  const status = enabled ? "green" : demo ? "yellow" : "off";
  const statusLabel = enabled ? "Live" : demo ? "Demo Mode" : "Not Connected";

  return (
    <div className="bg-white border border-slate-200 rounded-md overflow-hidden" data-testid={dataTestId}>
      <div className="flex items-center gap-3 p-4 border-b-2 border-slate-200">
        <div className={`inline-flex items-center justify-center w-10 h-10 rounded-md ${accent} text-white shrink-0`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600 font-bold">{provider}</div>
          <div className="font-display text-base font-black truncate">{provider} Integration</div>
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-[0.18em] font-bold ${STATUS_CHIP[status]}`}>
          {statusLabel}
        </span>
      </div>

      {enabled || demo ? (
        <table className="w-full text-sm">
          <tbody>
            {rows.map((r) => (
              <tr key={r.label} className="border-b border-slate-100 last:border-b-0">
                <td className="px-4 py-2 text-slate-700" title={r.tip}>{r.label}</td>
                <td className="px-4 py-2 text-right font-mono font-bold">
                  {r.value !== undefined && r.value !== null ? String(r.value) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="p-5">
          <div className="flex items-start gap-2 bg-slate-50 border border-slate-200 rounded p-3 text-xs text-slate-700">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-slate-500" />
            <div>{emptyLabel}</div>
          </div>
          <Link to={adminLink}>
            <Button variant="outline" size="sm" className="mt-3 w-full" data-testid={`${dataTestId}-admin-link`}>
              <ExternalLink className="w-3.5 h-3.5 mr-1" />
              Open Admin Integration Center
            </Button>
          </Link>
        </div>
      )}
      {demo && (
        <div className="bg-amber-50 border-t-2 border-amber-200 px-4 py-2 text-[11px] font-mono uppercase tracking-[0.15em] text-amber-800 font-bold flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" /> Demo / Preview data only
        </div>
      )}
    </div>
  );
}
