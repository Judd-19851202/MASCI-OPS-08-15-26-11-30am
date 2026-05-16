// useDraftSync.js — Phase J · non-invasive autosave companion for
// forms that already manage their own state via useState.
//
// Unlike `useDraft`, this hook does NOT own the form state — it
// observes `data`, debounces, and writes IndexedDB drafts. On mount
// it loads any existing draft and hands it back via `onRecover(draft)`
// so the parent decides whether to re-apply it.
//
// Returns:
//   {
//     draftStatus,   // "idle" | "saving" | "saved"
//     hasDraft,      // briefly true after a recovery is offered
//     discard(),     // wipe the IndexedDB draft + clear hasDraft
//     commit(),      // wipe the IndexedDB draft after successful POST
//   }

import { useEffect, useRef, useState, useCallback } from "react";
import { saveDraft, getDraft, discardDraft } from "./draftStore";

const DEBOUNCE_MS = 800;

export function useDraftSync(formKey, data, actorId, onRecover) {
  const [draftStatus, setDraftStatus] = useState("idle");
  const [hasDraft, setHasDraft] = useState(false);
  const loadedRef = useRef(false);
  const timerRef = useRef(null);
  const lastSavedKeyRef = useRef(null);
  const onRecoverRef = useRef(onRecover);
  onRecoverRef.current = onRecover;

  // On mount: try to load draft and hand it back.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const draft = await getDraft(actorId, formKey);
        if (!cancelled && draft && onRecoverRef.current) {
          onRecoverRef.current(draft);
          setHasDraft(true);
        }
      } finally {
        loadedRef.current = true;
        lastSavedKeyRef.current = JSON.stringify(data || {});
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formKey, actorId]);

  // Autosave: watch data changes, debounce, then persist.
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

  const discard = useCallback(async () => {
    await discardDraft(actorId, formKey);
    setHasDraft(false);
    setDraftStatus("idle");
  }, [actorId, formKey]);

  const commit = useCallback(async () => {
    await discardDraft(actorId, formKey);
    setHasDraft(false);
    setDraftStatus("idle");
    lastSavedKeyRef.current = null;
  }, [actorId, formKey]);

  return { draftStatus, hasDraft, discard, commit };
}
