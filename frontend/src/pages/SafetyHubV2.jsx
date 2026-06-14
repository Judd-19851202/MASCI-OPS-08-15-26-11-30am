// Track 13.6H · Phase 4 — Safety Recovery (live hub).
//
// MOUNTED AT: /safety-portal/hub_v2 (behind RequireSafety — same gate
// as /safety-portal). Classic /safety-portal hub preserved unchanged.
//
// REAL DATA ONLY: pulls every count from /api/safety/overview which
// already aggregates the real Safety engines (incidents, CAPAs, fire
// extinguishers, training records, safety documents, trench safety).
//
// Every card opens an existing Safety route — no placeholders, no
// future buttons. Trench Safety is the benchmark and stays untouched.
//
// One question this surface answers:
//   "What safety work requires attention right now?"

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
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
  const s = getSafetyToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Safety-Token"] = s;
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

function useSafetySignals() {
  const [s, setS] = useState({
    loaded: false,
    refreshedAt: null,
    capas_open: null,
    capas_overdue: null,
    fire_ext_overdue: null,
    training_expired: null,
    training_expiring_30d: null,
    incidents_last_7d: null,
    safety_documents_total: null,
  });

  useEffect(() => {
    let cancelled = false;
    safeJson("/api/safety/overview").then((r) => {
      if (cancelled) return;
      const b = r.body || {};
      setS({
        loaded: true,
        refreshedAt: new Date().toISOString(),
        capas_open:             r.ok ? (b.corrective_actions_open ?? null) : null,
        capas_overdue:          r.ok ? (b.corrective_actions_overdue ?? null) : null,
        fire_ext_overdue:       r.ok ? (b.fire_extinguishers_overdue ?? null) : null,
        training_expired:       r.ok ? (b.training_expired ?? null) : null,
        training_expiring_30d:  r.ok ? (b.training_expiring_30d ?? null) : null,
        incidents_last_7d:      r.ok ? (b.incidents_last_7d ?? null) : null,
        safety_documents_total: r.ok ? (b.safety_documents_total ?? null) : null,
      });
    });
    return () => { cancelled = true; };
  }, []);

  return s;
}

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

export default function SafetyHubV2() {
  const s = useSafetySignals();
  const isPreview = (typeof window !== "undefined") && /preview/i.test(window.location.host);

  const allZero = s.loaded && [
    s.capas_open, s.capas_overdue, s.fire_ext_overdue,
    s.training_expired, s.training_expiring_30d, s.incidents_last_7d,
  ].every((v) => v === null || v === 0);

  return (
    <div data-testid="safety-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      {isPreview && (
        <div
          data-testid="safety-hub-v2-preview-banner"
          style={{
            background: "var(--brand-primary)", color: "var(--brand-on-primary)",
            padding: "8px 16px", fontSize: 11, letterSpacing: "0.04em",
            textTransform: "uppercase", fontWeight: 700, textAlign: "center",
          }}
        >
          Preview Environment · MASCI Operations Platform
        </div>
      )}

      <PortalShell
        portalName="MASCI"
        portalRole="Safety Portal"
        pageTitle="What safety work requires attention right now?"
        subtitle="Every queue is a live count — open it to see what Safety needs to act on today. Trench Safety workflows live under Trench Safety."
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/safety/trench-safety" testid="safety-hub-v2-action-trench" intent="primary">Trench Safety</RealLink>
          </div>
        }
        lastActivity={
          <span data-testid="safety-hub-v2-last-activity">
            {s.loaded ? `Refreshed ${new Date(s.refreshedAt).toLocaleTimeString()}` : "Loading live signals…"}
          </span>
        }
      >
        {/* Section 1 — Corrective Actions (CAPAs). */}
        <section data-testid="safety-hub-v2-section-capas" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="01 · Corrective Actions · live"
            title="Open and overdue CAPAs"
            caption="Counts pulled live. Click a card to open the real Safety CAPA workflow."
          />
          <div data-testid="safety-hub-v2-queue-grid-capas"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/safety-portal/corrective-actions?focus_filter=open"
              testid="safety-hub-v2-queue-capas-open"
              title="Open CAPAs"
              why="Corrective actions in Open / In Progress / Pending Review"
              source="Source: corrective_actions_open"
              value={s.capas_open}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/corrective-actions?focus_filter=overdue"
              testid="safety-hub-v2-queue-capas-overdue"
              title="Overdue CAPAs"
              why="Open CAPAs with due_date in the past — operational truth from real timestamps"
              source="Source: corrective_actions_overdue"
              value={s.capas_overdue}
              loaded={s.loaded}
            />
          </div>
        </section>

        {/* Section 2 — Compliance: fire extinguishers + training. */}
        <section data-testid="safety-hub-v2-section-compliance" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="02 · Compliance · live"
            title="Expiration & inspection signals"
            caption="Real dates from real engines. No fabricated urgency."
          />
          <div data-testid="safety-hub-v2-queue-grid-compliance"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/safety-portal/fire-extinguishers?focus_filter=overdue"
              testid="safety-hub-v2-queue-fire-ext-overdue"
              title="Fire Extinguishers · Overdue"
              why="Units past next_due_date for inspection"
              source="Source: fire_extinguishers_overdue"
              value={s.fire_ext_overdue}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/training?focus_filter=expired"
              testid="safety-hub-v2-queue-training-expired"
              title="Training · Expired"
              why="Records past expiration_date — recertification needed"
              source="Source: training_expired"
              value={s.training_expired}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety-portal/training?focus_filter=expiring_30d"
              testid="safety-hub-v2-queue-training-expiring"
              title="Training · Expiring in 30d"
              why="Records expiring inside 30 days — schedule recert"
              source="Source: training_expiring_30d"
              value={s.training_expiring_30d}
              loaded={s.loaded}
            />
          </div>
        </section>

        {/* Section 3 — Incidents (read-only context). */}
        <section data-testid="safety-hub-v2-section-incidents" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="03 · Incidents · recent activity"
            title="Last 7 days · documented incidents"
            caption="Cross-portal read into the real incidents engine."
          />
          <div data-testid="safety-hub-v2-queue-grid-incidents"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/safety-portal/incidents"
              testid="safety-hub-v2-queue-incidents-7d"
              title="Incidents · last 7 days"
              why="Documented incidents reported in the past week"
              source="Source: incidents_last_7d"
              value={s.incidents_last_7d}
              loaded={s.loaded}
            />
            <QueueCard
              to="/safety/trench-safety"
              testid="safety-hub-v2-queue-trench-safety"
              title="Trench Safety Module"
              why="Benchmark module — daily inspections · permits · CP signoffs"
              source="Source: /safety/trench-safety · real engine"
              value={null}
              loaded={true}
            />
            <QueueCard
              to="/safety-portal/documents"
              testid="safety-hub-v2-queue-documents"
              title="Safety Documents on file"
              why="Reference docs — JHAs · SDS · regulatory posters"
              source="Source: safety_documents_total"
              value={s.safety_documents_total}
              loaded={s.loaded}
              variantWhenAttention="default"
            />
          </div>
        </section>

        {allZero && (
          <EmptyState
            testId="safety-hub-v2-all-clear"
            title="Safety is all clear."
            explanation="No CAPAs open, no overdue inspections, no expired training, and no incidents in the last 7 days."
            severity="good"
          />
        )}

      </PortalShell>
    </div>
  );
}
