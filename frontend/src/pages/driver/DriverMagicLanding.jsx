/**
 * DriverMagicLanding.jsx · iter393 · DLS Driver Magic-Link Entry.
 *
 * Route: /d/:token
 *
 * Lands the driver after they open the dispatcher-issued link.
 * Exchanges the magic token for a working driver session, persists
 * the resulting `X-Driver-Token`, then redirects to /driver.
 *
 * 0 typed characters. 0 taps required for the success path — this
 * screen exists only to show "Signing you in…" while the exchange
 * happens, then forwards.
 */
import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { persistDriverSession } from "@/lib/driverAuth";

const API = process.env.REACT_APP_BACKEND_URL;

/**
 * sessionStorage-backed guard that survives the BrowserRouter remount
 * triggered by `authTick` in App.js (validateStoredTokens runs on every
 * load and bumps the key when ANY stale portal token gets cleared).
 *
 * The guard key is bound to the magic token itself, so each new link
 * starts fresh while replays of the same link are rejected client-side.
 */
function consumeOnce(token) {
  const KEY = `masci.driver.magic.consumed:${token}`;
  try {
    if (sessionStorage.getItem(KEY)) return false;
    sessionStorage.setItem(KEY, "1");
    return true;
  } catch {
    return true;                                 // sessionStorage blocked — fall through
  }
}

export default function DriverMagicLanding() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const tenantOverride = params.get("tenant") || "";
  const [status, setStatus] = useState("loading"); // loading | error
  const [errorMsg, setErrorMsg] = useState("");
  // Same-mount guard for React 18 StrictMode dev double-invoke.
  const exchangedRef = useRef(false);

  useEffect(() => {
    if (exchangedRef.current) return;
    if (!token) {
      setStatus("error");
      setErrorMsg("Missing link token.");
      return;
    }
    // Cross-remount single-flight: only proceed if we have not yet
    // tried to exchange this exact token in this tab.
    if (!consumeOnce(token)) {
      // The exchange already ran in this tab. If we already persisted
      // a driver token, just forward to /driver — otherwise show the
      // error state so the user knows the link is spent.
      try {
        const stored = localStorage.getItem("masci.driver.token");
        if (stored) {
          navigate("/driver", { replace: true });
          return;
        }
      } catch {
        /* ignore */
      }
      setStatus("error");
      setErrorMsg("This link has already been used. Ask dispatch for a new one.");
      return;
    }
    exchangedRef.current = true;

    (async () => {
      try {
        const headers = { "Content-Type": "application/json" };
        if (tenantOverride) headers["X-Tenant-Id"] = tenantOverride;
        const r = await fetch(`${API}/api/dispatch/driver/session/exchange`, {
          method: "POST",
          headers,
          body: JSON.stringify({ magic_token: token }),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok || !j.driver_token) {
          setStatus("error");
          setErrorMsg(j.detail || "This link is no longer valid. Ask dispatch for a new one.");
          return;
        }
        persistDriverSession(j);
        navigate("/driver", { replace: true });
      } catch {
        setStatus("error");
        setErrorMsg("Connection failed. Check signal and try the link again.");
      }
    })();
  }, [token, tenantOverride, navigate]);

  return (
    <div
      data-testid="driver-magic-landing"
      className="min-h-screen w-full flex items-center justify-center px-6 py-12 bg-slate-950 text-slate-100"
    >
      <div className="max-w-sm w-full text-center space-y-6">
        <div
          className="inline-flex items-center justify-center h-16 w-16 rounded-full border-4 border-amber-400 text-amber-400 text-3xl font-bold"
          data-testid="driver-magic-brand"
        >
          DLS
        </div>
        {status === "loading" ? (
          <>
            <p className="text-2xl font-semibold tracking-tight">Signing you in…</p>
            <p className="text-base text-slate-400">
              Hold this screen for a second — you'll land on your truck shift automatically.
            </p>
            <div
              className="mx-auto h-2 w-32 rounded-full bg-slate-800 overflow-hidden"
              aria-hidden
            >
              <div className="h-full w-1/2 bg-amber-400 animate-pulse" />
            </div>
          </>
        ) : (
          <>
            <p
              className="text-2xl font-semibold text-rose-300"
              data-testid="driver-magic-error"
            >
              Link not active
            </p>
            <p className="text-base text-slate-300">{errorMsg}</p>
            <p className="text-sm text-slate-500">
              Magic links expire after 15 minutes and can only be used once.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
