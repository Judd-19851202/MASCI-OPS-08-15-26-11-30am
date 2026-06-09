import axios from "axios";
import { getAdminToken, clearAdminToken } from "@/lib/adminAuth";
import { getShopToken, clearShopToken } from "@/lib/shopAuth";
import { getPmToken, clearPmToken } from "@/lib/pmAuth";
import { getDevToken, clearDevToken } from "@/lib/devAuth";
import { getJwt, clearJwt } from "@/lib/jwtAuth";
import { getSafetyFormsToken, clearSafetyFormsToken } from "@/lib/safetyFormsAuth";
import { getLeadershipToken, clearLeadershipToken } from "@/lib/leadershipAuth";
import { getHrToken, clearHrToken } from "@/lib/hrAuth";
import { getFlToken, clearFlToken } from "@/lib/flAuth";
import { getSafetyToken, clearSafetyToken } from "@/lib/safetyAuth";
import { getDispatchToken, clearDispatchToken } from "@/lib/dispatchAuth";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API,
  headers: { "Content-Type": "application/json" },
  // No credentials — auth is sent via the Authorization / X-Admin-Token
  // headers so browsers don't reject the wildcard CORS that Cloudflare /
  // Emergent ingress applies. (See lib/jwtAuth.js for the rationale.)
  withCredentials: false,
  // Photos as base64 can be large — bump limits
  maxContentLength: 50 * 1024 * 1024,
  maxBodyLength: 50 * 1024 * 1024,
  // DR-BLOCKER-001B · R-BL-2 · client-side timeout.
  // Before this fix the axios instance had no `timeout`, so slow uploads
  // waited indefinitely for the Cloudflare/ingress 524 (~100s) before
  // throwing. That window let users mistake a hung upload for a working
  // one. 60s is a tighter, predictable budget — the resilient client
  // catches the abort and queues the payload to IDB. Field crews on
  // slow links now fail fast and get the queued banner immediately.
  // Doctrine: /app/memory/DR_BLOCKER_001A_FORENSIC_INVESTIGATION.md
  timeout: 60000,
});

// Attach Crew-Hub JWT, Safety-Admin token, and Shop token to every request.
api.interceptors.request.use((config) => {
  const adminTok = getAdminToken();
  if (adminTok) {
    config.headers["X-Admin-Token"] = adminTok;
  }
  const shopTok = getShopToken();
  if (shopTok) {
    config.headers["X-Shop-Token"] = shopTok;
  }
  const pmTok = getPmToken();
  if (pmTok) {
    config.headers["X-PM-Token"] = pmTok;
  }
  const devTok = getDevToken();
  if (devTok) {
    config.headers["X-Dev-Token"] = devTok;
  }
  const sfTok = getSafetyFormsToken();
  if (sfTok) {
    config.headers["X-Safety-Forms-Token"] = sfTok;
  }
  const leadTok = getLeadershipToken();
  if (leadTok) {
    config.headers["X-Leadership-Token"] = leadTok;
  }
  const hrTok = getHrToken();
  if (hrTok) {
    config.headers["X-HR-Token"] = hrTok;
  }
  const flTok = getFlToken();
  if (flTok) {
    config.headers["X-FL-Token"] = flTok;
  }
  const safetyTok = getSafetyToken();
  if (safetyTok) {
    config.headers["X-Safety-Token"] = safetyTok;
  }
  const dispatchTok = getDispatchToken();
  if (dispatchTok) {
    config.headers["X-Dispatch-Token"] = dispatchTok;
  }
  // iter375 · Phase 4B · directory session token (used by MFA management routes)
  try {
    const dirTok = window.localStorage.getItem("masci.directory.token") ||
                   window.sessionStorage.getItem("masci.directory.token");
    if (dirTok) {
      config.headers["X-Directory-Token"] = dirTok;
    }
  } catch (_e) { /* ignore */ }
  const jwt = getJwt();
  if (jwt && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${jwt}`;
  }
  return config;
});

// On 401, drop whichever token the request was using so the next protected
// route click bounces back to its login page. We don't redirect here — the
// route guards handle navigation cleanly.
//
// Iter520 · Phase V.5 · P0-2A — namespace-aware token clearing. Failures on
// `/api/admin/*` only clear the admin token; non-admin session tokens (PM,
// Shop, HR, etc.) survive. Otherwise a single failed admin-side widget
// inside a PM-or-Shop dashboard would kick the user out of their portal.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      const cfg = err.config || {};
      const url = String(cfg.url || "");
      const isAdminNamespace = url.startsWith("/admin/") || url.includes("/api/admin/");
      const isShopNamespace = url.startsWith("/shop/") || url.includes("/api/shop/");
      const isHrNamespace = url.startsWith("/hr/") || url.includes("/api/hr/");

      // If the 401 came from a namespaced route, only clear the matching
      // namespace token. The user's non-admin session must survive.
      if (isAdminNamespace) {
        if (cfg.headers?.["X-Admin-Token"]) clearAdminToken();
        return Promise.reject(err);
      }
      if (isShopNamespace) {
        if (cfg.headers?.["X-Shop-Token"]) clearShopToken();
        return Promise.reject(err);
      }
      if (isHrNamespace) {
        if (cfg.headers?.["X-HR-Token"]) clearHrToken();
        return Promise.reject(err);
      }

      // Non-namespaced 401 (e.g. /api/daily-reports/{id} rejected by a
      // top-level gate) — preserve the legacy behavior of clearing every
      // token the request carried so the next protected click bounces to
      // the right login.
      if (cfg.headers?.["X-Admin-Token"]) clearAdminToken();
      if (cfg.headers?.["X-Shop-Token"]) clearShopToken();
      if (cfg.headers?.["X-PM-Token"]) clearPmToken();
      if (cfg.headers?.["X-Dev-Token"]) clearDevToken();
      if (cfg.headers?.["X-Safety-Forms-Token"]) clearSafetyFormsToken();
      if (cfg.headers?.["X-Leadership-Token"]) clearLeadershipToken();
      if (cfg.headers?.["X-HR-Token"]) clearHrToken();
      if (cfg.headers?.["X-Safety-Token"]) clearSafetyToken();
      if (cfg.headers?.["X-Dispatch-Token"]) clearDispatchToken();
      if (cfg.headers?.["X-FL-Token"]) clearFlToken();
      if (cfg.headers?.Authorization) clearJwt();
    }
    return Promise.reject(err);
  }
);
