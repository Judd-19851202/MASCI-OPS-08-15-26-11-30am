// TrenchSafetyOnProjectPanel — calm, read-only panel that surfaces the
// trench safety assets currently assigned to a given project.
//
// Phase 4A · MASCI Trench Safety Operations System.
// Embedded on /pm/projects/{projectNumber} (and any other per-project
// surface that wants to display field-deployed trench safety hardware).
//
// Read-only. No actions — assignment lives in the Safety Portal.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Loader2, Boxes, ExternalLink, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";

const STATUS_BADGE = {
  "Available":       "bg-emerald-50 text-emerald-900 border-emerald-300",
  "Assigned":        "bg-blue-50 text-blue-900 border-blue-300",
  "In Transport":    "bg-cyan-50 text-cyan-900 border-cyan-300",
  "Inspection Hold": "bg-amber-50 text-amber-900 border-amber-400",
  "Repair":          "bg-red-50 text-red-900 border-red-300",
  "Retired":         "bg-slate-100 text-slate-600 border-slate-300",
};

const CONDITION_BADGE = {
  "Excellent":     "text-emerald-700",
  "Good":          "text-emerald-700",
  "Fair":          "text-amber-700",
  "Poor":          "text-red-700",
  "Out Of Service":"text-red-700",
};

export default function TrenchSafetyOnProjectPanel({
  projectNumber,
  projectName,
  projectId,
}) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!projectNumber && !projectName && !projectId) {
        setLoading(false);
        return;
      }
      setLoading(true);
      setErr("");
      try {
        const params = {};
        if (projectId) params.project_id = projectId;
        if (projectNumber) params.project_number = projectNumber;
        if (projectName) params.project_name = projectName;
        const r = await api.get("/trench-safety/by-project", { params });
        if (!cancelled) setItems(r.data?.current || []);
      } catch (e) {
        if (!cancelled) setErr(e?.response?.data?.detail || e?.message || "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [projectNumber, projectName, projectId]);

  return (
    <section
      className="mt-6 bg-white border border-slate-200 rounded-md shadow-sm"
      data-testid="trench-on-project-panel"
    >
      <header className="bg-slate-900 text-white px-5 py-3 flex items-center gap-3 flex-wrap">
        <Boxes className="w-5 h-5 text-cyan-300" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-cyan-300 font-bold flex-1">
          Trench Safety Assets on this Project
        </span>
        <span className="text-[11px] font-mono text-slate-300" data-testid="trench-on-project-count">
          {items.length} {items.length === 1 ? "asset" : "assets"}
        </span>
      </header>

      <div className="p-4">
        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 py-4" data-testid="trench-on-project-loading">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : err ? (
          <div className="p-3 border border-red-300 bg-red-50 rounded text-red-900 text-sm" data-testid="trench-on-project-error">
            {err}
          </div>
        ) : items.length === 0 ? (
          <div className="py-6 text-center text-sm text-slate-500 italic" data-testid="trench-on-project-empty">
            No trench safety assets currently assigned to this project.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">Asset</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">Type</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">Size</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">Condition</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">Status</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">Last Inspection</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">Location</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((a) => (
                  <tr key={a.asset_id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`trench-on-project-row-${a.asset_id}`}>
                    <td className="px-3 py-2 font-mono font-bold text-slate-900">{a.asset_id}</td>
                    <td className="px-3 py-2 text-slate-700 text-xs">{a.asset_type || "—"}</td>
                    <td className="px-3 py-2 text-slate-700 text-xs">{a.size || "—"}</td>
                    <td className={`px-3 py-2 text-xs font-bold ${CONDITION_BADGE[a.condition] || "text-slate-700"}`}>{a.condition || "—"}</td>
                    <td className="px-3 py-2">
                      <span className={`inline-block px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${STATUS_BADGE[a.operational_status] || "bg-slate-50 text-slate-700 border-slate-300"}`}>
                        {a.operational_status || "Available"}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-xs font-mono text-slate-600">
                      {a.last_inspection_at ? a.last_inspection_at.slice(0, 10) : <span className="text-amber-700">none</span>}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">{a.current_location || "—"}</td>
                    <td className="px-3 py-2">
                      <Link
                        to={`/trench-safety/assets/${a.asset_id}`}
                        className="inline-flex items-center justify-center text-cyan-700 hover:text-cyan-900"
                        title="Open field view"
                        data-testid={`trench-on-project-open-${a.asset_id}`}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-3 p-2 border border-slate-200 bg-slate-50 rounded text-[11px] text-slate-600 flex items-start gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 mt-0.5 shrink-0 text-amber-700" />
          <span>
            Read-only. Assignment and inspection management live in the{" "}
            <Link to="/safety/trench-safety" className="underline text-cyan-800">Safety Portal · Trench Safety</Link>.
          </span>
        </div>
      </div>
    </section>
  );
}
