// hrRoster.js — Track 19.03 · HR Employee Roster (canonical golden source)
//
// Single client-side gateway to the canonical HR roster endpoint
// (`GET /api/hr/employee-roster`). HR is gospel: any HR Save (create,
// patch, status change, reactivate) MUST instantly propagate to every
// operational picker on the page — Daily Reports, Safety Meetings,
// Pre-Ops, JHPs, Trench, QA/QC, Incident, Training, Academy, Dispatch,
// Fleet, Shop, Crew Builders, every dropdown / autocomplete / modal.
//
// Design contract (per operator directive):
//   * NO permanent in-memory cache. The previous EmployeeCombo /
//     trench EmployeePicker pattern stored the response in a module-
//     level `_cache` variable that lived for the entire SPA session —
//     once stale, a new HR add was invisible until full page reload.
//     That is the bug. We replace it with a short in-flight de-dup
//     ONLY (so 30 pickers mounting in the same render tick don't fire
//     30 requests), plus an event bus that bypasses all caching on
//     any HR write.
//   * Subscribers receive live updates the moment HR saves.
//   * Inactive / Terminated / Resigned / Retired employees are hidden
//     from NEW form pickers by default (endpoint enforces this).
//   * No hardcoded employee arrays. No frontend-only duplicate truth.
//   * Private HR fields (CDL, medical, SSN, DOB, email, phone) are
//     never returned by the canonical endpoint — server projection
//     guarantees this. Pickers never see private HR data.

import { api } from "@/lib/api";

const HR_ROSTER_EVENT = "hr:roster-changed";
const ENDPOINT = "/hr/employee-roster";

// In-flight de-dup ONLY. Cleared as soon as the request settles.
// Not a cache — purely a thundering-herd guard for batch picker
// mounts. The very next call after settlement re-fetches.
let _inflight = null;

// Most-recent successful snapshot, exposed to subscribers so a new
// picker mount can render immediately while a fresh read is in
// flight. Bus events from HR writes (`hr:roster-changed`) clear this
// before the next emit so stale items never linger.
let _lastSnapshot = null;
const _subscribers = new Set();

function _notify(items) {
  _lastSnapshot = items;
  for (const cb of _subscribers) {
    try {
      cb(items);
    } catch {
      // Subscriber errors must not break the bus.
    }
  }
}

/**
 * Fetch the canonical HR roster (active employees by default).
 * Returns an array of `{ id, name, preferred_name, employee_id,
 * crew, role, trade, department, lifecycle_status, is_active,
 * active, supervisor_name, supervisor_id, updated_at }` items.
 *
 * @param {object} opts
 * @param {boolean} opts.includeInactive  Include inactive/terminated
 *   employees. Default: false. Field pickers must leave this false.
 * @param {string} opts.role              Server-side role filter.
 * @param {string} opts.department        Server-side department filter.
 */
export async function fetchHrRoster(opts = {}) {
  const { includeInactive = false, role, department, q } = opts;
  const params = {};
  if (includeInactive) params.include_inactive = true;
  if (role) params.role = role;
  if (department) params.department = department;
  if (q) params.q = q;
  // De-dup ONLY when the same parameter shape is requested. The
  // overwhelmingly common call from pickers is the no-arg form,
  // which all share the same in-flight promise.
  const key = JSON.stringify(params);
  if (_inflight && _inflight.key === key) {
    return _inflight.promise;
  }
  const promise = api
    .get(ENDPOINT, { params, timeout: 30000 })
    .then((r) => {
      const items = Array.isArray(r?.data?.items) ? r.data.items : [];
      _notify(items);
      return items;
    })
    .catch(async (err) => {
      // TRACK 24.9 · Public-safe fallback.
      // Anonymous flows (public DR V3 at `/daily/new`) have no
      // portal token, so the auth-gated canonical endpoint returns
      // 401. Fall back to the public projection (name / id / trade
      // / role / crew / active only — no PII, enforced by lock
      // test). Any other error → return last known good snapshot
      // so pickers never poison an existing render.
      const status = err?.response?.status;
      if (status === 401) {
        try {
          const pub = await api.get(`${ENDPOINT}/public`, {
            params: (q ? { q } : {}),
            timeout: 30000,
            skipSessionStatus: true,
          });
          const items = Array.isArray(pub?.data?.items) ? pub.data.items : [];
          _notify(items);
          return items;
        } catch {
          return _lastSnapshot || [];
        }
      }
      return _lastSnapshot || [];
    })
    .finally(() => {
      _inflight = null;
    });
  _inflight = { key, promise };
  return promise;
}

/**
 * Subscribe a callback to live roster updates. The callback is
 * invoked immediately with the most recent snapshot (if any) and
 * again every time a fresh read settles or an HR Save fires the
 * `hr:roster-changed` bus event.
 *
 * Returns an unsubscribe function. Use inside `useEffect`.
 */
export function subscribeHrRoster(cb) {
  _subscribers.add(cb);
  // Replay last snapshot for instant render.
  if (_lastSnapshot) {
    try { cb(_lastSnapshot); } catch { /* ignore */ }
  }
  return () => _subscribers.delete(cb);
}

/**
 * Force-invalidate the snapshot and re-fetch. Called by `lib/
 * employeesApi.js` after every HR write so pickers see the change
 * before the user has time to switch tabs.
 */
export function invalidateHrRoster() {
  _lastSnapshot = null;
  _inflight = null;
  // Fire and forget — subscribers will get the fresh data via the
  // promise's `_notify` call when it settles.
  fetchHrRoster().catch(() => { /* swallow */ });
}

// Global event bus integration. Anything in the app may dispatch
// `window.dispatchEvent(new CustomEvent("hr:roster-changed"))` to
// instantly invalidate every picker — including legacy components
// outside the React tree.
if (typeof window !== "undefined" && !window.__hr_roster_bus_installed__) {
  window.__hr_roster_bus_installed__ = true;
  window.addEventListener(HR_ROSTER_EVENT, () => {
    invalidateHrRoster();
  });
}

/**
 * Convenience for HR writes — drop this anywhere a save lands.
 */
export function emitHrRosterChanged() {
  if (typeof window !== "undefined") {
    try {
      window.dispatchEvent(new CustomEvent(HR_ROSTER_EVENT));
    } catch {
      invalidateHrRoster();
    }
  } else {
    invalidateHrRoster();
  }
}
