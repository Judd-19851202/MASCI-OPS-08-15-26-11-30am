// Track 19.16 · Phase B1 · Incident Report — Draft Persistence
// Every keystroke is snapshotted to localStorage under a stable draft
// key. Drafts survive tab crashes, browser restarts, and mobile app
// swaps. A draft is discarded only when the case is successfully
// submitted or the user explicitly clears it.

const KEY_PREFIX = "masci.incident_report.draft.v1";
const INDEX_KEY = `${KEY_PREFIX}.__index__`;

function _safeGet(k) {
  try { return window.localStorage.getItem(k); } catch { return null; }
}
function _safeSet(k, v) {
  try { window.localStorage.setItem(k, v); } catch { /* quota / unavailable */ }
}
function _safeRemove(k) {
  try { window.localStorage.removeItem(k); } catch { /* noop */ }
}

// Returns the ID of the currently-active draft (creates one if absent).
export function ensureActiveDraftId() {
  let id = _safeGet(INDEX_KEY);
  if (!id) {
    id = `dr_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    _safeSet(INDEX_KEY, id);
  }
  return id;
}

export function currentDraftId() {
  return _safeGet(INDEX_KEY) || null;
}

function _keyFor(id) {
  return `${KEY_PREFIX}.${id}`;
}

export function loadDraft(id) {
  if (!id) return null;
  const raw = _safeGet(_keyFor(id));
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function saveDraft(id, draft) {
  if (!id) return;
  const snap = {
    ...draft,
    __updated_at__: new Date().toISOString(),
  };
  _safeSet(_keyFor(id), JSON.stringify(snap));
}

export function clearDraft(id) {
  if (!id) return;
  _safeRemove(_keyFor(id));
  const active = _safeGet(INDEX_KEY);
  if (active === id) _safeRemove(INDEX_KEY);
}

export function hasDraft() {
  const id = currentDraftId();
  if (!id) return false;
  const d = loadDraft(id);
  return !!(d && (d.incident_type || Object.keys(d).length > 1));
}

export default {
  ensureActiveDraftId,
  currentDraftId,
  loadDraft,
  saveDraft,
  clearDraft,
  hasDraft,
};
