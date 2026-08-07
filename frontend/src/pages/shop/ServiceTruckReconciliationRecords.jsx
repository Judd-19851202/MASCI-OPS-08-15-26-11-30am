// Track 13.30 — Service Truck Daily Reconciliation · list.
// Route: /shop/service-truck-reconciliation (RequireShop).
// Endpoint: GET /api/shop/service-truck-reconciliation.
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card, EmptyState } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;
const RANGES = [
  { id: "today", label: "Today",     days: 0 },
  { id: "7",     label: "Last 7 days", days: 7 },
  { id: "30",    label: "Last 30 days (default)", days: 30 },
  { id: "90",    label: "Last 90 days (max)", days: 90 },
];

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}
function rangeIso(preset) {
  const today = new Date();
  const to = today.toISOString().slice(0, 10);
  const days = (RANGES.find((r) => r.id === preset) || RANGES[2]).days;
  const from = new Date(today); from.setDate(today.getDate() - days);
  return { from: from.toISOString().slice(0, 10), to };
}
function StatusChip({ status }) {
  const map = {
    green:      { bg: "#d4edda", fg: "#155724", label: "Within expected range" },
    yellow:     { bg: "#fff3cd", fg: "#856404", label: "Needs review" },
    red:        { bg: "#f8d7da", fg: "#721c24", label: "Significant variance" },
    incomplete: { bg: "#e2e3e5", fg: "#383d41", label: "Incomplete" },
  };
  const s = map[status] || { bg: "#eee", fg: "#222", label: status || "—" };
  return (
    <span data-testid={`strr-list-chip-${status || "unknown"}`}
          style={{ padding: "1px 6px", borderRadius: 3, background: s.bg, color: s.fg, fontSize: 10, fontWeight: 700 }}>
      {s.label.toUpperCase()}
    </span>
  );
}
function fmt(n) { return (n == null ? "—" : Number(n).toFixed(1)); }

export default function ServiceTruckReconciliationRecords() {
  const [preset, setPreset] = useState("30");
  const [filters, setFilters] = useState({
    doc_id: "",
    service_truck_unit: "", tech_id: "", variance_status: "", status: "",
  });
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const dates = useMemo(() => rangeIso(preset), [preset]);

  const load = useCallback(async () => {
    setError(""); setLoading(true);
    try {
      const params = new URLSearchParams({ from: dates.from, to: dates.to, limit: "200" });
      for (const [k, v] of Object.entries(filters)) {
        if (v !== "" && v !== null && v !== undefined) params.set(k, String(v));
      }
      const r = await fetch(`${API}/api/shop/service-truck-reconciliation?${params}`, { headers: authHeaders() });
      const body = await r.json().catch(() => null);
      if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
      setData(body);
    } catch (e) { setError(e.message || "Failed to load."); }
    setLoading(false);
  }, [dates.from, dates.to, filters]);

  useEffect(() => { load(); }, [load]);

  const rows = (data && data.reconciliations) || [];

  return (
    <div data-testid="strr-list-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI" portalRole="Shop Portal · Service Truck Daily Check"
        pageTitle="Service Truck Daily Check Records"
        subtitle="Start-of-day · dispensed (from Fuel/Lube Visits) · end-of-day · variance · status."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <BackToShopLink testId="strr-list-back-to-shop" />
            <Link to="/shop/service-truck-reconciliation/new" data-testid="strr-list-new"
                  style={{ padding: "6px 12px", fontSize: 12, background: "var(--brand-primary,#1b4965)", color: "#fff", textDecoration: "none", borderRadius: 4 }}>
              + Start / Close day
            </Link>
          </div>
        }
      >
        <div data-testid="strr-list-filter-strip" style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12, alignItems: "center" }}>
          {RANGES.map((r) => (
            <button key={r.id} data-testid={`strr-list-range-${r.id}`} type="button" onClick={() => setPreset(r.id)}
              style={{ padding: "5px 10px", fontSize: 11, fontWeight: 700,
                background: preset === r.id ? "var(--brand-primary,#1b4965)" : "#ddd",
                color: preset === r.id ? "#fff" : "#222", border: "none", borderRadius: 4 }}>{r.label}</button>
          ))}
          <span style={{ fontSize: 11, color: "#666" }}>{dates.from} → {dates.to}</span>
          <span style={{ flex: 1 }} />
          <button data-testid="strr-list-refresh" type="button" onClick={load} disabled={loading}
            style={{ padding: "5px 10px", fontSize: 11 }}>{loading ? "…" : "Refresh"}</button>
        </div>

        <div data-testid="strr-list-filters-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 6, marginBottom: 12 }}>
          <input data-testid="strr-list-filter-doc-id" placeholder="Daily check #" value={filters.doc_id}
                 onChange={(e) => setFilters({ ...filters, doc_id: e.target.value.toUpperCase() })} style={{ padding: 5, fontSize: 12 }} />
          <input data-testid="strr-list-filter-truck" placeholder="Service truck unit" value={filters.service_truck_unit}
                 onChange={(e) => setFilters({ ...filters, service_truck_unit: e.target.value })} style={{ padding: 5, fontSize: 12 }} />
          <input data-testid="strr-list-filter-tech" placeholder="Tech employee id" value={filters.tech_id}
                 onChange={(e) => setFilters({ ...filters, tech_id: e.target.value })} style={{ padding: 5, fontSize: 12 }} />
          <select data-testid="strr-list-filter-variance" value={filters.variance_status}
                  onChange={(e) => setFilters({ ...filters, variance_status: e.target.value })} style={{ padding: 5, fontSize: 12 }}>
            <option value="">Any variance status</option>
            <option value="green">Within expected range</option>
            <option value="yellow">Needs review</option>
            <option value="red">Significant variance</option>
            <option value="incomplete">Incomplete</option>
          </select>
          <select data-testid="strr-list-filter-status" value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })} style={{ padding: 5, fontSize: 12 }}>
            <option value="">Any record status</option>
            <option value="start_logged">Start logged</option>
            <option value="closed">Closed</option>
            <option value="needs_review">Needs review</option>
          </select>
        </div>

        {error && (
          <div data-testid="strr-list-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, color: "#a33", fontSize: 12, marginBottom: 12 }}>
            Service truck daily check records unavailable. No data invented. · {error}
          </div>
        )}

        {data && (
          <div data-testid="strr-list-count-strip" style={{ fontSize: 12, color: "#555", marginBottom: 10 }}>
            <strong data-testid="strr-list-count">{data.count}</strong> daily check{data.count === 1 ? "" : "s"} ({dates.from} → {dates.to})
          </div>
        )}

        {loading && !data && (<div data-testid="strr-list-loading" style={{ fontSize: 12, color: "#666" }}>Loading…</div>)}

        {data && rows.length === 0 && !error && (
          <EmptyState data-testid="strr-list-empty"
            kicker="No daily checks in scope"
            title="No service truck daily checks found for this range."
            body="Adjust the date range or filters. No placeholder rows will be invented." />
        )}

        {rows.length > 0 && (
          <div data-testid="strr-list-rows" style={{ display: "grid", gap: 8 }}>
            {rows.map((row) => {
              const v = (row.variance && row.variance.rows) || [];
              const fuelLine = (key) => {
                const r = v.find((x) => x.field === key);
                return r ? `Δ${r.variance} ${r.unit}` : "—";
              };
              return (
                <Link key={row.id} to={`/shop/service-truck-reconciliation/${row.id}`} data-testid={`strr-list-row-${row.id}`}
                      style={{ textDecoration: "none", color: "inherit" }}>
                  <Card>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 700 }}>
                          <span className="font-mono" style={{ marginRight: 8 }}>{row.doc_id || row.id}</span>
                          {row.date} · Truck <strong>{row.service_truck_unit}</strong>
                          <span style={{ marginLeft: 8 }}><StatusChip status={row.variance_status} /></span>
                          <span style={{ marginLeft: 6, padding: "1px 6px", borderRadius: 3, background: "#eee", color: "#222", fontSize: 10, fontWeight: 700 }}>
                            {(row.status || "").replace("_", " ").toUpperCase()}
                          </span>
                        </div>
                        <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
                          Tech <strong>{row.tech_name || "—"}</strong> · visits {row.dispensed_quantities?.visit_count ?? 0} ·
                          start submitted {row.start_submitted_at ? formatPlatformTime(row.start_submitted_at) : "—"} ·
                          end submitted {row.end_submitted_at ? formatPlatformTime(row.end_submitted_at) : "—"}
                        </div>
                        <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
                          Red diesel {fuelLine("red_diesel_gallons")} · Clear diesel {fuelLine("clear_diesel_gallons")} ·
                          Gasoline {fuelLine("gasoline_gallons")} · DEF {fuelLine("def_gallons")} ·
                          Eng oil {fuelLine("engine_oil_quarts")} · Hyd {fuelLine("hydraulic_oil_quarts")}
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}

        <div data-testid="strr-list-doctrine" style={{ marginTop: 24, padding: 12, fontSize: 11, color: "#666",
              background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4 }}>
          Dispensed totals come from submitted Fuel/Lube Visits. No accounting · no cost · no fuel tax · no disciplinary language.
        </div>
      </PortalShell>
    </div>
  );
}
