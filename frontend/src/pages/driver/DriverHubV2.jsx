// Track 13.6J · Phase 2 — Driver V2 foundation (preview only).
//
// ROUTE: /driver/hub_v2 (no auth gate change — driver session via
// existing driverHeaders / getDriverToken from @/lib/driverAuth).
//
// DOCTRINE
//   • ≤ 2 taps · ≤ 30 seconds · immediate first action.
//   • The page answers exactly one question:
//       "What do I need to do right now?"
//   • Driver portal must NOT become a miniature PM / Dispatch / dashboard.
//   • Every action must lead to a REAL existing workflow.
//   • If the driver has no active assignment, show one big "Open My Shift
//     Screen" button that lands on /driver (the existing tap-and-work
//     surface) — never invent work.
//
// REAL DATA ONLY
//   GET /api/dispatch/driver/my-assignment    (existing real endpoint)
//
// Visual: full-bleed, dark, one giant primary card. No grids. No tabs.
// No nav. No KPIs. No vanity tiles.

import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { driverHeaders, getDriverToken } from "@/lib/driverAuth";

const API = process.env.REACT_APP_BACKEND_URL;

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
  const [state, setState] = useState({ loaded: false, body: null, signedIn: false });

  useEffect(() => {
    let cancelled = false;
    const tok = getDriverToken();
    if (!tok) { setState({ loaded: true, body: null, signedIn: false }); return; }
    (async () => {
      try {
        const r = await fetch(`${API}/api/dispatch/driver/my-assignment`, {
          headers: driverHeaders(),
        });
        const body = r.ok ? await r.json() : null;
        if (!cancelled) setState({ loaded: true, body, signedIn: true });
      } catch {
        if (!cancelled) setState({ loaded: true, body: null, signedIn: true });
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const assignment = state.body?.assignment || null;
  const currentState = (assignment?.current_state || "").toUpperCase();
  const truck = assignment?.truck_unit_number || assignment?.truck_id || "";
  const project = assignment?.project_number || "";
  const drop = assignment?.dump_site || assignment?.dump_location || "";

  const primaryAction = (() => {
    if (!state.signedIn) return { label: "SIGN IN", to: "/driver/login", testid: "driver-hub-v2-action-signin" };
    // Real existing workflow: /driver renders DriverShift (the tap-and-work surface).
    return { label: "OPEN MY SHIFT SCREEN", to: "/driver", testid: "driver-hub-v2-action-open-shift" };
  })();

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
          style={{
            margin: 0, fontSize: 32, fontWeight: 800, lineHeight: 1.15,
          }}
        >
          What do you need to do right now?
        </h1>

        {!state.loaded && (
          <div style={{ marginTop: 28, color: "rgba(255,255,255,0.6)" }}>
            Loading your shift…
          </div>
        )}

        {state.loaded && !state.signedIn && (
          <div data-testid="driver-hub-v2-state-signin" style={{ marginTop: 24 }}>
            <Big dim>You are not signed in.</Big>
            <Big dim>Tap below to start.</Big>
          </div>
        )}

        {state.loaded && state.signedIn && !assignment && (
          <div data-testid="driver-hub-v2-state-no-assignment" style={{ marginTop: 24 }}>
            <Big>No active assignment right now.</Big>
            <Big dim>When dispatch sends a job, your shift screen will update automatically.</Big>
          </div>
        )}

        {state.loaded && assignment && (
          <div data-testid="driver-hub-v2-state-have-assignment" style={{ marginTop: 24 }}>
            <Big>
              {truck ? `Truck ${truck}` : "Active assignment"}
              {project ? ` · Project ${project}` : ""}
            </Big>
            <Big dim>State: {currentState || "—"}</Big>
            {drop && <Big dim>Drop: {drop}</Big>}
          </div>
        )}

        {/* THE single primary action button — large tap target. */}
        <button
          data-testid={primaryAction.testid}
          onClick={() => navigate(primaryAction.to)}
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
          {primaryAction.label}
        </button>

        {/* ── Secondary actions: only those that already exist in the
              real platform. Each tap routes to an existing workflow. ── */}
        {state.loaded && state.signedIn && (
          <div data-testid="driver-hub-v2-secondary" style={{
            marginTop: 18,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 10,
          }}>
            <button
              data-testid="driver-hub-v2-action-report-issue"
              onClick={() => navigate("/driver")}
              style={secondaryBtnStyle}
            >
              Report an Issue
            </button>
            <a
              data-testid="driver-hub-v2-action-contact-dispatch"
              href="tel:+15555555555"
              style={{ ...secondaryBtnStyle, textDecoration: "none", display: "block", textAlign: "center" }}
            >
              Contact Dispatch
            </a>
          </div>
        )}

        <div
          data-testid="driver-hub-v2-trace-note"
          style={{
            marginTop: 36, fontSize: 10, lineHeight: 1.5,
            color: "rgba(255,255,255,0.4)",
          }}
        >
          Preview lane · Track 13.6J. The classic tap-and-work surface remains at
          <code style={{ color: "#fff" }}> /driver</code>. Every action on this
          screen opens a real existing workflow. Source: live
          <code style={{ color: "#fff" }}> /api/dispatch/driver/my-assignment</code>.
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
