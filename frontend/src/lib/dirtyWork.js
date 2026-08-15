// dirtyWork.js — shared "is there unsaved field work right now?" registry.
//
// Single source of truth used by the Zero-Stale-Client release controller to
// decide whether it is SAFE to reload for a new release. Reuses the existing
// shared draft owner (useFormDraft) rather than adding a competing dirty-state
// system: useFormDraft calls markDirty/markClean with a stable key as its
// debounced dirty computation flips.
//
// A workflow is "protected" (do NOT auto-reload) when ANY key is dirty. When
// the last dirty key clears (a save/submit/close = safe boundary), subscribers
// are notified so a deferred update can apply.

const _dirty = new Set();
const _subs = new Set();

function _emit() {
  const any = _dirty.size > 0;
  for (const fn of _subs) {
    try { fn(any); } catch { /* never break a producer */ }
  }
}

export function markDirty(key) {
  if (!key) return;
  if (!_dirty.has(key)) {
    _dirty.add(key);
    _emit();
  }
}

export function markClean(key) {
  if (!key) return;
  if (_dirty.has(key)) {
    _dirty.delete(key);
    _emit();
  }
}

export function isAnyDirty() {
  return _dirty.size > 0;
}

export function dirtyKeys() {
  return Array.from(_dirty);
}

// Subscribe to dirty->clean / clean->dirty transitions. Returns unsubscribe.
export function subscribeDirty(fn) {
  _subs.add(fn);
  return () => _subs.delete(fn);
}

// Test-only reset.
export function _resetDirtyWork() {
  _dirty.clear();
  _subs.clear();
}
