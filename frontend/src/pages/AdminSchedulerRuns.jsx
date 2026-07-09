// AdminSchedulerRuns.jsx — iter445 · Sprint · Scheduler Hardening
//
// Read-only admin view of every scheduled digest execution.
// Pairs with the backend `scheduler_runs` collection + the
// `/api/admin/scheduler-runs` endpoint.
//
// Operator value (cited verbatim from the OMEGA Batch):
//   1. Why did this digest send?
//   2. Which pod sent it?
//   3. When did it send?
//   4. Who received it?
//   5. Was a duplicate prevented?
//
// All five questions are answered by a single row in this table.

import React, { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, RefreshCw, ShieldAlert, ShieldCheck, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { usePageTitle } from "@/lib/usePageTitle";
import LastActivityLine from "@/components/admin/LastActivityLine";
// TRACK 27.03 · Final Completion · canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

const SCHEDULER_OPTIONS = [
  { value: "", label: "All schedulers" },
  { value: "po_digest", label: "PO Digest (Mondays 14:00 UTC)" },
  { value: "safety_digest", label: "Safety Digest" },
  { value: "operator_digest", label: "Operator Digest" },
];

function StatusBadge({ status, dedup }) {
  if (dedup) return (
    <Badge className="bg-amber-100 text-amber-900 border border-amber-300" data-testid="scheduler-run-status-dedup">
      <ShieldAlert className="h-3 w-3 mr-1" /> dedup-prevented
    </Badge>
  );
  if (status === "done") return (
    <Badge className="bg-emerald-100 text-emerald-900 border border-emerald-300" data-testid="scheduler-run-status-done">
      <ShieldCheck className="h-3 w-3 mr-1" /> sent
    </Badge>
  );
  if (status === "failed") return (
    <Badge className="bg-rose-100 text-rose-900 border border-rose-300" data-testid="scheduler-run-status-failed">
      <AlertTriangle className="h-3 w-3 mr-1" /> failed
    </Badge>
  );
  return (
    <Badge className="bg-slate-100 text-slate-900 border border-slate-300" data-testid="scheduler-run-status-running">
      in-progress
    </Badge>
  );
}

function fmtTime(iso) {
  if (!iso) return "—";
  return formatPlatformTime(iso);
}

function fmtDur(s) {
  if (s == null) return "—";
  if (s < 1) return `${Math.round(s * 1000)}ms`;
  if (s < 60) return `${s.toFixed(1)}s`;
  return `${(s / 60).toFixed(1)}m`;
}

export default function AdminSchedulerRuns() {
  usePageTitle("Scheduler Runs · MASCI Admin");
  const [scheduler, setScheduler] = useState("");
  const [items, setItems] = useState([]);
  const [totals, setTotals] = useState({ total: 0, dedup_total: 0, failed_total: 0 });
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (scheduler) params.set("scheduler", scheduler);
      params.set("limit", "100");
      const { data } = await api.get(`/admin/scheduler-runs?${params.toString()}`);
      setItems(data?.items || []);
      setTotals({
        total: data?.total || 0,
        dedup_total: data?.dedup_total || 0,
        failed_total: data?.failed_total || 0,
      });
    } catch (e) {
      console.error("[scheduler-runs] load failed", e);
      toast.error("Could not load scheduler runs. Try again.");
    } finally { setLoading(false); }
  };

  useEffect(() => { load();   }, [scheduler]);

  const summary = useMemo(() => ({
    headline: scheduler
      ? `${scheduler} · last ${items.length} runs`
      : `All schedulers · last ${items.length} runs`,
    duplicatesPrevented: totals.dedup_total,
    failures: totals.failed_total,
  }), [items, totals, scheduler]);

  return (
    <div className="min-h-screen bg-blueprint-bg">
      <header className="bg-slate-900 text-white border-b-4 border-yellow-400">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <Link to="/admin" className="flex items-center gap-2 text-yellow-300 hover:text-yellow-200" data-testid="scheduler-runs-back">
            <ArrowLeft className="h-4 w-4" /> Admin Hub
          </Link>
          <div className="font-mono text-xs uppercase tracking-widest text-slate-400">Scheduler Runs · iter445</div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6 space-y-6">
        <section>
          <p className="font-mono text-xs uppercase tracking-[0.22em] text-slate-500">audit · iter445</p>
          <h1 className="text-3xl font-bold text-slate-900 mt-1">Scheduler Runs</h1>
          <p className="text-sm text-slate-600 mt-2 max-w-3xl">
            Every scheduled digest fire is recorded here with the worker that
            sent it, the recipient count, and any duplicate attempts that were
            atomically rejected. Use this to answer questions about a specific
            Monday digest without having to read application logs.
          </p>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="border-l-4 border-l-slate-700 rounded bg-white p-4 shadow-sm" data-testid="scheduler-runs-stat-total">
            <p className="text-xs font-mono text-slate-500 uppercase">Recorded runs ({scheduler || "all"})</p>
            <p className="text-3xl font-bold text-slate-900 mt-1">{totals.total}</p>
          </div>
          <div className="border-l-4 border-l-amber-600 rounded bg-white p-4 shadow-sm" data-testid="scheduler-runs-stat-dedup">
            <p className="text-xs font-mono text-slate-500 uppercase">Duplicates prevented</p>
            <p className="text-3xl font-bold text-amber-700 mt-1">{summary.duplicatesPrevented}</p>
            <p className="text-xs text-slate-500 mt-1">Atomic dedup tripped — orphan scheduler attempted to fire but was blocked.</p>
          </div>
          <div className="border-l-4 border-l-rose-600 rounded bg-white p-4 shadow-sm" data-testid="scheduler-runs-stat-failed">
            <p className="text-xs font-mono text-slate-500 uppercase">Failures</p>
            <p className="text-3xl font-bold text-rose-700 mt-1">{summary.failures}</p>
          </div>
        </section>

        <section className="flex items-center gap-3 flex-wrap">
          <select
            value={scheduler}
            onChange={(e) => setScheduler(e.target.value)}
            className="rounded border border-slate-300 bg-white px-3 py-2 text-sm font-mono"
            data-testid="scheduler-runs-filter"
          >
            {SCHEDULER_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          <Button variant="outline" onClick={load} disabled={loading} data-testid="scheduler-runs-refresh">
            <RefreshCw className={`h-3.5 w-3.5 mr-2 ${loading ? "animate-spin" : ""}`} /> Refresh
          </Button>
          <LastActivityLine label="Loaded" />
        </section>

        <section className="bg-white border border-slate-200 rounded shadow-sm overflow-x-auto" data-testid="scheduler-runs-table">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-700">
              <tr>
                <th className="px-3 py-2 text-left font-mono text-xs uppercase tracking-wider">Scheduler</th>
                <th className="px-3 py-2 text-left font-mono text-xs uppercase tracking-wider">Slot</th>
                <th className="px-3 py-2 text-left font-mono text-xs uppercase tracking-wider">Started</th>
                <th className="px-3 py-2 text-left font-mono text-xs uppercase tracking-wider">Duration</th>
                <th className="px-3 py-2 text-right font-mono text-xs uppercase tracking-wider">Recipients</th>
                <th className="px-3 py-2 text-left font-mono text-xs uppercase tracking-wider">Pod</th>
                <th className="px-3 py-2 text-left font-mono text-xs uppercase tracking-wider">Status</th>
                <th className="px-3 py-2 text-right font-mono text-xs uppercase tracking-wider">Dedup attempts</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && !loading && (
                <tr><td colSpan={8} className="px-3 py-6 text-center text-slate-500 italic">No runs recorded yet. Scheduled digests will appear here.</td></tr>
              )}
              {items.map((it, idx) => (
                <tr key={`${it.scheduler}-${it.slot_key}-${idx}`} className="border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono text-xs">{it.scheduler}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-700">{it.slot_key}</td>
                  <td className="px-3 py-2 text-slate-700">{fmtTime(it.started_at)}</td>
                  <td className="px-3 py-2 text-slate-700">{fmtDur(it.duration_s)}</td>
                  <td className="px-3 py-2 text-right font-mono">{it.recipients ?? "—"}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-600">{it.host}:{it.pid}</td>
                  <td className="px-3 py-2"><StatusBadge status={it.status} dedup={false} /></td>
                  <td className="px-3 py-2 text-right">
                    {(it.dedup_attempts || 0) > 0
                      ? (<span className="font-mono text-amber-700 font-semibold" title="An orphan scheduler attempted to fire — atomic dedup blocked it">{it.dedup_attempts}</span>)
                      : (<span className="text-slate-400">0</span>)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="bg-slate-50 border border-slate-200 rounded p-4 text-xs text-slate-600 font-mono">
          <p className="uppercase tracking-wider text-slate-500 mb-1">How to read this page</p>
          <ul className="list-disc list-inside space-y-0.5">
            <li><strong>One row per slot</strong> · {`(scheduler, slot_key)`} is unique. Two rows means the operator ran two slots, NOT a duplicate.</li>
            <li><strong>Dedup attempts &gt; 0</strong> · an orphan scheduler tried to fire at the same slot and was atomically rejected. No duplicate email was sent.</li>
            <li><strong>Pod column</strong> · host:pid of the worker that won the slot. Cross-reference with k8s pod logs if needed.</li>
            <li><strong>Recipients</strong> · the number of emails actually delivered for that slot.</li>
          </ul>
        </section>
      </main>
    </div>
  );
}
