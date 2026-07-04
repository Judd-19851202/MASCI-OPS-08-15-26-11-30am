/**
 * OMEGA · Phase 1A · iter453 · OC-004 Site Inspection Finding Follow-Up Lifecycle Panel
 *
 * Closure-action contract (Amendment 001 REPLACE-4 binding) — operator picks ONE path:
 *   A) Re-inspection passed  → re_inspection_passed + re_inspection_record_id
 *   B) Corrective action     → corrective_action_completed + corrective_action_notes (>=20)
 *   C) Documented exception  → exception_approved + exception_reason (>=10) + dual sign-off
 *
 * "Acknowledge findings" ack-only closure is FORBIDDEN per Amendment 001.
 *
 * Reopen (CLOSED → FINDINGS_RAISED) and Rework (PENDING_RE_INSPECTION → FINDINGS_RAISED)
 * both require a written reason (>=5 chars).
 *
 * Backend wiring: /api/inspections/{id}/lifecycle | /transition | /state-events
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
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  ShieldAlert,
  AlertTriangle,
  Wrench,
  ClipboardCheck,
  Lock,
  RotateCcw,
  Undo2,
  History,
  Loader2,
} from "lucide-react";
import { UndoLastTransitionButton } from "@/components/UndoLastTransitionButton";

const STATE_LABEL = {
  OPEN: "Open",
  FINDINGS_RAISED: "Findings Raised",
  IN_REMEDIATION: "In Remediation",
  PENDING_RE_INSPECTION: "Pending Re-Inspection",
  CLOSED: "Closed",
};

const STATE_PILL = {
  OPEN: "bg-amber-100 text-amber-900 border-amber-400",
  FINDINGS_RAISED: "bg-red-100 text-red-900 border-red-400",
  IN_REMEDIATION: "bg-blue-100 text-blue-900 border-blue-400",
  PENDING_RE_INSPECTION: "bg-violet-100 text-violet-900 border-violet-400",
  CLOSED: "bg-emerald-100 text-emerald-900 border-emerald-400",
};

const TRANSITION_META = {
  FINDINGS_RAISED: { label: "Raise Findings", Icon: AlertTriangle },
  IN_REMEDIATION: { label: "Mark In Remediation", Icon: Wrench },
  PENDING_RE_INSPECTION: { label: "Mark Pending Re-Inspection", Icon: ClipboardCheck },
  CLOSED: { label: "Close Inspection", Icon: Lock },
};

function StatePill({ state }) {
  const cls = STATE_PILL[state] || "bg-slate-100 text-slate-800 border-slate-300";
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md border-2 font-mono text-[11px] uppercase tracking-[0.18em] font-bold ${cls}`}
      data-testid="site-inspection-lifecycle-state-pill"
    >
      {STATE_LABEL[state] || state}
    </span>
  );
}

const EMPTY_EVIDENCE = {
  path: "re_inspection",
  re_inspection_record_id: "",
  corrective_action_notes: "",
  exception_reason: "",
  pm_signoff_user_id: "",
  safety_signoff_user_id: "",
};

export function SiteInspectionLifecyclePanel({ inspectionId }) {
  const [view, setView] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [closeOpen, setCloseOpen] = useState(false);
  const [closeForm, setCloseForm] = useState(EMPTY_EVIDENCE);

  const [reasonOpen, setReasonOpen] = useState(false);
  const [reasonText, setReasonText] = useState("");
  const [reasonTarget, setReasonTarget] = useState(null); // {to_state, mode: "reopen"|"rework"}

  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const fetchView = useCallback(async () => {
    try {
      const r = await api.get(`/inspections/${inspectionId}/lifecycle`);
      setView(r.data);
      setError("");
    } catch (err) {
      setError(err?.response?.data?.detail || "Lifecycle data unavailable");
    }
  }, [inspectionId]);

  useEffect(() => { fetchView(); }, [fetchView]);

  const openHistory = useCallback(async () => {
    setHistoryOpen(true);
    setHistoryLoading(true);
    try {
      const r = await api.get(`/inspections/${inspectionId}/state-events`);
      setHistory(Array.isArray(r.data) ? r.data : []);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [inspectionId]);

  const doTransition = async (toState, payload = {}) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.post(`/inspections/${inspectionId}/transition`, {
        to_state: toState,
        ...payload,
      });
      toast.success(STATE_LABEL[toState] || toState);
      await fetchView();
      if (historyOpen) await openHistory();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const code = (detail && typeof detail === "object" && detail.code) ||
                   (typeof detail === "string" ? detail : "");
      const status = err?.response?.status;
      if (code?.startsWith?.("closure_evidence_missing")) {
        toast.error(`Closure blocked: ${code.split(":")[1] || "operational evidence required"}`);
      } else if (code === "reopen_reason_required") {
        toast.error("Reopen requires a written reason (5+ chars).");
      } else if (code === "rework_reason_required") {
        toast.error("Rework requires a written reason (5+ chars).");
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
        data-testid="site-inspection-lifecycle-error"
      >
        Lifecycle controls unavailable for this session.
      </div>
    );
  }
  if (!view) {
    return (
      <div
        className="print:hidden border-2 border-slate-200 bg-white rounded-md px-4 py-3 text-sm text-slate-500"
        data-testid="site-inspection-lifecycle-loading"
      >
        <Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading lifecycle…
      </div>
    );
  }

  const current = view.lifecycle_state;
  const allowedNext = (view.legal_next_states || []).filter(n => n.allowed_for_actor);

  const isReopen = (toState) => current === "CLOSED" && toState === "FINDINGS_RAISED";
  const isRework = (toState) => current === "PENDING_RE_INSPECTION" && toState === "FINDINGS_RAISED";

  const handleAction = (toState) => {
    if (toState === "CLOSED") {
      setCloseForm(EMPTY_EVIDENCE);
      setCloseOpen(true);
      return;
    }
    if (isReopen(toState)) {
      setReasonText("");
      setReasonTarget({ to_state: toState, mode: "reopen" });
      setReasonOpen(true);
      return;
    }
    if (isRework(toState)) {
      setReasonText("");
      setReasonTarget({ to_state: toState, mode: "rework" });
      setReasonOpen(true);
      return;
    }
    doTransition(toState);
  };

  const buildClosureEvidence = () => {
    const f = closeForm;
    if (f.path === "re_inspection") {
      return {
        re_inspection_passed: true,
        re_inspection_record_id: f.re_inspection_record_id.trim(),
      };
    }
    if (f.path === "corrective_action") {
      return {
        corrective_action_completed: true,
        corrective_action_notes: f.corrective_action_notes.trim(),
      };
    }
    return {
      exception_approved: true,
      exception_reason: f.exception_reason.trim(),
      pm_signoff_user_id: f.pm_signoff_user_id.trim(),
      safety_signoff_user_id: f.safety_signoff_user_id.trim(),
    };
  };

  const closureValid = (() => {
    const f = closeForm;
    if (f.path === "re_inspection") return f.re_inspection_record_id.trim().length > 0;
    if (f.path === "corrective_action") return f.corrective_action_notes.trim().length >= 20;
    if (f.path === "exception") {
      const pm = f.pm_signoff_user_id.trim();
      const sf = f.safety_signoff_user_id.trim();
      return (
        f.exception_reason.trim().length >= 10 &&
        pm.length > 0 &&
        sf.length > 0 &&
        pm !== sf
      );
    }
    return false;
  })();

  return (
    <section
      className="print:hidden border-2 border-slate-300 bg-white rounded-md px-4 py-4 sm:px-5 sm:py-5"
      data-testid="site-inspection-lifecycle-panel"
    >
      <div className="flex items-center gap-3 flex-wrap mb-4">
        <ShieldAlert className="w-5 h-5 text-red-700 shrink-0" aria-hidden />
        <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">
          Site Inspection Findings Lifecycle
        </span>
        <StatePill state={current} />
        <Button
          variant="outline" size="sm"
          className="ml-auto h-8 px-3 text-xs border-2 border-slate-300"
          onClick={openHistory}
          data-testid="site-inspection-lifecycle-history-btn"
        >
          <History className="w-3.5 h-3.5 mr-1" /> History
        </Button>
        <UndoLastTransitionButton
          workflow="site_inspection"
          recordId={inspectionId}
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
            data-testid="site-inspection-lifecycle-no-actions"
          >
            No further transitions available for your role at this state.
          </div>
        ) : allowedNext.map(({ to_state }) => {
          const meta = TRANSITION_META[to_state] || { label: to_state, Icon: ShieldAlert };
          const { Icon } = meta;
          const reopen = isReopen(to_state);
          const rework = isRework(to_state);
          const label = reopen ? "Reopen Inspection"
                       : rework ? "Return for Rework"
                       : meta.label;
          const tid = reopen
            ? "site-inspection-lifecycle-reopen-btn"
            : rework
              ? "site-inspection-lifecycle-rework-btn"
              : `site-inspection-lifecycle-mark-${to_state.toLowerCase()}-btn`;
          const IconEl = reopen ? RotateCcw : rework ? Undo2 : Icon;
          return (
            <Button
              key={to_state}
              onClick={() => handleAction(to_state)}
              disabled={busy}
              size="sm"
              className="h-9 px-3 font-bold uppercase tracking-wide text-xs border-b-2 border-slate-700 bg-slate-800 hover:bg-slate-900 text-white"
              data-testid={tid}
            >
              <IconEl className="w-3.5 h-3.5 mr-1" /> {label}
            </Button>
          );
        })}
      </div>

      {/* Closure modal · 3-path operational evidence */}
      <Dialog open={closeOpen} onOpenChange={setCloseOpen}>
        <DialogContent className="sm:max-w-lg" data-testid="site-inspection-closure-modal">
          <DialogHeader>
            <DialogTitle>Close Site Inspection</DialogTitle>
            <DialogDescription>
              Closure requires operational evidence — pick one path. &quot;Acknowledge findings&quot;
              ack-only closure is not permitted (Amendment 001 REPLACE-4).
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <RadioGroup
              value={closeForm.path}
              onValueChange={v => setCloseForm(s => ({ ...s, path: v }))}
              className="space-y-2"
            >
              <label className="flex items-start gap-3 cursor-pointer">
                <RadioGroupItem
                  value="re_inspection"
                  id="si-close-path-re-inspection"
                  data-testid="site-inspection-close-path-re-inspection"
                />
                <div className="flex-1">
                  <div className="text-sm font-bold text-slate-900">A · Re-inspection passed</div>
                  <div className="text-xs text-slate-500">
                    Record the site re-inspection ID that verifies remediation.
                  </div>
                  {closeForm.path === "re_inspection" && (
                    <div className="mt-2">
                      <Label htmlFor="si-close-re-id" className="text-[10px] uppercase tracking-wide font-bold">
                        Re-inspection Record ID
                      </Label>
                      <Input
                        id="si-close-re-id"
                        value={closeForm.re_inspection_record_id}
                        onChange={e => setCloseForm(s => ({ ...s, re_inspection_record_id: e.target.value }))}
                        placeholder="e.g. INSP-00123 or UUID"
                        className="mt-1"
                        data-testid="site-inspection-close-re-inspection-id"
                      />
                    </div>
                  )}
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer">
                <RadioGroupItem
                  value="corrective_action"
                  id="si-close-path-corrective-action"
                  data-testid="site-inspection-close-path-corrective-action"
                />
                <div className="flex-1">
                  <div className="text-sm font-bold text-slate-900">B · Corrective action completed</div>
                  <div className="text-xs text-slate-500">
                    Describe the corrective action performed (≥20 characters).
                  </div>
                  {closeForm.path === "corrective_action" && (
                    <div className="mt-2">
                      <Label htmlFor="si-close-ca-notes" className="text-[10px] uppercase tracking-wide font-bold">
                        Corrective Action Notes
                      </Label>
                      <Textarea
                        id="si-close-ca-notes"
                        value={closeForm.corrective_action_notes}
                        onChange={e => setCloseForm(s => ({ ...s, corrective_action_notes: e.target.value }))}
                        rows={3}
                        placeholder="e.g. Replaced damaged GFCI on circuit B, tagged out, foreman verified."
                        className="mt-1"
                        data-testid="site-inspection-close-ca-notes"
                      />
                      <div className="text-[10px] text-slate-500 mt-1 font-mono">
                        {closeForm.corrective_action_notes.trim().length}/20 chars min
                      </div>
                    </div>
                  )}
                </div>
              </label>

              <label className="flex items-start gap-3 cursor-pointer">
                <RadioGroupItem
                  value="exception"
                  id="si-close-path-exception"
                  data-testid="site-inspection-close-path-exception"
                />
                <div className="flex-1">
                  <div className="text-sm font-bold text-slate-900">C · Documented exception</div>
                  <div className="text-xs text-slate-500">
                    Requires written reason (≥10 chars) and dual sign-off (PM + Safety, distinct).
                  </div>
                  {closeForm.path === "exception" && (
                    <div className="mt-2 space-y-2">
                      <div>
                        <Label htmlFor="si-close-exc-reason" className="text-[10px] uppercase tracking-wide font-bold">
                          Exception Reason
                        </Label>
                        <Textarea
                          id="si-close-exc-reason"
                          value={closeForm.exception_reason}
                          onChange={e => setCloseForm(s => ({ ...s, exception_reason: e.target.value }))}
                          rows={2}
                          placeholder="e.g. Scope change removed affected work area."
                          className="mt-1"
                          data-testid="site-inspection-close-exception-reason"
                        />
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <Label htmlFor="si-close-pm" className="text-[10px] uppercase tracking-wide font-bold">
                            PM Sign-off User ID
                          </Label>
                          <Input
                            id="si-close-pm"
                            value={closeForm.pm_signoff_user_id}
                            onChange={e => setCloseForm(s => ({ ...s, pm_signoff_user_id: e.target.value }))}
                            placeholder="pm user id"
                            className="mt-1"
                            data-testid="site-inspection-close-pm-signoff"
                          />
                        </div>
                        <div>
                          <Label htmlFor="si-close-safety" className="text-[10px] uppercase tracking-wide font-bold">
                            Safety Sign-off User ID
                          </Label>
                          <Input
                            id="si-close-safety"
                            value={closeForm.safety_signoff_user_id}
                            onChange={e => setCloseForm(s => ({ ...s, safety_signoff_user_id: e.target.value }))}
                            placeholder="safety user id"
                            className="mt-1"
                            data-testid="site-inspection-close-safety-signoff"
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </label>
            </RadioGroup>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCloseOpen(false)}
              data-testid="site-inspection-close-cancel">
              Cancel
            </Button>
            <Button
              disabled={busy || !closureValid}
              onClick={() => {
                doTransition("CLOSED", { evidence: buildClosureEvidence() });
                setCloseOpen(false);
              }}
              className="bg-emerald-700 hover:bg-emerald-800 text-white"
              data-testid="site-inspection-close-confirm"
            >
              <Lock className="w-3.5 h-3.5 mr-1" /> Close Inspection
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reason modal (reopen / rework) */}
      <Dialog open={reasonOpen} onOpenChange={setReasonOpen}>
        <DialogContent className="sm:max-w-md" data-testid="site-inspection-reason-modal">
          <DialogHeader>
            <DialogTitle>
              {reasonTarget?.mode === "reopen" ? "Reopen Site Inspection" : "Return for Rework"}
            </DialogTitle>
            <DialogDescription>
              A written reason (≥5 chars) is required. Recorded permanently in the audit trail.
            </DialogDescription>
          </DialogHeader>
          <div className="py-2">
            <Label htmlFor="si-reason-input" className="text-xs uppercase tracking-wide font-bold">
              Reason
            </Label>
            <Textarea
              id="si-reason-input"
              value={reasonText}
              onChange={e => setReasonText(e.target.value)}
              rows={4}
              placeholder={
                reasonTarget?.mode === "reopen"
                  ? "e.g. New hazard surfaced after closeout."
                  : "e.g. Re-inspection failed on guardrail spacing."
              }
              className="mt-2"
              data-testid="site-inspection-reason-input"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReasonOpen(false)}
              data-testid="site-inspection-reason-cancel">
              Cancel
            </Button>
            <Button
              disabled={busy || reasonText.trim().length < 5}
              onClick={() => {
                doTransition(reasonTarget.to_state, { reason: reasonText.trim() });
                setReasonOpen(false);
              }}
              className="bg-blue-700 hover:bg-blue-800 text-white"
              data-testid="site-inspection-reason-confirm"
            >
              {reasonTarget?.mode === "reopen"
                ? <><RotateCcw className="w-3.5 h-3.5 mr-1" /> Reopen</>
                : <><Undo2 className="w-3.5 h-3.5 mr-1" /> Return for Rework</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History drawer */}
      <Dialog open={historyOpen} onOpenChange={setHistoryOpen}>
        <DialogContent className="sm:max-w-2xl" data-testid="site-inspection-history-modal">
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
              data-testid="site-inspection-history-empty"
            >
              No transitions recorded yet.
            </div>
          ) : (
            <div
              className="max-h-[60vh] overflow-y-auto divide-y divide-slate-200"
              data-testid="site-inspection-history-list"
            >
              {history.map(ev => (
                <div key={ev.id} className="py-3" data-testid="site-inspection-history-row">
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
                    <div className="mt-1 text-sm text-slate-800 italic">&quot;{ev.reason}&quot;</div>
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

export default SiteInspectionLifecyclePanel;
