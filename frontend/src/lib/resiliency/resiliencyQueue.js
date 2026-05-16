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

const QUEUE_KEY = "masci.resiliency.queue.v1";
const MAX_TRIES = 5;
const BACKOFFS_MS = [1000, 2000, 4000, 8000, 16000];

let _queue = null;        // in-memory mirror; null until first load
let _draining = false;
const _listeners = new Set();
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
  const config = {
    method: entry.method,
    url: entry.url,
    headers: {
      ...(entry.headers || {}),
      ...(entry.idempotencyKey
        ? { "Idempotency-Key": entry.idempotencyKey }
        : {}),
    },
    data: entry.body,
  };
  const r = await api.request(config);
  return r.data;
}

function _errMsg(e) {
  if (!e) return "unknown";
  return (e.response?.data?.detail || e.message || String(e)).slice(0, 240);
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
        await _attempt(it);
        // success → drop from queue.
      } catch (e) {
        it.tries += 1;
        it.lastError = _errMsg(e);
        if (it.tries >= MAX_TRIES) {
          it.status = "failed";
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
