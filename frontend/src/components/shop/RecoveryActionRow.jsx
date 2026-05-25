/**
 * RecoveryActionRow.jsx · iter424 · Phase 25.1 · Inline Recovery Continuity Actions
 * ────────────────────────────────────────────────────────────────────────────────
 * The single inline affordance that closes the Shop recovery cognition loop:
 * SEE recovery state  →  ACT on recovery state  →  in the SAME calm flow.
 *
 * Doctrine guards (lock these — do NOT relax):
 *   • Inline only — NO modal, NO popup, NO page transition, NO drawer
 *   • One dropdown + one short note + one Save button — that is the entire UI
 *   • State list is the canonical iter420 RECOVERY_STATES set, nothing more
 *   • Optional note placeholder rotates operational examples (subtly teaches
 *     operational continuity language without becoming a tutorial)
 *   • When `returned_to_service` is selected, a single calm coaching line
 *     surfaces below the dropdown — embedded, not modal, not "are you sure?"
 *   • Success toast is calm operational language ("Recovery state updated.")
 *   • Hits the existing iter420 POST /dispatch/recovery/{id}/transition —
 *     no new endpoint, no new collection, no role drift
 */
import React, { useMemo, useState } from "react";
import { Loader2, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

// Canonical iter420 recovery states · MUST mirror RECOVERY_STATES in
// /app/backend/routes/dispatch_continuity.py. Don't extend this list.
const RECOVERY_STATES = [
  "acknowledged",
  "diagnosing",
  "waiting_on_parts",
  "repair_active",
  "operational_test",
  "returned_to_service",
];

// Rotating placeholder examples — teach operational continuity language
// without becoming a tutorial. The chosen string is stable per card so
// the field doesn't flicker between renders.
const NOTE_EXAMPLES = [
  "Waiting on hydraulic hose",
  "Operational test complete",
  "Back running",
  "Parts arriving tomorrow",
  "Sensor swapped · running clean",
];

// State-specific embedded coaching · ONE calm line · embedded, not modal.
function coachingForState(state, t) {
  switch (state) {
    case "returned_to_service":
      return t("Returned to service means equipment is operationally ready for field continuity.");
    case "waiting_on_parts":
      return t("Waiting on parts pauses operational recovery until components arrive.");
    case "operational_test":
      return t("Operational test confirms field readiness before return.");
    default:
      return "";
  }
}

export const RecoveryActionRow = ({ assignmentId, currentState, onSaved, testIdPrefix }) => {
  const { t } = useT();
  // Choose a stable placeholder per card · uses assignment_id hash for
  // determinism (so the same card always shows the same example).
  const placeholder = useMemo(() => {
    if (!assignmentId) return NOTE_EXAMPLES[0];
    let h = 0;
    for (let i = 0; i < assignmentId.length; i += 1) {
      h = (h * 31 + assignmentId.charCodeAt(i)) | 0;
    }
    return NOTE_EXAMPLES[Math.abs(h) % NOTE_EXAMPLES.length];
  }, [assignmentId]);

  // Default the dropdown to the "next" canonical state if we know the
  // current one; otherwise to the first state. This biases the UI toward
  // forward operational progress without ever forcing the choice.
  const defaultNext = useMemo(() => {
    if (!currentState) return RECOVERY_STATES[0];
    const idx = RECOVERY_STATES.indexOf(currentState);
    if (idx >= 0 && idx < RECOVERY_STATES.length - 1) {
      return RECOVERY_STATES[idx + 1];
    }
    return currentState;
  }, [currentState]);

  const [nextState, setNextState] = useState(defaultNext);
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);

  const coaching = coachingForState(nextState, t);

  const onSave = async () => {
    if (!assignmentId || !nextState) return;
    if (nextState === currentState) {
      toast.message(t("Already in that recovery state."));
      return;
    }
    setSaving(true);
    try {
      await api.post(`/dispatch/recovery/${encodeURIComponent(assignmentId)}/transition`, {
        to_state: nextState,
        note: note.trim().slice(0, 500),
      });
      toast.success(t("Recovery state updated."), { duration: 3000 });
      setNote("");
      if (typeof onSaved === "function") onSaved();
    } catch (err) {
      // Operational language only · no jargon · no stack details
      const msg = err?.response?.data?.detail || t("Could not update recovery state. Try again.");
      toast.error(typeof msg === "string" ? msg : t("Could not update recovery state. Try again."));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="mt-3 pt-3 border-t border-slate-100 space-y-2"
      data-testid={`${testIdPrefix}-row`}
    >
      <div className="flex flex-col sm:flex-row sm:items-center gap-2">
        <label className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold shrink-0" htmlFor={`${testIdPrefix}-state-select`}>
          {t("Set recovery state")}
        </label>
        <select
          id={`${testIdPrefix}-state-select`}
          value={nextState}
          onChange={(e) => setNextState(e.target.value)}
          disabled={saving}
          data-testid={`${testIdPrefix}-state-select`}
          className="h-9 px-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-800 focus:border-amber-600 focus:outline-none disabled:opacity-50"
        >
          {RECOVERY_STATES.map((s) => (
            <option key={s} value={s}>
              {t(stateLabel(s))}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col sm:flex-row sm:items-center gap-2">
        <input
          type="text"
          value={note}
          maxLength={120}
          onChange={(e) => setNote(e.target.value)}
          placeholder={`${t("Note (optional)")}: ${t(placeholder)}`}
          disabled={saving}
          data-testid={`${testIdPrefix}-note-input`}
          className="h-9 flex-1 px-3 rounded-md border border-slate-300 bg-white text-sm placeholder:text-slate-400 focus:border-amber-600 focus:outline-none disabled:opacity-50"
        />
        <button
          type="button"
          onClick={onSave}
          disabled={saving || !nextState}
          data-testid={`${testIdPrefix}-save-btn`}
          className="inline-flex items-center justify-center gap-1 h-9 px-4 rounded-md bg-slate-900 hover:bg-slate-800 text-white font-bold uppercase tracking-wide text-xs disabled:opacity-50"
        >
          {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <ChevronRight className="w-3.5 h-3.5" />}
          {saving ? t("Saving…") : t("Save")}
        </button>
      </div>
      {coaching ? (
        <p
          className="text-[11px] text-slate-500 italic leading-snug pl-1"
          data-testid={`${testIdPrefix}-coaching`}
        >
          {coaching}
        </p>
      ) : null}
    </div>
  );
};

// Human-readable canonical state label · same wording as Shop section headers.
function stateLabel(state) {
  switch (state) {
    case "acknowledged": return "Acknowledged";
    case "diagnosing": return "Diagnosing";
    case "waiting_on_parts": return "Waiting on parts";
    case "repair_active": return "Repair Active";
    case "operational_test": return "Operational Test";
    case "returned_to_service": return "Returned to Service";
    default: return state;
  }
}
