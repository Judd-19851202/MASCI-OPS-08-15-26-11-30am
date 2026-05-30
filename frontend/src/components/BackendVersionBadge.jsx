import React, { useEffect, useState } from "react";

/**
 * BackendVersionBadge — tiny admin-only widget that calls `GET /api/version`
 * and renders a one-line status chip so the admin can tell at a glance
 * whether the live backend is actually running the latest deploy.
 *
 * Color logic:
 *   • green  — `/api/version` reachable AND uptime <= 7 days
 *              (normal state — backend was redeployed within the week)
 *   • amber  — `/api/version` reachable AND uptime > 7 days
 *              (might be stale — flag for review)
 *   • red    — `/api/version` unreachable or 404
 *              (old backend without the endpoint yet → definitely stale)
 *
 * Pairs naturally with `PersistenceHealthBanner` on Admin / PM hub pages.
 */

const API = process.env.REACT_APP_BACKEND_URL;
const WEEK_S = 7 * 24 * 60 * 60;

function fmtUptime(s) {
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  if (s < 86400) return `${Math.round(s / 3600)}h`;
  return `${Math.round(s / 86400)}d`;
}

export function BackendVersionBadge() {
  const [state, setState] = useState({ status: "loading", data: null });

  useEffect(() => {
    let alive = true;
    fetch(`${API}/api/version`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((data) => alive && setState({ status: "ok", data }))
      .catch((err) => alive && setState({ status: "err", error: String(err) }));
    return () => { alive = false; };
  }, []);

  if (state.status === "loading") {
    return (
      <div
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-[10px] font-mono uppercase tracking-[0.15em] text-slate-500"
        data-testid="backend-version-badge-loading"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" />
        Backend …
      </div>
    );
  }

  if (state.status === "err") {
    return (
      <div
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-50 border border-red-300 text-[10px] font-mono uppercase tracking-[0.15em] text-red-800"
        title={state.error}
        data-testid="backend-version-badge-err"
      >
        <span className="w-1.5 h-1.5 rounded-full bg-red-600" />
        Backend /api/version unreachable — redeploy
      </div>
    );
  }

  const { source_hash, commit, uptime_s, app_env } = state.data;
  // Gate to non-production environments — admins on production should not
  // see the deploy fingerprint pill in the live UI. Mirrors EnvBanner gating.
  if ((app_env || "production").toLowerCase() === "production") return null;
  const isAmber = uptime_s > WEEK_S;
  const shortHash = (source_hash || "").slice(0, 8) || "unknown";
  const shortCommit = commit && commit !== "unknown" ? commit.slice(0, 8) : null;

  const bg = isAmber ? "bg-amber-50 border-amber-300 text-amber-900"
                     : "bg-emerald-50 border-emerald-300 text-emerald-900";
  const dot = isAmber ? "bg-amber-500" : "bg-emerald-500";

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-[10px] font-mono uppercase tracking-[0.15em] ${bg}`}
      title={`source_hash=${source_hash}\ncommit=${commit}\nstarted_at=${state.data.started_at}`}
      data-testid="backend-version-badge"
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dot}`} />
      Backend {shortHash}
      {shortCommit && <span className="opacity-70">· {shortCommit}</span>}
      <span className="opacity-70">· up {fmtUptime(uptime_s || 0)}</span>
      {isAmber && <span className="font-bold">· stale?</span>}
    </div>
  );
}

export default BackendVersionBadge;
