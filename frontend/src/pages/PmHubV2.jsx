// Track 13.6D · PM Hub V2 — second real portal migration.
//
// MOUNTED AT: /pm/hub_v2 (behind RequirePm — same gate as /pm).
//
// REAL DATA · REAL ROUTES · REAL WORKFLOWS · REAL PERMISSIONS.
//
// Operator decisions honoured (per 13.6D directive):
//   • Project Risks  → PERMANENTLY renamed to Project Constraints.
//   • RFIs           → FORBIDDEN. Not displayed (no engine).
//   • Submittals     → FORBIDDEN. Not displayed (no engine).
//
// Single question this page answers:
//   "What requires PM attention today?"
//
// Auth pattern mirrors operations/ocCommandApi.js — X-PM-Token from
// pmAuth.getPmToken(). Permissions preserved byte-for-byte.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import {
  PortalShell,
  StatusChip,
  Card,
  EmptyState,
} from "../design-system";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const p = getPmToken();
  if (a) h["X-Admin-Token"] = a;
  if (p) h["X-PM-Token"] = p;
  return h;
}

async function safeJson(path) {
  try {
    const r = await fetch(`${API}${path}`, { headers: authHeaders() });
    const body = r.ok ? await r.json().catch(() => null) : null;
    return { ok: r.ok, status: r.status, body };
  } catch {
    return { ok: false, status: 0, body: null };
  }
}

function listOf(body) {
  if (!body) return [];
  if (Array.isArray(body)) return body;
  return body.items || body.results || body.jobs || body.records || body.daily_reports || body.incidents || body.capas || body.constraints || body.photos || [];
}

// Generic helper: count items matching a status set (case-insensitive).
function countWithStatus(rows, statuses) {
  const set = new Set(statuses.map((s) => s.toLowerCase()));
  return rows.filter((r) => set.has(String(r.status || r.lifecycle_state || "").toLowerCase())).length;
}

// ─────────────────────────────────────────────────────────────────────────────
// Data hook — pulls every PM queue from real APIs in parallel.
// ─────────────────────────────────────────────────────────────────────────────

function usePmSignals() {
  const [s, setS] = useState({
    loaded: false,
    refreshedAt: null,
    daily_needs_review: null,    // /api/daily-reports?status=submitted,needs_revision
    incidents_pending:  null,    // /api/incidents?status=submitted,pending_verification
    capas_due:          null,    // /api/pm/crew/capas (open/pending)
    constraints_open:   null,    // /api/constraints?status=open (or non-closed)
    projects_attention: null,    // /api/pm/jobs (filter to projects with signals)
    qaqc_action:        null,    // /api/qaqc/inspections?status=pending_verification
    crew_accountability:null,    // /api/pm/crew/summary
    photos_recent:      null,    // /api/job-photos?limit=10
  });

  useEffect(() => {
    let cancelled = false;
    const tasks = Promise.all([
      safeJson(`/api/daily-reports?limit=200`),
      safeJson(`/api/incidents?limit=200`),
      safeJson(`/api/pm/crew/capas`),
      safeJson(`/api/constraints?limit=200`),
      safeJson(`/api/pm/jobs`),
      safeJson(`/api/qaqc/inspections?limit=200`),
      safeJson(`/api/pm/crew/summary`),
      safeJson(`/api/job-photos?limit=10`),
    ]);

    tasks.then((res) => {
      if (cancelled) return;
      const [dr, inc, capa, con, jobs, qa, crew, photos] = res;
      const drRows  = dr.ok  ? listOf(dr.body)  : [];
      const incRows = inc.ok ? listOf(inc.body) : [];
      const conRows = con.ok ? listOf(con.body) : [];
      const qaRows  = qa.ok  ? listOf(qa.body)  : [];
      const capaRows= capa.ok? listOf(capa.body): [];
      const jobsRows= jobs.ok? listOf(jobs.body): [];
      const photoRows = photos.ok ? listOf(photos.body) : [];

      // Projects requiring attention = jobs that have ≥1 open signal joined.
      let projectsAtt = null;
      if (jobs.ok) {
        const flaggedKeys = new Set();
        const harvest = (rows) => rows.forEach((r) => {
          const k = r.project_number || r.job_number || r.job_id || r.project_id;
          if (k) flaggedKeys.add(String(k));
        });
        if (dr.ok)  harvest(drRows.filter((r) => /needs_revision|submitted/i.test(r.status || r.lifecycle_state || "")));
        if (inc.ok) harvest(incRows.filter((r) => /submitted|pending_verification/i.test(r.status || r.lifecycle_state || "")));
        if (con.ok) harvest(conRows.filter((r) => !/clos|resolv/i.test(r.status || "")));
        projectsAtt = jobsRows.filter((j) => flaggedKeys.has(String(j.project_number || j.job_number || j.id || ""))).length;
      }

      setS({
        loaded: true,
        refreshedAt: new Date().toISOString(),
        daily_needs_review:  dr.ok  ? countWithStatus(drRows, ["submitted","needs_revision","pending_verification"]) : null,
        incidents_pending:   inc.ok ? countWithStatus(incRows, ["submitted","pending_verification"]) : null,
        capas_due:           capa.ok? capaRows.filter((r) => !/clos|resolv|verif/i.test(r.status || "")).length : null,
        constraints_open:    con.ok ? conRows.filter((r) => !/clos|resolv/i.test(r.status || "")).length : null,
        projects_attention:  projectsAtt,
        qaqc_action:         qa.ok  ? countWithStatus(qaRows, ["submitted","pending_verification","needs_revision"]) : null,
        crew_accountability: crew.ok? (typeof crew.body === "object" && crew.body !== null ? (crew.body.attention_count ?? null) : null) : null,
        photos_recent:       photos.ok ? photoRows.length : null,
      });
    });
    return () => { cancelled = true; };
  }, []);

  return s;
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared helpers (same as HrHubV2)
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

export default function PmHubV2() {
  const s = usePmSignals();
  const isPreview = (typeof window !== "undefined") && /preview/i.test(window.location.host);

  const allZero = s.loaded && [
    s.daily_needs_review, s.incidents_pending, s.capas_due,
    s.constraints_open, s.projects_attention, s.qaqc_action,
    s.crew_accountability, s.photos_recent,
  ].every((v) => v === null || v === 0);

  return (
    <div data-testid="pm-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      {isPreview && (
        <div
          data-testid="pm-hub-v2-preview-banner"
          style={{
            background: "var(--brand-primary)", color: "var(--brand-on-primary)",
            padding: "8px 16px", fontSize: 11, letterSpacing: "0.04em",
            textTransform: "uppercase", fontWeight: 700, textAlign: "center",
          }}
        >
          PM Hub V2 · Live PM data · Side-by-side with /pm/hub · No route swap until operator approval
        </div>
      )}

      <PortalShell
        portalName="MASCI"
        portalRole="PM Portal · Hub V2"
        pageTitle="What requires your attention today?"
        subtitle="PM purpose: build projects. Every queue below is live · sourced from a real /api endpoint · clickable to a real /pm route."
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/pm/hub" testid="pm-hub-v2-back-classic">Open Classic PM Hub</RealLink>
            <RealLink to="/pm/command-center" testid="pm-hub-v2-action-cc" intent="primary">Command Center</RealLink>
          </div>
        }
        lastActivity={
          <span data-testid="pm-hub-v2-last-activity">
            {s.loaded ? `Refreshed ${new Date(s.refreshedAt).toLocaleTimeString()}` : "Loading live signals…"}
          </span>
        }
      >
        {/* Section 1 — Action queues. Real APIs, real counts, real destinations. */}
        <Section
          kicker="01 · Action queues · live"
          title="Open PM work"
          caption="Counts are queue sizes from real /api endpoints. Clicking a card opens the real PM workflow."
          testId="pm-hub-v2-section-queues"
        >
          <div
            data-testid="pm-hub-v2-queue-grid"
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}
          >
            <QueueCard
              to="/pm/daily"
              testid="pm-hub-v2-queue-daily"
              title="Daily Reports Requiring Review"
              why="Foreman-submitted reports awaiting PM verify or revise"
              source="Source: /api/daily-reports — submitted + needs_revision + pending_verification"
              value={s.daily_needs_review}
              loaded={s.loaded}
            />
            <QueueCard
              to="/pm/incidents"
              testid="pm-hub-v2-queue-incidents"
              title="Incidents Awaiting Verification"
              why="Submitted by foreman · must be verified before close"
              source="Source: /api/incidents — submitted + pending_verification"
              value={s.incidents_pending}
              loaded={s.loaded}
            />
            <QueueCard
              to="/pm/incidents?tab=capas"
              testid="pm-hub-v2-queue-capas"
              title="CAPAs Due"
              why="Open corrective actions awaiting close-out"
              source="Source: /api/pm/crew/capas — non-closed"
              value={s.capas_due}
              loaded={s.loaded}
            />
            <QueueCard
              to="/constraints"
              testid="pm-hub-v2-queue-constraints"
              title="Project Constraints Requiring Resolution"
              why="Open constraints blocking project work — Project Risks are permanently relabelled as Project Constraints"
              source="Source: /api/constraints — non-closed"
              value={s.constraints_open}
              loaded={s.loaded}
            />
            <QueueCard
              to="/pm/jobs"
              testid="pm-hub-v2-queue-projects"
              title="Projects Requiring Attention"
              why="Projects with ≥1 open Daily / Incident / Constraint signal"
              source="Source: /api/pm/jobs ⨯ joined live queues"
              value={s.projects_attention}
              loaded={s.loaded}
            />
            <QueueCard
              to="/qa-qc/inspections"
              testid="pm-hub-v2-queue-qaqc"
              title="QA/QC Requiring Action"
              why="Inspections awaiting PM verify or revise"
              source="Source: /api/qaqc/inspections — submitted + pending_verification + needs_revision"
              value={s.qaqc_action}
              loaded={s.loaded}
            />
          </div>
        </Section>

        {/* Section 2 — Reads PM watches but doesn't author. */}
        <Section
          kicker="02 · Field signals PM watches"
          title="Recent field activity"
          caption="Read-only signals from the live PM APIs. Clicking opens the underlying workflow."
          testId="pm-hub-v2-section-reads"
        >
          <div
            data-testid="pm-hub-v2-reads-grid"
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}
          >
            <QueueCard
              to="/pm/crew-compliance"
              testid="pm-hub-v2-read-crew"
              title="Crew Accountability"
              why="Open accountability signals across PM-scoped crews"
              source="Source: /api/pm/crew/summary"
              value={s.crew_accountability}
              loaded={s.loaded}
            />
            <QueueCard
              to="/pm/photos"
              testid="pm-hub-v2-read-photos"
              title="Recent Field Photos"
              why="Newest photo uploads from PM-scoped jobs"
              source="Source: /api/job-photos (last 10)"
              value={s.photos_recent}
              loaded={s.loaded}
              variantWhenAttention="default"
            />
          </div>
        </Section>

        {/* Section 3 — Permanent PM destinations (always-on, no count). */}
        <Section
          kicker="03 · PM destinations"
          title="Always-on PM surfaces"
          caption="These are the live PM routes — each is a real workflow surface, not a placeholder."
          testId="pm-hub-v2-section-destinations"
        >
          <div
            data-testid="pm-hub-v2-destinations-grid"
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}
          >
            <Link to="/pm/jobs" data-testid="pm-hub-v2-dest-jobs" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Projects" description="Scoped list of your projects · per-project drill" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/pm/command-center" data-testid="pm-hub-v2-dest-cc" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Command Center" description="Per-project resources · hauls · materials · timeline" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/pm/fleet" data-testid="pm-hub-v2-dest-fleet" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Fleet" description="PM-scoped equipment view" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/pm/qaqc" data-testid="pm-hub-v2-dest-qaqc" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="QA / QC" description="Quality inspections · per-project" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/pm/crew-compliance" data-testid="pm-hub-v2-dest-crew" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Crew Compliance" description="Per-crew certification + training currency" status={<StatusChip statusKey="verified" compact />} />
            </Link>
            <Link to="/pm/photos" data-testid="pm-hub-v2-dest-photos" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
              <Card title="Job Photos" description="Field photo library · R2-backed" status={<StatusChip statusKey="verified" compact />} />
            </Link>
          </div>
        </Section>

        {allZero && (
          <Section
            kicker="04 · Calm state"
            title="No PM action required right now"
            caption="Every action queue is empty across the live PM signals."
            testId="pm-hub-v2-section-calm"
          >
            <EmptyState
              title="All PM queues are clear."
              explanation="No daily reports awaiting verify · no incidents awaiting verify · no open CAPAs · no open constraints · no QA/QC action."
              severity="good"
            />
          </Section>
        )}

        <div
          data-testid="pm-hub-v2-purpose-note"
          style={{
            marginTop: 16, padding: "var(--pad-card)",
            background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
            borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
          }}
        >
          <strong style={{ color: "var(--ink-strong)" }}>PM Hub V2 · Track 13.6D · second real portal conversion.</strong>
          {" "}This hub renders live PM data through the Phase B1 design-system primitives.
          {" "}It does NOT replace <code>/pm/hub</code> — both routes are live in parallel.
          {" "}Project Risks are permanently relabelled as Project Constraints. Surfaces without a backing MASCI engine are not rendered.
          {" "}Operator approval via <code>/_internal/v2-compare/pm</code> is required before any route swap.
        </div>
      </PortalShell>
    </div>
  );
}
