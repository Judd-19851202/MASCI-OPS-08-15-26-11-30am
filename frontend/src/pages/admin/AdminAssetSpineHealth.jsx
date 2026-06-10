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
import { useNavigate } from "react-router-dom";

function _fmt(n) {
  return typeof n === "number" ? n.toLocaleString() : "—";
}

function _fmtPct(n) {
  return typeof n === "number" ? `${n.toFixed(1)}%` : "—";
}

function _fmtAt(s) {
  if (!s) return "never";
  try {
    const d = new Date(s);
    return d.toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
  } catch { return s; }
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
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8" data-testid="asset-spine-health-page">
      <div className="flex items-start justify-between gap-3 mb-6">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.22em] text-red-700 font-bold mb-1">
            ForgedOps · P0.1
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            Asset Spine Health
          </h1>
          <p className="text-sm text-slate-600 mt-1 max-w-2xl">
            Single source-of-truth posture across <code className="text-xs px-1 bg-slate-100 rounded">equipment_master</code>,
            Motive mappings, MaintainX, FleetWatcher. Read-only detectors only — no asset is mutated by this page.
          </p>
        </div>
        <button
          type="button"
          onClick={onScan}
          disabled={scanning}
          className="px-4 py-2 rounded bg-slate-900 hover:bg-black text-white font-bold uppercase tracking-wider text-xs flex items-center gap-2 disabled:opacity-60"
          data-testid="asset-spine-scan-btn"
        >
          {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {scanning ? "Scanning…" : "Run Scan Now"}
        </button>
      </div>

      {err && (
        <div className="mb-4 px-4 py-3 rounded border-2 border-red-300 bg-red-50 text-sm text-red-900 font-semibold" data-testid="asset-spine-err">
          {err}
        </div>
      )}

      {/* Fleet-level counts */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <Stat
          label="Total Assets"
          value={_fmt(health?.total_assets)}
          hint="across equipment_master"
          accent="slate"
          testid="stat-total"
        />
        <Stat
          label="Active"
          value={_fmt(health?.active_assets)}
          hint="not retired"
          accent="emerald"
          testid="stat-active"
        />
        <Stat
          label="Retired"
          value={_fmt(health?.retired_assets)}
          hint="preserved for audit"
          accent="slate"
          testid="stat-retired"
        />
        <Stat
          label="Motive Coverage"
          value={_fmtPct(health?.motive_coverage_pct)}
          hint={`${_fmt(health?.mapped_to_motive)} mapped / ${_fmt(health?.unmapped_to_motive)} unmapped`}
          accent={
            (health?.motive_coverage_pct ?? 0) >= 95 ? "emerald" :
            (health?.motive_coverage_pct ?? 0) >= 75 ? "amber" : "red"
          }
          testid="stat-coverage"
        />
      </section>

      {/* Reconciliation posture */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
        <Stat
          label="Mapping Queue"
          value={_fmt(health?.mapping_queue_depth)}
          hint="proposals awaiting operator approval"
          accent={(health?.mapping_queue_depth ?? 0) > 0 ? "amber" : "emerald"}
          testid="stat-queue"
        />
        <Stat
          label="Identity Conflicts"
          value={_fmt(health?.conflicts)}
          hint="project_identity_conflicts"
          accent={(health?.conflicts ?? 0) > 0 ? "amber" : "emerald"}
          testid="stat-conflicts"
        />
        <Stat
          label="Last Scan"
          value={_fmtAt(health?.last_scan_at)}
          hint={lastFindings
            ? `${(lastFindings.duplicates || 0) + (lastFindings.retired_but_active || 0) + (lastFindings.orphaned || 0) + (lastFindings.unsynced || 0)} findings`
            : "press \"Run Scan Now\""}
          accent="sky"
          testid="stat-last-scan"
        />
      </section>

      {/* Last scan findings (4-detector grid) */}
      <section className="bg-white rounded border border-slate-200 mb-6" data-testid="findings-card">
        <div className="px-5 py-3 border-b border-slate-200 flex items-center gap-2 bg-slate-50">
          <Search className="w-4 h-4 text-slate-700" />
          <h2 className="font-bold text-sm uppercase tracking-wider text-slate-900">
            Detector Findings (last scan)
          </h2>
          {runs[0]?.at && (
            <span className="ml-auto text-xs text-slate-500 font-mono">
              {_fmtAt(runs[0].at)}
            </span>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-slate-200">
          {[
            { key: "duplicates", label: "Duplicates", icon: GitBranch, note: "shared VIN / serial / unit number" },
            { key: "retired_but_active", label: "Retired but Active", icon: AlertTriangle, note: "Motive event < 72h on retired asset" },
            { key: "orphaned", label: "Orphaned", icon: Activity, note: "active, no signal in 30 days" },
            { key: "unsynced", label: "Unsynced", icon: Database, note: "active, no Motive mapping" },
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

      {/* Detailed unsynced list — actionable */}
      {latestFindings?.unsynced?.length > 0 && (
        <section className="bg-white rounded border border-slate-200 mb-6" data-testid="unsynced-card">
          <div className="px-5 py-3 border-b border-slate-200 bg-slate-50 flex items-center gap-2">
            <Database className="w-4 h-4 text-amber-700" />
            <h2 className="font-bold text-sm uppercase tracking-wider text-slate-900">
              Unsynced Assets — needs Motive mapping
            </h2>
            <span className="ml-auto text-xs font-mono text-slate-500">
              showing {Math.min(20, latestFindings.unsynced.length)} of {latestFindings.unsynced.length}
            </span>
          </div>
          <ul className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
            {latestFindings.unsynced.slice(0, 20).map((f) => (
              <li key={f.asset_id}
                  className="px-5 py-2 flex items-center justify-between gap-3 text-sm hover:bg-slate-50 cursor-pointer"
                  onClick={() => navigate(`/admin/asset/${f.asset_id}`)}
                  data-testid={`unsynced-row-${f.asset_id}`}
              >
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-slate-900 truncate">
                    {f.asset_name || f.unit_number || f.asset_id}
                  </div>
                  <div className="text-xs text-slate-500">
                    {f.unit_number || "—"} · {f.type || "Asset"}
                  </div>
                </div>
                <div className="text-xs font-mono uppercase tracking-wider text-amber-700">no mapping</div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Recent scan runs (audit) */}
      <section className="bg-white rounded border border-slate-200" data-testid="runs-card">
        <div className="px-5 py-3 border-b border-slate-200 bg-slate-50">
          <h2 className="font-bold text-sm uppercase tracking-wider text-slate-900">
            Recent Scan Runs (audit)
          </h2>
        </div>
        {runs.length === 0 ? (
          <div className="px-5 py-6 text-sm text-slate-500 italic text-center">
            No scans recorded yet. Press <strong>Run Scan Now</strong> to capture the first.
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {runs.map((r) => (
              <li key={r.id} className="px-5 py-2 flex items-center justify-between gap-3 text-sm" data-testid={`run-${r.id}`}>
                <div className="font-mono text-xs text-slate-600">{_fmtAt(r.at)}</div>
                <div className="flex items-center gap-3 text-xs">
                  <span title="duplicates">
                    <CheckCircle2 className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.duplicates ?? 0) === 0 ? "text-emerald-600" : "text-amber-600"}`} />
                    dup {_fmt(r.findings_summary?.duplicates)}
                  </span>
                  <span title="retired_but_active">
                    <AlertTriangle className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.retired_but_active ?? 0) === 0 ? "text-emerald-600" : "text-red-600"}`} />
                    re-active {_fmt(r.findings_summary?.retired_but_active)}
                  </span>
                  <span title="orphaned">
                    <Activity className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.orphaned ?? 0) === 0 ? "text-emerald-600" : "text-amber-600"}`} />
                    orphan {_fmt(r.findings_summary?.orphaned)}
                  </span>
                  <span title="unsynced">
                    <Database className={`inline w-3 h-3 mr-0.5 ${(r.findings_summary?.unsynced ?? 0) === 0 ? "text-emerald-600" : "text-amber-600"}`} />
                    unsync {_fmt(r.findings_summary?.unsynced)}
                  </span>
                </div>
                <div className="text-xs font-mono text-slate-500">{r.actor}</div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
