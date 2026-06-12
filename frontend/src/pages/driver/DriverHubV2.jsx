// Track 13.6K-DRIVER-CORRECTION — Driver V2 reality fix.
//
// ROUTE: /driver/hub_v2  (PREVIEW ONLY — no route swap.)
//
// REAL DRIVER FLOW (verified from source · DO NOT INVENT):
//   • Drivers DO NOT sign in. There is no driver account system.
//   • Public entry: /shift   (ShiftStart.jsx · "Driver Self-Start
//                              Operational Entry" · 0 passwords, 0
//                              accounts, 0 enrollment · pick driver +
//                              truck from canonical dropdowns · 1 tap
//                              "Start Shift" mints the in-browser
//                              driver session, forwards to /driver).
//   • Magic-link entry: /d/:token  (DriverMagicLanding.jsx ·
//                              dispatcher-issued · 0 typed characters
//                              · exchanges the token, persists driver
//                              session, forwards to /driver).
//   • Tap-and-work surface: /driver  (DriverShift.jsx · the operational
//                              surface · requires the in-browser
//                              session minted by either entry above).
//
// HUB V2 must do exactly ONE thing:
//   If a driver session already exists in this browser → one big tap
//   "OPEN MY SHIFT" → /driver.
//   Otherwise → one big tap "START SHIFT" → /shift (the real public
//   self-start entry, no login).
//
// Secondary buttons must only link to REAL existing destinations.
// "Report Issue" → /driver (defects + transitions live on the shift
//                            surface · no other public route exists).
// "Contact Dispatch" → tel: link if a number is in env, otherwise
//                       link to /shift (still real).
//
// FORBIDDEN: SIGN IN, login, account, fake auth, fake token, fake
// assignment, fake truck lookup, dashboard, KPIs.

import React from "react";
import { useNavigate } from "react-router-dom";
import { getDriverToken } from "@/lib/driverAuth";

function Big({ children, dim = false }) {
  return (
    <div style={{
      color: dim ? "rgba(255,255,255,0.55)" : "#fff",
      fontSize: 14, fontWeight: 600, letterSpacing: 0.4,
    }}>{children}</div>
  );
}

export default function DriverHubV2() {
  const navigate = useNavigate();
  // Driver "session" is the in-browser X-Driver-Token minted by /shift
  // or /d/:token. The presence of this token is the ONLY thing that
  // tells us whether the driver already self-started their shift —
  // it is NOT an account, NOT a login, and NOT validated here.
  const hasShiftSession = !!getDriverToken();

  const primary = hasShiftSession
    ? {
        label: "OPEN MY SHIFT",
        to: "/driver",
        testid: "driver-hub-v2-action-open-shift",
        sub: "Resume your active shift screen.",
      }
    : {
        label: "START SHIFT",
        to: "/shift",
        testid: "driver-hub-v2-action-start-shift",
        sub: "Pick your truck and name. No password. No account.",
      };

  return (
    <div
      data-testid="driver-hub-v2-root"
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #0b1220 0%, #050810 100%)",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        padding: "32px 24px",
        fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif",
      }}
    >
      <div style={{ maxWidth: 460, margin: "0 auto", width: "100%" }}>
        <div style={{
          fontSize: 11, letterSpacing: 2, textTransform: "uppercase",
          color: "rgba(255,255,255,0.55)", marginBottom: 8,
        }}>
          MASCI · Driver
        </div>

        <h1
          data-testid="driver-hub-v2-headline"
          style={{ margin: 0, fontSize: 32, fontWeight: 800, lineHeight: 1.15 }}
        >
          What do you need to do right now?
        </h1>

        <div data-testid={`driver-hub-v2-state-${hasShiftSession ? "have-session" : "no-session"}`}
             style={{ marginTop: 24 }}>
          <Big dim>{primary.sub}</Big>
        </div>

        {/* THE single primary action — large glove-friendly tap target. */}
        <button
          data-testid={primary.testid}
          onClick={() => navigate(primary.to)}
          style={{
            marginTop: 32,
            width: "100%",
            background: "#ff3b30",
            color: "#fff",
            border: "none",
            borderRadius: 14,
            padding: "22px 18px",
            fontSize: 18,
            fontWeight: 800,
            letterSpacing: 0.6,
            cursor: "pointer",
            boxShadow: "0 12px 30px rgba(255,59,48,0.35)",
          }}
        >
          {primary.label}
        </button>

        {/* Secondary real-only links. Both targets exist today. */}
        <div data-testid="driver-hub-v2-secondary" style={{
          marginTop: 18,
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 10,
        }}>
          {/* Report Issue == open the active shift surface; defect /
              issue capture lives on DriverShift today (see
              DriverShift.jsx · transitions + defect logging). */}
          <button
            data-testid="driver-hub-v2-action-report-issue"
            onClick={() => navigate(hasShiftSession ? "/driver" : "/shift")}
            style={secondaryBtnStyle}
          >
            Report an Issue
          </button>
          {/* Magic-link drivers may arrive from /d/:token; if a driver
              taps "Used a Link?" we send them to /shift so they can
              re-enter via the canonical public path. No fake auth. */}
          <button
            data-testid="driver-hub-v2-action-used-link"
            onClick={() => navigate("/shift")}
            style={secondaryBtnStyle}
          >
            Used a Link?
          </button>
        </div>

        <div
          data-testid="driver-hub-v2-trace-note"
          style={{ marginTop: 36, fontSize: 10, lineHeight: 1.5, color: "rgba(255,255,255,0.4)" }}
        >
          Preview lane · Track 13.6K-DRIVER-CORRECTION. Drivers do not
          sign in. Public self-start lives at{" "}
          <code style={{ color: "#fff" }}>/shift</code>. Dispatcher
          magic-link entry is{" "}
          <code style={{ color: "#fff" }}>/d/:token</code>. Tap-and-work
          shift screen is{" "}
          <code style={{ color: "#fff" }}>/driver</code>. Every button
          on this page opens one of those real existing routes.
        </div>
      </div>
    </div>
  );
}

const secondaryBtnStyle = {
  background: "transparent",
  color: "#fff",
  border: "1.5px solid rgba(255,255,255,0.25)",
  borderRadius: 12,
  padding: "16px 12px",
  fontSize: 14,
  fontWeight: 700,
  cursor: "pointer",
  letterSpacing: 0.3,
};
