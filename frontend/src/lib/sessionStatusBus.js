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
//     (the system has just proven it can talk to the backend) AND
//     lifts any user-ack suppression (session recovered).
//   • Callers can explicitly clear via `clearSessionStatus()` after a
//     successful re-login.
//
// TRACK 19.11 AMENDMENT · SESSION-EXPIRED LOOP FIX
// -----------------------------------------------------------------
// Field bug: on form pages (Daily Report / Equipment Pre-Op), an
// expired session caused the "Session Expired" modal to REOPEN on
// every subsequent keystroke because background pollers / roster
// refetches / autosaves fire 401s at intervals longer than the 800 ms
// debounce window. The user could dismiss "Stay Here" only to have
// the modal slam back in one second later.
//
// Fix: sticky **acknowledgment suppression** on auth-kind states.
// When the user explicitly dismisses SESSION_EXPIRED (or ACCESS_
// RESTRICTED) via `clearSessionStatus()`, remember the ack. Further
// publishes of that same kind are suppressed until:
//   1. A `success_loaded` event proves the session is repaired
//      (typically after "Log Back In" completes)
//   2. `resetSessionAck()` is called explicitly (login flows on
//      landing, or a fresh page load re-initializing the bus)
//
// Security-safe: does NOT extend an invalid session, does NOT hide
// the 401 from token-clearing logic in the interceptor. It only
// prevents the *UX modal* from thrashing on top of the operator's
// form work. All auth failures still result in tokens being cleared
// and route guards still bounce to login on next protected click.
//
// Draft-safe: does NOT touch autosave, does NOT clear draft state,
// does NOT block typing. Local drafts on the form page remain
// exactly as the user left them.
//
// State exported as a plain object {kind, status, at} for React.

const DEBOUNCE_MS = 800;

// Auth-kind states that carry sticky user-acknowledgment (once the
// user dismisses them, don't re-fire until the session recovers).
const ACK_STICKY_KINDS = new Set([
  "session_expired",
  "access_restricted",
]);

let _state = { kind: null, status: null, at: 0 };
const _listeners = new Set();
let _lastEmitKind = null;
let _lastEmitAt = 0;
// Set of ack-suppressed kinds. Once the user dismisses an auth kind,
// further publishes of THAT kind are ignored until session recovery.
let _ackSuppressed = new Set();

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

  // success_loaded acts as an "all-clear" signal for the visual
  // overlay. It CLEARS the modal if one is showing but does NOT lift
  // ack-suppression: a successful 2xx from a public / anonymous
  // endpoint (translations, health probes, public asset lookups)
  // does not actually prove the user's auth token is still valid.
  //
  // TRACK 22.4d · LEAVE-SITE / SESSION-EXPIRED LOOP ROOT CAUSE FIX
  // -----------------------------------------------------------
  // Field bug pattern: an operator on Pre-Op / Daily Report sees the
  // session-expired modal, dismisses it via "Stay Here", then every
  // few keystrokes the modal re-opens. Trace:
  //   1. 401 from an authed endpoint    → modal shows
  //   2. User clicks "Stay Here"        → ack added, modal hidden
  //   3. Public/anon endpoint returns 2xx (e.g. `/api/i18n/...`,
  //      `/api/public/masci-mark`, translations, or a background
  //      health probe) → `success_loaded` fires → OLD CODE cleared
  //      `_ackSuppressed`
  //   4. Next keystroke re-fires the authed picker → 401 → modal
  //      REOPENS because ack was wiped in step 3.
  //   5. Loop.
  //
  // Correct semantics: `success_loaded` cannot prove auth recovery
  // (the 2xx may be a public route). Only explicit re-auth
  // (`resetSessionAck()` on "Log Back In") or a fresh page load
  // may lift the sticky ack. This keeps operators typing in the
  // form without modal thrash while preserving all data-safety and
  // route-guard behavior.
  if (kind === "success_loaded") {
    if (_state.kind !== null) {
      _state = { kind: null, status: null, at: Date.now() };
      _notify();
    }
    _lastEmitKind = null;
    _lastEmitAt = Date.now();
    // NOTE: intentionally DO NOT clear `_ackSuppressed` here. See
    // block comment above for rationale.
    return;
  }
  if (kind === "success_empty") {
    // Don't change overlay state; empty success is legitimate data.
    return;
  }

  // TRACK 19.11 AMENDMENT — sticky ack-suppression. If the user has
  // already dismissed this exact auth kind, don't re-open the modal.
  // The condition that caused the 401 hasn't changed; the token wipe
  // in the interceptor is already done; showing the modal again on
  // every subsequent keystroke-triggered background 401 is pure UX
  // noise and destroys form usability at 5:30 AM.
  if (_ackSuppressed.has(kind)) {
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
 *
 * TRACK 19.11 AMENDMENT — dismissing an auth kind ALSO marks it as
 * ack-suppressed so it doesn't re-open the modal on every subsequent
 * background 401 while the operator finishes typing / signing.
 */
export function clearSessionStatus() {
  const dismissedKind = _state.kind;
  if (dismissedKind === null) return;
  if (ACK_STICKY_KINDS.has(dismissedKind)) {
    _ackSuppressed.add(dismissedKind);
  }
  _state = { kind: null, status: null, at: Date.now() };
  _notify();
}

/**
 * TRACK 19.11 AMENDMENT — explicit reset of ack-suppression.
 *
 * Called by:
 *   • Login pages on mount (fresh auth attempt should be able to
 *     re-open the modal if it fails again).
 *   • Explicit "Log Back In" primary action (before nav).
 *   • Tests.
 *
 * Does NOT clear overlay state — call `clearSessionStatus()` for that.
 */
export function resetSessionAck() {
  if (_ackSuppressed.size > 0) {
    _ackSuppressed = new Set();
  }
}

/**
 * Read-only introspection of the ack-suppression set.
 * Exposed for tests and diagnostics; NOT for UI decisions.
 */
export function getSessionAckState() {
  return {
    suppressed: Array.from(_ackSuppressed),
  };
}

// For tests only — reset internal counters between cases.
export const _testReset = () => {
  _state = { kind: null, status: null, at: 0 };
  _listeners.clear();
  _lastEmitKind = null;
  _lastEmitAt = 0;
  _ackSuppressed = new Set();
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
    resetAck: resetSessionAck,
    getAck: getSessionAckState,
  });
}
