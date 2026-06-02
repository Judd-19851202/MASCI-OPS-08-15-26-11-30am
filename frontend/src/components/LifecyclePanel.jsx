/**
 * OMEGA · Phase 1A · iter452 · Generic Workflow Lifecycle Panel
 *
 * Configuration-driven lifecycle UI shared across the 6 Phase 1A
 * workflows. iter451 introduced the inlined Incident version; iter452
 * extracts the shell and configures it per workflow.
 *
 * A config object describes:
 *   - workflowKey         (string, e.g. "incident", "daily_report", "payroll_variance")
 *   - apiBase             (string · e.g. "/incidents", "/daily-reports", "/hr/payroll-variance/batches")
 *   - title               (string · panel header)
 *   - stateLabels         ({STATE: "Human label"})
 *   - statePill           ({STATE: tailwind classes})
 *   - transitionLabels    ({TARGET_STATE: {label, Icon, tone, reopenLike?, kickbackLike?}})
 *   - closureConfig       (optional · for transitions whose target requires checkbox attestation)
 *     { targetState, title, description, flags: [{key, label, conditional?: fn(view)}], submitLabel }
 *   - reopenConfig        (optional · per transition that requires a reason)
 *     { targetStates: [...], title, description, placeholder }
 *   - kickbackConfig      (optional · for back-step that also requires a reason but isn't a "reopen")
 *     { fromState, toState, title, description, placeholder }
 *   - extraBadge          (optional · React node rendered next to the state pill)
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
import { History, Loader2, RotateCcw, Lock, ShieldAlert } from "lucide-react";
import { UndoLastTransitionButton } from "@/components/UndoLastTransitionButton";

function StatePill({ state, labels, classes, testid }) {
  const cls = classes[state] || "bg-slate-100 text-slate-800 border-slate-300";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md border-2 font-mono text-[11px] uppercase tracking-[0.18em] font-bold ${cls}`}
      data-testid={testid || "lifecycle-state-pill"}
    >
      {labels[state] || state}
    </span>
  );
}

export function LifecyclePanel({
  recordId,
  config,
}) {
  const {
    workflowKey,
    auditWorkflow,
    apiBase,
    title,
    stateLabels,
    statePill,
    transitionLabels,
    closureConfig,
    reopenConfig,
    kickbackConfig,
    extraBadge,
  } = config;

  const testidPrefix = workflowKey.replace(/_/g, "-");

  const [view, setView] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [closeOpen, setCloseOpen] = useState(false);
  const [closeFlags, setCloseFlags] = useState({});

  const [reasonOpen, setReasonOpen] = useState(false);
  const [reasonText, setReasonText] = useState("");
  const [reasonTarget, setReasonTarget] = useState(null); // {to_state, mode: "reopen"|"kickback"}

  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchView = useCallback(async () => {
    try {
      const r = await api.get(`${apiBase}/${recordId}/lifecycle`);
      setView(r.data);
      setError("");
    } catch (err) {
      setError(err?.response?.data?.detail || "Lifecycle data unavailable");
    }
  }, [apiBase, recordId]);

  useEffect(() => { fetchView(); }, [fetchView]);

  const openHistory = useCallback(async () => {
    setHistoryOpen(true);
    setHistoryLoading(true);
    try {
      const r = await api.get(`${apiBase}/${recordId}/state-events`);
      setHistory(Array.isArray(r.data) ? r.data : []);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [apiBase, recordId]);

  const doTransition = async (toState, payload = {}) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.post(`${apiBase}/${recordId}/transition`, {
        to_state: toState,
        ...payload,
      });
      toast.success(`${stateLabels[toState] || toState}`);
      await fetchView();
      if (historyOpen) await openHistory();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const code = (detail && typeof detail === "object" && detail.code) ||
                   (typeof detail === "string" ? detail : "");
      const status = err?.response?.status;
      if (code?.startsWith?.("closure_attestation_missing") ||
          code?.startsWith?.("finalize_attestation_missing")) {
        toast.error(`Blocked: missing ${code.split(":")[1]}`);
      } else if (code === "reopen_reason_required") {
        toast.error("Reopen requires a written reason.");
      } else if (code === "return_to_field_reason_required" ||
                 code === "back_step_reason_required") {
        toast.error("A written reason is required for this step.");
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

  if (error) {
    return (
      <div
        className="print:hidden border-2 border-rose-300 bg-rose-50 text-rose-900 rounded-md px-4 py-3 text-sm"
        data-testid={`${testidPrefix}-lifecycle-error`}
      >
        Lifecycle controls unavailable for this session.
      </div>
    );
  }
  if (!view) {
    return (
      <div
        className="print:hidden border-2 border-slate-200 bg-white rounded-md px-4 py-3 text-sm text-slate-500"
        data-testid={`${testidPrefix}-lifecycle-loading`}
      >
        <Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading lifecycle…
      </div>
    );
  }

  const current = view.lifecycle_state;
  const allowedNext = (view.legal_next_states || []).filter(n => n.allowed_for_actor);

  const handleAction = (toState) => {
    // Closure path
    if (closureConfig && closureConfig.targetState === toState) {
      const flags = {};
      for (const f of closureConfig.flags) {
        if (!f.conditional || f.conditional(view)) flags[f.key] = false;
      }
      setCloseFlags(flags);
      setCloseOpen(true);
      return;
    }
    // Reopen path
    if (reopenConfig && reopenConfig.targetStates.includes(toState) &&
        current === reopenConfig.fromState) {
      setReasonText("");
      setReasonTarget({ to_state: toState, mode: "reopen" });
      setReasonOpen(true);
      return;
    }
    // Kickback path
    if (kickbackConfig && kickbackConfig.fromState === current &&
        kickbackConfig.toState === toState) {
      setReasonText("");
      setReasonTarget({ to_state: toState, mode: "kickback" });
      setReasonOpen(true);
      return;
    }
    doTransition(toState);
  };

  return (
    <section
      className="print:hidden border-2 border-slate-300 bg-white rounded-md px-4 py-4 sm:px-5 sm:py-5"
      data-testid={`${testidPrefix}-lifecycle-panel`}
    >
      <div className="flex items-center gap-3 flex-wrap mb-4">
        <ShieldAlert className="w-5 h-5 text-red-700 shrink-0" aria-hidden />
        <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
          {title}
        </span>
        <StatePill state={current} labels={stateLabels} classes={statePill}
                   testid={`${testidPrefix}-lifecycle-state-pill`} />
        {extraBadge}
        <Button
          variant="outline" size="sm"
          className="ml-auto h-8 px-3 text-xs border-2 border-slate-300"
          onClick={openHistory}
          data-testid={`${testidPrefix}-lifecycle-history-btn`}
        >
          <History className="w-3.5 h-3.5 mr-1" /> History
        </Button>
        {auditWorkflow && (
          <UndoLastTransitionButton
            workflow={auditWorkflow}
            recordId={recordId}
            onUndone={() => {
              fetchView();
              if (historyOpen) openHistory();
            }}
          />
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {allowedNext.length === 0 ? (
          <div
            className="text-xs text-slate-500 italic"
            data-testid={`${testidPrefix}-lifecycle-no-actions`}
          >
            No further transitions available for your role at this state.
          </div>
        ) : allowedNext.map(({ to_state }) => {
          const meta = transitionLabels[to_state] || { label: to_state, Icon: ShieldAlert };
          const { Icon, label } = meta;
          const isReopen = reopenConfig && reopenConfig.targetStates.includes(to_state) &&
                           current === reopenConfig.fromState;
          const isKickback = kickbackConfig && kickbackConfig.fromState === current &&
                             kickbackConfig.toState === to_state;
          const buttonLabel = isReopen ? "Reopen" : (meta.label || label);
          const tid = isReopen
            ? `${testidPrefix}-lifecycle-reopen-btn`
            : isKickback
              ? `${testidPrefix}-lifecycle-kickback-btn`
              : `${testidPrefix}-lifecycle-mark-${to_state.toLowerCase()}-btn`;
          return (
            <Button
              key={to_state}
              onClick={() => handleAction(to_state)}
              disabled={busy}
              size="sm"
              className="h-9 px-3 font-bold uppercase tracking-wide text-xs border-b-2 border-slate-700 bg-slate-800 hover:bg-slate-900 text-white"
              data-testid={tid}
            >
              {isReopen
                ? <RotateCcw className="w-3.5 h-3.5 mr-1" />
                : Icon ? <Icon className="w-3.5 h-3.5 mr-1" /> : null}
              {buttonLabel}
            </Button>
          );
        })}
      </div>

      {/* Closure modal */}
      {closureConfig && (
        <Dialog open={closeOpen} onOpenChange={setCloseOpen}>
          <DialogContent className="sm:max-w-md" data-testid={`${testidPrefix}-closure-modal`}>
            <DialogHeader>
              <DialogTitle>{closureConfig.title}</DialogTitle>
              <DialogDescription>{
                typeof closureConfig.description === "function"
                  ? closureConfig.description(view)
                  : closureConfig.description
              }</DialogDescription>
            </DialogHeader>
            <div className="space-y-3 py-2">
              {closureConfig.flags
                .filter(f => !f.conditional || f.conditional(view))
                .map(f => (
                  <label key={f.key} className="flex items-start gap-3 cursor-pointer">
                    <Checkbox
                      checked={!!closeFlags[f.key]}
                      onCheckedChange={v => setCloseFlags(s => ({ ...s, [f.key]: !!v }))}
                      data-testid={`${testidPrefix}-close-flag-${f.key}`}
                    />
                    <span className={`text-sm ${f.emphasis ? "text-red-800 font-medium" : "text-slate-800"}`}>
                      {f.label}
                    </span>
                  </label>
                ))}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCloseOpen(false)}
                data-testid={`${testidPrefix}-close-cancel`}>
                Cancel
              </Button>
              <Button
                disabled={busy}
                onClick={() => {
                  doTransition(closureConfig.targetState, { evidence: closeFlags });
                  setCloseOpen(false);
                }}
                className="bg-emerald-700 hover:bg-emerald-800 text-white"
                data-testid={`${testidPrefix}-close-confirm`}
              >
                <Lock className="w-3.5 h-3.5 mr-1" /> {closureConfig.submitLabel || "Close"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}

      {/* Reason modal (reopen or kickback) */}
      <Dialog open={reasonOpen} onOpenChange={setReasonOpen}>
        <DialogContent className="sm:max-w-md" data-testid={`${testidPrefix}-reason-modal`}>
          <DialogHeader>
            <DialogTitle>{
              reasonTarget?.mode === "kickback"
                ? (kickbackConfig?.title || "Return to field")
                : (reopenConfig?.title || "Reopen")
            }</DialogTitle>
            <DialogDescription>{
              reasonTarget?.mode === "kickback"
                ? (kickbackConfig?.description || "A written reason is required.")
                : (reopenConfig?.description || "A written reason is required. Recorded in audit trail.")
            }</DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Label htmlFor="reason-input" className="text-xs uppercase tracking-wide font-bold">
              Reason
            </Label>
            <Textarea
              id="reason-input"
              value={reasonText}
              onChange={e => setReasonText(e.target.value)}
              rows={4}
              placeholder={
                reasonTarget?.mode === "kickback"
                  ? (kickbackConfig?.placeholder || "e.g. Missing crew hours.")
                  : (reopenConfig?.placeholder || "e.g. New evidence surfaced.")
              }
              className="mt-2"
              data-testid={`${testidPrefix}-reason-input`}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReasonOpen(false)}
              data-testid={`${testidPrefix}-reason-cancel`}>
              Cancel
            </Button>
            <Button
              disabled={busy || reasonText.trim().length < 5}
              onClick={() => {
                doTransition(reasonTarget.to_state, { reason: reasonText.trim() });
                setReasonOpen(false);
              }}
              className="bg-blue-700 hover:bg-blue-800 text-white"
              data-testid={`${testidPrefix}-reason-confirm`}
            >
              {reasonTarget?.mode === "kickback" ? "Return to field" : "Reopen"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History drawer */}
      <Dialog open={historyOpen} onOpenChange={setHistoryOpen}>
        <DialogContent className="sm:max-w-2xl" data-testid={`${testidPrefix}-history-modal`}>
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
              data-testid={`${testidPrefix}-history-empty`}
            >
              No transitions recorded yet.
            </div>
          ) : (
            <div
              className="max-h-[60vh] overflow-y-auto divide-y divide-slate-200"
              data-testid={`${testidPrefix}-history-list`}
            >
              {history.map(ev => (
                <div key={ev.id} className="py-3" data-testid={`${testidPrefix}-history-row`}>
                  <div className="flex items-center gap-2 flex-wrap text-xs">
                    <StatePill state={ev.from_state || (view.default_state || "OPEN")} labels={stateLabels} classes={statePill} />
                    <span className="text-slate-400">→</span>
                    <StatePill state={ev.to_state} labels={stateLabels} classes={statePill} />
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

export default LifecyclePanel;
