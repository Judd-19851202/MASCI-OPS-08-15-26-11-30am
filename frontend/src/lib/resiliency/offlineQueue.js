// offlineQueue.js — iter435 · Phase 31 · Pass B · Part 4.
//
// Generalised offline submit queue for operational write actions
// (lifecycle transitions, recovery state changes, short JSON form
// posts). Extracted from the iter421 driver-shift queue, made
// formKey-scoped so multiple workflows can share the primitive
// without colliding.
//
// Doctrine
// --------
// - **localStorage only.** No IDB, no Service Worker, no background
//   sync. Foreground replay only. iOS-safe.
// - **Max 3 in-flight items per formKey.** Drop oldest if exceeded.
// - **Replay strictly oldest → newest** on `online` event AND on
//   `replayQueue()` invocation.
// - **2xx OR 4xx clears the entry.** Operators cannot resolve a
//   stale 4xx from a quiet phone screen. 5xx + network errors keep.
// - **NO retry panel UI.** A tiny count getter is the only surface;
//   callers render their own calm "N waiting to send" indicator.
//
// API
// ---
//   enqueue(formKey, { method, url, headers, body }) → number (queue depth)
//   readQueue(formKey)                                → array
//   clearQueue(formKey)                               → void
//   replayQueue(formKey)                              → Promise<{ sent, kept, replayedAny }>
//   getQueueDepth(formKey)                            → number
//   onQueueChange(formKey, cb)                        → unsubscribe()
//
// Compatibility note: this module supersedes the per-page iter421
// driver shift queue. The old DriverShift helpers are re-implemented
// as thin shims over `enqueue / replayQueue` to preserve every
// behaviour bit (cap=3, oldest-first replay, 401 preservation).

import { migrateQueuedBody } from "./queuePayloadMigration";

const STORAGE_PREFIX = "masci.offline-queue.";
const DEFAULT_MAX = 3;
const _listeners = new Map(); // formKey → Set<cb>

function _key(formKey) {
  return `${STORAGE_PREFIX}${formKey}`;
}

function _notify(formKey) {
  const set = _listeners.get(formKey);
  if (!set) return;
  for (const cb of set) {
    try { cb(); } catch { /* ignore */ }
  }
}

export function readQueue(formKey) {
  if (!formKey) return [];
  try {
    const raw = localStorage.getItem(_key(formKey));
    if (!raw) return [];
    const arr = JSON.parse(raw);
    return Array.isArray(arr) ? arr : [];
  } catch {
    return [];
  }
}

function _write(formKey, items, max) {
  try {
    const capped = items.slice(-max);
    localStorage.setItem(_key(formKey), JSON.stringify(capped));
  } catch {
    /* localStorage unavailable — drop silently · operational continuity */
  }
  _notify(formKey);
}

export function clearQueue(formKey) {
  try { localStorage.removeItem(_key(formKey)); } catch { /* noop */ }
  _notify(formKey);
}

export function getQueueDepth(formKey) {
  return readQueue(formKey).length;
}

export function onQueueChange(formKey, cb) {
  let set = _listeners.get(formKey);
  if (!set) { set = new Set(); _listeners.set(formKey, set); }
  set.add(cb);
  return () => set.delete(cb);
}

/**
 * Enqueue an HTTP write for later replay. Returns the new queue depth
 * (capped to `max`, default 3).
 */
export function enqueue(formKey, entry, { max = DEFAULT_MAX } = {}) {
  if (!formKey || !entry || !entry.url) return 0;
  const q = readQueue(formKey);
  q.push({
    method: entry.method || "POST",
    url: entry.url,
    headers: entry.headers || {},
    body: entry.body,
    queued_at: new Date().toISOString(),
    meta: entry.meta || {},
  });
  _write(formKey, q, max);
  return Math.min(q.length, max);
}

const API = process.env.REACT_APP_BACKEND_URL;

async function _attempt(entry) {
  const url = entry.url.startsWith("http") ? entry.url : `${API}${entry.url}`;
  const opts = {
    method: entry.method || "POST",
    headers: {
      "Content-Type": "application/json",
      ...(entry.headers || {}),
    },
  };
  if (entry.body != null) {
    // P0-QUEUE-2026-08-13 · shared strip-only legacy-payload migration.
    let outBody = entry.body;
    if (typeof outBody !== "string") {
      try {
        outBody = migrateQueuedBody(outBody, entry.meta?.formKey || "").body;
      } catch { /* migration best-effort; never block a send */ }
    }
    opts.body = typeof outBody === "string" ? outBody : JSON.stringify(outBody);
  }
  return fetch(url, opts);
}

/**
 * Replay every queued entry for `formKey` strictly oldest → newest.
 * 2xx + 4xx clear the entry. 401 preserves (auth lost). 5xx + network
 * errors keep for next replay tick.
 */
export async function replayQueue(formKey, { max = DEFAULT_MAX } = {}) {
  const q = readQueue(formKey);
  if (q.length === 0) return { sent: 0, kept: 0, replayedAny: false };
  const remaining = [];
  let sent = 0;
  let replayedAny = false;
  for (const entry of q) {
    try {
      const r = await _attempt(entry);
      if (r.status === 401) {
        // Auth lost — preserve full queue.
        _write(formKey, q, max);
        return { sent, kept: q.length, replayedAny };
      }
      if (r.ok || (r.status >= 400 && r.status < 500)) {
        sent += 1;
        replayedAny = true;
      } else {
        remaining.push(entry);
      }
    } catch {
      remaining.push(entry);
    }
  }
  if (remaining.length === 0) {
    clearQueue(formKey);
  } else {
    _write(formKey, remaining, max);
  }
  return { sent, kept: remaining.length, replayedAny };
}

// Auto-replay on `online`. Per-formKey replay is also called manually
// by callers that own the form context.
const _allKnownFormKeys = new Set();

function _registerForReplay(formKey) {
  _allKnownFormKeys.add(formKey);
}

if (typeof window !== "undefined") {
  window.addEventListener("online", () => {
    for (const k of _allKnownFormKeys) { replayQueue(k); }
  });
}

// Optional helper for callers to opt their formKey into online auto-replay.
export function registerAutoReplay(formKey) {
  _registerForReplay(formKey);
}
