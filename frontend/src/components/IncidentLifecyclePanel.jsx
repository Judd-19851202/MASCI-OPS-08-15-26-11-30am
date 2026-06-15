/**
 * OMEGA · Phase 1A · iter451 · OC-001 Incident Lifecycle Panel
 *
 * Renders:
 *   - Current state pill (OPEN / UNDER_INVESTIGATION / CORRECTIVE_ACTION_REQUIRED / PENDING_CLOSURE / CLOSED)
 *   - Role-gated action buttons (driven by GET /api/incidents/{id}/lifecycle)
 *   - Closure attestation modal (3 checkboxes + optional OSHA ack)
 *   - Reopen modal (mandatory reason)
 *   - Transition history drawer (GET /api/incidents/{id}/state-events)
 *
 * Scoped to ViewIncident.jsx for iter451. Subsequent iterations
 * generalize the shell into a shared <LifecyclePanel/> component.
 */
import React, { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Textarea } from "@/components/ui/textarea";
import {
  ShieldAlert,
  Search,
  Wrench,
  ClipboardCheck,
  Lock,
  RotateCcw,
  History,
  Loader2,
} from "lucide-react";
import { UndoLastTransitionButton } from "@/components/UndoLastTransitionButton";

const STATE_LABEL = {
  OPEN: "Open",
  UNDER_INVESTIGATION: "Under Investigation",
  CORRECTIVE_ACTION_REQUIRED: "Corrective Action Required",
  PENDING_CLOSURE: "Pending Closure",
  CLOSED: "Closed",
};

const STATE_PILL = {
  OPEN: "bg-amber-100 text-amber-900 border-amber-400",
  UNDER_INVESTIGATION: "bg-blue-100 text-blue-900 border-blue-400",
  CORRECTIVE_ACTION_REQUIRED: "bg-orange-100 text-orange-900 border-orange-400",
  PENDING_CLOSURE: "bg-purple-100 text-purple-900 border-purple-400",
  CLOSED: "bg-emerald-100 text-emerald-900 border-emerald-400",
};

const TRANSITION_LABEL = {
  UNDER_INVESTIGATION: { label: "Mark Under Investigation", Icon: Search, tone: "blue" },
  CORRECTIVE_ACTION_REQUIRED: { label: "Mark Corrective Action Required", Icon: Wrench, tone: "orange" },
  PENDING_CLOSURE: { label: "Mark Pending Closure", Icon: ClipboardCheck, tone: "purple" },
  CLOSED: { label: "Mark Closed", Icon: Lock, tone: "emerald" },
};

function isReopen(fromState, toState) {
  return fromState === "CLOSED" && toState === "UNDER_INVESTIGATION";
}

function StatePill({ state }) {
  const cls = STATE_PILL[state] || "bg-slate-100 text-slate-800 border-slate-300";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md border-2 font-mono text-[11px] uppercase tracking-[0.18em] font-bold ${cls}`}
      data-testid="incident-lifecycle-state-pill"
    >
      {STATE_LABEL[state] || state}
    </span>
  );
}

export function IncidentLifecyclePanel({ incidentId, oshaRecordable }) {
  const [view, setView] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [closeOpen, setCloseOpen] = useState(false);
  const [closeFlags, setCloseFlags] = useState({
    investigation_complete: false,
    capa_complete: false,
    safety_review_complete: false,
    osha_recordable_ack: false,
  });

  const [reopenOpen, setReopenOpen] = useState(false);
  const [reopenReason, setReopenReason] = useState("");

  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchView = useCallback(async () => {
    try {
      // TRACK 14.0-PLATFORM-STABILITY · The lifecycle fetch is a
      // background read alongside the incident detail view. A 401/403
      // here (e.g. role lacks lifecycle permission, or stale portal
      // token races with a successful incident GET) must NOT pop the
      // global Session Expired overlay over already-rendered valid
      // incident content. The panel renders its own inline "Lifecycle
      // controls unavailable for this session." card instead.
      const r = await api.get(`/incidents/${incidentId}/lifecycle`, { skipSessionStatus: true });
      setView(r.data);
      setError("");
    } catch (err) {
      setError(err?.response?.data?.detail || "Lifecycle data unavailable");
    }
  }, [incidentId]);

  useEffect(() => {
    fetchView();
  }, [fetchView]);

  const doTransition = async (toState, payload = {}) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.post(`/incidents/${incidentId}/transition`, {
        to_state: toState,
        ...payload,
      });
      toast.success(
        isReopen(view?.lifecycle_state, toState)
          ? "Incident reopened"
          : `Incident marked ${STATE_LABEL[toState] || toState}`
      );
      await fetchView();
      if (historyOpen) await openHistory();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const code =
        (detail && typeof detail === "object" && detail.code) ||
        (typeof detail === "string" ? detail : "");
      const status = err?.response?.status;
      if (code?.startsWith?.("closure_attestation_missing")) {
        toast.error(`Closure blocked: missing ${code.split(":")[1]}`);
      } else if (code === "reopen_reason_required") {
        toast.error("Reopen requires a written reason.");
      } else if (status === 403) {
        toast.error("Your role cannot perform this transition.");
      } else if (status === 422) {
        toast.error(`Transition not allowed (${code || "validation"}).`);
      } else if (status === 401) {
        toast.error("Sign-in required.");
      } else {
        toast.error("Transition failed. Try again.");
      }
    } finally {
      setBusy(false);
    }
  };

  const openHistory = useCallback(async () => {
    setHistoryOpen(true);
    setHistoryLoading(true);
    try {
      const r = await api.get(`/incidents/${incidentId}/state-events`);
      setHistory(Array.isArray(r.data) ? r.data : []);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [incidentId]);

  if (error) {
    return (
      <div
        className="print:hidden border-2 border-rose-300 bg-rose-50 text-rose-900 rounded-md px-4 py-3 text-sm"
        data-testid="incident-lifecycle-error"
      >
        Lifecycle controls unavailable for this session.
      </div>
    );
  }
  if (!view) {
    return (
      <div
        className="print:hidden border-2 border-slate-200 bg-white rounded-md px-4 py-3 text-sm text-slate-500"
        data-testid="incident-lifecycle-loading"
      >
        <Loader2 className="w-4 h-4 inline animate-spin mr-2" />
        Loading lifecycle…
      </div>
    );
  }

  const current = view.lifecycle_state;
  const allowedNext = (view.legal_next_states || []).filter(n => n.allowed_for_actor);

  return (
    <section
      className="print:hidden border-2 border-slate-300 bg-white rounded-md px-4 py-4 sm:px-5 sm:py-5"
      data-testid="incident-lifecycle-panel"
    >
      <div className="flex items-center gap-3 flex-wrap mb-4">
        <ShieldAlert className="w-5 h-5 text-red-700 shrink-0" aria-hidden />
        <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
          Incident Lifecycle
        </span>
        <StatePill state={current} />
        {oshaRecordable && (
          <span
            className="font-mono text-[10px] uppercase tracking-[0.18em] px-2 py-0.5 rounded bg-red-100 text-red-900 border border-red-300 font-bold"
            data-testid="osha-recordable-flag"
          >
            OSHA Recordable
          </span>
        )}
        <Button
          variant="outline"
          size="sm"
          className="ml-auto h-8 px-3 text-xs border-2 border-slate-300"
          onClick={openHistory}
          data-testid="incident-lifecycle-history-btn"
        >
          <History className="w-3.5 h-3.5 mr-1" /> History
        </Button>
        <UndoLastTransitionButton
          workflow="incident"
          recordId={incidentId}
          onUndone={() => {
            fetchView();
            if (historyOpen) openHistory();
          }}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {allowedNext.length === 0 ? (
          <div
            className="text-xs text-slate-500 italic"
            data-testid="incident-lifecycle-no-actions"
          >
            No further transitions available for your role at this state.
          </div>
        ) : (
          allowedNext.map(({ to_state }) => {
            const meta = TRANSITION_LABEL[to_state] || { label: to_state, Icon: ShieldAlert };
            const { Icon } = meta;
            const reopen = isReopen(current, to_state);
            const label = reopen ? "Reopen Incident" : meta.label;
            const testid = reopen
              ? "incident-lifecycle-reopen-btn"
              : `incident-lifecycle-mark-${to_state.toLowerCase()}-btn`;
            const onClick = () => {
              if (to_state === "CLOSED") {
                setCloseFlags({
                  investigation_complete: false,
                  capa_complete: false,
                  safety_review_complete: false,
                  osha_recordable_ack: false,
                });
                setCloseOpen(true);
              } else if (reopen) {
                setReopenReason("");
                setReopenOpen(true);
              } else {
                doTransition(to_state);
              }
            };
            return (
              <Button
                key={to_state}
                onClick={onClick}
                disabled={busy}
                size="sm"
                className="h-9 px-3 font-bold uppercase tracking-wide text-xs border-b-2 border-slate-700 bg-slate-800 hover:bg-slate-900 text-white"
                data-testid={testid}
              >
                {reopen
                  ? <RotateCcw className="w-3.5 h-3.5 mr-1" />
                  : <Icon className="w-3.5 h-3.5 mr-1" />}
                {label}
              </Button>
            );
          })
        )}
      </div>

      {/* Closure attestation modal */}
      <Dialog open={closeOpen} onOpenChange={setCloseOpen}>
        <DialogContent className="sm:max-w-md" data-testid="incident-closure-modal">
          <DialogHeader>
            <DialogTitle>Close Incident</DialogTitle>
            <DialogDescription>
              Confirm each step is complete. All three attestations are required.
              {oshaRecordable && " OSHA-recordable acknowledgement is also required."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-2">
            {[
              ["investigation_complete", "Investigation complete"],
              ["capa_complete", "Corrective actions complete"],
              ["safety_review_complete", "Safety review complete"],
            ].map(([key, label]) => (
              <label key={key} className="flex items-start gap-3 cursor-pointer">
                <Checkbox
                  checked={closeFlags[key]}
                  onCheckedChange={v => setCloseFlags(s => ({ ...s, [key]: !!v }))}
                  data-testid={`incident-close-flag-${key}`}
                />
                <span className="text-sm text-slate-800">{label}</span>
              </label>
            ))}
            {oshaRecordable && (
              <label className="flex items-start gap-3 cursor-pointer pt-2 border-t border-slate-200">
                <Checkbox
                  checked={closeFlags.osha_recordable_ack}
                  onCheckedChange={v => setCloseFlags(s => ({ ...s, osha_recordable_ack: !!v }))}
                  data-testid="incident-close-flag-osha"
                />
                <span className="text-sm text-red-800 font-medium">
                  I acknowledge this is an OSHA-recordable incident and have
                  preserved the 300/301 record.
                </span>
              </label>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCloseOpen(false)}
              data-testid="incident-close-cancel">
              Cancel
            </Button>
            <Button
              disabled={busy}
              onClick={() => {
                doTransition("CLOSED", { evidence: closeFlags });
                setCloseOpen(false);
              }}
              className="bg-emerald-700 hover:bg-emerald-800 text-white"
              data-testid="incident-close-confirm"
            >
              <Lock className="w-3.5 h-3.5 mr-1" /> Close Incident
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reopen modal */}
      <Dialog open={reopenOpen} onOpenChange={setReopenOpen}>
        <DialogContent className="sm:max-w-md" data-testid="incident-reopen-modal">
          <DialogHeader>
            <DialogTitle>Reopen Incident</DialogTitle>
            <DialogDescription>
              A written reason is required. This will be recorded permanently in the audit trail.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Label htmlFor="reopen-reason" className="text-xs uppercase tracking-wide font-bold">
              Reason for reopening
            </Label>
            <Textarea
              id="reopen-reason"
              value={reopenReason}
              onChange={e => setReopenReason(e.target.value)}
              rows={4}
              placeholder="e.g. New witness statement contradicts initial findings."
              className="mt-2"
              data-testid="incident-reopen-reason"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReopenOpen(false)}
              data-testid="incident-reopen-cancel">
              Cancel
            </Button>
            <Button
              disabled={busy || reopenReason.trim().length < 5}
              onClick={() => {
                doTransition("UNDER_INVESTIGATION", { reason: reopenReason.trim() });
                setReopenOpen(false);
              }}
              className="bg-blue-700 hover:bg-blue-800 text-white"
              data-testid="incident-reopen-confirm"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1" /> Reopen
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History drawer */}
      <Dialog open={historyOpen} onOpenChange={setHistoryOpen}>
        <DialogContent className="sm:max-w-2xl" data-testid="incident-history-modal">
          <DialogHeader>
            <DialogTitle>Lifecycle Audit Trail</DialogTitle>
            <DialogDescription>
              Append-only record of every state transition. Newest first.
            </DialogDescription>
          </DialogHeader>
          {historyLoading ? (
            <div className="py-6 text-center text-slate-500 text-sm">
              <Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading…
            </div>
          ) : history.length === 0 ? (
            <div
              className="py-6 text-center text-slate-500 text-sm"
              data-testid="incident-history-empty"
            >
              No transitions recorded yet.
            </div>
          ) : (
            <div
              className="max-h-[60vh] overflow-y-auto divide-y divide-slate-200"
              data-testid="incident-history-list"
            >
              {history.map(ev => (
                <div key={ev.id} className="py-3" data-testid="incident-history-row">
                  <div className="flex items-center gap-2 flex-wrap text-xs">
                    <StatePill state={ev.from_state || "OPEN"} />
                    <span className="text-slate-400">→</span>
                    <StatePill state={ev.to_state} />
                    <span className="ml-auto font-mono text-[10px] text-slate-500 uppercase tracking-wider">
                      {new Date(ev.at).toLocaleString()}
                    </span>
                  </div>
                  <div className="mt-1.5 text-xs text-slate-600">
                    <span className="font-mono uppercase tracking-wider">{ev.actor_role}</span>
                    {ev.actor_name && <span> · {ev.actor_name}</span>}
                  </div>
                  {ev.reason && (
                    <div className="mt-1 text-sm text-slate-800 italic">"{ev.reason}"</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </section>
  );
}

export default IncidentLifecyclePanel;
