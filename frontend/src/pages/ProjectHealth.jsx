// ProjectHealth.jsx — Phase H · Project / Job Health Dashboard.
//
// Per-project operational friction summary. Reads from
// GET /api/project-health (admin/exec/safety see all · PM scope-
// filtered · HR/Shop/Dispatch/FL get 403). NO charts, NO scoring
// engine, NO AI. Sortable table; deep-links to filtered list pages.
//
// Status ladder (deterministic, set server-side):
//   🟢 green = no friction
//   🟡 amber = ≥1 task overdue · ≥1 PO missing receipt · ≥1 doc
//             expiring in 14d · ≥1 CA overdue
//   🔴 red   = ≥1 doc expired · ≥1 PO overdue receipt · ≥1 open
//             incident with severity High/Critical · ≥3 tasks
//             overdue · ≥3 CAs overdue
//
// Mandatory legal footer (per user instruction): present at bottom.

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity, RefreshCw, ArrowUpDown, ChevronRight,
  AlertTriangle, Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

const STATUS_TINT = {
  green: "border-emerald-300 bg-emerald-50 text-emerald-800",
  amber: "border-amber-300 bg-amber-50 text-amber-900",
  red:   "border-rose-300   bg-rose-50   text-rose-900",
};
const STATUS_DOT = {
  green: "bg-emerald-500",
  amber: "bg-amber-500",
  red:   "bg-rose-500",
};
const STATUS_LABEL = {
  green: "Green",
  amber: "Amber",
  red:   "Red",
};

// Each indicator: label + deep-link template. project_number is
// injected when building the row link.
const INDICATORS = [
  { key: "tasks_overdue",         label: "Overdue tasks",
    url:  (pn) => `/tasks?status=Overdue&linked_project_number=${encodeURIComponent(pn)}` },
  { key: "pos_pending_approval",  label: "POs pending",
    url:  (pn) => `/po-requests?status=Pending Approval&project_number=${encodeURIComponent(pn)}` },
  { key: "pos_missing_receipt",   label: "POs missing receipt",
    url:  (pn) => `/po-requests?quick=pending_receipt&project_number=${encodeURIComponent(pn)}` },
  { key: "pos_overdue_receipt",   label: "POs overdue receipt",
    url:  (pn) => `/po-requests?status=Overdue Receipt&project_number=${encodeURIComponent(pn)}` },
  { key: "docs_expiring",         label: "Docs expiring 14d",
    url:  (pn) => `/document-expirations?status=Expiring Soon&project_number=${encodeURIComponent(pn)}` },
  { key: "docs_expired",          label: "Docs expired",
    url:  (pn) => `/document-expirations?status=Expired&project_number=${encodeURIComponent(pn)}` },
  { key: "incidents_open",        label: "Incidents open",
    url:  (pn) => `/incidents?project_number=${encodeURIComponent(pn)}` },
  { key: "ca_overdue",            label: "CAs overdue",
    url:  (pn) => `/safety-portal/corrective-actions?project_number=${encodeURIComponent(pn)}` },
];

// Sort options. Default = worst-first (status + total).
const SORT_OPTIONS = [
  { key: "worst",            label: "Worst first" },
  { key: "project_asc",      label: "Project # A→Z" },
  { key: "project_desc",     label: "Project # Z→A" },
  { key: "name_asc",         label: "Name A→Z" },
];

const STATUS_FILTERS = [
  { key: "all",   label: "All" },
  { key: "red",   label: "Red only" },
  { key: "amber", label: "Amber only" },
  { key: "green", label: "Green only" },
];

function applySort(rows, sort) {
  const out = [...rows];
  if (sort === "worst") return out;  // server already worst-first
  if (sort === "project_asc")
    return out.sort((a, b) => a.project_number.localeCompare(b.project_number));
  if (sort === "project_desc")
    return out.sort((a, b) => b.project_number.localeCompare(a.project_number));
  if (sort === "name_asc")
    return out.sort((a, b) => (a.project_name || "").localeCompare(b.project_name || ""));
  return out;
}

export default function ProjectHealth() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sort, setSort] = useState("worst");
  const [statusFilter, setStatusFilter] = useState("all");
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.get("/project-health");
      setData(r.data);
    } catch (e) {
      const code = e?.response?.status;
      if (code === 403) {
        setError("forbidden");
      } else if (code === 401) {
        setError("auth");
      } else {
        setError(e?.response?.data?.detail || e.message || "load failed");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const visibleRows = useMemo(() => {
    if (!data?.rows) return [];
    const filtered = statusFilter === "all"
      ? data.rows
      : data.rows.filter((r) => r.status === statusFilter);
    return applySort(filtered, sort);
  }, [data, sort, statusFilter]);

  if (error === "forbidden") {
    return (
      <div className="max-w-3xl mx-auto p-6">
        <div className="border-2 border-amber-300 bg-amber-50 text-amber-900 p-4 rounded-md font-mono text-sm" data-testid="project-health-forbidden">
          Project Health is restricted to Admin · PM · Safety · Executive roles.
        </div>
      </div>
    );
  }

  if (error === "auth") {
    return null;
  }

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6" data-testid="project-health-page">
      <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
        <div className="flex items-center gap-3 min-w-0">
          <Activity className="w-5 h-5 text-slate-700 shrink-0" />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold font-display text-slate-900 leading-tight">
              Project Health
            </h1>
            <p className="text-[11px] font-mono uppercase tracking-[0.16em] text-slate-500 mt-0.5">
              Operational friction by job · live data
            </p>
          </div>
        </div>
        <Button
          onClick={load}
          variant="outline"
          size="sm"
          disabled={loading}
          data-testid="project-health-refresh"
        >
          {loading
            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
            : <RefreshCw className="w-3.5 h-3.5" />}
          <span className="ml-1.5 text-xs">Refresh</span>
        </Button>
      </div>

      {/* Summary strip */}
      {data?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3 mb-4" data-testid="project-health-summary">
          {["red", "amber", "green"].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s === statusFilter ? "all" : s)}
              className={`border-2 rounded-md p-3 text-left transition-colors ${STATUS_TINT[s]} ${statusFilter === s ? "ring-2 ring-slate-900" : ""}`}
              data-testid={`project-health-summary-${s}`}
            >
              <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold">
                {STATUS_LABEL[s]}
              </div>
              <div className="text-2xl font-bold leading-none mt-1">
                {data.summary[s] ?? 0}
              </div>
            </button>
          ))}
          <div className="border-2 border-slate-300 bg-white text-slate-700 rounded-md p-3" data-testid="project-health-summary-total">
            <div className="text-[10px] font-mono uppercase tracking-[0.16em] font-bold">Total Active</div>
            <div className="text-2xl font-bold leading-none mt-1">
              {data.summary.total ?? 0}
            </div>
          </div>
        </div>
      )}

      {/* Filter + sort row */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">Filter</div>
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setStatusFilter(f.key)}
            className={`text-xs font-mono px-2 py-1 rounded border-2 transition-colors ${
              statusFilter === f.key
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
            }`}
            data-testid={`project-health-filter-${f.key}`}
          >
            {f.label}
          </button>
        ))}
        <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500 ml-3">Sort</div>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="border-2 border-slate-300 rounded font-mono text-xs px-2 py-1 bg-white"
          data-testid="project-health-sort"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.key} value={o.key}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && error !== "forbidden" && error !== "auth" && (
        <div className="border-2 border-rose-300 bg-rose-50 text-rose-800 p-3 rounded-md font-mono text-xs mb-3" data-testid="project-health-error">
          Load failed: {String(error)}
        </div>
      )}

      {/* Loading */}
      {loading && !data && (
        <div className="border border-slate-200 bg-white p-4 rounded-md font-mono text-xs text-slate-500" data-testid="project-health-loading">
          Loading project friction map…
        </div>
      )}

      {/* Empty */}
      {!loading && data && visibleRows.length === 0 && (
        <div className="border-2 border-dashed border-slate-300 bg-white text-slate-500 italic p-6 rounded-md text-center text-sm" data-testid="project-health-empty">
          No projects match the current filter.
        </div>
      )}

      {/* Table */}
      {visibleRows.length > 0 && (
        <div className="border-2 border-slate-300 bg-white rounded-md overflow-hidden" data-testid="project-health-table">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-50 border-b-2 border-slate-200">
                <tr>
                  <th className="text-left p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600 w-20">Status</th>
                  <th className="text-left p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600 sticky left-0 bg-slate-50">Project</th>
                  {INDICATORS.map((i) => (
                    <th
                      key={i.key}
                      className="text-center p-2 font-mono uppercase tracking-wider text-[10px] text-slate-600 whitespace-nowrap"
                      title={i.label}
                    >
                      {i.label}
                    </th>
                  ))}
                  <th className="w-8 p-2" aria-hidden="true" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visibleRows.map((r) => (
                  <ProjectRow key={r.project_number} row={r} onNavigate={navigate} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Mandatory legal/operational disclaimer footer */}
      <div className="mt-5 border-t-2 border-dashed border-slate-300 pt-3 text-[10px] font-mono text-slate-500 leading-relaxed" data-testid="project-health-disclaimer">
        Operational Health Indicator — based on live operational signals, not a
        compliance guarantee. Project status is informational; consult HR /
        Safety / PM for binding determinations.
      </div>
    </div>
  );
}

function ProjectRow({ row, onNavigate }) {
  const sev = row.status || "green";
  return (
    <tr
      className="hover:bg-slate-50 transition-colors"
      data-testid={`project-health-row-${row.project_number}`}
    >
      <td className="p-2 align-middle">
        <span
          className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border-2 text-[10px] font-mono uppercase tracking-wider font-bold ${STATUS_TINT[sev]}`}
          data-testid={`project-health-row-${row.project_number}-status`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[sev]}`} />
          {STATUS_LABEL[sev]}
        </span>
      </td>
      <td className="p-2 align-middle min-w-[180px]">
        <div className="font-mono font-bold text-slate-900 text-xs">{row.project_number}</div>
        <div className="text-[11px] text-slate-600 truncate max-w-[220px]" title={row.project_name}>
          {row.project_name}
        </div>
      </td>
      {INDICATORS.map((ind) => {
        const v = row.indicators?.[ind.key] ?? 0;
        const isHot = v > 0;
        return (
          <td key={ind.key} className="p-2 text-center align-middle">
            {isHot ? (
              <button
                type="button"
                onClick={() => onNavigate(ind.url(row.project_number))}
                className="inline-flex items-center gap-0.5 font-mono font-bold text-rose-700 hover:underline"
                data-testid={`project-health-row-${row.project_number}-${ind.key}`}
              >
                {v}<ChevronRight className="w-3 h-3" />
              </button>
            ) : (
              <span
                className="font-mono text-slate-300"
                data-testid={`project-health-row-${row.project_number}-${ind.key}`}
              >
                —
              </span>
            )}
          </td>
        );
      })}
      <td className="p-2 align-middle text-slate-300">
        <ChevronRight className="w-3.5 h-3.5" />
      </td>
    </tr>
  );
}
