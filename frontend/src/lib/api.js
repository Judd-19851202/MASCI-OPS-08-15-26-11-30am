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
import { setMustChange, redirectToChangePassword } from "@/lib/mustChangePassword";
import { getDeviceId } from "@/lib/resiliency/deviceId";

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
  try {
    const deviceId = getDeviceId();
    if (deviceId) {
      config.headers["X-Device-Id"] = deviceId;
    }
  } catch (_e) { /* ignore */ }
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
// PROD-FRONTEND-ERROR-001 · Defense-in-depth: normalise Pydantic
// validation-detail arrays into a renderable string at the response
// interceptor BEFORE any caller's `catch` block touches `err.response
// .data.detail`. Prevents the "Objects are not valid as a React child"
// crash that occurred on production Safari 26.5 from arrays of
// {type, loc, msg, input, url} objects being passed to <toast.error>.
import { safeErrorMessage } from "./safeErrorMessage";
// TRUST-DIAGNOSTICS-001 · Classify every rejection and publish a
// single global signal so a multi-card storm becomes one clear modal
// instead of "SERVER UNREACHABLE" + N × "Failed to load…" toasts.
import { classifyApiError } from "./errorClassification";
import { publishSessionStatus } from "./sessionStatusBus";

api.interceptors.response.use(
  (res) => {
    // Positive signal: clears any active session-expired / outage modal
    // the moment the backend responds with a real payload. Cheap to do
    // on every successful 2xx.
    try {
      publishSessionStatus({ kind: "success_loaded", status: res?.status ?? 200 });
    } catch { /* never break the response path */ }
    return res;
  },
  (err) => {
    // Normalise validation-detail BEFORE the caller's catch sees it.
    const data = err?.response?.data;
    if (data && typeof data === "object") {
      const d = data.detail;
      const isPydantic =
        Array.isArray(d) || (d && typeof d === "object" && (d.msg || d.type));
      if (isPydantic) {
        try {
          // Store the safe string on `detail`. Keep the original raw
          // shape on `detail_raw` so debugging tools / Sentry breadcrumbs
          // can still inspect it without ever flowing into React.
          data.detail_raw = d;
          data.detail = safeErrorMessage(d, "Validation error — check your input");
        } catch { /* never crash the interceptor */ }
      }
    }

    // ─────────────────────────────────────────────────────────────
    // Track 15.14A · Layer 3 client handler — backend backstop sent
    // HTTP 403 with `{detail:{code:"PASSWORD_CHANGE_REQUIRED"}}`.
    // Detect, persist the per-portal flag, and bounce the user into
    // the right /change-password page. Idempotent + silent.
    // ─────────────────────────────────────────────────────────────
    try {
      if (err?.response?.status === 403) {
        const det = err?.response?.data?.detail;
        const code =
          (det && typeof det === "object" && det.code) ||
          (typeof det === "string" && det.includes("PASSWORD_CHANGE_REQUIRED")
            ? "PASSWORD_CHANGE_REQUIRED"
            : null);
        if (code === "PASSWORD_CHANGE_REQUIRED") {
          const cfgHdrs = err?.config?.headers || {};
          let portal = null;
          if (cfgHdrs["X-HR-Token"]) portal = "hr";
          else if (cfgHdrs["X-PM-Token"]) portal = "pm";
          else if (cfgHdrs["X-Shop-Token"]) portal = "shop";
          else if (cfgHdrs["X-Safety-Token"]) portal = "safety";
          else if (cfgHdrs["X-Dispatch-Token"]) portal = "dispatch";
          else if (cfgHdrs["X-FL-Token"]) portal = "fl";
          else if (cfgHdrs["X-Admin-Token"]) portal = "admin";
          if (!portal) {
            // Fall back to active portal from URL.
            const p = (typeof window !== "undefined" && window.location && window.location.pathname) || "";
            if (p.startsWith("/hr")) portal = "hr";
            else if (p.startsWith("/pm")) portal = "pm";
            else if (p.startsWith("/shop")) portal = "shop";
            else if (p.startsWith("/safety")) portal = "safety";
            else if (p.startsWith("/dispatch")) portal = "dispatch";
            else if (p.startsWith("/field-leadership")) portal = "fl";
            else if (p.startsWith("/admin")) portal = "admin";
          }
          if (portal) {
            setMustChange(portal, true);
            // Only redirect if we're not already on the change-password
            // route (avoid bounce loops).
            const here =
              typeof window !== "undefined" && window.location
                ? window.location.pathname
                : "";
            if (!/change-password/.test(here)) {
              redirectToChangePassword(portal);
            }
            // Stop session_status publish below — this is not an auth
            // failure, it's a flow gate.
            return Promise.reject(err);
          }
        }
      }
    } catch { /* never break interceptor */ }

    // TRACK 14.0-PLATFORM-STABILITY · Namespace-scoped 401 handling.
    //
    // The previous implementation cleared the matching portal token on
    // a namespaced 401 BUT still let the classification flow through to
    // `publishSessionStatus`, which raised a platform-wide "Session
    // Expired" modal. That made every background widget call that the
    // user wasn't authorized for (e.g. a Safety user's UI accidentally
    // hitting an admin-only widget) pop the modal over valid content.
    //
    // New rule: a namespaced 401 is a *localized* auth signal — clear
    // ONLY that namespace token and return without raising the global
    // overlay. The route guard for that portal will bounce the user
    // back to the correct login the next time they navigate inside it.
    // Other portal sessions stay live.
    //
    // TRACK 15.13E — Cross-portal session bleed protection.
    // Non-namespaced 401s (e.g. /api/daily-reports/{id}, /api/asset-care/*)
    // previously wiped EVERY portal token and broadcast a global
    // "Session Expired" modal. That blew up HR and Asset Admin
    // workflows in production whenever a read endpoint rejected a
    // valid portal token. The fix: infer the *active* portal from
    // window.location.pathname (the portal the user is actively in)
    // and scope the cleanup to that portal alone. Other portal
    // sessions stay live.
    const cfg = err.config || {};
    let _namespacedHandled = false;
    if (err?.response?.status === 401) {
      const url = String(cfg.url || "");
      const isAdminNamespace = url.startsWith("/admin/") || url.includes("/api/admin/");
      const isShopNamespace = url.startsWith("/shop/") || url.includes("/api/shop/");
      const isHrNamespace = url.startsWith("/hr/") || url.includes("/api/hr/");
      const isPmNamespace = url.startsWith("/pm/") || url.includes("/api/pm/");
      const isSafetyNamespace = url.startsWith("/safety/") || url.includes("/api/safety/");
      const isDispatchNamespace = url.startsWith("/dispatch/") || url.includes("/api/dispatch/");
      const isFlNamespace = url.includes("/field-leadership/portal");
      const isLeadershipNamespace = url.startsWith("/leadership/") || url.includes("/api/leadership/");
      const isSafetyFormsNamespace = url.includes("/safety-forms/");
      const isDevNamespace = url.startsWith("/dev/") || url.includes("/api/dev/");
      // TRACK 14.0-PLATFORM-STABILITY · Cross-portal helper endpoints
      // that legitimately 401 for non-admin viewers and whose
      // affordances are designed to silently hide on auth failure.
      // Treat their 401s exactly like a namespaced auth signal — no
      // global modal, no token wipe.
      const isWorkflowsHelper = url.startsWith("/workflows/") || url.includes("/api/workflows/");
      const isNotificationsHelper = url.startsWith("/notifications/") || url.includes("/api/notifications/");
      const isOperationsHelper = url.startsWith("/operations/") || url.includes("/api/operations/") || url.startsWith("/operations-center") || url.includes("/api/operations-center");
      const isCrossPortalHelper = isWorkflowsHelper || isNotificationsHelper || isOperationsHelper;

      if (isAdminNamespace) {
        if (cfg.headers?.["X-Admin-Token"]) clearAdminToken();
        _namespacedHandled = true;
      } else if (isShopNamespace) {
        if (cfg.headers?.["X-Shop-Token"]) clearShopToken();
        _namespacedHandled = true;
      } else if (isHrNamespace) {
        if (cfg.headers?.["X-HR-Token"]) clearHrToken();
        _namespacedHandled = true;
      } else if (isPmNamespace) {
        if (cfg.headers?.["X-PM-Token"]) clearPmToken();
        _namespacedHandled = true;
      } else if (isSafetyNamespace) {
        if (cfg.headers?.["X-Safety-Token"]) clearSafetyToken();
        _namespacedHandled = true;
      } else if (isDispatchNamespace) {
        if (cfg.headers?.["X-Dispatch-Token"]) clearDispatchToken();
        _namespacedHandled = true;
      } else if (isFlNamespace) {
        if (cfg.headers?.["X-FL-Token"]) clearFlToken();
        _namespacedHandled = true;
      } else if (isLeadershipNamespace) {
        if (cfg.headers?.["X-Leadership-Token"]) clearLeadershipToken();
        _namespacedHandled = true;
      } else if (isSafetyFormsNamespace) {
        if (cfg.headers?.["X-Safety-Forms-Token"]) clearSafetyFormsToken();
        _namespacedHandled = true;
      } else if (isDevNamespace) {
        if (cfg.headers?.["X-Dev-Token"]) clearDevToken();
        _namespacedHandled = true;
      } else if (isCrossPortalHelper) {
        // Cross-portal helper 401 — silent. Do NOT clear any tokens
        // (this would be wrong: the user may have a perfectly valid
        // portal session that just doesn't satisfy this helper).
        _namespacedHandled = true;
      } else {
        // TRACK 15.13E — Non-namespaced 401 (e.g. /api/daily-reports/{id},
        // /api/asset-care/*). Determine the *active portal* from
        // window.location.pathname so the cleanup is portal-scoped
        // instead of a global token wipe. Production failure mode the
        // previous "wipe everything" branch caused:
        //   • HR user reading a Daily Report → backend rejects (gate
        //     was admin-only) → frontend wipes HR token → user is
        //     kicked out of HR portal even though their session is fine.
        //   • Asset Admin reading Asset Care summary → same pattern.
        // The fix: only clear the active portal's token, and only
        // broadcast `session_expired` if the request actually carried
        // that token. Other portal sessions remain live.
        let activePortal = null;
        try {
          const p = (typeof window !== "undefined" && window.location && window.location.pathname) || "";
          if (p.startsWith("/admin/") || p === "/admin") activePortal = "admin";
          else if (p.startsWith("/hr/") || p === "/hr") activePortal = "hr";
          else if (p.startsWith("/shop/") || p === "/shop") activePortal = "shop";
          else if (p.startsWith("/pm/") || p === "/pm") activePortal = "pm";
          else if (p.startsWith("/safety/") || p === "/safety") activePortal = "safety";
          else if (p.startsWith("/dispatch/") || p === "/dispatch") activePortal = "dispatch";
          else if (p.startsWith("/field-leadership/") || p === "/field-leadership") activePortal = "fl";
          else if (p.startsWith("/leadership/") || p === "/leadership") activePortal = "leadership";
          else if (p.startsWith("/dev/") || p === "/dev") activePortal = "dev";
        } catch { /* keep activePortal = null */ }

        if (activePortal) {
          // TRACK 15.13H — Portal-scoped 401 absorption.
          //
          // A 401 from a single non-namespaced endpoint with the
          // active portal's token is OVERWHELMINGLY a "this user
          // lacks the role for this specific endpoint" signal
          // (e.g. HR hitting `/api/daily-reports/{id}/lifecycle`,
          // which is admin/PM-only by design). It is NOT proof
          // that the user's portal session expired.
          //
          // Rule: do NOT clear any token in this branch. The token
          // is still valid for every endpoint the user IS
          // authorized for. Just silence the global "Session
          // Expired" modal so a peripheral 401 cannot bounce the
          // user out of an otherwise-working session.
          //
          // If the token IS truly invalid, the next protected
          // call (or the next route-guard check on navigation)
          // will fail consistently and the route guard will route
          // them to the portal sign-in. We never lose them.
          //
          // Net effect for the production failure modes:
          //   • Lifecycle 401 for HR on a DR detail page →
          //     suppressed; HR session stays live.
          //   • Stale Shop background helper 401 while user is on
          //     /hr/* → suppressed; HR session unaffected.
          //   • Cross-portal helper 401 (already handled above) →
          //     unchanged.
          _namespacedHandled = true;
        } else {
          // No portal context (root, /login, etc.). Preserve the
          // legacy behavior of clearing every token the request
          // carried so the next protected click bounces to the right
          // login. This branch should be rare in production.
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
      }
    }
    // TRUST-DIAGNOSTICS-001 · Publish the classified failure to the
    // global session-status bus. The overlay component renders ONE
    // modal regardless of how many parallel loaders fail.
    //
    // Suppress the publish if:
    //  • caller opted out via `config.skipSessionStatus === true`
    //    (health probes, version checks, queue replays, background
    //    polling loaders — all marked via the explicit flag).
    //  • the 401 was already absorbed as a namespaced auth signal
    //    above (`_namespacedHandled === true`). The route guard for
    //    that portal owns the recovery UX; the global overlay would
    //    be a duplicate, misleading "Session Expired" over a still-
    //    valid foreground session in a different portal.
    try {
      if (!cfg.skipSessionStatus && !_namespacedHandled) {
        const classification = classifyApiError(err);
        publishSessionStatus(classification);
      }
    } catch { /* never break the response path */ }
    return Promise.reject(err);
  }
);
