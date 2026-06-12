// Track 13.6B · Side-by-Side Comparison view.
//
// Internal-only side-by-side renderer: left pane = live current portal,
// right pane = V2 preview. Operator visually compares before any swap is
// even contemplated. Mounted at /_internal/v2-compare/:portal.

import React from "react";
import { useParams, Link } from "react-router-dom";
import { PortalShell, Card, StatusChip, EmptyState } from "../design-system";

const PORTAL_CONFIG = {
  pm: {
    label: "PM",
    currentTitle: "Current PM Portal · /pm/hub",
    currentTo: "/pm/hub",
    currentNote: "Requires PM login (pm.demo@mascigc.com). The current PM portal carries the live data; iframe may show the login page until you authenticate in another tab.",
    v2Title: "PM Hub V2 · /pm/hub_v2 (live · real APIs)",
    v2To: "/pm/hub_v2",
    purpose: "Build projects",
  },
  hr: {
    label: "HR",
    currentTitle: "Current HR Portal · /hr",
    currentTo: "/hr",
    currentNote: "Requires HR login (hrmanager@mascigc.com). The current HR portal carries the live data; iframe may show the login page until you authenticate in another tab.",
    v2Title: "HR Hub V2 · /hr/hub_v2 (live · real APIs)",
    v2To: "/hr/hub_v2",
    purpose: "Maintain workforce readiness",
  },
};

function Pane({ title, to, note, isV2, testid }) {
  return (
    <div
      data-testid={testid}
      style={{
        display: "flex",
        flexDirection: "column",
        border: "1px solid var(--border-bold)",
        borderRadius: "var(--radius-card)",
        overflow: "hidden",
        background: "var(--paper-card)",
        minHeight: 720,
      }}
    >
      <div
        style={{
          padding: "10px 12px",
          borderBottom: "1px solid var(--border-bold)",
          background: isV2 ? "var(--paper-tinted-success)" : "var(--paper-rail)",
          color: isV2 ? "var(--ink-strong)" : "var(--paper-rail-ink)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div>
          <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em", opacity: 0.8 }}>
            {isV2 ? "V2 preview" : "Live current"}
          </div>
          <div style={{ fontSize: 14, fontWeight: 700 }}>{title}</div>
        </div>
        <Link
          to={to}
          target="_blank"
          rel="noopener noreferrer"
          data-testid={`${testid}-open-new-tab`}
          style={{
            fontSize: 12, fontWeight: 600,
            padding: "4px 10px",
            border: "1px solid currentColor",
            borderRadius: "var(--radius-card)",
            textDecoration: "none",
            color: "inherit",
          }}
        >
          Open in new tab →
        </Link>
      </div>
      <iframe
        title={title}
        src={to}
        data-testid={`${testid}-iframe`}
        style={{ flex: 1, border: 0, minHeight: 700, background: "var(--paper-base)" }}
      />
      {note && (
        <div
          style={{
            padding: "8px 12px",
            borderTop: "1px solid var(--border-bold)",
            background: "var(--paper-base)",
            color: "var(--ink-soft)",
            fontSize: 11,
          }}
        >
          {note}
        </div>
      )}
    </div>
  );
}

export default function V2Compare() {
  const { portal } = useParams();
  const cfg = PORTAL_CONFIG[portal];

  if (!cfg) {
    return (
      <div data-testid="v2-compare-unknown" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
        <PortalShell
          portalName="MASCI"
          portalRole="V2 Side-by-Side Comparison"
          pageTitle={`Unknown portal '${portal}'`}
          subtitle="The portal name in the URL does not match any active V2 preview lane."
        >
          <EmptyState
            title="No comparison configured for this portal."
            explanation="Active comparisons today: /_internal/v2-compare/pm and /_internal/v2-compare/hr."
            severity="neutral"
          />
          <div style={{ marginTop: 16 }}>
            <Link to="/_internal/v2-index" data-testid="v2-compare-back-to-index" style={{ fontSize: 12, fontWeight: 600 }}>
              ← Back to V2 Index
            </Link>
          </div>
        </PortalShell>
      </div>
    );
  }

  return (
    <div data-testid={`v2-compare-root-${portal}`} style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <div
        data-testid="v2-compare-banner"
        style={{
          background: "var(--brand-primary)", color: "var(--brand-on-primary)",
          padding: "10px 16px", fontSize: 12, letterSpacing: "0.04em",
          textTransform: "uppercase", fontWeight: 700, textAlign: "center",
        }}
      >
        Internal · V2 Side-by-Side · {cfg.label} · No route swap from this page
      </div>
      <PortalShell
        portalName="MASCI"
        portalRole={`${cfg.label} Portal · Comparison`}
        pageTitle={`${cfg.label} Portal · Current vs V2`}
        subtitle={`${cfg.label} portal purpose: ${cfg.purpose}. Use this view to visually verify the V2 preserves intent before any migration is authorized.`}
        primaryActions={
          <Link to="/_internal/v2-index" data-testid="v2-compare-back-index" style={{
            display: "inline-block", padding: "6px 12px",
            background: "var(--paper-card)", color: "var(--ink-strong)",
            border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
            fontSize: 12, fontWeight: 600, textDecoration: "none",
          }}>
            ← V2 Index
          </Link>
        }
      >
        <Card
          data-testid={`v2-compare-instructions-${portal}`}
          title="How to use this view"
          description="Iframes load the live current portal on the left and the V2 preview on the right. If the left pane shows a login screen, sign in to the portal in a separate tab — your session cookie will flow into this iframe on the next refresh."
          status={<StatusChip statusKey="submitted" compact />}
        />
        <div
          data-testid={`v2-compare-grid-${portal}`}
          style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16, alignItems: "stretch" }}
        >
          <Pane title={cfg.currentTitle} to={cfg.currentTo} note={cfg.currentNote} isV2={false} testid={`v2-compare-current-${portal}`} />
          <Pane title={cfg.v2Title}     to={cfg.v2To}     note={null}                isV2={true}  testid={`v2-compare-v2-${portal}`}     />
        </div>

        <div
          data-testid={`v2-compare-rule-${portal}`}
          style={{
            marginTop: 20, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>13.6B §5 rule:</strong>
          {" "}No live portal route may be swapped until this side-by-side has been operator-approved. Approval is recorded in
          {" "}<code>/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md</code>.
        </div>
      </PortalShell>
    </div>
  );
}
