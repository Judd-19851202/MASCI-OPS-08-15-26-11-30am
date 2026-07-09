// Track 13.29 Phase 2 — Fuel/Lube Visit detail.
// Route: /shop/fuel-lube/:visitId (RequireShop). Backend: GET /api/shop/fuel-lube/visits/{id}.
import React, { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const API = process.env.REACT_APP_BACKEND_URL;
function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken(); const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}
function fmt(n) { return (n == null ? "—" : Number(n).toFixed(1)); }

export default function FuelLubeVisitDetail() {
  const { visitId } = useParams();
  const [visit, setVisit] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const r = await fetch(`${API}/api/shop/fuel-lube/visits/${encodeURIComponent(visitId)}`, { headers: authHeaders() });
      const body = await r.json().catch(() => null);
      if (!r.ok) throw new Error((body && body.detail) || `HTTP ${r.status}`);
      setVisit(body);
    } catch (e) { setError(e.message || "Failed to load."); }
  }, [visitId]);

  useEffect(() => { load(); }, [load]);

  const t = (visit && visit.totals) || {};
  const lines = (visit && visit.equipment_lines) || [];
  const defectIds = (visit && visit.defect_ids) || [];

  return (
    <div data-testid="fuel-lube-detail-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI" portalRole="Shop Portal · Fuel/Lube Visit"
        pageTitle={`Visit ${visitId}`}
        subtitle="Submitted Fuel/Lube Visit Record · totals · per-equipment lines · issues · defect linkage."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <BackToShopLink testId="fuel-lube-detail-back-to-shop" />
            <Link to="/shop/fuel-lube" data-testid="fuel-lube-detail-back" style={{ padding: "6px 12px", fontSize: 12, background: "#eee", color: "#222", textDecoration: "none", borderRadius: 4 }}>← Records</Link>
            <button data-testid="fuel-lube-detail-print" type="button" onClick={() => window.print()} style={{ padding: "6px 12px", fontSize: 12 }}>Print</button>
          </div>
        }
      >
        {error && (
          <div data-testid="fuel-lube-detail-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, color: "#a33", fontSize: 12, marginBottom: 12 }}>
            Fuel/lube visit unavailable. No data invented. · {error}
          </div>
        )}
        {!visit && !error && (<div data-testid="fuel-lube-detail-loading" style={{ fontSize: 12, color: "#666" }}>Loading…</div>)}

        {visit && (
          <>
            <Card data-testid="fuel-lube-detail-header">
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8, fontSize: 12 }}>
                <div>Date: <strong>{visit.visit_date}</strong></div>
                <div>Project: <strong>{visit.project_number || "—"}</strong>{visit.project_name ? ` · ${visit.project_name}` : ""}</div>
                <div>Truck: <strong>{visit.fuel_lube_truck_unit || "—"}</strong></div>
                <div>Tech: <strong>{visit.fuel_lube_tech_name || "—"}</strong>{visit.fuel_lube_tech_id ? ` (${visit.fuel_lube_tech_id})` : ""}</div>
                <div>Arrival → Departure: <strong>{visit.arrival_time || "—"}</strong> → <strong>{visit.departure_time || "—"}</strong></div>
                <div>Location source: <strong>{visit.location_source || "—"}</strong></div>
                <div>Submitted by: <strong>{visit.submitted_by || "—"}</strong></div>
                <div>Submitted at: <strong>{visit.submitted_at ? formatPlatformTime(visit.submitted_at) : "—"}</strong></div>
                <div>Status: <strong>{visit.status || "—"}</strong></div>
              </div>
            </Card>

            <Card data-testid="fuel-lube-detail-totals" style={{ marginTop: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>Totals</div>
              <div data-testid="fuel-lube-detail-totals-grid" style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 6, fontSize: 12 }}>
                <div>Red diesel · {fmt(t.red_diesel_gallons)} gal</div>
                <div>Clear diesel · {fmt(t.clear_diesel_gallons)} gal</div>
                <div>Gasoline · {fmt(t.gasoline_gallons)} gal</div>
                <div>DEF · {fmt(t.def_gallons)} gal</div>
                <div>Engine oil · {fmt(t.engine_oil_quarts)} qt</div>
                <div>Hyd oil · {fmt(t.hydraulic_oil_quarts)} qt</div>
                <div>Coolant · {fmt(t.coolant_quarts)} qt</div>
                <div>Trans fluid · {fmt(t.transmission_fluid_quarts)} qt</div>
                <div>Gear oil · {fmt(t.gear_oil_quarts)} qt</div>
                <div>Units serviced · {t.units_serviced ?? "—"}</div>
                <div>Greased · {t.greased_count ?? 0}</div>
                <div style={{ color: (t.issues_found_count || 0) > 0 ? "#a33" : "#666", fontWeight: 700 }}>Issues found · {t.issues_found_count ?? 0}</div>
              </div>
            </Card>

            <h3 style={{ marginTop: 16, fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em", color: "#666" }}>Equipment lines ({lines.length})</h3>
            <div style={{ display: "grid", gap: 8 }}>
              {lines.map((l, i) => (
                <Card key={i} data-testid={`fuel-lube-detail-line-${i}`}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
                    <div style={{ fontSize: 13, fontWeight: 700 }}>
                      Unit <strong>{l.unit_number}</strong>{l.equipment_name ? ` · ${l.equipment_name}` : ""}
                      {l.issue_found && (
                        <span data-testid={`fuel-lube-detail-line-issue-flag-${i}`} style={{ marginLeft: 8, padding: "1px 6px", fontSize: 10, background: "#fae2e0", color: "#a33", borderRadius: 3, fontWeight: 700 }}>
                          ISSUE · {l.issue_severity || "—"}
                        </span>
                      )}
                    </div>
                    <Link to={`/shop/units/${encodeURIComponent(l.unit_number)}/history`}
                          data-testid={`fuel-lube-detail-line-unit-history-${i}`}
                          style={{ fontSize: 11, color: "var(--brand-primary,#1b4965)", textDecoration: "none" }}>
                      View Unit History →
                    </Link>
                  </div>
                  <div style={{ fontSize: 11, color: "#555", marginTop: 4 }}>
                    Meter hours: <strong>{l.meter_hours ?? "—"}</strong> · Odometer: <strong>{l.odometer_miles ?? "—"}</strong> ·
                    Greased: <strong>{l.greased ? "yes" : "no"}</strong>{!l.greased && l.not_greased_reason ? ` (${l.not_greased_reason})` : ""}
                  </div>
                  <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
                    Red diesel {fmt(l.red_diesel_gallons)} · Clear diesel {fmt(l.clear_diesel_gallons)} · Gas {fmt(l.gasoline_gallons)} · DEF {fmt(l.def_gallons)} ·
                    Engine oil {fmt(l.engine_oil_quarts)} · Hyd {fmt(l.hydraulic_oil_quarts)} · Coolant {fmt(l.coolant_quarts)} · Trans {fmt(l.transmission_fluid_quarts)} · Gear {fmt(l.gear_oil_quarts)}
                  </div>
                  {l.line_notes && (<div style={{ fontSize: 11, color: "#222", marginTop: 4 }}>Notes: {l.line_notes}</div>)}
                  {l.issue_found && (
                    <div style={{ marginTop: 6, padding: 8, background: "#fdf3f0", borderRadius: 4 }}>
                      <div style={{ fontSize: 11, fontWeight: 700 }}>Issue · {l.issue_category || "—"} · {l.issue_severity || "—"}</div>
                      <div style={{ fontSize: 12, marginTop: 2 }}>{l.issue_description || "—"}</div>
                      {(l.issue_photo_ids || []).length > 0 && (
                        <div style={{ fontSize: 10, color: "#666", marginTop: 4 }}>
                          Photo attachments: {(l.issue_photo_ids || []).join(", ")}
                        </div>
                      )}
                      <div style={{ fontSize: 11, color: "#555", marginTop: 4 }}>
                        Sent to the shop defect queue. Visible in <Link data-testid={`fuel-lube-detail-line-mgr-queue-link-${i}`} to="/shop/manager/queue">Shop Manager Queue</Link>.
                      </div>
                    </div>
                  )}
                </Card>
              ))}
            </div>

            {defectIds.length > 0 && (
              <div data-testid="fuel-lube-detail-defect-ids" style={{ marginTop: 12, fontSize: 11, color: "#555" }}>
                Defect records created: {defectIds.map((id) => <code key={id} style={{ marginRight: 6 }}>{id}</code>)}
              </div>
            )}

            <div data-testid="fuel-lube-detail-doctrine" style={{ marginTop: 24, padding: 12, fontSize: 11, color: "#666",
              background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4 }}>
              Each service entry is saved to the unit&apos;s history. Issues flow to the shop defect queue.
              Print uses the browser&apos;s native dialog. PDF / email / CSV exports are not enabled here.
            </div>
          </>
        )}
      </PortalShell>
    </div>
  );
}
