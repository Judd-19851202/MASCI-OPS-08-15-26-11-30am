import React from "react";
import { EVENT_FAMILY_LABEL } from "@/lib/operations-map/eventVocab";

/* Identity-aligned timeline.
 *
 * Translates raw Motive event_family strings (vehicle_gps,
 * geofence_enter, harsh_event, fault_code, dvir, ai_coach_recap)
 * into operational language the ForgedOps operator already uses
 * elsewhere on the platform:
 *
 *   vehicle_gps          → "Position Update"
 *   geofence_enter       → "Arrived at <geofence>"
 *   geofence_exit        → "Departed <geofence>"
 *   harsh_event          → "Safety Event"
 *   fault_code           → "Mechanical Fault"
 *   dvir                 → "Inspection Logged"
 *   ai_coach_recap       → "Coaching Event"
 */
const FAMILY_DOT = {
  vehicle_gps:           "#10b981",
  vehicle_location:      "#10b981",
  vehicle_location_received: "#10b981",
  geofence_enter:        "#0ea5e9",
  geofence_exit:         "#8b5cf6",
  asset_geofence_enter:  "#0ea5e9",
  asset_geofence_exit:   "#8b5cf6",
  harsh_event:           "#f43f5e",
  fault_code:            "#f59e0b",
  dvir:                  "#64748b",
  ai_coach_recap:        "#06b6d4",
};

function fmtTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

function describe(row) {
  const family = row.event_family || row.event_kind;
  const label = EVENT_FAMILY_LABEL[family] || "Event";
  const dot   = FAMILY_DOT[family] || "#94a3b8";
  const pres  = { label, dot };
  const subject = row.unit_number || `Asset ${row.vehicle_id || "?"}`;

  const bits = [];
  if (family === "vehicle_gps" || family === "vehicle_location" || family === "vehicle_location_received") {
    if (row.speed_mph != null) bits.push(`${row.speed_mph} mph`);
    else if (row.speed_kph != null) bits.push(`${row.speed_kph} km/h`);
    if (row.city) bits.push(`${row.city}${row.state ? ", " + row.state : ""}`);
  } else if (family === "harsh_event") {
    if (row.severity) bits.push(`severity ${row.severity}`);
  } else if (family === "fault_code") {
    if (row.severity) bits.push(`severity ${row.severity}`);
  } else {
    if (row.city) bits.push(`${row.city}${row.state ? ", " + row.state : ""}`);
  }
  return { pres, subject, detail: bits.join(" · ") };
}

export default function MapTimelineDock({ rows }) {
  if (!rows || rows.length === 0) {
    return (
      <section className="ops-map-timeline" data-testid="ops-map-timeline">
        <h4>Operational Activity · waiting for events</h4>
      </section>
    );
  }
  return (
    <section className="ops-map-timeline" data-testid="ops-map-timeline">
      <h4>Operational Activity · {rows.length} events · live</h4>
      {rows.map((r, i) => {
        const { pres, subject, detail } = describe(r);
        return (
          <div className="row" key={r.id || i} data-testid={`ops-map-timeline-row-${i}`}>
            <span className="ts">{fmtTime(r.event_at)}</span>
            <span className="dot" style={{ background: pres.dot }} />
            <span>
              <strong>{subject}</strong>
              <span style={{ color: "#475569" }}> — {pres.label}</span>
              {detail && <span style={{ color: "#64748b" }}> · {detail}</span>}
              {r.source === "webhook" && (
                <span style={{ color: "#0d9488", marginLeft: 8, fontSize: 11,
                              textTransform: "uppercase", letterSpacing: "0.06em",
                              fontWeight: 700 }}>
                  live
                </span>
              )}
            </span>
          </div>
        );
      })}
    </section>
  );
}
