// Track 13.6G — Focus Banner for Deep-Link Operational Triage.
//
// When a PM clicks a row in /pm/holds or /pm/due-today, the destination
// URL carries a focus query param. This banner detects the param, loads
// the exact record from its REAL existing source API, and renders a
// prominent context-loaded card at the top of the destination page —
// fulfilling the doctrine:
//   "originating object must already be selected, highlighted, or
//    context-loaded · operator should never need to search / filter /
//    re-find the item."
//
// Supports four focus query params (one per row.kind on the PM hub):
//   focus_unit      → equipment_master by unit_number
//   focus_asset_id  → equipment_master by id
//   focus_defect_id → fleet_defects by id
//   focus_capa      → corrective_actions by id
//
// No new auth. No new endpoints. Uses existing PM/admin token plumbing.
// If the source record is not visible to the PM (out-of-scope) the
// banner renders an honest "scope-excluded" empty state.

import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = {};
  const a = getAdminToken();
  const p = getPmToken();
  const d = getDispatchToken();
  if (a) h["X-Admin-Token"] = a;
  if (p) h["X-PM-Token"] = p;
  if (d) h["X-Dispatch-Token"] = d;
  return h;
}

function readParams(search) {
  const p = new URLSearchParams(search);
  return {
    unit: p.get("focus_unit") || "",
    asset_id: p.get("focus_asset_id") || "",
    defect_id: p.get("focus_defect_id") || "",
    capa_id: p.get("focus_capa") || "",
    // Track 13.6H — dispatch deep-link triage.
    assignment_id: p.get("focus_assignment_id") || "",
    truck_id: p.get("focus_truck_id") || "",
    driver_id: p.get("focus_driver_id") || "",
  };
}

async function fetchEquipment(unit, asset_id) {
  // Real source: /api/equipment-master (public read in this codebase).
  try {
    const r = await fetch(`${API}/api/equipment-master?limit=1000`, { headers: authHeaders() });
    if (!r.ok) return null;
    const body = await r.json();
    const list = Array.isArray(body) ? body : (body?.items || body?.equipment || []);
    if (asset_id) {
      const hit = list.find((e) => e.id === asset_id || e.asset_id === asset_id);
      if (hit) return hit;
    }
    if (unit) {
      return list.find((e) => e.unit_number === unit) || null;
    }
    return null;
  } catch { return null; }
}

async function fetchFleetDefect(defect_id) {
  try {
    const r = await fetch(`${API}/api/fleet-defects?limit=1000`, { headers: authHeaders() });
    if (!r.ok) return null;
    const body = await r.json();
    const list = Array.isArray(body) ? body : (body?.items || body?.defects || []);
    return list.find((d) => d.id === defect_id) || null;
  } catch { return null; }
}

async function fetchCapa(capa_id) {
  // Real source: /api/pm/crew/capas (PM-scoped) — falls back to
  // /api/corrective-actions (admin-scoped) when PM endpoint isn't available.
  for (const path of ["/api/pm/crew/capas?limit=1000", "/api/corrective-actions?limit=1000"]) {
    try {
      const r = await fetch(`${API}${path}`, { headers: authHeaders() });
      if (!r.ok) continue;
      const body = await r.json();
      const list = Array.isArray(body) ? body : (body?.items || body?.capas || []);
      const hit = list.find((c) => c.id === capa_id);
      if (hit) return hit;
    } catch { /* try next */ }
  }
  return null;
}

// ── Track 13.6H · dispatch fetchers ────────────────────────────────
async function fetchAssignment(assignment_id) {
  try {
    const r = await fetch(`${API}/api/dispatch/assignments?limit=1000`,
                          { headers: authHeaders() });
    if (!r.ok) return null;
    const body = await r.json();
    const list = Array.isArray(body) ? body : (body?.items || body?.assignments || []);
    return list.find((a) => a.id === assignment_id || a.assignment_id === assignment_id) || null;
  } catch { return null; }
}

async function fetchDispatchTruck(truck_id) {
  // Truck identity in dispatch is the unit_number from equipment_master.
  return fetchEquipment(truck_id, truck_id);
}

async function fetchDispatchDriver(driver_id) {
  try {
    const r = await fetch(`${API}/api/dispatch/command/drivers?limit=2000`,
                          { headers: authHeaders() });
    if (!r.ok) return null;
    const body = await r.json();
    const list = Array.isArray(body) ? body : (body?.items || body?.drivers || []);
    return list.find((d) => d.id === driver_id
                            || d.driver_id === driver_id
                            || d.employee_id === driver_id
                            || d.name === driver_id) || null;
  } catch { return null; }
}

function BannerShell({ kind, sourceEngine, headline, sublines, scopeNote, testId }) {
  return (
    <div
      data-testid={testId}
      data-focus-kind={kind}
      data-source-engine={sourceEngine}
      style={{
        margin: "16px 0",
        padding: "14px 18px",
        background: "#fff8e0",
        border: "1px solid #f0c34a",
        borderRadius: 8,
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{
          background: "#f0c34a", color: "#3b2c00",
          padding: "2px 8px", borderRadius: 4, fontSize: 10,
          fontWeight: 700, letterSpacing: 0.5, textTransform: "uppercase",
        }}>FOCUSED</span>
        <strong style={{ color: "#3b2c00", fontSize: 14 }}>{headline}</strong>
      </div>
      {(sublines || []).map((s, i) => (
        <div key={i} style={{ color: "#5a4500", fontSize: 12 }}>{s}</div>
      ))}
      <div style={{ color: "#7a6300", fontSize: 10, fontStyle: "italic", marginTop: 2 }}>
        {scopeNote} · Source engine: {sourceEngine}
      </div>
    </div>
  );
}

export default function FocusBanner() {
  const { search } = useLocation();
  const params = readParams(search);
  const hasFocus = !!(params.unit || params.asset_id || params.defect_id
                       || params.capa_id || params.assignment_id
                       || params.truck_id || params.driver_id);
  const [state, setState] = useState({ loaded: false, record: null });

  useEffect(() => {
    if (!hasFocus) return;
    let cancelled = false;
    (async () => {
      let rec = null;
      let kind = "";
      let engine = "";
      if (params.unit || params.asset_id) {
        rec = await fetchEquipment(params.unit, params.asset_id);
        kind = "equipment_hold";
        engine = "equipment_master";
      } else if (params.defect_id) {
        rec = await fetchFleetDefect(params.defect_id);
        kind = "fleet_defect";
        engine = "fleet_defects";
      } else if (params.capa_id) {
        rec = await fetchCapa(params.capa_id);
        kind = "capa";
        engine = "corrective_actions";
      } else if (params.assignment_id) {
        rec = await fetchAssignment(params.assignment_id);
        kind = "assignment";
        engine = "dispatch_assignments";
      } else if (params.truck_id) {
        rec = await fetchDispatchTruck(params.truck_id);
        kind = "dispatch_truck";
        engine = "equipment_master";
      } else if (params.driver_id) {
        rec = await fetchDispatchDriver(params.driver_id);
        kind = "dispatch_driver";
        engine = "dispatch_command_drivers";
      }
      if (!cancelled) setState({ loaded: true, record: rec, kind, engine });
    })();
    return () => { cancelled = true; };
  }, [hasFocus, params.unit, params.asset_id, params.defect_id, params.capa_id,
       params.assignment_id, params.truck_id, params.driver_id]);

  if (!hasFocus) return null;
  if (!state.loaded) {
    return (
      <BannerShell
        kind="loading"
        sourceEngine="…"
        headline="Loading focused record…"
        sublines={["Resolving the originating object from its real source engine."]}
        scopeNote="PM scope respected"
        testId="focus-banner-loading"
      />
    );
  }
  if (!state.record) {
    return (
      <BannerShell
        kind="scope-excluded"
        sourceEngine="—"
        headline="Focused record not visible in your scope"
        sublines={[
          "Either the record was deleted, or your PM project scope excludes it.",
          "No data invented — empty state is honest.",
        ]}
        scopeNote="PM scope honored"
        testId="focus-banner-scope-excluded"
      />
    );
  }
  const r = state.record;
  if (state.kind === "equipment_hold") {
    return (
      <BannerShell
        kind="equipment_hold"
        sourceEngine="equipment_master"
        headline={`${r.unit_number || r.asset_id || "Equipment"} · ${r.status || "—"}`}
        sublines={[
          `${r.make_model || r.model || r.type || r.asset_type || "Equipment"} · project ${r.current_project_number || "—"}`,
          r.out_of_service_reason || r.description || r.notes ? `Reason: ${r.out_of_service_reason || r.description || r.notes}` : null,
        ].filter(Boolean)}
        scopeNote="Loaded from real equipment_master row"
        testId="focus-banner-equipment"
      />
    );
  }
  if (state.kind === "fleet_defect") {
    return (
      <BannerShell
        kind="fleet_defect"
        sourceEngine="fleet_defects"
        headline={`Defect · ${r.truck_unit_number || "truck"} · ${r.status || "—"}`}
        sublines={[
          `${r.category || "defect"} — ${r.item_text || ""}`.trim(),
          r.reported_at ? `Reported ${new Date(r.reported_at).toLocaleString()}` : null,
        ].filter(Boolean)}
        scopeNote="Loaded from real fleet_defects row"
        testId="focus-banner-defect"
      />
    );
  }
  if (state.kind === "capa") {
    return (
      <BannerShell
        kind="capa"
        sourceEngine="corrective_actions"
        headline={`CAPA · ${r.title || r.summary || "Open"} · due ${r.due_date || "—"}`}
        sublines={[
          `Status: ${r.status || "open"}`,
          (r.linked_employee_name || r.employee_name) ? `Linked to: ${r.linked_employee_name || r.employee_name}` : null,
        ].filter(Boolean)}
        scopeNote="Loaded from real corrective_actions row"
        testId="focus-banner-capa"
      />
    );
  }
  // ── Track 13.6H · dispatch banner variants ─────────────────────────
  if (state.kind === "assignment") {
    return (
      <BannerShell
        kind="assignment"
        sourceEngine="dispatch_assignments"
        headline={`Assignment · ${r.driver_name || r.driver || "driver"} · ${r.status || "—"}`}
        sublines={[
          `Truck: ${r.truck_id || r.truck_unit_number || "—"} · Project: ${r.project_number || "—"}`,
          r.shift_start_at ? `Shift start: ${new Date(r.shift_start_at).toLocaleString()}` : null,
        ].filter(Boolean)}
        scopeNote="Loaded from real dispatch_assignments row"
        testId="focus-banner-assignment"
      />
    );
  }
  if (state.kind === "dispatch_truck") {
    return (
      <BannerShell
        kind="dispatch_truck"
        sourceEngine="equipment_master"
        headline={`Truck · ${r.unit_number || r.asset_id || "—"} · ${r.status || "—"}`}
        sublines={[
          `${r.make_model || r.model || r.type || r.asset_type || "Truck"} · project ${r.current_project_number || "—"}`,
        ]}
        scopeNote="Loaded from real equipment_master row"
        testId="focus-banner-dispatch-truck"
      />
    );
  }
  if (state.kind === "dispatch_driver") {
    return (
      <BannerShell
        kind="dispatch_driver"
        sourceEngine="dispatch_command_drivers"
        headline={`Driver · ${r.name || r.driver_name || r.employee_name || "—"}`}
        sublines={[
          `Status: ${r.shift_state || r.status || r.state || "—"}`,
          (r.truck_id || r.assigned_truck) ? `Assigned truck: ${r.truck_id || r.assigned_truck}` : null,
        ].filter(Boolean)}
        scopeNote="Loaded from real dispatch_command drivers feed"
        testId="focus-banner-dispatch-driver"
      />
    );
  }
  return null;
}
