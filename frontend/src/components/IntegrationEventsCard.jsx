// IntegrationEventsCard — reusable cross-portal placeholder card for
// Motive driver-safety events and MaintainX work orders.
//
// Reads /api/integrations/{motive/events|maintainx/work-orders}.
// Empty state renders when no rows are returned (typical until demo
// mode is enabled or live data lands). Demo mode is controlled per-
// provider in the Admin Integration Center.
import React, { useEffect, useState } from "react";
import axios from "axios";
import {
  Activity, Wrench, AlertOctagon, Loader2, RefreshCcw, ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SEVERITY = {
  high:     "bg-red-100 text-red-900 border-red-300",
  medium:   "bg-amber-100 text-amber-900 border-amber-300",
  low:      "bg-slate-100 text-slate-800 border-slate-300",
  critical: "bg-red-200 text-red-900 border-red-400",
};

const STATUS = {
  Open:          "bg-amber-100 text-amber-900 border-amber-300",
  "In Progress": "bg-blue-100 text-blue-900 border-blue-300",
  Done:          "bg-emerald-100 text-emerald-900 border-emerald-300",
  Closed:        "bg-slate-200 text-slate-700 border-slate-300",
};

const ACCENT_BORDER = {
  slate:  "border-slate-700",
  cyan:   "border-cyan-700",
  purple: "border-purple-700",
  orange: "border-orange-700",
  indigo: "border-indigo-700",
};

/**
 * Props:
 *   provider: "motive" | "maintainx"
 *   tokenHeader: { "X-Admin-Token": ... } | { "X-Safety-Token": ... } etc
 *   title: optional
 *   accent: "slate" (default) | "cyan" | "purple" | "orange" | "indigo"
 *   limit: number of rows to show (default 5)
 */
export default function IntegrationEventsCard({
  provider, tokenHeader, title, accent = "slate", limit = 5,
}) {
  const [rows, setRows] = useState(null);
  const [loading, setLoading] = useState(true);

  const isMotive = provider === "motive";
  const url = isMotive
    ? `${API}/integrations/motive/events`
    : `${API}/integrations/maintainx/work-orders`;
  const Icon = isMotive ? Activity : Wrench;
  const heading = title || (isMotive
    ? "Driver Safety Events"
    : "Open Work Orders");
  const sub = isMotive
    ? "Motive · Telematics & coaching events"
    : "MaintainX · Maintenance & repairs";

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await axios.get(`${url}?limit=${limit}`, { headers: tokenHeader });
      setRows(Array.isArray(r.data) ? r.data : []);
    } catch {
      setRows([]);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { refresh(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [provider]);

  const border = ACCENT_BORDER[accent] || ACCENT_BORDER.slate;

  return (
    <div
      className={`bg-white border-2 ${border} rounded-md p-5`}
      data-testid={`integration-events-card-${provider}`}
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white shrink-0">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              {sub}
            </div>
            <h3 className="font-display text-lg font-black text-slate-900 leading-tight mt-0.5">
              {heading}
            </h3>
          </div>
        </div>
        <Button
          size="sm" variant="outline" onClick={refresh} disabled={loading}
          className="h-8"
          data-testid={`integration-events-refresh-${provider}`}
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCcw className="w-3.5 h-3.5" />}
        </Button>
      </div>

      {loading && rows === null ? (
        <div className="text-center text-slate-500 py-6">
          <Loader2 className="w-5 h-5 animate-spin mx-auto" />
        </div>
      ) : !rows || rows.length === 0 ? (
        <EmptyState provider={provider} />
      ) : (
        <ul className="divide-y divide-slate-100" data-testid={`integration-events-list-${provider}`}>
          {rows.slice(0, limit).map((row) => (
            isMotive ? <MotiveRow key={row.id} row={row} /> : <WorkOrderRow key={row.id} row={row} />
          ))}
        </ul>
      )}
    </div>
  );
}

function EmptyState({ provider }) {
  const isMotive = provider === "motive";
  return (
    <div
      className="border-2 border-dashed border-slate-200 rounded-md p-5 text-center"
      data-testid={`integration-events-empty-${provider}`}
    >
      <AlertOctagon className="w-6 h-6 text-slate-300 mx-auto mb-2" />
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
        No records yet
      </div>
      <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
        {isMotive
          ? "Driver-safety events will appear here once the Motive integration is connected. Admins can enable Demo Mode in the Integration Center to preview the populated UI."
          : "MaintainX work orders will appear here once the integration is connected. Admins can enable Demo Mode in the Integration Center to preview the populated UI."}
      </p>
    </div>
  );
}

function MotiveRow({ row }) {
  const sev = SEVERITY[row.severity] || SEVERITY.low;
  const when = (row.event_at || "").slice(0, 16).replace("T", " ");
  return (
    <li className="py-2.5 flex items-start gap-3" data-testid={`motive-event-row-${row.id}`}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-bold text-sm capitalize">
            {row.event_type_label || (row.event_type || "").replace(/_/g, " ")}
          </span>
          <span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${sev}`}>
            {row.severity}
          </span>
          {row.is_demo && (
            <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 text-[9px] font-mono uppercase tracking-[0.15em] font-bold">
              Demo
            </span>
          )}
          {row.coaching_required && (
            <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-900 text-[9px] font-mono uppercase tracking-[0.15em] font-bold">
              Coach
            </span>
          )}
          {row.notify && (
            <span className="px-1.5 py-0.5 rounded bg-red-700 text-white text-[9px] font-mono uppercase tracking-[0.15em] font-bold" data-testid="motive-event-notify">
              Bell
            </span>
          )}
        </div>
        <div className="text-xs text-slate-600 truncate" data-testid="motive-event-summary">
          {row.summary || `${row.driver_name || "—"} · ${row.unit_number || "—"}${row.location?.address ? ` · ${row.location.address}` : ""}`}
        </div>
        {row.details && (
          <div className="text-[11px] text-slate-500 mt-0.5 truncate">{row.details}</div>
        )}
      </div>
      <div className="text-[10px] font-mono text-slate-400 shrink-0 pt-1">{when}</div>
    </li>
  );
}

function WorkOrderRow({ row }) {
  const sts = STATUS[row.status] || STATUS.Open;
  const sev = SEVERITY[row.priority] || SEVERITY.medium;
  return (
    <li className="py-2.5 flex items-start gap-3" data-testid={`maintainx-wo-row-${row.id}`}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs font-bold">{row.wo_number || "—"}</span>
          <span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${sts}`}>
            {row.status}
          </span>
          <span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${sev}`}>
            {row.priority}
          </span>
          {row.is_demo && (
            <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 text-[9px] font-mono uppercase tracking-[0.15em] font-bold">
              Demo
            </span>
          )}
          {row.safety_related && (
            <span className="px-1.5 py-0.5 rounded bg-red-50 text-red-800 text-[9px] font-mono uppercase tracking-[0.15em] font-bold">
              Safety
            </span>
          )}
          {row.equipment_down && (
            <span className="px-1.5 py-0.5 rounded bg-slate-200 text-slate-800 text-[9px] font-mono uppercase tracking-[0.15em] font-bold">
              Down
            </span>
          )}
        </div>
        <div className="text-sm font-bold truncate">{row.title || "—"}</div>
        <div className="text-[11px] text-slate-500 truncate">
          {row.unit_number || "—"} · {row.assigned_technician_name || "Unassigned"}
          {row.due_date ? ` · Due ${row.due_date}` : ""}
        </div>
      </div>
      <ChevronRight className="w-4 h-4 text-slate-300 mt-1 shrink-0" />
    </li>
  );
}
