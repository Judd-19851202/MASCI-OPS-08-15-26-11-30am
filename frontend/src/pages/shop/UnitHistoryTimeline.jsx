// Track 13.27 — Unit History Timeline page.
//
// MOUNTED AT: /shop/units/:unitNumber/history (behind RequireShop).
// Consumes: GET /api/assets/{unit_number}/timeline (Track 13.26 Asset
// Service Event Backbone).
//
// Doctrine reminders honored:
//   - Repair Complete ≠ RTS  (chip language explicit).
//   - No fake events / no fabricated MaintainX or Fuel/Lube.
//   - Single source of truth: the backbone IS the timeline.
//   - No second history system.
//
// References:
//   /app/memory/TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md
//   /app/memory/TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md
//   /app/memory/TRACK_13_28_MECHANIC_ASSIGNMENT_WORKFLOW.md
//   /app/memory/TRACK_13_28_PHASE_2_SHOP_WORKFORCE_UI_PARTS_CAPTURE.md
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getShopToken } from "@/lib/shopAuth";
import { PortalShell, Card, EmptyState } from "../../design-system";
import BackToShopLink from "@/components/shop/BackToShopLink";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const s = getShopToken();
  if (a) h["X-Admin-Token"] = a;
  if (s) h["X-Shop-Token"] = s;
  return h;
}

async function api(path) {
  const r = await fetch(`${API}${path}`, { headers: authHeaders() });
  const body = await r.json().catch(() => null);
  if (!r.ok) {
    const detail = (body && body.detail) || `HTTP ${r.status}`;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return body;
}

// ── Calm, source-honest labels per event_type/subtype ──────────────────
const EVENT_LABEL = {
  "preop|submitted": "Pre-Op Submitted",
  "preop|failed": "Pre-Op Needs Review",
  "dvir|submitted": "DVIR Submitted",
  "dvir|failed": "DVIR Needs Review",
  "defect|opened": "Defect Opened",
  "defect|assigned": "Repair Assigned",
  "defect|accepted": "Mechanic Accepted",
  "defect|acknowledged": "Defect Acknowledged",
  "repair|started": "Repair Started",
  "repair|completed": "Repair Complete",
  "repair|manager_reviewed": "Manager Reviewed",
  "oos|preop": "Unit Out Of Service · Pre-Op",
  "oos|dvir": "Unit Out Of Service · DVIR",
  "oos|manual_oos": "Unit Out Of Service · Dispatch",
  "rts|verified": "Returned To Service",
  "inspection|shop_signed_off": "Shop Signed Off",
  "material|cycle": "Haul Cycle",
  "presence": "Motive Presence",
  "transfer|transfer": "Asset Transferred",
  "transfer|retire": "Asset Retired",
  "transfer|activate": "Asset Activated",
};

const TYPE_TONE = {
  preop:      { tone: "#357", icon: "P" },
  dvir:       { tone: "#357", icon: "D" },
  defect:     { tone: "#c47", icon: "!" },
  oos:        { tone: "#a33", icon: "×" },
  repair:     { tone: "#258", icon: "↻" },
  rts:        { tone: "#137a48", icon: "✓" },
  inspection: { tone: "#357", icon: "I" },
  material:   { tone: "#a86", icon: "↑" },
  presence:   { tone: "#888", icon: "•" },
  transfer:   { tone: "#666", icon: "→" },
  attachment: { tone: "#666", icon: "@" },
  note:       { tone: "#666", icon: "·" },
};

function chipForEvent(ev) {
  const key = `${ev.event_type}|${ev.event_subtype || ""}`;
  const fallback = ev.event_subtype
    ? `${ev.event_type} · ${ev.event_subtype}`
    : ev.event_type;
  return EVENT_LABEL[key] || EVENT_LABEL[ev.event_type] || fallback;
}

function formatTs(iso) {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function PartsBlock({ partsUsed = [], partsOnOrder = [] }) {
  if (partsUsed.length === 0 && partsOnOrder.length === 0) return null;
  return (
    <div data-testid="unit-history-parts-block" style={{ marginTop: 8, padding: 8, background: "#f4f6f8", borderRadius: 4 }}>
      {partsUsed.length > 0 && (
        <div data-testid="unit-history-parts-used">
          <div style={{ fontSize: 11, fontWeight: 700, color: "#444", marginBottom: 4 }}>Parts used ({partsUsed.length})</div>
          <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "#666", textAlign: "left" }}>
                <th style={{ padding: 3 }}>Part</th>
                <th style={{ padding: 3 }}>Part #</th>
                <th style={{ padding: 3 }}>Manufacturer</th>
                <th style={{ padding: 3 }}>Supplier</th>
                <th style={{ padding: 3, textAlign: "right" }}>Qty</th>
                <th style={{ padding: 3 }}>Notes</th>
              </tr>
            </thead>
            <tbody>
              {partsUsed.map((p, i) => (
                <tr key={i} data-testid={`unit-history-part-used-row-${i}`} style={{ borderTop: "1px solid #e3e6ea" }}>
                  <td style={{ padding: 3 }}>{p.part_name || "—"}</td>
                  <td style={{ padding: 3 }}>{p.part_number || "—"}</td>
                  <td style={{ padding: 3 }}>{p.manufacturer || "—"}</td>
                  <td style={{ padding: 3 }}>{p.supplier || "—"}</td>
                  <td style={{ padding: 3, textAlign: "right" }}>{p.quantity ?? 1}</td>
                  <td style={{ padding: 3, color: "#666" }}>{p.notes || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {partsOnOrder.length > 0 && (
        <div data-testid="unit-history-parts-on-order" style={{ marginTop: 8 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: "#a86", marginBottom: 4 }}>Parts on order / waiting ({partsOnOrder.length})</div>
          <table style={{ width: "100%", fontSize: 11, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ color: "#666", textAlign: "left" }}>
                <th style={{ padding: 3 }}>Part</th>
                <th style={{ padding: 3 }}>Part #</th>
                <th style={{ padding: 3 }}>Manufacturer</th>
                <th style={{ padding: 3 }}>Supplier</th>
                <th style={{ padding: 3, textAlign: "right" }}>Qty</th>
                <th style={{ padding: 3 }}>Ordered</th>
                <th style={{ padding: 3 }}>Expected</th>
                <th style={{ padding: 3 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {partsOnOrder.map((p, i) => (
                <tr key={i} data-testid={`unit-history-part-order-row-${i}`} style={{ borderTop: "1px solid #e3e6ea" }}>
                  <td style={{ padding: 3 }}>{p.part_name || "—"}</td>
                  <td style={{ padding: 3 }}>{p.part_number || "—"}</td>
                  <td style={{ padding: 3 }}>{p.manufacturer || "—"}</td>
                  <td style={{ padding: 3 }}>{p.supplier || "—"}</td>
                  <td style={{ padding: 3, textAlign: "right" }}>{p.quantity ?? 1}</td>
                  <td style={{ padding: 3 }}>{p.ordered_date || "—"}</td>
                  <td style={{ padding: 3 }}>{p.expected_date || "—"}</td>
                  <td style={{ padding: 3 }}>{p.order_status || "open"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function EventCard({ ev }) {
  const t = TYPE_TONE[ev.event_type] || { tone: "#666", icon: "?" };
  const label = chipForEvent(ev);
  const partsUsed = ev.parts_used || [];
  const partsOnOrder = ev.parts_on_order || [];
  const relateds = [
    ev.related_defect_id ? `defect ${ev.related_defect_id.slice(-8)}` : null,
    ev.related_preop_id ? `pre-op ${ev.related_preop_id.slice(-8)}` : null,
    ev.related_dvir_id ? `DVIR ${ev.related_dvir_id.slice(-8)}` : null,
    ev.related_work_order_id ? `WO ${ev.related_work_order_id.slice(-8)}` : null,
    ev.related_attachment_id ? `attach ${ev.related_attachment_id.slice(-8)}` : null,
    ev.project_number ? `project ${ev.project_number}` : null,
  ].filter(Boolean);
  return (
    <Card data-testid={`unit-history-event-${ev.event_id}`}>
      <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
        <div style={{
          flex: "0 0 30px", width: 30, height: 30, borderRadius: 15,
          background: t.tone, color: "#fff",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 13, fontWeight: 700,
        }}>{t.icon}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
            <span data-testid={`unit-history-event-label-${ev.event_id}`} style={{ fontSize: 13, fontWeight: 700, color: t.tone }}>{label}</span>
            <span style={{ fontSize: 11, color: "#666", whiteSpace: "nowrap" }}>{formatTs(ev.timestamp)}</span>
          </div>
          <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
            {ev.actor_name && (<span>by <strong>{ev.actor_name}</strong>{ev.actor_role ? ` (${ev.actor_role})` : ""} · </span>)}
            source <code style={{ fontSize: 10, background: "#eef0f3", padding: "1px 4px", borderRadius: 3 }}>{ev.source_system}</code>
          </div>
          {(ev.status_before || ev.status_after) && (
            <div style={{ fontSize: 11, color: "#555", marginTop: 2 }}>
              status: <strong>{ev.status_before || "—"}</strong> → <strong>{ev.status_after || "—"}</strong>
              {(ev.availability_before || ev.availability_after) && (
                <> · availability: <strong>{ev.availability_before || "—"}</strong> → <strong>{ev.availability_after || "—"}</strong></>
              )}
            </div>
          )}
          {ev.notes && (
            <div style={{ fontSize: 12, color: "#222", marginTop: 4 }}>{ev.notes}</div>
          )}
          {relateds.length > 0 && (
            <div style={{ fontSize: 10, color: "#888", marginTop: 4 }}>
              {relateds.join(" · ")}
            </div>
          )}
          <PartsBlock partsUsed={partsUsed} partsOnOrder={partsOnOrder} />
        </div>
      </div>
    </Card>
  );
}

const RANGE_PRESETS = [
  { id: "30",  label: "Last 30 days", days: 30 },
  { id: "90",  label: "Last 90 days", days: 90 },  // backend max
  { id: "ytd", label: "This year (year-to-date)", days: null },  // computed
];

function rangeDates(presetId) {
  const today = new Date();
  const toIso = today.toISOString().slice(0, 10);
  const preset = RANGE_PRESETS.find((r) => r.id === presetId) || RANGE_PRESETS[1];
  if (preset.days != null) {
    const d = new Date(today);
    d.setDate(d.getDate() - preset.days);
    return { from: d.toISOString().slice(0, 10), to: toIso };
  }
  // YTD — cap at backend max 90 days.
  const yearStart = new Date(today.getFullYear(), 0, 1);
  const ninetyAgo = new Date(today); ninetyAgo.setDate(today.getDate() - 90);
  const start = yearStart > ninetyAgo ? yearStart : ninetyAgo;
  return { from: start.toISOString().slice(0, 10), to: toIso };
}

export default function UnitHistoryTimeline() {
  const params = useParams();
  const unitNumber = params.unitNumber || "";
  const [presetId, setPresetId] = useState("90");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const dates = useMemo(() => rangeDates(presetId), [presetId]);

  const load = useCallback(async () => {
    setError(""); setLoading(true);
    try {
      const params = new URLSearchParams({
        from: dates.from,
        to: dates.to,
        limit: "500",
      });
      if (eventTypeFilter) params.set("event_type", eventTypeFilter);
      if (sourceFilter) params.set("source_system", sourceFilter);
      const body = await api(`/api/assets/${encodeURIComponent(unitNumber)}/timeline?${params}`);
      setData(body);
    } catch (e) { setError(e.message || "Failed to load timeline."); }
    setLoading(false);
  }, [unitNumber, dates.from, dates.to, eventTypeFilter, sourceFilter]);

  useEffect(() => { if (unitNumber) load(); }, [load, unitNumber]);

  const availableEventTypes = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.counts.by_event_type || {})
      .filter(([, n]) => n > 0)
      .map(([k]) => k);
  }, [data]);

  const availableSources = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.counts.by_source_system || {})
      .filter(([, n]) => n > 0)
      .map(([k]) => k);
  }, [data]);

  return (
    <div data-testid="unit-history-timeline-root" style={{ background: "var(--paper-base)", minHeight: "100vh" }}>
      <PortalShell
        portalName="MASCI"
        portalRole="Shop Portal · Unit History"
        pageTitle={`Unit History · ${unitNumber || "(no unit)"}`}
        subtitle="Complete operational timeline for this asset — pre-ops, DVIRs, defects, repairs, fuel/lube, return-to-service."
        primaryActions={
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <BackToShopLink testId="unit-history-back-to-shop" />
            <Link
              to="/shop/units/history"
              data-testid="unit-history-back-to-selector"
              style={{ padding: "6px 12px", fontSize: 12, background: "#eee", color: "#222", textDecoration: "none", borderRadius: 4 }}
            >Pick different unit</Link>
            <button
              data-testid="unit-history-refresh"
              onClick={load}
              type="button"
              disabled={loading}
              style={{ padding: "6px 12px", fontSize: 12 }}
            >{loading ? "Loading…" : "Refresh"}</button>
          </div>
        }
      >
        {/* ── Filter strip ───────────────────────────────────────── */}
        <div data-testid="unit-history-filter-strip" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16, alignItems: "center" }}>
          {RANGE_PRESETS.map((r) => (
            <button
              key={r.id}
              data-testid={`unit-history-filter-range-${r.id}`}
              type="button"
              onClick={() => setPresetId(r.id)}
              style={{
                padding: "6px 10px", fontSize: 11, fontWeight: 700,
                background: presetId === r.id ? "var(--brand-primary, #1b4965)" : "#ddd",
                color: presetId === r.id ? "#fff" : "#222",
                border: "none", borderRadius: 4,
              }}
            >{r.label}</button>
          ))}
          <span style={{ fontSize: 11, color: "#666" }}>{dates.from} → {dates.to}</span>
          <span style={{ flex: 1 }} />
          <select
            data-testid="unit-history-filter-event-type"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            style={{ padding: 6, fontSize: 12 }}
          >
            <option value="">All event types</option>
            {availableEventTypes.map((t) => (
              <option key={t} value={t}>{`${t} · ${(data && data.counts.by_event_type[t]) || 0}`}</option>
            ))}
          </select>
          <select
            data-testid="unit-history-filter-source"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            style={{ padding: 6, fontSize: 12 }}
          >
            <option value="">All sources</option>
            {availableSources.map((s) => (
              <option key={s} value={s}>{`${s} · ${(data && data.counts.by_source_system[s]) || 0}`}</option>
            ))}
          </select>
        </div>

        {/* ── Header strip · counts + last updated ─────────────────── */}
        {data && (
          <div data-testid="unit-history-header-strip" style={{ marginBottom: 16, fontSize: 12, color: "#555" }}>
            <strong data-testid="unit-history-event-count">{data.counts.total}</strong> events ·
            {" "}asset id <code style={{ fontSize: 10 }}>{data.asset_id || "—"}</code> ·
            {" "}generated {formatTs(data.doctrine && data.doctrine.generated_at)}
          </div>
        )}

        {/* ── Error ─────────────────────────────────────────────── */}
        {error && (
          <div data-testid="unit-history-error" style={{ background: "#fae2e0", padding: 12, borderRadius: 4, color: "#a33", fontSize: 12, marginBottom: 16 }}>
            Unit history feed unavailable. No data invented. · {error}
          </div>
        )}

        {/* ── Events ─────────────────────────────────────────────── */}
        {loading && !data && (
          <div data-testid="unit-history-loading" style={{ fontSize: 12, color: "#666" }}>Loading…</div>
        )}

        {data && data.events.length === 0 && !error && (
          <EmptyState
            data-testid="unit-history-empty"
            kicker="No events in scope"
            title={data.asset_id ? "No asset history events found for this unit in the selected range." : "No asset record found for this unit, or no events exist in the selected range."}
            body="Try a wider date range, clear filters, or pick a different unit. No placeholder events will be invented."
          />
        )}

        {data && data.events.length > 0 && (
          <div data-testid="unit-history-events-list" style={{ display: "grid", gap: 10 }}>
            {data.events.map((ev) => (
              <EventCard key={ev.event_id} ev={ev} />
            ))}
          </div>
        )}

        {/* ── Unavailable event families (honest placeholders) ────── */}
        {data && data.unavailable_event_types && data.unavailable_event_types.length > 0 && (
          <section data-testid="unit-history-unavailable-block" style={{ marginTop: 28 }}>
            <h3 style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: ".05em", color: "#888", marginBottom: 8 }}>
              Not yet tracked
            </h3>
            <div style={{ fontSize: 11, color: "#666", marginBottom: 8 }}>
              These event families are honest placeholders — backend has no source yet. They will appear here when their tracks ship.
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 8 }}>
              {data.unavailable_event_types.map((u) => (
                <div key={u.event_type} data-testid={`unit-history-placeholder-${u.event_type}`} style={{
                  padding: 10, background: "#eef0f3", borderRadius: 4,
                  borderLeft: "3px solid #aaa",
                }}>
                  <div style={{ fontSize: 12, fontWeight: 700, textTransform: "capitalize" }}>{u.event_type}</div>
                  <div style={{ fontSize: 11, color: "#555", marginTop: 4 }}>{u.reason}</div>
                  <div style={{ fontSize: 10, color: "#888", marginTop: 4, fontStyle: "italic" }}>{u.future_track}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── Doctrine footer ───────────────────────────────────── */}
        <div data-testid="unit-history-doctrine-footer" style={{
          marginTop: 24, padding: 12, fontSize: 11, color: "#666",
          background: "var(--paper-card)", border: "1px dashed var(--border-bold)", borderRadius: 4,
        }}>
          Single source of truth · Asset Service Event Backbone. One unit · one history.
          Repair Complete ≠ Returned-To-Service — Dispatch retains the final RTS step.
        </div>
      </PortalShell>
    </div>
  );
}
