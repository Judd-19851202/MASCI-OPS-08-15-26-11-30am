// Track 13.6G — Dispatch Recovery (preview).
//
// MOUNTED AT: /dispatch-portal/hub_v2 (behind RequireDispatch — same gate
// as /dispatch-portal). The classic dispatch hub at /dispatch-portal is
// PRESERVED unchanged. No route swap, no engine duplication, no
// permission drift — this is a presentation-only modernization.
//
// REAL DATA ONLY:
//   /api/dispatch/command/summary  (real Dispatch Command Center engine)
// Every card opens an existing dispatch surface:
//   /dispatch-portal/board                · driver-assignment queue
//   /dispatch-portal/command              · MapLibre operational map
//   /dispatch-portal/fleet                · fleet visibility
//   /dispatch-portal/driver-qualification · DOT / CDL readiness queue
//
// Single question this surface answers:
//   "What requires the dispatcher's attention right now?"
//
// Visual guardrail compliance: this page does NOT mount MapLibre and
// does NOT touch /dispatch-portal/command. Map remains intact.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
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
  const d = getDispatchToken();
  if (a) h["X-Admin-Token"] = a;
  if (d) h["X-Dispatch-Token"] = d;
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

function useDispatchSignals() {
  const [s, setS] = useState({
    loaded: false,
    refreshedAt: null,
    drivers_unacked: null,     // summary.drivers.counts.un_acked
    active_hauls: null,        // summary.haul.counts.active_hauls
    waiting_plant: null,       // summary.haul.counts.waiting_on_plant
    waiting_dump: null,        // summary.haul.counts.waiting_on_dump
    breakdown_impacts: null,   // summary.haul.counts.breakdown_impacts
    fleet_oos: null,           // summary.fleet.counts.oos
    in_shop: null,             // summary.fleet.counts.in_shop
    shop_defects_open: null,   // summary.shop.defects_open
    incidents_open: null,      // summary.safety.incidents_open
    capas_open: null,          // summary.safety.corrective_actions_open
  });

  useEffect(() => {
    let cancelled = false;
    safeJson("/api/dispatch/command/summary").then((r) => {
      if (cancelled) return;
      const b = r.body || {};
      const fc = b.fleet?.counts || {};
      const dc = b.drivers?.counts || {};
      const hc = b.haul?.counts || {};
      const sf = b.safety || {};
      const sh = b.shop || {};
      setS({
        loaded: true,
        refreshedAt: new Date().toISOString(),
        drivers_unacked:   r.ok ? (dc.un_acked ?? null) : null,
        active_hauls:      r.ok ? (hc.active_hauls ?? null) : null,
        waiting_plant:     r.ok ? (hc.waiting_on_plant ?? null) : null,
        waiting_dump:      r.ok ? (hc.waiting_on_dump ?? null) : null,
        breakdown_impacts: r.ok ? (hc.breakdown_impacts ?? null) : null,
        fleet_oos:         r.ok ? (fc.oos ?? null) : null,
        in_shop:           r.ok ? (fc.in_shop ?? null) : null,
        shop_defects_open: r.ok ? (sh.defects_open ?? null) : null,
        incidents_open:    r.ok ? (sf.incidents_open ?? null) : null,
        capas_open:        r.ok ? (sf.corrective_actions_open ?? null) : null,
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

function QueueCard({ to, testid, title, why, source, value, loaded }) {
  const isAttention = loaded && typeof value === "number" && value > 0;
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <Card
        title={title}
        description={why}
        metric={loaded ? (value === null ? "—" : value) : "…"}
        variant={isAttention ? "warning" : "default"}
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

export default function DispatchHubV2() {
  const s = useDispatchSignals();
  const allZero = s.loaded && [
    s.drivers_unacked, s.active_hauls, s.waiting_plant, s.waiting_dump,
    s.breakdown_impacts, s.fleet_oos, s.in_shop, s.shop_defects_open,
    s.incidents_open, s.capas_open,
  ].every((v) => v === null || v === 0);

  return (
    <div data-testid="dispatch-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Dispatch Portal"
        pageTitle="What requires the dispatcher's attention right now?"
        subtitle="Every queue is a live count — open it to see what Dispatch needs to act on today. The Map command surface is one click away."
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/dispatch-portal/command" testid="dispatch-hub-v2-action-cc" intent="primary">Open Command Map</RealLink>
          </div>
        }
        lastActivity={
          <span data-testid="dispatch-hub-v2-last-activity">
            {s.loaded ? `Refreshed ${new Date(s.refreshedAt).toLocaleTimeString()}` : "Loading live signals…"}
          </span>
        }
      >
        {/* Section 1 — Driver + Haul action queues. */}
        <section data-testid="dispatch-hub-v2-section-drivers" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="01 · Driver & Haul Queues · live"
            title="Open dispatch work"
            caption="Counts pulled from /api/dispatch/command/summary in real time. Click a card to open the real dispatch workflow."
          />
          <div
            data-testid="dispatch-hub-v2-queue-grid-drivers"
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}
          >
            <QueueCard
              to="/dispatch-portal/board?focus_filter=unacked"
              testid="dispatch-hub-v2-queue-unacked"
              title="Drivers Un-Acknowledged"
              why="Assignment-only drivers without a recorded shift acknowledgement"
              source="Live count · driver acknowledgements pending"
              value={s.drivers_unacked}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/board?focus_filter=active"
              testid="dispatch-hub-v2-queue-active-hauls"
              title="Active Hauls"
              why="Hauls currently in cycle across all jobs"
              source="Live count · hauls currently moving"
              value={s.active_hauls}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/board?focus_filter=waiting_plant"
              testid="dispatch-hub-v2-queue-waiting-plant"
              title="Waiting on Plant"
              why="Drivers stalled at plant — escalate or re-route"
              source="Live count · trucks idle at plant"
              value={s.waiting_plant}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/board?focus_filter=waiting_dump"
              testid="dispatch-hub-v2-queue-waiting-dump"
              title="Waiting on Dump"
              why="Drivers stalled at dump site — escalate or re-route"
              source="Live count · drivers stalled at dump site"
              value={s.waiting_dump}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/board?focus_filter=breakdown"
              testid="dispatch-hub-v2-queue-breakdowns"
              title="Breakdown Impacts"
              why="Active breakdowns blocking the haul plan"
              source="Live count · assignments held by breakdown"
              value={s.breakdown_impacts}
              loaded={s.loaded}
            />
          </div>
        </section>

        {/* Section 2 — Fleet & Shop action queues. */}
        <section data-testid="dispatch-hub-v2-section-fleet" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="02 · Fleet & Shop · live"
            title="Equipment + shop signals"
            caption="Cross-portal read from the same Command Center summary. Hold sources preserve their original workflow."
          />
          <div
            data-testid="dispatch-hub-v2-queue-grid-fleet"
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}
          >
            <QueueCard
              to="/dispatch-portal/fleet?focus_filter=oos"
              testid="dispatch-hub-v2-queue-fleet-oos"
              title="Fleet · Out of Service"
              why="Units in 'oos' status across the fleet"
              source="Live count · units out of service"
              value={s.fleet_oos}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/fleet?focus_filter=in_shop"
              testid="dispatch-hub-v2-queue-fleet-in-shop"
              title="Fleet · In Shop"
              why="Units physically routed to the shop"
              source="Live count · units currently in the shop"
              value={s.in_shop}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/fleet?focus_filter=defects"
              testid="dispatch-hub-v2-queue-shop-defects"
              title="Open Shop Defects"
              why="Defects active across the fleet (Pre-Op + fleet_defects)"
              source="Live count · open shop defects"
              value={s.shop_defects_open}
              loaded={s.loaded}
            />
          </div>
        </section>

        {/* Section 3 — Safety cross-portal read. */}
        <section data-testid="dispatch-hub-v2-section-safety" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="03 · Safety · cross-portal read"
            title="Safety attention items"
            caption="Read-only from the Safety engine — Dispatch sees these to coordinate, never to mutate."
          />
          <div
            data-testid="dispatch-hub-v2-queue-grid-safety"
            style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}
          >
            <QueueCard
              to="/dispatch-portal/command"
              testid="dispatch-hub-v2-queue-incidents-open"
              title="Open Incidents"
              why="Incidents not yet closed by the Safety team"
              source="Live count · open safety incidents"
              value={s.incidents_open}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/command"
              testid="dispatch-hub-v2-queue-capas-open"
              title="Open CAPAs"
              why="Corrective actions still open across the fleet"
              source="Live count · open corrective actions"
              value={s.capas_open}
              loaded={s.loaded}
            />
            <QueueCard
              to="/dispatch-portal/driver-qualification"
              testid="dispatch-hub-v2-queue-driver-qual"
              title="Driver Qualification"
              why="Approved-driver / CDL readiness dashboard (real Driver Qualification engine)"
              source="Live read · DOT and CDL readiness queue"
              value={null}
              loaded={true}
            />
          </div>
        </section>

        {allZero && (
          <EmptyState
            testId="dispatch-hub-v2-all-clear"
            title="Dispatch is all clear."
            explanation="No queue currently shows attention items. The live Command Center map remains the source of truth for in-the-moment ops."
            severity="good"
          />
        )}

      </PortalShell>
    </div>
  );
}
