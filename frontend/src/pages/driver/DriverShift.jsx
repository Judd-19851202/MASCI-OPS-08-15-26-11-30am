/**
 * DriverShift.jsx · iter393 · DLS Driver Tap-and-Work Surface.
 *
 * Route: /driver
 *
 * The minimum-friction shift screen. One assignment in focus. Big tap
 * targets. 0 required typing.
 *
 * Layout (top → bottom):
 *   1. Truck + driver header (slim · tap target = SIGN OUT)
 *   2. Current state card (giant, high contrast)
 *   3. Next-state transition grid (preferred next states from the
 *      iter392 lifecycle engine, 80 px buttons)
 *   4. Wait-state sheet (canonical reasons, one-tap)
 *
 * Network: relies on `/api/dispatch/driver/my-assignment` + transition
 * endpoints. Polls every 6 s while the screen is foregrounded so a
 * dispatcher cancel/reassign reflects without driver action.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  clearDriverSession,
  driverHeaders,
  getDriverSession,
  getDriverToken,
} from "@/lib/driverAuth";

const API = process.env.REACT_APP_BACKEND_URL;

const STATE_LABEL = {
  ASSIGNED: "Assigned · ready to roll",
  ENROUTE_TO_LOAD: "En route to load",
  AT_LOAD_SITE: "At load site",
  LOADING: "Loading",
  LOADED: "Loaded · secure your ticket",
  ENROUTE_TO_JOB: "En route to job",
  ARRIVED_JOB: "Arrived at job",
  DUMPING: "Dumping",
  COMPLETE: "Complete — start next cycle when dispatched",
  WAITING: "Waiting",
  HOLD: "On hold",
  BREAKDOWN: "Breakdown",
  OFF_SHIFT: "Off shift",
};

const STATE_TONE = {
  ASSIGNED: "bg-slate-700 text-slate-50",
  ENROUTE_TO_LOAD: "bg-sky-700 text-sky-50",
  AT_LOAD_SITE: "bg-sky-800 text-sky-50",
  LOADING: "bg-indigo-700 text-indigo-50",
  LOADED: "bg-indigo-800 text-indigo-50",
  ENROUTE_TO_JOB: "bg-emerald-700 text-emerald-50",
  ARRIVED_JOB: "bg-emerald-800 text-emerald-50",
  DUMPING: "bg-amber-700 text-amber-50",
  COMPLETE: "bg-emerald-900 text-emerald-50",
  WAITING: "bg-rose-700 text-rose-50",
  HOLD: "bg-rose-800 text-rose-50",
  BREAKDOWN: "bg-rose-900 text-rose-50",
  OFF_SHIFT: "bg-slate-800 text-slate-200",
};

const WAIT_REASONS = [
  ["WAITING_ON_PLANT", "Plant"],
  ["WAITING_ON_LOADER", "Loader"],
  ["WAITING_ON_DUMP", "Dump"],
  ["WAITING_ON_PAVER", "Paver"],
  ["WAITING_ON_TRAFFIC", "Traffic"],
  ["WAITING_ON_LANE_CLOSURE", "Lane closure"],
  ["WAITING_ON_ASSIGNMENT", "Next dispatch"],
  ["STAGING", "Staging"],
];

const PRIMARY_NEXT = [
  "ENROUTE_TO_LOAD", "AT_LOAD_SITE", "LOADING", "LOADED",
  "ENROUTE_TO_JOB", "ARRIVED_JOB", "DUMPING", "COMPLETE",
];

function StateChip({ state }) {
  const tone = STATE_TONE[state] || "bg-slate-700 text-slate-50";
  return (
    <div
      data-testid="driver-current-state"
      className={`rounded-2xl px-6 py-8 text-center shadow-xl ${tone}`}
    >
      <div className="text-xs uppercase tracking-[0.25em] opacity-80">Current state</div>
      <div className="mt-2 text-3xl font-bold tracking-tight">
        {STATE_LABEL[state] || state || "—"}
      </div>
    </div>
  );
}

function TapButton({ label, onClick, tone = "amber", testId, disabled = false }) {
  const palette = {
    amber: "bg-amber-400 text-slate-950 hover:bg-amber-300 active:bg-amber-500",
    rose: "bg-rose-500 text-white hover:bg-rose-400 active:bg-rose-600",
    slate: "bg-slate-700 text-slate-50 hover:bg-slate-600 active:bg-slate-800",
    emerald: "bg-emerald-500 text-white hover:bg-emerald-400 active:bg-emerald-600",
  }[tone];
  return (
    <button
      type="button"
      data-testid={testId}
      disabled={disabled}
      onClick={onClick}
      className={`min-h-[80px] w-full rounded-2xl text-xl font-bold tracking-tight shadow-lg disabled:opacity-40 disabled:cursor-not-allowed ${palette}`}
    >
      {label}
    </button>
  );
}

export default function DriverShift() {
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [allowed, setAllowed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyState, setBusyState] = useState(null);
  const [waitSheetOpen, setWaitSheetOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const session = useMemo(() => getDriverSession(), []);

  const goSignedOut = useCallback(() => {
    clearDriverSession();
    navigate("/", { replace: true });
  }, [navigate]);

  const refresh = useCallback(async () => {
    if (!getDriverToken()) {
      goSignedOut();
      return;
    }
    try {
      const r = await fetch(`${API}/api/dispatch/driver/my-assignment`, {
        headers: driverHeaders(),
      });
      if (r.status === 401) {
        goSignedOut();
        return;
      }
      const j = await r.json().catch(() => ({}));
      setAssignment(j.assignment || null);
      setAllowed(Array.isArray(j.allowed_next_states) ? j.allowed_next_states : []);
      setErrorMsg("");
    } catch {
      setErrorMsg("Connection failed — retrying…");
    } finally {
      setLoading(false);
    }
  }, [goSignedOut]);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 6000);
    return () => clearInterval(id);
  }, [refresh]);

  const transition = useCallback(async (toState, extra = {}) => {
    if (!assignment) return;
    setBusyState(toState);
    try {
      const r = await fetch(
        `${API}/api/dispatch/driver/assignments/${assignment.id}/transition`,
        {
          method: "POST",
          headers: driverHeaders(),
          body: JSON.stringify({ to_state: toState, ...extra }),
        },
      );
      if (r.status === 401) {
        goSignedOut();
        return;
      }
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        setErrorMsg(j.detail || "Could not record that. Try again.");
      } else {
        setAssignment(j.assignment || null);
        setAllowed(Array.isArray(j.allowed_next_states) ? j.allowed_next_states : []);
        setErrorMsg("");
      }
    } catch {
      setErrorMsg("Connection failed — try again.");
    } finally {
      setBusyState(null);
      setWaitSheetOpen(false);
    }
  }, [assignment, goSignedOut]);

  if (loading) {
    return (
      <div
        data-testid="driver-shift-loading"
        className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-100"
      >
        <p className="text-xl">Loading your shift…</p>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div
        data-testid="driver-no-assignment"
        className="min-h-screen flex flex-col items-center justify-center bg-slate-950 text-slate-100 px-6 text-center space-y-6"
      >
        <p className="text-3xl font-bold tracking-tight">No active haul right now</p>
        <p className="text-base text-slate-400 max-w-sm">
          Dispatch will assign your next cycle. This screen will update on its own —
          keep it open in your phone.
        </p>
        <button
          type="button"
          data-testid="driver-sign-out-empty"
          onClick={goSignedOut}
          className="mt-6 text-sm uppercase tracking-widest text-slate-400 underline"
        >
          Sign out
        </button>
      </div>
    );
  }

  const currentState = assignment.current_state || "";
  const orderedNext = PRIMARY_NEXT.filter((s) => allowed.includes(s));
  const showWaitButton = allowed.includes("WAITING");
  const showHoldButton = allowed.includes("HOLD");
  const showBreakdownButton = allowed.includes("BREAKDOWN");
  const showOffShift = allowed.includes("OFF_SHIFT");

  return (
    <div
      data-testid="driver-shift"
      className="min-h-screen bg-slate-950 text-slate-100 pb-24"
    >
      {/* Header */}
      <header className="px-5 pt-6 pb-3 flex items-start justify-between">
        <div>
          <div className="text-xs uppercase tracking-[0.25em] text-amber-400 font-semibold">
            Driver shift
          </div>
          <div className="mt-1 text-xl font-bold" data-testid="driver-truck-label">
            Truck · {assignment.truck_id || "—"}
          </div>
          <div className="text-sm text-slate-400" data-testid="driver-name-label">
            {session?.driver?.driver_name || assignment.driver_name || "—"}
          </div>
        </div>
        <button
          type="button"
          data-testid="driver-sign-out"
          onClick={goSignedOut}
          className="text-xs uppercase tracking-widest text-slate-400 underline"
        >
          Sign out
        </button>
      </header>

      {/* Current state card */}
      <section className="px-5 mt-2">
        <StateChip state={currentState} />
        {currentState === "WAITING" && assignment.current_wait_reason ? (
          <p className="mt-3 text-center text-rose-300 text-sm" data-testid="driver-wait-reason">
            Reason · {assignment.current_wait_reason.replace(/_/g, " ")}
          </p>
        ) : null}
        {assignment.project_number ? (
          <p className="mt-2 text-center text-xs text-slate-500">
            Job · {assignment.project_number}{assignment.material ? ` · ${assignment.material}` : ""}
          </p>
        ) : null}
      </section>

      {/* Primary transitions */}
      <section className="px-5 mt-6 space-y-3" data-testid="driver-transition-grid">
        {orderedNext.length === 0 ? (
          <p className="text-center text-sm text-slate-400">
            No next step — dispatch will pick this up.
          </p>
        ) : (
          orderedNext.map((s) => (
            <TapButton
              key={s}
              testId={`driver-next-${s}`}
              label={STATE_LABEL[s] || s}
              tone="amber"
              disabled={busyState !== null}
              onClick={() => transition(s)}
            />
          ))
        )}
      </section>

      {/* Pause states */}
      <section className="px-5 mt-8 space-y-3">
        {showWaitButton ? (
          <TapButton
            testId="driver-open-wait-sheet"
            label="Waiting…"
            tone="rose"
            disabled={busyState !== null}
            onClick={() => setWaitSheetOpen(true)}
          />
        ) : null}
        {showBreakdownButton ? (
          <TapButton
            testId="driver-breakdown"
            label="Breakdown"
            tone="rose"
            disabled={busyState !== null}
            onClick={() => transition("BREAKDOWN")}
          />
        ) : null}
        {showHoldButton ? (
          <TapButton
            testId="driver-hold"
            label="Hold"
            tone="slate"
            disabled={busyState !== null}
            onClick={() => transition("HOLD")}
          />
        ) : null}
        {showOffShift ? (
          <TapButton
            testId="driver-off-shift"
            label="End shift"
            tone="slate"
            disabled={busyState !== null}
            onClick={() => transition("OFF_SHIFT")}
          />
        ) : null}
      </section>

      {/* Errors */}
      {errorMsg ? (
        <p
          data-testid="driver-error"
          className="mt-6 mx-5 text-sm rounded-xl bg-rose-900/40 border border-rose-700 px-4 py-3 text-rose-200"
        >
          {errorMsg}
        </p>
      ) : null}

      {/* Wait sheet */}
      {waitSheetOpen ? (
        <div
          data-testid="driver-wait-sheet"
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-end sm:items-center justify-center z-50"
          onClick={() => setWaitSheetOpen(false)}
        >
          <div
            className="w-full sm:max-w-md bg-slate-900 rounded-t-3xl sm:rounded-3xl p-6 space-y-3 border-t-4 border-rose-500"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <p className="text-lg font-bold tracking-tight">What are you waiting on?</p>
              <button
                type="button"
                data-testid="driver-wait-sheet-close"
                onClick={() => setWaitSheetOpen(false)}
                className="text-slate-400 text-sm uppercase tracking-widest"
              >
                Cancel
              </button>
            </div>
            <div className="space-y-2">
              {WAIT_REASONS.map(([reason, short]) => (
                <TapButton
                  key={reason}
                  testId={`driver-wait-reason-${reason}`}
                  label={short}
                  tone="rose"
                  disabled={busyState !== null}
                  onClick={() => transition("WAITING", { wait_reason: reason })}
                />
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
