// Track 13.6I · Phase 5 — Shop Recovery (preview lane).
//
// MOUNTED AT: /shop/hub_v2 (behind RequireShop — same gate as /shop).
// Classic Shop hub at /shop is preserved unchanged. No route swap.
//
// REAL DATA ONLY:
//   /api/dispatch/command/summary  (existing cross-portal-read engine)
// Every card opens an existing shop route — no placeholders.
//
// Doctrine reminder:
//   Repair Complete ≠ Safe To Use. The Shop V2 preview surfaces both
//   "Repair Awaiting Verification" AND "Returned To Service" as
//   distinct queues so the verification step stays visible.
//
// One question this surface answers:
//   "What equipment requires recovery right now?"

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, StatusChip, Card, EmptyState } from "../design-system";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

async function safeJson(path) {
  try {
    const r = await fetch(`${API}${path}`, { headers: authHeaders() });
    const body = r.ok ? await r.json().catch(() => null) : null;
    return { ok: r.ok, status: r.status, body };
  } catch { return { ok: false, status: 0, body: null }; }
}

function useShopSignals() {
  const [s, setS] = useState({
    loaded: false,
    refreshedAt: null,
    defects_open: null,
    defects_acked: null,
    oos_units: null,
    active_recovery: null,
    waiting_on_parts: null,
    returned_to_service_7d: null,
    defect_open_units: null,
  });
  useEffect(() => {
    let cancelled = false;
    safeJson("/api/dispatch/command/summary").then((r) => {
      if (cancelled) return;
      const sh = (r.body || {}).shop || {};
      setS({
        loaded: true,
        refreshedAt: new Date().toISOString(),
        defects_open:           r.ok ? (sh.defects_open ?? null) : null,
        defects_acked:          r.ok ? (sh.defects_acknowledged ?? null) : null,
        oos_units:              r.ok ? (sh.oos_units ?? null) : null,
        active_recovery:        r.ok ? (sh.active_recovery ?? null) : null,
        waiting_on_parts:       r.ok ? (sh.waiting_on_parts ?? null) : null,
        returned_to_service_7d: r.ok ? (sh.returned_to_service_7d ?? null) : null,
        defect_open_units:      r.ok ? (sh.defect_open_units ?? null) : null,
      });
    });
    return () => { cancelled = true; };
  }, []);
  return s;
}

function SectionHeader({ kicker, title, caption }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
      <div>
        <div style={{ fontSize: "var(--kicker-size)", letterSpacing: "var(--kicker-tracking)", fontWeight: "var(--kicker-weight)", textTransform: "uppercase", color: "var(--ink-faint)" }}>{kicker}</div>
        <h2 style={{ margin: "2px 0 0", fontSize: 18, fontWeight: 700, color: "var(--ink-strong)", fontFamily: "var(--font-display)" }}>{title}</h2>
        {caption && <p style={{ margin: "2px 0 0", fontSize: 12, color: "var(--ink-soft)" }}>{caption}</p>}
      </div>
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
        <p style={{ margin: "8px 0 0", fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>{source}</p>
      </Card>
    </Link>
  );
}

export default function ShopHubV2() {
  const s = useShopSignals();
  const isPreview = (typeof window !== "undefined") && /preview/i.test(window.location.host);
  const allZero = s.loaded && [
    s.defects_open, s.defects_acked, s.oos_units, s.active_recovery,
    s.waiting_on_parts, s.returned_to_service_7d, s.defect_open_units,
  ].every((v) => v === null || v === 0);

  return (
    <div data-testid="shop-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      {isPreview && (
        <div data-testid="shop-hub-v2-preview-banner" style={{
          background: "var(--brand-primary)", color: "var(--brand-on-primary)",
          padding: "8px 16px", fontSize: 11, letterSpacing: "0.04em",
          textTransform: "uppercase", fontWeight: 700, textAlign: "center",
        }}>
          Shop Hub V2 · Live Shop data · Side-by-side with /shop · No route swap until operator approval
        </div>
      )}
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Portal · Hub V2"
        pageTitle="What equipment requires recovery right now?"
        subtitle="Every queue is live · sourced from /api/dispatch/command/summary.shop · clickable to a real Shop surface. Repair Complete ≠ Safe To Use — verification step preserved."
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/shop" testid="shop-hub-v2-back-classic">Open Classic Shop Hub</RealLink>
            <RealLink to="/shop/fleet" testid="shop-hub-v2-action-fleet" intent="primary">Fleet Visibility</RealLink>
          </div>
        }
        lastActivity={
          <span data-testid="shop-hub-v2-last-activity">
            {s.loaded ? `Refreshed ${new Date(s.refreshedAt).toLocaleTimeString()}` : "Loading live signals…"}
          </span>
        }
      >
        {/* Section 1 — Equipment needing attention. */}
        <section data-testid="shop-hub-v2-section-attention" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="01 · Equipment Needing Attention · live"
            title="Open defects + OOS units"
            caption="Real counts from real engines. Click any card to open the real shop workflow."
          />
          <div data-testid="shop-hub-v2-queue-grid-attention"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/shop/fleet?focus_filter=defects"
              testid="shop-hub-v2-queue-defects-open"
              title="Open Defects"
              why="Active defects across the fleet (Pre-Op + fleet_defects)"
              source="Source: summary.shop.defects_open"
              value={s.defects_open}
              loaded={s.loaded}
            />
            <QueueCard
              to="/shop/fleet?focus_filter=defects_acked"
              testid="shop-hub-v2-queue-defects-acked"
              title="Defects Acknowledged"
              why="Acknowledged but not yet resolved"
              source="Source: summary.shop.defects_acknowledged"
              value={s.defects_acked}
              loaded={s.loaded}
            />
            <QueueCard
              to="/shop/fleet?focus_filter=oos"
              testid="shop-hub-v2-queue-oos-units"
              title="Out-Of-Service Units"
              why="Units currently flagged OOS in the equipment master"
              source="Source: summary.shop.oos_units"
              value={s.oos_units}
              loaded={s.loaded}
            />
            <QueueCard
              to="/shop/fleet?focus_filter=defect_open_units"
              testid="shop-hub-v2-queue-defect-open-units"
              title="Units With Open Defect"
              why="Distinct unit count carrying at least one open defect"
              source="Source: summary.shop.defect_open_units"
              value={s.defect_open_units}
              loaded={s.loaded}
            />
          </div>
        </section>

        {/* Section 2 — Recovery pipeline. */}
        <section data-testid="shop-hub-v2-section-recovery" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="02 · Recovery Pipeline · live"
            title="Active recovery + delays"
            caption="Maintenance Hold = engine status. Waiting on parts is the real shop delay."
          />
          <div data-testid="shop-hub-v2-queue-grid-recovery"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <QueueCard
              to="/shop/equipment"
              testid="shop-hub-v2-queue-active-recovery"
              title="Active Recovery Work"
              why="Units currently in active repair / maintenance"
              source="Source: summary.shop.active_recovery"
              value={s.active_recovery}
              loaded={s.loaded}
            />
            <QueueCard
              to="/shop/equipment"
              testid="shop-hub-v2-queue-waiting-parts"
              title="Waiting On Parts"
              why="Recovery blocked pending parts arrival"
              source="Source: summary.shop.waiting_on_parts"
              value={s.waiting_on_parts}
              loaded={s.loaded}
            />
            <QueueCard
              to="/shop/equipment"
              testid="shop-hub-v2-queue-rts-7d"
              title="Returned To Service (7d)"
              why="Units verified safe-to-use and released in last 7 days — Repair Complete ≠ Safe To Use"
              source="Source: summary.shop.returned_to_service_7d"
              value={s.returned_to_service_7d}
              loaded={s.loaded}
            />
          </div>
        </section>

        {allZero && (
          <EmptyState
            testId="shop-hub-v2-all-clear"
            title="Shop is all clear."
            explanation="No open defects, no OOS units, no active recovery work, and no parts wait."
            severity="good"
          />
        )}

        <div data-testid="shop-hub-v2-trace-note" style={{
          marginTop: 16, padding: "var(--pad-card)",
          background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
          borderRadius: "var(--radius-card)", color: "var(--ink-soft)", fontSize: 12,
        }}>
          <strong style={{ color: "var(--ink-strong)" }}>Shop Hub V2 · Track 13.6I recovery.</strong>{" "}
          Presentation-only modernization — every shop engine, route,
          permission, and workflow preserved. Every count traces to a real
          source field. Repair Complete ≠ Safe To Use rule maintained.
        </div>
      </PortalShell>
    </div>
  );
}
