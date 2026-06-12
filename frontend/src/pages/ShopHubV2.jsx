// Track 13.6I · Phase 5 — Shop Recovery (live hub).
//
// MOUNTED AT: /shop/hub_v2 (behind RequireShop — same gate as /shop).
// Classic Shop hub remains available as the legacy rollback at /shop/hub_legacy.
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

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, StatusChip, Card, EmptyState } from "../design-system";
// Track 13.7B · Shop Recovery Map lens — reuse the certified
// MapLibre engine + 15-s snapshot. NO new map system, NO new
// backend, NO new provider. Truthful copy enforced below.
import MapCanvas from "@/components/operations-map/MapCanvas";
import "@/components/operations-map/OperationsMap.css";
import { useMapSnapshot } from "@/lib/operations-map/useMapSnapshot";

const API = process.env.REACT_APP_BACKEND_URL;
const EMPTY_MAP_FILTERS = { types: [], status: [], driver: null, project: null };

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

// Track 13.7B · Shop Recovery Map lens.
// Reuses the certified MapLibre engine + 15-s snapshot.
// Filters to Shop-relevant attention reasons ONLY (no fabrication).
const REASON_LABEL = {
  maintenance: "Maintenance Due",
  inspection:  "Inspection Overdue",
};
const REASON_TONE = {
  maintenance: { bg: "#fff1f2", color: "#be123c", border: "#fda4af" },
  inspection:  { bg: "#fffbeb", color: "#b45309", border: "#fcd34d" },
};
// Operator-readable next-step matches `/api/operations-map/asset/{key}`
// (operations_map_v1.py `OWNER_BY_REASON` + `NEXT_BY_REASON`).
const REASON_NEXT = {
  maintenance: "Shop review open issue",
  inspection:  "Shop review inspection",
};

function ShopRecoveryRow({ asset, highlighted, onClick }) {
  const tone = REASON_TONE[asset.attention_reason] || { bg: "#f8fafc", color: "#0f172a", border: "#e2e8f0" };
  const where = (asset.assignment && asset.assignment.name) || "Unassigned / Unknown";
  return (
    <button
      type="button"
      data-testid={`shop-recovery-map-row-${asset.unit_number}`}
      onClick={onClick}
      style={{
        textAlign: "left", cursor: "pointer", width: "100%",
        background: highlighted ? "#fff7ed" : "var(--paper-card)",
        border: `1px solid ${highlighted ? "#fb923c" : "var(--border-bold)"}`,
        borderLeft: `5px solid ${tone.border}`,
        borderRadius: "var(--radius-card)",
        padding: "8px 12px",
        marginBottom: 8,
        display: "grid",
        gridTemplateColumns: "120px 1fr auto",
        gap: 10, alignItems: "baseline",
      }}
    >
      <span style={{
        fontFamily: "Chivo, IBM Plex Sans, sans-serif", fontWeight: 900,
        fontSize: 14, color: "var(--ink-strong)", letterSpacing: "0.03em",
      }}>{asset.unit_number || "—"}</span>
      <span style={{ fontSize: 12, color: "var(--ink-soft)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {where}
      </span>
      <span style={{
        fontSize: 10, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase",
        padding: "2px 8px", borderRadius: 999,
        background: tone.bg, color: tone.color, border: `1px solid ${tone.border}`,
      }}>{REASON_LABEL[asset.attention_reason] || asset.attention_reason}</span>
      <span style={{ gridColumn: "1 / -1", fontSize: 11, color: "#0f766e", fontWeight: 700 }}>
        Next: {REASON_NEXT[asset.attention_reason] || "Shop review"}
      </span>
    </button>
  );
}

function ShopRecoveryMap() {
  const { data, loading, error, lastFetchMs } = useMapSnapshot({ refreshMs: 15000 });
  const [selectedUnit, setSelectedUnit] = useState(null);
  // Responsive narrow detection (iPad portrait / phone). Re-evaluates on resize so
  // rotating the device flips the layout. Side-by-side ≥ 900px, stacked < 900px.
  const [narrow, setNarrow] = useState(
    typeof window !== "undefined" && window.innerWidth ? window.innerWidth < 900 : false
  );
  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const onResize = () => setNarrow(window.innerWidth < 900);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Filter to Shop-owned attention reasons ONLY. Source: per-asset
  // `attention_reason` field set by `/api/operations-map/snapshot`
  // (operations_map_v1.py lines 444–456). NO fabricated filters.
  const shopAssets = useMemo(() => {
    if (!data || !Array.isArray(data.assets)) return [];
    return data.assets.filter((a) => a.attention_reason === "maintenance" || a.attention_reason === "inspection");
  }, [data]);

  const filteredSnapshot = useMemo(() => ({
    assets: shopAssets,
    geofences: data?.geofences || [],
    counts: data?.counts || {},
  }), [shopAssets, data]);

  const updated = lastFetchMs ? new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—";
  const maintenanceCount = shopAssets.filter((a) => a.attention_reason === "maintenance").length;
  const inspectionCount  = shopAssets.filter((a) => a.attention_reason === "inspection").length;
  const gridCols = narrow ? "minmax(0, 1fr)" : "minmax(0, 1fr) minmax(0, 360px)";

  return (
    <section data-testid="shop-recovery-map-section" style={{ marginBottom: 28 }}>
      <SectionHeader
        kicker="03 · Recovery Map · secondary"
        title="Recovery Map"
        caption="Shop-visible units needing maintenance or inspection attention. Live location from current operations-map feed."
      />

      <div
        data-testid="shop-recovery-map-grid"
        style={{
          display: "grid",
          gridTemplateColumns: gridCols,
          gap: 16,
          alignItems: "stretch",
        }}
      >
        {/* Map embed — sized box; CSS scope rule in OperationsMap.css
            forces .ops-map-canvas to absolute-fill this container. */}
        <div
          data-testid="shop-recovery-map-wrap"
          style={{
            position: "relative", width: "100%", height: 360,
            background: "#0b1320",
            border: "1px solid var(--border-bold)",
            borderRadius: "var(--radius-card)",
            overflow: "hidden",
          }}
        >
          {loading && !data ? (
            <div data-testid="shop-recovery-map-loading"
              style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "#cbd5e1", fontSize: 13 }}>
              Loading live positions…
            </div>
          ) : error ? (
            <div data-testid="shop-recovery-map-error"
              style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", color: "#fda4af", fontSize: 13, padding: 16, textAlign: "center" }}>
              Map feed unavailable · {String(error)}
            </div>
          ) : (
            <MapCanvas
              snapshot={filteredSnapshot}
              filters={EMPTY_MAP_FILTERS}
              onSelect={(unit) => setSelectedUnit(unit || null)}
            />
          )}
        </div>

        {/* Unit list — primary interaction surface (Shop stays queue-first). */}
        <div data-testid="shop-recovery-map-list" style={{
          background: "var(--paper-card)",
          border: "1px solid var(--border-bold)",
          borderRadius: "var(--radius-card)",
          padding: "12px 12px 8px 12px",
          minHeight: 360, maxHeight: 360, overflowY: "auto",
        }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontSize: 10, letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 900, color: "var(--ink-strong)" }}>
              {shopAssets.length} unit{shopAssets.length === 1 ? "" : "s"}
            </span>
            <span data-testid="shop-recovery-map-as-of" style={{ fontSize: 10, color: "var(--ink-faint)" }}>
              Updated {updated}
            </span>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
            <span data-testid="shop-recovery-map-maintenance-count" style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase",
              padding: "2px 8px", borderRadius: 999,
              background: REASON_TONE.maintenance.bg, color: REASON_TONE.maintenance.color,
              border: `1px solid ${REASON_TONE.maintenance.border}`,
            }}>{maintenanceCount} Maintenance</span>
            <span data-testid="shop-recovery-map-inspection-count" style={{
              fontSize: 10, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase",
              padding: "2px 8px", borderRadius: 999,
              background: REASON_TONE.inspection.bg, color: REASON_TONE.inspection.color,
              border: `1px solid ${REASON_TONE.inspection.border}`,
            }}>{inspectionCount} Inspection</span>
          </div>
          {shopAssets.length === 0 ? (
            <EmptyState
              testId="shop-recovery-map-empty"
              title="No Shop attention on the map."
              explanation="No units currently carry a Shop-owned attention reason (maintenance or inspection) in the operations-map snapshot."
              severity="good"
            />
          ) : (
            shopAssets.map((a) => (
              <ShopRecoveryRow
                key={a.unit_number || a.asset_id}
                asset={a}
                highlighted={selectedUnit && a.unit_number === selectedUnit}
                onClick={() => setSelectedUnit(a.unit_number || null)}
              />
            ))
          )}
        </div>
      </div>

      <div data-testid="shop-recovery-map-truth-note" style={{
        marginTop: 10, padding: "10px 12px",
        background: "var(--paper-card)",
        border: "1px dashed var(--border-bold)",
        borderRadius: "var(--radius-card)",
        color: "var(--ink-soft)", fontSize: 11, lineHeight: 1.5,
      }}>
        <strong style={{ color: "var(--ink-strong)" }}>Provider truth.</strong>{" "}
        Maintenance and inspection attention based on existing operations-map snapshot.
        Live location from current operations-map feed. Provider availability depends on
        configured integrations — Motive is the verified live position feed today;
        MaintainX and FleetWatcher are not active providers for this map.
      </div>
    </section>
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
          Shop Hub V2 · Live Shop operations hub · Repair Complete and Returned-To-Service remain separate · Legacy rollback at /shop/hub_legacy
        </div>
      )}
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Portal · Hub V2"
        pageTitle="What equipment requires recovery right now?"
        subtitle="Every queue is live · sourced from /api/dispatch/command/summary.shop · clickable to a real Shop surface. Repair Complete ≠ Safe To Use — verification step preserved."
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <RealLink to="/shop/equipment" testid="shop-hub-v2-action-preops">Equipment Pre-Ops</RealLink>
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

        {/* Section 3 — Recovery Map · secondary lens (Track 13.7B). */}
        <ShopRecoveryMap />

        {/* Section 4 · Shop Records · live (Track 13.24).
            Direct entry points to the existing live record surfaces so
            mechanics and shop managers don't have to hunt through hidden
            routes. Each card links to a real mounted page backed by a real
            endpoint. No fabricated counts here — counts live on the
            destination pages. */}
        <section data-testid="shop-hub-v2-section-records" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="04 · Shop Records · live"
            title="Equipment Pre-Ops · Truck DVIRs · Defect history"
            caption="Direct access to the existing record surfaces. No new system — links to live pages backed by real endpoints."
          />
          <div data-testid="shop-hub-v2-records-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <RealLink to="/shop/equipment" testid="shop-hub-v2-record-preops" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
              <div style={{
                padding: "var(--pad-card)", background: "var(--paper-card)",
                border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink-strong)" }}>Equipment Pre-Ops</div>
                <div style={{ marginTop: 6, fontSize: 12, color: "var(--ink-soft)" }}>
                  Pre-operation inspection list — opens the live Equipment Dashboard.
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
                  Source: /api/equipment-inspections (newest first · 1000-row cap · shop+admin scope)
                </div>
              </div>
            </RealLink>
            <RealLink to="/shop/fleet" testid="shop-hub-v2-record-dvirs" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
              <div style={{
                padding: "var(--pad-card)", background: "var(--paper-card)",
                border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink-strong)" }}>Truck DVIRs · Fleet Visibility</div>
                <div style={{ marginTop: 6, fontSize: 12, color: "var(--ink-soft)" }}>
                  Per-unit DVIR + defect state. Defect detail, acknowledge, repair, RTS audit trail are reached from each unit row.
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
                  Source: /api/shop/fleet/by-unit · /api/fleet/defects/{`{id}`}/detail
                </div>
              </div>
            </RealLink>
            <RealLink to="/shop/fleet?focus_filter=defects" testid="shop-hub-v2-record-defects" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
              <div style={{
                padding: "var(--pad-card)", background: "var(--paper-card)",
                border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink-strong)" }}>Defect / Inspection History</div>
                <div style={{ marginTop: 6, fontSize: 12, color: "var(--ink-soft)" }}>
                  Full defect list across the fleet — same source as Section 01 Open Defects tile, but unfiltered.
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
                  Source: /api/shop/fleet/defects
                </div>
              </div>
            </RealLink>
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

        {/* Track 13.28 Phase 2 — Shop Workforce surfaces. */}
        <section data-testid="shop-hub-v2-section-workforce" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="05 · Shop Workforce · live"
            title="Manager queue · My assignments"
            caption="Track 13.28 lifecycle: assign → accept → start → repair → manager review → Dispatch RTS. Every action attributable. Repair Complete ≠ RTS."
          />
          <div data-testid="shop-hub-v2-workforce-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
            <RealLink to="/shop/manager/queue" testid="shop-hub-v2-action-manager-queue" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
              <div style={{
                padding: "var(--pad-card)", background: "var(--paper-card)",
                border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink-strong)" }}>Manager Queue</div>
                <div style={{ marginTop: 6, fontSize: 12, color: "var(--ink-soft)" }}>
                  Unassigned · Assigned · Accepted · In Progress · Pending Review · RTS Pending. Assign to mechanic. Approve / reject completed repairs.
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
                  Source: /api/shop/manager/queue (Track 13.28 lifecycle endpoints)
                </div>
              </div>
            </RealLink>
            <RealLink to="/shop/me" testid="shop-hub-v2-action-my-assignments" style={{ display: "block", textDecoration: "none", color: "inherit" }}>
              <div style={{
                padding: "var(--pad-card)", background: "var(--paper-card)",
                border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
              }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: "var(--ink-strong)" }}>My Assignments</div>
                <div style={{ marginTop: 6, fontSize: 12, color: "var(--ink-soft)" }}>
                  Mechanic-only view of work assigned to me. Accept · start · complete with repair notes + parts used.
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: "var(--ink-faint)", fontStyle: "italic" }}>
                  Source: /api/shop/me/assignments (Track 13.28 per-user queue)
                </div>
              </div>
            </RealLink>
          </div>
        </section>

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
