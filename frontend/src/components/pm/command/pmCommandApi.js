/**
 * pm/command/pmCommandApi.js — thin REST client for the PM Command
 * Center Phase 4A backend endpoints (/api/pm/command-center/*).
 *
 * Doctrine:
 *   - Routed through the shared `api` axios instance so the global
 *     interceptor handles namespace-aware token injection AND
 *     namespace-aware 401 absorption (see /app/frontend/src/lib/api.js).
 *   - Every call passes `skipSessionStatus: true` because these
 *     widgets are background dashboard fetches. A 401 (e.g. an
 *     admin without a PM token, or vice versa) must NEVER pop the
 *     global Session Expired modal over valid content — the widget
 *     just renders empty / "no data" locally.
 *   - All endpoints support an optional ?project_number=... filter
 *     so the operator can pin one project or view all assigned jobs.
 *
 * TRACK 14.0-RC1-FERRARI (2026-02-15): Migrated from raw `fetch` to
 * the shared axios `api` instance. The raw-fetch path produced
 * uncaught `Error: GET /api/pm/command-center/... → 401` lines in
 * the browser console every time an admin viewed a dashboard that
 * embedded a PM widget without an active PM token. Axios handles
 * these silently when `skipSessionStatus: true` is set.
 */
import { api } from "@/lib/api";
import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";

function q(params) {
  const usp = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v != null && v !== "") usp.set(k, String(v));
  });
  const s = usp.toString();
  return s ? `?${s}` : "";
}

async function _get(path, params) {
  // TRACK 14.0-RC1 · D2 PM Command Center 401-race fix.
  //
  // Before this guard the call fired immediately on mount even if
  // the user had no admin or PM token yet — producing a guaranteed
  // 401 in the browser console and on the backend access log. The
  // global interceptor silenced the modal (skipSessionStatus=true)
  // but the noise still polluted devtools and the stress-loop
  // console budget (iteration_515 reported 5×401 here).
  //
  // Rule: if NEITHER an admin token NOR a PM token exists in
  // localStorage at fetch time, return null instead of firing. The
  // RequirePm route guard guarantees one of these is present when
  // the page is actually mounted — this defensive guard only
  // matters during the millisecond between component mount and
  // hydration completing, AND for any future caller that mounts
  // this widget outside RequirePm.
  if (!getAdminToken() && !getPmToken()) {
    return null;
  }
  // skipSessionStatus prevents background widget failures (e.g. a
  // namespaced 401 because the viewer doesn't hold the PM token)
  // from raising the global Session Expired overlay.
  const r = await api.get(`${path}${q(params)}`, { skipSessionStatus: true });
  return r.data;
}

export const pmCommandApi = {
  overview:     (project_number)        => _get("/pm/command-center/overview", { project_number }),
  resources:    (project_number, limit = 1000) => _get("/pm/command-center/resources", { project_number, limit }),
  hauls:        (project_number, limit = 500)  => _get("/pm/command-center/hauls", { project_number, limit }),
  materials:    (project_number, days = 7)     => _get("/pm/command-center/materials", { project_number, days }),
  shopImpact:   (project_number)        => _get("/pm/command-center/shop-impact", { project_number }),
  safetyImpact: (project_number)        => _get("/pm/command-center/safety-impact", { project_number }),
  timeline:     (project_number, days = 7, limit = 300) => _get("/pm/command-center/timeline", { project_number, days, limit }),
};

export default pmCommandApi;
