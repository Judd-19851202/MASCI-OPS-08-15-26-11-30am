// resiliencyQueue.js — In-memory upload retry queue + IndexedDB
// persistence + foreground retry with exponential backoff.
//
// Phase J · Field Resiliency. Use:
//   await enqueueUpload({
//     method: "POST",
//     url: "/api/incidents",
//     headers: { ... },
//     body: { ... },
//     idempotencyKey: "<uuid>",
//     formKey: "incident-new",   // optional — for diagnostics
//   });
//
// Drains automatically on page focus + `online` event. Max 5 attempts
// with backoff: 1s · 2s · 4s · 8s · 16s. After 5 failures, item is
// marked `failed` (still kept for user inspection but not retried).
//
// The queue is INTENTIONALLY foreground-only. No service worker, no
// background sync API. iOS-safe. WebView-safe.

import { get, set, del } from "idb-keyval";
import { api } from "@/lib/api";
import { normalizeDailyReportPayload, formatUnrepairableErrors } from "../dailyReportPayloadRepair";

const QUEUE_KEY = "masci.resiliency.queue.v1";
const MAX_TRIES = 5;
const BACKOFFS_MS = [1000, 2000, 4000, 8000, 16000];

let _queue = null;        // in-memory mirror; null until first load
let _draining = false;
const _listeners = new Set();
const _itemListeners = new Map(); // idempotencyKey → Set<{onSuccess,onFail}>
let _retryTimer = null;

async function _load() {
  if (_queue !== null) return _queue;
  try {
    _queue = (await get(QUEUE_KEY)) || [];
  } catch {
    _queue = [];
  }
  return _queue;
}

async function _persist() {
  try {
    if (_queue && _queue.length > 0) {
      await set(QUEUE_KEY, _queue);
    } else {
      await del(QUEUE_KEY);
    }
  } catch {
    // ignore
  }
}

function _notify() {
  for (const cb of _listeners) {
    try { cb(_queue || []); } catch { /* ignore */ }
  }
}

/** Subscribe to queue changes. Returns unsubscribe fn. */
export function onQueueChange(cb) {
  _listeners.add(cb);
  // fire once with current state (load lazily)
  _load().then(() => cb(_queue || []));
  return () => _listeners.delete(cb);
}

/**
 * TRUST-1 · TF-011 · 2026-05-27.
 * Subscribe to delivery outcome for a single queued item, keyed by its
 * idempotency key. Used by long forms (NewDailyReport) to defer
 * discarding the IDB draft until the offline queue confirms a 2xx OR
 * gives up (status=failed after MAX_TRIES). Callback receives
 *   { ok: true,  data }                 on confirmed 2xx
 *   { ok: false, status: "failed", lastError }   when retries exhaust
 * Subscription auto-unregisters after firing once. Safe to call before
 * the item is enqueued — the listener will fire on the next drain.
 */
export function onQueueItemSettled(idempotencyKey, cb) {
  if (!idempotencyKey || typeof cb !== "function") return () => {};
  let set = _itemListeners.get(idempotencyKey);
  if (!set) { set = new Set(); _itemListeners.set(idempotencyKey, set); }
  set.add(cb);
  return () => {
    const s = _itemListeners.get(idempotencyKey);
    if (s) { s.delete(cb); if (s.size === 0) _itemListeners.delete(idempotencyKey); }
  };
}

function _notifyItem(idempotencyKey, payload) {
  const set = _itemListeners.get(idempotencyKey);
  if (!set) return;
  for (const cb of set) {
    try { cb(payload); } catch { /* ignore */ }
  }
  _itemListeners.delete(idempotencyKey);
}

/** Current pending count (excludes `failed` items). */
export function getQueueDepth() {
  if (!_queue) return 0;
  return _queue.filter((it) => it.status !== "failed").length;
}

export function getQueueItems() {
  return [...(_queue || [])];
}

/**
 * Add an upload to the queue. Tries once immediately; if it fails,
 * persists for retry. Returns {ok: true, data} on immediate success,
 * or {ok: false, queued: true} if queued for later retry.
 */
export async function enqueueUpload(item) {
  await _load();
  const entry = {
    id: item.idempotencyKey || _randId(),
    method: item.method || "POST",
    url: item.url,
    headers: item.headers || {},
    body: item.body,
    idempotencyKey: item.idempotencyKey,
    formKey: item.formKey,
    tries: 0,
    status: "pending",
    enqueuedAt: Date.now(),
    lastError: null,
  };
  // First attempt inline.
  try {
    const data = await _attempt(entry);
    return { ok: true, data };
  } catch (e) {
    entry.tries = 1;
    entry.lastError = _errMsg(e);
    _queue.push(entry);
    await _persist();
    _notify();
    _scheduleDrain();
    return { ok: false, queued: true, error: entry.lastError };
  }
}

async function _attempt(entry) {
  // OFFLINE-UPLOAD-002 · Per-formKey payload repair on every attempt.
  // The repaired body is sent to the network but the persisted entry
  // body is NEVER mutated, so a discard+restore round-trip remains
  // possible and no user-entered text is lost.
  let bodyToSend = entry.body;
  if ((entry.formKey || "") === "daily-report" || String(entry.formKey || "").startsWith("daily-report::")) {
    const repair = normalizeDailyReportPayload(entry.body);
    if (repair.errors.length > 0) {
      // Surface a field-level, human-readable failure instead of letting
      // the backend reply with a truncated Pydantic message. The drawer
      // already coerces and displays `lastError`.
      const err = new Error(
        `Daily Report has fields we can't auto-fix — ${formatUnrepairableErrors(repair.errors)}. Edit the report and resubmit.`,
      );
      err.code = "DR_PAYLOAD_UNREPAIRABLE";
      err.repairErrors = repair.errors;
      throw err;
    }
    bodyToSend = repair.body;
  }
  const config = {
    method: entry.method,
    url: entry.url,
    headers: {
      ...(entry.headers || {}),
      ...(entry.idempotencyKey
        ? { "Idempotency-Key": entry.idempotencyKey }
        : {}),
    },
    data: bodyToSend,
  };
  const r = await api.request(config);
  return r.data;
}

// OFFLINE-UPLOAD-002 · Pretty-print FastAPI / Pydantic 422 validation
// detail arrays into "<path>: <msg> (got <input>)". Falls through to
// whatever string-like message exists for non-422 errors.
function _prettyPydantic(detail) {
  if (!Array.isArray(detail)) return null;
  const parts = [];
  for (const d of detail) {
    if (!d || typeof d !== "object") continue;
    const loc = Array.isArray(d.loc) ? d.loc.filter((x) => x !== "body") : [];
    const path = loc.length > 0 ? loc.join(".") : "(body)";
    const msg = typeof d.msg === "string" ? d.msg : "invalid";
    const inputStr = d.input !== undefined
      ? ` (got ${typeof d.input === "string" ? `"${String(d.input).slice(0, 24)}"` : JSON.stringify(d.input).slice(0, 24)})`
      : "";
    parts.push(`${path}: ${msg}${inputStr}`);
  }
  if (parts.length === 0) return null;
  const head = parts.slice(0, 2).join("; ");
  const tail = parts.length > 2 ? ` (+${parts.length - 2} more)` : "";
  return head + tail;
}

function _errMsg(e) {
  if (!e) return "unknown";
  // FastAPI 422: detail is an array of { loc, msg, type, input }
  const detail = e.response?.data?.detail;
  if (Array.isArray(detail)) {
    const pretty = _prettyPydantic(detail);
    if (pretty) return pretty.slice(0, 240);
  }
  // Single-string detail (most other 4xx/5xx)
  if (typeof detail === "string" && detail.length > 0) return detail.slice(0, 240);
  // Object detail — coerce to JSON safely
  if (detail && typeof detail === "object") {
    try { return JSON.stringify(detail).slice(0, 240); } catch { /* */ }
  }
  if (typeof e.message === "string" && e.message.length > 0) return e.message.slice(0, 240);
  try { return String(e).slice(0, 240); } catch { return "error"; }
}

function _randId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function _scheduleDrain() {
  if (_retryTimer) clearTimeout(_retryTimer);
  // Use the next item's backoff timer, capped to MAX backoff.
  const next = (_queue || []).find((it) => it.status !== "failed");
  if (!next) return;
  const idx = Math.min(next.tries - 1, BACKOFFS_MS.length - 1);
  const delay = BACKOFFS_MS[Math.max(0, idx)];
  _retryTimer = setTimeout(() => { drainQueue(); }, delay);
}

/**
 * OFFLINE-UPLOAD-001 · Last-resort recovery.
 *
 * Wipes the entire queue. Only invoked from the DrawerErrorBoundary
 * fallback in QueueStatusPill when rendering individual items has
 * already failed — at that point per-item discard is unreliable
 * because synthetic ids may not match persisted entries.
 */
export async function clearQueue() {
  await _load();
  const before = _queue.length;
  _queue = [];
  await _persist();
  _notify();
  return { removed: before };
}

/**
 * OFFLINE-UPLOAD-001 · Manual discard path.
 *
 * Removes a single queue item by id (idempotency key or generated id).
 * Used by the operator's per-item "Discard" affordance in the
 * QueueStatusPill drawer so users can recover from a stuck or
 * malformed submission without blanking the UI.
 *
 * Contract:
 *   • ONLY called from operator UI; never from drains or listeners.
 *   • If the id matches no entry, this is a no-op.
 *   • Persists immediately and notifies subscribers.
 *   • Does NOT touch retry/backoff/MAX_TRIES logic.
 *
 * Returns { removed: <0|1> } so callers can show a toast if desired.
 */
export async function discardQueueItem(id) {
  if (!id) return { removed: 0 };
  await _load();
  const before = _queue.length;
  _queue = _queue.filter((it) => it && it.id !== id);
  const removed = before - _queue.length;
  if (removed > 0) {
    await _persist();
    _notify();
  }
  return { removed };
}

/**
 * DR-QUEUE-RETRY-001 · Manual re-arm path.
 *
 * Resets EVERY item currently in the `failed` terminal state back to
 * `pending` (tries=0, lastError cleared), then triggers a drain so the
 * re-armed items get a fresh retry lifecycle.
 *
 * Contract:
 *   • ONLY called from the operator's "Retry All" affordance — never
 *     from background drains or the `online` / `focus` listeners.
 *   • Automatic drainQueue() behavior is unchanged: it continues to
 *     skip items with status === "failed".
 *   • Idempotency-Key is still attached on every _attempt(), so a
 *     re-armed item that was actually delivered server-side will be
 *     deduplicated by the backend on the next try — no duplicates.
 *   • No backend, schema, or IndexedDB structure change.
 *
 * Returns { reset: <count>, drained: true } so callers can show a
 * confirmation toast if desired.
 */
export async function retryAllFailed() {
  await _load();
  let reset = 0;
  for (const it of _queue) {
    if (it.status === "failed") {
      it.status = "pending";
      it.tries = 0;
      it.lastError = null;
      reset += 1;
    }
  }
  if (reset > 0) {
    await _persist();
    _notify();
  }
  await drainQueue();
  return { reset, drained: true };
}

/**
 * Attempt every pending item in the queue. Items that exhaust
 * MAX_TRIES move to `failed` status.
 */
export async function drainQueue() {
  if (_draining) return;
  await _load();
  if (!navigator.onLine) {
    _scheduleDrain();
    return;
  }
  _draining = true;
  try {
    const remaining = [];
    for (const it of _queue) {
      if (it.status === "failed") {
        remaining.push(it);
        continue;
      }
      try {
        const data = await _attempt(it);
        // success → drop from queue + notify any listener so the
        // caller can finally commit() / discard the IDB draft.
        if (it.idempotencyKey) {
          _notifyItem(it.idempotencyKey, { ok: true, data });
        }
      } catch (e) {
        it.tries += 1;
        it.lastError = _errMsg(e);
        if (it.tries >= MAX_TRIES) {
          it.status = "failed";
          if (it.idempotencyKey) {
            _notifyItem(it.idempotencyKey, {
              ok: false, status: "failed", lastError: it.lastError,
            });
          }
        }
        remaining.push(it);
      }
    }
    _queue = remaining;
    await _persist();
    _notify();
    if (_queue.some((it) => it.status !== "failed")) {
      _scheduleDrain();
    }
  } finally {
    _draining = false;
  }
}

// Auto-drain on online + focus events.
if (typeof window !== "undefined") {
  window.addEventListener("online", () => { drainQueue(); });
  window.addEventListener("focus", () => { drainQueue(); });
}
