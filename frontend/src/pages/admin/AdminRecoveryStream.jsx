/**
 * OMEGA · FOCP Release 2 · TR-0002 · Admin Recovery Stream
 *
 * Cross-workflow audit visibility. Reads
 *   GET /api/admin/recovery/transitions?workflow=&only_undos=&limit=
 *
 * Renders the unified stream of every status change across every
 * workflow (incident / daily_report / qaqc_inspection / site_inspection
 * / payroll_variance / jha_ack), with reversals visually distinguished.
 *
 * Read-only — undo is initiated from each record's lifecycle panel.
 */
import React, { useEffect, useState, useCallback } from "react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { RotateCcw, Loader2, RefreshCw, Filter, Undo2 } from "lucide-react";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const WORKFLOW_LABELS = {
  incident: "Incident",
  daily_report: "Daily Report",
  qaqc_inspection: "QA/QC",
  site_inspection: "Site Inspection",
  payroll_variance: "Payroll Variance",
  jha_ack: "JHP Acknowledgement",
};

export default function AdminRecoveryStream() {
  const [events, setEvents] = useState([]);
  const [supported, setSupported] = useState([]);
  const [loading, setLoading] = useState(true);
  const [workflow, setWorkflow] = useState("");
  const [onlyUndos, setOnlyUndos] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { limit: 100 };
      if (workflow) params.workflow = workflow;
      if (onlyUndos) params.only_undos = true;
      const r = await api.get("/admin/recovery/transitions", { params });
      setEvents(r.data?.events || []);
      setSupported(r.data?.supported_workflows || []);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [workflow, onlyUndos]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <AdminShell>
      <div
        className="max-w-6xl mx-auto px-4 py-6 sm:py-8"
        data-testid="admin-recovery-stream-page"
      >
        <div className="mb-6 flex flex-wrap items-end gap-3">
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-amber-700">
              FOCP Release 2 · TR-0002
            </span>
            <h1 className="font-display text-3xl font-black tracking-tight text-slate-900 mt-1">
              Recovery Stream
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Append-only audit of every status change across every workflow. Reversals
              (&quot;undo&quot;) are tagged but never replace the original transition.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={load}
            className="ml-auto h-9 px-3 border-2 border-slate-300"
            data-testid="admin-recovery-stream-refresh"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
        </div>

        <section
          className="bg-white border-2 border-slate-200 rounded-md p-4 mb-4 flex flex-wrap items-center gap-3"
          data-testid="admin-recovery-stream-filters"
        >
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
            Filter
          </span>
          <select
            value={workflow}
            onChange={(e) => setWorkflow(e.target.value)}
            className="h-9 border-2 border-slate-300 rounded px-2 text-sm bg-white"
            data-testid="admin-recovery-stream-workflow-select"
          >
            <option value="">All workflows</option>
            {supported.map((w) => (
              <option key={w} value={w}>
                {WORKFLOW_LABELS[w] || w}
              </option>
            ))}
          </select>
          <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={onlyUndos}
              onChange={(e) => setOnlyUndos(e.target.checked)}
              data-testid="admin-recovery-stream-only-undos"
              className="h-4 w-4"
            />
            <span className="text-slate-700">Only reversals (undo)</span>
          </label>
          <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
            {events.length} events
          </span>
        </section>

        <section
          className="bg-white border-2 border-slate-200 rounded-md overflow-hidden"
          data-testid="admin-recovery-stream-list"
        >
          {loading ? (
            <div className="py-10 text-center text-slate-500 text-sm">
              <Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading…
            </div>
          ) : events.length === 0 ? (
            <div
              className="py-10 text-center text-slate-500 italic text-sm"
              data-testid="admin-recovery-stream-empty"
            >
              No events match the current filter.
            </div>
          ) : (
            <ul className="divide-y divide-slate-200">
              {events.map((ev) => {
                const isUndo = !!ev.is_undo;
                return (
                  <li
                    key={ev.id}
                    className={`px-4 py-3 ${
                      isUndo ? "bg-amber-50" : "bg-white"
                    }`}
                    data-testid={`admin-recovery-stream-row-${ev.id}`}
                  >
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <span className="font-mono uppercase tracking-[0.18em] px-2 py-0.5 rounded bg-slate-900 text-white font-bold">
                        {WORKFLOW_LABELS[ev.workflow] || ev.workflow}
                      </span>
                      {isUndo && (
                        <span
                          className="font-mono uppercase tracking-[0.18em] px-2 py-0.5 rounded bg-amber-200 text-amber-900 font-bold inline-flex items-center gap-1"
                          data-testid={`admin-recovery-stream-undo-badge-${ev.id}`}
                        >
                          <Undo2 className="w-3 h-3" /> Undo
                        </span>
                      )}
                      <span className="font-mono uppercase text-slate-800">
                        {ev.from_state || "—"}
                      </span>
                      <RotateCcw className="w-3 h-3 text-slate-400" />
                      <span className="font-mono uppercase text-slate-800">
                        {ev.to_state || "—"}
                      </span>
                      <span className="ml-auto font-mono text-[10px] text-slate-500">
                        {ev.at ? formatPlatformTime(ev.at) : "—"}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-slate-600 flex flex-wrap gap-x-3 gap-y-1">
                      <span>
                        <b className="font-mono uppercase tracking-wider">
                          {ev.actor_role || "—"}
                        </b>
                        {ev.actor_name ? ` · ${ev.actor_name}` : ""}
                      </span>
                      <span className="text-slate-500">
                        Record: <span className="font-mono">{ev.record_doc_id || ev.record_id}</span>
                      </span>
                    </div>
                    {ev.reason && (
                      <div className="mt-1 text-xs italic text-slate-800">
                        &quot;{ev.reason}&quot;
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </AdminShell>
  );
}
