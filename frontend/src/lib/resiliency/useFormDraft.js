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
  saveDraft, getDraftEntry, discardDraft,
  migrateLegacyDrafts, storeIdempotencyKey, getIdempotencyKey,
  clearIdempotencyKey,
} from "./draftStore";
import { getDeviceScopedActorId, getLegacyActorIds } from "./actorId";
import { emitDraftEvent } from "./draftTelemetry";
import { estimateQuota } from "./quotaProbe";

const DEBOUNCE_MS = 800;
const MAX_INTERVAL_MS = 10_000;
// TRUST-1 · TF-004 — surface a calm operator warning BEFORE a silent
// QuotaExceededError. The estimate API is cheap; probe once on mount
// and then every 60s while the form is open. Threshold tuned to
// give the operator ~20% headroom for a multi-photo daily report.
const QUOTA_WARN_RATIO = 0.8;
const QUOTA_PROBE_INTERVAL_MS = 60_000;

export function useFormDraft(formKey, data, actorId) {
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
  const migrationDoneRef = useRef(false);

  // Keep a live ref to the current `data` so the lifecycle listeners
  // (which close over no dep array) always flush the latest state.
  useEffect(() => { dataRef.current = data; }, [data]);

  // ── Mount: migrate legacy drafts + load any existing draft ────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const deviceActorId = getDeviceScopedActorId();
        // One-time legacy migration — re-key any token-derived
        // orphaned drafts under the new device id.
        if (!migrationDoneRef.current) {
          migrationDoneRef.current = true;
          try {
            const legacy = getLegacyActorIds();
            const r = await migrateLegacyDrafts(deviceActorId, legacy, formKey);
            if (r.migrated > 0) {
              emitDraftEvent("draft.actorId.rotated", {
                formKey,
                migratedDrafts: r.migrated,
                kept: r.kept,
              });
            }
          } catch { /* migration must never crash mount */ }
        }
        const entry = await getDraftEntry(deviceActorId, formKey);
        if (!cancelled && entry) {
          setPendingDraft(entry.form);
          setPendingSavedAt(entry.savedAt);
          // We can't reliably know whether the draft was originally
          // saved under a different actorId after migration (we
          // already merged keys), so we treat any post-migration
          // recovery as "potentially cross-token" if the operator's
          // current portal token differs from the device id.
          setPendingIsCrossToken(actorId && actorId !== deviceActorId);
          emitDraftEvent("draft.restore.offered", {
            formKey,
            ageSeconds: Math.floor((Date.now() - (entry.savedAt || 0)) / 1000),
            payloadBytes: JSON.stringify(entry.form || {}).length,
            isCrossToken: Boolean(actorId && actorId !== deviceActorId),
          });
        }
      } finally {
        if (!cancelled) {
          setLoaded(true);
          lastSavedKeyRef.current = JSON.stringify(data || {});
        }
      }
    })();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formKey]);

  // ── Core save routine — used by debounce, interval, and lifecycle.
  const _doSave = useCallback(async (trigger) => {
    const deviceActorId = getDeviceScopedActorId();
    const serialized = JSON.stringify(dataRef.current || {});
    if (serialized === lastSavedKeyRef.current) return;
    setDraftStatus("saving");
    const t0 = (typeof performance !== "undefined") ? performance.now() : Date.now();
    const r = await saveDraft(deviceActorId, formKey, dataRef.current);
    const dt = ((typeof performance !== "undefined") ? performance.now() : Date.now()) - t0;
    if (r.ok) {
      lastSavedKeyRef.current = serialized;
      lastSaveAtMsRef.current = Date.now();
      setLastSavedAt(r.savedAt);
      setLastError(null);
      setDraftStatus("saved");
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      idleTimerRef.current = setTimeout(() => setDraftStatus("idle"), 1500);
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
  }, [formKey]);

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
    await discardDraft(deviceActorId, formKey);
    await clearIdempotencyKey(deviceActorId, formKey);
    setPendingDraft(null);
    setPendingSavedAt(null);
    setDraftStatus("idle");
    setLastSavedAt(null);
    setLastError(null);
    lastSavedKeyRef.current = null;
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
