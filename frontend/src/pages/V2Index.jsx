// Track 13.6B · Operator Review Hub.
//
// Internal-only landing that lists every V2 lane (live-swapped, companion,
// or retired) plus links to the side-by-side comparison view per portal.
// NOT linked from any operator nav. Mounted at /_internal/v2-index.

import React from "react";
import { Link } from "react-router-dom";
import { PortalShell, Card, StatusChip, EmptyState } from "../design-system";

const PREVIEW_LANES = [
  {
    id: "pm-v2",
    portal: "PM",
    title: "PM Portal · V2",
    track: "13.6B / 13.6D / 13.6F",
    builtOn: "2026-06-12",
    status: "live-swapped",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 9 },
    previewTo: "/_internal/pm-v2-preview",
    compareTo: "/_internal/v2-compare/pm",
    currentTo: "/pm/hub",
    summary: "LIVE — PmHubV2 is mounted at /pm/hub. Project Risks PERMANENTLY renamed to Project Constraints. RFIs and Submittals removed (no engine). Legacy rollback preserved at /pm/hub_legacy during the operator signoff window.",
  },
  {
    id: "hr-v2",
    portal: "HR",
    title: "HR Portal · V2",
    track: "13.6B / 13.6C / 13.6E",
    builtOn: "2026-06-12",
    status: "live-swapped",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 9 },
    previewTo: "/_internal/hr-v2-preview",
    compareTo: "/_internal/v2-compare/hr",
    currentTo: "/hr",
    summary: "LIVE — HrHubV2 is mounted at /hr. Real APIs · real workflows · same HR auth. Legacy rollback preserved at /hr/hub_legacy during the operator signoff window.",
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
    track: "13.6K",
    builtOn: "2026-06-12",
    status: "companion",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 8 },
    previewTo: "/admin/hub_v2",
    compareTo: null,
    currentTo: "/admin",
    summary: "COMPANION LANE. Provides cross-portal operational awareness (integrations health · expirations · safety / fleet attention) that classic /admin does not surface. Classic /admin remains the canonical settings / users / audit hub.",
  },
  {
    id: "dispatch-v2",
    portal: "Dispatch",
    title: "Dispatch Portal · V2",
    track: "13.6G/J/L",
    builtOn: "2026-06-12",
    status: "companion-only",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 8 },
    previewTo: "/dispatch-portal/hub_v2",
    compareTo: null,
    currentTo: "/dispatch-portal",
    summary: "COMPANION LANE ONLY. The map-dominant classic Dispatcher at /dispatch-portal is the canonical Dispatch experience — MapLibre + Motive + FleetWatcher are operationally critical. Dispatch V2 at /dispatch-portal/hub_v2 is a supplementary action-queue read; never a swap target. No V2 redesign may hide / minimize / move-behind-tabs / replace the operational map.",
  },
  {
    id: "safety-v2",
    portal: "Safety",
    title: "Safety Portal · V2",
    track: "13.6H",
    builtOn: "2026-06-12",
    status: "live-swapped",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 9 },
    previewTo: "/safety-portal/hub_v2",
    compareTo: null,
    currentTo: "/safety-portal",
    summary: "LIVE — SafetyHubV2 is mounted at /safety-portal. Fed by /api/safety/overview, 8 action queues across CAPAs / compliance / incidents. Trench Safety benchmark module preserved at /safety/trench-safety (zero touch). Legacy rollback preserved at /safety-portal/hub_legacy during the operator signoff window.",
  },
  {
    id: "shop-v2",
    portal: "Shop",
    title: "Shop Portal · V2",
    track: "13.6I",
    builtOn: "2026-06-12",
    status: "live-swapped",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 9 },
    previewTo: "/shop/hub_v2",
    compareTo: null,
    currentTo: "/shop",
    summary: "LIVE — ShopHubV2 is mounted at /shop. Fed by /api/dispatch/command/summary.shop, 7 action queues across attention, recovery pipeline. Repair Complete ≠ Returned-To-Service rule preserved via separate Returned-To-Service queue. Recovery Map lens available. Legacy rollback preserved at /shop/hub_legacy during the operator signoff window.",
  },
  {
    id: "driver-v2",
    portal: "Driver",
    title: "Driver Portal · V2",
    track: "13.6L",
    builtOn: null,
    status: "retired",
    score: null,
    previewTo: null,
    compareTo: null,
    currentTo: "/shift",
    summary: "RETIRED. Existing operational workflow (/shift public self-start · /d/:token magic-link · /driver tap-and-work) already satisfies ≤ 2 taps / ≤ 30 seconds. Drivers do not sign in, have no accounts, no passwords. The hub layer added unnecessary friction and provided no operational lift.",
  },
  {
    id: "leadership-v2",
    portal: "Leadership",
    title: "Leadership Portal · V2",
    track: "13.6K",
    builtOn: "2026-06-12",
    status: "companion",
    score: { powerful: 9, simple: 9, beautiful: 9, trusted: 9, proven: 8 },
    previewTo: "/leadership/hub_v2",
    compareTo: null,
    currentTo: "/leadership",
    summary: "COMPANION LANE. Provides cross-portal executive attention (Safety threats · Execution threats · Compliance threats) that no other surface currently provides. Reads /api/safety/overview · /api/operations/expirations/summary · /api/dispatch/command/summary. No swap.",
  },
  {
    id: "field-leadership-v2",
    portal: "Field Leadership",
    title: "Field Leadership Portal · V2",
    track: "13.6L",
    builtOn: null,
    status: "retired",
    score: null,
    previewTo: null,
    compareTo: null,
    currentTo: "/field-leadership/portal/dashboard",
    summary: "RETIRED. Existing field leadership operational portal at /field-leadership/portal/dashboard already satisfies the intended workflow. Preview hub duplicated functionality and added no operational lift.",
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
        pageTitle="V2 lanes · live + companion + retired"
        subtitle="Live-swapped portals are mounted at their canonical routes with legacy rollback preserved. Companion lanes supplement the classic portal. Retired lanes are documented for history only."
        lastActivity={<span data-testid="v2-index-last-activity">Operator Review Hub</span>}
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
