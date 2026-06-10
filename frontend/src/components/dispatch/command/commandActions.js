/**
 * commandActions.js · Phase 3.1 cross-tab actionability handoff.
 *
 * Persists a single "pending action" via sessionStorage so a click in
 * one tab survives the lazy mount of another tab and a re-render
 * cycle in React StrictMode.
 */
const KEY = "masci.dcc.pending_action";
const subs = new Set();

function _read() {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (_e) { return null; }
}

function _write(a) {
  try {
    if (a) sessionStorage.setItem(KEY, JSON.stringify(a));
    else sessionStorage.removeItem(KEY);
  } catch (_e) { /* noop */ }
}

export function publishCommandAction(action) {
  const withId = { ...action, id: action?.id || `${Date.now()}-${Math.random().toString(36).slice(2, 8)}` };
  _write(withId);
  for (const fn of subs) {
    try { fn(withId); } catch (_e) { /* noop */ }
  }
}

export function subscribeCommandAction(fn) {
  subs.add(fn);
  const pending = _read();
  if (pending) {
    try { fn(pending); } catch (_e) { /* noop */ }
  }
  return () => subs.delete(fn);
}

export function consumePendingCommandAction() {
  // Read-only: do NOT clear sessionStorage here. React StrictMode
  // double-mounts components in dev which would consume the action
  // before the second (live) mount sees it. The action is cleared
  // explicitly via clearPendingCommandAction() after the operator
  // sends or dismisses.
  return _read();
}

export function clearPendingCommandAction() {
  _write(null);
}
