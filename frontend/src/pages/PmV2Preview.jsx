// Track 13.5A · Phase B2 — PM Portal V2 Preview Lane.
//
// PURPOSE
//   Visual evaluation lane for a future PM Portal redesign built on
//   the Phase B1 shared design primitives. This route exists ONLY for
//   operator review at /_internal/pm-v2-preview. It is not linked
//   from any operator navigation, does not load any live PM data, and
//   does not mutate anything.
//
// STRICT BOUNDARIES (per operator directive)
//   • DO NOT import any PM workflow code.
//   • DO NOT call any /api/pm/* endpoint.
//   • DO NOT mutate any state outside this component tree.
//   • DO NOT rename or replace any existing PM route or form.
//   • DO NOT link to this page from any operator portal.
//
// All data on this page is local mock fixture. The same data is rendered
// in three responsive viewports — desktop, iPad landscape, iPad portrait —
// during the side-by-side comparison capture.

import React, { useMemo, useState } from "react";
import {
  PortalShell,
  StatusChip,
  Card,
  DataTable,
  EmptyState,
} from "../design-system";

// ─────────────────────────────────────────────────────────────────────────────
// MOCK FIXTURES — local only, never reach the network.
// ─────────────────────────────────────────────────────────────────────────────

const MOCK_PM = {
  name: "Devon Marsh",
  role: "Senior Project Manager",
  region: "Central Florida",
};

const TODAY_PULSE = [
  { id: "active_projects", title: "Active Projects",          metric: 8,  caption: "across CFL + Coast", status: "verified" },
  { id: "crews_in_field",  title: "Crews in Field Today",     metric: 6,  caption: "23 crew members",   status: "in_transport" },
  { id: "open_holds",      title: "Open Holds",               metric: 2,  caption: "1 safety · 1 cert", status: "safety_hold", variant: "warning" },
  { id: "due_today",       title: "Due Today",                metric: 4,  caption: "RFIs + submittals", status: "pending_verification" },
];

const PROJECTS = [
  { id: "20-07", number: "20-07", name: "I-4 Cross-Country Drainage",     phase: "Underground", crews: 2, health: "verified",            risks: 1, rfis: 2, submittals: 0, daily: "Submitted",     updated: "12 min ago" },
  { id: "21-06", number: "21-06", name: "Avalon Park Phase III",          phase: "Roadway",     crews: 1, health: "needs_revision",      risks: 3, rfis: 1, submittals: 2, daily: "Needs Revision", updated: "1 hr ago" },
  { id: "22-11", number: "22-11", name: "Lake Nona Medical City — Lift 4",phase: "Structural",  crews: 1, health: "verified",            risks: 0, rfis: 0, submittals: 1, daily: "Submitted",     updated: "32 min ago" },
  { id: "23-02", number: "23-02", name: "Daytona Industrial Park",        phase: "Sitework",    crews: 1, health: "maintenance_hold",    risks: 2, rfis: 0, submittals: 0, daily: "Pending",       updated: "yesterday" },
  { id: "23-09", number: "23-09", name: "Sanford Airport Apron",          phase: "Paving",      crews: 1, health: "verified",            risks: 0, rfis: 0, submittals: 0, daily: "Submitted",     updated: "4 min ago" },
];

const RISKS = [
  { id: "R-2401", project: "21-06", title: "Wet utility conflict at Sta. 14+25", severity: "urgent",    owner: "Devon", due: "Tomorrow" },
  { id: "R-2402", project: "21-06", title: "FDOT permit revision pending",       severity: "attention", owner: "Devon", due: "Fri" },
  { id: "R-2403", project: "21-06", title: "Subgrade compaction sample missing", severity: "attention", owner: "QA/QC", due: "Today" },
  { id: "R-2404", project: "23-02", title: "Box culvert delivery slipped 3 days",severity: "attention", owner: "Procurement", due: "Mon" },
  { id: "R-2405", project: "23-02", title: "Operator certification expiring",    severity: "info",      owner: "HR",    due: "Next wk" },
  { id: "R-2406", project: "20-07", title: "Dewatering pump backup needed",      severity: "info",      owner: "Devon", due: "—" },
];

const RFIS = [
  { id: "RFI-1187", project: "20-07", question: "Confirm pipe class @ Sta. 22+10",        status: "submitted",            age: "2d" },
  { id: "RFI-1188", project: "20-07", question: "Clarify joint detail at headwall A-12",  status: "pending_verification", age: "1d" },
  { id: "RFI-1189", project: "21-06", question: "Subgrade modulus for paving section",    status: "needs_revision",       age: "3d" },
];

const SUBMITTALS = [
  { id: "S-441",  project: "21-06", item: "RCP 36\" gasketed joint", status: "submitted",  age: "4d", reviewer: "EOR" },
  { id: "S-442",  project: "21-06", item: "Curb-mix design",         status: "verified",   age: "8d", reviewer: "EOR" },
  { id: "S-443",  project: "22-11", item: "Cast-iron lift station frame", status: "needs_revision", age: "1d", reviewer: "EOR" },
];

const INCIDENTS = [
  { id: "INC-512", project: "21-06", when: "Today · 09:14", kind: "Near-miss", status: "submitted", crew: "Crew A" },
  { id: "INC-510", project: "23-02", when: "Yesterday",      kind: "Property", status: "verified",  crew: "Crew C" },
];

const CAPAS = [
  { id: "CAPA-204", project: "21-06", title: "Spotter required on backup operations within 25 ft",  status: "pending_verification", due: "Thu" },
  { id: "CAPA-201", project: "23-02", title: "Inspect culvert pads before stockpile",               status: "verified",            due: "Closed" },
];

const PHOTOS = [
  { id: "PH-9921", project: "20-07", caption: "Lift station rebar tie-in",   when: "Today · 08:42" },
  { id: "PH-9922", project: "20-07", caption: "Subgrade after compaction",   when: "Today · 09:10" },
  { id: "PH-9923", project: "23-09", caption: "Asphalt mat — sta. 12+00",    when: "Today · 10:05" },
  { id: "PH-9924", project: "22-11", caption: "Box-out for lift hardware",   when: "Today · 10:55" },
];

const DAILY_REPORTS = [
  { id: "DR-7411", project: "20-07", crew: "Crew A", weather: "Sunny · 84°F", manhours: 78, status: "submitted",       updated: "12 min ago" },
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
    <div className="flex items-end justify-between" style={{ gap: 16, marginBottom: 12 }}>
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
        {caption && (
          <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>
            {caption}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}

function Section({ kicker, title, caption, action, children, testId, style }) {
  return (
    <section data-testid={testId} style={{ marginBottom: SECTION_GAP, ...style }}>
      <SectionHeader kicker={kicker} title={title} caption={caption} action={action} />
      {children}
    </section>
  );
}

function MockButton({ children, testid, intent = "default" }) {
  const tone =
    intent === "primary"
      ? { bg: "var(--brand-primary)", color: "var(--brand-on-primary)", border: "var(--brand-primary)" }
      : { bg: "var(--paper-card)", color: "var(--ink-strong)", border: "var(--border-bold)" };
  return (
    <button
      data-testid={testid}
      type="button"
      onClick={(e) => e.preventDefault()}
      style={{
        padding: "6px 12px",
        background: tone.bg,
        color: tone.color,
        border: `1px solid ${tone.border}`,
        borderRadius: "var(--radius-card)",
        fontSize: 12,
        fontWeight: 600,
        letterSpacing: "0.01em",
        cursor: "pointer",
      }}
    >
      {children}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Surface mini-components (each represents one PM workflow surface)
// ─────────────────────────────────────────────────────────────────────────────

function CommandCenter() {
  return (
    <Section
      kicker="01 · Command Center"
      title="What needs you today"
      caption="A calm answer to 'what's the move right now?' — built on the canonical status vocabulary."
      testId="pm-v2-section-command-center"
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
          <Card
            key={p.id}
            title={p.title}
            description={p.caption}
            metric={p.metric}
            variant={p.variant || "default"}
            status={<StatusChip statusKey={p.status} compact />}
            data-testid={`pm-v2-pulse-${p.id}`}
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
    { key: "number", header: "Job #",      width: 90,  sortable: true },
    { key: "name",   header: "Project",                  sortable: true, wrap: true },
    { key: "phase",  header: "Phase",      width: 130 },
    { key: "crews",  header: "Crews",      width: 70,  align: "right" },
    {
      key: "health",
      header: "Health",
      width: 170,
      render: (r) => <StatusChip statusKey={r.health} compact />,
    },
    { key: "risks",      header: "Risks",      width: 70,  align: "right" },
    { key: "rfis",       header: "RFIs",       width: 70,  align: "right" },
    { key: "submittals", header: "Submittals", width: 90,  align: "right" },
    {
      key: "daily",
      header: "Daily Report",
      width: 140,
    },
    { key: "updated", header: "Updated", width: 110, align: "right" },
  ];

  return (
    <Section
      kicker="02 · Projects"
      title="Project list"
      caption="One row per project. The same status vocabulary appears everywhere — operators learn it once."
      testId="pm-v2-section-projects"
      action={<MockButton testid="pm-v2-projects-export" intent="default">Export</MockButton>}
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
      kicker="03 · Project Health"
      title="Avalon Park Phase III · 21-06"
      caption="Per-project pulse: phase signals + the canonical chips that drive the rest of the PM surface."
      testId="pm-v2-section-project-health"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        <Card title="Project Phase" description="Roadway"        metric="62%" status={<StatusChip statusKey="in_transport" compact />} />
        <Card title="Daily Report"  description="Crew B"          metric="—"    status={<StatusChip statusKey="needs_revision" compact />} variant="warning" />
        <Card title="Open Risks"    description="3 active"        metric="3"    status={<StatusChip statusKey="reopened" compact />} variant="warning" />
        <Card title="Crew Compliance" description="100% certs"    metric="100%" status={<StatusChip statusKey="verified" compact />} variant="success" />
        <Card title="QA / QC"       description="2 outstanding"   metric="2"    status={<StatusChip statusKey="pending_verification" compact />} />
        <Card title="Photos Today"  description="14 uploaded"     metric="14"   status={<StatusChip statusKey="submitted" compact />} />
      </div>
    </Section>
  );
}

function Risks() {
  const columns = [
    { key: "id",      header: "ID",       width: 110 },
    { key: "project", header: "Project",  width: 110 },
    { key: "title",   header: "Risk",     wrap: true },
    {
      key: "severity",
      header: "Severity",
      width: 140,
      render: (r) => <StatusChip label={r.severity[0].toUpperCase() + r.severity.slice(1)} severity={r.severity} compact />,
    },
    { key: "owner",   header: "Owner",    width: 130 },
    { key: "due",     header: "Due",      width: 110, align: "right" },
  ];
  return (
    <Section
      kicker="04 · Risks"
      title="Open risks across the PM book"
      caption="Severity uses the canonical scale. There is no 'rejected' — there is only 'needs revision' or 'attention'."
      testId="pm-v2-section-risks"
    >
      <DataTable
        data-testid="pm-v2-risks-table"
        columns={columns}
        rows={RISKS}
        rowKey={(r) => r.id}
      />
    </Section>
  );
}

function RFIsAndSubmittals() {
  const rfiCols = [
    { key: "id",       header: "RFI",     width: 110 },
    { key: "project",  header: "Project", width: 90 },
    { key: "question", header: "Question", wrap: true },
    { key: "status",   header: "Status",  width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "age",      header: "Age",     width: 60, align: "right" },
  ];
  const subCols = [
    { key: "id",       header: "Submittal", width: 90 },
    { key: "project",  header: "Project",   width: 90 },
    { key: "item",     header: "Item", wrap: true },
    { key: "reviewer", header: "Reviewer",  width: 100 },
    { key: "status",   header: "Status",    width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "age",      header: "Age",       width: 60, align: "right" },
  ];
  return (
    <Section
      kicker="05 · Documents"
      title="RFIs & submittals"
      caption="Documents on one calm rail. Empty isn't an error — it's the goal."
      testId="pm-v2-section-rfis-submittals"
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <DataTable data-testid="pm-v2-rfis-table"       columns={rfiCols} rows={RFIS}       rowKey={(r) => r.id} caption="RFIs"       />
        <DataTable data-testid="pm-v2-submittals-table" columns={subCols} rows={SUBMITTALS} rowKey={(r) => r.id} caption="Submittals" />
      </div>
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
      kicker="06 · Safety"
      title="Incidents & CAPAs"
      caption="A non-punitive safety record: events get tracked, corrective actions get owned."
      testId="pm-v2-section-incidents-capas"
    >
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <DataTable data-testid="pm-v2-incidents-table" columns={incCols}  rows={INCIDENTS} rowKey={(r) => r.id} caption="Incidents" />
        <DataTable data-testid="pm-v2-capas-table"     columns={capaCols} rows={CAPAS}     rowKey={(r) => r.id} caption="Corrective Actions" />
      </div>
    </Section>
  );
}

function Photos() {
  return (
    <Section
      kicker="07 · Photos"
      title="From the field today"
      caption="Operator-uploaded photos surface here. This is a presentation tile — full library lives in Phase B3+."
      testId="pm-v2-section-photos"
    >
      <div
        data-testid="pm-v2-photos-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
          gap: 12,
        }}
      >
        {PHOTOS.map((ph) => (
          <Card
            key={ph.id}
            density="compact"
            title={ph.id}
            description={ph.caption}
            data-testid={`pm-v2-photo-${ph.id}`}
          >
            <div
              style={{
                marginTop: 6,
                aspectRatio: "4 / 3",
                background: "var(--paper-base)",
                border: "1px dashed var(--border-bold)",
                borderRadius: "var(--radius-card)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--ink-faint)",
                fontSize: 11,
                letterSpacing: "0.04em",
              }}
              aria-label="Mock photo placeholder"
            >
              MOCK · {ph.project}
            </div>
            <p style={{ margin: "6px 0 0", fontSize: 11, color: "var(--ink-soft)" }}>
              {ph.when}
            </p>
          </Card>
        ))}
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
      kicker="08 · Daily Reports"
      title="Today's submissions"
      caption="Foremen submit, PM verifies. 'Needs Revision' is the strongest negative — never 'Rejected'."
      testId="pm-v2-section-daily-reports"
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

function EmptySurfaces() {
  return (
    <Section
      kicker="09 · Absence with poise"
      title="What the calm state looks like"
      caption="When nothing is wrong, the PM portal does not invent anxiety."
      testId="pm-v2-section-empty"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
        <EmptyState
          title="No open safety holds."
          explanation="Crews can be assigned without override. This is the goal — not a missing screen."
          severity="good"
        />
        <EmptyState
          title="No RFIs awaiting your reply."
          explanation="When one lands, you'll see it on the Command Center pulse before anywhere else."
          severity="neutral"
        />
        <EmptyState
          title="Telematics feed is stale on RB-518."
          explanation="Last position 1 hr ago. Investigation queued; no operator action required right now."
          severity="attention"
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
    <div
      data-testid="pm-v2-preview-root"
      style={{ background: "var(--paper-base)", minHeight: "100vh" }}
    >
      {/* Internal-only banner — operator review lane, never production. */}
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
        Internal · PM Portal V2 Preview · Phase B2 · Mock data · No live workflows · No route swap
      </div>

      <PortalShell
        portalName="MASCI"
        portalRole="PM Portal · V2 Preview"
        pageTitle={`Good morning, ${MOCK_PM.name.split(" ")[0]}.`}
        subtitle={`${MOCK_PM.role} · ${MOCK_PM.region}. This is what your day looks like — on the new visual language.`}
        primaryActions={
          <div className="flex items-center gap-2">
            <MockButton testid="pm-v2-action-new-rfi">New RFI</MockButton>
            <MockButton testid="pm-v2-action-open-cc" intent="primary">Open Command Center</MockButton>
          </div>
        }
        lastActivity={
          <span data-testid="pm-v2-last-activity">
            Last data refresh · 12 min ago · MOCK
          </span>
        }
      >
        <CommandCenter />
        <ProjectList />
        <ProjectHealth />
        <Risks />
        <RFIsAndSubmittals />
        <IncidentsAndCapas />
        <Photos />
        <DailyReports />
        <EmptySurfaces />

        {/* Footer note */}
        <div
          data-testid="pm-v2-footer-note"
          style={{
            marginTop: 32,
            padding: "var(--pad-card)",
            background: "var(--paper-card)",
            border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)",
            color: "var(--ink-soft)",
            fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>Phase B2 boundary.</strong>
          {" "}This preview lane reads no live data and writes nothing.
          It exists so the operator can compare the future PM visual language
          against the current PM portal before any migration is authorized.
        </div>
      </PortalShell>
    </div>
  );
}
