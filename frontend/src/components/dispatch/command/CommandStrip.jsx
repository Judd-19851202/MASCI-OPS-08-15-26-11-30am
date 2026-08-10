/**
 * CommandStrip.jsx · Overview KPI strip for Dispatch Command Center.
 *
 * 8 calm color-coded tiles, clickable to deep-link to the right tab.
 * Skeleton-loader-safe: renders an em-dash when the summary is still
 * loading.
 */
import React from "react";
import {
  Truck, User, Send, Activity, Wrench, ShieldAlert, AlertOctagon, AlertTriangle,
} from "lucide-react";
import { KpiInlineHelp } from "@/components/KpiInlineHelp";

function Tile({
  icon: Icon, label, value, sub, tone, onClick, testId,
}) {
  const toneCls = {
    slate:   "border-slate-300 bg-slate-50 text-slate-900",
    emerald: "border-emerald-300 bg-emerald-50 text-emerald-900",
    sky:     "border-sky-300 bg-sky-50 text-sky-900",
    indigo:  "border-indigo-300 bg-indigo-50 text-indigo-900",
    amber:   "border-amber-300 bg-amber-50 text-amber-900",
    rose:    "border-rose-300 bg-rose-50 text-rose-900",
    slatedk: "border-slate-400 bg-slate-100 text-slate-900",
  }[tone] || "border-slate-300 bg-white text-slate-900";

  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      className={`flex flex-col items-start gap-1 border ${toneCls} rounded-md p-3 sm:p-4 text-left hover:shadow-md transition-shadow min-h-[88px] w-full focus:outline-none focus:ring-2 focus:ring-slate-400`}
    >
      <div className="flex items-center justify-between w-full">
        <Icon className="w-4 h-4 opacity-70" />
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-70">
          {label}
        </div>
      </div>
      <div className="font-display text-2xl sm:text-3xl font-black leading-none mt-1">
        {value == null ? "—" : value}
      </div>
      {sub ? (
        <div className="font-mono text-[10px] uppercase tracking-[0.12em] opacity-60">
          {sub}
        </div>
      ) : null}
    </button>
  );
}

export default function CommandStrip({ summary, loading, onJumpTo, metadata }) {
  const fleet = summary?.fleet?.counts || {};
  const drivers = summary?.drivers?.counts || {};
  const haul = summary?.haul?.counts || {};
  const shop = summary?.shop || {};
  const safety = summary?.safety || {};

  const dispatches = (haul.active_hauls != null) ? haul.active_hauls : null;
  // Operational truth: active assets = spine-active + phantom trucks
  // in active dispatch (handled inside fleet.active already in Phase 3).
  const activeAssets = (fleet.active != null) ? fleet.active : null;
  // Operational truth: active drivers = sessions ∪ assignment-named drivers
  const activeDrivers = (drivers.active_total != null)
    ? drivers.active_total
    : (drivers.shifted != null ? drivers.shifted : null);
  const assetsInShop = (shop.oos_units != null && shop.defect_open_units != null)
    ? (shop.oos_units + shop.defect_open_units) : null;
  const failedDvirs = shop.defects_open != null ? shop.defects_open : null;
  const openDefects = (shop.defects_open != null && shop.defects_acknowledged != null)
    ? (shop.defects_open + shop.defects_acknowledged) : null;
  const incidents = safety.incidents_open != null ? safety.incidents_open : null;
  const needsMapping = fleet.needs_mapping || 0;

  const skeleton = !summary && loading;

  return (
    <div data-testid="command-strip" className="space-y-2">
      <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500" data-testid="command-strip-help-row">
        <span>Dispatch snapshot</span>
        <KpiInlineHelp metadata={metadata} fallbackLabel="Dispatch snapshot" testId="command-strip-help" />
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 sm:gap-3">
        <Tile icon={User}   label="Drivers"    value={skeleton ? "…" : activeDrivers}
          sub={drivers.assignment_only ? `${drivers.assignment_only} no_session` : "active"} tone="sky"     onClick={() => onJumpTo("drivers")} testId="strip-drivers" />
        <Tile icon={Truck}  label="Assets"     value={skeleton ? "…" : activeAssets}
          sub={needsMapping > 0 ? `${needsMapping} needs map` : "active"}    tone="emerald" onClick={() => onJumpTo("fleet")}   testId="strip-assets" />
        <Tile icon={Send}   label="Dispatches" value={skeleton ? "…" : dispatches}
          sub="active"    tone="indigo"  onClick={() => onJumpTo("hauls")}   testId="strip-dispatches" />
        <Tile icon={Activity} label="Hauls"    value={skeleton ? "…" : haul.active_hauls ?? null}
          sub="in-flight" tone="indigo"  onClick={() => onJumpTo("hauls")}   testId="strip-hauls" />
        <Tile icon={Wrench} label="In Shop"    value={skeleton ? "…" : assetsInShop}
          sub="oos + defect" tone="amber" onClick={() => onJumpTo("shop")}   testId="strip-in-shop" />
        <Tile icon={ShieldAlert} label="DVIR Open" value={skeleton ? "…" : failedDvirs}
          sub="needs attn" tone="amber"  onClick={() => onJumpTo("shop")}    testId="strip-dvir-open" />
        <Tile icon={AlertOctagon} label="Defects"  value={skeleton ? "…" : openDefects}
          sub="open + ack" tone="rose"   onClick={() => onJumpTo("shop")}    testId="strip-defects" />
        <Tile icon={AlertTriangle} label="Incidents" value={skeleton ? "…" : incidents}
          sub="open"       tone="rose"   onClick={() => onJumpTo("shop")}    testId="strip-incidents" />
      </div>

      {/* Phase 3 · Operational trust strip — explicit reconciliation
          warnings so the dispatcher never sees a false zero.
          Phase 3.1 · banner now links directly to the mapping queue. */}
      {!skeleton && needsMapping > 0 ? (
        <div
          data-testid="command-strip-needs-mapping"
          className="bg-amber-50 border border-amber-300 text-amber-900 rounded-md p-2 text-xs flex items-center justify-between gap-2"
        >
          <span>
            <b>{needsMapping}</b> active dispatch truck{needsMapping === 1 ? "" : "s"}{" "}
            {needsMapping === 1 ? "is" : "are"} not in the Asset Spine yet — surface them in the Fleet tab as
            <span className="font-mono"> not_in_spine</span> rows.
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onJumpTo("fleet")}
              data-testid="command-strip-needs-mapping-link"
              className="font-mono uppercase tracking-widest text-[10px] underline"
            >Open Fleet →</button>
            <a
              href="/admin/asset-mapping"
              data-testid="command-strip-mapping-queue-link"
              className="font-mono uppercase tracking-widest text-[10px] bg-amber-900 text-white rounded px-2 py-1 hover:bg-amber-800"
            >Open Mapping Queue →</a>
          </div>
        </div>
      ) : null}
    </div>
  );
}
