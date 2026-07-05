// MotivePostureRibbon.jsx — TRACK 22.4a · Operator Trust Repair.
//
// Renders a calm, non-panic ribbon at the top of Dispatch surfaces when
// Motive is UNREACHABLE, STALE, MISSING_CONFIG, or otherwise not
// LIVE_VERIFIED. Consumes the dispatch-safe endpoint
// `/api/dispatch/motive-posture` — the same three-state truth model as
// the admin Integration Truth surface, so operators see the same
// honesty their admins see, right where they work.
//
// Trust doctrine (F-01/F-02 remediation):
//   • Never renders "map is live" when Motive is not LIVE_VERIFIED.
//   • Never hides stale integration state behind an admin-only page.
//   • Never blocks the map or the dispatch primary actions.
import React, { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, RefreshCcw, Loader2 } from "lucide-react";
import { getAdminToken } from "@/lib/adminAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";

const API = process.env.REACT_APP_BACKEND_URL;

const RIBBON_TONE = {
  LIVE_VERIFIED: {
    bg: "bg-emerald-50",
    border: "border-emerald-300",
    text: "text-emerald-900",
    icon: CheckCircle2,
    label: "MOTIVE · LIVE",
  },
  CONFIGURED: {
    bg: "bg-amber-50",
    border: "border-amber-300",
    text: "text-amber-900",
    icon: AlertTriangle,
    label: "MOTIVE · AWAITING FIRST SYNC",
  },
  UNREACHABLE: {
    bg: "bg-amber-50",
    border: "border-amber-300",
    text: "text-amber-900",
    icon: AlertTriangle,
    label: "MOTIVE · CONNECTIVITY DEGRADED",
  },
  MISSING_CONFIG: {
    bg: "bg-slate-50",
    border: "border-slate-300",
    text: "text-slate-800",
    icon: AlertTriangle,
    label: "MOTIVE · NOT CONFIGURED",
  },
  MISSING_SECRET: {
    bg: "bg-slate-50",
    border: "border-slate-300",
    text: "text-slate-800",
    icon: AlertTriangle,
    label: "MOTIVE · MISSING CREDENTIALS",
  },
  DISABLED: {
    bg: "bg-slate-50",
    border: "border-slate-300",
    text: "text-slate-700",
    icon: AlertTriangle,
    label: "MOTIVE · DISABLED",
  },
  PARTIAL: {
    bg: "bg-amber-50",
    border: "border-amber-300",
    text: "text-amber-900",
    icon: AlertTriangle,
    label: "MOTIVE · PARTIAL",
  },
  ERROR: {
    bg: "bg-red-50",
    border: "border-red-300",
    text: "text-red-900",
    icon: AlertTriangle,
    label: "MOTIVE · ERROR",
  },
  DEFAULT: {
    bg: "bg-slate-50",
    border: "border-slate-300",
    text: "text-slate-800",
    icon: AlertTriangle,
    label: "MOTIVE · UNKNOWN",
  },
};

function messageFor(payload) {
  const overall = payload?.overall || "DEFAULT";
  switch (overall) {
    case "LIVE_VERIFIED":
      return "Motive is live and delivering recent position data.";
    case "UNREACHABLE":
      return "Motive location feed is not currently verified. Dispatch assignments remain available, but live fleet location may be incomplete.";
    case "MISSING_CONFIG":
    case "MISSING_SECRET":
      return "Motive credentials are not configured in this environment. The map renders demo/geofence data only; live fleet position is not available.";
    case "CONFIGURED":
      return "Motive credentials are present, but no recent successful sync has been observed. Dispatch assignments remain available.";
    case "PARTIAL":
      return "Motive is partially configured. Some live signals may be missing.";
    case "DISABLED":
      return "Motive integration is disabled. Dispatch operates on assignments and roll-off data only.";
    case "ERROR":
      return "Motive reported an error. Dispatch assignments remain available.";
    default:
      return "Motive live status could not be determined.";
  }
}

async function fetchPosture({ timeoutMs = 3000 } = {}) {
  const admin = getAdminToken?.();
  const dispatch = getDispatchToken?.();
  const headers = { "Content-Type": "application/json" };
  if (admin) headers["X-Admin-Token"] = admin;
  if (dispatch) headers["X-Dispatch-Token"] = dispatch;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const r = await fetch(`${API}/api/dispatch/motive-posture`, {
      headers,
      signal: controller.signal,
    });
    if (!r.ok) {
      return { ok: false, status: r.status, body: null };
    }
    const body = await r.json().catch(() => null);
    return { ok: true, status: r.status, body };
  } catch (err) {
    return { ok: false, status: 0, body: null, aborted: err?.name === "AbortError" };
  } finally {
    clearTimeout(timer);
  }
}

function fmtRelative(iso) {
  if (!iso) return "never";
  try {
    const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  } catch {
    return "—";
  }
}

export default function MotivePostureRibbon({
  testId = "motive-posture-ribbon",
  hideWhenLive = false,
}) {
  const [state, setState] = useState({ loaded: false, ok: false, body: null });

  const load = useCallback(() => {
    setState((s) => ({ ...s, loaded: false }));
    fetchPosture().then((r) => setState({ loaded: true, ...r }));
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchPosture().then((r) => {
      if (!cancelled) setState({ loaded: true, ...r });
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // Never blocks the map — while loading, render a slim non-committal
  // placeholder so the UI doesn't jump.
  if (!state.loaded) {
    return (
      <div
        data-testid={`${testId}-loading`}
        className="mb-3 flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600"
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Checking Motive live posture…
      </div>
    );
  }

  // Failure to fetch the posture itself is truthful too — do not
  // silently hide it.
  if (!state.ok || !state.body) {
    return (
      <div
        data-testid={`${testId}-error`}
        className="mb-3 flex items-center justify-between gap-3 rounded-md border-2 border-slate-200 bg-white px-3 py-2 text-xs text-slate-700"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-3.5 w-3.5" />
          <span>
            Motive posture unavailable. Dispatch assignments and roll-off data
            remain available.
          </span>
        </div>
        <button
          type="button"
          onClick={load}
          data-testid={`${testId}-retry`}
          className="inline-flex items-center gap-1 rounded border border-slate-300 px-2 py-0.5 text-[11px] font-mono uppercase tracking-widest font-bold hover:border-slate-500"
        >
          <RefreshCcw className="h-3 w-3" /> Retry
        </button>
      </div>
    );
  }

  const overall = state.body.overall || "DEFAULT";
  const tone = RIBBON_TONE[overall] || RIBBON_TONE.DEFAULT;
  const Icon = tone.icon;
  const lastSync = state.body.last_successful_sync_at;

  // Doctrine: never render a green "live" claim unless operational
  // status is truly LIVE_VERIFIED. hideWhenLive lets the map author
  // suppress the ribbon entirely on the happy path.
  if (overall === "LIVE_VERIFIED" && hideWhenLive) return null;

  return (
    <div
      data-testid={testId}
      className={`mb-3 flex flex-col gap-2 rounded-md border-2 ${tone.border} ${tone.bg} px-3 py-2 text-sm ${tone.text} sm:flex-row sm:items-center sm:justify-between`}
    >
      <div className="flex items-start gap-2">
        <Icon className="mt-0.5 h-4 w-4 flex-shrink-0" />
        <div>
          <div
            data-testid={`${testId}-label`}
            className="font-mono text-[11px] uppercase tracking-widest font-bold"
          >
            {tone.label}
          </div>
          <div className="mt-0.5 text-xs sm:text-sm" data-testid={`${testId}-message`}>
            {messageFor(state.body)}
          </div>
          <div className="mt-0.5 text-[11px] opacity-80">
            last sync: <span data-testid={`${testId}-last-sync`}>{fmtRelative(lastSync)}</span>
            {" · "}config: <span data-testid={`${testId}-config`}>{state.body.config_status}</span>
            {" · "}connectivity: <span data-testid={`${testId}-connectivity`}>{state.body.connectivity_status}</span>
            {" · "}operational: <span data-testid={`${testId}-operational`}>{state.body.operational_status}</span>
          </div>
        </div>
      </div>
      <button
        type="button"
        onClick={load}
        data-testid={`${testId}-refresh`}
        className="inline-flex items-center gap-1 self-start rounded border-2 border-current px-2 py-1 text-[11px] font-mono uppercase tracking-widest font-bold hover:opacity-80 sm:self-auto"
      >
        <RefreshCcw className="h-3 w-3" /> Refresh
      </button>
    </div>
  );
}
