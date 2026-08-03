// Track 13.6B · HR Portal V2 Preview — Action-Queue Conversion.
//
// PHILOSOPHY (13.6B Rules):
//   #1 NO DEAD OBJECTS · #2 EVERY KPI LEADS SOMEWHERE · #3 ACTIONS OVER NUMBERS
//   #4 HR purpose: MAINTAIN WORKFORCE READINESS. Nothing on this surface may
//      exist if it does not serve workforce readiness.
//
// EVERY VISIBLE OBJECT ANSWERS:
//   1. What is this?       (header + caption)
//   2. Where from?         (caption names the backing /api/hr/* endpoint)
//   3. Why does it matter? (operator action implied by chip + variant)
//   4. What happens when clicked? (Link to a real /hr route)
//
// STRICT BOUNDARIES:
//   • No /api/hr/* fetch (mock fixtures only).
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

const MOCK_HR = { name: "Alex Rivera", role: "HR Manager", region: "All Florida regions" };

// Action queues only — counts are queue sizes, not headcount totals.
const ACTION_QUEUES = [
  {
    id: "pending_requests",
    title: "Employee Requests · pending",
    metric: 5,
    caption: "Employee requests still waiting on an HR decision",
    why: "PTO · offboard · reactivate · profile changes — HR action required",
    statusKey: "pending_verification",
    variant: "warning",
    to: "/hr/time-off?status=pending",
  },
  {
    id: "certs_expiring",
    title: "Credentials Expiring in 30 d",
    metric: 11,
    caption: "Driver qualification and training renewals due soon",
    why: "Renewals must be scheduled before expiry · field readiness at risk",
    statusKey: "submitted",
    variant: "warning",
    to: "/hr/driver-qualification?expiring=30",
  },
  {
    id: "daily_attention",
    title: "Daily Reports Flagged by HR",
    metric: 2,
    caption: "Crew reports with time and payroll questions",
    why: "Man-hour discrepancies · payroll variance check before lock",
    statusKey: "needs_revision",
    variant: "warning",
    to: "/hr/payroll-variance",
  },
  {
    id: "accountability_open",
    title: "Accountability Signals Open",
    metric: 3,
    caption: "Open accountability items still needing follow-up",
    why: "Coaching signals (positive + attention) · review and close",
    statusKey: "submitted",
    variant: "default",
    to: "/hr/employee-accountability",
  },
];

// Operational readiness queues — every row is a person who needs HR action.
const READINESS_REQUESTS = [
  { id: "REQ-3120", employee: "Garcia, L.",  kind: "PTO",         when: "Today",     status: "submitted",            owner: "HR" },
  { id: "REQ-3119", employee: "Patel, R.",   kind: "Offboard",    when: "Today",     status: "pending_verification", owner: "HR" },
  { id: "REQ-3118", employee: "Nguyen, T.",  kind: "Reactivate",  when: "Yesterday", status: "submitted",            owner: "HR" },
];

const EXPIRING_DRIVERS = [
  { id: "DQ-1203", driver: "Diaz, R.",   license: "CDL-B · FL", expires: "2026-06-30", days: 18,  status: "pending_verification" },
  { id: "DQ-1202", driver: "Singh, A.",  license: "CDL-A · FL", expires: "2026-07-04", days: 22,  status: "submitted" },
];

const EXPIRING_TRAINING = [
  { id: "TR-440", topic: "Trench Safety Refresher",   audience: "All field",  due: "30 days", status: "submitted" },
  { id: "TR-441", topic: "Hazcom · annual",           audience: "All field",  due: "60 days", status: "submitted" },
];

const ACCOUNTABILITY_OPEN = [
  { id: "ACC-9001", employee: "Crew B · Smith, A.",    signal: "Late starts (3 in 14d)",          severity: "attention", updated: "Today" },
  { id: "ACC-9002", employee: "Crew D · Johnson, K.",  signal: "Missing equipment return",         severity: "attention", updated: "Yesterday" },
  { id: "ACC-9003", employee: "Crew A · Williams, P.", signal: "Coaching · positive recognition",  severity: "positive",  updated: "Mon" },
];

const PAYROLL_FLAGS = [
  { id: "DR-7410", project: "21-06", crew: "Crew B", manhours: 42, flag: "−6 hrs vs Motive ELD", status: "needs_revision", updated: "1 hr ago" },
  { id: "DR-7405", project: "23-02", crew: "Crew C", manhours: 78, flag: "Overtime threshold",   status: "needs_revision", updated: "yesterday" },
];

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
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
    }}>{children}</Link>
  );
}

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
      title="Open HR action queues"
      caption="Every card opens a live HR work queue. Numbers reflect work waiting on action, not inventory totals."
      testId="hr-v2-section-queues"
    >
      <div data-testid="hr-v2-queue-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
        {ACTION_QUEUES.map((q) => (
          <ActionQueueCard key={q.id} to={q.to} testid={`hr-v2-queue-${q.id}`} queue={q} />
        ))}
      </div>
    </Section>
  );
}

function RequestsQueue() {
  const [sort, setSort] = useState({ key: "id", direction: "desc" });
  const rows = useMemo(() => {
    const dir = sort.direction === "asc" ? 1 : -1;
    return [...READINESS_REQUESTS].sort((a, b) => (a[sort.key] > b[sort.key] ? dir : -dir));
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
      title="PTO · Offboard · Reactivate · Profile changes"
      caption="Employee requests that still need an HR decision inside the live portal."
      testId="hr-v2-section-requests"
      action={<RealLink to="/hr/time-off?status=pending" testid="hr-v2-requests-open">Open Time-Off Queue</RealLink>}
    >
      <DataTable
        data-testid="hr-v2-requests-table"
        columns={cols}
        rows={rows}
        rowKey={(r) => r.id}
        sort={sort}
        onSortChange={setSort}
        empty={<EmptyState title="No employee requests pending." severity="good" />}
      />
    </Section>
  );
}

function ComplianceExpiry() {
  const dqCols = [
    { key: "id",       header: "ID",       width: 100 },
    { key: "driver",   header: "Driver",   wrap: true },
    { key: "license",  header: "License",  width: 130 },
    { key: "expires",  header: "Expires",  width: 120 },
    { key: "days",     header: "Days",     width: 70, align: "right" },
    { key: "status",   header: "Status",   width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  const tCols = [
    { key: "id",       header: "ID",        width: 80 },
    { key: "topic",    header: "Training",  wrap: true },
    { key: "audience", header: "Audience",  width: 120 },
    { key: "due",      header: "Due",       width: 90 },
    { key: "status",   header: "Status",    width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
  ];
  return (
    <Section
      kicker="03 · Compliance expiry queue"
      title="Driver qualification & training renewals"
      caption="Driver qualification and training renewals due within the next 30 days."
      testId="hr-v2-section-compliance"
    >
      <div data-testid="hr-v2-compliance-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
        <DataTable
          data-testid="hr-v2-driver-qual-table"
          columns={dqCols}
          rows={EXPIRING_DRIVERS}
          rowKey={(r) => r.id}
          caption="Driver qualifications · expiring ≤ 30d"
          empty={<EmptyState title="No driver qualifications expiring." severity="good" />}
        />
        <DataTable
          data-testid="hr-v2-training-table"
          columns={tCols}
          rows={EXPIRING_TRAINING}
          rowKey={(r) => r.id}
          caption="Training · due within 60d"
          empty={<EmptyState title="No training renewals due." severity="good" />}
        />
      </div>
    </Section>
  );
}

function PayrollVariance() {
  const cols = [
    { key: "id",       header: "Report",  width: 100 },
    { key: "project",  header: "Project", width: 80 },
    { key: "crew",     header: "Crew",    width: 80 },
    { key: "manhours", header: "Hours",   width: 70, align: "right" },
    { key: "flag",     header: "Flag",    wrap: true },
    { key: "status",   header: "Status",  width: 170, render: (r) => <StatusChip statusKey={r.status} compact /> },
    { key: "updated",  header: "Updated", width: 100, align: "right" },
  ];
  return (
    <Section
      kicker="04 · Payroll variance"
      title="Man-hour flags before payroll lock"
      caption="Payroll differences flagged before lock so HR can review the source records."
      testId="hr-v2-section-payroll"
      action={<RealLink to="/hr/payroll-variance" testid="hr-v2-payroll-open">Open Payroll Variance</RealLink>}
    >
      <DataTable
        data-testid="hr-v2-payroll-table"
        columns={cols}
        rows={PAYROLL_FLAGS}
        rowKey={(r) => r.id}
        empty={<EmptyState title="No payroll variance flags this week." severity="good" />}
      />
    </Section>
  );
}

function Accountability() {
  const cols = [
    { key: "id",       header: "ID",       width: 110 },
    { key: "employee", header: "Employee", wrap: true },
    { key: "signal",   header: "Signal",   wrap: true },
    {
      key: "severity",
      header: "Severity",
      width: 140,
      render: (r) => <StatusChip label={r.severity[0].toUpperCase() + r.severity.slice(1)} severity={r.severity === "positive" ? "positive" : "attention"} compact />,
    },
    { key: "updated", header: "Updated", width: 100, align: "right" },
  ];
  return (
    <Section
      kicker="05 · Accountability signals"
      title="Open coaching items (positive + attention)"
      caption="Read the full context, support the crew, and close the loop with the same calm voice used across the platform."
      testId="hr-v2-section-accountability"
      action={<RealLink to="/hr/employee-accountability" testid="hr-v2-accountability-open">Open Accountability</RealLink>}
    >
      <DataTable
        data-testid="hr-v2-accountability-table"
        columns={cols}
        rows={ACCOUNTABILITY_OPEN}
        rowKey={(r) => r.id}
        empty={<EmptyState title="No open accountability signals." severity="good" />}
      />
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
          background: "var(--brand-primary)", color: "var(--brand-on-primary)",
          padding: "10px 16px", fontSize: 12, letterSpacing: "0.04em",
          textTransform: "uppercase", fontWeight: 700, textAlign: "center",
        }}
      >
        HR Portal · Action queues
      </div>

      <PortalShell
        portalName="MASCI"
        portalRole="HR Portal · Action Queue Workspace"
        pageTitle={`What requires your attention today, ${MOCK_HR.name.split(" ")[0]}?`}
        subtitle={`${MOCK_HR.role} · ${MOCK_HR.region}. HR purpose: MAINTAIN WORKFORCE READINESS. Every surface below is a queue of people who need an HR action — never a vanity headcount.`}
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/hr/driver-qualification?expiring=30" testid="hr-v2-action-expiring">Expiring Credentials</RealLink>
            <RealLink to="/hr/employee-accountability" testid="hr-v2-action-accountability" intent="primary">Open Accountability</RealLink>
          </div>
        }
        lastActivity={<span data-testid="hr-v2-last-activity">Live HR action queues ready</span>}
      >
        <ActionQueues />
        <RequestsQueue />
        <ComplianceExpiry />
        <PayrollVariance />
        <Accountability />

        <div
          data-testid="hr-v2-purpose-note"
          style={{
            marginTop: 16, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>HR portal purpose:</strong>
          {" "}<em>Maintain workforce readiness.</em> Every visible card and row represents a person or a person&apos;s compliance item that needs HR action.
          {" "}Vanity headcount ({"\u201C"}217 employees{"\u201D"}) is intentionally absent — Active Employees lives in the live HR Hub for inventory; this workspace stays focused on action.
        </div>
      </PortalShell>
    </div>
  );
}
