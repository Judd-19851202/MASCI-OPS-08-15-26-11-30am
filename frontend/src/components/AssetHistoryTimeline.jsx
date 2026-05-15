// AssetHistoryTimeline — Iter141. Chronological merged history feed
// for one equipment_master_id or employee_master_id. Used inside the
// EquipmentMasterPanel edit dialog + SafetyEmployeeProfiles + as the
// body of the dedicated /admin/equipment/:id/history full-page view.
//
// Props:
//   kind: "equipment" | "employee"
//   masterId: string
//   compact?: boolean — collapse subtitles + hide summary chips
//   limit?: number — clip the list (default unlimited)
import React, { useEffect, useState } from "react";
import {
  Activity, AlertTriangle, ClipboardCheck, Flame,
  GraduationCap, Wrench, UserCog, Calendar, Loader2,
  ExternalLink, Clock,
} from "lucide-react";
import { Link } from "react-router-dom";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const KIND_META = {
  incident:            { label: "Incident",            icon: AlertTriangle, dot: "bg-red-600",     ring: "ring-red-200"     },
  ca:                  { label: "Corrective Action",   icon: ClipboardCheck, dot: "bg-amber-600",   ring: "ring-amber-200"   },
  inspection:          { label: "Inspection",          icon: Activity,       dot: "bg-cyan-700",    ring: "ring-cyan-200"    },
  fire_ext_inspection: { label: "Fire Ext Inspection", icon: Flame,          dot: "bg-orange-600",  ring: "ring-orange-200"  },
  training:            { label: "Training",            icon: GraduationCap,  dot: "bg-blue-700",    ring: "ring-blue-200"    },
  operations_event:    { label: "Operations Event",    icon: Wrench,         dot: "bg-slate-700",   ring: "ring-slate-200"   },
  field_leadership:    { label: "HR / Leadership",     icon: UserCog,        dot: "bg-purple-700",  ring: "ring-purple-200"  },
};

const statusClass = (s) => {
  if (!s) return "";
  const u = String(s).toUpperCase();
  if (["PASS", "CLOSED", "COMPLETED", "RESOLVED"].includes(u)) return "bg-emerald-100 text-emerald-800 border-emerald-300";
  if (["FAIL", "OPEN", "OVERDUE", "BLOCKED"].includes(u))       return "bg-red-100 text-red-800 border-red-300";
  return "bg-slate-100 text-slate-700 border-slate-300";
};

const severityClass = (s) => {
  if (!s) return "";
  const u = String(s).toLowerCase();
  if (u.includes("critical") || u.includes("major")) return "bg-red-100 text-red-800 border-red-300";
  if (u.includes("minor"))                            return "bg-amber-100 text-amber-800 border-amber-300";
  return "bg-slate-100 text-slate-700 border-slate-300";
};

export default function AssetHistoryTimeline({ kind, masterId, compact = false, limit }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!masterId) return;
    let alive = true;
    setLoading(true);
    setErr(null);
    const url = kind === "equipment"
      ? `${API}/master-lookup/equipment/${masterId}/history`
      : `${API}/master-lookup/employees/${masterId}/history`;
    axios.get(url)
      .then((r) => { if (alive) setData(r.data); })
      .catch((e) => { if (alive) setErr(e?.response?.data?.detail || "Failed to load history"); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [kind, masterId]);

  if (!masterId) return null;

  if (loading) {
    return (
      <div className="border-2 border-dashed border-slate-200 rounded-md p-4 text-center text-slate-500" data-testid="asset-history-loading">
        <Loader2 className="w-5 h-5 mx-auto animate-spin text-slate-400" />
        <div className="text-xs font-mono mt-1 uppercase tracking-[0.15em]">Loading history…</div>
      </div>
    );
  }

  if (err) {
    return (
      <div className="border-2 border-red-200 bg-red-50 rounded-md p-3 text-xs text-red-800 font-mono" data-testid="asset-history-error">
        {err}
      </div>
    );
  }

  const events = (data?.events || []).slice(0, limit || undefined);
  const summary = data?.summary || {};

  return (
    <div className="border-2 border-slate-300 rounded-md bg-white" data-testid={`asset-history-${kind}`}>
      <div className="flex items-center justify-between px-3 py-2 border-b-2 border-slate-200 bg-slate-50">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
          <Clock className="w-3.5 h-3.5" /> Chronological History
        </div>
        <span className="text-[10px] font-mono text-slate-500" data-testid="asset-history-total">
          {data?.total || 0} event{(data?.total || 0) === 1 ? "" : "s"}
        </span>
      </div>

      {!compact && Object.keys(summary).length > 0 && (
        <div className="px-3 py-2 border-b border-slate-100 flex flex-wrap gap-1.5" data-testid="asset-history-summary">
          {Object.entries(summary).map(([k, n]) => {
            const meta = KIND_META[k] || { label: k };
            return (
              <span key={k} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[10px] font-mono">
                <span className={`w-1.5 h-1.5 rounded-full ${meta.dot || "bg-slate-500"}`}></span>
                {meta.label} <strong className="ml-0.5">{n}</strong>
              </span>
            );
          })}
        </div>
      )}

      {events.length === 0 ? (
        <div className="text-center text-slate-500 italic text-sm py-6" data-testid="asset-history-empty">
          No events on record yet.
        </div>
      ) : (
        <ol className="relative p-4 space-y-3">
          {/* Vertical rail */}
          <div className="absolute left-[1.4rem] top-4 bottom-4 w-[2px] bg-slate-200 pointer-events-none" />
          {events.map((e, idx) => {
            const meta = KIND_META[e.kind] || { label: e.kind, icon: Activity, dot: "bg-slate-500", ring: "ring-slate-200" };
            const Icon = meta.icon;
            return (
              <li key={`${e.kind}-${e.record_id || idx}`} className="relative pl-12" data-testid={`asset-history-item-${idx}`}>
                <div className={`absolute left-2 top-1 w-7 h-7 rounded-full ${meta.dot} ring-4 ${meta.ring} flex items-center justify-center text-white shadow-sm`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="border border-slate-200 rounded-md p-2.5 hover:border-slate-400 hover:shadow-sm transition-all bg-white">
                  <div className="flex items-start justify-between gap-2 flex-wrap">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500">
                        <Calendar className="w-3 h-3" />
                        <span data-testid={`asset-history-date-${idx}`}>{(e.at || "—").slice(0, 10)}</span>
                        <span className="text-slate-300">·</span>
                        <span className="font-bold text-slate-700">{meta.label}</span>
                      </div>
                      <div className="font-bold text-sm text-slate-900 mt-0.5 break-words" data-testid={`asset-history-title-${idx}`}>{e.title || "—"}</div>
                      {!compact && e.subtitle && (
                        <div className="text-xs text-slate-600 mt-0.5 break-words">{e.subtitle}</div>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {e.status && (
                        <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${statusClass(e.status)}`}>
                          {e.status}
                        </span>
                      )}
                      {e.severity && (
                        <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${severityClass(e.severity)}`}>
                          {e.severity}
                        </span>
                      )}
                      {e.route && (
                        <Link
                          to={e.route}
                          className="p-1 text-slate-400 hover:text-slate-900 rounded hover:bg-slate-100"
                          data-testid={`asset-history-link-${idx}`}
                          title="Open record"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      )}
                    </div>
                  </div>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
