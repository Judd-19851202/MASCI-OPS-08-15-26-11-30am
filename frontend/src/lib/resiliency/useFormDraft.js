// useFormDraft.js — iter440 · P0 field-incident remediation · 2026-05-27.
//
// Manual-restore autosave hook used by every long-form editor on the
// platform (NewDailyReport, NewIncident, NewInspection, HR Payroll
// Variance, DLS Day-1 Debrief, RecoveryAction).
//
// What changed at iter440
// -----------------------
// The autosave used to be a simple 800ms debounce + silent IDB write.
// The field returned a P0 report: drafts disappearing on iPhone
// Safari, restore loading stale work, current work lost. The
// remediation:
//
//   1. **Device-scoped IDB key.** Internally we now key on
//      `getDeviceScopedActorId()` so a token rotation does NOT orphan
//      the morning's draft. The `actorId` parameter is kept for API
//      compat and is used only for telemetry segmentation.
//
//   2. **Truthful status.** The pill now exposes a `"failed"` state
//      driven by the real success/failure of the IDB write. The
//      hook also returns `lastSavedAt` so the pill can render
//      "Saved 12s ago".
//
//   3. **iOS lifecycle handlers.** `visibilitychange (hidden)`,
//      `pagehide`, and `beforeunload` synchronously flush the
//      current form to IDB (bypassing the 800 ms debounce). This
//      catches the foreman who taps the home button mid-typing.
//
//   4. **Max-interval forced flush.** Every 10 s while the form is
//      dirty, a save is forced even if the operator hasn't stopped
//      typing. This bounds the worst-case data loss to 10 s.
//
//   5. **Legacy draft migration.** On first mount with the new code,
//      any drafts written under prior token-derived actor ids are
//      re-keyed under the device-scoped id (one-time, idempotent).
//
//   6. **Telemetry.** Every write / failure / lifecycle transition
//      emits a `draft.*` event to `/api/draft-telemetry` so we can
//      diagnose any future field report from the device side.

import { useEffect, useRef, useState, useCallback } from "react";
import {
  saveDraft, getDraftEntry, discardDraft, clearDraft,
  storeIdempotencyKey, getIdempotencyKey,
  clearIdempotencyKey,
} from "./draftStore";
import {
  getDeviceScopedActorId,
  getStableActorIdentity,
} from "./actorId";
import { emitDraftEvent } from "./draftTelemetry";
import { estimateQuota } from "./quotaProbe";
import { markPriorUsage } from "./priorUsage";

const DEBOUNCE_MS = 800;
const MAX_INTERVAL_MS = 10_000;
// TRUST-1 · TF-004 — surface a calm operator warning BEFORE a silent
// QuotaExceededError. The estimate API is cheap; probe once on mount
// and then every 60s while the form is open. Threshold tuned to
// give the operator ~20% headroom for a multi-photo daily report.
const QUOTA_WARN_RATIO = 0.8;
const QUOTA_PROBE_INTERVAL_MS = 60_000;

export function useFormDraft(_formKeyBase, data, actorId, options = {}) {
  // TRACK 26.11 · optional `scope` (e.g. `"26-07::2026-07-08"`) is
  // appended to the effective form key so drafts for different
  // (project, report_date) pairs don't overwrite each other on the
  // same device. Falls back to the ambient formKey when scope is
  // empty — preserving pre-26.11 behavior for the "no project yet"
  // prelude and for every module that doesn't opt into scoping.
  const rawScope = (options.scope || "").trim();
  const publicAnonymous = Boolean(options.publicAnonymous);
  const formKey = rawScope ? `${_formKeyBase}::${rawScope}` : _formKeyBase;

  const [pendingDraft, setPendingDraft] = useState(null);
  const [pendingSavedAt, setPendingSavedAt] = useState(null);
  const [pendingIsCrossToken, setPendingIsCrossToken] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [draftStatus, setDraftStatus] = useState("idle");
  const [lastSavedAt, setLastSavedAt] = useState(null);
  const [lastError, setLastError] = useState(null);
  // TRUST-1 · TF-004 — calm storage pressure surface. `null` until
  // first probe lands; { ratio, usageMb, quotaMb } once probed.
  const [quotaPressure, setQuotaPressure] = useState(null);

  const timerRef = useRef(null);
  const intervalRef = useRef(null);
  const lastSavedKeyRef = useRef(null);
  const lastSaveAtMsRef = useRef(0);
  const dataRef = useRef(data);
  const idleTimerRef = useRef(null);
  const hasLoadedScopeOnceRef = useRef(false);
  // Keep a live ref to the current `data` so the lifecycle listeners
  // (which close over no dep array) always flush the latest state.
  useEffect(() => { dataRef.current = data; }, [data]);

  // ── Mount: load only the exact current-scope draft ────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      let loadedEntry = null;
      try {
        const deviceActorId = getDeviceScopedActorId();
        const entry = await getDraftEntry(deviceActorId, formKey);
        loadedEntry = entry;
        // TRACK 19.04 · Form Session Isolation.
        // Only OFFER the draft if it was saved by the currently
        // signed-in portal actor. A draft saved by Actor A on this
        // device is invisible to Actor B — Actor B starts blank.
        // Legacy drafts (no `savedByActor` stamp) are treated as
        // trusted for backward compat but flagged cross-token so
        // the UI can render the "unknown author" affordance.
        const currentAuthActor = publicAnonymous ? deviceActorId : getStableActorIdentity();
        const draftAuthor = entry && entry.savedByActor;
        const allowAnonTransition = draftAuthor === "anon" || draftAuthor === deviceActorId;
        const authorMismatch = Boolean(
          entry && draftAuthor && draftAuthor !== currentAuthActor && !allowAnonTransition
        );
        if (!cancelled && entry && !authorMismatch) {
          setPendingDraft(entry.form);
          setPendingSavedAt(entry.savedAt);
          setPendingIsCrossToken(publicAnonymous ? false : Boolean(actorId && actorId !== deviceActorId));
          emitDraftEvent("draft.restore.offered", {
            formKey,
            ageSeconds: Math.floor((Date.now() - (entry.savedAt || 0)) / 1000),
            payloadBytes: JSON.stringify(entry.form || {}).length,
            isCrossToken: publicAnonymous ? false : Boolean(actorId && actorId !== deviceActorId),
          });
        } else if (!cancelled && entry && authorMismatch) {
          // Actor B on the same device — do NOT offer Actor A's
          // draft. Emit telemetry so we can measure how often the
          // isolation actually blocks a cross-actor bleed.
          emitDraftEvent("draft.restore.blocked_cross_actor", {
            formKey,
            ageSeconds: Math.floor((Date.now() - (entry.savedAt || 0)) / 1000),
            payloadBytes: JSON.stringify(entry.form || {}).length,
          });
        }
      } finally {
        if (!cancelled) {
          setLoaded(true);
          if (loadedEntry?.form) {
            lastSavedKeyRef.current = JSON.stringify(loadedEntry.form || {});
          } else if (hasLoadedScopeOnceRef.current) {
            // Scope can legitimately change mid-session (e.g. daily
            // report operator/project/date becoming known after the
            // operator starts typing). When that happens, preserve the
            // current in-memory form as dirty so the debounce writes it
            // under the newly-resolved scope instead of treating the
            // unsaved state as already persisted.
            lastSavedKeyRef.current = null;
          } else {
            lastSavedKeyRef.current = JSON.stringify(dataRef.current || {});
          }
          hasLoadedScopeOnceRef.current = true;
        }
      }
    })();
    return () => { cancelled = true; };
     
  }, [actorId, formKey, publicAnonymous]);

  // ── Core save routine — used by debounce, interval, and lifecycle.
  const _doSave = useCallback(async (trigger) => {
    const deviceActorId = getDeviceScopedActorId();
    const serialized = JSON.stringify(dataRef.current || {});
    if (serialized === lastSavedKeyRef.current) return;
    setDraftStatus("saving");
    const t0 = (typeof performance !== "undefined") ? performance.now() : Date.now();
    const r = await saveDraft(deviceActorId, formKey, dataRef.current, {
      savedByActor: publicAnonymous ? deviceActorId : getStableActorIdentity(),
    });
    const dt = ((typeof performance !== "undefined") ? performance.now() : Date.now()) - t0;
    if (r.ok) {
      lastSavedKeyRef.current = serialized;
      lastSaveAtMsRef.current = Date.now();
      setLastSavedAt(r.savedAt);
      setLastError(null);
      setDraftStatus("saved");
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      idleTimerRef.current = setTimeout(() => setDraftStatus("idle"), 1500);
      // TRUST-1 · TF-001 — record that this device has used the form
      // so a future returning-foreman session with empty IDB can be
      // distinguished from a genuinely first-time user.
      try { markPriorUsage(formKey); } catch { /* ignore */ }
      emitDraftEvent("draft.write.ok", {
        formKey,
        payloadBytes: serialized.length,
        latencyMs: Math.round(dt),
        trigger,
      });
    } else {
      setLastError({ message: r.error, name: r.errorName });
      setDraftStatus("failed");
      emitDraftEvent("draft.write.fail", {
        formKey,
        errorName: r.errorName,
        error: r.error,
        payloadBytes: serialized.length,
        trigger,
      });
    }
  }, [formKey, publicAnonymous]);

  // ── Autosave on data changes (debounced) ──────────────────────────
  useEffect(() => {
    if (!loaded) return;
    const serialized = JSON.stringify(data || {});
    if (serialized === lastSavedKeyRef.current) return;
    setDraftStatus((s) => (s === "failed" ? "failed" : "saving"));
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => { _doSave("debounce"); }, DEBOUNCE_MS);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [data, loaded, _doSave]);

  // ── Max-interval forced flush (every 10 s while dirty) ────────────
  useEffect(() => {
    if (!loaded) return;
    if (intervalRef.current) clearInterval(intervalRef.current);
    intervalRef.current = setInterval(() => {
      const serialized = JSON.stringify(dataRef.current || {});
      if (serialized === lastSavedKeyRef.current) return;
      if (Date.now() - lastSaveAtMsRef.current < MAX_INTERVAL_MS) return;
      _doSave("interval");
    }, MAX_INTERVAL_MS);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [loaded, _doSave]);

  // ── iOS lifecycle: visibilitychange + pagehide + beforeunload ─────
  useEffect(() => {
    if (!loaded) return;
    const flushOnLifecycle = (trigger) => {
      const serialized = JSON.stringify(dataRef.current || {});
      const dirty = serialized !== lastSavedKeyRef.current;
      emitDraftEvent("draft.lifecycle", {
        formKey,
        transition: trigger,
        pendingDirty: dirty,
      });
      if (dirty) { _doSave(trigger); }
    };
    const onVis = () => {
      if (document.visibilityState === "hidden") {
        flushOnLifecycle("visibilitychange");
      } else if (document.visibilityState === "visible") {
        emitDraftEvent("draft.lifecycle", {
          formKey,
          transition: "visible",
          pendingDirty: false,
        });
      }
    };
    const onHide = () => flushOnLifecycle("pagehide");
    const onBeforeUnload = () => flushOnLifecycle("beforeunload");
    document.addEventListener("visibilitychange", onVis);
    window.addEventListener("pagehide", onHide);
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => {
      document.removeEventListener("visibilitychange", onVis);
      window.removeEventListener("pagehide", onHide);
      window.removeEventListener("beforeunload", onBeforeUnload);
    };
  }, [loaded, formKey, _doSave]);

  // ── TRUST-1 · TF-004 · calm storage pressure probe ────────────────
  // Probes navigator.storage.estimate() once on mount and then every
  // 60s while the form is open. If usage/quota >= 80%, exposes the
  // numbers via `quotaPressure` so the page can render a small calm
  // chip BEFORE the next big write fails silently. Also fires a
  // single quota.warning telemetry event per session per form.
  useEffect(() => {
    if (!loaded) return undefined;
    let cancelled = false;
    let warnedOnce = false;
    const probe = async () => {
      try {
        const q = await estimateQuota();
        if (cancelled) return;
        if (!q || !q.supported || q.ratio == null) {
          setQuotaPressure(null);
          return;
        }
        if (q.ratio >= QUOTA_WARN_RATIO) {
          setQuotaPressure({
            ratio: q.ratio,
            usageMb: q.usageMb,
            quotaMb: q.quotaMb,
            freeMb: q.freeMb,
          });
          if (!warnedOnce) {
            warnedOnce = true;
            emitDraftEvent("quota.warning", {
              formKey,
              ratio: Number(q.ratio.toFixed(3)),
              usageMb: q.usageMb,
              quotaMb: q.quotaMb,
            });
          }
        } else {
          setQuotaPressure(null);
        }
      } catch { /* never throw from probe */ }
    };
    probe();
    const id = setInterval(probe, QUOTA_PROBE_INTERVAL_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, [loaded, formKey]);

  // ── restore() returns the pending draft and clears it ─────────────
  const restore = useCallback(() => {
    const d = pendingDraft;
    setPendingDraft(null);
    setPendingSavedAt(null);
    emitDraftEvent("draft.restore.action", { formKey, choice: "restore" });
    return d;
  }, [pendingDraft, formKey]);

  const discard = useCallback(async () => {
    const deviceActorId = getDeviceScopedActorId();
    await discardDraft(deviceActorId, formKey);
    setPendingDraft(null);
    setPendingSavedAt(null);
    setDraftStatus("idle");
    setLastSavedAt(null);
    setLastError(null);
    lastSavedKeyRef.current = JSON.stringify({});
    emitDraftEvent("draft.restore.action", { formKey, choice: "discard" });
  }, [formKey]);

  const commit = useCallback(async () => {
    const deviceActorId = getDeviceScopedActorId();
    await clearDraft(deviceActorId, formKey);
    await clearIdempotencyKey(deviceActorId, formKey);
    setPendingDraft(null);
    setPendingSavedAt(null);
    setDraftStatus("idle");
    setLastSavedAt(null);
    setLastError(null);
    lastSavedKeyRef.current = null;
    emitDraftEvent("draft.restore.action", { formKey, choice: "commit" });
  }, [formKey]);

  return {
    pendingDraft,
    pendingSavedAt,
    pendingIsCrossToken,
    loaded,
    draftStatus,
    lastSavedAt,
    lastError,
    quotaPressure,
    restore,
    discard,
    commit,
  };
}

// Helper for pages that submit offline-queued: persist the idempotency
// key in IDB so a reload mid-queue does not mint a duplicate.
export async function persistIdempotencyKey(formKey, key) {
  try {
    await storeIdempotencyKey(getDeviceScopedActorId(), formKey, key);
  } catch { /* ignore */ }
}

export async function loadIdempotencyKey(formKey) {
  try {
    return await getIdempotencyKey(getDeviceScopedActorId(), formKey);
  } catch {
    return null;
  }
}
