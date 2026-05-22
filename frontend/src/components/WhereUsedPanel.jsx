// WhereUsedPanel — Iter140. Cross-portal footprint surface.
//
// Given an equipment_master_id or employee_master_id, fetches and
// renders every record across the platform that references it:
// incidents, corrective actions, inspections, fire extinguishers,
// training records. Deep-links each row to its source portal.
//
// Usage:
//   <WhereUsedPanel kind="equipment" masterId={id} />
//   <WhereUsedPanel kind="employee"  masterId={id} />
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity, AlertTriangle, ClipboardCheck, Flame,
  GraduationCap, ExternalLink, Loader2, Layers,
} from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Pretty labels + icons per collection key returned by the backend.
const COLLECTION_META = {
  incidents:               { label: "Incidents",            icon: AlertTriangle, accent: "red" },
  corrective_actions:      { label: "Corrective Actions",   icon: ClipboardCheck, accent: "amber" },
  equipment_inspections:   { label: "Inspections",          icon: Activity,       accent: "cyan" },
  fire_extinguishers:      { label: "Fire Extinguishers",   icon: Flame,          accent: "orange" },
  safety_training_records: { label: "Training Records",     icon: GraduationCap,  accent: "blue" },
};

const ACCENT = {
  red:    "border-red-300 bg-red-50 text-red-900",
  amber:  "border-amber-300 bg-amber-50 text-amber-900",
  cyan:   "border-cyan-300 bg-cyan-50 text-cyan-900",
  orange: "border-orange-300 bg-orange-50 text-orange-900",
  blue:   "border-blue-300 bg-blue-50 text-blue-900",
};

export default function WhereUsedPanel({ kind, masterId, compact = false }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!masterId) return;
    let alive = true;
    setLoading(true);
    setErr(null);
    const path = kind === "equipment"
      ? `${API}/master-lookup/equipment/${masterId}/where-used`
      : `${API}/master-lookup/employees/${masterId}/where-used`;
    axios.get(path)
      .then((r) => { if (alive) setData(r.data); })
      .catch((e) => { if (alive) setErr(e?.response?.data?.detail || "Could not load footprint"); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [kind, masterId]);

  if (!masterId) return null;

  if (loading) {
    return (
      <div className="border-2 border-dashed border-slate-200 rounded-md p-4 text-center text-slate-500" data-testid="where-used-loading">
        <Loader2 className="w-5 h-5 mx-auto animate-spin text-slate-400" />
        <div className="text-xs font-mono mt-1 uppercase tracking-[0.15em]">Loading footprint…</div>
      </div>
    );
  }

  if (err) {
    return (
      <div className="border-2 border-red-200 bg-red-50 rounded-md p-3 text-xs text-red-800 font-mono" data-testid="where-used-error">
        {err}
      </div>
    );
  }

  const total = data?.total || 0;
  const records = data?.records || {};

  return (
    <div className="border border-slate-200 rounded-md bg-white" data-testid={`where-used-${kind}`}>
      <div className="flex items-center justify-between px-3 py-2 border-b-2 border-slate-200 bg-slate-50">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">
          <Layers className="w-3.5 h-3.5" /> Cross-Portal Footprint
        </div>
        <span className="text-[10px] font-mono text-slate-500" data-testid="where-used-total">
          {total} record{total === 1 ? "" : "s"}
        </span>
      </div>

      {total === 0 ? (
        <div className="text-center text-slate-500 italic text-sm py-6" data-testid="where-used-empty">
          No cross-portal references on file yet.
        </div>
      ) : (
        <div className={`grid grid-cols-1 ${compact ? "" : "sm:grid-cols-2"} gap-3 p-3`}>
          {Object.entries(records).map(([collKey, items]) => {
            if (!items || items.length === 0) return null;
            const meta = COLLECTION_META[collKey] || { label: collKey, icon: Activity, accent: "cyan" };
            const Icon = meta.icon;
            return (
              <div
                key={collKey}
                className={`border-2 rounded-md p-3 ${ACCENT[meta.accent] || ACCENT.cyan}`}
                data-testid={`where-used-group-${collKey}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-[0.18em] font-bold">
                    <Icon className="w-3.5 h-3.5" /> {meta.label}
                  </div>
                  <span className="text-[10px] font-mono opacity-70">{items.length}</span>
                </div>
                <ul className="space-y-1.5">
                  {items.slice(0, 8).map((r) => (
                    <li key={r.id || r.label}>
                      <Link
                        to={r.route}
                        className="flex items-start gap-1.5 text-xs leading-snug hover:underline group"
                        data-testid={`where-used-row-${collKey}-${r.id}`}
                      >
                        <ExternalLink className="w-3 h-3 mt-0.5 shrink-0 opacity-60 group-hover:opacity-100" />
                        <span className="truncate">{r.label}</span>
                      </Link>
                    </li>
                  ))}
                  {items.length > 8 && (
                    <li className="text-[10px] italic opacity-70 font-mono pl-4">
                      + {items.length - 8} more…
                    </li>
                  )}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
