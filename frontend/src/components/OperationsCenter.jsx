// OperationsCenter.jsx — Iter C.
//
// Thin per-role aggregated operational visibility surface. Each card
// is one real upstream count (or compact dict). Every card deep-links
// to the underlying list. NO fake metrics. NO duplicate Project
// Health logic. Renderable inline (Hub headers) or as a full page.
//
// Usage:
//   <OperationsCenter compact />     ← Hub header strip (top 3-4 cards)
//   <OperationsCenter />              ← full grid view
import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle, AlertCircle, Activity, ChevronRight, RefreshCw,
} from "lucide-react";
import { fetchOperationsCenter } from "@/lib/operationsCenterApi";
import { tintFor } from "@/lib/statusBadges";

const SEV_RING = {
  Critical: "border-rose-300 bg-rose-50",
  Warning:  "border-amber-300 bg-amber-50",
  Info:     "border-slate-200 bg-white",
};
const SEV_TEXT = {
  Critical: "text-rose-700",
  Warning:  "text-amber-800",
  Info:     "text-slate-700",
};

function CardTile({ card, onOpen }) {
  const sev = card.severity || "Info";
  const isCount = "count" in card;
  // value cards (integration_health / audit_coverage) render as compact strips
  if (!isCount && card.key === "integration_health") {
    const v = card.value || {};
    return (
      <button
        type="button"
        onClick={onOpen}
        className={`text-left rounded-md border-2 ${SEV_RING[sev]} p-3 hover:shadow-sm transition-shadow w-full`}
        data-testid={`ops-card-${card.key}`}
      >
        <div className="flex items-center justify-between mb-1">
          <div className={`text-[10px] font-mono uppercase tracking-[0.16em] font-bold ${SEV_TEXT[sev]}`}>{card.label}</div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
        </div>
        <div className="text-sm font-bold text-slate-900 capitalize">{v.status || "unknown"}</div>
        {v.checked_at && (
          <div className="text-[10px] font-mono text-slate-500 mt-0.5">checked {String(v.checked_at).slice(0, 16)}</div>
        )}
      </button>
    );
  }
  if (!isCount && card.key === "audit_coverage") {
    const v = card.value || {};
    return (
      <button
        type="button"
        onClick={onOpen}
        className={`text-left rounded-md border-2 ${SEV_RING[sev]} p-3 hover:shadow-sm transition-shadow w-full`}
        data-testid={`ops-card-${card.key}`}
        id="audit-coverage"
      >
        <div className="flex items-center justify-between mb-1">
          <div className={`text-[10px] font-mono uppercase tracking-[0.16em] font-bold ${SEV_TEXT[sev]}`}>{card.label}</div>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
        </div>
        <div className="text-2xl font-bold text-slate-900 leading-tight">{v.coverage_pct ?? 0}%</div>
        <div className="text-[10px] font-mono text-slate-500 mt-0.5">
          {v.covered ?? 0} / {v.total ?? 0} records with audit log
        </div>
        {(v.modules || []).length > 0 && (
          <div className="mt-2 grid grid-cols-3 gap-1">
            {v.modules.map((m) => {
              const tot = m.with + m.without;
              const pct = tot ? Math.round((m.with / tot) * 100) : 0;
              return (
                <div key={m.module} className="text-[9px] font-mono text-slate-600">
                  <div className="font-bold truncate">{m.module}</div>
                  <div>{pct}%</div>
                </div>
              );
            })}
          </div>
        )}
      </button>
    );
  }
  // count card
  return (
    <button
      type="button"
      onClick={onOpen}
      className={`text-left rounded-md border-2 ${SEV_RING[sev]} p-3 hover:shadow-sm transition-shadow w-full`}
      data-testid={`ops-card-${card.key}`}
    >
      <div className="flex items-center justify-between mb-1">
        <div className={`text-[10px] font-mono uppercase tracking-[0.16em] font-bold ${SEV_TEXT[sev]}`}>{card.label}</div>
        <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
      </div>
      <div className="text-3xl font-bold leading-none text-slate-900">{card.count}</div>
      {card.count > 0 && (
        <div className={`text-[10px] font-mono mt-1.5 inline-block px-1.5 py-0.5 rounded border ${tintFor("severity", sev)}`}>
          {sev === "Critical" ? "Needs attention" : sev === "Warning" ? "Watch" : ""}
        </div>
      )}
    </button>
  );
}

export default function OperationsCenter({ compact = false, className = "" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const navigate = useNavigate();

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const d = await fetchOperationsCenter();
      setData(d);
    } catch (e) {
      const code = e?.response?.status;
      setErr(code === 401 ? "AUTH_REQUIRED" : "FAIL");
      setData(null);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  const visibleCards = useMemo(() => {
    if (!data?.cards) return [];
    if (compact) {
      // top 4 highest-severity cards with >0 count
      const sorted = [...data.cards].sort((a, b) => {
        const w = { Critical: 3, Warning: 2, Info: 1 };
        return (w[b.severity] || 0) - (w[a.severity] || 0)
          || (b.count || 0) - (a.count || 0);
      });
      return sorted.slice(0, 4);
    }
    return data.cards;
  }, [data, compact]);

  if (err === "AUTH_REQUIRED") return null; // silent on anon pages
  if (loading) {
    return (
      <div className={`rounded-md border-2 border-slate-200 bg-white p-3 text-xs text-slate-500 ${className}`} data-testid="ops-center-loading">
        Loading operational visibility…
      </div>
    );
  }
  if (err === "FAIL") {
    return (
      <div className={`rounded-md border-2 border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 ${className}`} data-testid="ops-center-error">
        <AlertCircle className="w-3.5 h-3.5 inline -mt-0.5 mr-1" />
        Could not load operations center.
      </div>
    );
  }
  if (!data || visibleCards.length === 0) return null;

  const containerCls = compact
    ? "grid grid-cols-2 sm:grid-cols-4 gap-2"
    : "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3";

  return (
    <section
      className={className}
      data-testid="ops-center"
      aria-label="Operations Center"
    >
      {!compact && (
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-slate-600" />
            <h2 className="text-sm font-bold font-mono uppercase tracking-[0.16em] text-slate-700">
              Operations Center · {data.role}
            </h2>
          </div>
          <button
            onClick={load}
            className="text-[10px] font-mono uppercase tracking-wider text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
            data-testid="ops-center-refresh"
          >
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        </div>
      )}
      <div className={containerCls}>
        {visibleCards.map((c) => (
          <CardTile
            key={c.key}
            card={c}
            onOpen={() => c.url && navigate(c.url)}
          />
        ))}
      </div>
      {!compact && (
        <div className="mt-3 text-[10px] font-mono text-slate-400">
          Real upstream counts · generated {String(data.generated_at).slice(0, 19)}
        </div>
      )}
    </section>
  );
}
