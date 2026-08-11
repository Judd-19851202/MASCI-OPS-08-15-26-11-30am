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
import { KpiInlineHelp } from "@/components/KpiInlineHelp";

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

function Section({ k, t, c, action, children }) {
  return (
    <section style={{ marginBottom: 28 }}>
      <div style={{ marginBottom: 12, display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
        <div>
        <div style={{ fontSize: 10, letterSpacing: 1.5, textTransform: "uppercase", color: "var(--ink-faint)" }}>{k}</div>
        <h2 style={{ margin: "2px 0 0", fontSize: 18, fontWeight: 700, color: "var(--ink-strong)" }}>{t}</h2>
        {c && <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>{c}</p>}
        </div>
        {action}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>{children}</div>
    </section>
  );
}

export default function LeadershipHubV2() {
  const [s, setS] = useState({ loaded: false, ds: null, ts: null, dq: null, dsMeta: null });
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      j("/api/dispatch/command/summary"),
      j("/api/field-leadership/portal/crew/training-summary"),
      j("/api/field-leadership/portal/driver-qualification?limit=50"),
    ]).then(([ds, ts, dq]) => {
        if (!cancelled) {
          setS({
            loaded: true,
            ds: ds.body,
            ts: ts.body,
            dq: dq.body,
            dsMeta: ds.body?.kpi_metadata || null,
          });
        }
      });
    return () => { cancelled = true; };
  }, []);
  const ts = s.ts || {};
  const dq = s.dq || {};
  const dqSummary = dq.summary || {};
  const ds = s.ds || {};
  return (
    <div data-testid="leadership-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI" portalRole="Leadership Hub"
        pageTitle="What requires leadership attention?"
        subtitle="Field leadership attention across crew readiness, dispatch pressure, and safety follow-up. No vanity metrics. Every card points to a real field workflow."
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

        <Section k="00 · 30-Second Awareness · live" t="Field Leadership Portal" c="One glance at what is active before crews roll out">
          <QC
            to="/field-leadership/portal/dashboard"
            testid="lead-hub-v2-q-fl-portal"
            title="Projects in scope →"
            why="Active work currently visible through the field-leadership command surface"
            source="Dispatch command summary"
            value={ds.jobs?.counts?.projects_active ?? null}
            loaded={s.loaded}
          />
        </Section>

        <Section
          k="01 · Threats to Safety · live"
          t="Safety attention items"
          c="Safety signals the field-leadership role can actually act on"
          action={<KpiInlineHelp metadata={s.dsMeta?.sections?.safety_watch} fallbackLabel="Safety attention items" testId="leadership-hub-v2-safety-help" />}
        >
          <QC to="/incidents/report" testid="lead-hub-v2-q-incidents-open" title="Open Incidents" why="Incidents still open in the shared safety watch" source="Dispatch safety watch" value={ds.safety?.incidents_open ?? null} loaded={s.loaded} />
          <QC to="/field-leadership/portal/dashboard" testid="lead-hub-v2-q-capas-open" title="Open Corrective Actions" why="Corrective actions still active across the shared safety watch" source="Dispatch safety watch" value={ds.safety?.corrective_actions_open ?? null} loaded={s.loaded} />
          <QC to="/field-leadership/portal/driver-qualification" testid="lead-hub-v2-q-training-expired" title="Training · Expired" why="Crew training records already expired and needing follow-up" source="Field-leadership crew training summary" value={ts.expired_count ?? null} loaded={s.loaded} />
        </Section>

        <Section
          k="02 · Threats to Execution · live"
          t="Fleet + shop signals"
          c="Live dispatch + equipment pressure seen by field leadership"
          action={<KpiInlineHelp metadata={s.dsMeta?.sections?.fleet_shop} fallbackLabel="Fleet and shop signals" testId="leadership-hub-v2-execution-help" />}
        >
          <QC to="/field-leadership/portal/dashboard" testid="lead-hub-v2-q-fleet-oos" title="Fleet · OOS" why="Units currently out of service across the fleet" source="Dispatch fleet snapshot" value={ds.fleet?.counts?.oos ?? null} loaded={s.loaded} />
          <QC to="/field-leadership/portal/dashboard" testid="lead-hub-v2-q-breakdowns" title="Active Breakdowns" why="Breakdowns currently blocking the haul plan" source="Dispatch haul impact summary" value={ds.haul?.counts?.breakdown_impacts ?? null} loaded={s.loaded} />
          <QC to="/field-leadership/portal/dashboard" testid="lead-hub-v2-q-shop-defects" title="Open Shop Defects" why="Defects still active across the fleet" source="Dispatch shop snapshot" value={ds.shop?.defects_open ?? null} loaded={s.loaded} />
        </Section>

        <Section
          k="03 · Threats to Compliance · live"
          t="Crew readiness expirations"
          c="Training and driver-readiness expirations visible to field leadership"
        >
          <QC to="/field-leadership/portal/driver-qualification" testid="lead-hub-v2-q-exp-expired" title="Training · Expired" why="Training already past expiration and needing coordination before work starts" source="Field-leadership crew training summary" value={ts.expired_count ?? null} loaded={s.loaded} />
          <QC to="/field-leadership/portal/driver-qualification" testid="lead-hub-v2-q-exp-30" title="Training / Driver Expiring ≤ 30 days" why="Training, CDL, or medical-card expirations inside the next 30 days" source="Field-leadership training + driver qualification summary" value={(ts.expiring_within_30d_count ?? 0) + (dqSummary.cdl_expiring_30d ?? 0) + (dqSummary.medical_card_expiring_30d ?? 0)} loaded={s.loaded} />
        </Section>

        <div data-testid="leadership-hub-v2-trace-note" style={{ marginTop: 16, padding: "var(--pad-card)", background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12 }}>
          <strong style={{ color: "var(--ink-strong)" }}>Leadership Hub · executive attention.</strong>{" "}
          Field-leadership attention only. Not a vanity dashboard. Every count traces to a field-leadership-safe source; every card opens a real field workflow.
        </div>
      </PortalShell>
    </div>
  );
}
