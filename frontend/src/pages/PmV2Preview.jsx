// Track 13.6A · PM Portal V2 Preview — Operational Recovery correction.
//
// PURPOSE
//   Visual evaluation lane for a future PM portal redesign, mounted ONLY at
//   /_internal/pm-v2-preview. The 13.5A Phase B2 version of this page rendered
//   RFIs and Submittals as mock data — surfaces that have no engine, no API,
//   and no route. Track 13.6A removes all dead objects so the preview shows
//   only PM concepts backed by real, partial-real, or operator-decided data.
//
// HARD RULE (13.6A):
//   No visible object may exist unless it does something real.
//   • RFIs            → REMOVED (no engine in codebase).
//   • Submittals      → REMOVED (no engine in codebase).
//   • Risks           → REPLACED with Project Constraints (real engine: `/api/constraints/*`).
//   • Mock photo grid → kept as a tile that links to the live /pm/photos route.
//   • Every visible button has either a real destination or is explicitly
//     marked non-interactive (no fake routes, no fake handlers).
//
// STRICT BOUNDARIES (still in force from B2):
//   • No /api/pm/* fetch in this preview (mock fixtures only).
//   • No state mutation outside this component tree.
//   • No portal swap. No nav link. No deploy.

import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  PortalShell,
  StatusChip,
  Card,
  DataTable,
  EmptyState,
} from "../design-system";

// ─────────────────────────────────────────────────────────────────────────────
// MOCK FIXTURES — every row mirrors data that already exists in MASCI engines.
// ─────────────────────────────────────────────────────────────────────────────

const MOCK_PM = {
  name: "Devon Marsh",
  role: "Senior Project Manager",
  region: "Central Florida",
};

// Each pulse is bound to a real route in the live PM portal. Clicking the
// card navigates to that route (not stubbed). Engines without a real list
// route are intentionally omitted.
const TODAY_PULSE = [
  {
    id: "assigned_projects",
    title: "Assigned Projects",
    metric: 8,
    caption: "Scoped via PM email",
    statusKey: "verified",
    variant: "default",
    to: "/pm/jobs",
    api: "/api/pm/jobs",
  },
  {
    id: "daily_reports",
    title: "Daily Reports Today",
    metric: 4,
    caption: "1 needs revision",
    statusKey: "needs_revision",
    variant: "warning",
    to: "/pm/daily",
    api: "/api/daily-reports",
  },
  {
    id: "open_incidents",
    title: "Open Incidents",
    metric: 2,
    caption: "pending verify",
    statusKey: "pending_verification",
    variant: "default",
    to: "/pm/incidents",
    api: "/api/incidents",
  },
  {
    id: "open_constraints",
    title: "Open Project Constraints",
    metric: 3,
    caption: "real engine · awaiting close",
    statusKey: "submitted",
    variant: "warning",
    to: "/constraints",
    api: "/api/constraints",
  },
];

const PROJECTS = [
  { id: "20-07", number: "20-07", name: "I-4 Cross-Country Drainage",       phase: "Underground", crews: 2, health: "verified",          incidents: 0, constraints: 1, daily: "Submitted",      updated: "12 min ago" },
  { id: "21-06", number: "21-06", name: "Avalon Park Phase III",            phase: "Roadway",     crews: 1, health: "needs_revision",    incidents: 1, constraints: 2, daily: "Needs Revision", updated: "1 hr ago" },
  { id: "22-11", number: "22-11", name: "Lake Nona Medical City — Lift 4",  phase: "Structural",  crews: 1, health: "verified",          incidents: 0, constraints: 0, daily: "Submitted",      updated: "32 min ago" },
  { id: "23-02", number: "23-02", name: "Daytona Industrial Park",          phase: "Sitework",    crews: 1, health: "maintenance_hold", incidents: 1, constraints: 0, daily: "Pending",        updated: "yesterday" },
  { id: "23-09", number: "23-09", name: "Sanford Airport Apron",            phase: "Paving",      crews: 1, health: "verified",          incidents: 0, constraints: 0, daily: "Submitted",      updated: "4 min ago" },
];

const INCIDENTS = [
  { id: "INC-512", project: "21-06", when: "Today · 09:14", kind: "Near-miss", status: "submitted", crew: "Crew A" },
  { id: "INC-510", project: "23-02", when: "Yesterday",    kind: "Property",  status: "verified",  crew: "Crew C" },
];

const CAPAS = [
  { id: "CAPA-204", project: "21-06", title: "Spotter required on backup operations within 25 ft", status: "pending_verification", due: "Thu" },
  { id: "CAPA-201", project: "23-02", title: "Inspect culvert pads before stockpile",              status: "verified",            due: "Closed" },
];

const CONSTRAINTS = [
  { id: "CST-2401", project: "21-06", title: "Wet utility conflict at Sta. 14+25",   status: "submitted",            owner: "Devon",       updated: "Today" },
  { id: "CST-2402", project: "21-06", title: "FDOT permit revision pending",         status: "pending_verification", owner: "Devon",       updated: "Today" },
  { id: "CST-2404", project: "23-02", title: "Box culvert delivery slipped 3 days",  status: "submitted",            owner: "Procurement", updated: "Mon" },
];

const DAILY_REPORTS = [
  { id: "DR-7411", project: "20-07", crew: "Crew A", weather: "Sunny · 84°F",  manhours: 78, status: "submitted",       updated: "12 min ago" },
  { id: "DR-7410", project: "21-06", crew: "Crew B", weather: "Cloudy · 80°F", manhours: 42, status: "needs_revision", updated: "1 hr ago" },
  { id: "DR-7409", project: "22-11", crew: "Crew C", weather: "Sunny · 82°F", manhours: 38, status: "submitted",       updated: "32 min ago" },
  { id: "DR-7408", project: "23-09", crew: "Crew D", weather: "Sunny · 81°F", manhours: 22, status: "submitted",       updated: "4 min ago" },
];

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const SECTION_GAP = 28;

function SectionHeader({ kicker, title, caption, action }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
      <div>
        <div
          style={{
            fontSize: "var(--kicker-size)",
            letterSpacing: "var(--kicker-tracking)",
            fontWeight: "var(--kicker-weight)",
            textTransform: "uppercase",
            color: "var(--ink-faint)",
          }}
        >
          {kicker}
        </div>
        <h2
          style={{
            margin: "2px 0 0",
            fontSize: 18,
            fontWeight: 700,
            color: "var(--ink-strong)",
            fontFamily: "var(--font-display)",
          }}
        >
          {title}
        </h2>
        {caption && <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>{caption}</p>}
      </div>
      {action}
    </div>
  );
}

function Section({ kicker, title, caption, action, children, testId }) {
  return (
    <section data-testid={testId} style={{ marginBottom: SECTION_GAP }}>
      <SectionHeader kicker={kicker} title={title} caption={caption} action={action} />
      {children}
    </section>
  );
}

function RealLink({ to, testid, children, intent = "default" }) {
  const tone =
    intent === "primary"
      ? { bg: "var(--brand-primary)", color: "var(--brand-on-primary)", border: "var(--brand-primary)" }
      : { bg: "var(--paper-card)", color: "var(--ink-strong)", border: "var(--border-bold)" };
  return (
    <Link
      to={to}
      data-testid={testid}
      style={{
        display: "inline-block",
        padding: "6px 12px",
        background: tone.bg,
        color: tone.color,
        border: `1px solid ${tone.border}`,
        borderRadius: "var(--radius-card)",
        fontSize: 12,
        fontWeight: 600,
        textDecoration: "none",
      }}
    >
      {children}
    </Link>
  );
}

function ClickableCard({ to, testid, ...cardProps }) {
  return (
    <Link
      to={to}
      data-testid={testid}
      style={{ textDecoration: "none", color: "inherit", display: "block" }}
    >
      <Card {...cardProps} />
    </Link>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sections
// ─────────────────────────────────────────────────────────────────────────────

function CommandCenter() {
  return (
    <Section
      kicker="01 · What requires PM attention today"
      title="Today's pulse"
      caption="Every card links to the live PM surface it summarises. Numbers shown are preview-only; live PM portal continues to serve real data."
      testId="pm-v2-section-pulse"
    >
      <div
        data-testid="pm-v2-pulse-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 16,
        }}
      >
        {TODAY_PULSE.map((p) => (
          <ClickableCard
            key={p.id}
            to={p.to}
            testid={`pm-v2-pulse-${p.id}`}
            title={p.title}
            description={p.caption}
            metric={p.metric}
            variant={p.variant}
            status={<StatusChip statusKey={p.statusKey} compact />}
          />
        ))}
      </div>
    </Section>
  );
}

function ProjectList() {
  const [sort, setSort] = useState({ key: "number", direction: "asc" });
  const rows = useMemo(() => {
    const dir = sort.direction === "asc" ? 1 : -1;
    return [...PROJECTS].sort((a, b) => (a[sort.key] > b[sort.key] ? dir : -dir));
  }, [sort]);

  const columns = [
    { key: "number", header: "Job #",     width: 90,  sortable: true },
    { key: "name",   header: "Project",                sortable: true, wrap: true },
    { key: "phase",  header: "Phase",     width: 130 },
    { key: "crews",  header: "Crews",     width: 70,  align: "right" },
    { key: "health", header: "Health",    width: 170, render: (r) => <StatusChip statusKey={r.health} compact /> },
    { key: "incidents",   header: "Open Incidents",   width: 120, align: "right" },
    { key: "constraints", header: "Open Constraints", width: 140, align: "right" },
    { key: "daily",       header: "Daily Report",     width: 140 },
    { key: "updated",     header: "Updated",          width: 110, align: "right" },
  ];

  return (
    <Section
      kicker="02 · Assigned Projects"
      title="Your project book"
      caption="Backed by /api/pm/jobs in live PM. RFIs, Submittals, and Risks columns are intentionally absent (no MASCI engine today)."
      testId="pm-v2-section-projects"
      action={<RealLink to="/pm/jobs" testid="pm-v2-projects-open">Open Projects</RealLink>}
    >
      <DataTable
        data-testid="pm-v2-projects-table"
        columns={columns}
        rows={rows}
        rowKey={(r) => r.id}
        sort={sort}
        onSortChange={setSort}
      />
    </Section>
  );
}

function ProjectHealth() {
  return (
    <Section
      kicker="03 · Project Health · 21-06"
      title="Avalon Park Phase III"
      caption="Per-project pulse · backed by /api/pm/command-center/* Phase 4A endpoints in live PM."
      testId="pm-v2-section-project-health"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        <Card title="Project Phase"         description="Roadway"     metric="62%" status={<StatusChip statusKey="in_transport" compact />} />
        <Card title="Daily Report"          description="Crew B"      metric="—"   status={<StatusChip statusKey="needs_revision" compact />} variant="warning" />
        <Card title="Open Incidents"        description="1 active"    metric="1"   status={<StatusChip statusKey="submitted" compact />} variant="warning" />
        <Card title="Open Constraints"      description="2 active"    metric="2"   status={<StatusChip statusKey="pending_verification" compact />} variant="warning" />
        <Card title="Crew Compliance"       description="100% certs"  metric="100%" status={<StatusChip statusKey="verified" compact />} variant="success" />
        <Card title="QA / QC"               description="2 outstanding" metric="2" status={<StatusChip statusKey="pending_verification" compact />} />
      </div>
    </Section>
  );
}

function ProjectConstraints() {
  const cols = [
    { key: "id",      header: "Constraint", width: 110 },
    { key: "project", header: "Project",    width: 90 },
    { key: "title",   header: "Issue",      wrap: true },
    { key: "owner",   header: "Owner",      width: 130 },
    { key: "status",  header: "Status",     width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "updated", header: "Updated",    width: 90, align: "right" },
  ];
  return (
    <Section
      kicker="04 · Project Constraints"
      title="Open across your projects"
      caption="Backed by the real Constraints engine (/api/constraints/*). Phase B1 chips applied; live PM surface unchanged."
      testId="pm-v2-section-constraints"
      action={<RealLink to="/constraints" testid="pm-v2-constraints-open">Open Constraints</RealLink>}
    >
      <DataTable
        data-testid="pm-v2-constraints-table"
        columns={cols}
        rows={CONSTRAINTS}
        rowKey={(r) => r.id}
      />
    </Section>
  );
}

function IncidentsAndCapas() {
  const incCols = [
    { key: "id",      header: "ID",      width: 100 },
    { key: "project", header: "Project", width: 90 },
    { key: "when",    header: "When",    width: 130 },
    { key: "kind",    header: "Kind",    width: 100 },
    { key: "crew",    header: "Crew",    width: 90 },
    { key: "status",  header: "Status",  width: 150, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  const capaCols = [
    { key: "id",      header: "CAPA",       width: 110 },
    { key: "project", header: "Project",    width: 90 },
    { key: "title",   header: "Corrective Action", wrap: true },
    { key: "due",     header: "Due",        width: 90 },
    { key: "status",  header: "Status",     width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  return (
    <Section
      kicker="05 · Safety"
      title="Incidents & CAPAs"
      caption="Backed by /api/incidents/* (full lifecycle) and /api/pm/crew/capas (PM-scoped CAPAs)."
      testId="pm-v2-section-incidents-capas"
      action={<RealLink to="/pm/incidents" testid="pm-v2-incidents-open">Open Incidents</RealLink>}
    >
      <div data-testid="pm-v2-incidents-capas-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <DataTable data-testid="pm-v2-incidents-table" columns={incCols}  rows={INCIDENTS} rowKey={(r) => r.id} caption="Incidents" />
        <DataTable data-testid="pm-v2-capas-table"     columns={capaCols} rows={CAPAS}     rowKey={(r) => r.id} caption="Corrective Actions" />
      </div>
    </Section>
  );
}

function DailyReports() {
  const cols = [
    { key: "id",       header: "Report",     width: 110 },
    { key: "project",  header: "Project",    width: 90 },
    { key: "crew",     header: "Crew",       width: 90 },
    { key: "weather",  header: "Weather",    width: 160 },
    { key: "manhours", header: "Man-hours",  width: 110, align: "right" },
    { key: "status",   header: "Status",     width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "updated",  header: "Updated",    width: 110, align: "right" },
  ];
  return (
    <Section
      kicker="06 · Daily Reports"
      title="Today's submissions"
      caption="Backed by /api/daily-reports* full lifecycle. 'Needs Revision' is the strongest negative — never 'Rejected'."
      testId="pm-v2-section-daily-reports"
      action={<RealLink to="/pm/daily" testid="pm-v2-daily-open">Open Daily Reports</RealLink>}
    >
      <DataTable
        data-testid="pm-v2-daily-table"
        columns={cols}
        rows={DAILY_REPORTS}
        rowKey={(r) => r.id}
      />
    </Section>
  );
}

function PhotosTile() {
  return (
    <Section
      kicker="07 · Photos"
      title="From the field"
      caption="The live PM Photos library lives at /pm/photos. This is a real link, not a mock grid."
      testId="pm-v2-section-photos"
      action={<RealLink to="/pm/photos" testid="pm-v2-photos-open">Open Photos</RealLink>}
    >
      <Card
        title="Job Photos Library"
        description="Backed by /pm/photos (JobPhotosLibrary component) — real R2 storage."
        status={<StatusChip statusKey="verified" compact />}
        data-testid="pm-v2-photos-card"
      >
        <p style={{ margin: 0, fontSize: 12, color: "var(--ink-soft)" }}>
          No mock photo grid is rendered here — only the link to the real surface. Mock thumbnails would imply an engine that already exists, so they are intentionally absent.
        </p>
      </Card>
    </Section>
  );
}

function CalmStates() {
  return (
    <Section
      kicker="08 · Calm states"
      title="What 'nothing wrong' looks like"
      caption="When the data is calm, the PM portal does not invent anxiety."
      testId="pm-v2-section-empty"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
        <EmptyState
          title="No open safety holds."
          explanation="Crews can be assigned without override. This is the goal — not a missing screen."
          severity="good"
        />
        <EmptyState
          title="No constraints to action."
          explanation="When one lands, you'll see it on Today's pulse before anywhere else."
          severity="neutral"
        />
      </div>
    </Section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function PmV2Preview() {
  return (
    <div data-testid="pm-v2-preview-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <div
        data-testid="pm-v2-preview-banner"
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
        Internal · PM Portal V2 Preview · Track 13.6A Recovery · Mock pulse · Real-engine surfaces only · No route swap
      </div>

      <PortalShell
        portalName="MASCI"
        portalRole="PM Portal · V2 Preview"
        pageTitle={`What requires your attention today, ${MOCK_PM.name.split(" ")[0]}?`}
        subtitle={`${MOCK_PM.role} · ${MOCK_PM.region}. Every card and table below links to a live PM surface backed by a real MASCI API.`}
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/pm/daily" testid="pm-v2-action-daily">Daily Reports</RealLink>
            <RealLink to="/pm/command-center" testid="pm-v2-action-cc" intent="primary">Open Command Center</RealLink>
          </div>
        }
        lastActivity={<span data-testid="pm-v2-last-activity">Preview only · live PM portal continues at /pm/*</span>}
      >
        <CommandCenter />
        <ProjectList />
        <ProjectHealth />
        <ProjectConstraints />
        <IncidentsAndCapas />
        <DailyReports />
        <PhotosTile />
        <CalmStates />

        <div
          data-testid="pm-v2-removed-note"
          style={{
            marginTop: 16,
            padding: "var(--pad-card)",
            background: "var(--paper-card)",
            border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)",
            color: "var(--ink-soft)",
            fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>Removed in Track 13.6A:</strong>
          {" "}<em>RFIs</em> and <em>Submittals</em> (no MASCI engine today) and <em>Risks</em> (replaced with the real Project Constraints engine).
          {" "}If MASCI ever adopts RFI / Submittal engines, those surfaces will return — backed by real APIs, never mocks.
        </div>
      </PortalShell>
    </div>
  );
}
