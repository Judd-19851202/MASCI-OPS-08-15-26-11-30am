// useFormDraft.js — iter434 · Phase 31 · Part 2.
//
// Manual-restore variant of `useDraftSync`.
//
// Unlike `useDraftSync` (which calls `onRecover(draft)` and lets the
// parent immediately re-apply state), this hook NEVER auto-applies
// the recovered draft. Instead it exposes:
//
//   {
//     pendingDraft,    // the loaded draft (or null) · NOT applied yet
//     loaded,          // true once the initial load completed
//     draftStatus,     // "idle" | "saving" | "saved" · for the pill
//     restore(),       // returns the pending draft and clears it
//     discard(),       // wipes the IDB entry and clears pendingDraft
//     commit(),        // wipes the IDB entry after a successful POST
//   }
//
// The parent calls `restore()` from the calm `<DraftRestorePrompt />`
// only after the user explicitly chooses Restore. This satisfies the
// Phase 31 doctrine: "Do NOT auto-overwrite submitted data."
//
// Autosave still runs on `data` changes (debounced) so the user's
// in-progress edits are persisted continuously.

import { useEffect, useRef, useState, useCallback } from "react";
import { saveDraft, getDraft, discardDraft } from "./draftStore";

const DEBOUNCE_MS = 800;

export function useFormDraft(formKey, data, actorId) {
  const [pendingDraft, setPendingDraft] = useState(null);
  const [loaded, setLoaded] = useState(false);
  const [draftStatus, setDraftStatus] = useState("idle");
  const timerRef = useRef(null);
  const lastSavedKeyRef = useRef(null);

  // On mount: load any existing draft into pendingDraft (do NOT apply).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const draft = await getDraft(actorId, formKey);
        if (!cancelled && draft) setPendingDraft(draft);
      } finally {
        if (!cancelled) {
          setLoaded(true);
          lastSavedKeyRef.current = JSON.stringify(data || {});
        }
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formKey, actorId]);

  // Autosave on data changes (debounced). Same shape as useDraftSync.
  useEffect(() => {
    if (!loaded) return;
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
  }, [data, formKey, actorId, loaded]);

  // restore() returns the pending draft and clears it so the parent
  // can call setData(restored) explicitly. Idempotent.
  const restore = useCallback(() => {
    const d = pendingDraft;
    setPendingDraft(null);
    return d;
  }, [pendingDraft]);

  const discard = useCallback(async () => {
    await discardDraft(actorId, formKey);
    setPendingDraft(null);
    setDraftStatus("idle");
  }, [actorId, formKey]);

  const commit = useCallback(async () => {
    await discardDraft(actorId, formKey);
    setPendingDraft(null);
    setDraftStatus("idle");
    lastSavedKeyRef.current = null;
  }, [actorId, formKey]);

  return { pendingDraft, loaded, draftStatus, restore, discard, commit };
}
