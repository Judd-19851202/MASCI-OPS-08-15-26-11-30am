// Admin Operations Event Log — central viewer for the operations
// event collection ("nervous system" of the platform).
import React, { useEffect, useState } from "react";
import { Activity, Loader2, RefreshCcw, Filter, ChevronLeft, ChevronRight } from "lucide-react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";

const SEV_PILL = {
  info:     "bg-slate-100 text-slate-700 border-slate-200",
  low:      "bg-blue-100 text-blue-900 border-blue-300",
  medium:   "bg-amber-100 text-amber-900 border-amber-300",
  high:     "bg-orange-100 text-orange-900 border-orange-300",
  critical: "bg-red-100 text-red-900 border-red-300",
};

const STATUS_PILL = {
  Open:          "bg-amber-100 text-amber-900 border-amber-300",
  "In Progress": "bg-blue-100 text-blue-900 border-blue-300",
  Closed:        "bg-emerald-100 text-emerald-900 border-emerald-300",
  Archived:      "bg-slate-200 text-slate-700 border-slate-300",
};

export default function AdminOperationsEvents() {
  const [data, setData] = useState({ rows: [], total: 0 });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ event_type: "", severity: "", status: "", source_module: "", asset_id: "" });
  const [offset, setOffset] = useState(0);
  const limit = 50;

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit, offset });
      Object.entries(filters).forEach(([k, v]) => v && params.append(k, v));
      const r = await api.get(`/operations/events?${params.toString()}`);
      setData(r.data);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [offset]);

  const apply = () => { setOffset(0); load(); };
  const reset = () => { setFilters({ event_type: "", severity: "", status: "", source_module: "", asset_id: "" }); setTimeout(load, 0); };

  return (
    <AdminShell title="Operations Event Log">
      <div className="max-w-7xl mx-auto" data-testid="admin-events-page">
        <div className="bg-white border border-slate-200 rounded-md p-5 mb-4">
          <div className="flex items-start gap-3">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-900 text-white shrink-0">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">Operations · Event Log</span>
              <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">Platform Operational History</h1>
              <p className="text-sm text-slate-600 mt-1">
                Append-only log of major operational events across Dispatch, Field Operations, Safety, Shop, and integration placeholders.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-md p-3 mb-3 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 items-end">
          <div><label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">Type</label><Input value={filters.event_type} onChange={(e) => setFilters({ ...filters, event_type: e.target.value })} placeholder="asset_assigned" className="h-8 text-xs" data-testid="evt-filter-type" /></div>
          <div><label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">Severity</label>
            <Select value={filters.severity || "any"} onValueChange={(v) => setFilters({ ...filters, severity: v === "any" ? "" : v })}>
              <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="any" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                {["info","low","medium","high","critical"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div><label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">Status</label>
            <Select value={filters.status || "any"} onValueChange={(v) => setFilters({ ...filters, status: v === "any" ? "" : v })}>
              <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="any" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                {["Open","In Progress","Closed","Archived"].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div><label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">Source</label><Input value={filters.source_module} onChange={(e) => setFilters({ ...filters, source_module: e.target.value })} placeholder="dispatch" className="h-8 text-xs" /></div>
          <div><label className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-500 font-bold">Asset id</label><Input value={filters.asset_id} onChange={(e) => setFilters({ ...filters, asset_id: e.target.value })} placeholder="UUID" className="h-8 text-xs" /></div>
          <div className="flex gap-1">
            <Button size="sm" onClick={apply} className="h-8" data-testid="evt-apply-filters"><Filter className="w-3.5 h-3.5 mr-1" />Apply</Button>
            <Button size="sm" variant="outline" onClick={reset} className="h-8">Reset</Button>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-md overflow-x-auto">
          {loading ? <div className="text-center py-8 text-slate-500"><Loader2 className="w-6 h-6 animate-spin mx-auto" /></div> : (
            <table className="w-full text-xs" data-testid="evt-table">
              <thead className="bg-slate-100 text-slate-700 font-mono uppercase tracking-[0.15em]">
                <tr>
                  <th className="text-left px-3 py-2">When</th>
                  <th className="text-left px-3 py-2">Type</th>
                  <th className="text-left px-3 py-2">Title</th>
                  <th className="text-left px-3 py-2">Source</th>
                  <th className="text-left px-3 py-2">Asset</th>
                  <th className="text-left px-3 py-2">Severity</th>
                  <th className="text-left px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.map((e) => (
                  <tr key={e.id} className="border-t border-slate-100">
                    <td className="px-3 py-2 font-mono text-slate-500 whitespace-nowrap">{(e.created_at || "").slice(0,16).replace("T"," ")}</td>
                    <td className="px-3 py-2 font-mono whitespace-nowrap">{e.event_type}</td>
                    <td className="px-3 py-2">{e.event_title}</td>
                    <td className="px-3 py-2 text-slate-500">{e.source_module}</td>
                    <td className="px-3 py-2 font-mono text-slate-500">{e.asset_id ? e.asset_id.slice(0,8) : "—"}</td>
                    <td className="px-3 py-2"><span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${SEV_PILL[e.severity] || ""}`}>{e.severity}</span></td>
                    <td className="px-3 py-2"><span className={`px-1.5 py-0.5 rounded border text-[9px] font-mono uppercase tracking-[0.15em] font-bold ${STATUS_PILL[e.status] || ""}`}>{e.status}</span></td>
                  </tr>
                ))}
                {data.rows.length === 0 && <tr><td colSpan="7" className="text-center text-slate-500 italic py-6">No events match the current filters.</td></tr>}
              </tbody>
            </table>
          )}
        </div>

        <div className="flex items-center justify-between mt-3 text-xs text-slate-500">
          <span>Showing {data.rows.length} of {data.total}</span>
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - limit))}><ChevronLeft className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="outline" disabled={offset + limit >= data.total || loading} onClick={() => setOffset(offset + limit)}><ChevronRight className="w-3.5 h-3.5" /></Button>
            <Button size="sm" variant="outline" onClick={load} aria-label="Refresh events" title="Refresh"><RefreshCcw className="w-3.5 h-3.5" /></Button>
          </div>
        </div>
      </div>
    </AdminShell>
  );
}
