// releaseUpdate.js — Zero-Stale-Client release delivery controller.
//
// Goal: after a production deploy, every open browser converges to the current
// authorized release WITHOUT the operator refreshing, clearing cache, or even
// knowing a release happened — and WITHOUT ever destroying unsaved field work.
//
// Reuses canonical owners (no duplicate systems):
//   • release identity  → GET /api/version (existing no-store endpoint; its
//     `deployable_content_fingerprint` changes on every real release).
//   • dirty-work signal → lib/dirtyWork (fed by the shared useFormDraft owner).
//   • multi-tab         → BroadcastChannel('masci-release').
//
// State machine (operational client-update states — NOT data-freshness/auth):
//   CURRENT | UPDATE_AVAILABLE | UPDATE_PENDING_DIRTY_WORK | UPDATING
//   | UPDATE_REQUIRED | OFFLINE | UPDATE_FAILED | UNKNOWN
//
// Fail-safe by construction: any uncertainty ⇒ UNKNOWN and NO reload. A reload
// only ever happens when a genuinely newer release is confirmed AND there is no
// dirty work AND the reload-loop guard permits it.

const API = process.env.REACT_APP_BACKEND_URL;

export const RELEASE_STATES = {
  CURRENT: "CURRENT",
  UPDATE_AVAILABLE: "UPDATE_AVAILABLE",
  UPDATE_PENDING_DIRTY_WORK: "UPDATE_PENDING_DIRTY_WORK",
  UPDATING: "UPDATING",
  UPDATE_REQUIRED: "UPDATE_REQUIRED",
  OFFLINE: "OFFLINE",
  UPDATE_FAILED: "UPDATE_FAILED",
  UNKNOWN: "UNKNOWN",
};

const PERIODIC_MS = 5 * 60 * 1000;      // low-cost long-lived cadence
const MIN_CHECK_GAP_MS = 15 * 1000;     // dedupe bursty triggers
const LOOP_GUARD_WINDOW_MS = 60 * 1000; // if a reload doesn't change the served
const LOOP_GUARD_MAX = 2;               // fingerprint within this window, stop.
const LOOP_KEY = "masci.release.reloadGuard";

let _bootFingerprint = null;   // the release this tab actually loaded
let _state = RELEASE_STATES.UNKNOWN;
let _target = null;            // fingerprint we want to converge to
let _lastCheckAt = 0;
let _inflight = null;
let _timer = null;
let _channel = null;
const _subs = new Set();

function _isDirty() {
  // Lazy require to avoid a hard import cycle in tests.
  try {
    // eslint-disable-next-line global-require
    const { isAnyDirty } = require("./dirtyWork");
    return isAnyDirty();
  } catch {
    return false;
  }
}

function _setState(next, extra = {}) {
  _state = next;
  for (const fn of _subs) {
    try { fn({ state: next, boot: _bootFingerprint, target: _target, ...extra }); } catch { /* noop */ }
  }
}

export function getReleaseState() {
  return { state: _state, boot: _bootFingerprint, target: _target };
}

export function subscribeReleaseState(fn) {
  _subs.add(fn);
  try { fn(getReleaseState()); } catch { /* noop */ }
  return () => _subs.delete(fn);
}

function _fingerprintOf(body) {
  // Canonical release identity from the existing /api/version contract. Prefer
  // the deployable fingerprint from release provenance (most release-accurate);
  // fall back to the served frontend build source hash. Both change on a real
  // release. Never invent a separate version number.
  const prov = body?.deployable_release_provenance || {};
  return (
    prov.build_deployable_fingerprint ||
    prov.authorized_deployable_fingerprint ||
    body?.frontend_build_source_hash ||
    body?.source_hash ||
    body?.release ||
    null
  );
}

async function _fetchFingerprint() {
  const r = await fetch(`${API}/api/version`, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  const body = await r.json();
  return { fp: _fingerprintOf(body), body };
}

function _readGuard() {
  try {
    const raw = sessionStorage.getItem(LOOP_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

// Returns true if we are allowed to reload toward `target` (loop-safe).
function _guardAllowsReload(target) {
  const now = Date.now();
  const g = _readGuard();
  if (!g || g.target !== target || now - g.first > LOOP_GUARD_WINDOW_MS) {
    try { sessionStorage.setItem(LOOP_KEY, JSON.stringify({ target, count: 1, first: now })); } catch { /* noop */ }
    return true;
  }
  if (g.count >= LOOP_GUARD_MAX) return false; // reload isn't sticking → stop
  try { sessionStorage.setItem(LOOP_KEY, JSON.stringify({ ...g, count: g.count + 1 })); } catch { /* noop */ }
  return true;
}

function _clearGuardIfConverged() {
  // On a normal load where boot == the released fingerprint, drop any guard.
  const g = _readGuard();
  if (g && g.target && _bootFingerprint && g.target === _bootFingerprint) {
    try { sessionStorage.removeItem(LOOP_KEY); } catch { /* noop */ }
  }
}

function _performReload(target) {
  if (!_guardAllowsReload(target)) {
    _setState(RELEASE_STATES.UPDATE_FAILED);
    return;
  }
  _setState(RELEASE_STATES.UPDATING);
  try { _channel && _channel.postMessage({ type: "updating", target }); } catch { /* noop */ }
  // Give subscribers a tick to paint an "updating" state, then reload.
  setTimeout(() => {
    try { window.location.reload(); } catch { /* noop */ }
  }, 60);
}

let _dirtySubBound = false;
function _ensureDirtySubscription() {
  if (_dirtySubBound) return;
  try {
    // eslint-disable-next-line global-require
    const { subscribeDirty } = require("./dirtyWork");
    subscribeDirty((anyDirty) => { if (!anyDirty) _maybeApply(); });
    _dirtySubBound = true;
  } catch { /* noop */ }
}

// Apply a detected update if it is safe. Called after every successful check
// and whenever dirty work clears at a safe boundary.
function _maybeApply() {
  if (!_target || _target === _bootFingerprint) return;
  if (_isDirty()) {
    _ensureDirtySubscription();
    _setState(RELEASE_STATES.UPDATE_PENDING_DIRTY_WORK);
    return;
  }
  _performReload(_target);
}

export async function checkNow(reason = "manual") {
  const now = Date.now();
  if (now - _lastCheckAt < MIN_CHECK_GAP_MS && reason !== "force") return _inflight;
  if (_inflight) return _inflight;
  if (typeof navigator !== "undefined" && navigator.onLine === false) {
    _setState(RELEASE_STATES.OFFLINE);
    return null;
  }
  _lastCheckAt = now;
  _inflight = (async () => {
    try {
      const { fp } = await _fetchFingerprint();
      if (!fp) { _setState(RELEASE_STATES.UNKNOWN); return; }
      if (!_bootFingerprint) {
        _bootFingerprint = fp;             // first successful check = boot anchor
        _clearGuardIfConverged();
        _setState(RELEASE_STATES.CURRENT);
        return;
      }
      if (fp !== _bootFingerprint) {
        _target = fp;
        _setState(RELEASE_STATES.UPDATE_AVAILABLE, { target: fp });
        _maybeApply();
      } else {
        _target = null;
        _setState(RELEASE_STATES.CURRENT);
      }
    } catch {
      // Network / endpoint failure → never claim CURRENT, never reload.
      _setState(navigator.onLine === false ? RELEASE_STATES.OFFLINE : RELEASE_STATES.UNKNOWN);
    } finally {
      _inflight = null;
    }
  })();
  return _inflight;
}

// Called by the UI when the operator explicitly chooses to update now (only
// offered once work is protected).
export function applyUpdateNow() {
  if (_target && _target !== _bootFingerprint) _performReload(_target);
  else checkNow("force");
}

let _started = false;
export function startReleaseWatch() {
  if (_started || typeof window === "undefined") return;
  _started = true;

  // Multi-tab coordination: if any tab is updating, others just note it; a
  // dirty tab never reloads because of another tab.
  try {
    if ("BroadcastChannel" in window) {
      _channel = new BroadcastChannel("masci-release");
      _channel.onmessage = (ev) => {
        if (ev?.data?.type === "updating" && ev.data.target) {
          _target = ev.data.target;
          _maybeApply(); // will defer if this tab is dirty
        }
      };
    }
  } catch { /* noop */ }

  // Lifecycle triggers (NOT just a timer): startup, tab visible, reconnect.
  checkNow("startup");
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") checkNow("visible");
  });
  window.addEventListener("focus", () => checkNow("focus"));
  window.addEventListener("online", () => checkNow("online"));
  window.addEventListener("pageshow", (e) => { if (e.persisted) checkNow("resume"); });

  // When the last dirty form clears (safe boundary), apply any pending update.
  _ensureDirtySubscription();

  _timer = setInterval(() => checkNow("periodic"), PERIODIC_MS);
}

export function stopReleaseWatch() {
  if (_timer) clearInterval(_timer);
  _timer = null;
  _started = false;
}

// Test-only reset.
export function _resetReleaseUpdate() {
  _bootFingerprint = null;
  _state = RELEASE_STATES.UNKNOWN;
  _target = null;
  _lastCheckAt = 0;
  _inflight = null;
  if (_timer) clearInterval(_timer);
  _timer = null;
  _started = false;
  _dirtySubBound = false;
  _subs.clear();
  try { sessionStorage.removeItem(LOOP_KEY); } catch { /* noop */ }
}

// Test-only seam to set the boot anchor deterministically.
export function _setBootFingerprintForTest(fp) { _bootFingerprint = fp; }
