// OperationalSignalsPanel — Iter160 (Phase 2.5 · Operational Signal Density).
//
// Admin-only compact panel mounted inside AdminAnalytics. Renders REAL
// operational throughput + cycle-time signals captured at fan-out tap
// points. NO charts, NO marketing tiles, NO predictive scoring. Each
// number is a direct rollup of an actual operational event.
//
// Data shape (from GET /api/admin/operational-signals):
//   { window_days, throughput{<signal>: {total, by_day[]}},
//     cycle_time_ms{<signal>: {count, avg_ms, p50_ms, p90_ms}},
//     equipment_top_failing[], doc_threshold_breakdown[], deltas{} }

import React, { useCallback, useEffect, useState } from "react";
import {
  ArrowDown, ArrowUp, Minus, Loader2, RefreshCw, Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

// Throughput tile labels — kept short, operationally-named.
const THROUGHPUT_LABELS = {
  "incident.created":       "Incidents",
  "ca.created":             "CAs created",
  "po.submit":              "PO submits",
  "equipment.fail":         "Equipment fails",
  "fire_ext.fail":          "Fire-ext fails",
  "training.deficiency":    "Training deficiencies",
  "doc.threshold_fired":    "Doc threshold fires",
  "hr.offboarding_started": "Offboardings",
};

const CYCLE_LABELS = {
  "ca.closed":  "CA cycle (created → closed)",
  "po.approve": "PO approval (submit → approved)",
  "po.receipt": "PO receipt (approved → uploaded)",
  "po.close":   "PO full lifecycle",
};

// Deep-link map — each card links to the underlying records page.
const DEEP_LINKS = {
  "incident.created":       "/incidents-dashboard",
  "ca.created":             "/safety-portal/corrective-actions",
  "po.submit":              "/po-requests",
  "equipment.fail":         "/admin/equipment",
  "fire_ext.fail":          "/safety-portal/fire-extinguishers",
  "training.deficiency":    "/leadership/records",
  "doc.threshold_fired":    "/document-expirations",
  "hr.offboarding_started": "/hr/employees",
};

function formatMs(ms) {
  if (ms == null) return "—";
  const s = ms / 1000;
  if (s < 60) return `${Math.round(s)}s`;
  const m = s / 60;
  if (m < 60) return `${Math.round(m)}m`;
  const h = m / 60;
  if (h < 24) return `${h.toFixed(1)}h`;
  const d = h / 24;
  return `${d.toFixed(1)}d`;
}

function DeltaArrow({ direction }) {
  if (direction === "up") {
    return <ArrowUp className="w-3 h-3 text-emerald-700" aria-label="up" />;
  }
  if (direction === "down") {
    return <ArrowDown className="w-3 h-3 text-amber-700" aria-label="down" />;
  }
  return <Minus className="w-3 h-3 text-slate-400" aria-label="flat" />;
}

export default function OperationalSignalsPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [windowDays, setWindowDays] = useState(30);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/admin/operational-signals`, {
        params: { window_days: windowDays },
      });
      setData(res.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Load failed");
    } finally {
      setLoading(false);
    }
  }, [windowDays]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="mt-6" data-testid="operational-signals-panel">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-slate-700" />
          <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] font-bold text-slate-800">
            Operational Signals
          </h2>
          <span className="text-[10px] text-slate-500 italic ml-1">
            real events · admin only
          </span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={windowDays}
            onChange={(e) => setWindowDays(Number(e.target.value))}
            className="border-2 border-slate-300 rounded-sm font-mono text-[11px] px-2 py-1 bg-white"
            data-testid="ops-signals-window-select"
          >
            <option value={7}>Last 7d</option>
            <option value={30}>Last 30d</option>
            <option value={90}>Last 90d</option>
          </select>
          <Button
            onClick={load}
            variant="outline"
            size="sm"
            disabled={loading}
            data-testid="ops-signals-refresh"
          >
            {loading
              ? <Loader2 className="w-3 h-3 animate-spin" />
              : <RefreshCw className="w-3 h-3" />}
          </Button>
        </div>
      </div>

      {error && (
        <div
          className="border-2 border-amber-300 bg-amber-50 text-amber-900 px-3 py-2 rounded-sm font-mono text-xs mb-3"
          data-testid="ops-signals-error"
        >
          Signals load error: {String(error)}
        </div>
      )}

      {!data && !loading && !error && (
        <EmptyState text="No operational signals captured yet." />
      )}

      {data && (
        <>
          {/* Throughput tiles */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-3 mb-4">
            {Object.entries(THROUGHPUT_LABELS).map(([sig, label]) => {
              const t = data.throughput?.[sig] || { total: 0 };
              const d = data.deltas?.[sig] || { direction: "flat", previous: 0 };
              const url = DEEP_LINKS[sig];
              const total = t.total ?? 0;
              const Inner = (
                <div
                  className="border-2 border-slate-300 bg-white rounded-md p-2 hover:border-slate-500 transition-colors"
                  data-testid={`ops-signal-tile-${sig.replace(/\./g, "-")}`}
                >
                  <div className="font-mono text-[9px] uppercase tracking-[0.18em] font-bold text-slate-700 truncate">
                    {label}
                  </div>
                  <div className="flex items-baseline justify-between mt-1">
                    <div className="font-display text-xl font-black text-slate-900 leading-none">
                      {total.toLocaleString()}
                    </div>
                    <div className="flex items-center gap-1">
                      <DeltaArrow direction={d.direction} />
                      <span className="font-mono text-[9px] text-slate-500">
                        prev {d.previous ?? 0}
                      </span>
                    </div>
                  </div>
                </div>
              );
              return url ? (
                <a key={sig} href={url} className="block no-underline">{Inner}</a>
              ) : (
                <div key={sig}>{Inner}</div>
              );
            })}
          </div>

          {/* Cycle time rollups */}
          <div className="border-2 border-slate-300 bg-white rounded-md mb-4">
            <div className="bg-slate-50 border-b-2 border-slate-200 px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
              Cycle time (real elapsed)
            </div>
            <div className="divide-y divide-slate-100">
              {Object.entries(CYCLE_LABELS).map(([sig, label]) => {
                const ct = data.cycle_time_ms?.[sig] || { count: 0 };
                return (
                  <div
                    key={sig}
                    className="px-3 py-2 grid grid-cols-5 gap-2 items-center text-[12px]"
                    data-testid={`ops-cycle-row-${sig.replace(/\./g, "-")}`}
                  >
                    <div className="col-span-2 font-mono text-slate-800 truncate">
                      {label}
                    </div>
                    <Stat label="n" value={ct.count} />
                    <Stat label="avg" value={ct.count ? formatMs(ct.avg_ms) : "—"} />
                    <Stat label="p90" value={ct.count ? formatMs(ct.p90_ms) : "—"} />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Top failing equipment + doc threshold breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
            <div className="border-2 border-slate-300 bg-white rounded-md">
              <div className="bg-slate-50 border-b-2 border-slate-200 px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
                Top failing equipment
              </div>
              <div className="p-2">
                {(data.equipment_top_failing || []).length === 0 ? (
                  <EmptyState text="No equipment failures in window." />
                ) : (
                  <ul className="text-[12px] font-mono">
                    {data.equipment_top_failing.map((row) => (
                      <li
                        key={row.equipment_id}
                        className="flex justify-between py-1 border-b border-slate-100 last:border-0"
                        data-testid={`ops-equipment-fail-${row.equipment_id}`}
                      >
                        <span className="truncate text-slate-700">{row.equipment_id}</span>
                        <span className="font-bold text-slate-900">{row.count}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="border-2 border-slate-300 bg-white rounded-md">
              <div className="bg-slate-50 border-b-2 border-slate-200 px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] font-bold text-slate-700">
                Doc threshold fires
              </div>
              <div className="p-2">
                {(data.doc_threshold_breakdown || []).length === 0 ? (
                  <EmptyState text="No threshold fires in window." />
                ) : (
                  <ul className="text-[12px] font-mono">
                    {data.doc_threshold_breakdown.map((row, i) => (
                      <li
                        key={`${row.category}-${row.threshold}-${i}`}
                        className="flex justify-between py-1 border-b border-slate-100 last:border-0"
                        data-testid={`ops-doc-threshold-${row.category}-${row.threshold}`}
                      >
                        <span className="truncate text-slate-700">
                          {row.category} · {row.threshold === -1 ? "expired" : `${row.threshold}d`}
                        </span>
                        <span className="font-bold text-slate-900">{row.count}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="text-right">
      <span className="font-mono text-[9px] uppercase tracking-wider text-slate-500 mr-1">{label}</span>
      <span className="font-mono font-bold text-slate-900">{value}</span>
    </div>
  );
}

function EmptyState({ text }) {
  return (
    <div className="text-center text-slate-500 italic text-[12px] py-3 border border-dashed border-slate-300 rounded-sm">
      {text}
    </div>
  );
}
