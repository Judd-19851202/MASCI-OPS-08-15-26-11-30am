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
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { PortalShell, StatusChip, Card, EmptyState } from "../design-system";

const API = process.env.REACT_APP_BACKEND_URL;

function h() {
  return buildScopedPortalAuthHeaders(["admin", "fl"], { "Content-Type": "application/json" });
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
  return (
    <div data-testid="leadership-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI" portalRole="Leadership Hub"
        pageTitle="What requires leadership attention?"
        subtitle="Cross-portal threats to execution, schedule, safety, compliance. No vanity metrics. Every card opens the workflow that resolves it."
      >
        <section className="wp17-mission-banner" data-testid="leadership-hub-v2-mission-banner">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="wp17-kicker text-white/70">Today’s focus</div>
              <h2 className="mt-2 font-display text-xl font-black text-white">Show leadership only the threats that need intervention, not a second admin portal.</h2>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                See the biggest operational threats quickly and open the work that clears them.
              </p>
            </div>
          </div>
        </section>

        {/* TRACK 15.46 · FR-01 · Discoverability link to the Executive
            Overview (Track 15.44). One nav entry so executives never
            need to remember a URL. */}
        <Section k="00 · 30-Second Awareness · live" t="Executive Overview" c="Six-tile attention surface · ≤ 30 second comprehension">
          <QC
            to="/admin/executive-overview"
            testid="lead-hub-v2-q-executive-overview"
            title="Executive Overview →"
            why="Jobs / Overdue / Staffing / Equipment / Safety / Activity — single page"
            source="Company operations overview"
            value={null}
            loaded={true}
          />
        </Section>

        <Section k="01 · Threats to Safety · live" t="Safety attention items" c="Live safety summary">
          <QC to="/safety-portal" testid="lead-hub-v2-q-incidents-open" title="Open Incidents" why="Incidents not yet closed by Safety" source="Safety summary" value={ds.safety?.incidents_open ?? null} loaded={s.loaded} />
          <QC to="/safety-portal" testid="lead-hub-v2-q-capas-overdue" title="Overdue CAPAs" why="Corrective actions past due dates" source="Corrective action summary" value={sa.corrective_actions_overdue ?? null} loaded={s.loaded} />
          <QC to="/safety-portal" testid="lead-hub-v2-q-training-expired" title="Training · Expired" why="Credentials already expired — renewal needed" source="Training status summary" value={sa.training_expired ?? null} loaded={s.loaded} />
        </Section>

        <Section k="02 · Threats to Execution · live" t="Fleet + shop signals" c="Cross-portal read into dispatch + shop">
          <QC to="/dispatch-portal" testid="lead-hub-v2-q-fleet-oos" title="Fleet · OOS" why="Units out of service across the fleet" source="Fleet status summary" value={ds.fleet?.counts?.oos ?? null} loaded={s.loaded} />
          <QC to="/dispatch-portal" testid="lead-hub-v2-q-breakdowns" title="Active Breakdowns" why="Breakdowns blocking the haul plan" source="Haul impact summary" value={ds.haul?.counts?.breakdown_impacts ?? null} loaded={s.loaded} />
          <QC to="/shop" testid="lead-hub-v2-q-shop-defects" title="Open Shop Defects" why="Defects active across the fleet" source="Shop defect summary" value={ds.shop?.defects_open ?? null} loaded={s.loaded} />
        </Section>

        <Section k="03 · Threats to Compliance · live" t="Document + credential expirations" c="Live expiration dates from shared records">
          <QC to="/admin/training" testid="lead-hub-v2-q-exp-expired" title="Documents · Expired" why="Already past expiration date" source="Expiration summary" value={ex.expired ?? null} loaded={s.loaded} />
          <QC to="/admin/training" testid="lead-hub-v2-q-exp-30" title="Expiring ≤ 30 days" why="Inside the next 30-day renewal window" source="30-day renewal summary" value={ex.in_30 ?? null} loaded={s.loaded} />
        </Section>

        <div data-testid="leadership-hub-v2-trace-note" style={{ marginTop: 16, padding: "var(--pad-card)", background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12 }}>
          <strong style={{ color: "var(--ink-strong)" }}>Leadership Hub · executive attention.</strong>{" "}
          Executive attention only. Not a vanity dashboard. Every count traces to a real source; every card opens the workflow that resolves the threat.
        </div>
      </PortalShell>
    </div>
  );
}
