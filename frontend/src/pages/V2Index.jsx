// Track 13.6B · Operator Review Hub.
//
// Internal-only landing that lists every V2 preview lane, plus links to the
// side-by-side comparison view per portal. NOT linked from any operator nav.
// Mounted at /_internal/v2-index.

import React from "react";
import { Link } from "react-router-dom";
import { PortalShell, Card, StatusChip, EmptyState } from "../design-system";

const PREVIEW_LANES = [
  {
    id: "pm-v2",
    portal: "PM",
    title: "PM Portal · V2",
    track: "13.6B",
    builtOn: "2026-06-12",
    status: "operational",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 8 },
    previewTo: "/_internal/pm-v2-preview",
    compareTo: "/_internal/v2-compare/pm",
    currentTo: "/pm/hub",
    summary: "Action-queue PM preview. Every card opens a real PM queue (Daily-to-revise · Incidents-pending · CAPAs-due · Constraints-open). RFIs · Submittals · Risks · mock photos removed.",
  },
  {
    id: "hr-v2",
    portal: "HR",
    title: "HR Portal · V2",
    track: "13.6B",
    builtOn: "2026-06-12",
    status: "operational",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 8 },
    previewTo: "/_internal/hr-v2-preview",
    compareTo: "/_internal/v2-compare/hr",
    currentTo: "/hr",
    summary: "Action-queue HR preview. Every card opens a real HR queue (Pending requests · Expiring certs · Payroll variance · Accountability signals). Vanity headcount removed.",
  },
  {
    id: "design-system",
    portal: "Design System",
    title: "Design System V1 · primitives showcase",
    track: "13.5A",
    builtOn: "2026-06-12",
    status: "operational",
    score: { powerful: 8, simple: 8, beautiful: 8, trusted: 7, proven: 7 },
    previewTo: "/_internal/design-system",
    compareTo: null,
    currentTo: null,
    summary: "Isolated showcase of every Phase B1 primitive (PortalShell · PublicShell · StatusChip · Card · DataTable · EmptyState) + canonical status registry.",
  },
  {
    id: "admin-v2",
    portal: "Admin",
    title: "Admin Portal · V2",
    track: "TBD",
    builtOn: null,
    status: "planned",
    score: null,
    previewTo: null,
    compareTo: null,
    currentTo: "/admin",
    summary: "Planned. Awaiting operator authorization after HR or PM pilot migration.",
  },
  {
    id: "dispatch-v2",
    portal: "Dispatch",
    title: "Dispatch Portal · V2",
    track: "TBD",
    builtOn: null,
    status: "planned",
    score: null,
    previewTo: null,
    compareTo: null,
    currentTo: "/dispatch-portal",
    summary: "Planned. Already strong post-13.4A; migration risk is map-rendering — needs targeted guardrail before any swap.",
  },
  {
    id: "safety-v2",
    portal: "Safety",
    title: "Safety Portal · V2",
    track: "TBD",
    builtOn: null,
    status: "planned",
    score: null,
    previewTo: null,
    compareTo: null,
    currentTo: "/safety",
    summary: "Planned. Trench Safety module is the reference benchmark for other portals; migration is mostly chrome alignment.",
  },
  {
    id: "shop-v2",
    portal: "Shop",
    title: "Shop Portal · V2",
    track: "TBD",
    builtOn: null,
    status: "planned",
    score: null,
    previewTo: null,
    compareTo: null,
    currentTo: "/shop",
    summary: "Planned. Smallest portal; migration is mostly amber-vs-orange drift correction (V-01).",
  },
  {
    id: "driver-v2",
    portal: "Driver",
    title: "Driver Portal · V2",
    track: "TBD",
    builtOn: null,
    status: "planned",
    score: null,
    previewTo: null,
    compareTo: null,
    currentTo: "/driver",
    summary: "Planned. Highest impact / lowest score today; needs static Driver Hub landing (V-15 / R-13) before any migration.",
  },
];

function Avg(s) {
  if (!s) return null;
  const vals = [s.powerful, s.simple, s.beautiful, s.trusted, s.proven];
  return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
}

function PreviewRow({ lane }) {
  const isOperational = lane.status === "operational";
  return (
    <Card
      data-testid={`v2-index-row-${lane.id}`}
      title={lane.title}
      description={lane.summary}
      status={
        isOperational
          ? <StatusChip statusKey="verified" compact />
          : <StatusChip statusKey="draft" compact label="Planned" />
      }
      variant={isOperational ? "default" : "default"}
    >
      <div style={{ display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap", marginTop: 12 }}>
        <div style={{ minWidth: 110 }}>
          <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--ink-faint)", marginBottom: 2 }}>Track</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-strong)" }}>{lane.track}</div>
        </div>
        <div style={{ minWidth: 110 }}>
          <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--ink-faint)", marginBottom: 2 }}>Built</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-strong)" }}>{lane.builtOn || "—"}</div>
        </div>
        <div style={{ minWidth: 110 }}>
          <div style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--ink-faint)", marginBottom: 2 }}>5-pillar avg</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "var(--ink-strong)" }}>{Avg(lane.score) || "—"} / 10</div>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {lane.previewTo && (
            <Link to={lane.previewTo} data-testid={`v2-index-${lane.id}-preview`} style={btnStyle("primary")}>
              Open Preview
            </Link>
          )}
          {lane.compareTo && (
            <Link to={lane.compareTo} data-testid={`v2-index-${lane.id}-compare`} style={btnStyle("default")}>
              Side-by-Side vs Current
            </Link>
          )}
          {lane.currentTo && (
            <Link to={lane.currentTo} data-testid={`v2-index-${lane.id}-current`} style={btnStyle("default")}>
              Open Current Portal
            </Link>
          )}
        </div>
      </div>
    </Card>
  );
}

function btnStyle(intent) {
  const tone = intent === "primary"
    ? { bg: "var(--brand-primary)", color: "var(--brand-on-primary)", border: "var(--brand-primary)" }
    : { bg: "var(--paper-card)", color: "var(--ink-strong)", border: "var(--border-bold)" };
  return {
    display: "inline-block",
    padding: "6px 12px",
    background: tone.bg,
    color: tone.color,
    border: `1px solid ${tone.border}`,
    borderRadius: "var(--radius-card)",
    fontSize: 12,
    fontWeight: 600,
    textDecoration: "none",
  };
}

export default function V2Index() {
  const operational = PREVIEW_LANES.filter((l) => l.status === "operational");
  const planned = PREVIEW_LANES.filter((l) => l.status === "planned");
  return (
    <div data-testid="v2-index-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <div
        data-testid="v2-index-banner"
        style={{
          background: "var(--brand-primary)", color: "var(--brand-on-primary)",
          padding: "10px 16px", fontSize: 12, letterSpacing: "0.04em",
          textTransform: "uppercase", fontWeight: 700, textAlign: "center",
        }}
      >
        Internal · V2 Index · Operator Review Hub · Not operator-facing · Not customer-facing
      </div>
      <PortalShell
        portalName="MASCI"
        portalRole="V2 Preview Review Hub"
        pageTitle="Active V2 preview lanes"
        subtitle="Every preview built so far · operator review before any migration · no route swap can happen from this page."
        lastActivity={<span data-testid="v2-index-last-activity">Updated by Track 13.6B</span>}
      >
        <section data-testid="v2-index-section-operational" style={{ marginBottom: 28 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 14, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--ink-faint)" }}>
            Operational previews ({operational.length})
          </h3>
          <div style={{ display: "grid", gap: 16 }}>
            {operational.map((lane) => <PreviewRow key={lane.id} lane={lane} />)}
          </div>
        </section>

        <section data-testid="v2-index-section-planned">
          <h3 style={{ margin: "0 0 12px", fontSize: 14, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--ink-faint)" }}>
            Planned lanes ({planned.length})
          </h3>
          {planned.length === 0 ? (
            <EmptyState title="No planned lanes." severity="neutral" />
          ) : (
            <div style={{ display: "grid", gap: 16 }}>
              {planned.map((lane) => <PreviewRow key={lane.id} lane={lane} />)}
            </div>
          )}
        </section>

        <div
          data-testid="v2-index-rules-note"
          style={{
            marginTop: 28, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>Migration rule (13.6B §5):</strong>
          {" "}No portal route may be swapped until the operator has reviewed it on the corresponding
          {" "}<em>Side-by-Side vs Current</em> page. The comparison page renders the current portal and
          {" "}the V2 preview together so visual approval can happen without leaving the review hub.
        </div>
      </PortalShell>
    </div>
  );
}
