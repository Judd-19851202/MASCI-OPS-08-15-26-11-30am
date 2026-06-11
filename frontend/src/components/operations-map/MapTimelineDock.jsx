import React from "react";

const FAMILY_COLOR = {
  vehicle_gps: "#22c55e",
  geofence_enter: "#38bdf8",
  geofence_exit: "#a78bfa",
  asset_geofence_enter: "#38bdf8",
  asset_geofence_exit: "#a78bfa",
  harsh_event: "#ef4444",
  fault_code: "#f59e0b",
  dvir: "#94a3b8",
  ai_coach_recap: "#22d3ee",
};

function fmtTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

export default function MapTimelineDock({ rows }) {
  if (!rows || rows.length === 0) {
    return (
      <section className="ops-map-timeline" data-testid="ops-map-timeline">
        <h4 style={{ color: "#64748b", margin: 0, fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase" }}>
          Timeline · waiting for events
        </h4>
      </section>
    );
  }
  return (
    <section className="ops-map-timeline" data-testid="ops-map-timeline">
      <h4 style={{ color: "#94a3b8", margin: "0 0 6px 0", fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase" }}>
        Timeline · {rows.length} events · live
      </h4>
      {rows.map((r, i) => (
        <div className="row" key={r.id || i} data-testid={`ops-map-timeline-row-${i}`}>
          <span className="ts">{fmtTime(r.event_at)}</span>
          <span className="dot" style={{ background: FAMILY_COLOR[r.event_family] || "#64748b" }} />
          <span>
            <strong style={{ color: "#cbd5e1" }}>{r.unit_number || `veh ${r.vehicle_id || "?"}`}</strong>
            <span style={{ color: "#94a3b8" }}> · {r.event_family || r.event_kind || "event"}</span>
            {r.speed_mph != null && <span style={{ color: "#64748b" }}> · {r.speed_mph} mph</span>}
            {r.city && <span style={{ color: "#64748b" }}> · {r.city}, {r.state}</span>}
            {r.severity && <span style={{ color: "#f87171", marginLeft: 8 }}>{r.severity}</span>}
            {r.source === "webhook" && <span style={{ color: "#38bdf8", marginLeft: 8 }}>live</span>}
          </span>
        </div>
      ))}
    </section>
  );
}
