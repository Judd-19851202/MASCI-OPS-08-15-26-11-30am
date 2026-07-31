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
import { useT } from "@/lib/i18n";
import {
  enqueueOffline, readOfflineQueue, clearOfflineQueue,
  replayOfflineQueue, registerOfflineAutoReplay,
  stagePhoto, flushStaged,
} from "@/lib/resiliency";
import { toast } from "sonner";

const API = process.env.REACT_APP_BACKEND_URL;

// ════════════════════════════════════════════════════════════════════
// iter421 · Phase 23.0 · Offline Continuity Primitive (walking skeleton)
// ────────────────────────────────────────────────────────────────────
// One job: if a lifecycle transition fails because the device is
// offline / weak signal, hold the update locally and replay when
// signal returns. Operational truth NEVER disappears — it just waits.
//
// iter435 · Phase 31 Pass B · Storage primitives extracted to
// `lib/resiliency/offlineQueue.js` so the SAME guarantees can be
// re-used by Shop Recovery, Dispatch assignment writes, etc. Behavior
// is preserved: formKey="driver-lifecycle" · max 3 · oldest→newest
// replay · 401 preserves queue · 2xx + 4xx clear entries.
// ════════════════════════════════════════════════════════════════════
const OFFLINE_FORM_KEY = "driver-lifecycle";
const OFFLINE_QUEUE_MAX = 3;
registerOfflineAutoReplay(OFFLINE_FORM_KEY);

function readDriverQueue() {
  return readOfflineQueue(OFFLINE_FORM_KEY);
}

function enqueueOfflineTransition(entry) {
  // Translate the iter421 action shape into the iter435 HTTP shape so
  // a single replayer drives every queued lifecycle write.
  const depth = enqueueOffline(OFFLINE_FORM_KEY, {
    method: "POST",
    url: `/api/dispatch/driver/assignments/${entry.assignment_id}/transition`,
    headers: driverHeaders(),
    body: { to_state: entry.to_state, ...(entry.extra || {}) },
    meta: {
      assignment_id: entry.assignment_id,
      to_state: entry.to_state,
      queued_at: entry.queued_at,
    },
  }, { max: OFFLINE_QUEUE_MAX });
  return depth;
}

// Canonical state keys stay constant (used by the backend lifecycle
// engine) — the human-readable label is resolved through `t()` at
// render time so EN / ES parity is automatic.
const STATE_LABEL_KEY = {
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

const WAIT_REASON_KEY = [
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
  const { t } = useT();
  const tone = STATE_TONE[state] || "bg-slate-700 text-slate-50";
  const labelKey = STATE_LABEL_KEY[state];
  return (
    <div
      data-testid="driver-current-state"
      className={`rounded-2xl px-6 py-8 text-center shadow-xl ${tone}`}
    >
      <div className="text-xs uppercase tracking-[0.25em] opacity-80">{t("Current state")}</div>
      <div className="mt-2 text-3xl font-bold tracking-tight">
        {labelKey ? t(labelKey) : (state || "—")}
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
  const { t } = useT();
  const [assignment, setAssignment] = useState(null);
  const [allowed, setAllowed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyState, setBusyState] = useState(null);
  const [waitSheetOpen, setWaitSheetOpen] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  // iter418 · Phase 20.1 · breakdown-proof optional prompt
  const [breakdownProofPrompt, setBreakdownProofPrompt] = useState(false);
  const [breakdownProofBusy, setBreakdownProofBusy] = useState(false);
  // iter421 · Phase 23.0 · offline pending count
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  // D-1.1 · acknowledgement state
  const [ackBusy, setAckBusy] = useState(false);

  const session = useMemo(() => getDriverSession(), []);

  const goSignedOut = useCallback(() => {
    clearDriverSession();
    navigate("/shift", { replace: true });
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
      setErrorMsg(t("Connection failed — retrying…"));
    } finally {
      setLoading(false);
    }
  }, [goSignedOut, t]);

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
        setErrorMsg(j.detail || t("Could not record that. Try again."));
      } else {
        setAssignment(j.assignment || null);
        setAllowed(Array.isArray(j.allowed_next_states) ? j.allowed_next_states : []);
        setErrorMsg("");
        // iter418 · Phase 20.1 · After a BREAKDOWN tap, offer optional photo proof
        if (toState === "BREAKDOWN") {
          setBreakdownProofPrompt(true);
        }
      }
    } catch {
      // iter421 · Phase 23.0 · Network failure → queue locally · stay calm.
      // The transition becomes a pending operational update, NOT an error.
      const count = enqueueOfflineTransition({
        assignment_id: assignment.id,
        to_state: toState,
        extra: extra || {},
        queued_at: new Date().toISOString(),
      });
      setPendingSyncCount(count);
      setErrorMsg("");
    } finally {
      setBusyState(null);
      setWaitSheetOpen(false);
    }
  }, [assignment, goSignedOut, t]);

  // D-1.1 · driver ACK · single POST · refreshes assignment on success
  // so the ACK card disappears and the next-state buttons take over.
  const acknowledge = useCallback(async (targetRev = null) => {
    if (!assignment || ackBusy) return;
    setAckBusy(true);
    try {
      const r = await fetch(
        `${API}/api/dispatch/driver/assignments/${assignment.id}/acknowledge`,
        {
          method: "POST",
          headers: driverHeaders(),
          body: JSON.stringify({
            method: "tap",
            device: navigator.userAgent || "",
            target_revision_seq: targetRev,
          }),
        },
      );
      if (r.status === 401) {
        goSignedOut();
        return;
      }
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        setErrorMsg(j.detail || t("Could not record acknowledgement. Try again."));
        return;
      }
      setAssignment(j.assignment || assignment);
      setAllowed(Array.isArray(j.allowed_next_states) ? j.allowed_next_states : allowed);
      setErrorMsg("");
    } catch {
      setErrorMsg(t("Connection failed — try again."));
    } finally {
      setAckBusy(false);
    }
  }, [assignment, ackBusy, allowed, goSignedOut, t]);

  // iter421 · Phase 23.0 · Replay queued transitions when signal returns.
  // Invisible · operational · no retry chrome. Runs on mount AND on the
  // browser `online` event. Mirrors operational truth back to backend
  // strictly in queued order (oldest→newest). iter435 · the actual
  // queue + replay primitives now live in `lib/resiliency/offlineQueue`
  // so Shop Recovery / Dispatch / etc. share the same guarantees.
  const replayDriverQueue = useCallback(async () => {
    const q = readDriverQueue();
    if (q.length === 0) {
      setPendingSyncCount(0);
      return;
    }
    if (!getDriverToken()) return;
    const { kept, replayedAny } = await replayOfflineQueue(
      OFFLINE_FORM_KEY, { max: OFFLINE_QUEUE_MAX },
    );
    setPendingSyncCount(kept);
    if (replayedAny) {
      // Pull fresh assignment truth after replay so UI mirrors backend
      refresh();
    }
  }, [refresh]);

  // Boot · seed counter from any pre-existing queue · attempt one replay.
  useEffect(() => {
    setPendingSyncCount(readDriverQueue().length);
    replayDriverQueue();
    const onOnline = () => replayDriverQueue();
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [replayDriverQueue]);

  if (loading) {
    return (
      <div
        data-testid="driver-shift-loading"
        className="min-h-screen flex items-center justify-center wp17-public-shell text-slate-100"
      >
        <p className="text-xl wp17-public-card px-6 py-4 bg-slate-950/88">{t("Loading your shift…")}</p>
      </div>
    );
  }

  if (!assignment) {
    return (
      <div
        data-testid="driver-no-assignment"
        className="min-h-screen flex flex-col items-center justify-center wp17-public-shell text-slate-100 px-6 text-center space-y-6"
      >
        <div className="wp17-public-card p-8 bg-slate-950/88">
        <p className="text-3xl font-bold tracking-tight">{t("No active haul right now")}</p>
        <p className="text-base text-slate-400 max-w-sm">
          {t("Dispatch will assign your next cycle. This screen will update on its own — keep it open in your phone.")}
        </p>
        <button
          type="button"
          data-testid="driver-sign-out-empty"
          onClick={goSignedOut}
          className="mt-6 inline-flex items-center justify-center min-h-[44px] px-4 text-sm uppercase tracking-widest text-slate-400 underline"
        >
          {t("Sign out")}
        </button>
        </div>
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
      className="min-h-screen wp17-public-shell text-slate-100 pb-24"
    >
      {/* Header */}
      <header className="wp17-public-header px-5 pt-6 pb-3 flex items-start justify-between text-white rounded-b-2xl">
        <div>
          <div className="text-xs uppercase tracking-[0.25em] text-amber-400 font-semibold">
            {t("Driver shift")}
          </div>
          <div className="mt-1 text-xl font-bold" data-testid="driver-truck-label">
            {t("Truck")} · {assignment.truck_id || "—"}
          </div>
          <div className="text-sm text-slate-400" data-testid="driver-name-label">
            {session?.driver?.driver_name || assignment.driver_name || "—"}
          </div>
        </div>
        <button
          type="button"
          data-testid="driver-sign-out"
          onClick={goSignedOut}
          className="inline-flex items-center justify-center min-h-[44px] px-3 -mr-2 text-xs uppercase tracking-widest text-slate-400 underline"
        >
          {t("Sign out")}
        </button>
      </header>

      {/* Current state card */}
      <section className="px-5 mt-2">
        <StateChip state={currentState} />
        {currentState === "WAITING" && assignment.current_wait_reason ? (
          <p className="mt-3 text-center text-rose-300 text-sm" data-testid="driver-wait-reason">
            {t("Reason")} · {(() => {
              const pair = WAIT_REASON_KEY.find(([k]) => k === assignment.current_wait_reason);
              return pair ? t(pair[1]) : assignment.current_wait_reason.replace(/_/g, " ");
            })()}
          </p>
        ) : null}
        {assignment.project_number ? (
          <p className="mt-2 text-center text-xs text-slate-500">
            {t("Job")} · {assignment.project_number}{assignment.material ? ` · ${assignment.material}` : ""}
          </p>
        ) : null}
        {/* iter421 · Phase 23.0 · offline pending sync indicator (invisible language) */}
        {pendingSyncCount > 0 && (
          <p
            className="mt-2 text-center text-xs text-amber-300"
            data-testid="driver-pending-sync"
          >
            {pendingSyncCount === 1
              ? t("1 update waiting to sync")
              : t("{n} updates waiting to sync").replace("{n}", String(pendingSyncCount))}
          </p>
        )}
      </section>

      {/* D-1.1 · ACK card · prominent · pre-transition · shown only
          when (a) initial ACK is missing OR (b) a revision is pending
          and the driver has not re-acknowledged. */}
      {assignment && (!assignment.acked_at || assignment.revision_pending) && (
        <section
          data-testid="driver-ack-card"
          className={
            "mx-5 mt-5 rounded-2xl border p-5 "
            + (assignment.revision_pending
              ? "border-amber-500 bg-amber-950/40"
              : "border-emerald-500 bg-emerald-950/40")
          }
        >
          <div
            className="text-xs uppercase tracking-wide font-bold"
            style={{ color: assignment.revision_pending ? "#fbbf24" : "#34d399" }}
          >
            {assignment.revision_pending
              ? t("Revision pending · please re-acknowledge")
              : t("Acknowledge this assignment")}
          </div>
          <p className="text-sm text-slate-100 mt-1.5 leading-snug">
            {assignment.revision_pending
              ? t("Dispatch has revised your assignment. Tap ACKNOWLEDGE to confirm you've seen the changes before you move.")
              : t("Tap ACKNOWLEDGE so dispatch knows you've received this assignment. Then start your run.")}
          </p>
          {/* D-1.5 · show the revision delta when revision_pending */}
          {assignment.revision_pending && Array.isArray(assignment.revision_history)
            && assignment.revision_history.length > 0 && (() => {
              const last = assignment.revision_history[assignment.revision_history.length - 1];
              const after = last?.after || {};
              const changedKeys = Object.keys(after);
              if (changedKeys.length === 0) return null;
              return (
                <div
                  data-testid="driver-revision-delta"
                  className="mt-3 bg-slate-950/60 border border-amber-700/60 rounded-lg p-3 space-y-1.5"
                >
                  <div className="text-[10px] uppercase tracking-wider text-amber-300 font-bold">
                    {t("What changed")}
                  </div>
                  {changedKeys.map((k) => (
                    <div key={k} className="text-sm text-slate-100">
                      <span className="text-amber-300 font-semibold mr-1">{k.replace(/_/g, " ")}:</span>
                      <span className="font-mono">{String(after[k] ?? "")}</span>
                    </div>
                  ))}
                  {last?.reason ? (
                    <div className="text-xs text-slate-400 italic mt-2">
                      {t("Reason")} · {last.reason}
                    </div>
                  ) : null}
                </div>
              );
            })()}
          <button
            type="button"
            data-testid="driver-ack-button"
            disabled={ackBusy}
            onClick={() => acknowledge(
              assignment.revision_pending
                ? (assignment.revision_seq || 0)
                : null,
            )}
            className={
              "mt-4 w-full min-h-[64px] rounded-xl text-base font-bold uppercase tracking-wider "
              + "transition active:scale-[0.99] disabled:opacity-60 "
              + (assignment.revision_pending
                ? "bg-amber-500 text-amber-950 hover:bg-amber-400"
                : "bg-emerald-500 text-emerald-950 hover:bg-emerald-400")
            }
          >
            {ackBusy
              ? t("Recording…")
              : assignment.revision_pending
                ? t("ACKNOWLEDGE REVISION")
                : t("ACKNOWLEDGE")}
          </button>
        </section>
      )}

      {/* iter418 · Phase 20.1 · Optional breakdown-proof prompt */}
      {breakdownProofPrompt && (
        <section
          className="mx-5 mt-4 rounded-2xl border border-rose-700 bg-rose-950/60 p-4"
          data-testid="driver-breakdown-proof-prompt"
        >
          <div className="text-xs uppercase tracking-wide text-rose-300 font-bold">
            {t("Operational proof · optional")}
          </div>
          <p className="text-sm text-slate-100 mt-1">
            {t("Add a breakdown photo? Helps Shop see what's wrong.")}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <label className="inline-flex">
              <input
                type="file"
                accept="image/*"
                capture="environment"
                disabled={breakdownProofBusy}
                onChange={async (e) => {
                  const f = e.target.files?.[0];
                  e.target.value = "";
                  if (!f) return;
                  if (f.size > 5 * 1024 * 1024) {
                    setErrorMsg(t("File too large (5 MB max)."));
                    return;
                  }
                  setBreakdownProofBusy(true);
                  try {
                    const form = new FormData();
                    form.append("host_id", assignment.id);
                    form.append("file", f);
                    let r;
                    try {
                      r = await fetch(
                        `${API}/api/dispatch/driver/breakdown-proof/upload`,
                        { method: "POST", headers: driverHeaders({ omitContentType: true }), body: form },
                      );
                    } catch (netErr) {
                      // iter438 · Phase 31 · Pass C · stage the photo
                      // so it auto-retries on `online` / `focus`. The
                      // driver gets calm confirmation instead of a
                      // red error · breakdown photo never disappears.
                      try {
                        await stagePhoto({
                          file: f,
                          hostKind: "breakdown_proof",
                          hostId: assignment.id,
                          attachmentType: "breakdown_proof",
                          note: "",
                        });
                        toast.message(t("Photo saved on this device · will send when online."));
                        setBreakdownProofPrompt(false);
                      } catch {
                        setErrorMsg(t("Connection failed — try again."));
                      }
                      return;
                    }
                    if (!r.ok) {
                      if (r.status >= 500) {
                        // 5xx — stage for later retry · driver moves on.
                        try {
                          await stagePhoto({
                            file: f,
                            hostKind: "breakdown_proof",
                            hostId: assignment.id,
                            attachmentType: "breakdown_proof",
                            note: "",
                          });
                          toast.message(t("Photo saved on this device · will send when online."));
                          setBreakdownProofPrompt(false);
                        } catch {
                          const j = await r.json().catch(() => ({}));
                          setErrorMsg(j.detail || t("Upload failed."));
                        }
                      } else {
                        const j = await r.json().catch(() => ({}));
                        setErrorMsg(j.detail || t("Upload failed."));
                      }
                    } else {
                      setBreakdownProofPrompt(false);
                      // Opportunistic flush of any prior staged photos.
                      flushStaged().catch(() => { /* silent */ });
                    }
                  } catch {
                    setErrorMsg(t("Connection failed — try again."));
                  } finally {
                    setBreakdownProofBusy(false);
                  }
                }}
                data-testid="driver-breakdown-proof-input"
                className="hidden"
              />
              <span
                className={`inline-flex items-center px-4 h-12 rounded-md text-sm font-bold cursor-pointer
                  ${breakdownProofBusy ? "bg-slate-700 text-slate-400" : "bg-amber-400 text-slate-950"}`}
              >
                {breakdownProofBusy ? t("Uploading…") : t("Take Photo")}
              </span>
            </label>
            <button
              type="button"
              data-testid="driver-breakdown-proof-skip"
              onClick={() => setBreakdownProofPrompt(false)}
              className="inline-flex items-center px-4 h-12 rounded-md text-sm font-bold text-slate-300 underline"
            >
              {t("Skip")}
            </button>
          </div>
        </section>
      )}

      {/* Primary transitions */}
      <section className="px-5 mt-6 space-y-3" data-testid="driver-transition-grid">
        {orderedNext.length === 0 ? (
          <p className="text-center text-sm text-slate-400">
            {t("No next step — dispatch will pick this up.")}
          </p>
        ) : (
          orderedNext.map((s) => (
            <TapButton
              key={s}
              testId={`driver-next-${s}`}
              label={STATE_LABEL_KEY[s] ? t(STATE_LABEL_KEY[s]) : s}
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
            label={t("Waiting…")}
            tone="rose"
            disabled={busyState !== null}
            onClick={() => setWaitSheetOpen(true)}
          />
        ) : null}
        {showBreakdownButton ? (
          <TapButton
            testId="driver-breakdown"
            label={t("Breakdown")}
            tone="rose"
            disabled={busyState !== null}
            onClick={() => transition("BREAKDOWN")}
          />
        ) : null}
        {showHoldButton ? (
          <TapButton
            testId="driver-hold"
            label={t("Hold")}
            tone="slate"
            disabled={busyState !== null}
            onClick={() => transition("HOLD")}
          />
        ) : null}
        {showOffShift ? (
          <TapButton
            testId="driver-off-shift"
            label={t("End shift")}
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
          <div className="w-full sm:max-w-md bg-slate-900 rounded-t-3xl sm:rounded-3xl p-6 space-y-3 border-t-4 border-rose-500"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <p className="text-lg font-bold tracking-tight">{t("What are you waiting on?")}</p>
              <button
                type="button"
                data-testid="driver-wait-sheet-close"
                onClick={() => setWaitSheetOpen(false)}
                className="inline-flex items-center justify-center min-h-[44px] px-3 text-slate-400 text-sm uppercase tracking-widest"
              >
                {t("Cancel")}
              </button>
            </div>
            <div className="space-y-2">
              {WAIT_REASON_KEY.map(([reason, short]) => (
                <TapButton
                  key={reason}
                  testId={`driver-wait-reason-${reason}`}
                  label={t(short)}
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
