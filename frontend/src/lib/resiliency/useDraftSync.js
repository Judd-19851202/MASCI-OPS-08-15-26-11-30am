// useDraftSync.js — TRACK 27.08 · explicit-restore contract.
//
// Behavior:
//   * On mount: LOAD the draft, but DO NOT auto-apply it. Expose it
//     to the caller as `pendingDraft` so the caller renders an
//     explicit "Restore / Start blank" prompt.
//   * When the caller confirms restore, they call `applyDraft()` which
//     invokes `onRecover(draft)` with the loaded body.
//   * When the caller chooses start-blank, they call `discard()` which
//     wipes the persisted draft.
//   * Autosave still runs (debounced) as the operator types so an
//     interrupted session recovers cleanly.
//
// The previous "silent auto-apply" behaviour is deliberately gone —
// production users reported prior submissions leaking into fresh
// forms because the auto-apply happened before the operator could
// even see the empty form. This hook now guarantees blank-by-default
// unless the operator explicitly restores.

import { useCallback, useEffect, useRef, useState } from "react";
import { discardDraft, getDraft, saveDraft } from "./draftStore";

const DEBOUNCE_MS = 800;

export function useDraftSync(formKey, data, actorId, onRecover) {
  const [draftStatus, setDraftStatus] = useState("idle");
  const [pendingDraft, setPendingDraft] = useState(null);
  const loadedRef = useRef(false);
  const timerRef = useRef(null);
  const lastSavedKeyRef = useRef(null);
  const onRecoverRef = useRef(onRecover);
  onRecoverRef.current = onRecover;

  // On mount: load the draft into local state — do NOT apply it.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const draft = await getDraft(actorId, formKey);
        if (!cancelled && draft) {
          setPendingDraft(draft);
        }
      } finally {
        loadedRef.current = true;
        lastSavedKeyRef.current = JSON.stringify(data || {});
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formKey, actorId]);

  // Autosave — same as before, but only after the initial load
  // completes so we never overwrite a real draft with the empty
  // initial-state serialisation.
  useEffect(() => {
    if (!loadedRef.current) return;
    const serialized = JSON.stringify(data || {});
    if (serialized === lastSavedKeyRef.current) return;
    setDraftStatus("saving");
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      await saveDraft(actorId, formKey, data);
      lastSavedKeyRef.current = serialized;
      setDraftStatus("saved");
      setTimeout(() => setDraftStatus("idle"), 1200);
    }, DEBOUNCE_MS);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [data, formKey, actorId]);

  // Operator chose to restore — invoke onRecover with the loaded
  // draft body and clear the pending state.
  const applyDraft = useCallback(() => {
    if (pendingDraft && onRecoverRef.current) {
      onRecoverRef.current(pendingDraft);
    }
    setPendingDraft(null);
  }, [pendingDraft]);

  // Operator chose "start blank" OR the form has just been submitted.
  const discard = useCallback(async () => {
    await discardDraft(actorId, formKey);
    setPendingDraft(null);
    setDraftStatus("idle");
    // Reset the debounce ref so the next keystroke will save a fresh
    // draft rather than being no-op'd by a stale serialised match.
    lastSavedKeyRef.current = JSON.stringify(data || {});
  }, [actorId, formKey, data]);

  const commit = useCallback(async () => {
    await discardDraft(actorId, formKey);
    setPendingDraft(null);
    setDraftStatus("idle");
    lastSavedKeyRef.current = null;
  }, [actorId, formKey]);

  return {
    draftStatus,
    pendingDraft,        // { … } if a draft was recovered, else null
    hasPendingDraft: !!pendingDraft,
    applyDraft,          // caller invokes when operator clicks Restore
    discard,             // caller invokes when operator clicks Start blank
    commit,              // caller invokes after successful submit
  };
}
