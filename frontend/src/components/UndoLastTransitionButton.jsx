/**
 * OMEGA · FOCP Release 2 · TR-0002 · Universal Undo Last Transition
 *
 * Reusable affordance for any lifecycle panel. Renders only when:
 *   - the current actor can see the panel (panel rendering is the
 *     read gate)
 *   - GET /workflows/{workflow}/{record_id}/last-transition returns
 *     undoable=true (which itself requires admin auth — non-admin
 *     viewers see no button)
 *
 * On confirm: POST /workflows/{workflow}/{record_id}/undo-last-transition
 * with a mandatory reason (>=5 chars). Calls onUndone() so the host
 * panel can refresh its lifecycle view and history.
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
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Undo2, Loader2 } from "lucide-react";

export function UndoLastTransitionButton({ workflow, recordId, onUndone }) {
  const [last, setLast] = useState(null);
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [available, setAvailable] = useState(false);

  const refresh = useCallback(async () => {
    if (!workflow || !recordId) return;
    try {
      const r = await api.get(
        `/workflows/${workflow}/${recordId}/last-transition`
      );
      const ok = !!r.data?.undoable;
      setAvailable(ok);
      setLast(ok ? r.data : null);
    } catch {
      // Non-admin viewers get 401/403 here — we silently hide the
      // affordance. The standard lifecycle panel keeps working.
      setAvailable(false);
      setLast(null);
    }
  }, [workflow, recordId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (!available || !last) return null;

  const ev = last.last_event || {};
  const fromState = ev.from_state || "—";
  const toState = ev.to_state || "—";
  const at = ev.at ? new Date(ev.at).toLocaleString() : "—";
  const actor = ev.actor_name || ev.actor_role || "—";

  const submit = async () => {
    const clean = (reason || "").trim();
    if (clean.length < 5) {
      toast.error("A reason of at least 5 characters is required.");
      return;
    }
    setBusy(true);
    try {
      await api.post(
        `/workflows/${workflow}/${recordId}/undo-last-transition`,
        { reason: clean }
      );
      toast.success("Last transition reversed.");
      setOpen(false);
      setReason("");
      await refresh();
      if (onUndone) onUndone();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const code =
        (detail && typeof detail === "object" && detail.code) ||
        (typeof detail === "string" ? detail : "");
      if (code === "no_transition_to_undo") {
        toast.error("This record has no transitions to undo yet.");
      } else if (code === "undo_state_mismatch") {
        toast.error("State drifted since the last transition. Refusing to undo.");
      } else if (err?.response?.status === 401) {
        toast.error("Admin sign-in required.");
      } else if (err?.response?.status === 403) {
        toast.error("Your role cannot undo transitions.");
      } else {
        toast.error("Undo failed. Try again.");
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={() => {
          setReason("");
          setOpen(true);
        }}
        className="h-8 px-3 text-xs border-2 border-amber-400 bg-amber-50 hover:bg-amber-100 text-amber-900 font-bold"
        data-testid="undo-last-transition-btn"
      >
        <Undo2 className="w-3.5 h-3.5 mr-1" />
        Undo last status change
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md" data-testid="undo-last-transition-modal">
          <DialogHeader>
            <DialogTitle>Reverse last status change</DialogTitle>
            <DialogDescription>
              This will move the record back to its previous state. The reversal
              is appended to the audit trail — the original transition is never
              deleted.
            </DialogDescription>
          </DialogHeader>

          <div className="py-2 space-y-2 border-2 border-slate-200 rounded-md p-3 bg-slate-50">
            <div className="text-[11px] font-mono uppercase tracking-[0.18em] text-slate-500">
              Last transition
            </div>
            <div className="text-sm text-slate-800">
              <b className="font-mono uppercase">{fromState}</b>
              <span className="mx-2 text-slate-400">→</span>
              <b className="font-mono uppercase">{toState}</b>
            </div>
            <div className="text-xs text-slate-600">
              By {actor} · {at}
            </div>
            <div className="text-xs text-amber-900 italic pt-1">
              Reversing will set state back to <b className="font-mono uppercase">{fromState}</b>.
            </div>
          </div>

          <div className="py-2">
            <Label
              htmlFor="undo-reason"
              className="text-xs uppercase tracking-wide font-bold"
            >
              Reason for reversal
            </Label>
            <Textarea
              id="undo-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              placeholder="e.g. Status was advanced on the wrong record."
              className="mt-1.5"
              data-testid="undo-last-transition-reason"
            />
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setOpen(false)}
              data-testid="undo-last-transition-cancel"
            >
              Cancel
            </Button>
            <Button
              disabled={busy || reason.trim().length < 5}
              onClick={submit}
              className="bg-amber-700 hover:bg-amber-800 text-white"
              data-testid="undo-last-transition-confirm"
            >
              {busy ? (
                <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />
              ) : (
                <Undo2 className="w-3.5 h-3.5 mr-1" />
              )}
              Reverse transition
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

export default UndoLastTransitionButton;
