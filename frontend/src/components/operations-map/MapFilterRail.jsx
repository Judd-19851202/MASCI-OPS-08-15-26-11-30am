import React from "react";
import { ASSET_KIND_LABEL, KIND_LIST } from "@/lib/operations-map/icons";

/* Identity-aligned filter rail.
 * Projects and Geofences are PRIMARY operational filters (top of rail).
 * Equipment Type is moved to SECONDARY (below the fold). Status is
 * always visible because it's the at-a-glance triage tool.
 */
const STATUS_TILES = [
  { id: "green", label: "Working",   tone: "emerald" },
  { id: "amber", label: "Idle",      tone: "amber"   },
  { id: "red",   label: "Attention", tone: "rose"    },
  { id: "gray",  label: "Offline",   tone: "slate"   },
];

function toggle(list, value) {
  return list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
}

export default function MapFilterRail({ filters, setTypes, setStatus, setDriver, projects, geofences }) {
  const allTypes = filters.types.length === 0;

  return (
    <aside className="ops-map-rail" data-testid="ops-map-filter-rail">

      {/* PRIMARY · Projects */}
      <h4>Projects</h4>
      <select
        data-testid="ops-map-filter-project"
        defaultValue=""
        style={{ marginBottom: 4 }}>
        <option value="">All Active Projects</option>
        {(projects || []).map((p) => (
          <option key={p.id || p} value={p.id || p}>{p.name || p}</option>
        ))}
      </select>

      {/* PRIMARY · Geofences */}
      <h4>Geofences</h4>
      <select
        data-testid="ops-map-filter-geofence"
        defaultValue=""
        style={{ marginBottom: 4 }}>
        <option value="">All Geofences ({geofences?.length ?? 0})</option>
        {(geofences || []).slice(0, 200).map((g) => (
          <option key={g.id} value={g.id}>
            {g.name} {g.category ? `· ${g.category}` : ""}
          </option>
        ))}
      </select>

      {/* ALWAYS · Status (operational triage) */}
      <h4>Status</h4>
      {STATUS_TILES.map((s) => (
        <label key={s.id} data-testid={`ops-map-filter-status-${s.id}`}>
          <input type="checkbox"
            checked={filters.status.includes(s.id)}
            onChange={() => setStatus(toggle(filters.status, s.id))} />
          <span>{s.label}</span>
        </label>
      ))}

      {/* PRIMARY · Operator (driver) */}
      <h4>Operator</h4>
      <input
        type="text"
        data-testid="ops-map-filter-driver"
        placeholder="Operator name…"
        value={filters.driver}
        onChange={(e) => setDriver(e.target.value)}
      />

      {/* SECONDARY · Equipment Type (collapsed by default) */}
      <details style={{ marginTop: 16 }} data-testid="ops-map-filter-equipment-type">
        <summary style={{ cursor: "pointer", color: "#0f172a",
                           fontFamily: "Chivo, IBM Plex Sans, sans-serif",
                           fontWeight: 900, fontSize: 11,
                           letterSpacing: "0.08em", textTransform: "uppercase",
                           padding: "4px 0" }}>
          Equipment Type
        </summary>
        <label data-testid="ops-map-filter-type-all" style={{ marginTop: 6 }}>
          <input type="checkbox" checked={allTypes} onChange={() => setTypes([])} />
          <span>All equipment</span>
        </label>
        {KIND_LIST.map((k) => (
          <label key={k} data-testid={`ops-map-filter-type-${k}`}>
            <input type="checkbox"
              checked={!allTypes && filters.types.includes(k)}
              onChange={() => setTypes(toggle(filters.types, k))} />
            <span>{ASSET_KIND_LABEL[k]}</span>
          </label>
        ))}
      </details>
    </aside>
  );
}
