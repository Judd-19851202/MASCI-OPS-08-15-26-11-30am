// TRUST-DIAGNOSTICS-001 · Session-status pub/sub.
//
// Tiny event bus that the central axios interceptor publishes into and
// the SessionStatusOverlay subscribes to. Single source of truth so a
// storm of failing card-loaders collapses into ONE global modal
// instead of multiple "Failed to load…" toasts.
//
// Suppression rules baked in here so the overlay component stays dumb:
//   • Duplicate identical-kind events within DEBOUNCE_MS = 800 are
//     collapsed (cards firing in parallel produce one modal).
//   • A `success_loaded` event for ANY route clears any active overlay
//     (the system has just proven it can talk to the backend).
//   • Callers can explicitly clear via `clearSessionStatus()` after a
//     successful re-login.
//
// State exported as a plain object {kind, status, at} for React.

const DEBOUNCE_MS = 800;

let _state = { kind: null, status: null, at: 0 };
const _listeners = new Set();
let _lastEmitKind = null;
let _lastEmitAt = 0;

function _notify() {
  for (const cb of _listeners) {
    try { cb(_state); } catch { /* never break the bus */ }
  }
}

export function getSessionStatus() {
  return _state;
}

export function subscribeSessionStatus(cb) {
  if (typeof cb !== "function") return () => {};
  _listeners.add(cb);
  // Replay current state immediately so late mounts get the picture.
  try { cb(_state); } catch { /* */ }
  return () => { _listeners.delete(cb); };
}

/**
 * Publish a classification to the bus.
 *
 * @param {{kind: string|null, status?: number|null}} classification
 *   Output of classifyApiError(). `kind === null` is a no-op (per-call
 *   4xx that shouldn't preempt the global overlay).
 */
export function publishSessionStatus(classification) {
  if (!classification || !classification.kind) return;
  const kind = classification.kind;

  // success_loaded acts as an "all-clear" signal regardless of debounce.
  if (kind === "success_loaded") {
    if (_state.kind !== null) {
      _state = { kind: null, status: null, at: Date.now() };
      _notify();
    }
    _lastEmitKind = null;
    _lastEmitAt = Date.now();
    return;
  }
  if (kind === "success_empty") {
    // Don't change overlay state; empty success is legitimate data.
    return;
  }

  const now = Date.now();
  if (_lastEmitKind === kind && now - _lastEmitAt < DEBOUNCE_MS) {
    // Coalesce: same kind, within debounce window — keep timestamp,
    // do not re-render.
    return;
  }
  _lastEmitKind = kind;
  _lastEmitAt = now;
  _state = {
    kind,
    status: classification.status ?? null,
    at: now,
  };
  _notify();
}

/**
 * Explicit dismissal (e.g. user clicks "Stay Here" on Session Expired).
 * The overlay hides; the underlying error condition does not change.
 */
export function clearSessionStatus() {
  if (_state.kind === null) return;
  _state = { kind: null, status: null, at: Date.now() };
  _notify();
}

// For tests only — reset internal counters between cases.
export const _testReset = () => {
  _state = { kind: null, status: null, at: 0 };
  _listeners.clear();
  _lastEmitKind = null;
  _lastEmitAt = 0;
};

// TRUST-DIAGNOSTICS-001 · Expose a stable surface on window so ops
// scripts and Playwright tests can drive the overlay without poking
// webpack internals. Carries no tokens, no PII; just the UX state
// signal. Mirrors `publishSessionStatus` / `clearSessionStatus`.
if (typeof window !== "undefined") {
  window.__masciSessionBus = Object.freeze({
    publish: publishSessionStatus,
    clear: clearSessionStatus,
    get: getSessionStatus,
  });
}
