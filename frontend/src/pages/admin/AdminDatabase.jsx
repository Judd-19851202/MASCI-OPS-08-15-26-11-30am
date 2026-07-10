// AdminDatabase.jsx — iter437 · Phase Sigma-III · P1
//
// Calm operational observability panel for /admin/database. Hosts the
// StorageObservabilityCard (inline-SVG sparkline + runway summary)
// alongside the live cluster-capacity snapshot.
//
// Doctrine:
//   - Read-only. No mutations. No analytics. No charts beyond the sparkline.
//   - Quiet — minimum chrome, slate text, no animations.
//   - Mobile-safe — single column on small screens, two columns on lg+.
import React, { useEffect, useState } from "react";
import { Database, Loader2, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import StorageObservabilityCard from "@/components/admin/StorageObservabilityCard";
import { api } from "@/lib/api";

const SEVERITY = {
  ok:       { cls: "border-emerald-300 bg-emerald-50", Icon: CheckCircle2, label: "OK" },
  warning:  { cls: "border-amber-300 bg-amber-50",     Icon: AlertTriangle, label: "WARN" },
  critical: { cls: "border-red-400 bg-red-50",         Icon: XCircle,       label: "CRITICAL" },
};

function CapacityNow() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setErr(null);
      try {
        const r = await api.get("/cluster/capacity");
        if (!cancelled) setData(r.data);
      } catch (e) {
        if (!cancelled) setErr(e?.message || "fetch failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    const t = setInterval(load, 5 * 60 * 1000); // 5-minute poll
    return () => { cancelled = true; clearInterval(t); };
  }, []);

  const sev = data?.severity || "ok";
  const cfg = SEVERITY[sev] || SEVERITY.ok;

  return (
    <section
      className={`border-2 ${cfg.cls} rounded-md p-4`}
      data-testid="capacity-now-card"
      aria-label={`Atlas capacity — ${cfg.label}`}
    >
      <header className="flex items-center gap-2 mb-2">
        <cfg.Icon className="w-4 h-4" />
        <span className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold">
          Atlas Capacity · {cfg.label}
        </span>
        {loading && (
          <Loader2 className="w-3 h-3 animate-spin text-slate-400 ml-auto" />
        )}
      </header>
      {err ? (
        <p className="text-xs text-slate-500 font-mono" data-testid="capacity-now-error">
          probe unavailable · {err}
        </p>
      ) : !data ? (
        <p className="text-xs text-slate-400 font-mono">loading…</p>
      ) : (
        <div className="space-y-1">
          <div className="text-sm font-mono" data-testid="capacity-now-usage">
            {Number(data.storage_used_mb || 0).toFixed(1)} MB
            {data.tier_quota_mb ? ` / ${data.tier_quota_mb} MB` : ""}
            {typeof data.storage_used_pct === "number" && data.tier_quota_mb
              ? ` · ${data.storage_used_pct.toFixed(1)}%`
              : ""}
          </div>
          {data.dbs && (
            <div
              className="text-[10px] text-slate-500 font-mono"
              data-testid="capacity-now-dbs"
            >
              {Object.entries(data.dbs)
                .map(([k, v]) => `${k}: ${Number(v).toFixed(1)} MB`)
                .join(" · ")}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default function AdminDatabase() {
  return (
    <LegacyAdminModernShell
      title="Database Capacity"
      subtitle="Storage trend and capacity forecast."
      breadcrumb={[
        { label: "Diagnostics", to: "/admin/diagnostics" },
        { label: "Database Capacity" },
      ]}
      testidPrefix="admin-database"
    >
      <div className="max-w-7xl mx-auto" data-testid="admin-database-page">
        <header className="bg-white border border-slate-200 rounded-md p-5 mb-4 flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-slate-800 text-white shrink-0">
            <Database className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600 font-bold">
              Storage Observability · Sigma-III
            </span>
            <h1 className="font-display text-2xl font-black tracking-tight mt-0.5">
              Database
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Read-only operational observability. Live cluster snapshot, 30-day storage trend, runway estimate.
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-4">
          <CapacityNow />
          <StorageObservabilityCard />
        </div>
      </div>
    </LegacyAdminModernShell>
  );
}
