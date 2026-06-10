/**
 * pm/command/PmCommandStrip.jsx — top operational strip.
 *
 * 12 KPI tiles backed strictly by /api/pm/command-center/overview.
 * Each tile is clickable and jumps to the relevant section. No fake
 * green status; counts render em-dash while loading and the exact
 * backend integer once available.
 */
import React from "react";
import {
  Briefcase, Truck, User, Package, Layers, Activity,
  Boxes, Wrench, ShieldAlert, AlertTriangle, ListChecks, HardHat,
} from "lucide-react";

const TILES = [
  { key: "active_assignments", label: "Active Jobs", icon: Briefcase,   section: "resources" },
  { key: "trucks_assigned",    label: "Trucks",      icon: Truck,       section: "resources", filterKind: "truck" },
  { key: "drivers_assigned",   label: "Drivers",     icon: User,        section: "hauls" },
  { key: "equipment_assigned", label: "Equipment",   icon: Package,     section: "resources" },
  { key: "trailers_assigned",  label: "Trailers",    icon: Layers,      section: "resources", filterKind: "trailer" },
  { key: "road_plates_assigned", label: "Road Plates", icon: HardHat,   section: "resources", filterKind: "road_plate" },
  { key: "active_hauls",       label: "Active Hauls", icon: Activity,   section: "hauls" },
  { key: "materials_in_today", label: "Materials Today", icon: Boxes,   section: "materials",
    derive: (c) => (c.materials_in_today ?? 0) + (c.materials_out_today ?? 0) },
  { key: "defects_open",       label: "Open Defects", icon: Wrench,     section: "shop" },
  { key: "incidents_open",     label: "Incidents",   icon: AlertTriangle, section: "safety" },
  { key: "capas_open",         label: "Open Safety", icon: ShieldAlert, section: "safety" },
  { key: "loads_today",        label: "Loads Today", icon: ListChecks,  section: "hauls" },
];

export default function PmCommandStrip({ overview, loading, onJumpTo, onJumpToWithFilter }) {
  const counts = overview?.counts || {};
  return (
    <div
      data-testid="pm-cc-strip"
      className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2"
    >
      {TILES.map((t) => {
        const Icon = t.icon;
        const raw = t.derive ? t.derive(counts) : counts[t.key];
        const value = loading && raw == null ? "—" : (raw ?? 0);
        const tid = `pm-cc-tile-${t.key.replace(/_/g, "-")}`;
        return (
          <button
            key={t.key}
            type="button"
            data-testid={tid}
            onClick={() => {
              if (t.filterKind && onJumpToWithFilter) {
                onJumpToWithFilter(t.section, t.filterKind);
              } else {
                onJumpTo(t.section);
              }
            }}
            className="bg-white border border-slate-200 hover:border-slate-500 rounded-lg p-2.5 sm:p-3 text-left transition-colors group"
          >
            <div className="flex items-center justify-between mb-1">
              <Icon className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700" />
              <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400 group-hover:text-slate-700">→</span>
            </div>
            <div data-testid={`${tid}-value`} className="font-mono text-xl sm:text-2xl font-black text-slate-900 leading-none">
              {value}
            </div>
            <div className="text-[10.5px] sm:text-xs font-bold uppercase tracking-wider text-slate-600 mt-1">
              {t.label}
            </div>
          </button>
        );
      })}
    </div>
  );
}
