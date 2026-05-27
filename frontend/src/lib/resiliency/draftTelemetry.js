// draftTelemetry.js — P0 field-incident remediation · 2026-05-27.
//
// Client-side append-only telemetry buffer for the form-draft /
// autosave subsystem. NEVER logs form content — only sizes, error
// names, timestamps, page-lifecycle transitions.
//
// Flow:
//   emitDraftEvent("draft.write.ok", { trigger, payloadBytes })
//     → push into in-memory ring buffer (cap 200)
//     → debounce 5s → batch POST /api/draft-telemetry
//
//   pagehide:
//     → navigator.sendBeacon synchronous flush (cap 50 events / batch)
//
//   online:
//     → immediate flush
//
// Failure mode is silent. Telemetry MUST NEVER block the autosave
// critical path.

import { getDeviceId } from "./deviceId";
import { getActorId } from "./actorId";

const API = process.env.REACT_APP_BACKEND_URL;
const ENDPOINT = "/api/draft-telemetry";
const BUFFER_CAP = 200;
const BATCH_CAP = 50;
const FLUSH_DEBOUNCE_MS = 5_000;
const RETRY_BACKOFF_MS = 30_000;

const _buf = [];
let _flushTimer = null;
let _backoffTimer = null;
let _flushing = false;

function _portalToken() {
  // Pick whichever live portal token is present; the backend accepts
  // any. We don't pin to one because field operators move across
  // portals.
  try {
    // Local imports to avoid bundler cycles.
    const ks = [
      "admin_token", "pm_token", "hr_token", "safety_token",
      "dispatch_token", "leadership_token", "shop_token",
    ];
    for (const k of ks) {
      try {
        const v = localStorage.getItem(k);
        if (v) return [k, v];
      } catch { /* ignore */ }
    }
  } catch { /* ignore */ }
  return [null, null];
}

function _tokenHeader() {
  const [k, v] = _portalToken();
  if (!k || !v) return null;
  const headerName = {
    admin_token: "X-Admin-Token",
    pm_token: "X-Pm-Token",
    hr_token: "X-Hr-Token",
    safety_token: "X-Safety-Token",
    dispatch_token: "X-Dispatch-Token",
    leadership_token: "X-Leadership-Token",
    shop_token: "X-Shop-Token",
  }[k];
  return headerName ? { [headerName]: v } : null;
}

function _uuid() {
  try {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
  } catch { /* ignore */ }
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function emitDraftEvent(eventName, meta) {
  if (!eventName) return;
  try {
    const evt = {
      eventId: _uuid(),
      event: eventName,
      actorId: getActorId(),
      deviceId: getDeviceId(),
      formKey: (meta && meta.formKey) || "unknown",
      ts: Date.now(),
      meta: meta || {},
    };
    // formKey lives at the top-level on the wire — keep it out of meta.
    if (evt.meta.formKey) {
      const { formKey, ...rest } = evt.meta;
      evt.formKey = formKey;
      evt.meta = rest;
    }
    if (_buf.length >= BUFFER_CAP) _buf.shift();
    _buf.push(evt);
    _scheduleFlush();
  } catch { /* never throw from telemetry */ }
}

function _scheduleFlush() {
  if (_flushTimer || _backoffTimer) return;
  _flushTimer = setTimeout(() => {
    _flushTimer = null;
    flushDraftTelemetry();
  }, FLUSH_DEBOUNCE_MS);
}

async function _postBatch(batch) {
  if (!API || !batch.length) return false;
  const headers = { "Content-Type": "application/json" };
  // iter441 — POST anonymously when no portal token is present.
  // The P0 population (foremen on /daily/submit via public link)
  // carry no token; we still need their telemetry to land. Backend
  // accepts anonymous batches and rate-limits per device.
  const tok = _tokenHeader();
  if (tok) Object.assign(headers, tok);
  try {
    const r = await fetch(`${API}${ENDPOINT}`, {
      method: "POST",
      headers,
      body: JSON.stringify({ batch }),
      keepalive: true,
    });
    return r.ok;
  } catch {
    return false;
  }
}

export async function flushDraftTelemetry() {
  if (_flushing) return;
  if (!_buf.length) return;
  _flushing = true;
  try {
    while (_buf.length) {
      const batch = _buf.splice(0, BATCH_CAP);
      const ok = await _postBatch(batch);
      if (!ok) {
        // Restore the unsent batch and back off.
        _buf.unshift(...batch);
        if (_backoffTimer) clearTimeout(_backoffTimer);
        _backoffTimer = setTimeout(() => {
          _backoffTimer = null;
          flushDraftTelemetry();
        }, RETRY_BACKOFF_MS);
        break;
      }
    }
  } finally {
    _flushing = false;
  }
}

// Synchronous flush via navigator.sendBeacon — for pagehide. We do
// NOT await; sendBeacon is fire-and-forget from the page's POV.
export function flushDraftTelemetryBeacon() {
  if (!API || !_buf.length) return;
  try {
    if (typeof navigator === "undefined" || !navigator.sendBeacon) return;
    const tok = _tokenHeader();
    if (!tok) return;
    // sendBeacon does not allow custom headers. We embed the token
    // header as a query-string fallback ONLY for telemetry; the
    // server accepts it via the same require_any_portal_token dep.
    // To stay simple, we use a Blob with type application/json and
    // pass the token via querystring — but our backend currently
    // reads only headers. Therefore: emit a best-effort fetch
    // with keepalive: true instead (Safari supports this).
    const batch = _buf.splice(0, BATCH_CAP);
    const body = JSON.stringify({ batch });
    try {
      // keepalive: true is the iOS Safari way to flush on pagehide.
      fetch(`${API}${ENDPOINT}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...tok },
        body,
        keepalive: true,
      });
    } catch { /* never throw from beacon */ }
  } catch { /* ignore */ }
}

// Wire up online/pagehide listeners once per module load.
if (typeof window !== "undefined") {
  try {
    window.addEventListener("online", () => { flushDraftTelemetry(); });
    window.addEventListener("pagehide", () => { flushDraftTelemetryBeacon(); });
    document.addEventListener("visibilitychange", () => {
      if (document.visibilityState === "hidden") {
        flushDraftTelemetryBeacon();
      }
    });
  } catch { /* ignore */ }
}

// Test helper.
export function _drainBufferForTests() {
  const out = _buf.slice();
  _buf.length = 0;
  return out;
}
