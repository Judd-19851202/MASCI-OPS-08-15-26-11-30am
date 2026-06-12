// Track 13.6B · PM Portal V2 Preview — Action-Queue Conversion.
//
// PHILOSOPHY (13.6B Rules):
//   #1 NO DEAD OBJECTS — every visible item exists, functions, has destination.
//   #2 EVERY KPI MUST LEAD SOMEWHERE — counts open queues, not vanity numbers.
//   #3 ACTIONS OVER NUMBERS — "What requires my attention?" before "How many?".
//   #4 PORTAL PURPOSE — PM exists to BUILD PROJECTS. Nothing on this surface
//      may exist if it does not serve building projects.
//
// EVERY VISIBLE OBJECT ANSWERS:
//   1. What is this?       (header + caption)
//   2. Where from?         (caption names the backing API)
//   3. Why does it matter? (operator action implied by the chip + variant)
//   4. What happens when clicked? (Link to= a real PM route)
//
// STRICT BOUNDARIES:
//   • No /api/pm/* fetch (mock fixtures only).
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

// Action queues only. Every card represents WORK, not COUNT.
// `metric` is the SIZE OF THE QUEUE, not a vanity total.
const ACTION_QUEUES = [
  {
    id: "daily_needs_revision",
    title: "Daily Reports to Revise",
    metric: 1,
    caption: "Source: /api/daily-reports?status=needs_revision · PM-scoped",
    why: "Foreman flagged · PM action required to verify or revise",
    statusKey: "needs_revision",
    variant: "warning",
    to: "/pm/daily?status=needs_revision",
  },
  {
    id: "incidents_pending",
    title: "Incidents Awaiting Your Verify",
    metric: 2,
    caption: "Source: /api/incidents?status=pending_verification",
    why: "Submitted by foreman · PM must verify before close",
    statusKey: "pending_verification",
    variant: "warning",
    to: "/pm/incidents?status=pending_verification",
  },
  {
    id: "capas_due",
    title: "CAPAs Due This Week",
    metric: 1,
    caption: "Source: /api/pm/crew/capas · scoped",
    why: "Corrective action approaching due date · must close or extend",
    statusKey: "pending_verification",
    variant: "warning",
    to: "/pm/incidents?tab=capas&due=this_week",
  },
  {
    id: "constraints_open",
    title: "Constraints to Resolve",
    metric: 3,
    caption: "Source: /api/constraints?status=open · PM-scoped",
    why: "Project blockers · each prevents work · resolve or escalate",
    statusKey: "submitted",
    variant: "warning",
    to: "/constraints?status=open",
  },
];

// "Projects need PM action" — NOT "all projects". This is a derived queue.
const PROJECTS_NEEDING_ACTION = [
  { id: "21-06", number: "21-06", name: "Avalon Park Phase III",     why: "Daily Report needs revision · 2 open constraints · 1 incident pending verify", chips: ["needs_revision","submitted","pending_verification"], updated: "1 hr ago" },
  { id: "23-02", number: "23-02", name: "Daytona Industrial Park",   why: "1 incident pending verify · maintenance hold on RB-518",                       chips: ["pending_verification","maintenance_hold"],            updated: "yesterday" },
  { id: "20-07", number: "20-07", name: "I-4 Cross-Country Drainage", why: "1 open constraint awaiting permit revision",                                   chips: ["submitted"],                                          updated: "12 min ago" },
];

const INCIDENTS_QUEUE = [
  { id: "INC-512", project: "21-06", when: "Today · 09:14",  kind: "Near-miss", crew: "Crew A", status: "submitted" },
  { id: "INC-509", project: "23-02", when: "Today · 07:40",  kind: "Property",  crew: "Crew C", status: "submitted" },
];

const CAPA_QUEUE = [
  { id: "CAPA-204", project: "21-06", title: "Spotter required on backup operations within 25 ft", due: "Thu (2 days)", status: "pending_verification" },
];

const CONSTRAINTS_QUEUE = [
  { id: "CST-2401", project: "21-06", title: "Wet utility conflict at Sta. 14+25",  owner: "Devon",       status: "submitted",            updated: "Today" },
  { id: "CST-2402", project: "21-06", title: "FDOT permit revision pending",        owner: "Devon",       status: "pending_verification", updated: "Today" },
  { id: "CST-2404", project: "23-02", title: "Box culvert delivery slipped 3 days", owner: "Procurement", status: "submitted",            updated: "Mon" },
];

const DAILY_TO_REVISE = [
  { id: "DR-7410", project: "21-06", crew: "Crew B", manhours: 42, status: "needs_revision", updated: "1 hr ago" },
];

// ─────────────────────────────────────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────────────────────────────────────

function SectionHeader({ kicker, title, caption, action }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
      <div>
        <div style={{ fontSize: "var(--kicker-size)", letterSpacing: "var(--kicker-tracking)", fontWeight: "var(--kicker-weight)", textTransform: "uppercase", color: "var(--ink-faint)" }}>{kicker}</div>
        <h2 style={{ margin: "2px 0 0", fontSize: 18, fontWeight: 700, color: "var(--ink-strong)", fontFamily: "var(--font-display)" }}>{title}</h2>
        {caption && <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>{caption}</p>}
      </div>
      {action}
    </div>
  );
}

function Section({ kicker, title, caption, action, children, testId }) {
  return (
    <section data-testid={testId} style={{ marginBottom: 28 }}>
      <SectionHeader kicker={kicker} title={title} caption={caption} action={action} />
      {children}
    </section>
  );
}

function RealLink({ to, testid, children, intent = "default" }) {
  const tone = intent === "primary"
    ? { bg: "var(--brand-primary)", color: "var(--brand-on-primary)", border: "var(--brand-primary)" }
    : { bg: "var(--paper-card)", color: "var(--ink-strong)", border: "var(--border-bold)" };
  return (
    <Link to={to} data-testid={testid} style={{
      display: "inline-block", padding: "6px 12px", background: tone.bg, color: tone.color,
      border: `1px solid ${tone.border}`, borderRadius: "var(--radius-card)",
      fontSize: 12, fontWeight: 600, textDecoration: "none",
    }}>
      {children}
    </Link>
  );
}

// Action-queue card. The metric is the SIZE OF THE QUEUE. Click = open the queue.
function ActionQueueCard({ to, testid, queue }) {
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <Card
        title={queue.title}
        description={queue.why}
        metric={queue.metric}
        variant={queue.variant}
        status={<StatusChip statusKey={queue.statusKey} compact />}
      >
        <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
          {queue.caption}
        </p>
      </Card>
    </Link>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Sections
// ─────────────────────────────────────────────────────────────────────────────

function ActionQueues() {
  return (
    <Section
      kicker="01 · What requires you today"
      title="Open action queues"
      caption="Every card opens a real PM queue. Numbers are queue sizes, never vanity counts."
      testId="pm-v2-section-queues"
    >
      <div data-testid="pm-v2-queue-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
        {ACTION_QUEUES.map((q) => (
          <ActionQueueCard key={q.id} to={q.to} testid={`pm-v2-queue-${q.id}`} queue={q} />
        ))}
      </div>
    </Section>
  );
}

function ProjectsNeedingAction() {
  const [sort, setSort] = useState({ key: "number", direction: "asc" });
  const rows = useMemo(() => {
    const dir = sort.direction === "asc" ? 1 : -1;
    return [...PROJECTS_NEEDING_ACTION].sort((a, b) => (a[sort.key] > b[sort.key] ? dir : -dir));
  }, [sort]);

  const cols = [
    { key: "number", header: "Job #",  width: 90,  sortable: true },
    { key: "name",   header: "Project", sortable: true, wrap: true },
    { key: "why",    header: "Why it needs you", wrap: true },
    {
      key: "chips",
      header: "Signals",
      width: 280,
      render: (r) => (
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
          {r.chips.map((c, i) => <StatusChip key={i} statusKey={c} compact />)}
        </div>
      ),
    },
    { key: "updated", header: "Updated", width: 100, align: "right" },
  ];

  return (
    <Section
      kicker="02 · Projects · only those needing action"
      title="Filtered project queue"
      caption="Source: derived from /api/pm/jobs joined to open daily / incident / constraint records. Projects with zero signals are intentionally absent from this view."
      testId="pm-v2-section-projects-action"
      action={<RealLink to="/pm/jobs" testid="pm-v2-projects-open">Open All Projects</RealLink>}
    >
      <DataTable
        data-testid="pm-v2-projects-action-table"
        columns={cols}
        rows={rows}
        rowKey={(r) => r.id}
        sort={sort}
        onSortChange={setSort}
        empty={
          <EmptyState
            title="No projects need your action right now."
            explanation="All daily reports verified, no open incidents, no open constraints. This is the goal — not a missing screen."
            severity="good"
          />
        }
      />
    </Section>
  );
}

function VerifyQueue() {
  const incCols = [
    { key: "id",      header: "ID",      width: 100 },
    { key: "project", header: "Project", width: 90 },
    { key: "when",    header: "When",    width: 130 },
    { key: "kind",    header: "Kind",    width: 100 },
    { key: "crew",    header: "Crew",    width: 90 },
    { key: "status",  header: "Status",  width: 150, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  const dailyCols = [
    { key: "id",       header: "Report",   width: 110 },
    { key: "project",  header: "Project",  width: 90 },
    { key: "crew",     header: "Crew",     width: 90 },
    { key: "manhours", header: "Man-hrs",  width: 90, align: "right" },
    { key: "status",   header: "Status",   width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "updated",  header: "Updated",  width: 100, align: "right" },
  ];
  return (
    <Section
      kicker="03 · Verify queue"
      title="Submitted by foremen · awaiting your verify"
      caption="Backed by /api/incidents?status=submitted and /api/daily-reports?status=needs_revision. Verify-or-revise actions live inside the linked surfaces."
      testId="pm-v2-section-verify"
      action={<RealLink to="/pm/incidents?status=pending_verification" testid="pm-v2-verify-open">Open Verify Queue</RealLink>}
    >
      <div data-testid="pm-v2-verify-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <DataTable
          data-testid="pm-v2-incidents-queue-table"
          columns={incCols}
          rows={INCIDENTS_QUEUE}
          rowKey={(r) => r.id}
          caption="Incidents · submitted"
          empty={<EmptyState title="No incidents pending verify." severity="good" />}
        />
        <DataTable
          data-testid="pm-v2-daily-queue-table"
          columns={dailyCols}
          rows={DAILY_TO_REVISE}
          rowKey={(r) => r.id}
          caption="Daily Reports · needs revision"
          empty={<EmptyState title="All daily reports verified." severity="good" />}
        />
      </div>
    </Section>
  );
}

function CapaAndConstraints() {
  const capaCols = [
    { key: "id",      header: "CAPA",                width: 110 },
    { key: "project", header: "Project",             width: 90 },
    { key: "title",   header: "Corrective Action",   wrap: true },
    { key: "due",     header: "Due",                 width: 120 },
    { key: "status",  header: "Status",              width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  const cstCols = [
    { key: "id",      header: "Constraint",   width: 110 },
    { key: "project", header: "Project",      width: 90 },
    { key: "title",   header: "Issue",        wrap: true },
    { key: "owner",   header: "Owner",        width: 130 },
    { key: "status",  header: "Status",       width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "updated", header: "Updated",      width: 90, align: "right" },
  ];
  return (
    <Section
      kicker="04 · Close-out queues"
      title="CAPAs & Project Constraints"
      caption="Backed by /api/pm/crew/capas and /api/constraints (real engines). Both queues drive 'project ready to close' decisions."
      testId="pm-v2-section-capa-constraints"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <DataTable
          data-testid="pm-v2-capas-table"
          columns={capaCols}
          rows={CAPA_QUEUE}
          rowKey={(r) => r.id}
          caption="CAPAs due this week"
          empty={<EmptyState title="No CAPAs due this week." severity="good" />}
        />
        <DataTable
          data-testid="pm-v2-constraints-table"
          columns={cstCols}
          rows={CONSTRAINTS_QUEUE}
          rowKey={(r) => r.id}
          caption="Open project constraints"
          empty={<EmptyState title="No open constraints." severity="good" />}
        />
      </div>
    </Section>
  );
}

function FieldEvidence() {
  return (
    <Section
      kicker="05 · Field evidence"
      title="Today's photos & daily reports"
      caption="Both link straight to the real PM surfaces. No mock thumbnails — operator opens the real library."
      testId="pm-v2-section-evidence"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
        <Link to="/pm/photos" data-testid="pm-v2-photos-card" style={{ textDecoration: "none", color: "inherit" }}>
          <Card
            title="Job Photos Library"
            description="Backed by /pm/photos · real R2 storage. No mock thumbnails are rendered here — open the real library to review."
            status={<StatusChip statusKey="verified" compact />}
          />
        </Link>
        <Link to="/pm/daily" data-testid="pm-v2-daily-card" style={{ textDecoration: "none", color: "inherit" }}>
          <Card
            title="All Daily Reports"
            description="Backed by /api/daily-reports — PM-scoped read + verify chain."
            status={<StatusChip statusKey="submitted" compact />}
          />
        </Link>
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
          background: "var(--brand-primary)", color: "var(--brand-on-primary)",
          padding: "10px 16px", fontSize: 12, letterSpacing: "0.04em",
          textTransform: "uppercase", fontWeight: 700, textAlign: "center",
        }}
      >
        Internal · PM V2 Preview · Track 13.6B · Action queues only · Every card opens a real PM surface · No route swap
      </div>

      <PortalShell
        portalName="MASCI"
        portalRole="PM Portal · V2 Preview · Action-Queue Edition"
        pageTitle={`What requires your attention today, ${MOCK_PM.name.split(" ")[0]}?`}
        subtitle={`${MOCK_PM.role} · ${MOCK_PM.region}. PM purpose: BUILD PROJECTS. Every surface below is a queue you can act on — counts are queue sizes, never vanity numbers.`}
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/pm/daily?status=needs_revision" testid="pm-v2-action-revise">Daily Reports To Revise</RealLink>
            <RealLink to="/pm/command-center" testid="pm-v2-action-cc" intent="primary">Open Command Center</RealLink>
          </div>
        }
        lastActivity={<span data-testid="pm-v2-last-activity">Preview only · live PM portal continues at /pm/*</span>}
      >
        <ActionQueues />
        <ProjectsNeedingAction />
        <VerifyQueue />
        <CapaAndConstraints />
        <FieldEvidence />

        <div
          data-testid="pm-v2-purpose-note"
          style={{
            marginTop: 16, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>PM portal purpose · enforced in 13.6B:</strong>
          {" "}<em>Build projects.</em> Every visible object on this preview serves that purpose.
          {" "}Anything that did not — vanity totals, count-of-everything cards, RFI/Submittal/Risk mocks — was removed.
          {" "}Counts here are queue sizes (work-to-do), never inventory tallies.
        </div>
      </PortalShell>
    </div>
  );
}
