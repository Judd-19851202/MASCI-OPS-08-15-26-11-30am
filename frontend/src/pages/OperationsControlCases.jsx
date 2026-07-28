import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, FolderSearch, RefreshCw, ShieldCheck, WandSparkles } from "lucide-react";
import { toast } from "sonner";
import { listOperationalCases, runOperationalCaseCertification } from "@/lib/operationsControlCasesApi";
import { formatPlatformTime } from "@/lib/platformTime";

const STATUS_FILTERS = ["all", "OPEN", "UNDER_REVIEW", "INVESTIGATING", "ESCALATED", "PENDING_VERIFICATION", "CLOSED", "DUPLICATE"];

function CaseTone({ status }) {
  const tone = {
    ESCALATED: "bg-rose-100 text-rose-900 border-rose-300",
    PENDING_VERIFICATION: "bg-amber-100 text-amber-900 border-amber-300",
    CLOSED: "bg-emerald-100 text-emerald-900 border-emerald-300",
    DUPLICATE: "bg-slate-200 text-slate-700 border-slate-300",
  }[status] || "bg-sky-100 text-sky-900 border-sky-300";
  return <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold tracking-wide`} data-testid={`occ-case-status-${status}`}>{status}</span>;
}

export default function OperationsControlCases() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [filter, setFilter] = useState("all");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const next = await listOperationalCases();
      setData(next);
      setError("");
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load Operational Cases.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const rows = useMemo(() => {
    const list = data?.cases || [];
    if (filter === "all") return list;
    return list.filter((row) => row.status === filter);
  }, [data, filter]);

  const runCertification = useCallback(async () => {
    setRunning(true);
    try {
      const result = await runOperationalCaseCertification();
      toast.success(result.release_determination || "Certification chain completed.");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Certification run failed.");
    } finally {
      setRunning(false);
    }
  }, [load]);

  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white/90 p-5 shadow-sm" data-testid="occ-cases-queue">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <div className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Operational Case Management</div>
          <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-950">Dedicated Case queue</h2>
          <p className="mt-2 text-sm text-slate-600">Every action here is persisted through the canonical backend. No UI-only state, no silent mutation, no duplicate governed outcomes.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60"
            data-testid="occ-cases-refresh-button"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
          <button
            type="button"
            onClick={runCertification}
            disabled={running}
            className="inline-flex items-center gap-2 rounded-full border border-emerald-300 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-900 hover:bg-emerald-100 disabled:opacity-60"
            data-testid="occ-cases-certification-run-button"
          >
            <WandSparkles className={`h-4 w-4 ${running ? "animate-pulse" : ""}`} /> {running ? "Running certification…" : "Run WP-14F certification"}
          </button>
        </div>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-5" data-testid="occ-cases-summary-strip">
        {[
          { key: "total", label: "Total", icon: FolderSearch, value: data?.summary?.total || 0 },
          { key: "open", label: "Open", icon: AlertTriangle, value: data?.summary?.open || 0 },
          { key: "escalated", label: "Escalated", icon: AlertTriangle, value: data?.summary?.escalated || 0 },
          { key: "pending_verification", label: "Pending verification", icon: ShieldCheck, value: data?.summary?.pending_verification || 0 },
          { key: "critical", label: "Critical", icon: ShieldCheck, value: data?.summary?.critical || 0 },
        ].map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.key} className="rounded-3xl border border-slate-200 bg-slate-50 p-4" data-testid={`occ-cases-summary-${card.key}`}>
              <div className="flex items-center gap-2 text-slate-500"><Icon className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.22em]">{card.label}</span></div>
              <div className="mt-3 text-3xl font-black text-slate-950">{card.value}</div>
            </div>
          );
        })}
      </div>

      <div className="mt-5 flex flex-wrap gap-2" data-testid="occ-cases-filter-bar">
        {STATUS_FILTERS.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => setFilter(status)}
            className={`rounded-full border px-3 py-1.5 text-xs font-semibold tracking-wide ${filter === status ? "border-slate-900 bg-slate-900 text-white" : "border-slate-300 bg-white text-slate-700 hover:bg-slate-100"}`}
            data-testid={`occ-cases-filter-${status.toLowerCase()}`}
          >
            {status === "all" ? "All statuses" : status.replaceAll("_", " ")}
          </button>
        ))}
      </div>

      {error ? <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid="occ-cases-error">{error}</div> : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-2" data-testid="occ-cases-list">
        {!loading && rows.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-500" data-testid="occ-cases-empty">No Operational Cases match the current filter yet.</div>
        ) : null}
        {rows.map((row) => (
          <Link
            key={row.id}
            to={`/operations-control/cases/${encodeURIComponent(row.id)}`}
            className="group rounded-[1.75rem] border border-slate-200 bg-white p-5 transition-transform duration-200 hover:-translate-y-0.5 hover:border-slate-400"
            data-testid={`occ-case-card-${row.id}`}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-[11px] uppercase tracking-[0.22em] text-slate-500">{row.case_type_label || row.case_type_id}</div>
                <div className="mt-2 text-xl font-black text-slate-950" data-testid={`occ-case-number-${row.id}`}>{row.case_number}</div>
                <div className="mt-1 text-sm text-slate-600">{row.project_number || "No project"} · {row.project_name || "Unlabeled project"}</div>
              </div>
              <CaseTone status={row.status} />
            </div>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-600">
              <span className="rounded-full bg-slate-100 px-2.5 py-1" data-testid={`occ-case-severity-${row.id}`}>severity: {row.severity}</span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1" data-testid={`occ-case-priority-${row.id}`}>priority: {row.priority}</span>
              <span className="rounded-full bg-slate-100 px-2.5 py-1" data-testid={`occ-case-owner-${row.id}`}>owner: {row.case_owner_name || row.case_owner_role || "—"}</span>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2 text-sm text-slate-700">
              <div data-testid={`occ-case-origin-${row.id}`}>
                <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Governed origin</div>
                <div className="mt-1">{row.origin?.source_doc_id || row.origin?.source_record_id || "—"}</div>
              </div>
              <div data-testid={`occ-case-updated-${row.id}`}>
                <div className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Last updated</div>
                <div className="mt-1">{row.updated_at ? formatPlatformTime(row.updated_at) : "—"}</div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
