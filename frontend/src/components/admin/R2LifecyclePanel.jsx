// TRACK 27.06 · R2 STORAGE LIFECYCLE PANEL
// ────────────────────────────────────────────────────────────────
// Operator surface for the storage-lifecycle governance system.
// Rendered inside `AdminStorageRecovery`. Read-only — the delete
// engine is disabled at the backend until Phase 7 unlocks.
//
// Sections:
//   1. Overall Storage Health score (from `/api/admin/r2/lifecycle/health`)
//   2. Classification breakdown ("VERIFIED_OWNER / VERIFIED_ORPHAN / …")
//   3. Top prefixes + top projects (executive analytics)
//   4. Dry-run preview (candidates + certification refusal state)
//   5. Trigger a fresh scan (idempotent · zero deletes)
//
// Every timestamp routes through `platformTime.js` (zero-UTC rule).
import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import { RefreshCw, HardDrive, ShieldCheck, AlertTriangle, Database, Layers } from "lucide-react";
import { toast } from "sonner";

import { getAdminToken } from "@/lib/adminAuth";
import { formatRelativeTime } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;

function _band(band) {
  switch ((band || "").toUpperCase()) {
    case "GREEN": return { bg: "bg-emerald-50", ring: "ring-emerald-300", text: "text-emerald-800", pill: "GREEN" };
    case "AMBER": return { bg: "bg-amber-50", ring: "ring-amber-300", text: "text-amber-800", pill: "AMBER" };
    case "RED":   return { bg: "bg-red-50", ring: "ring-red-300", text: "text-red-800", pill: "RED" };
    default:      return { bg: "bg-slate-50", ring: "ring-slate-300", text: "text-slate-700", pill: "UNKNOWN" };
  }
}

function _gb(bytes) {
  if (!bytes) return "0 B";
  const gb = bytes / (1024 ** 3);
  if (gb >= 1) return `${gb.toFixed(2)} GB`;
  const mb = bytes / (1024 ** 2);
  if (mb >= 1) return `${mb.toFixed(1)} MB`;
  return `${(bytes / 1024).toFixed(0)} KB`;
}

async function _get(path) {
  return axios.get(`${API}${path}`, {
    headers: { "X-Admin-Token": getAdminToken() || "" },
    timeout: 60000,
  });
}
async function _post(path) {
  return axios.post(`${API}${path}`, {}, {
    headers: { "X-Admin-Token": getAdminToken() || "" },
    timeout: 120000,
  });
}

export default function R2LifecyclePanel() {
  const [latest, setLatest] = useState(null);
  const [intel, setIntel] = useState(null);
  const [dryRun, setDryRun] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [err, setErr] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const [l, i, d] = await Promise.all([
        _get("/api/admin/r2/lifecycle/latest"),
        _get("/api/admin/r2/lifecycle/intelligence"),
        _post("/api/admin/r2/lifecycle/dry-run"),
      ]);
      setLatest(l.data);
      setIntel(i.data);
      setDryRun(d.data);
    } catch (e) {
      setErr(e?.response?.data?.detail || e?.message || "Failed to load lifecycle data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const runScan = useCallback(async (maxPages) => {
    setScanning(true);
    try {
      const q = maxPages ? `?max_pages=${maxPages}` : "";
      const { data } = await _post(`/api/admin/r2/lifecycle/scan${q}`);
      toast.success(`Scanned ${data.inventory?.total_objects || 0} objects · ${data.classification?.counts?.VERIFIED_ORPHAN || 0} orphan candidates`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Scan failed");
    } finally {
      setScanning(false);
    }
  }, [load]);

  if (err) {
    return (
      <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800" data-testid="r2-lifecycle-error">
        <div className="font-semibold mb-1">Lifecycle unreachable</div>
        <div className="text-xs">{err}</div>
      </div>
    );
  }

  const health = latest?.health;
  const bandStyle = _band(health?.band);
  const cls = latest?.classification?.counts || {};
  const inv = latest?.inventory || {};
  const objects = health?.objects || {};

  return (
    <div className="space-y-4" data-testid="r2-lifecycle-panel">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
            <HardDrive className="w-5 h-5" /> R2 Storage Lifecycle
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Every object · verified owner · evidence-backed. Read-only — deletion is out of scope.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => runScan(3)}
            disabled={scanning}
            className="text-xs px-3 py-1.5 rounded-md border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-50 font-semibold"
            data-testid="r2-lifecycle-scan-preview"
          >
            {scanning ? "Scanning…" : "Quick scan (3 pages)"}
          </button>
          <button
            onClick={() => runScan(undefined)}
            disabled={scanning}
            className="text-xs px-3 py-1.5 rounded-md border border-slate-900 bg-slate-900 text-white hover:bg-slate-800 disabled:opacity-50 font-semibold inline-flex items-center gap-1.5"
            data-testid="r2-lifecycle-scan-full"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? "animate-spin" : ""}`} />
            {scanning ? "Scanning…" : "Full lifecycle scan"}
          </button>
        </div>
      </div>

      {/* Health score */}
      <div className={`rounded-lg border ${bandStyle.ring} ring-1 ${bandStyle.bg} p-4`} data-testid="r2-lifecycle-health-card">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Storage Health</div>
            <div className={`text-3xl font-black leading-none mt-1 ${bandStyle.text}`} data-testid="r2-lifecycle-health-score">
              {health?.overall_score ?? "—"}<span className="text-lg opacity-60">/100</span>
            </div>
          </div>
          <span className={`px-2 py-1 rounded font-mono text-[10px] tracking-widest font-bold ${bandStyle.text} border border-current`} data-testid="r2-lifecycle-health-band">
            {bandStyle.pill}
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4 text-xs">
          {Object.entries(health?.sub_scores || {}).map(([k, v]) => (
            <div key={k} className="rounded bg-white border border-slate-200 p-2" data-testid={`r2-lifecycle-sub-${k}`}>
              <div className="font-mono text-[9px] uppercase tracking-widest text-slate-500 truncate">{k.replace(/_score$/, "").replace(/_/g, " ")}</div>
              <div className="font-black text-slate-900 text-sm mt-0.5">{v}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-2 mt-3 text-xs text-slate-600">
          <div>Bucket: <strong>{health?.capacity?.gb?.toFixed(1) ?? "—"} GB</strong> (alert {health?.capacity?.alert_gb} GB)</div>
          <div>Objects: <strong>{objects.total ?? "—"}</strong></div>
          <div>Orphans: <strong>{objects.verified_orphan ?? "—"}</strong> ({objects.orphan_pct ?? 0}%)</div>
        </div>
      </div>

      {/* Classification */}
      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="r2-lifecycle-classification-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-black text-slate-900 flex items-center gap-1.5">
            <Layers className="w-4 h-4" /> Classification Snapshot
          </h3>
          <div className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
            {latest?.classification?.completed_at
              ? `Last run · ${formatRelativeTime(latest.classification.completed_at)}`
              : "Never scanned"}
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
          {Object.entries(cls).map(([klass, count]) => (
            <div key={klass}
                 className={`rounded p-2 border ${
                   klass === "VERIFIED_ORPHAN" && count > 0 ? "border-amber-300 bg-amber-50" :
                   klass === "VERIFIED_OWNER" && count > 0 ? "border-emerald-300 bg-emerald-50" :
                   klass === "AMBIGUOUS" && count > 0 ? "border-red-300 bg-red-50" :
                   "border-slate-200 bg-slate-50"
                 }`}
                 data-testid={`r2-lifecycle-class-${klass}`}>
              <div className="font-mono text-[9px] uppercase tracking-widest text-slate-500">{klass.replace(/_/g, " ")}</div>
              <div className="font-black text-slate-900 text-lg mt-0.5">{count}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Dry-run */}
      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="r2-lifecycle-dry-run-card">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-black text-slate-900 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" /> Dry-Run · Certification Gate
          </h3>
          <span className="px-2 py-1 rounded font-mono text-[10px] uppercase tracking-widest border border-slate-300 bg-slate-100 text-slate-700">
            Delete engine {dryRun?.delete_engine_status || "DISABLED"}
          </span>
        </div>
        <div className="text-sm text-slate-700 space-y-1">
          <div><strong>Candidates:</strong> {dryRun?.candidates_count ?? 0} objects · <strong>{dryRun?.candidates_total_gb ?? 0} GB</strong> would be reclaimed.</div>
          <div><strong>Certification:</strong>{" "}
            <span className={dryRun?.certification?.batch_allowed ? "text-emerald-700 font-semibold" : "text-red-700 font-semibold"}>
              {dryRun?.certification?.batch_allowed ? "batch allowed" : dryRun?.certification?.refusal_reason || "batch refused"}
            </span>
          </div>
          <div className="text-xs text-slate-500 italic mt-2">{dryRun?.policy}</div>
        </div>
        {(dryRun?.candidates_sample || []).length > 0 && (
          <div className="mt-3 max-h-56 overflow-y-auto border border-slate-100 rounded" data-testid="r2-lifecycle-candidates-list">
            <table className="w-full text-xs">
              <thead className="bg-slate-50 text-slate-500 font-mono uppercase tracking-wide text-[9px]">
                <tr><th className="text-left px-2 py-1">Key</th><th className="text-right px-2 py-1">Size</th></tr>
              </thead>
              <tbody>
                {(dryRun.candidates_sample || []).slice(0, 20).map((c) => (
                  <tr key={c.key} className="border-t border-slate-100">
                    <td className="px-2 py-1 truncate max-w-md font-mono text-[10px]" title={c.key}>{c.key}</td>
                    <td className="px-2 py-1 text-right tabular-nums">{_gb(c.size)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Executive intel */}
      <div className="grid md:grid-cols-2 gap-3">
        <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="r2-lifecycle-top-prefixes">
          <h3 className="text-sm font-black text-slate-900 flex items-center gap-1.5 mb-2">
            <Database className="w-4 h-4" /> GB by Prefix (top 5)
          </h3>
          <ul className="text-xs space-y-1">
            {(intel?.top_prefixes || []).slice(0, 5).map((p) => (
              <li key={p.prefix} className="flex justify-between">
                <span className="font-mono truncate">{p.prefix}</span>
                <span className="tabular-nums text-slate-600">{p.gb} GB · {p.count} objs</span>
              </li>
            ))}
            {(intel?.top_prefixes || []).length === 0 && (
              <li className="text-slate-500 italic">No inventory yet — click "Full lifecycle scan".</li>
            )}
          </ul>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="r2-lifecycle-cost">
          <h3 className="text-sm font-black text-slate-900 flex items-center gap-1.5 mb-2">
            <AlertTriangle className="w-4 h-4" /> Cost Intelligence (R2)
          </h3>
          <ul className="text-xs space-y-1">
            <li className="flex justify-between"><span>Current monthly</span><strong>${intel?.cost?.current_monthly_usd?.toFixed(2) ?? "—"}</strong></li>
            <li className="flex justify-between"><span>Current annual</span><strong>${intel?.cost?.current_annual_usd?.toFixed(2) ?? "—"}</strong></li>
            <li className="flex justify-between text-amber-800"><span>Orphan reclaim / month</span><strong>${intel?.cost?.orphan_reclaim_monthly_usd?.toFixed(2) ?? "—"}</strong></li>
            <li className="flex justify-between text-amber-800"><span>Projected savings</span><strong>{intel?.cost?.projected_savings_pct ?? "—"}%</strong></li>
          </ul>
          <div className="mt-2 text-[10px] text-slate-500 italic">
            At Cloudflare R2 ${intel?.cost?.unit_price_usd_per_gb_month ?? "0.015"} / GB-month. Egress is free.
          </div>
        </div>
      </div>
    </div>
  );
}
