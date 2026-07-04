// useDraft.js — React hook for shared autosave + draft recovery.
//
// Usage:
//   const {
//     formData, setFormData,
//     draftStatus,      // "idle" | "saving" | "saved"
//     hasDraft,         // true when a draft was loaded on mount
//     discard,
//   } = useDraft("incident-new", initialFormData, actorId);
//
// Behavior:
//   * On mount: tries to load a draft for (actorId, formKey). If found,
//     setFormData(draft) AND hasDraft=true (so the parent can show a
//     "Draft recovered" toast).
//   * On formData change: autosaves debounced 600ms. draftStatus flips
//     to "saving" → "saved" briefly (so the parent can render a pill).
//   * `discard()` clears the IndexedDB entry AND resets state.
//   * `commit()` clears the draft after a successful submit (called by
//     parent on submission success).

import { useEffect, useRef, useState, useCallback } from "react";
import { saveDraft, getDraft, discardDraft } from "./draftStore";

const DEBOUNCE_MS = 600;

export function useDraft(formKey, initial, actorId) {
  const [formData, _setFormData] = useState(initial);
  const [draftStatus, setDraftStatus] = useState("idle");
  const [hasDraft, setHasDraft] = useState(false);
  const timerRef = useRef(null);
  const loadedRef = useRef(false);
  const lastSavedKeyRef = useRef(null);

  // Mount: try to load a draft.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const draft = await getDraft(actorId, formKey);
        if (!cancelled && draft) {
          _setFormData(draft);
          setHasDraft(true);
        }
      } finally {
        loadedRef.current = true;
        lastSavedKeyRef.current = JSON.stringify(formData);
      }
    })();
    return () => { cancelled = true; };
     
  }, [formKey, actorId]);

  // Autosave debounced.
  useEffect(() => {
    if (!loadedRef.current) return;
    const serialized = JSON.stringify(formData);
    // Skip noisy saves for identical state.
    if (serialized === lastSavedKeyRef.current) return;
    setDraftStatus("saving");
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      await saveDraft(actorId, formKey, formData);
      lastSavedKeyRef.current = serialized;
      setDraftStatus("saved");
      // Pill displays for ~1.2s then returns to idle.
      setTimeout(() => setDraftStatus("idle"), 1200);
    }, DEBOUNCE_MS);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [formData, formKey, actorId]);

  // Wrap setter to clear hasDraft once the user starts typing again
  // (acknowledges they've seen the recovery).
  const setFormData = useCallback((next) => {
    setHasDraft(false);
    _setFormData(next);
  }, []);

  const discard = useCallback(async () => {
    await discardDraft(actorId, formKey);
    _setFormData(initial);
    setHasDraft(false);
    setDraftStatus("idle");
    lastSavedKeyRef.current = JSON.stringify(initial);
  }, [actorId, formKey, initial]);

  const commit = useCallback(async () => {
    // Called by parent on successful submission — clears draft so the
    // form doesn't auto-rehydrate on next visit.
    await discardDraft(actorId, formKey);
    setHasDraft(false);
    setDraftStatus("idle");
  }, [actorId, formKey]);

  return { formData, setFormData, draftStatus, hasDraft, discard, commit };
}
