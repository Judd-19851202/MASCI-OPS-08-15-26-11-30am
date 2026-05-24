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
  Truck, ArrowLeft, AlertTriangle, Wrench, Clock, Activity, RefreshCw, Send, Download, Bell,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { LifecycleGuide } from "@/components/LifecycleGuide";
import { paletteFor } from "@/lib/portalPalette";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getAdminToken } from "@/lib/adminAuth";
import { usePageTitle } from "@/lib/usePageTitle";
import { toast } from "sonner";
import AssignmentDrawer from "@/components/dispatch/AssignmentDrawer";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;
const DISPATCH_PAL = paletteFor("dispatch");
const POLL_MS = 5000;
const STUCK_THRESHOLD_MIN = 30;

const STATE_LABEL_KEY = {
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
  const { t } = useT();
  const tone = STATE_TONE[state] || STATE_TONE.ASSIGNED;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wide border ${tone}`}
      data-testid={`board-state-${state}`}
    >
      {STATE_LABEL_KEY[state] ? t(STATE_LABEL_KEY[state]) : (state || "—")}
    </span>
  );
}

function FindingsBanner({ findings, counts, onOpen }) {
  const { t } = useT();
  // Severity prioritization is already done server-side; we just trim to
  // 6 chips so the banner stays calm.
  const visible = findings.slice(0, 6);
  const severityTone = (sev) =>
    sev === "critical" ? "bg-rose-100 text-rose-900 border-rose-300" :
    sev === "high"     ? "bg-amber-100 text-amber-900 border-amber-300" :
                         "bg-slate-100 text-slate-800 border-slate-300";
  return (
    <div
      data-testid="board-findings-banner"
      className="bg-white border border-amber-300 border-l-4 border-l-amber-500 rounded-md p-4"
    >
      <div className="flex items-start gap-3 flex-wrap">
        <Bell className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
        <div className="flex-1 min-w-[200px]">
          <div className="text-xs font-mono uppercase tracking-[0.22em] text-amber-700 font-bold">
            {t("Operational signals")}
          </div>
          <div className="text-sm text-slate-700 mt-0.5">
            {counts.total
              ? `${counts.total} ${counts.total === 1 ? t("finding requires operational attention.") : t("findings require operational attention.")}`
              : t("No active findings.")}
            {" "}
            {counts.BREAKDOWN_ACTIVE
              ? <span className="font-bold text-rose-800">{counts.BREAKDOWN_ACTIVE} {counts.BREAKDOWN_ACTIVE === 1 ? t("breakdown") : t("breakdowns")} · </span>
              : null}
            {counts.ASSIGNMENT_STUCK
              ? <span className="font-bold text-amber-800">{counts.ASSIGNMENT_STUCK} {t("stuck")} · </span>
              : null}
            {counts.WAIT_THRESHOLD_EXCEEDED
              ? <span className="font-bold text-rose-700">{counts.WAIT_THRESHOLD_EXCEEDED} {counts.WAIT_THRESHOLD_EXCEEDED === 1 ? t("long wait") : t("long waits")} · </span>
              : null}
            {counts.NON_STANDARD_TRANSITION_PATTERN
              ? <span className="font-bold text-slate-700">{counts.NON_STANDARD_TRANSITION_PATTERN} {counts.NON_STANDARD_TRANSITION_PATTERN === 1 ? t("pattern") : t("patterns")}</span>
              : null}
          </div>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {visible.map((f, idx) => (
          <button
            key={`${f.kind}-${f.assignment_id || f.truck_id}-${idx}`}
            type="button"
            data-testid={`finding-chip-${f.kind}-${idx}`}
            onClick={() => onOpen(f)}
            className={`text-left text-xs font-medium px-2.5 py-1.5 rounded border ${severityTone(f.severity)} hover:shadow-sm transition-shadow max-w-[260px] truncate`}
            title={f.headline}
          >
            {f.headline}
          </button>
        ))}
      </div>
    </div>
  );
}

function ExportStrip({ onDownload, tenantOverride }) {
  const { t } = useT();
  const stamp = new Date().toISOString().replace(/[-:]/g, "").slice(0, 13);
  const ts = tenantOverride ? `_${tenantOverride}` : "";
  return (
    <div
      data-testid="board-export-strip"
      className="flex flex-wrap gap-2 items-center bg-slate-50 border border-slate-200 rounded-md px-3 py-2"
    >
      <span className="text-xs uppercase tracking-widest text-slate-500 font-bold flex items-center gap-1">
        <Download className="w-3.5 h-3.5" />
        {t("Operational exports (CSV)")}
      </span>
      <Button
        size="sm" variant="outline"
        onClick={() => onDownload("/api/dispatch/exports/assignments.csv", `dispatch_assignments${ts}_${stamp}.csv`)}
        data-testid="export-assignments"
      >
        {t("Assignments")}
      </Button>
      <Button
        size="sm" variant="outline"
        onClick={() => onDownload("/api/dispatch/exports/state-events.csv?limit=5000", `dispatch_state_events${ts}_${stamp}.csv`)}
        data-testid="export-state-events"
      >
        {t("State events")}
      </Button>
      <Button
        size="sm" variant="outline"
        onClick={() => onDownload("/api/dispatch/exports/haul-cycles.csv", `dispatch_haul_cycles${ts}_${stamp}.csv`)}
        data-testid="export-haul-cycles"
      >
        {t("Haul cycles")}
      </Button>
    </div>
  );
}


function SummaryStrip({ assignments }) {
  const { t } = useT();
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
        t("Active hauls"), counts.active,
        <Activity className="w-5 h-5 text-slate-700" />,
        "bg-white border-slate-200",
        "summary-active",
      )}
      {tile(
        t("Waiting"), counts.waiting,
        <Clock className="w-5 h-5 text-rose-700" />,
        "bg-rose-50 border-rose-200",
        "summary-waiting",
      )}
      {tile(
        t("Breakdown"), counts.breakdown,
        <Wrench className="w-5 h-5 text-rose-800" />,
        "bg-rose-100 border-rose-300",
        "summary-breakdown",
      )}
      {tile(
        `${t("Stuck")} > ${STUCK_THRESHOLD_MIN}m`, counts.stuck,
        <AlertTriangle className="w-5 h-5 text-amber-700" />,
        "bg-amber-50 border-amber-200",
        "summary-stuck",
      )}
    </div>
  );
}

function AssignmentRow({ a, onOpen }) {
  const { t } = useT();
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
          {a.project_name || a.project_number || t("Unassigned project")}
        </div>
        <div className="text-slate-500 truncate">
          {[a.material, a.source_location, a.destination].filter(Boolean).join(" → ")}
        </div>
      </div>

      <div className="text-right shrink-0">
        <div className={`text-xs font-bold ${isStuck ? "text-amber-700" : "text-slate-600"}`}>
          {m === null ? "—" : `${m}${t("m in state")}`}
        </div>
        <div className="text-[11px] text-slate-400 uppercase tracking-wider">
          {t("tap for actions")}
        </div>
      </div>
    </button>
  );
}

export default function DispatchBoard() {
  usePageTitle("Operational Board · Dispatch · MASCI");
  const nav = useNavigate();
  const { t } = useT();
  const [assignments, setAssignments] = useState([]);
  const [findings, setFindings] = useState([]);
  const [findingCounts, setFindingCounts] = useState({});
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
      const [r1, r2] = await Promise.all([
        fetch(
          `${API}/api/dispatch/assignments/board?limit=300`,
          { headers: authHeaders(tenantOverride) },
        ),
        fetch(
          `${API}/api/dispatch/governance/findings`,
          { headers: authHeaders(tenantOverride) },
        ),
      ]);
      if (r1.status === 401) {
        nav("/dispatch-portal/login", { replace: true });
        return;
      }
      const j1 = await r1.json().catch(() => ({}));
      setAssignments(Array.isArray(j1.assignments) ? j1.assignments : []);
      if (r2.ok) {
        const j2 = await r2.json().catch(() => ({}));
        setFindings(Array.isArray(j2.findings) ? j2.findings : []);
        setFindingCounts(j2.counts || {});
      } else {
        // Findings is best-effort — never break the board if it fails.
        setFindings([]);
        setFindingCounts({});
      }
      setErrorMsg("");
    } catch {
      setErrorMsg(t("Connection failed — retrying…"));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [nav, tenantOverride, t]);

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
    toast.success(t("Removed from active board"));
  }, [t]);

  /**
   * CSV downloads — fetch with auth headers so we can pass
   * X-Tenant-Id, then trigger a client-side download. Native <a href>
   * cannot attach headers.
   */
  const downloadCsv = useCallback(async (path, suggestedName) => {
    try {
      const r = await fetch(`${API}${path}`, { headers: authHeaders(tenantOverride) });
      if (!r.ok) {
        toast.error(`${t("Export failed")} (${r.status})`);
        return;
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = suggestedName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success(t("Export downloaded"));
    } catch {
      toast.error(t("Export failed — check connection."));
    }
  }, [tenantOverride, t]);

  /** Map a finding to the assignment row + open the drawer. */
  const openFinding = useCallback((finding) => {
    if (!finding?.assignment_id) {
      toast.info(t("Truck-level finding — open the row directly to act."));
      return;
    }
    const target = assignments.find((a) => a.id === finding.assignment_id);
    if (target) {
      setDrawerAssignment(target);
    } else {
      toast.info(t("Assignment not on active board — likely already cleared."));
    }
  }, [assignments, t]);

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
            {t("Dispatch Hub")}
          </Link>
          <h1 className="ml-auto text-sm sm:text-base font-bold uppercase tracking-widest opacity-80">
            {t("Operational Board")}
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
                {t("Dispatch Lifecycle System")}
              </span>
              <h2 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-900 mt-1">
                {t("Live operational flow")}
              </h2>
              <p className="text-sm text-slate-600 mt-2 max-w-2xl">
                {t("Every active haul, one card. Tap a row to see history, issue a driver magic link, cancel, reassign, or revoke a session. Refreshes every")} {Math.round(POLL_MS / 1000)} {t("seconds.")}
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
              {t("Refresh")}
            </Button>
          </div>
        </div>

        <SummaryStrip assignments={assignments} />

        {/* iter396 · LifecycleGuide — only here where confusion risk is real */}
        <LifecycleGuide
          id="dispatch-operational-board"
          icon={Activity}
          title={t("What this board is telling you")}
          summary={t("Calm operational truth · forgiving transitions · governance signals")}
          accent="orange"
          sections={[
            {
              label: t("Lifecycle"),
              body: t("Every truck moves through 13 canonical states. Non-standard transitions are accepted but tagged so operations are never blocked. See the glossary for full definitions."),
            },
            {
              label: t("Findings"),
              body: t("Four signals only — BREAKDOWN_ACTIVE (critical), ASSIGNMENT_STUCK (≥30 min in non-terminal state), WAIT_THRESHOLD_EXCEEDED (≥20 min in WAITING), NON_STANDARD_TRANSITION_PATTERN (≥3 non-standard transitions in 2h per truck). Nothing else fires."),
            },
            {
              label: t("Roles"),
              body: t("Dispatch and Admin act here. Drivers act on the magic-link mobile screen. PM and Shop see project- and breakdown-scoped signals on their own hubs. Safety, FL, and HR remain operationally quiet on DLS by design — restraint until live operations tell us where signal-surfacing actually helps."),
            },
            {
              label: t("Restraint"),
              body: t("Read-only · refreshes every 5 seconds · no chat, no maps, no analytics. The lifecycle engine is the single source of operational truth — every action here delegates to it so nothing gets out of sync."),
            },
          ]}
        />

        {/* iter395 · governance findings banner — calm, glanceable */}
        {findings.length > 0 ? (
          <FindingsBanner
            findings={findings}
            counts={findingCounts}
            onOpen={openFinding}
          />
        ) : null}

        {/* iter395 · CSV operational intelligence exports */}
        <ExportStrip onDownload={downloadCsv} tenantOverride={tenantOverride} />

        {tenantOverride ? (
          <div className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2" data-testid="board-tenant-override">
            {t("Viewing tenant override:")} <strong>{tenantOverride}</strong> ({t("dev mode")})
          </div>
        ) : null}

        {errorMsg ? (
          <div className="text-sm rounded-md bg-rose-50 border border-rose-200 px-4 py-2 text-rose-800" data-testid="board-error">
            {errorMsg}
          </div>
        ) : null}

        {loading ? (
          <div className="text-center text-slate-500 py-10" data-testid="board-loading">
            {t("Loading operational board…")}
          </div>
        ) : assignments.length === 0 ? (
          <div className="text-center text-slate-500 py-12 border-2 border-dashed border-slate-300 rounded-lg" data-testid="board-empty">
            <Send className="w-8 h-8 mx-auto mb-3 text-slate-400" />
            <p className="font-bold text-slate-700">{t("No active hauls right now.")}</p>
            <p className="text-sm mt-1">
              {t("Trucks will appear here the moment dispatch creates an assignment.")}
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
