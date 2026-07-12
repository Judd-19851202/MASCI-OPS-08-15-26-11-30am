// Track 13.6K · Phase 3 — Leadership Hub V2 (preview only).
// MOUNTED AT: /leadership/hub_v2 (behind RequireLeadership). Classic /leadership untouched.
// REAL DATA SOURCES (existing, no new APIs):
//   GET /api/safety/overview                   (incidents, CAPAs, training)
//   GET /api/operations/expirations/summary    (compliance + cert expirations)
//   GET /api/dispatch/command/summary          (cross-portal ops attention)
// Doctrine: executive attention only. Not a vanity dashboard. Every card
// must lead to a real existing workflow.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getLeadershipToken } from "@/lib/leadershipAuth";
import { PortalShell, StatusChip, Card, EmptyState } from "../design-system";

const API = process.env.REACT_APP_BACKEND_URL;

function h() {
  const out = { "Content-Type": "application/json" };
  const a = getAdminToken(); const lt = getLeadershipToken();
  if (a) out["X-Admin-Token"] = a;
  if (lt) out["X-Leadership-Token"] = lt;
  return out;
}
async function j(p) {
  try { const r = await fetch(`${API}${p}`, { headers: h() }); return { ok: r.ok, body: r.ok ? await r.json() : null }; }
  catch { return { ok: false, body: null }; }
}

function QC({ to, testid, title, why, source, value, loaded }) {
  const isAtt = loaded && typeof value === "number" && value > 0;
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit" }}>
      <Card title={title} description={why}
            metric={loaded ? (value === null ? "—" : value) : "…"}
            variant={isAtt ? "warning" : "default"}
            status={!loaded ? <StatusChip statusKey="draft" compact label="Loading" />
                    : value === null ? <StatusChip statusKey="offline_feed" compact />
                    : isAtt ? <StatusChip statusKey="pending_verification" compact />
                    : <StatusChip statusKey="verified" compact />}>
        <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>{source}</p>
      </Card>
    </Link>
  );
}

function Section({ k, t, c, children }) {
  return (
    <section style={{ marginBottom: 28 }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, letterSpacing: 1.5, textTransform: "uppercase", color: "var(--ink-faint)" }}>{k}</div>
        <h2 style={{ margin: "2px 0 0", fontSize: 18, fontWeight: 700, color: "var(--ink-strong)" }}>{t}</h2>
        {c && <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>{c}</p>}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>{children}</div>
    </section>
  );
}

export default function LeadershipHubV2() {
  const [s, setS] = useState({ loaded: false, sa: null, ex: null, ds: null });
  useEffect(() => {
    let cancelled = false;
    Promise.all([j("/api/safety/overview"), j("/api/operations/expirations/summary"), j("/api/dispatch/command/summary")])
      .then(([sa, ex, ds]) => { if (!cancelled) setS({ loaded: true, sa: sa.body, ex: ex.body, ds: ds.body }); });
    return () => { cancelled = true; };
  }, []);
  const sa = s.sa || {};
  const ex = s.ex?.counts || {};
  const ds = s.ds || {};
  const isPreview = typeof window !== "undefined" && /preview/i.test(window.location.host);

  return (
    <div data-testid="leadership-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      {isPreview && (
        <div data-testid="leadership-hub-v2-preview-banner" style={{ background: "var(--brand-primary)", color: "var(--brand-on-primary)", padding: "8px 16px", fontSize: 11, letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 700, textAlign: "center" }}>
          Leadership Hub V2 · Non-production companion lane · Classic surfaces remain canonical
        </div>
      )}
      <PortalShell
        portalName="MASCI" portalRole="Leadership · Hub V2"
        pageTitle="What requires executive attention?"
        subtitle="Cross-portal threats to execution, schedule, safety, compliance. No vanity metrics. Every card opens the workflow that resolves it."
      >
        {/* TRACK 15.46 · FR-01 · Discoverability link to the Executive
            Overview (Track 15.44). One nav entry so executives never
            need to remember a URL. */}
        <Section k="00 · 30-Second Awareness · live" t="Executive Overview" c="Six-tile attention surface · ≤ 30 second comprehension">
          <QC
            to="/admin/executive-overview"
            testid="lead-hub-v2-q-executive-overview"
            title="Executive Overview →"
            why="Jobs / Overdue / Staffing / Equipment / Safety / Activity — single page"
            source="Source: /api/admin/executive/overview"
            value={null}
            loaded={true}
          />
        </Section>

        <Section k="01 · Threats to Safety · live" t="Safety attention items" c="Real from /api/safety/overview">
          <QC to="/safety-portal" testid="lead-hub-v2-q-incidents-open" title="Open Incidents" why="Incidents not yet closed by Safety" source="Source: safety/overview" value={ds.safety?.incidents_open ?? null} loaded={s.loaded} />
          <QC to="/safety-portal" testid="lead-hub-v2-q-capas-overdue" title="Overdue CAPAs" why="Corrective actions past due_date" source="Source: safety/overview.corrective_actions_overdue" value={sa.corrective_actions_overdue ?? null} loaded={s.loaded} />
          <QC to="/safety-portal" testid="lead-hub-v2-q-training-expired" title="Training · Expired" why="Certs already expired — recert needed" source="Source: safety/overview.training_expired" value={sa.training_expired ?? null} loaded={s.loaded} />
        </Section>

        <Section k="02 · Threats to Execution · live" t="Fleet + shop signals" c="Cross-portal read into dispatch + shop">
          <QC to="/dispatch-portal" testid="lead-hub-v2-q-fleet-oos" title="Fleet · OOS" why="Units out of service across the fleet" source="Source: dispatch.command.summary.fleet.counts.oos" value={ds.fleet?.counts?.oos ?? null} loaded={s.loaded} />
          <QC to="/dispatch-portal" testid="lead-hub-v2-q-breakdowns" title="Active Breakdowns" why="Breakdowns blocking the haul plan" source="Source: dispatch.command.summary.haul.counts.breakdown_impacts" value={ds.haul?.counts?.breakdown_impacts ?? null} loaded={s.loaded} />
          <QC to="/shop" testid="lead-hub-v2-q-shop-defects" title="Open Shop Defects" why="Defects active across the fleet" source="Source: dispatch.command.summary.shop.defects_open" value={ds.shop?.defects_open ?? null} loaded={s.loaded} />
        </Section>

        <Section k="03 · Threats to Compliance · live" t="Document + cert expirations" c="Real dates from real engines">
          <QC to="/admin/training" testid="lead-hub-v2-q-exp-expired" title="Documents · Expired" why="Already past expiration date" source="Source: operations/expirations.counts.expired" value={ex.expired ?? null} loaded={s.loaded} />
          <QC to="/admin/training" testid="lead-hub-v2-q-exp-30" title="Expiring ≤ 30 days" why="Inside 30-day expiration window" source="Source: counts.in_30" value={ex.in_30 ?? null} loaded={s.loaded} />
        </Section>

        <div data-testid="leadership-hub-v2-trace-note" style={{ marginTop: 16, padding: "var(--pad-card)", background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12 }}>
          <strong style={{ color: "var(--ink-strong)" }}>Leadership Hub · executive attention.</strong>{" "}
          Executive attention only. Not a vanity dashboard. Every count traces to a real source; every card opens the workflow that resolves the threat.
        </div>
      </PortalShell>
    </div>
  );
}
