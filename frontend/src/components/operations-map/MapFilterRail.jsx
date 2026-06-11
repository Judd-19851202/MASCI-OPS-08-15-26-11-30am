import React from "react";
import { ASSET_KIND_LABEL, KIND_LIST } from "@/lib/operations-map/icons";

const STATUSES = [
  { id: "green", label: "Active"   },
  { id: "amber", label: "Stale"    },
  { id: "red",   label: "Critical" },
  { id: "gray",  label: "Offline"  },
];

function toggle(list, value) {
  return list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
}

export default function MapFilterRail({ filters, setTypes, setStatus, setDriver, projects }) {
  const allTypes = filters.types.length === 0;
  const allStatus = filters.status.length === 0 || filters.status.length === 4;

  return (
    <aside className="ops-map-rail" data-testid="ops-map-filter-rail">
      <h4>Asset Type</h4>
      <label data-testid="ops-map-filter-type-all">
        <input type="checkbox" checked={allTypes} onChange={() => setTypes([])} />
        <span>All</span>
      </label>
      {KIND_LIST.map((k) => (
        <label key={k} data-testid={`ops-map-filter-type-${k}`}>
          <input type="checkbox"
            checked={!allTypes && filters.types.includes(k)}
            onChange={() => setTypes(toggle(filters.types, k))} />
          <span>{ASSET_KIND_LABEL[k]}</span>
        </label>
      ))}
      <h4>Status</h4>
      <label data-testid="ops-map-filter-status-all">
        <input type="checkbox" checked={allStatus} onChange={() => setStatus(STATUSES.map((s) => s.id))} />
        <span>All</span>
      </label>
      {STATUSES.map((s) => (
        <label key={s.id} data-testid={`ops-map-filter-status-${s.id}`}>
          <input type="checkbox"
            checked={filters.status.includes(s.id)}
            onChange={() => setStatus(toggle(filters.status, s.id))} />
          <span>{s.label}</span>
        </label>
      ))}
      <h4>Project</h4>
      <select
        data-testid="ops-map-filter-project"
        defaultValue=""
        style={{ width: "100%", padding: 6, borderRadius: 6, background: "#0b1320", color: "#cbd5e1", border: "1px solid #334155" }}>
        <option value="">All projects</option>
        {(projects || []).map((p) => <option key={p} value={p}>{p}</option>)}
      </select>
      <h4>Driver</h4>
      <input
        data-testid="ops-map-filter-driver"
        placeholder="driver name..."
        value={filters.driver}
        onChange={(e) => setDriver(e.target.value)}
        style={{ width: "100%", padding: 6, borderRadius: 6, background: "#0b1320", color: "#cbd5e1", border: "1px solid #334155" }}
      />
    </aside>
  );
}
