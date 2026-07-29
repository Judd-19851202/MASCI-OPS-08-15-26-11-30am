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
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { PortalShell, StatusChip, Card, EmptyState } from "../design-system";
import ShopSideNavV2, { isShopSidebarV2Enabled } from "@/components/shop/sidebar/ShopSideNavV2";
// Track 13.7B · Shop Recovery Map lens — reuse the certified
// MapLibre engine + 15-s snapshot. NO new map system, NO new
// backend, NO new provider. Truthful copy enforced below.
import MapCanvas from "@/components/operations-map/MapCanvas";
import "@/components/operations-map/OperationsMap.css";
import { useMapSnapshot } from "@/lib/operations-map/useMapSnapshot";
import OiAttentionStrip from "@/components/operational_intelligence/OiAttentionStrip";

const API = process.env.REACT_APP_BACKEND_URL;
const EMPTY_MAP_FILTERS = { types: [], status: [], driver: null, project: null };

function authHeaders() {
  return buildScopedPortalAuthHeaders(["admin", "shop"], { "Content-Type": "application/json" });
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
  // Retained as a tiny helper for the Recovery Map row; the previous
  // top-of-hub usage was replaced by HubCard in the Command Center
  // restructure (Track 13.30B).
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
  const hasUnit = !!asset.unit_number;
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
      <span style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 11, color: "#0f766e", fontWeight: 700 }}>
          Next: {REASON_NEXT[asset.attention_reason] || "Shop review"}
        </span>
        {hasUnit && (
          <Link
            to={`/shop/units/${encodeURIComponent(asset.unit_number)}/history`}
            data-testid={`shop-recovery-map-row-history-${asset.unit_number}`}
            onClick={(e) => e.stopPropagation()}
            style={{
              fontSize: 10, fontWeight: 700, letterSpacing: ".03em",
              color: "var(--brand-primary, #1b4965)", textDecoration: "none",
            }}
          >
            Open History →
          </Link>
        )}
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

  const updated = lastFetchMs ? formatPlatformTimeOnly() : "—";
  const maintenanceCount = shopAssets.filter((a) => a.attention_reason === "maintenance").length;
  const inspectionCount  = shopAssets.filter((a) => a.attention_reason === "inspection").length;
  const gridCols = narrow ? "minmax(0, 1fr)" : "minmax(0, 1fr) minmax(0, 360px)";

  return (
    <section data-testid="shop-recovery-map-section" style={{ marginBottom: 28 }}>
      <SectionHeader
        kicker="09 · Recovery Map · secondary"
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
        Live position feed from Motive. MaintainX and FleetWatcher are not active providers for this map.
      </div>
    </section>
  );
}

// ─── Shop Command Center (Track 13.30B + 13.30C) ──────────────────
// Workflow-first layout: Header w/ Global Unit Search → Role-aware
// Your Queue strip → Attention Required → Active Work → Parts +
// Waiting → Fuel / Service → Unit Intelligence → Records → Recovery
// Map. Engineering copy removed; every link resolves to a mounted
// route; no fake counts; preserves all hard locks (Repair Complete ≠
// RTS; Dispatch retains RTS authority).

import UnitSearchComponent from "@/components/shop/UnitSearch";
import YourQueueStripComponent from "@/components/shop/YourQueueStrip";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

function HubCard({ to, testid, title, body, metric, status, dense }) {
  const showMetric = metric !== undefined && metric !== null;
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <Card
        title={title}
        description={body}
        metric={showMetric ? metric : undefined}
        variant={status === "attention" ? "warning" : "default"}
        status={
          status === "loading" ? <StatusChip statusKey="draft" compact label="Loading" />
          : status === "offline" ? <StatusChip statusKey="offline_feed" compact />
          : status === "attention" ? <StatusChip statusKey="pending_verification" compact />
          : status === "verified" ? <StatusChip statusKey="verified" compact />
          : null
        }
        compact={!!dense}
      />
    </Link>
  );
}

// Track 13.30C · Priority metric tile for Section 01.
// Stronger visual hierarchy: red for live attention, amber for needs
// review, calm for clear. Loads with "—" until live signals hydrate.
function PriorityMetric({ to, testid, label, description, value, loaded, accent }) {
  const hasValue = loaded && typeof value === "number";
  const active = hasValue && value > 0;
  const palette = active
    ? (accent === "red"
        ? { bg: "#fef2f2", border: "#fecaca", text: "#991b1b", chip: "pending_verification" }
        : { bg: "#fffbeb", border: "#fde68a", text: "#92400e", chip: "pending_verification" })
    : { bg: "var(--paper-card)", border: "var(--border-bold)", text: "var(--ink-strong)",
        chip: loaded ? "verified" : "draft" };
  const chipLabel = !loaded ? "Loading" : (value === null || value === undefined ? "Offline" : (active ? "Action" : "Clear"));
  return (
    <Link to={to} data-testid={testid} style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <div style={{
        padding: "16px 18px", background: palette.bg, border: `1px solid ${palette.border}`,
        borderRadius: "var(--radius-card)", minHeight: 116,
        display: "flex", flexDirection: "column", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: palette.text, textTransform: "uppercase", letterSpacing: ".04em" }}>{label}</div>
          <StatusChip statusKey={palette.chip} compact label={chipLabel} />
        </div>
        <div data-testid={`${testid}-value`} style={{
          fontSize: 38, fontWeight: 800, color: palette.text, lineHeight: 1,
          marginTop: 6,
        }}>
          {!loaded ? "…" : (value == null ? "—" : value)}
        </div>
        <div style={{ marginTop: 6, fontSize: 11, color: "var(--ink-soft)" }}>{description}</div>
      </div>
    </Link>
  );
}

// Track 13.30D · Parts-on-order rollup card (live).
function PartsOnOrderCard() {
  const [d, setD] = React.useState(null);
  const [unavailable, setUnavailable] = React.useState(false);
  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/shop/parts/on-order/summary?limit=5`, { headers: authHeaders() });
        if (!r.ok) {
          if (alive) setUnavailable(true);
          return;
        }
        const b = await r.json().catch(() => null);
        if (alive) setD(b);
      } catch { if (alive) setUnavailable(true); }
    })();
    return () => { alive = false; };
  }, []);
  if (unavailable) return (
    <div data-testid="shop-hub-v2-parts-rollup-unavailable"
         style={{ padding: "12px 14px", fontSize: 12, color: "var(--ink-soft)",
                  background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
                  borderRadius: "var(--radius-card)" }}>
      Parts rollup is not available for your role. Open the Manager Queue to see parts-on-order items directly.
    </div>
  );
  if (!d)  return <div data-testid="shop-hub-v2-parts-rollup-loading" style={{ padding: 12, fontSize: 12, color: "var(--ink-soft)" }}>Loading…</div>;
  return (
    <div data-testid="shop-hub-v2-parts-rollup" style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 12 }}>
        {[
          ["Total parts on order", d.total_parts_on_order, "amber"],
          ["Units waiting",        d.units_waiting_parts,  d.units_waiting_parts > 0 ? "amber" : "calm"],
          ["Defects waiting",      d.defects_waiting_parts, d.defects_waiting_parts > 0 ? "amber" : "calm"],
          ["Expected today",       d.expected_today,       "blue"],
          ["Overdue",              d.overdue_parts,        d.overdue_parts > 0 ? "red" : "calm"],
        ].map(([label, value, accent]) => {
          const p = accent === "red"   ? { bg: "#fef2f2", border: "#fecaca", text: "#991b1b" }
                  : accent === "amber" ? { bg: "#fffbeb", border: "#fde68a", text: "#92400e" }
                  : accent === "blue"  ? { bg: "#eff6ff", border: "#bfdbfe", text: "#1e40af" }
                                       : { bg: "var(--paper-card)", border: "var(--border-bold)", text: "var(--ink-strong)" };
          return (
            <div key={label} data-testid={`shop-hub-v2-parts-${label.toLowerCase().replace(/\s+/g, "-")}`}
                 style={{ padding: "12px 14px", background: p.bg, border: `1px solid ${p.border}`,
                          borderRadius: "var(--radius-card)" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: p.text, textTransform: "uppercase", letterSpacing: ".04em" }}>{label}</div>
              <div style={{ fontSize: 28, fontWeight: 800, color: p.text, lineHeight: 1, marginTop: 4 }}>{value}</div>
            </div>
          );
        })}
      </div>
      {d.items && d.items.length > 0 && (
        <div data-testid="shop-hub-v2-parts-rollup-list" style={{
          background: "var(--paper-card)", border: "1px solid var(--border-bold)",
          borderRadius: "var(--radius-card)", overflow: "hidden",
        }}>
          {d.items.slice(0, 5).map((it, i) => (
            <Link key={it.defect_id + "-" + i} to={it.links?.unit_history || "/shop/manager/queue"}
                  data-testid={`shop-hub-v2-parts-row-${it.unit_number}`}
                  style={{ display: "block", padding: "8px 12px", textDecoration: "none", color: "inherit",
                           borderBottom: i < d.items.length - 1 ? "1px solid #e5e7eb" : "none" }}>
              <div style={{ fontSize: 12, fontWeight: 700 }}>
                {it.unit_number || "—"} · {it.part_name || "—"} {it.quantity > 1 ? `× ${it.quantity}` : ""}
              </div>
              <div style={{ fontSize: 11, color: "var(--ink-soft)" }}>
                {it.assigned_mechanic_name ? `Mechanic: ${it.assigned_mechanic_name} · ` : ""}
                {it.expected_date ? `Expected: ${it.expected_date} · ` : ""}
                Age {it.age_days}d
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

// Track 13.31 · PM Engine summary card (live · read-only).
function PmEngineCard() {
  const [d, setD] = React.useState(null);
  const [unavailable, setUnavailable] = React.useState(false);
  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/shop/pm/summary`, { headers: authHeaders() });
        if (!r.ok) {
          if (alive) setUnavailable(true);
          return;
        }
        const b = await r.json().catch(() => null);
        if (alive) setD(b);
      } catch { if (alive) setUnavailable(true); }
    })();
    return () => { alive = false; };
  }, []);
  if (unavailable) return (
    <div data-testid="shop-hub-v2-pm-unavailable"
         style={{ padding: "12px 14px", fontSize: 12, color: "var(--ink-soft)",
                  background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
                  borderRadius: "var(--radius-card)" }}>
      PM Engine summary is not available for your role. Use the PM Dashboard link below to view detail.
    </div>
  );
  if (!d)  return <div data-testid="shop-hub-v2-pm-loading" style={{ padding: 12, fontSize: 12, color: "var(--ink-soft)" }}>Loading…</div>;
  const sc = d.schedule_counts || {};
  const wo = d.work_order_counts || {};
  const tiles = [
    ["PM overdue",        sc.overdue,           "red",   "/shop/pm/schedules?status=overdue"],
    ["PM due",            sc.due,               "amber", "/shop/pm/schedules?status=due"],
    ["PM due soon",       sc.due_soon,          "blue",  "/shop/pm/schedules?status=due_soon"],
    ["PM unassigned",     d.unassigned,         "red",   "/shop/pm/work-orders?status=open"],
    ["PM in progress",    wo.in_progress,       "blue",  "/shop/pm/work-orders?status=in_progress"],
    ["PM waiting parts",  wo.waiting_parts,     "amber", "/shop/pm/work-orders?status=waiting_parts"],
    ["PM pending review", wo.completed,         "amber", "/shop/pm/work-orders?status=completed"],
    ["PM needs meter",    sc.unknown_meter,     "grey",  "/shop/pm/schedules?status=unknown_meter"],
  ];
  return (
    <div data-testid="shop-hub-v2-pm-grid" style={{
      display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12,
    }}>
      {tiles.map(([label, value, accent, to]) => {
        const active = (typeof value === "number") && value > 0;
        const p = !active ? { bg: "var(--paper-card)", border: "var(--border-bold)", text: "var(--ink-strong)" }
              : accent === "red"   ? { bg: "#fef2f2", border: "#fecaca", text: "#991b1b" }
              : accent === "amber" ? { bg: "#fffbeb", border: "#fde68a", text: "#92400e" }
              : accent === "blue"  ? { bg: "#eff6ff", border: "#bfdbfe", text: "#1e40af" }
              :                      { bg: "#f1f5f9", border: "#cbd5e1", text: "#475569" };
        const tid = `shop-hub-v2-pm-${label.toLowerCase().replace(/\s+/g, "-")}`;
        return (
          <Link key={label} to={to} data-testid={tid}
                style={{ textDecoration: "none", color: "inherit", display: "block" }}>
            <div style={{ padding: "12px 14px", background: p.bg, border: `1px solid ${p.border}`,
                          borderRadius: "var(--radius-card)" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: p.text, textTransform: "uppercase", letterSpacing: ".04em" }}>{label}</div>
              <div data-testid={`${tid}-value`} style={{ fontSize: 28, fontWeight: 800, color: p.text, lineHeight: 1, marginTop: 4 }}>{value ?? "—"}</div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

// Track 13.30D · Mechanic workload card (live · non-punitive).
function MechanicWorkloadCard() {
  const [d, setD] = React.useState(null);
  const [unavailable, setUnavailable] = React.useState(false);
  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/shop/mechanics/workload`, { headers: authHeaders() });
        if (!r.ok) {
          if (alive) setUnavailable(true);
          return;
        }
        const b = await r.json().catch(() => null);
        if (alive) setD(b);
      } catch { if (alive) setUnavailable(true); }
    })();
    return () => { alive = false; };
  }, []);
  if (unavailable) return (
    <div data-testid="shop-hub-v2-workload-unavailable"
         style={{ padding: "12px 14px", fontSize: 12, color: "var(--ink-soft)",
                  background: "var(--paper-card)", border: "1px dashed var(--border-bold)",
                  borderRadius: "var(--radius-card)" }}>
      Mechanic workload is not available for your role. Mechanics see their own queue at My Assignments; managers see all queues at Manager Queue.
    </div>
  );
  if (!d)  return <div data-testid="shop-hub-v2-workload-loading" style={{ padding: 12, fontSize: 12, color: "var(--ink-soft)" }}>Loading…</div>;
  if (!d.mechanics || d.mechanics.length === 0) {
    return <div data-testid="shop-hub-v2-workload-empty" style={{ padding: 12, fontSize: 12, color: "var(--ink-soft)", background: "var(--paper-card)", border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)" }}>
      No mechanics currently assigned to active work.
    </div>;
  }
  const LOAD_LABEL = { clear: "Clear", normal: "Normal", busy: "Busy", heavy_load: "Heavy load" };
  const LOAD_TONE  = {
    clear:      { bg: "#dcfce7", text: "#166534" },
    normal:     { bg: "#eff6ff", text: "#1e40af" },
    busy:       { bg: "#fffbeb", text: "#92400e" },
    heavy_load: { bg: "#fee2e2", text: "#991b1b" },
  };
  return (
    <div data-testid="shop-hub-v2-workload-grid" style={{
      display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12,
    }}>
      {d.mechanics.slice(0, 12).map((m) => {
        const t = LOAD_TONE[m.load_status] || LOAD_TONE.clear;
        return (
          <Link key={m.mechanic_id} to="/shop/manager/queue"
                data-testid={`shop-hub-v2-workload-row-${m.mechanic_id}`}
                style={{ textDecoration: "none", color: "inherit", display: "block",
                         padding: "12px 14px", background: "var(--paper-card)",
                         border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
              <strong style={{ fontSize: 13, color: "var(--ink-strong)" }}>{m.mechanic_name}</strong>
              <span style={{ padding: "2px 8px", borderRadius: 3, background: t.bg, color: t.text, fontSize: 10, fontWeight: 700, textTransform: "uppercase" }}>
                {LOAD_LABEL[m.load_status] || m.load_status}
              </span>
            </div>
            <div style={{ marginTop: 6, fontSize: 11, color: "var(--ink-soft)" }}>
              Assigned <strong>{m.assigned}</strong> · Accepted <strong>{m.accepted}</strong> ·
              In progress <strong>{m.in_progress}</strong> · Waiting parts <strong>{m.waiting_parts}</strong> ·
              Pending review <strong>{m.pending_review}</strong>{m.rejected_back > 0 ? <> · <span style={{ color: "#991b1b" }}>Rejected back {m.rejected_back}</span></> : null}
            </div>
            {m.current_units.length > 0 && (
              <div style={{ marginTop: 4, fontSize: 11, color: "var(--ink-soft)" }}>
                Units: {m.current_units.join(", ")}
              </div>
            )}
          </Link>
        );
      })}
    </div>
  );
}

export default function ShopHubV2() {
  const s = useShopSignals();
  const allZero = s.loaded && [
    s.defects_open, s.defects_acked, s.oos_units, s.active_recovery,
    s.waiting_on_parts, s.returned_to_service_7d, s.defect_open_units,
  ].every((v) => v === null || v === 0);

  // Track 19.28 · P0-3 · Shop Tile Visibility Polish.
  // Asset Administrator · Historical Records section is a specialized
  // workspace. Non-asset-admin shop users (mechanics, shop managers, etc.)
  // should NOT see these tiles — the backend already blocks the workflow,
  // but the tiles were creating confusing "click and blocked" UX.
  //
  // Visibility rule:
  //   - Admin token holders → always see (super-admins).
  //   - Shop users with masci.is_asset_admin=true → see it.
  //   - Everyone else → hidden.
  const isAssetAdmin = React.useMemo(() => {
    try {
      if (buildScopedPortalAuthHeaders(["admin"])["X-Admin-Token"]) return true;
      if (typeof window !== "undefined") {
        return window.localStorage.getItem("masci.is_asset_admin") === "true";
      }
    } catch { /* noop */ }
    return false;
  }, []);

  // Live-count helpers
  const num = (v) => (s.loaded ? (v === null || v === undefined ? "—" : v) : "…");
  const tone = (v) => (!s.loaded ? "loading" : v === null ? "offline" : v > 0 ? "attention" : "verified");

  return (
    <div data-testid="shop-hub-v2-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Operations"
        pageTitle="Shop Command Center"
        subtitle="What needs attention · what's assigned · what's waiting. Repair complete still requires RTS verification by Dispatch."
        primaryActions={
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
            <Link to="/shop/equipment" data-testid="shop-hub-v2-action-preops"
                  style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                           background: "var(--paper-card)", color: "var(--ink-strong)",
                           border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>Equipment Pre-Ops</Link>
            <Link to="/shop/fleet" data-testid="shop-hub-v2-action-fleet"
                  style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                           background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                           border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>Fleet Visibility</Link>
            <Link to="/shop/fuel-lube/new" data-testid="shop-hub-v2-action-fuel-lube-new-top"
                  style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                           background: "var(--paper-card)", color: "var(--ink-strong)",
                           border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>New Fuel/Lube Visit</Link>
            {/* Track 15.13A · Asset Care entry point on the Shop Hub.
                Always visible — same design system, same chrome — so any
                shop user (Asset Admin, Asset Manager, Shop Manager,
                Mechanic) can reach the Asset Care & Readiness workspace
                without typing the URL. Asset admins still land there
                directly via ShopLogin → landingFor(); this link covers
                the case where someone navigates to /shop manually. */}
            <Link to="/shop/asset-care" data-testid="shop-hub-v2-action-asset-care"
                  style={{ padding: "6px 12px", fontSize: 12, fontWeight: 600,
                           background: "var(--paper-card)", color: "var(--ink-strong)",
                           border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>Asset Care &amp; Readiness</Link>
          </div>
        }
        lastActivity={
          <span data-testid="shop-hub-v2-last-activity">
            {s.loaded ? `Refreshed ${formatPlatformTimeOnly(s.refreshedAt)}` : "Loading live signals…"}
          </span>
        }
        sideNav={isShopSidebarV2Enabled() ? <ShopSideNavV2 /> : undefined}
      >
        {/* Track 19.52 · P1 #4 — OI Attention Strip.
           shop_intelligence signal at the top of the Shop Hub —
           safety holds → aging critical defects → OOS. Zero-drift. */}
        <OiAttentionStrip
          portal="shop"
          productIds={["shop_intelligence"]}
          title="Shop Intelligence · attention now"
          testId="shop-hub-v2-oi-strip"
        />

        {/* Global Unit Search · Track 13.30C — sits directly under the
            primary action row so it is visible without scrolling. */}
        <section data-testid="shop-hub-v2-unit-search-section"
                 style={{ marginBottom: 18 }}>
          <UnitSearchComponent inline />
        </section>

        {/* Role-aware Your Queue strip · Track 13.30C — replaces the
            generic strip when the caller resolves to manager/mechanic. */}
        <YourQueueStripComponent />

        {/* 01 · Attention Required — what is down, what is open, what is
            blocking the shop right now. Live counts only. Priority styling
            (red/amber/calm) per count tone. */}
        <section data-testid="shop-hub-v2-section-attention" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="01 · Attention required"
            title="What needs the shop's attention right now"
            caption="Live shop counts. Click any tile to open the underlying queue."
          />
          <div data-testid="shop-hub-v2-attention-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            <PriorityMetric to="/shop/fleet?focus_filter=oos" testid="shop-hub-v2-queue-oos-units"
                     label="Out-of-Service units"
                     description="Units flagged OOS in the equipment master."
                     value={s.oos_units} loaded={s.loaded} accent="red" />
            <PriorityMetric to="/shop/fleet?focus_filter=defects" testid="shop-hub-v2-queue-defects-open"
                     label="Open defects"
                     description="Active defects across the fleet (pre-op + DVIR + fuel/lube)."
                     value={s.defects_open} loaded={s.loaded} accent="red" />
            <PriorityMetric to="/shop/fleet?focus_filter=defect_open_units" testid="shop-hub-v2-queue-defect-open-units"
                     label="Units carrying defects"
                     description="Distinct units with at least one open defect."
                     value={s.defect_open_units} loaded={s.loaded} accent="amber" />
            <PriorityMetric to="/shop/equipment" testid="shop-hub-v2-queue-waiting-parts"
                     label="Waiting on parts"
                     description="Recovery blocked pending parts arrival."
                     value={s.waiting_on_parts} loaded={s.loaded} accent="amber" />
          </div>
        </section>

        {/* 02 · Active Work — Manager Queue + My Assignments + acknowledged. */}
        <section data-testid="shop-hub-v2-section-active-work" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="02 · Active work"
            title="Defects in flight"
            caption="Assign · accept · start · complete · review. Repair complete still requires RTS verification."
          />
          <div data-testid="shop-hub-v2-active-work-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            <HubCard to="/shop/manager/queue" testid="shop-hub-v2-aw-manager-queue"
                     title="Manager Queue" body="Six buckets · assign · reassign · review." />
            <HubCard to="/shop/me" testid="shop-hub-v2-aw-my-assignments"
                     title="My Assignments" body="Mechanic-only queue — accept · start · complete with parts." />
            <HubCard to="/shop/fleet?focus_filter=defects_acked" testid="shop-hub-v2-aw-acknowledged"
                     title="Acknowledged · not yet repaired"
                     body="Defects accepted by shop but repair not yet complete."
                     metric={num(s.defects_acked)} status={tone(s.defects_acked)} />
            <HubCard to="/shop/equipment" testid="shop-hub-v2-aw-active-recovery"
                     title="Active recovery work" body="Units currently in active repair or maintenance."
                     metric={num(s.active_recovery)} status={tone(s.active_recovery)} />
          </div>
        </section>

        {/* 03 · Mechanic Workload — live per-mechanic queue. */}
        <section data-testid="shop-hub-v2-section-mechanic-workload" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="03 · Mechanic workload"
            title="Who's loaded right now"
            caption="Per-mechanic open · accepted · in progress · waiting parts. Click any row to open the manager queue."
          />
          <MechanicWorkloadCard />
        </section>

        {/* 04 · Preventive Maintenance — live PM Engine summary (Track 13.31). */}
        <section data-testid="shop-hub-v2-section-pm" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="04 · Preventive maintenance"
            title="PM due · overdue · in flight"
            caption="PM completion does NOT return units to service. Dispatch retains RTS authority."
          />
          <PmEngineCard />
          <div style={{ marginTop: 10, display: "flex", gap: 8, flexWrap: "wrap" }}>
            <Link to="/shop/pm" data-testid="shop-hub-v2-pm-dashboard-link"
                  style={{ padding: "6px 12px", fontSize: 11, fontWeight: 700,
                           background: "var(--brand-primary)", color: "var(--brand-on-primary)",
                           border: "1px solid var(--brand-primary)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>Open PM Dashboard</Link>
            <Link to="/shop/pm/templates" data-testid="shop-hub-v2-pm-templates-link"
                  style={{ padding: "6px 12px", fontSize: 11, fontWeight: 600,
                           background: "var(--paper-card)", color: "var(--ink-strong)",
                           border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>Manage PM Templates</Link>
            <Link to="/shop/pm/schedules" data-testid="shop-hub-v2-pm-schedules-link"
                  style={{ padding: "6px 12px", fontSize: 11, fontWeight: 600,
                           background: "var(--paper-card)", color: "var(--ink-strong)",
                           border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
                           textDecoration: "none" }}>Manage PM Schedules</Link>
          </div>
        </section>

        {/* 05 · Parts + Waiting — live rollup card replaces the prior
            dashed placeholder. Source: /api/shop/parts/on-order/summary. */}
        <section data-testid="shop-hub-v2-section-parts" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="05 · Parts and waiting"
            title="What's blocked on parts"
            caption="Total parts on order, units waiting, expected today, and overdue items."
          />
          <PartsOnOrderCard />
        </section>

        {/* 05 · Fuel / Service — primary entry points for fuel/lube and
            service-truck workflows. */}
        <section data-testid="shop-hub-v2-section-fuel-service" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="06 · Fuel and service"
            title="Fuel · fluids · service-truck accountability"
            caption="Submit visits · review records · close service-truck days · acknowledge variance."
          />
          <div data-testid="shop-hub-v2-fuel-service-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            <HubCard to="/shop/fuel-lube/new" testid="shop-hub-v2-action-fuel-lube-new"
                     title="New Fuel / Lube Visit"
                     body="One job · many equipment lines. Issues create shop defects automatically." />
            <HubCard to="/shop/fuel-lube" testid="shop-hub-v2-action-fuel-lube-records"
                     title="Fuel / Lube Records"
                     body="Submitted visits archive · filter by date · project · truck · tech · unit · issue." />
            <HubCard to="/shop/service-truck-reconciliation/new" testid="shop-hub-v2-action-strr-new"
                     title="Service Truck — Start / Close Day"
                     body="Log start-of-day quantities · close day to compute variance from real fuel/lube visits." />
            <HubCard to="/shop/service-truck-reconciliation" testid="shop-hub-v2-action-strr-records"
                     title="Reconciliation Records"
                     body="Truck-day variance archive · within expected range · needs review · significant variance." />
          </div>
        </section>

        {/* 06 · Unit Intelligence — drill into a single unit. Future Global
            Unit Search slot is reserved but NOT fake — only an inert
            placeholder until Track 13.30C provides the search backend. */}
        <section data-testid="shop-hub-v2-section-unit-intel" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="07 · Unit intelligence"
            title="Find a unit · open its full story"
            caption="One unit · one timeline. Pre-Ops · DVIRs · defects · repairs · parts · fuel · RTS."
          />
          <div data-testid="shop-hub-v2-unit-intel-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            <HubCard to="/shop/units/history" testid="shop-hub-v2-unit-history"
                     title="Unit History"
                     body="Type a unit number to load its complete operational story." />
            <HubCard to="/shop/fleet?focus_filter=defects" testid="shop-hub-v2-unit-defect-history"
                     title="Defect / Inspection History"
                     body="Full defect feed across the fleet." />
            <div data-testid="shop-hub-v2-unit-search-inline-slot" style={{
              padding: "var(--pad-card)", background: "var(--paper-card)",
              border: "1px solid var(--border-bold)", borderRadius: "var(--radius-card)",
            }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--ink-strong)", marginBottom: 6 }}>
                Quick unit search
              </div>
              <UnitSearchComponent inline />
            </div>
          </div>
        </section>

        {/* 07 · Records — archival surfaces; sit below active work. */}
        <section data-testid="shop-hub-v2-section-records" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="08 · Records"
            title="Archive · audits · history"
            caption="Pre-Ops · Truck DVIRs · Fuel/Lube · Reconciliations. Honest empty states · no fake exports."
          />
          <div data-testid="shop-hub-v2-records-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            <HubCard to="/shop/equipment" testid="shop-hub-v2-record-preops"
                     title="Equipment Pre-Ops" body="Pre-operation inspection list." />
            <HubCard to="/shop/fleet" testid="shop-hub-v2-record-dvirs"
                     title="Truck DVIRs · Fleet Visibility" body="Per-unit DVIR and defect state." />
            <HubCard to="/shop/fleet?focus_filter=defects" testid="shop-hub-v2-record-defects"
                     title="Defect / Inspection History" body="Full defect feed across the fleet." />
            <HubCard to="/shop/fuel-lube" testid="shop-hub-v2-record-fuel-lube"
                     title="Fuel / Lube Visit Records" body="Submitted visits archive." />
            <HubCard to="/shop/service-truck-reconciliation" testid="shop-hub-v2-record-strr"
                     title="Reconciliation Records" body="Truck-day variance archive." />
            <HubCard to="/shop/fleet?focus_filter=rts_pending" testid="shop-hub-v2-record-rts-7d"
                     title="Returned to Service · last 7 days"
                     body="Units verified safe-to-use and released in the last week."
                     metric={num(s.returned_to_service_7d)} status={tone(s.returned_to_service_7d)} />
          </div>
        </section>

        {/* 08 · Map — secondary lens, lowest priority. */}
        <ShopRecoveryMap />

        {/* 09 · Asset Administrator · Historical Records (Track 19.25 · nav-only).
              Only functionally usable by shop users flagged `is_asset_admin`;
              the backend gate enforces this even if others click through.
              Track 19.28 · P0-3 · Visibility polish — hidden entirely from
              non-asset-admin shop users to avoid "click and blocked" UX. */}
        {isAssetAdmin && (
        <section data-testid="shop-hub-v2-section-asset-records" style={{ marginBottom: 28 }}>
          <SectionHeader
            kicker="09 · Asset Administrator · Historical Records"
            title="Upload · classify · approve"
            caption="PPE, tools, phones/tablets/iPads, survey equipment, laser units, replacements. Manual only — no OCR."
          />
          <div data-testid="shop-hub-v2-asset-records-grid"
               style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            <HubCard to="/hr/historical-records/intake" testid="shop-hub-v2-asset-intake"
                     title="Asset Records Intake"
                     body="Upload a signed acknowledgement, PPE / tool issue slip, or replacement doc." />
            <HubCard to="/hr/historical-records/queue" testid="shop-hub-v2-asset-queue"
                     title="Asset Records Queue"
                     body="Approve, reject, or reassign staged Asset-lane records." />
            <HubCard to="/hr/historical-records/batches" testid="shop-hub-v2-asset-batches"
                     title="Bulk Historical Intake"
                     body="Many files · one session · one lane · single classify pass." />
          </div>
        </section>
        )}

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
          <strong style={{ color: "var(--ink-strong)" }}>Repair complete still requires RTS verification.</strong>{" "}
          Shop completes repairs and parts capture; Dispatch verifies and clears units back to service. Legacy hub remains at /shop/hub_legacy if needed.
        </div>
      </PortalShell>
    </div>
  );
}
