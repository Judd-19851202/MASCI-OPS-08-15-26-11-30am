import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

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
    const interval = setInterval(probe, POLL_MS);
    return () => {
      clearInterval(interval);
      if (recoveredTimer) clearTimeout(recoveredTimer);
    };
  }, []);

  if (status !== "down" && status !== "recovered") return null;

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
              try again. Reports won't save until this banner disappears.
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
