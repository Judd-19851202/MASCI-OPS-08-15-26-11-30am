// Track 13.6A · HR Portal V2 Preview — Operational Recovery Phase 1.
//
// PURPOSE
//   Lowest-risk preview lane for a future HR portal redesign. Mounted ONLY at
//   /_internal/hr-v2-preview. Built entirely on Phase B1 primitives. No live
//   HR route, form, workflow, content model, or role behavior is touched.
//
// HARD RULE (13.6A):
//   No visible object may exist unless it does something real. Every card
//   and table on this page corresponds to a live HR API endpoint that
//   already exists in `/app/backend/routes/hr_portal.py` and ships in
//   production HR. RFIs, Submittals, mock dashboards, fake KPIs are
//   absent by design.
//
// STRICT BOUNDARIES:
//   • No /api/hr/* fetch in this preview (mock fixtures only).
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
// MOCK FIXTURES — every row mirrors data shape returned by real HR APIs.
// ─────────────────────────────────────────────────────────────────────────────

const MOCK_HR = {
  name: "Alex Rivera",
  role: "HR Manager",
  region: "All Florida regions",
};

// Each pulse card links to the live HR route it summarises. No card without
// a real destination is rendered.
const TODAY_PULSE = [
  {
    id: "active_employees",
    title: "Active Employees",
    metric: 217,
    caption: "headcount as of today",
    statusKey: "verified",
    variant: "default",
    to: "/hr",
    api: "/api/hr/employees",
  },
  {
    id: "pending_requests",
    title: "Pending Employee Requests",
    metric: 5,
    caption: "PTO + offboard + other",
    statusKey: "pending_verification",
    variant: "warning",
    to: "/hr/time-off",
    api: "/api/hr/employee-requests",
  },
  {
    id: "daily_attention",
    title: "Daily Reports Needing HR Attention",
    metric: 2,
    caption: "manhours discrepancies",
    statusKey: "needs_revision",
    variant: "warning",
    to: "/hr/daily-reports",
    api: "/api/hr/daily-reports",
  },
  {
    id: "training_due",
    title: "Training Records Expiring (30d)",
    metric: 11,
    caption: "renewals coming due",
    statusKey: "submitted",
    variant: "default",
    to: "/hr/training-records",
    api: "/api/hr/training-records",
  },
];

const REQUESTS = [
  { id: "REQ-3120", employee: "Garcia, L.",  kind: "PTO",        when: "Today",     status: "submitted",            owner: "HR" },
  { id: "REQ-3119", employee: "Patel, R.",   kind: "Offboard",   when: "Today",     status: "pending_verification", owner: "HR" },
  { id: "REQ-3118", employee: "Nguyen, T.",  kind: "Reactivate", when: "Yesterday", status: "submitted",            owner: "HR" },
  { id: "REQ-3117", employee: "Brown, J.",   kind: "PTO",        when: "Yesterday", status: "verified",             owner: "HR" },
  { id: "REQ-3116", employee: "Lopez, M.",   kind: "Address",    when: "2 days",    status: "verified",             owner: "HR" },
];

const ACCOUNTABILITY = [
  { id: "ACC-9001", employee: "Crew B · Smith, A.",    summary: "Late starts (3 in 14d)",          severity: "attention", updated: "Today" },
  { id: "ACC-9002", employee: "Crew D · Johnson, K.",  summary: "Missing equipment return",         severity: "attention", updated: "Yesterday" },
  { id: "ACC-9003", employee: "Crew A · Williams, P.", summary: "Coaching · positive recognition",  severity: "positive",  updated: "Mon" },
];

const DAILY_REPORTS_HR_VIEW = [
  { id: "DR-7411", project: "20-07", crew: "Crew A", manhours: 78, status: "submitted",        updated: "12 min ago" },
  { id: "DR-7410", project: "21-06", crew: "Crew B", manhours: 42, status: "needs_revision",  updated: "1 hr ago" },
  { id: "DR-7409", project: "22-11", crew: "Crew C", manhours: 38, status: "submitted",        updated: "32 min ago" },
  { id: "DR-7408", project: "23-09", crew: "Crew D", manhours: 22, status: "submitted",        updated: "4 min ago" },
];

const DRIVER_QUAL = [
  { id: "DQ-1201", driver: "Hernandez, J.", license: "CDL-A · FL", expires: "2026-08-12", status: "verified" },
  { id: "DQ-1202", driver: "Singh, A.",     license: "CDL-A · FL", expires: "2026-07-04", status: "submitted" },
  { id: "DQ-1203", driver: "Diaz, R.",      license: "CDL-B · FL", expires: "2026-06-30", status: "pending_verification" },
];

const TRAINING = [
  { id: "TR-440", topic: "Trench Safety Refresher",   audience: "All field",  due: "30 days", status: "submitted" },
  { id: "TR-441", topic: "Hazcom · annual",            audience: "All field",  due: "60 days", status: "submitted" },
  { id: "TR-442", topic: "Forklift recertification",   audience: "Shop",       due: "Closed",  status: "verified" },
];

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

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
        <h2 style={{ margin: "2px 0 0", fontSize: 18, fontWeight: 700, color: "var(--ink-strong)", fontFamily: "var(--font-display)" }}>
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
    <section data-testid={testId} style={{ marginBottom: 28 }}>
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

function Pulse() {
  return (
    <Section
      kicker="01 · What requires HR attention today"
      title="Today's pulse"
      caption="Every card links to a real /hr route backed by a real /api/hr endpoint. No vanity metrics."
      testId="hr-v2-section-pulse"
    >
      <div
        data-testid="hr-v2-pulse-grid"
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
            testid={`hr-v2-pulse-${p.id}`}
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

function EmployeeRequests() {
  const [sort, setSort] = useState({ key: "id", direction: "desc" });
  const rows = useMemo(() => {
    const dir = sort.direction === "asc" ? 1 : -1;
    return [...REQUESTS].sort((a, b) => (a[sort.key] > b[sort.key] ? dir : -dir));
  }, [sort]);

  const cols = [
    { key: "id",       header: "ID",        width: 110, sortable: true },
    { key: "employee", header: "Employee",  sortable: true, wrap: true },
    { key: "kind",     header: "Type",      width: 120 },
    { key: "when",     header: "When",      width: 120 },
    { key: "status",   header: "Status",    width: 180, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "owner",    header: "Owner",     width: 90 },
  ];
  return (
    <Section
      kicker="02 · Employee Requests"
      title="Pending PTO, offboard, reactivation, profile changes"
      caption="Backed by /api/hr/employee-requests in the live HR portal."
      testId="hr-v2-section-requests"
      action={<RealLink to="/hr/time-off" testid="hr-v2-requests-open">Open Time-Off Queue</RealLink>}
    >
      <DataTable
        data-testid="hr-v2-requests-table"
        columns={cols}
        rows={rows}
        rowKey={(r) => r.id}
        sort={sort}
        onSortChange={setSort}
      />
    </Section>
  );
}

function EmployeeAccountability() {
  const cols = [
    { key: "id",       header: "ID",       width: 110 },
    { key: "employee", header: "Employee", wrap: true },
    { key: "summary",  header: "Signal",   wrap: true },
    {
      key: "severity",
      header: "Severity",
      width: 140,
      render: (r) => <StatusChip label={r.severity[0].toUpperCase() + r.severity.slice(1)} severity={r.severity === "positive" ? "positive" : "attention"} compact />,
    },
    { key: "updated",  header: "Updated",  width: 100, align: "right" },
  ];
  return (
    <Section
      kicker="03 · Employee Accountability"
      title="Crew signals"
      caption="Backed by /api/hr/employee-accountability — calm, non-punitive voice (positive recognition + attention items)."
      testId="hr-v2-section-accountability"
      action={<RealLink to="/hr/employee-accountability" testid="hr-v2-accountability-open">Open Accountability</RealLink>}
    >
      <DataTable
        data-testid="hr-v2-accountability-table"
        columns={cols}
        rows={ACCOUNTABILITY}
        rowKey={(r) => r.id}
      />
    </Section>
  );
}

function DailyReportsHrView() {
  const cols = [
    { key: "id",       header: "Report",   width: 110 },
    { key: "project",  header: "Project",  width: 90 },
    { key: "crew",     header: "Crew",     width: 90 },
    { key: "manhours", header: "Man-hours", width: 110, align: "right" },
    { key: "status",   header: "Status",   width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "updated",  header: "Updated",  width: 110, align: "right" },
  ];
  return (
    <Section
      kicker="04 · Daily Reports · HR view"
      title="Today's manhours signals"
      caption="Read-only HR view of /api/daily-reports — HR verifies time but never edits engine records."
      testId="hr-v2-section-daily"
      action={<RealLink to="/hr/daily-reports" testid="hr-v2-daily-open">Open Daily Reports</RealLink>}
    >
      <DataTable
        data-testid="hr-v2-daily-table"
        columns={cols}
        rows={DAILY_REPORTS_HR_VIEW}
        rowKey={(r) => r.id}
      />
    </Section>
  );
}

function Compliance() {
  const driverCols = [
    { key: "id",      header: "ID",       width: 100 },
    { key: "driver",  header: "Driver",   wrap: true },
    { key: "license", header: "License",  width: 130 },
    { key: "expires", header: "Expires",  width: 120 },
    { key: "status",  header: "Status",   width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  const trainingCols = [
    { key: "id",       header: "ID",        width: 90 },
    { key: "topic",    header: "Training",  wrap: true },
    { key: "audience", header: "Audience",  width: 120 },
    { key: "due",      header: "Due",       width: 100 },
    { key: "status",   header: "Status",    width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  return (
    <Section
      kicker="05 · Compliance"
      title="Driver qualification & training currency"
      caption="Backed by /api/hr/driver-qualification/dashboard and /api/hr/training-records."
      testId="hr-v2-section-compliance"
    >
      <div data-testid="hr-v2-compliance-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <DataTable data-testid="hr-v2-driver-qual-table" columns={driverCols}   rows={DRIVER_QUAL} rowKey={(r) => r.id} caption="Driver Qualification" />
        <DataTable data-testid="hr-v2-training-table"    columns={trainingCols} rows={TRAINING}    rowKey={(r) => r.id} caption="Training" />
      </div>
    </Section>
  );
}

function CalmStates() {
  return (
    <Section
      kicker="06 · Calm states"
      title="What 'nothing wrong' looks like in HR"
      caption="The HR portal does not invent anxiety. When all signals are calm, you see calm."
      testId="hr-v2-section-empty"
    >
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
        <EmptyState
          title="No open offboards this week."
          explanation="Smooth week. Routine onboarding only."
          severity="good"
        />
        <EmptyState
          title="No incident-related HR follow-ups."
          explanation="No safety event has surfaced an HR action item."
          severity="neutral"
        />
        <EmptyState
          title="One driver qualification expiring this week."
          explanation="Singh, A. · CDL-A · expires 2026-07-04. Renewal reminder scheduled."
          severity="attention"
        />
      </div>
    </Section>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function HrV2Preview() {
  return (
    <div data-testid="hr-v2-preview-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <div
        data-testid="hr-v2-preview-banner"
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
        Internal · HR Portal V2 Preview · Track 13.6A Recovery · Mock pulse · Real-engine surfaces only · No live HR route changed
      </div>

      <PortalShell
        portalName="MASCI"
        portalRole="HR Portal · V2 Preview"
        pageTitle={`What requires your attention today, ${MOCK_HR.name.split(" ")[0]}?`}
        subtitle={`${MOCK_HR.role} · ${MOCK_HR.region}. HR content model, workflows, routes, and role clarity are preserved. This preview only renders the visual language.`}
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/hr/employee-accountability" testid="hr-v2-action-accountability">Accountability</RealLink>
            <RealLink to="/hr" testid="hr-v2-action-hub" intent="primary">Open HR Hub</RealLink>
          </div>
        }
        lastActivity={<span data-testid="hr-v2-last-activity">Preview only · live HR portal continues at /hr/*</span>}
      >
        <Pulse />
        <EmployeeRequests />
        <EmployeeAccountability />
        <DailyReportsHrView />
        <Compliance />
        <CalmStates />

        <div
          data-testid="hr-v2-boundary-note"
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
          <strong style={{ color: "var(--ink-strong)" }}>Phase 13.6A boundary.</strong>
          {" "}HR content model, workflows, routes, data logic, and role clarity are preserved byte-for-byte.
          {" "}Every primitive on this page is backed by an HR endpoint that already ships
          (`/api/hr/employees`, `/api/hr/employee-requests`, `/api/hr/daily-reports`, `/api/hr/employee-accountability`,
          {" "}`/api/hr/driver-qualification/dashboard`, `/api/hr/training-records`).
          {" "}No HR route is swapped. No HR form is touched.
        </div>
      </PortalShell>
    </div>
  );
}
