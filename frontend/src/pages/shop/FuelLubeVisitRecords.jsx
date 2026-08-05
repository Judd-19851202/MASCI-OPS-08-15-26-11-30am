// Track 13.29 Phase 2 — Fuel/Lube Visit Records (list).
// Route: /shop/fuel-lube (RequireShop). Backend: GET /api/shop/fuel-lube/visits.
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card, EmptyState } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;
const RANGES = [
  { id: "today", label: "Today", days: 0 },
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
async function api(path) {
  const r = await fetch(`${API}${path}`, { headers: authHeaders() });
  const body = await r.json().catch(() => null);
  if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
  return body;
}
function rangeIso(preset) {
  const today = new Date();
  const to = today.toISOString().slice(0, 10);
  const days = (RANGES.find((r) => r.id === preset) || RANGES[2]).days;
  const from = new Date(today); from.setDate(today.getDate() - days);
  return { from: from.toISOString().slice(0, 10), to };
}
function fmt(n) { return (n == null ? "—" : Number(n).toFixed(1)); }

export default function FuelLubeVisitRecords() {
  const { t } = useT();
  const [preset, setPreset] = useState("30");
  const [filters, setFilters] = useState({
    doc_id: "",
    project_number: "", fuel_lube_truck_unit: "", fuel_lube_tech_id: "",
    unit_number: "", has_issue: "", fuel_type: "",
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
      setData(await api(`/api/shop/fuel-lube/visits?${params}`));
    } catch (e) { setError(e.message || "Failed to load."); }
    setLoading(false);
  }, [dates.from, dates.to, filters]);

  useEffect(() => { load(); }, [load]);

  const visits = (data && data.visits) || [];

  return (
    <div data-testid="fuel-lube-records-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI" portalRole="Shop Portal · Fuel/Lube Records"
        pageTitle="Fuel / Lube Visit Records"
        subtitle="Submitted job-based service visits with fuel, fluids, grease, meter readings, and field-discovered issues."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <BackToShopLink testId="fuel-lube-records-back-to-shop" />
            <Link to="/shop/fuel-lube/new" data-testid="fuel-lube-records-new"
                  style={{ padding: "6px 12px", fontSize: 12, background: "var(--brand-primary,#1b4965)", color: "#fff", textDecoration: "none", borderRadius: 4 }}>
              + New visit
            </Link>
          </div>
        }
      >
        <div data-testid="fuel-lube-records-filter-strip" style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12, alignItems: "center" }}>
          {RANGES.map((r) => (
            <button key={r.id} data-testid={`fuel-lube-records-range-${r.id}`} type="button" onClick={() => setPreset(r.id)}
              style={{ padding: "5px 10px", fontSize: 11, fontWeight: 700,
                background: preset === r.id ? "var(--brand-primary,#1b4965)" : "#ddd",
                color: preset === r.id ? "#fff" : "#222", border: "none", borderRadius: 4 }}>{r.label}</button>
          ))}
          <span style={{ fontSize: 11, color: "#666" }}>{dates.from} → {dates.to}</span>
          <span style={{ flex: 1 }} />
          <button data-testid="fuel-lube-records-refresh" type="button" onClick={load} disabled={loading}
            style={{ padding: "5px 10px", fontSize: 11 }}>{loading ? "…" : "Refresh"}</button>
        </div>

        <div data-testid="fuel-lube-records-filters-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(160px,1fr))", gap: 6, marginBottom: 12 }}>
          <input data-testid="fuel-lube-records-filter-doc-id" placeholder="Visit #" value={filters.doc_id} onChange={(e) => setFilters({ ...filters, doc_id: e.target.value.toUpperCase() })} style={{ padding: 5, fontSize: 12 }} />
          <input data-testid="fuel-lube-records-filter-project" placeholder="Project #" value={filters.project_number} onChange={(e) => setFilters({ ...filters, project_number: e.target.value })} style={{ padding: 5, fontSize: 12 }} />
          <input data-testid="fuel-lube-records-filter-truck" placeholder="Fuel/Lube truck" value={filters.fuel_lube_truck_unit} onChange={(e) => setFilters({ ...filters, fuel_lube_truck_unit: e.target.value })} style={{ padding: 5, fontSize: 12 }} />
          <input data-testid="fuel-lube-records-filter-tech" placeholder="Tech employee id" value={filters.fuel_lube_tech_id} onChange={(e) => setFilters({ ...filters, fuel_lube_tech_id: e.target.value })} style={{ padding: 5, fontSize: 12 }} />
          <input data-testid="fuel-lube-records-filter-unit" placeholder="Unit serviced" value={filters.unit_number} onChange={(e) => setFilters({ ...filters, unit_number: e.target.value })} style={{ padding: 5, fontSize: 12 }} />
          <select data-testid="fuel-lube-records-filter-has-issue" value={filters.has_issue} onChange={(e) => setFilters({ ...filters, has_issue: e.target.value })} style={{ padding: 5, fontSize: 12 }}>
            <option value="">Any issue status</option>
            <option value="true">Only with issues</option>
            <option value="false">Only no-issue</option>
          </select>
          <select data-testid="fuel-lube-records-filter-fuel-type" value={filters.fuel_type} onChange={(e) => setFilters({ ...filters, fuel_type: e.target.value })} style={{ padding: 5, fontSize: 12 }}>
            <option value="">Any fuel type</option>
            <option value="red_diesel">Red diesel</option>
            <option value="clear_diesel">Clear diesel</option>
            <option value="gasoline">Gasoline</option>
            <option value="def">DEF</option>
          </select>
        </div>

        {error && (
          <div data-testid="fuel-lube-records-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, color: "#a33", fontSize: 12, marginBottom: 12 }}>
            Fuel/lube visit records unavailable. No data invented. · {error}
          </div>
        )}

        {data && (
          <div data-testid="fuel-lube-records-count-strip" style={{ fontSize: 12, color: "#555", marginBottom: 10 }}>
            <strong data-testid="fuel-lube-records-count">{data.count}</strong> visit{data.count === 1 ? "" : "s"} ({dates.from} → {dates.to})
          </div>
        )}

        {loading && !data && (<div data-testid="fuel-lube-records-loading" style={{ fontSize: 12, color: "#666" }}>Loading…</div>)}

        {data && visits.length === 0 && !error && (
          <EmptyState data-testid="fuel-lube-records-empty"
            kicker="No visits in scope"
            title="No fuel/lube visits found for this range."
            body="Adjust the date range or filters. No placeholder rows will be invented." />
        )}

        {visits.length > 0 && (
          <div data-testid="fuel-lube-records-list" style={{ display: "grid", gap: 8 }}>
            {visits.map((v) => {
              const t = v.totals || {};
              return (
                <Link key={v.id} to={`/shop/fuel-lube/${v.id}`} data-testid={`fuel-lube-records-row-${v.id}`}
                      style={{ textDecoration: "none", color: "inherit" }}>
                  <Card>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 700 }}>
                          <span className="font-mono" style={{ marginRight: 8 }}>{v.doc_id || v.id}</span>
                          {v.visit_date} · Project <strong>{v.project_number || "—"}</strong>{v.project_name ? ` (${v.project_name})` : ""}
                          {(v.issues_found_count || 0) > 0 && (
                            <span data-testid={`fuel-lube-records-issue-flag-${v.id}`} style={{ marginLeft: 8, padding: "1px 6px", fontSize: 10, background: "#fae2e0", color: "#a33", borderRadius: 3, fontWeight: 700 }}>
                              {v.issues_found_count} ISSUE{v.issues_found_count === 1 ? "" : "S"}
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
                          Truck <strong>{v.fuel_lube_truck_unit || "—"}</strong> · Tech <strong>{v.fuel_lube_tech_name || "—"}</strong> ·
                          submitted {v.submitted_at ? formatPlatformTime(v.submitted_at) : "—"}
                        </div>
                        <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
                          Units serviced: <strong>{t.units_serviced ?? "—"}</strong> · Greased: {t.greased_count ?? 0} ·
                          Red diesel {fmt(t.red_diesel_gallons)} gal · Clear diesel {fmt(t.clear_diesel_gallons)} gal ·
                          Gasoline {fmt(t.gasoline_gallons)} gal · DEF {fmt(t.def_gallons)} gal
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}

        <div data-testid="fuel-lube-records-doctrine" style={{ marginTop: 24, padding: 12, fontSize: 11, color: "#666",
          background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4 }}>
          Submitted visits archive. Issues you flagged here become shop defects automatically.
          Each service entry is also saved to the unit&apos;s history.
        </div>
      </PortalShell>
    </div>
  );
}
