// M-2 · M-2-7 · Admin Operations Dashboard.
//
// Read-only operational counts derived from `operational_events`.
// Visibility only — never writes, never mutates any other collection.
import React, { useEffect, useState, useCallback } from "react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import {
  Radar, RefreshCw, Loader2, Truck, Factory, Warehouse, Wrench, Trash2,
  Mountain, HelpCircle, Activity,
} from "lucide-react";

const CARDS = [
  { label: "Equipment On Projects",        key: "Equipment On Projects",        Icon: Truck,     tone: "emerald" },
  { label: "Equipment At Plants",          key: "Equipment At Plants",          Icon: Factory,   tone: "amber" },
  { label: "Equipment At Pits",            key: "Equipment At Pits",            Icon: Mountain,  tone: "amber" },
  { label: "Equipment At Yard",            key: "Equipment At Yard",            Icon: Warehouse, tone: "slate" },
  { label: "Equipment At Shop",            key: "Equipment At Shop",            Icon: Wrench,    tone: "slate" },
  { label: "Equipment At Disposal Sites",  key: "Equipment At Disposal Sites",  Icon: Trash2,    tone: "slate" },
  { label: "Unknown Location",             key: "Unknown Location",             Icon: HelpCircle,tone: "red" },
];

const TONE = {
  emerald: "bg-emerald-50 border-emerald-300 text-emerald-900",
  amber:   "bg-amber-50 border-amber-300 text-amber-900",
  slate:   "bg-slate-50 border-slate-200 text-slate-900",
  red:     "bg-red-50 border-red-300 text-red-900",
};

export default function AdminOperationsDashboard() {
  const [buckets, setBuckets] = useState({});
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [audit, setAudit] = useState(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const r = await api.get("/admin/operational-events/dashboard");
        if (cancelled) return;
        setBuckets(r.data?.buckets || {});
        setTotal(r.data?.total_assets_with_state || 0);
      } catch (e) {
        if (!cancelled) toast.error(`Dashboard load failed: ${e?.response?.data?.detail || e.message}`);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [tick]);

  const runMaterialize = useCallback(async () => {
    setRunning(true);
    try {
      const r = await api.post("/admin/operational-events/materialize");
      toast.success(
        `Routed ${r.data.routed} events from ${r.data.events_considered} raw · upserted ${r.data.upserted}${r.data.skipped_by_storage_gate ? ` · skipped ${r.data.skipped_by_storage_gate}` : ""}`
      );
      setTick((t) => t + 1);
    } catch (e) {
      toast.error(`Materialize failed: ${e?.response?.data?.detail || e.message}`);
    } finally { setRunning(false); }
  }, []);

  const runAudit = useCallback(async () => {
    setRunning(true);
    try {
      const r = await api.get("/admin/operational-events/audit");
      setAudit(r.data?.answers || null);
      toast.success("Trust audit refreshed");
    } catch (e) {
      toast.error(`Audit failed: ${e?.response?.data?.detail || e.message}`);
    } finally { setRunning(false); }
  }, []);

  return (
    <AdminShell title="Operations · Motive Visibility" section="command-center">
      <div className="space-y-4" data-testid="ops-dashboard-page">
        {/* Header */}
        <div className="rounded border-2 border-slate-300 bg-white p-4 flex items-start justify-between gap-3">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-red-700 font-bold">
              M-2 · Event Router
            </div>
            <h2 className="text-xl font-black text-slate-900 mt-0.5 flex items-center gap-2">
              <Radar className="w-5 h-5" /> Equipment by location
            </h2>
            <p className="text-sm text-slate-600 max-w-2xl mt-1">
              Read-only operational visibility. Derived from Motive telemetry +
              Verified geofences. <strong>No writes</strong> to dispatch,
              daily reports, payroll, or workflow state.
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button
              onClick={runMaterialize}
              disabled={running}
              variant="outline"
              className="border-2"
              data-testid="ops-materialize-btn"
            >
              {running ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-1" />}
              Materialize Events
            </Button>
            <Button
              onClick={runAudit}
              disabled={running}
              className="bg-slate-900 hover:bg-black text-white"
              data-testid="ops-audit-btn"
            >
              <Activity className="w-4 h-4 mr-1" />
              Run Trust Audit
            </Button>
          </div>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2" data-testid="ops-cards">
          {CARDS.map(({ label, key, Icon, tone }) => (
            <div
              key={key}
              className={`px-3 py-2 rounded border ${TONE[tone]}`}
              data-testid={`ops-card-${key.toLowerCase().replace(/\s+/g, "-")}`}
            >
              <div className="font-mono text-[10px] uppercase tracking-wider opacity-80 flex items-center gap-1">
                <Icon className="w-3 h-3" /> {label}
              </div>
              <div className="text-3xl font-black mt-1">
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : (buckets[key] ?? 0)}
              </div>
            </div>
          ))}
        </div>
        <div className="text-xs text-slate-500 font-mono">
          Tracking {total} asset{total === 1 ? "" : "s"} with at least one routed event.
        </div>

        {/* Trust audit panel */}
        {audit && (
          <div
            className="rounded border-2 border-slate-300 bg-white p-4"
            data-testid="ops-audit-panel"
          >
            <h3 className="text-lg font-black text-slate-900 mb-2">
              M-2 Operational Trust Audit
            </h3>
            <table className="w-full text-sm">
              <tbody>
                {[
                  ["Q1 · assets generating events",          audit.q1_assets_generating_events],
                  ["Q2 · presence events total",             audit.q2_presence_events_total],
                  ["Q2 · observed days",                     audit.q2_observed_days],
                  ["Q2 · avg events / day",                  audit.q2_avg_events_per_day],
                  ["Q3 · distinct geofences in events",      audit.q3_distinct_geofences_in_events],
                  ["Q3 · unmatched (UNKNOWN) geofences",     audit.q3_unmatched_geofences],
                  ["Q4 · routed event count vs raw delta",   audit.q4_discarded_events],
                  ["Q5 · duplicates collapsed",              audit.q5_duplicates_collapsed],
                  ["Q6 · asset_mappings total",              audit.q6_asset_mappings_total],
                  ["Q6 · MASCI-mapped assets",               audit.q6_asset_mappings_masci_mapped],
                  ["Q6 · unmapped assets",                   audit.q6_asset_mappings_unmapped],
                  ["Q7 · avg webhook latency (ms)",          audit.q7_avg_webhook_latency_ms ?? "—"],
                  ["Q9 · lowest-confidence category",        audit.q9_lowest_confidence_category || "—"],
                  ["Q10 · accuracy estimate (%)",            audit.q10_accuracy_pct_estimate],
                ].map(([k, v]) => (
                  <tr key={k} className="border-b border-slate-100">
                    <td className="px-2 py-1 font-mono text-xs text-slate-700">{k}</td>
                    <td className="px-2 py-1 text-right font-mono font-bold">{String(v)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="text-xs text-slate-500 font-mono mt-2">
              Q8 top geofences: {(audit.q8_top_geofences || []).slice(0, 3)
                .map((t) => `${t.name} (${t.events})`).join(" · ") || "—"}
            </div>
          </div>
        )}
      </div>
    </AdminShell>
  );
}
