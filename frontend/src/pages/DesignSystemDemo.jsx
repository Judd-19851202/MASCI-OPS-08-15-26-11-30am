// Track 13.5A · Phase B1 — Internal Design System Demo Page.
//
// PURPOSE:
//   Isolated showcase of the seven shared design primitives.
//   This page is mounted ONLY at /_internal/design-system and is
//   NOT linked from any operator navigation. It exists exclusively
//   to provide visual proof that the primitives render correctly
//   under tokens.css without touching any production portal.
//
// CONSTRAINTS:
//   • No real data. No real auth. No real workflows.
//   • No engine wiring. No mutation of state outside this page.
//   • Token-only styling. No portal CSS leakage.
import React, { useMemo, useState } from "react";
import {
  PortalShell,
  PublicShell,
  StatusChip,
  Card,
  EmptyState,
  DataTable,
  STATUS_REGISTRY,
} from "../design-system";

const SECTION_GAP = 32;

function Section({ kicker, title, description, children, testId }) {
  return (
    <section
      data-testid={testId}
      style={{ marginBottom: SECTION_GAP }}
    >
      <div style={{ marginBottom: 12 }}>
        <div
          style={{
            fontSize: "var(--kicker-size)",
            letterSpacing: "var(--kicker-tracking)",
            fontWeight: "var(--kicker-weight)",
            textTransform: "uppercase",
            color: "var(--ink-faint)",
            marginBottom: 4,
          }}
        >
          {kicker}
        </div>
        <h2
          style={{
            fontSize: 20,
            fontWeight: 700,
            color: "var(--ink-strong)",
            margin: 0,
            fontFamily: "var(--font-display)",
          }}
        >
          {title}
        </h2>
        {description && (
          <p
            style={{
              color: "var(--ink-soft)",
              fontSize: 13,
              margin: "4px 0 0",
              maxWidth: 720,
            }}
          >
            {description}
          </p>
        )}
      </div>
      {children}
    </section>
  );
}

const SAMPLE_ROWS = [
  { id: "RB-101", unit: "RB-101", make: "Caterpillar", model: "320", status: "available",     hours: 1421, updated: "2 min ago" },
  { id: "RB-204", unit: "RB-204", make: "Komatsu",     model: "PC210", status: "assigned",      hours: 982,  updated: "9 min ago" },
  { id: "RB-309", unit: "RB-309", make: "John Deere",  model: "350G", status: "maintenance_hold", hours: 2110, updated: "1 hr ago" },
  { id: "RB-412", unit: "RB-412", make: "Volvo",       model: "EC220", status: "in_transport",   hours: 654,  updated: "20 min ago" },
  { id: "RB-518", unit: "RB-518", make: "Caterpillar", model: "336", status: "stale_position",  hours: 1888, updated: "yesterday" },
];

export default function DesignSystemDemo() {
  const [sort, setSort] = useState({ key: "unit", direction: "asc" });

  const sortedRows = useMemo(() => {
    if (!sort) return SAMPLE_ROWS;
    const dir = sort.direction === "asc" ? 1 : -1;
    return [...SAMPLE_ROWS].sort((a, b) => {
      const av = a[sort.key];
      const bv = b[sort.key];
      if (av === bv) return 0;
      return av > bv ? dir : -dir;
    });
  }, [sort]);

  const columns = [
    { key: "unit",   header: "Unit",   sortable: true,  width: 110 },
    { key: "make",   header: "Make",   sortable: true },
    { key: "model",  header: "Model",  sortable: true },
    {
      key: "status",
      header: "Status",
      render: (row) => <StatusChip statusKey={row.status} compact />,
    },
    { key: "hours",  header: "Engine Hours", align: "right", sortable: true },
    { key: "updated", header: "Last Update",  align: "right" },
  ];

  // Render every entry in the canonical status vocabulary.
  const allStatusKeys = Object.keys(STATUS_REGISTRY);

  return (
    <div
      data-testid="design-system-demo-root"
      style={{ background: "var(--paper-base)", minHeight: "100vh" }}
    >
      {/* Top banner — this is NOT a portal, just an isolation marker. */}
      <div
        data-testid="design-system-demo-banner"
        style={{
          background: "var(--brand-primary)",
          color: "var(--brand-on-primary)",
          padding: "10px 16px",
          fontSize: 12,
          letterSpacing: "0.04em",
          textTransform: "uppercase",
          fontWeight: 700,
          textAlign: "center",
        }}
      >
        Internal · Design System V1 · Phase B1 · No operator workflows touched
      </div>

      <PortalShell
        portalName="MASCI"
        portalRole="Design System · Internal"
        pageTitle="Shared Design Primitives Foundation"
        subtitle="Isolated visual showcase. No portal migration. No engine wiring."
        lastActivity={<span>Mounted at <code>/_internal/design-system</code></span>}
      >
        {/* Status Chips */}
        <Section
          kicker="01 · Vocabulary"
          title="StatusChip · Standard Status Registry"
          description="Every operator-facing state in MASCI maps to one of these chips. Forbidden labels (Rejected · Denied · Failed) are absent by design."
          testId="ds-demo-section-status"
        >
          <div
            data-testid="ds-demo-status-grid"
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: 8,
              padding: "var(--pad-card)",
              background: "var(--paper-card)",
              border: "1px solid var(--border-hairline)",
              borderRadius: "var(--radius-card)",
            }}
          >
            {allStatusKeys.map((k) => (
              <StatusChip key={k} statusKey={k} />
            ))}
          </div>
        </Section>

        {/* Cards */}
        <Section
          kicker="02 · Surfaces"
          title="Card · Density + Variant Matrix"
          description="The base operator surface. Three density modes, four variants. Used by every operator portal in Phase B2+."
          testId="ds-demo-section-card"
        >
          <div
            data-testid="ds-demo-card-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: 16,
            }}
          >
            <Card
              title="Active Jobs"
              description="Currently dispatched"
              metric="47"
              status={<StatusChip statusKey="verified" compact />}
            />
            <Card
              title="Open Holds"
              description="Awaiting verification"
              metric="3"
              variant="warning"
              status={<StatusChip statusKey="maintenance_hold" compact />}
            />
            <Card
              title="Safety Hold"
              description="One unit pending stand-down"
              metric="1"
              variant="danger"
              status={<StatusChip statusKey="safety_hold" compact />}
            />
            <Card
              title="Verified Today"
              description="Closed out"
              metric="12"
              variant="success"
              status={<StatusChip statusKey="verified" compact />}
            />
            <Card
              title="Compact Density"
              description="Used in dense list rows"
              density="compact"
            >
              <p style={{ margin: 0, fontSize: 12, color: "var(--ink-soft)" }}>
                Tighter padding for high-density panels.
              </p>
            </Card>
            <Card
              title="Spacious Density"
              description="Used for headline surfaces"
              density="spacious"
            >
              <p style={{ margin: 0, fontSize: 12, color: "var(--ink-soft)" }}>
                Roomier padding for hero metrics.
              </p>
            </Card>
          </div>
        </Section>

        {/* DataTable */}
        <Section
          kicker="03 · Records"
          title="DataTable · Sort · Empty · Loading"
          description="Presentation primitive only. Parent owns data + sort state. Status chips render inline."
          testId="ds-demo-section-datatable"
        >
          <div style={{ marginBottom: 16 }}>
            <DataTable
              data-testid="ds-demo-datatable-loaded"
              caption="Sample equipment roster (fixture data — not live)."
              columns={columns}
              rows={sortedRows}
              rowKey={(r) => r.id}
              sort={sort}
              onSortChange={setSort}
            />
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 16,
            }}
          >
            <DataTable
              data-testid="ds-demo-datatable-loading"
              columns={columns}
              rows={[]}
              loading
            />
            <DataTable
              data-testid="ds-demo-datatable-empty"
              columns={columns}
              rows={[]}
              empty={
                <EmptyState
                  title="No equipment matches this filter."
                  explanation="Clear the filter or widen the date range."
                />
              }
            />
          </div>
        </Section>

        {/* Empty State */}
        <Section
          kicker="04 · Absence"
          title="EmptyState · Non-Punitive Voice"
          description="What the operator sees when there is nothing — calm, descriptive, never an error."
          testId="ds-demo-section-empty"
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
              gap: 16,
            }}
          >
            <EmptyState
              title="No active holds."
              explanation="The fleet is clear. Equipment can be assigned without override."
              severity="good"
            />
            <EmptyState
              title="No reports submitted today."
              explanation="Field crews have not posted a daily report yet."
              severity="neutral"
            />
            <EmptyState
              title="Stale telematics feed."
              explanation="Motive has not received a position in 45 minutes. Investigation queued."
              severity="attention"
            />
          </div>
        </Section>

        {/* PublicShell preview */}
        <Section
          kicker="05 · Public Surfaces"
          title="PublicShell · QR-landing Wrapper"
          description="The presentation wrapper for public-facing surfaces (trench-safety QR landings, excavation forms). Renders without operator chrome."
          testId="ds-demo-section-public-shell"
        >
          <div
            style={{
              border: "1px dashed var(--border-bold)",
              borderRadius: "var(--radius-card)",
              overflow: "hidden",
              background: "var(--paper-base)",
            }}
          >
            <PublicShell surfaceName="Excavation Reference">
              <Card
                title="Site information"
                description="Public-facing copy lives inside the shell. No operator nav."
              >
                <p style={{ margin: 0, fontSize: 13, color: "var(--ink-regular)" }}>
                  This is what a QR-landing surface looks like wrapped by PublicShell.
                  Used for sub-routes that face the public, not operators.
                </p>
              </Card>
            </PublicShell>
          </div>
        </Section>

        {/* Footer note */}
        <Section
          kicker="06 · Governance"
          title="Phase B1 Boundary"
          description="These primitives exist. They are not yet applied. Phase B2 migrates one pilot portal — under explicit operator authorization only."
          testId="ds-demo-section-governance"
        >
          <Card
            title="Foundation Scope"
            description="Foundation only. No portal touched. No workflow altered."
          >
            <ul style={{ margin: 0, paddingLeft: 18, color: "var(--ink-regular)", fontSize: 13, lineHeight: 1.6 }}>
              <li>PortalShell · PublicShell · StatusChip · Card · EmptyState · DataTable · statusRegistry</li>
              <li>All primitives consume tokens.css variables exclusively.</li>
              <li>Mounted at <code>/_internal/design-system</code>; not linked from operator navigation.</li>
              <li>Forbidden status labels never enter the registry.</li>
            </ul>
          </Card>
        </Section>
      </PortalShell>
    </div>
  );
}
