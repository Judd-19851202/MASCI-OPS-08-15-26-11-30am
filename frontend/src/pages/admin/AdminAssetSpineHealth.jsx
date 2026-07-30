// FORGEDOPS · P0.1 · Asset Spine Health Dashboard.
//
// Single-page admin view backed by /api/asset-spine/health and /scan.
// Fleet-level counts + detector findings · audit-logged scan runs.
//
// Doctrine: /app/memory/MASTER_ASSET_GOVERNANCE_ARCHITECTURE.md §9–§10.

import { useEffect, useState, useCallback } from "react";
import {
  Activity, AlertTriangle, CheckCircle2, RefreshCw,
  Database, GitBranch, Search, Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
// TRACK 27.03 · Final Completion · canonical local-time formatter.
import { formatPlatformTime } from "@/lib/platformTime";
import { useNavigate } from "react-router-dom";

function _fmt(n) {
  return typeof n === "number" ? n.toLocaleString() : "—";
}

function _fmtPct(n) {
  return typeof n === "number" ? `${n.toFixed(1)}%` : "—";
}

function _fmtAt(s) {
  if (!s) return "never";
  return formatPlatformTime(s);
}

function detectorLabel(key) {
  return {
    duplicates: "Potential duplicates",
    retired_but_active: "Retired but still reporting",
    orphaned: "No recent signal",
    unsynced: "Missing Motive link",
  }[key] || key;
}

function actorLabel(value) {
  if (!value) return "Unknown actor";
  if (value === "scheduler") return "Scheduled scan";
  return String(value).replace(/[_-]+/g, " ");
}

function Stat({ label, value, hint, accent = "slate", testid }) {
  const colors = {
    slate: "text-slate-900 bg-white border-slate-200",
    emerald: "text-emerald-900 bg-emerald-50 border-emerald-200",
    amber: "text-amber-900 bg-amber-50 border-amber-200",
    red: "text-red-900 bg-red-50 border-red-200",
    sky: "text-sky-900 bg-sky-50 border-sky-200",
  }[accent] || "text-slate-900 bg-white border-slate-200";
  return (
    <div className={`rounded border ${colors} px-4 py-3`} data-testid={testid}>
      <div className="font-mono text-[10px] uppercase tracking-widest opacity-70">{label}</div>
      <div className="text-2xl font-black tabular-nums mt-0.5">{value}</div>
      {hint && <div className="text-xs opacity-70 mt-1">{hint}</div>}
    </div>
  );
}

export default function AdminAssetSpineHealth() {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [runs, setRuns] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setErr(null);
    try {
      const [h, r] = await Promise.all([
        api.get("/asset-spine/health"),
        api.get("/asset-spine/health/runs?limit=10"),
      ]);
      setHealth(h.data);
      setRuns(r.data?.items || []);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Failed to load");
    }
  }, []);

  // Initial fetch — inline to avoid the set-state-in-effect chain lint.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [h, r] = await Promise.all([
          api.get("/asset-spine/health"),
          api.get("/asset-spine/health/runs?limit=10"),
        ]);
        if (cancelled) return;
        setHealth(h.data);
        setRuns(r.data?.items || []);
      } catch (e) {
        if (cancelled) return;
        setErr(e?.response?.data?.detail || e?.message || "Failed to load");
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const onScan = useCallback(async () => {
    setScanning(true);
    setErr(null);
    try {
      await api.post("/asset-spine/health/scan", {});
      await load();
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Scan failed");
    } finally {
      setScanning(false);
    }
  }, [load]);

  const lastFindings = runs[0]?.findings_summary;
  const latestFindings = runs[0]?.findings;

  return (
    <LegacyAdminModernShell
      title="Asset Spine Health"
      subtitle="Read-only asset registry health for fleet records, mappings, and lifecycle integrity."
      breadcrumb={[
        { label: "Operations & Assets", to: "/admin/asset-mapping" },
        { label: "Asset Spine Health" },
      ]}
      testidPrefix="asset-spine-health"
      primaryActions={(
        <button
          type="button"
          onClick={onScan}
          disabled={scanning}
          className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          data-testid="asset-spine-scan-btn"
        >
          {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {scanning ? "Scanning…" : "Run scan now"}
        </button>
      )}
    >
      <div className="space-y-6" data-testid="asset-spine-health-page">
        <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl space-y-2">
              <div className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-700">
                Asset registry signal board
              </div>
              <h2 className="text-2xl font-black text-slate-950">What this page tells operators</h2>
              <p className="text-sm leading-relaxed text-slate-700">
                This board checks whether equipment records agree with the connected systems around them. A healthy card means the registry is aligned. An amber or red card means operators should review stale links, conflicting identities, or retired equipment that still appears active.
              </p>
            </div>
            <div className="grid min-w-[240px] grid-cols-2 gap-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-mono">Last scan</div>
                <div className="mt-2 text-sm font-semibold text-slate-950">{_fmtAt(health?.last_scan_at)}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <div className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-mono">Open issues</div>
                <div className="mt-2 text-2xl font-black text-slate-950">
                  {(lastFindings?.duplicates || 0) + (lastFindings?.retired_but_active || 0) + (lastFindings?.orphaned || 0) + (lastFindings?.unsynced || 0)}
                </div>
              </div>
            </div>
          </div>
        </section>

        {err && (
          <div className="px-4 py-3 rounded border-2 border-red-300 bg-red-50 text-sm text-red-900 font-semibold" data-testid="asset-spine-err">
            {err}
          </div>
        )}

        <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Stat
          label="Tracked assets"
          value={_fmt(health?.total_assets)}
          hint="records currently held in the core asset registry"
          accent="slate"
          testid="stat-total"
        />
        <Stat
          label="Working fleet"
          value={_fmt(health?.active_assets)}
          hint="assets still expected to report or operate"
          accent="emerald"
          testid="stat-active"
        />
        <Stat
          label="Retired records"
          value={_fmt(health?.retired_assets)}
          hint="kept for audit history only"
          accent="slate"
          testid="stat-retired"
        />
        <Stat
          label="Motive link coverage"
          value={_fmtPct(health?.motive_coverage_pct)}
          hint={`${_fmt(health?.mapped_to_motive)} linked · ${_fmt(health?.unmapped_to_motive)} still missing`}
          accent={
            (health?.motive_coverage_pct ?? 0) >= 95 ? "emerald" :
            (health?.motive_coverage_pct ?? 0) >= 75 ? "amber" : "red"
          }
          testid="stat-coverage"
        />
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <Stat
          label="Mapping review queue"
          value={_fmt(health?.mapping_queue_depth)}
          hint="suggested links waiting for human confirmation"
          accent={(health?.mapping_queue_depth ?? 0) > 0 ? "amber" : "emerald"}
          testid="stat-queue"
        />
        <Stat
          label="Identity conflicts"
          value={_fmt(health?.conflicts)}
          hint="records that disagree about what the asset actually is"
          accent={(health?.conflicts ?? 0) > 0 ? "amber" : "emerald"}
          testid="stat-conflicts"
        />
        <Stat
          label="Most recent scan"
          value={_fmtAt(health?.last_scan_at)}
          hint={lastFindings
            ? `${(lastFindings.duplicates || 0) + (lastFindings.retired_but_active || 0) + (lastFindings.orphaned || 0) + (lastFindings.unsynced || 0)} issues found`
            : "run a scan to capture the first snapshot"}
          accent="sky"
          testid="stat-last-scan"
        />
        </section>

        <section className="bg-white rounded border border-slate-200" data-testid="findings-card">
        <div className="px-5 py-3 border-b border-slate-200 flex items-center gap-2 bg-slate-50">
          <Search className="w-4 h-4 text-slate-700" />
          <h2 className="font-bold text-sm uppercase tracking-wider text-slate-900">
            Latest detector findings
          </h2>
          {runs[0]?.at && (
            <span className="ml-auto text-xs text-slate-500 font-mono">
              {_fmtAt(runs[0].at)}
            </span>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-slate-200">
            {[
            { key: "duplicates", label: "Potential duplicates", icon: GitBranch, note: "same VIN, serial, or unit appears more than once" },
            { key: "retired_but_active", label: "Retired but still reporting", icon: AlertTriangle, note: "retired equipment still shows recent activity" },
            { key: "orphaned", label: "No recent signal", icon: Activity, note: "active asset has not reported in 30 days" },
            { key: "unsynced", label: "Missing Motive link", icon: Database, note: "active asset has no live Motive mapping" },
          ].map(({ key, label, icon: Icon, note }) => {
            const n = lastFindings?.[key];
            const tone = n == null ? "slate" : n === 0 ? "emerald" : key === "retired_but_active" ? "red" : "amber";
            const accentMap = {
              slate: "text-slate-700",
              emerald: "text-emerald-700",
              amber: "text-amber-700",
              red: "text-red-700",
            };
            return (
              <div key={key} className="px-5 py-4" data-testid={`finding-${key}`}>
                <div className="flex items-center gap-2 mb-1">
                  <Icon className={`w-4 h-4 ${accentMap[tone]}`} />
                  <span className="font-mono text-[10px] uppercase tracking-widest text-slate-600 font-bold">
                    {label}
                  </span>
                </div>
                <div className={`text-2xl font-black tabular-nums ${accentMap[tone]}`}>
                  {n == null ? "—" : _fmt(n)}
                </div>
                <div className="text-xs text-slate-500 mt-1">{note}</div>
              </div>
            );
          })}
        </div>
        </section>

        {latestFindings?.unsynced?.length > 0 && (
          <section className="bg-white rounded border border-slate-200" data-testid="unsynced-card">
          <div className="px-5 py-3 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
            <Database className="w-4 h-4 text-amber-700" />
            <h2 className="font-bold text-sm uppercase tracking-wider text-slate-900">
              Assets still missing a Motive link
            </h2>
            <span className="ml-auto text-xs font-mono text-slate-500">
              showing {Math.min(20, latestFindings.unsynced.length)} of {latestFindings.unsynced.length}
            </span>
          </div>
          <ul className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
            {latestFindings.unsynced.slice(0, 20).map((f) => (
              <li key={f.asset_id}
                  className="px-5 py-2 flex items-center justify-between gap-3 text-sm hover:bg-slate-50 cursor-pointer"
                  onClick={() => navigate(`/admin/assets/${f.asset_id}`)}
                  data-testid={`unsynced-row-${f.asset_id}`}
              >
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-slate-900 truncate">
                    {f.asset_name || f.unit_number || "Asset record without a display name"}
                  </div>
                  <div className="text-xs text-slate-500">
                    {f.unit_number || "Unit number not recorded"} · {f.type || "Asset"}
                  </div>
                </div>
                <div className="text-xs font-mono uppercase tracking-wider text-amber-700">needs link</div>
              </li>
            ))}
          </ul>
          </section>
        )}

        <section className="bg-white rounded border border-slate-200" data-testid="runs-card">
        <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
          <h2 className="font-bold text-sm uppercase tracking-wider text-slate-900">
            Recent scan history
          </h2>
        </div>
        {runs.length === 0 ? (
          <div className="px-5 py-6 text-sm text-slate-500 italic text-center">
            No scans are recorded yet. Run the first scan to create a baseline.
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {runs.map((r) => (
              <li key={r.id} className="px-5 py-2 flex items-center justify-between gap-3 text-sm" data-testid={`run-${r.id}`}>
                <div className="font-mono text-xs text-slate-600">{_fmtAt(r.at)}</div>
                <div className="flex items-center gap-3 text-xs">
                  <span title="duplicates">
                    <CheckCircle2 className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.duplicates ?? 0) === 0 ? "text-emerald-600" : "text-amber-600"}`} />
                    duplicate {_fmt(r.findings_summary?.duplicates)}
                  </span>
                  <span title="retired_but_active">
                    <AlertTriangle className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.retired_but_active ?? 0) === 0 ? "text-emerald-600" : "text-red-600"}`} />
                    retired live {_fmt(r.findings_summary?.retired_but_active)}
                  </span>
                  <span title="orphaned">
                    <Activity className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.orphaned ?? 0) === 0 ? "text-emerald-600" : "text-amber-600"}`} />
                    no signal {_fmt(r.findings_summary?.orphaned)}
                  </span>
                  <span title="unsynced">
                    <Database className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.unsynced ?? 0) === 0 ? "text-emerald-600" : "text-amber-600"}`} />
                    missing link {_fmt(r.findings_summary?.unsynced)}
                  </span>
                </div>
                <div className="text-xs font-mono text-slate-500">{actorLabel(r.actor)}</div>
              </li>
            ))}
          </ul>
        )}
        </section>
      </div>
    </LegacyAdminModernShell>
  );
}
