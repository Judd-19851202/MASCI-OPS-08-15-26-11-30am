// Track 19.16 · Phase B2 · Incident submission offline queue.
// -----------------------------------------------------------------
// Reliable local queue with explicit retry + idempotency. Not a
// service-worker (deferred by choice — the constitution allows it).
//
// Contract:
//   * Every submission carries an `idempotency_key` — the server keys
//     duplicate posts to the same case, so re-tries can never create
//     two cases.
//   * When online: submits immediately, resolves with server response.
//   * When offline: writes to queue, resolves with a "queued" marker.
//   * On `online` window event: replays every queued item once.
//   * Failed replays remain in queue for the next opportunity.

import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const QUEUE_KEY = "masci.incident.public_queue.v1";

function _read() {
  try {
    return JSON.parse(window.localStorage.getItem(QUEUE_KEY) || "[]");
  } catch { return []; }
}
function _write(items) {
  try { window.localStorage.setItem(QUEUE_KEY, JSON.stringify(items)); } catch { /* noop */ }
}

export function isOnline() {
  if (typeof navigator === "undefined") return true;
  return navigator.onLine !== false;
}

export function newIdempotencyKey() {
  return `nm_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
}

// Submit a public near-miss with online / offline branching.
// Returns { status: "submitted" | "queued", case_number?, case_id?, idempotency_key }.
export async function submitPublicNearMiss(payload) {
  const idempotency_key = payload.idempotency_key || newIdempotencyKey();
  const body = { ...payload, idempotency_key };

  if (!isOnline()) {
    const queued = _read();
    // Guard against duplicate queueing by idempotency key.
    if (!queued.some((q) => q.idempotency_key === idempotency_key)) {
      queued.push({ body, queued_at: new Date().toISOString(), attempts: 0 });
      _write(queued);
    }
    return { status: "queued", idempotency_key };
  }

  try {
    const { data } = await axios.post(
      `${API}/public/near-miss`,
      body,
      {
        headers: { "Content-Type": "application/json", "X-Idempotency-Key": idempotency_key },
        timeout: 20000,
      },
    );
    return {
      status: "submitted",
      case_number: data.case_number,
      case_id: data.case_id,
      submitter_kind: data.submitter_kind,
      duplicate: data.duplicate,
      idempotency_key,
    };
  } catch (e) {
    // Network failure → queue for retry.
    const queued = _read();
    if (!queued.some((q) => q.idempotency_key === idempotency_key)) {
      queued.push({ body, queued_at: new Date().toISOString(), attempts: 1, error: e.message });
      _write(queued);
    }
    return { status: "queued", idempotency_key };
  }
}

// Flush every queued item. Called on `online` event and on kiosk mount.
export async function flushQueue(onEach) {
  if (!isOnline()) return { flushed: 0, remaining: _read().length };
  const items = _read();
  const stillQueued = [];
  let flushed = 0;
  for (const item of items) {
    try {
      const { data } = await axios.post(
        `${API}/public/near-miss`,
        item.body,
        {
          headers: {
            "Content-Type": "application/json",
            "X-Idempotency-Key": item.body.idempotency_key,
          },
          timeout: 20000,
        },
      );
      flushed += 1;
      if (typeof onEach === "function") {
        try { onEach({ ok: true, item, data }); } catch { /* noop */ }
      }
    } catch (e) {
      stillQueued.push({ ...item, attempts: (item.attempts || 0) + 1, error: e.message });
      if (typeof onEach === "function") {
        try { onEach({ ok: false, item, error: e.message }); } catch { /* noop */ }
      }
    }
  }
  _write(stillQueued);
  return { flushed, remaining: stillQueued.length };
}

export function queueLength() {
  return _read().length;
}

export function clearQueue() {
  _write([]);
}

// Attach a browser 'online' listener. Returns a cleanup function.
export function watchOnline(cb) {
  if (typeof window === "undefined") return () => {};
  const handler = () => cb && cb();
  window.addEventListener("online", handler);
  return () => window.removeEventListener("online", handler);
}
