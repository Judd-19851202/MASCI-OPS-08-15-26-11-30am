// TRUST-DIAGNOSTICS-001 · Global session/error overlay.
//
// One modal, four user-facing kinds:
//   • session_expired      — 401 from any protected endpoint
//   • access_restricted    — 403
//   • network_unreachable  — fetch failed / offline / timeout
//   • backend_unavailable  — 5xx
//
// Replaces the multi-card "Failed to load…" storm + the misleading
// "SERVER UNREACHABLE" banner that an expired session used to trigger.
//
// Mounted ONCE globally in App.js. Subscribes to sessionStatusBus.
// Suppresses itself on login/auth-portal routes so users mid-login
// don't see a "Session Expired" modal stacked on top of their form.
//
// Doctrine: /app/memory/TRUST_DIAGNOSTICS_001_CERTIFICATION.md

import { useEffect, useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AlertTriangle, Lock, WifiOff, ServerCrash, X } from "lucide-react";
import {
  subscribeSessionStatus,
  clearSessionStatus,
  resetSessionAck,
} from "@/lib/sessionStatusBus";
import { ERROR_KINDS } from "@/lib/errorClassification";
import { useT } from "@/lib/i18n";

// Routes where the overlay must NOT appear (would stack on top of an
// active login form and confuse the user).
const SUPPRESS_PREFIXES = [
  "/admin/login", "/login", "/safety-login", "/hr-login",
  "/dispatch/login", "/pm/login", "/shop/login",
  "/field-leadership/portal", "/field-leadership/login",
  "/auth", "/portal/login",
];

// Where to send the user when they tap "Log Back In". The overlay is
// generic; pick the safest entry point based on the current route.
function _loginRouteForCurrent(pathname) {
  if (pathname.startsWith("/admin")) return "/admin/login";
  if (pathname.startsWith("/safety")) return "/safety-login";
  if (pathname.startsWith("/hr")) return "/hr-login";
  if (pathname.startsWith("/dispatch")) return "/dispatch/login";
  if (pathname.startsWith("/pm")) return "/pm/login";
  if (pathname.startsWith("/shop")) return "/shop/login";
  if (pathname.startsWith("/field-leadership")) return "/field-leadership/portal";
  return "/admin/login";
}

const ICON_FOR = {
  [ERROR_KINDS.SESSION_EXPIRED]: Lock,
  [ERROR_KINDS.ACCESS_RESTRICTED]: AlertTriangle,
  [ERROR_KINDS.NETWORK_UNREACHABLE]: WifiOff,
  [ERROR_KINDS.BACKEND_UNAVAILABLE]: ServerCrash,
};

const ACCENT_FOR = {
  [ERROR_KINDS.SESSION_EXPIRED]: { ring: "border-amber-400", bg: "bg-amber-50", title: "text-amber-900", icon: "text-amber-600" },
  [ERROR_KINDS.ACCESS_RESTRICTED]: { ring: "border-slate-400", bg: "bg-slate-50", title: "text-slate-900", icon: "text-slate-600" },
  [ERROR_KINDS.NETWORK_UNREACHABLE]: { ring: "border-sky-400", bg: "bg-sky-50", title: "text-sky-900", icon: "text-sky-600" },
  [ERROR_KINDS.BACKEND_UNAVAILABLE]: { ring: "border-red-500", bg: "bg-red-50", title: "text-red-900", icon: "text-red-600" },
};

function _copy(state, t) {
  switch (state.kind) {
    case ERROR_KINDS.SESSION_EXPIRED:
      return {
        title: t("Session Expired"),
        body: t("Your login session has expired. No data has been lost. Please log back in to continue."),
        primary: t("Log Back In"),
        secondary: t("Stay Here"),
      };
    case ERROR_KINDS.ACCESS_RESTRICTED:
      return {
        title: t("Access Restricted"),
        body: t("Your account does not have permission to view this area."),
        primary: null,
        secondary: t("Dismiss"),
      };
    case ERROR_KINDS.NETWORK_UNREACHABLE:
      return {
        title: t("Connection Problem"),
        body: t("Your device cannot reach platform services right now. Any drafts or pending uploads remain protected locally."),
        primary: t("Retry"),
        secondary: t("Dismiss"),
      };
    case ERROR_KINDS.BACKEND_UNAVAILABLE:
      return {
        title: t("Services Temporarily Unavailable"),
        body: t("The server is reachable but returned an error. Try again shortly. Field drafts remain protected locally."),
        primary: t("Retry"),
        secondary: t("Dismiss"),
      };
    default:
      return null;
  }
}

export default function SessionStatusOverlay() {
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useT();
  const [state, setState] = useState({ kind: null, status: null });
  const [retryBusy, setRetryBusy] = useState(false);

  useEffect(() => {
    const unsub = subscribeSessionStatus(setState);
    return unsub;
  }, []);

  const onDismiss = useCallback(() => { clearSessionStatus(); }, []);
  const onPrimary = useCallback(async () => {
    if (state.kind === ERROR_KINDS.SESSION_EXPIRED) {
      // TRACK 19.11 AMENDMENT — user is explicitly re-authenticating.
      // Lift the ack-suppression so a genuinely fresh 401 after login
      // can raise the modal again.
      clearSessionStatus();
      resetSessionAck();
      navigate(_loginRouteForCurrent(location.pathname));
      return;
    }
    const retry = state?.meta?.retry;
    if (typeof retry === "function") {
      try {
        setRetryBusy(true);
        await Promise.resolve(retry());
      } finally {
        setRetryBusy(false);
      }
      return;
    }
    clearSessionStatus();
  }, [state, location.pathname, navigate]);

  // Suppress on login / portal routes — the user is mid-auth.
  const suppressed = SUPPRESS_PREFIXES.some((p) => location.pathname.startsWith(p));
  const copy = _copy(state, t);
  if (!copy || suppressed) return null;

  const Icon = ICON_FOR[state.kind] || AlertTriangle;
  const accent = ACCENT_FOR[state.kind] || ACCENT_FOR[ERROR_KINDS.NETWORK_UNREACHABLE];

  return (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="session-status-title"
      data-testid="session-status-overlay"
      data-kind={state.kind}
    >
      <div
        className={`w-full max-w-md rounded-lg border-2 ${accent.ring} ${accent.bg} shadow-2xl overflow-hidden`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-5 flex items-start gap-4">
          <Icon className={`w-8 h-8 shrink-0 ${accent.icon}`} aria-hidden />
          <div className="min-w-0 flex-1">
            <h2
              id="session-status-title"
              className={`text-lg font-black tracking-tight ${accent.title} mb-1`}
              data-testid="session-status-title"
            >
              {copy.title}
            </h2>
            <p className="text-sm text-slate-700 leading-snug" data-testid="session-status-body">
              {copy.body}
            </p>
          </div>
          <button
            type="button"
            onClick={onDismiss}
            className="p-1 -mr-1 -mt-1 text-slate-500 hover:text-slate-900 hover:bg-white rounded transition-colors shrink-0"
            aria-label={t("Close")}
            data-testid="session-status-close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="px-6 py-4 bg-white/60 border-t border-slate-200 flex flex-col-reverse sm:flex-row gap-2 sm:justify-end">
          <button
            type="button"
            onClick={onDismiss}
            className="px-4 py-2 rounded font-bold uppercase tracking-wider text-xs text-slate-700 hover:bg-slate-100 transition-colors"
            data-testid="session-status-secondary"
          >
            {copy.secondary}
          </button>
          {copy.primary && (
            <button
              type="button"
              onClick={onPrimary}
              disabled={retryBusy}
              className="px-4 py-2 rounded font-bold uppercase tracking-wider text-xs bg-slate-900 hover:bg-black text-white transition-colors"
              data-testid="session-status-primary"
            >
              {retryBusy ? t("Retrying…") : copy.primary}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
