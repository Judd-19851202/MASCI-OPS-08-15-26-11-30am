// Track 13.6K · Phase 2 — Field Leadership Hub V2 (preview only).
// MOUNTED AT: /field-leadership/hub_v2 (behind RequireFl). Classic at /leadership untouched.
// REAL DATA SOURCES (existing, no new APIs):
//   GET /api/field-leadership                  (list of FL records)
//   GET /api/dispatch/command/summary          (cross-portal ops attention)
//   GET /api/safety/overview                   (cross-portal safety read)
// Doctrine: "What requires field action today?" — superintendent / foreman view.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getFlToken } from "@/lib/flAuth";
import { PortalShell, StatusChip, Card, EmptyState } from "../design-system";

const API = process.env.REACT_APP_BACKEND_URL;

function h() {
  const out = { "Content-Type": "application/json" };
  const a = getAdminToken(); const fl = getFlToken();
  if (a) out["X-Admin-Token"] = a;
  if (fl) out["X-FL-Token"] = fl;
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

export default function FieldLeadershipHubV2() {
  const [s, setS] = useState({ loaded: false, fl: null, ds: null, sa: null });
  useEffect(() => {
    let cancelled = false;
    Promise.all([j("/api/field-leadership?limit=200"), j("/api/dispatch/command/summary"), j("/api/safety/overview")])
      .then(([fl, ds, sa]) => { if (!cancelled) setS({ loaded: true, fl: fl.body, ds: ds.body, sa: sa.body }); });
    return () => { cancelled = true; };
  }, []);
  const flList = Array.isArray(s.fl) ? s.fl : (s.fl?.items || s.fl?.records || []);
  // Real attention signals — submissions not yet reviewed.
  const flPending = s.loaded ? flList.filter(r => /pending|submitted|open/i.test(r.status || r.lifecycle_state || "")).length : null;
  const flRecent = s.loaded ? flList.length : null;
  const ds = s.ds || {};
  const sa = s.sa || {};
  const isPreview = typeof window !== "undefined" && /preview/i.test(window.location.host);

  return (
    <div data-testid="fl-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      {isPreview && (
        <div data-testid="fl-hub-v2-preview-banner" style={{ background: "var(--brand-primary)", color: "var(--brand-on-primary)", padding: "8px 16px", fontSize: 11, letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 700, textAlign: "center" }}>
          Field Leadership Hub V2 · Live FL data · Side-by-side with /leadership · No route swap until operator approval
        </div>
      )}
      <PortalShell
        portalName="MASCI" portalRole="Field Leadership · Hub V2"
        pageTitle="What requires field action today?"
        subtitle="Superintendent / foreman view. Every queue opens a real existing FL workflow."
        primaryActions={
          <div style={{ display: "flex", gap: 8 }}>
            <Link to="/leadership" data-testid="fl-hub-v2-back-classic" style={{ display: "inline-block", padding: "6px 12px", background: "var(--paper-card)", color: "var(--ink-strong)", border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)", fontSize: 12, fontWeight: 600, textDecoration: "none" }}>Open Classic FL Hub</Link>
          </div>
        }
      >
        <Section k="01 · Field signals · live" t="Submissions and on-field activity" c="Real records from /api/field-leadership">
          <QC to="/leadership/records" testid="fl-hub-v2-q-pending" title="FL Records · Pending" why="Submissions awaiting review" source="Source: /api/field-leadership · pending/submitted/open" value={flPending} loaded={s.loaded} />
          <QC to="/leadership/records" testid="fl-hub-v2-q-recent" title="FL Records · Total Recent" why="Records in the recent window (last 200)" source="Source: /api/field-leadership total" value={flRecent} loaded={s.loaded} />
        </Section>

        <Section k="02 · Safety · cross-portal read" t="Field safety attention" c="Read-only into the Safety engine — never mutate from FL.">
          <QC to="/safety-portal" testid="fl-hub-v2-q-capas-overdue" title="Overdue CAPAs" why="Past due_date · real timestamps" source="Source: safety/overview.corrective_actions_overdue" value={sa.corrective_actions_overdue ?? null} loaded={s.loaded} />
          <QC to="/safety-portal" testid="fl-hub-v2-q-incidents-7d" title="Incidents · last 7d" why="Documented incidents in past week" source="Source: safety/overview.incidents_last_7d" value={sa.incidents_last_7d ?? null} loaded={s.loaded} />
        </Section>

        <Section k="03 · Fleet · cross-portal read" t="Field-impacting equipment" c="Read-only into Dispatch + Shop. Field cannot mutate.">
          <QC to="/dispatch-portal/fleet" testid="fl-hub-v2-q-fleet-oos" title="Fleet · OOS" why="Out-of-service units across the fleet" source="Source: dispatch.command.summary.fleet.counts.oos" value={ds.fleet?.counts?.oos ?? null} loaded={s.loaded} />
          <QC to="/dispatch-portal/fleet" testid="fl-hub-v2-q-shop-defects" title="Open Shop Defects" why="Defects active across the fleet" source="Source: dispatch.command.summary.shop.defects_open" value={ds.shop?.defects_open ?? null} loaded={s.loaded} />
        </Section>

        <div data-testid="fl-hub-v2-trace-note" style={{ marginTop: 16, padding: "var(--pad-card)", background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12 }}>
          <strong style={{ color: "var(--ink-strong)" }}>Field Leadership Hub V2 · Track 13.6K preview.</strong>{" "}
          Every count traces to a real source; every card opens an existing FL / Safety / Dispatch workflow. Classic FL hub remains untouched at <code>/leadership</code>.
        </div>
      </PortalShell>
    </div>
  );
}
