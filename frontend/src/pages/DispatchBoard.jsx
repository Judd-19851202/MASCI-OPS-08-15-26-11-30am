/**
 * DispatchBoard.jsx · iter394 · DLS Operational Flow Board.
 *
 * Route: /dispatch-portal/board (dispatch + admin only)
 *
 * The operational heartbeat. Truck-by-truck rows. Tone-keyed state
 * chips. Glanceable wait visibility. One drawer per row for full
 * history + the four canonical dispatcher actions (magic-link issue,
 * cancel, reassign, revoke session).
 *
 * Restraint doctrine (per iter394 directive):
 *   • No maps, no GPS, no charts, no analytics.
 *   • No filters / search chrome — board is small enough to scan.
 *   • Calm, slate canvas. Wait + breakdown rows alone get warning tone.
 *   • Polls every 5 s. The driver lifecycle layer is the source of
 *     truth — we never duplicate state locally beyond a snapshot.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Truck, ArrowLeft, AlertTriangle, Wrench, Clock, Activity, RefreshCw, Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { paletteFor } from "@/lib/portalPalette";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { usePageTitle } from "@/lib/usePageTitle";
import { toast } from "sonner";
import AssignmentDrawer from "@/components/dispatch/AssignmentDrawer";

const API = process.env.REACT_APP_BACKEND_URL;
const DISPATCH_PAL = paletteFor("dispatch");
const POLL_MS = 5000;
const STUCK_THRESHOLD_MIN = 30;

const STATE_LABEL = {
  ASSIGNED: "Assigned",
  ENROUTE_TO_LOAD: "En route · load",
  AT_LOAD_SITE: "At load",
  LOADING: "Loading",
  LOADED: "Loaded",
  ENROUTE_TO_JOB: "En route · job",
  ARRIVED_JOB: "At job",
  DUMPING: "Dumping",
  COMPLETE: "Complete",
  WAITING: "Waiting",
  HOLD: "Hold",
  BREAKDOWN: "Breakdown",
  OFF_SHIFT: "Off shift",
};

const STATE_TONE = {
  ASSIGNED: "bg-slate-100 text-slate-800 border-slate-300",
  ENROUTE_TO_LOAD: "bg-sky-50 text-sky-800 border-sky-300",
  AT_LOAD_SITE: "bg-sky-100 text-sky-900 border-sky-400",
  LOADING: "bg-indigo-50 text-indigo-800 border-indigo-300",
  LOADED: "bg-indigo-100 text-indigo-900 border-indigo-400",
  ENROUTE_TO_JOB: "bg-emerald-50 text-emerald-800 border-emerald-300",
  ARRIVED_JOB: "bg-emerald-100 text-emerald-900 border-emerald-400",
  DUMPING: "bg-amber-50 text-amber-800 border-amber-300",
  COMPLETE: "bg-emerald-200 text-emerald-900 border-emerald-500",
  WAITING: "bg-rose-50 text-rose-800 border-rose-300",
  HOLD: "bg-slate-200 text-slate-800 border-slate-400",
  BREAKDOWN: "bg-rose-100 text-rose-900 border-rose-400",
  OFF_SHIFT: "bg-slate-100 text-slate-600 border-slate-300",
};

function authHeaders(tenantOverride) {
  const headers = { "Content-Type": "application/json" };
  const admin = getAdminToken();
  const disp = getDispatchToken();
  if (admin) headers["X-Admin-Token"] = admin;
  if (disp) headers["X-Dispatch-Token"] = disp;
  if (tenantOverride) headers["X-Tenant-Id"] = tenantOverride;
  return headers;
}

function minutesSince(iso) {
  if (!iso) return null;
  try {
    const t = new Date(iso).getTime();
    if (Number.isNaN(t)) return null;
    return Math.max(0, Math.round((Date.now() - t) / 60000));
  } catch {
    return null;
  }
}

function StateChip({ state }) {
  const tone = STATE_TONE[state] || STATE_TONE.ASSIGNED;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide border ${tone}`}
      data-testid={`board-state-${state}`}
    >
      {STATE_LABEL[state] || state || "—"}
    </span>
  );
}

function SummaryStrip({ assignments }) {
  const counts = useMemo(() => {
    const base = {
      active: 0, waiting: 0, breakdown: 0, stuck: 0,
    };
    for (const a of assignments) {
      base.active += 1;
      if (a.current_state === "WAITING") base.waiting += 1;
      if (a.current_state === "BREAKDOWN") base.breakdown += 1;
      const m = minutesSince(a.last_transition_at);
      if (m !== null && m >= STUCK_THRESHOLD_MIN) base.stuck += 1;
    }
    return base;
  }, [assignments]);

  const tile = (label, value, icon, tone, testId) => (
    <div
      data-testid={testId}
      className={`flex-1 min-w-[120px] rounded-lg border px-4 py-3 flex items-center gap-3 ${tone}`}
    >
      {icon}
      <div>
        <div className="text-xs uppercase tracking-widest opacity-70">{label}</div>
        <div className="text-2xl font-black leading-none mt-0.5">{value}</div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-wrap gap-3" data-testid="board-summary-strip">
      {tile(
        "Active hauls", counts.active,
        <Activity className="w-5 h-5 text-slate-700" />,
        "bg-white border-slate-200",
        "summary-active",
      )}
      {tile(
        "Waiting", counts.waiting,
        <Clock className="w-5 h-5 text-rose-700" />,
        "bg-rose-50 border-rose-200",
        "summary-waiting",
      )}
      {tile(
        "Breakdown", counts.breakdown,
        <Wrench className="w-5 h-5 text-rose-800" />,
        "bg-rose-100 border-rose-300",
        "summary-breakdown",
      )}
      {tile(
        `Stuck > ${STUCK_THRESHOLD_MIN}m`, counts.stuck,
        <AlertTriangle className="w-5 h-5 text-amber-700" />,
        "bg-amber-50 border-amber-200",
        "summary-stuck",
      )}
    </div>
  );
}

function AssignmentRow({ a, onOpen }) {
  const m = minutesSince(a.last_transition_at);
  const isStuck = m !== null && m >= STUCK_THRESHOLD_MIN;
  const isWaiting = a.current_state === "WAITING";
  const isBreakdown = a.current_state === "BREAKDOWN";
  const tone =
    isBreakdown ? "border-rose-300 bg-rose-50" :
    isWaiting   ? "border-rose-200 bg-rose-50/60" :
    isStuck     ? "border-amber-300 bg-amber-50" :
                  "border-slate-200 bg-white";

  return (
    <button
      type="button"
      data-testid={`board-row-${a.id}`}
      onClick={() => onOpen(a)}
      className={`w-full text-left rounded-lg border ${tone} px-4 py-3 hover:shadow-md hover:border-orange-400 transition-shadow flex flex-col sm:flex-row sm:items-center gap-3`}
    >
      <div className="flex items-center gap-3 min-w-[180px] sm:w-56">
        <Truck className="w-5 h-5 text-slate-700 shrink-0" />
        <div>
          <div className="font-bold text-slate-900 text-sm" data-testid={`row-truck-${a.id}`}>
            {a.truck_id || "—"}
          </div>
          <div className="text-xs text-slate-600 truncate max-w-[180px]">
            {a.driver_name || a.driver_id || "—"}
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-1 min-w-[180px]">
        <StateChip state={a.current_state} />
        {isWaiting && a.current_wait_reason ? (
          <span className="text-[11px] text-rose-700 font-bold tracking-wide" data-testid={`row-wait-${a.id}`}>
            {a.current_wait_reason.replace(/_/g, " ")}
          </span>
        ) : null}
      </div>

      <div className="flex-1 min-w-[160px] text-xs text-slate-700">
        <div className="font-bold truncate" data-testid={`row-project-${a.id}`}>
          {a.project_name || a.project_number || "Unassigned project"}
        </div>
        <div className="text-slate-500 truncate">
          {[a.material, a.source_location, a.destination].filter(Boolean).join(" → ")}
        </div>
      </div>

      <div className="text-right shrink-0">
        <div className={`text-xs font-bold ${isStuck ? "text-amber-700" : "text-slate-600"}`}>
          {m === null ? "—" : `${m}m in state`}
        </div>
        <div className="text-[11px] text-slate-400 uppercase tracking-wider">
          tap for actions
        </div>
      </div>
    </button>
  );
}

export default function DispatchBoard() {
  usePageTitle("Operational Board · Dispatch · MASCI");
  const nav = useNavigate();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [drawerAssignment, setDrawerAssignment] = useState(null);
  // Tenant override is read-only support for `dls-demo` dev work.
  // Set ?tenant=dls-demo on the URL to see seeded demo data.
  const tenantOverride = useMemo(() => {
    const q = new URLSearchParams(window.location.search);
    return q.get("tenant") || "";
  }, []);

  const refresh = useCallback(async ({ silent } = {}) => {
    if (!silent) setRefreshing(true);
    try {
      const r = await fetch(
        `${API}/api/dispatch/assignments/board?limit=300`,
        { headers: authHeaders(tenantOverride) },
      );
      if (r.status === 401) {
        nav("/dispatch-portal/login", { replace: true });
        return;
      }
      const j = await r.json().catch(() => ({}));
      setAssignments(Array.isArray(j.assignments) ? j.assignments : []);
      setErrorMsg("");
    } catch {
      setErrorMsg("Connection failed — retrying…");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [nav, tenantOverride]);

  useEffect(() => {
    refresh({ silent: true });
    const id = setInterval(() => refresh({ silent: true }), POLL_MS);
    return () => clearInterval(id);
  }, [refresh]);

  const handleDrawerChange = useCallback((updated) => {
    if (!updated) return;
    setAssignments((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
    setDrawerAssignment(updated);
  }, []);

  const handleDrawerRemoved = useCallback((id) => {
    setAssignments((prev) => prev.filter((a) => a.id !== id));
    setDrawerAssignment(null);
    toast.success("Removed from active board");
  }, []);

  return (
    <div className="min-h-screen blueprint-bg flex flex-col" data-testid="dispatch-board">
      <div className="caution-stripe" />
      <header className={`bg-slate-900 text-white border-b-4 ${DISPATCH_PAL.hubHeaderBar}`}>
        <div className="max-w-6xl mx-auto px-5 sm:px-8 py-4 flex items-center gap-3 flex-wrap">
          <Link
            to="/dispatch-portal"
            className={`inline-flex items-center text-white ${DISPATCH_PAL.hubLinkHover} text-xs sm:text-sm font-bold uppercase tracking-wide`}
            data-testid="board-back-link"
          >
            <ArrowLeft className="w-3.5 h-3.5 mr-1" />
            Dispatch Hub
          </Link>
          <h1 className="ml-auto text-sm sm:text-base font-bold uppercase tracking-widest opacity-80">
            Operational Board
          </h1>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-8 py-6 space-y-6 flex-1 w-full">
        {/* Title card matches DispatchHub convention */}
        <div className="bg-white border border-slate-200 border-l-4 border-l-orange-500 rounded-md p-5">
          <div className="flex items-start gap-3">
            <Activity className="w-6 h-6 mt-1 text-slate-700 shrink-0" />
            <div className="flex-1">
              <span className="font-mono text-xs uppercase tracking-[0.22em] text-orange-700 font-bold">
                Dispatch Lifecycle System
              </span>
              <h2 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
                Live operational flow
              </h2>
              <p className="text-sm text-slate-600 mt-2 max-w-2xl">
                Every active haul, one card. Tap a row to see history, issue
                a driver magic link, cancel, reassign, or revoke a session.
                Refreshes every {Math.round(POLL_MS / 1000)} seconds.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refresh()}
              disabled={refreshing}
              data-testid="board-refresh"
            >
              <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        <SummaryStrip assignments={assignments} />

        {tenantOverride ? (
          <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2" data-testid="board-tenant-override">
            Viewing tenant override: <strong>{tenantOverride}</strong> (dev mode)
          </div>
        ) : null}

        {errorMsg ? (
          <div className="text-sm rounded-md bg-rose-50 border border-rose-200 px-4 py-2 text-rose-800" data-testid="board-error">
            {errorMsg}
          </div>
        ) : null}

        {loading ? (
          <div className="text-center text-slate-500 py-10" data-testid="board-loading">
            Loading operational board…
          </div>
        ) : assignments.length === 0 ? (
          <div className="text-center text-slate-500 py-12 border-2 border-dashed border-slate-300 rounded-lg" data-testid="board-empty">
            <Send className="w-8 h-8 mx-auto mb-3 text-slate-400" />
            <p className="font-bold text-slate-700">No active hauls right now.</p>
            <p className="text-sm mt-1">
              Create an assignment via the iter392 API to populate the board.
            </p>
          </div>
        ) : (
          <div className="space-y-2" data-testid="board-rows">
            {assignments.map((a) => (
              <AssignmentRow key={a.id} a={a} onOpen={setDrawerAssignment} />
            ))}
          </div>
        )}
      </main>

      <AssignmentDrawer
        assignment={drawerAssignment}
        tenantOverride={tenantOverride}
        onClose={() => setDrawerAssignment(null)}
        onChanged={handleDrawerChange}
        onRemoved={handleDrawerRemoved}
      />
    </div>
  );
}
