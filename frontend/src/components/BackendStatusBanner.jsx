import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";
import { useCaptureMode } from "@/lib/captureMode";
import { subscribeSessionStatus } from "@/lib/sessionStatusBus";
import { ERROR_KINDS } from "@/lib/errorClassification";

/**
 * BackendStatusBanner
 * -------------------
 * Field-crew-friendly red banner that appears at the top of EVERY page when
 * the production backend is unreachable. Replaces the confusing "Network
 * Error" / "Could not save" toast spam users used to see during prod 520s.
 *
 *  - Polls /api/health every 15 seconds.
 *  - 1st failure = silent (could be a flake). 2nd consecutive failure = banner.
 *  - When the backend recovers, banner stays visible briefly with a green
 *    "Back online" tick so users see the recovery, then hides itself.
 *  - Hidden in print.
 *
 * Mounted once globally in App.js. Renders nothing when status is healthy.
 */
const POLL_MS = 15000;

export default function BackendStatusBanner() {
  // null = unknown, "up" = healthy, "down" = unreachable, "recovered" = just came back
  const [status, setStatus] = useState(null);
  const captureMode = useCaptureMode();
  // TRUST-DIAGNOSTICS-001 · Track the global session-status bus so we
  // can suppress this banner when the overlay is already showing a
  // clearer per-condition message (Session Expired / Access Restricted /
  // Connection Problem / Services Unavailable). Prevents the same
  // network/5xx event from producing both a banner AND a modal.
  const [overlayOwnsView, setOverlayOwnsView] = useState(false);
  useEffect(() => {
    const unsub = subscribeSessionStatus((s) => {
      setOverlayOwnsView(s.kind === ERROR_KINDS.SESSION_EXPIRED ||
                         s.kind === ERROR_KINDS.ACCESS_RESTRICTED ||
                         s.kind === ERROR_KINDS.NETWORK_UNREACHABLE ||
                         s.kind === ERROR_KINDS.BACKEND_UNAVAILABLE);
    });
    return unsub;
  }, []);

  useEffect(() => {
    const url = `${process.env.REACT_APP_BACKEND_URL}/api/health`;
    let consecutiveFailures = 0;
    let recoveredTimer = null;

    const probe = async () => {
      try {
        const ctrl = new AbortController();
        const t = setTimeout(() => ctrl.abort(), 8000);
        const r = await fetch(url, {
          method: "GET",
          cache: "no-store",
          credentials: "omit",
          signal: ctrl.signal,
        });
        clearTimeout(t);
        if (r.ok) {
          consecutiveFailures = 0;
          setStatus((prev) => {
            if (prev === "down") {
              if (recoveredTimer) clearTimeout(recoveredTimer);
              recoveredTimer = setTimeout(() => setStatus("up"), 6000);
              return "recovered";
            }
            return "up";
          });
          return;
        }
        consecutiveFailures += 1;
      } catch {
        consecutiveFailures += 1;
      }
      // Only flip to "down" after 2+ consecutive failures (avoids flicker on
      // single-request flakes).
      if (consecutiveFailures >= 2) setStatus("down");
    };

    probe();
    // TRACK 14.0-RC1-PERF: Pause when tab is hidden. The probe runs
    // immediately on focus so backgrounded tabs that come forward see
    // the current banner state without waiting up to 15s.
    const tick = () => {
      if (document.visibilityState === "visible") probe();
    };
    const interval = setInterval(tick, POLL_MS);
    const onVis = () => {
      if (document.visibilityState === "visible") probe();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", onVis);
      if (recoveredTimer) clearTimeout(recoveredTimer);
    };
  }, []);

  // iter347 · capture-mode hides chrome so promo clips stay clean.
  if (captureMode) return null;
  if (status !== "down" && status !== "recovered") return null;
  // TRUST-DIAGNOSTICS-001 · Defer to the overlay when it's already
  // explaining the same condition. Only one platform-wide message
  // about reachability/auth should ever be on screen.
  if (overlayOwnsView) return null;

  const isDown = status === "down";

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-[100] print:hidden ${
        isDown ? "bg-red-700" : "bg-emerald-600"
      } text-white shadow-lg`}
      role="alert"
      data-testid="backend-status-banner"
    >
      <div className="max-w-screen-xl mx-auto px-4 py-2 flex items-center gap-3 text-sm font-bold">
        {isDown ? (
          <AlertTriangle className="w-5 h-5 shrink-0 animate-pulse" />
        ) : (
          <CheckCircle2 className="w-5 h-5 shrink-0" />
        )}
        <div className="flex-1 leading-tight">
          {isDown ? (
            <>
              <span className="font-display tracking-wide uppercase">
                Server Unreachable —
              </span>{" "}
              The MASCI backend is down. Your form data is safe — wait ~60s and
              try again. Reports won&apos;t save until this banner disappears.
            </>
          ) : (
            <>
              <span className="font-display tracking-wide uppercase">
                Server Back Online —
              </span>{" "}
              You can submit forms again.
            </>
          )}
        </div>
      </div>
    </div>
  );
}
