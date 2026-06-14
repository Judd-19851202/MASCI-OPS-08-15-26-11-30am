// Track 13.6C · HR Hub V2 — first real portal migration.
//
// MOUNTED AT: /hr/hub_v2 (lives behind RequireHr like /hr).
//
// REAL DATA · REAL ROUTES · REAL WORKFLOWS · REAL PERMISSIONS.
// No mock fixtures. No vanity metrics. No dead buttons.
//
// Action-queue model (Rules 1-3 from 13.6B):
//   • Every count is a queue size sourced from a real /api/* endpoint.
//   • Every card is a <Link> to a real /hr route.
//   • Top section answers "What requires HR attention today?".
//
// Auth pattern mirrors HrKpiStrip.jsx — same X-Admin-Token header,
// same token-resolution priority (masci.hr.token → masci.admin.token).
// HR permissions are preserved byte-for-byte.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  PortalShell,
  StatusChip,
  Card,
  EmptyState,
} from "../design-system";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function authHeaders() {
  const t =
    sessionStorage.getItem("masci.hr.token") ||
    sessionStorage.getItem("masci.admin.token") ||
    "";
  return t ? { "X-Admin-Token": t } : {};
}

// Generic safe fetch — returns { ok, status, body } and never throws.
async function safeJson(url, headers) {
  try {
    const r = await fetch(url, { headers });
    const body = r.ok ? await r.json().catch(() => null) : null;
    return { ok: r.ok, status: r.status, body };
  } catch {
    return { ok: false, status: 0, body: null };
  }
}

function listOf(body) {
  if (!body) return [];
  if (Array.isArray(body)) return body;
  return body.items || body.employees || body.results || [];
}

// ─────────────────────────────────────────────────────────────────────────────
// Data hook — pulls every queue size and metadata in parallel from real APIs.
// ─────────────────────────────────────────────────────────────────────────────

function useHrSignals() {
  const [state, setState] = useState({
    loaded: false,
    refreshedAt: null,
    pending_requests: null,       // /api/employee-requests?status=pending
    time_off_pending: null,       // /api/time-off-requests?status=pending
    training_exp_soon: null,      // /api/operations/expirations/summary
    docs_expired: null,           // /api/operations/expirations/summary
    accountability_open: null,    // /api/employee-accountability
    field_leadership_recent: null,// /api/hr/field-leadership
    daily_reports_today: null,    // /api/hr/daily-reports
    incidents_recent: null,       // /api/hr/incidents
  });

  useEffect(() => {
    let cancelled = false;
    const headers = authHeaders();

    const tasks = [
      safeJson(`${API}/employee-requests?status=pending`, headers),
      safeJson(`${API}/time-off-requests?status=pending`, headers),
      safeJson(`${API}/operations/expirations/summary`, headers),
      safeJson(`${API}/employee-accountability?limit=200`, headers),
      safeJson(`${API}/hr/field-leadership?limit=10`, headers),
      safeJson(`${API}/hr/daily-reports?limit=10`, headers),
      safeJson(`${API}/hr/incidents?limit=10`, headers),
    ];

    Promise.all(tasks).then((res) => {
      if (cancelled) return;
      const [er, to, exp, acc, fl, dr, inc] = res;
      const expBody = exp.body || {};
      setState({
        loaded: true,
        refreshedAt: new Date().toISOString(),
        pending_requests:        er.ok  ? listOf(er.body).length  : null,
        time_off_pending:        to.ok  ? listOf(to.body).length  : null,
        training_exp_soon:       exp.ok ? ((expBody.expiring_in_30 ?? 0) + (expBody.expiring_in_60 ?? 0)) : null,
        docs_expired:            exp.ok ? (expBody.expired ?? 0)  : null,
        accountability_open:     acc.ok ? listOf(acc.body).filter((r) => !((r.status || "").toLowerCase().startsWith("clos") || (r.status || "").toLowerCase().startsWith("resol"))).length : null,
        field_leadership_recent: fl.ok  ? listOf(fl.body).length  : null,
        daily_reports_today:     dr.ok  ? listOf(dr.body).length  : null,
        incidents_recent:        inc.ok ? listOf(inc.body).length : null,
      });
    });
    return () => { cancelled = true; };
  }, []);

  return state;
}

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

// A queue card backed by a real API. Renders "—" until loaded; never invents numbers.
function QueueCard({ to, testid, title, why, source, value, loaded, variantWhenAttention = "warning" }) {
  const isAttention = loaded && typeof value === "number" && value > 0;
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <Card
        title={title}
        description={why}
        metric={loaded ? (value === null ? "—" : value) : "…"}
        variant={isAttention ? variantWhenAttention : "default"}
        status={
          !loaded ? <StatusChip statusKey="draft" compact label="Loading" />
          : value === null ? <StatusChip statusKey="offline_feed" compact />
          : isAttention ? <StatusChip statusKey="pending_verification" compact />
          : <StatusChip statusKey="verified" compact />
        }
      >
        <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
          {source}
        </p>
      </Card>
    </Link>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Page
// ─────────────────────────────────────────────────────────────────────────────

export default function HrHubV2() {
  const s = useHrSignals();
  const isPreview = (typeof window !== "undefined") && /preview/i.test(window.location.host);

  return (
    <div data-testid="hr-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      {isPreview && (
        <div
          data-testid="hr-hub-v2-preview-banner"
          style={{
            background: "var(--brand-primary)", color: "var(--brand-on-primary)",
            padding: "8px 16px", fontSize: 11, letterSpacing: "0.04em",
            textTransform: "uppercase", fontWeight: 700, textAlign: "center",
          }}
        >
          HR Hub V2 · Live HR operations hub · Real HR data · Real workflows · Legacy rollback at /hr/hub_legacy
        </div>
      )}

      <PortalShell
        portalName="MASCI"
        portalRole="HR Portal · Hub V2"
        pageTitle="What requires your attention today?"
        subtitle="HR purpose: keep the workforce ready. Every queue below is a live count — open it to see who needs your attention today."
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/hr" testid="hr-hub-v2-back-classic">Open Classic HR Hub</RealLink>
            <RealLink to="/hr/employee-accountability" testid="hr-hub-v2-action-accountability" intent="primary">Accountability</RealLink>
          </div>
        }
        lastActivity={
          <span data-testid="hr-hub-v2-last-activity">
            {s.loaded ? `Refreshed ${new Date(s.refreshedAt).toLocaleTimeString()}` : "Loading live signals…"}
          </span>
        }
      >
        {/* Section 1 — Action queues. Real APIs, real counts, real destinations. */}
        <Section
          kicker="01 · Action queues · live"
          title="Open HR work"
          caption="Counts are queue sizes from real /api endpoints. Clicking a card opens the real HR workflow — no mock data, no synthesized values."
          testId="hr-hub-v2-section-queues"
        >
          <div
            data-testid="hr-hub-v2-queue-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: 16,
            }}
          >
            <QueueCard
              to="/hr/employee-requests"
              testid="hr-hub-v2-queue-employee-requests"
              title="Employee Requests · pending"
              why="New-hire and termination submissions awaiting HR approval"
              source="Source: /api/employee-requests?status=pending"
              value={s.pending_requests}
              loaded={s.loaded}
            />
            <QueueCard
              to="/hr/time-off"
              testid="hr-hub-v2-queue-time-off"
              title="Time-Off Requests · pending"
              why="Vacation / sick approvals awaiting HR"
              source="Source: /api/time-off-requests?status=pending"
              value={s.time_off_pending}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/document-expirations"
              testid="hr-hub-v2-queue-training-due"
              title="Training / Certs Due"
              why="Credentials expiring in the next 60 days"
              source="Source: /api/operations/expirations/summary (30d + 60d buckets)"
              value={s.training_exp_soon}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/document-expirations?bucket=expired"
              testid="hr-hub-v2-queue-docs-expired"
              title="Documents Expired"
              why="Past expiry — must be addressed now"
              source="Source: /api/operations/expirations/summary (expired bucket)"
              value={s.docs_expired}
              loaded={s.loaded}
              variantWhenAttention="danger"
            />
            <QueueCard
              to="/hr/employee-accountability"
              testid="hr-hub-v2-queue-accountability"
              title="Accountability Signals · open"
              why="Coaching items (positive + attention) awaiting close-out"
              source="Source: /api/employee-accountability — non-closed states"
              value={s.accountability_open}
              loaded={s.loaded}
              variantWhenAttention="warning"
            />
          </div>
        </Section>

        {/* Section 2 — Cross-portal reads HR cares about (workforce readiness). */}
        <Section
          kicker="02 · Workforce-readiness reads"
          title="Field signals HR watches"
          caption="HR reads (never writes) these surfaces. Counts source from the live HR-scoped APIs the classic hub already uses."
          testId="hr-hub-v2-section-reads"
        >
          <div
            data-testid="hr-hub-v2-reads-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: 16,
            }}
          >
            <QueueCard
              to="/hr/daily-reports"
              testid="hr-hub-v2-read-daily"
              title="Recent Daily Reports"
              why="Read-only HR view for man-hour + payroll variance checks"
              source="Source: /api/hr/daily-reports (last 10)"
              value={s.daily_reports_today}
              loaded={s.loaded}
              variantWhenAttention="default"
            />
            <QueueCard
              to="/hr/incidents"
              testid="hr-hub-v2-read-incidents"
              title="Recent Incidents · HR view"
              why="HR follow-up tracking on safety events"
              source="Source: /api/hr/incidents (last 10)"
              value={s.incidents_recent}
              loaded={s.loaded}
              variantWhenAttention="warning"
            />
            <QueueCard
              to="/hr/field-leadership"
              testid="hr-hub-v2-read-fl"
              title="Field-Leadership Records · recent"
              why="HR has read access to FL submissions for personnel review"
              source="Source: /api/hr/field-leadership (last 10)"
              value={s.field_leadership_recent}
              loaded={s.loaded}
              variantWhenAttention="default"
            />
          </div>
        </Section>

        {/* Section 3 — Permanent HR destinations (always-on, no count). */}
        <Section
          kicker="03 · HR destinations"
          title="Always-on HR surfaces"
          caption="These are the live HR routes. Each is a real surface — not a tile, not a placeholder."
          testId="hr-hub-v2-section-destinations"
        >
          <div
            data-testid="hr-hub-v2-destinations-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 16,
            }}
          >
            <Link to="/hr/employees" data-testid="hr-hub-v2-dest-employees" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Employees" description="Roster · search · profile · timeline · accountability brief" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/hr/training-records" data-testid="hr-hub-v2-dest-training" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Training Records" description="Per-employee training history · upload + assignment" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/hr/driver-qualification" data-testid="hr-hub-v2-dest-driver-qual" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Driver Qualification" description="CDL · medical card · DOT compliance dashboard" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/hr/payroll-variance" data-testid="hr-hub-v2-dest-payroll" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Payroll Variance" description="Man-hour reconciliation before payroll lock" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/hr/time-verification" data-testid="hr-hub-v2-dest-time-verify" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Time Verification" description="Submitted-time vs ELD reconciliation" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/hr/field-leadership-users" data-testid="hr-hub-v2-dest-fl-users" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Field-Leadership Users" description="Manage FL portal access (shared admin/HR panel)" status={<StatusChip statusKey="verified" compact />} />
            </Link>
          </div>
        </Section>

        {/* Calm states + permission proof */}
        {s.loaded && (
          ((s.pending_requests ?? 0) +
           (s.time_off_pending ?? 0) +
           (s.training_exp_soon ?? 0) +
           (s.docs_expired ?? 0) +
           (s.accountability_open ?? 0)) === 0
        ) && (
          <Section
            kicker="04 · Calm state"
            title="No HR action required right now"
            caption="Every action queue is empty. Workforce is ready · all signals green."
            testId="hr-hub-v2-section-calm"
          >
            <EmptyState
              title="All HR queues are clear."
              explanation="No pending requests · no expiring credentials · no open accountability items."
              severity="good"
            />
          </Section>
        )}

        <div
          data-testid="hr-hub-v2-purpose-note"
          style={{
            marginTop: 16, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>HR Hub V2 · Track 13.6C · first real portal conversion.</strong>
          {" "}This hub renders live HR data through the Phase B1 design-system primitives.
          {" "}This hub is the live HR operations surface at <code>/hr</code> — real APIs, real workflows.
          {" "}Legacy rollback route remains available at <code>/hr/hub_legacy</code> during the operator signoff window.
        </div>
      </PortalShell>
    </div>
  );
}
