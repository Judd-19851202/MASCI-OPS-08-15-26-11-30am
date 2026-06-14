// Track 13.6K · Phase 1 — Admin Hub V2 (preview only).
// MOUNTED AT: /admin/hub_v2 (behind RequireAdmin). Classic /admin untouched.
// REAL DATA SOURCES (existing, no new APIs):
//   GET /api/admin/integrations/health     (Mongo, R2, Resend, Motive, etc.)
//   GET /api/operations/expirations/summary (DOC + cert expiration buckets)
//   GET /api/dispatch/command/summary       (cross-portal ops attention)
// Doctrine: Operations Control Center, NOT settings screen. Every count
// opens an existing admin / ops surface — no dead objects.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { PortalShell, StatusChip, Card, EmptyState } from "../design-system";
import AdminSideNavV2 from "@/components/admin/sidebar/SideNavV2";

const API = process.env.REACT_APP_BACKEND_URL;

function h() {
  const t = getAdminToken();
  return t ? { "Content-Type": "application/json", "X-Admin-Token": t } : { "Content-Type": "application/json" };
}
async function j(p) {
  try { const r = await fetch(`${API}${p}`, { headers: h() }); return { ok: r.ok, body: r.ok ? await r.json() : null }; }
  catch { return { ok: false, body: null }; }
}

function QC({ to, testid, title, why, source, value, loaded, secondary }) {
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
        {secondary && <p style={{ margin: "4px 0 0", fontSize: 11, color: "var(--ink-strong)", fontWeight: 600 }}>{secondary}</p>}
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

export default function AdminHubV2() {
  const [s, setS] = useState({ loaded: false, integ: null, exp: null, ds: null });
  useEffect(() => {
    let cancelled = false;
    Promise.all([j("/api/admin/integrations/health"), j("/api/operations/expirations/summary"), j("/api/dispatch/command/summary")])
      .then(([i, e, d]) => { if (!cancelled) setS({ loaded: true, integ: i.body, exp: e.body, ds: d.body }); });
    return () => { cancelled = true; };
  }, []);
  const isPreview = typeof window !== "undefined" && /preview/i.test(window.location.host);
  const probes = s.integ?.probes || [];
  const degraded = probes.filter(p => p.status && p.status !== "ok").length;
  const expC = s.exp?.counts || {};
  const ds = s.ds || {};
  const incidentsOpen = ds.safety?.incidents_open ?? null;
  const capasOpen = ds.safety?.corrective_actions_open ?? null;
  const fleetOos = ds.fleet?.counts?.oos ?? null;

  return (
    <div data-testid="admin-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      {isPreview && (
        <div data-testid="admin-hub-v2-preview-banner" style={{ background: "var(--brand-primary)", color: "var(--brand-on-primary)", padding: "8px 16px", fontSize: 11, letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 700, textAlign: "center" }}>
          Admin Hub V2 · Operations Control Center · Companion lane to /admin · Classic Admin Hub remains canonical
        </div>
      )}
      <PortalShell
        portalName="MASCI" portalRole="Admin Portal · Hub V2"
        pageTitle="What requires admin action right now?"
        subtitle="Live cross-portal signals. Every queue opens a real existing admin / ops workflow."
        primaryActions={
          <div style={{ display: "flex", gap: 8 }}>
            <Link to="/admin" data-testid="admin-hub-v2-back-classic" style={{ display: "inline-block", padding: "6px 12px", background: "var(--paper-card)", color: "var(--ink-strong)", border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", fontSize: 12, fontWeight: 600, textDecoration: "none" }}>Open Classic Admin Hub</Link>
          </div>
        }
        sideNav={<AdminSideNavV2 />}
      >
        <Section k="01 · System Health · live" t="Integration probes" c="Real probe results from /api/admin/integrations/health">
          <QC to="/admin/operations-dashboard" testid="admin-hub-v2-q-integrations-degraded" title="Degraded Integrations" why="Probes returning non-OK status" source="Source: integrations.health.probes" value={s.loaded ? degraded : null} loaded={s.loaded} />
          <QC to="/admin/asset-spine" testid="admin-hub-v2-q-asset-spine" title="Asset Spine Conflicts" why="Unresolved asset master conflicts" source="Source: dispatch.command.summary (spine)" value={ds.spine?.conflicts ?? null} loaded={s.loaded} />
        </Section>

        <Section k="02 · Compliance · live" t="Expirations + certifications" c="Real dates from existing engines · no fabricated urgency">
          <QC to="/admin/training" testid="admin-hub-v2-q-exp-expired" title="Documents · Expired" why="Already past expiration date · operational truth" source="Source: operations/expirations/summary.counts.expired" value={expC.expired ?? null} loaded={s.loaded} />
          <QC to="/admin/training" testid="admin-hub-v2-q-exp-30" title="Expiring ≤ 30 days" why="Documents inside 30-day window" source="Source: counts.in_30" value={expC.in_30 ?? null} loaded={s.loaded} />
          <QC to="/admin/training" testid="admin-hub-v2-q-exp-60" title="Expiring 31–60 days" why="Documents inside 60-day window" source="Source: counts.in_60" value={expC.in_60 ?? null} loaded={s.loaded} />
        </Section>

        <Section k="03 · Cross-portal · read" t="Operational signals across portals" c="Read-only views into Safety + Dispatch engines">
          <QC to="/safety-portal" testid="admin-hub-v2-q-incidents" title="Open Incidents (Safety)" why="Incidents not yet closed by Safety" source="Source: dispatch.command.summary.safety.incidents_open" value={incidentsOpen} loaded={s.loaded} />
          <QC to="/safety-portal" testid="admin-hub-v2-q-capas" title="Open CAPAs (Safety)" why="Corrective actions still open" source="Source: dispatch.command.summary.safety.corrective_actions_open" value={capasOpen} loaded={s.loaded} />
          <QC to="/dispatch-portal" testid="admin-hub-v2-q-fleet-oos" title="Fleet · OOS" why="Units out of service across the fleet" source="Source: dispatch.command.summary.fleet.counts.oos" value={fleetOos} loaded={s.loaded} />
        </Section>

        {/* Track 13.8E — Operational Locations recovery surfacing.
            The reconciliation workflow at /admin/geofence-reconciliation is already
            built end-to-end (page + 9 admin endpoints). Surface as a discoverability
            card only. No metric is invented; no queue count is fetched. */}
        <Section k="04 · Map data quality · admin" t="Operational locations reconciliation" c="Pre-existing admin workflow surfaced for discoverability — no new system">
          <Link to="/admin/geofence-reconciliation" data-testid="admin-hub-v2-q-geofence-reconciliation" style={{ textDecoration: "none", color: "inherit" }}>
            <Card
              title="Geofence Reconciliation"
              description="Review proposed Motive geofence ↔ MASCI project matches. Approve, reject, reassign, or bulk-approve high-confidence rows. Cleaner geofences mean cleaner assignment names on every operations-map marker (PM, Shop Recovery, Dispatch all read the same source)."
              variant="default"
              status={<StatusChip statusKey="verified" compact label="Live workflow" />}
            >
              <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
                Source: /admin/geofence-reconciliation (existing route · admin-only)
              </p>
            </Card>
          </Link>
        </Section>

        {/* Track 13.22 · Phase D — Material Movement Ledger · Data-Quality + CSV.
            Surfaces the company-wide ledger queue at /admin/material-ledger-quality.
            Reuses the dispatch+admin gated endpoint from Track 13.21 (no new system). */}
        <Section k="05 · Material data quality · admin" t="Material movement ledger" c="Missing proof, partial proof, and exportable material movement rows. No cost / accounting / pay-app fields.">
          <Link to="/admin/material-ledger-quality" data-testid="admin-hub-v2-q-material-ledger-quality" style={{ textDecoration: "none", color: "inherit" }}>
            <Card
              title="Material Ledger Quality"
              description="Company-wide missing-proof queue + CSV export over the Material Movement Ledger (haul cycles · scale-ticket attachments · daily report material rows). Operator-driven follow-up for hauls without ticket proof. FleetWatcher remains not connected."
              variant="default"
              status={<StatusChip statusKey="verified" compact label="Live workflow" />}
            >
              <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
                Source: /admin/material-ledger-quality (Track 13.22 · admin-only · reuses /api/dispatch/haul-ledger)
              </p>
            </Card>
          </Link>
        </Section>

        <div data-testid="admin-hub-v2-trace-note" style={{ marginTop: 16, padding: "var(--pad-card)", background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12 }}>
          <strong style={{ color: "var(--ink-strong)" }}>Admin Hub V2 · Track 13.6K preview.</strong>{" "}
          Operations Control Center · presentation-only. Every count traces to a real source; every card opens an existing workflow. Settings, users, integrations, and audit trails remain in the classic admin surface — no rebuild.
        </div>
      </PortalShell>
    </div>
  );
}
