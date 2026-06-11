import React from "react";

/* Identity-aligned timeline.
 *
 * Translates raw Motive event_family strings (vehicle_gps,
 * geofence_enter, harsh_event, fault_code, dvir, ai_coach_recap)
 * into operational language the ForgedOps operator already uses
 * elsewhere on the platform:
 *
 *   vehicle_gps          → "Position update"
 *   geofence_enter       → "Arrived at <geofence>"
 *   geofence_exit        → "Departed <geofence>"
 *   harsh_event          → "Safety event"
 *   fault_code           → "Mechanical fault"
 *   dvir                 → "Inspection logged"
 *   ai_coach_recap       → "Coaching event"
 */
const FAMILY_PRESENTATION = {
  vehicle_gps:           { label: "Position update",  dot: "#10b981" },
  geofence_enter:        { label: "Arrived",          dot: "#0ea5e9" },
  geofence_exit:         { label: "Departed",         dot: "#8b5cf6" },
  asset_geofence_enter:  { label: "Arrived",          dot: "#0ea5e9" },
  asset_geofence_exit:   { label: "Departed",         dot: "#8b5cf6" },
  harsh_event:           { label: "Safety event",     dot: "#f43f5e" },
  fault_code:            { label: "Mechanical fault", dot: "#f59e0b" },
  dvir:                  { label: "Inspection",       dot: "#64748b" },
  ai_coach_recap:        { label: "Coaching event",   dot: "#06b6d4" },
};

function fmtTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
}

function describe(row) {
  const pres = FAMILY_PRESENTATION[row.event_family] || { label: "Event", dot: "#94a3b8" };
  const subject = row.unit_number || `Asset ${row.vehicle_id || "?"}`;

  const bits = [];
  if (row.event_family === "vehicle_gps") {
    if (row.speed_mph != null) bits.push(`${row.speed_mph} mph`);
    else if (row.speed_kph != null) bits.push(`${row.speed_kph} km/h`);
    if (row.city) bits.push(`${row.city}${row.state ? ", " + row.state : ""}`);
  } else if (row.event_family === "harsh_event") {
    if (row.severity) bits.push(`severity ${row.severity}`);
  } else if (row.event_family === "fault_code") {
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
