// FleetVisibility.jsx — iter251 Phase 3 · Dispatch / Shop / Safety
// fleet visibility surfaces · operational clarity NOT dashboard theater.
//
// One component, three scopes ("dispatch" | "shop" | "safety") driven by the
// `scope` prop. All three views render the operator-strongly-approved
// "group defects by truck" presentation:
//   • OOS-bearing units first
//   • Driver-note thumbprint surfaced under each defect (the single
//     highest-signal operational input)
//   • Calm operational statuses: Available / Monitor / Repair Required /
//     Out of Service / Repair In Progress
//   • NO compliance theater · NO scoreboards · NO KPI bloat
//
// Scope deltas:
//   dispatch  → focus on availability + OOS readout
//   shop      → focus on actionability + photos + repair pipeline
//   safety    → focus on governance + audit trail + version stamp
//
// Mobile-first · no horizontal overflow · matches existing portal palette.

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Truck, AlertOctagon, Wrench, CheckCircle2, Clock,
  RefreshCw, MessageSquareQuote, ShieldCheck, FileDown, ChevronDown, ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { MasciLogo } from "@/components/MasciLogo";
import { LangToggle } from "@/components/LangToggle";
import { useT } from "@/lib/i18n";
import { paletteFor } from "@/lib/portalPalette";
import { getShopToken } from "@/lib/shopAuth";
import { getDispatchToken } from "@/lib/dispatchAuth";
import { getSafetyToken } from "@/lib/safetyAuth";
import { getAdminToken } from "@/lib/adminAuth";

const API = process.env.REACT_APP_BACKEND_URL || "";

function scopeTokenHeader(scope) {
  // Always include X-Admin-Token when present · enables admin "view as
  // Shop/Dispatch/Safety" impersonation without minting a portal token.
  // The backend gates ALL three by-scope endpoints with admin OR portal
  // token, so this is safe and operator-approved (test report iter255).
  const admin = getAdminToken() || "";
  const base = admin ? { "X-Admin-Token": admin } : {};
  if (scope === "shop") return { ...base, "X-Shop-Token": getShopToken() || "" };
  if (scope === "dispatch") return { ...base, "X-Dispatch-Token": getDispatchToken() || "" };
  if (scope === "safety") return { ...base, "X-Safety-Token": getSafetyToken() || "" };
  return base;
}

function scopeHomeRoute(scope) {
  return scope === "shop"
    ? "/shop"
    : scope === "dispatch"
    ? "/dispatch-portal"
    : "/safety-portal";
}

function StatusPill({ status, t }) {
  const map = {
    available:           { label: t("Available"),           bg: "bg-emerald-100", text: "text-emerald-900", border: "border-emerald-300" },
    defect_open:         { label: t("Repair Required"),     bg: "bg-amber-100",   text: "text-amber-900",   border: "border-amber-300"   },
    oos:                 { label: t("Out of Service"),      bg: "bg-red-100",     text: "text-red-900",     border: "border-red-300"     },
    repair_in_progress:  { label: t("Repair In Progress"),  bg: "bg-sky-100",     text: "text-sky-900",     border: "border-sky-300"     },
    returned_to_service: { label: t("Returned to Service"), bg: "bg-emerald-100", text: "text-emerald-900", border: "border-emerald-300" },
    unknown:             { label: t("Unknown"),             bg: "bg-slate-100",   text: "text-slate-700",   border: "border-slate-300"   },
  };
  const cfg = map[status] || map.unknown;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border-2 text-[10px] font-mono uppercase tracking-wider font-bold ${cfg.bg} ${cfg.text} ${cfg.border}`}
      data-testid={`fleet-status-pill-${status}`}
    >
      {cfg.label}
    </span>
  );
}

function SeverityBadge({ severity, t }) {
  if (severity === "oos") {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-red-700 text-white">
        <AlertOctagon className="w-3 h-3" />
        {t("Out of Service")}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-600 text-white">
      <Wrench className="w-3 h-3" />
      {t("Monitor")}
    </span>
  );
}

function UnitCard({ group, scope, t, expanded, onToggle }) {
  const unit = group.unit_number;
  const status = group.truck_status || (group.open_oos_count > 0 ? "oos" : "defect_open");
  const lastAt = group.latest_inspection_at
    ? new Date(group.latest_inspection_at).toLocaleString()
    : t("—");
  return (
    <div
      className="bg-white rounded-md border-2 border-slate-200 overflow-hidden shadow-sm"
      data-testid={`fleet-unit-card-${unit}`}
    >
      <button
        type="button"
        onClick={onToggle}
        className="w-full px-4 py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50 transition-colors text-left"
        data-testid={`fleet-unit-card-${unit}-toggle`}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white shrink-0">
            <Truck className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <div className="font-display text-base sm:text-lg font-bold text-slate-900 truncate">
              {unit}{group.is_trailer ? ` · ${t("Trailer")}` : ""}
            </div>
            <div className="font-mono text-[11px] uppercase tracking-wider text-slate-500 truncate">
              {[group.make_model, group.category, group.year]
                .filter(Boolean).join(" · ") || t("Fleet unit")}
            </div>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          {group.open_oos_count > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-700 text-white text-[11px] font-bold uppercase tracking-wider">
              {group.open_oos_count} {t("OOS")}
            </span>
          )}
          {group.open_monitor_count > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-600 text-white text-[11px] font-bold uppercase tracking-wider">
              {group.open_monitor_count} {t("Monitor")}
            </span>
          )}
          <StatusPill status={status} t={t} />
          {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
        </div>
      </button>

      {expanded && (
        <div className="border-t-2 border-slate-200 px-4 py-3 bg-slate-50/40">
          <div className="text-[11px] font-mono uppercase tracking-wider text-slate-500 mb-2">
            {t("Latest DVIR")}: {lastAt}
            {group.latest_driver_name && ` · ${t("Driver")}: ${group.latest_driver_name}`}
          </div>
          <ul className="space-y-2.5">
            {group.defects.map((d, i) => (
              <li
                key={d.defect_id || i}
                className="bg-white border-2 border-slate-200 rounded-md px-3 py-2"
                data-testid={`fleet-unit-card-${unit}-defect-${i}`}
              >
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="text-sm font-semibold text-slate-900 leading-snug min-w-0">
                    {d.checklist_item || d.item || t("(no item)")}
                  </div>
                  <SeverityBadge severity={d.severity} t={t} />
                </div>
                {d.driver_note && (
                  <div
                    className="flex items-start gap-1.5 text-[13px] text-slate-700 italic bg-amber-50/60 border-l-2 border-amber-400 pl-2 py-1 rounded-sm"
                    data-testid={`fleet-unit-card-${unit}-defect-${i}-note`}
                  >
                    <MessageSquareQuote className="w-3.5 h-3.5 shrink-0 text-amber-700 mt-0.5" />
                    <span>"{d.driver_note}"</span>
                  </div>
                )}
                {Array.isArray(d.photos) && d.photos.length > 0 && (
                  <div className="text-[11px] text-slate-500 mt-1">
                    {d.photos.length} {t("photo(s)")}
                  </div>
                )}
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1.5 text-[11px] text-slate-500 font-mono">
                  {d.reported_at && (
                    <span>
                      <Clock className="w-3 h-3 inline-block mr-1 -mt-px" />
                      {new Date(d.reported_at).toLocaleString()}
                    </span>
                  )}
                  {d.regulation_ref && scope === "safety" && (
                    <span className="text-slate-400">{d.regulation_ref}</span>
                  )}
                  <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                    {d.status || "open"}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function FleetVisibility({ scope = "shop" }) {
  const { t } = useT();
  const palette = paletteFor(scope === "shop" ? "Shop" : scope === "dispatch" ? "Dispatch" : "Safety");
  const accent = palette?.accentHex || "#0F172A";

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [expanded, setExpanded] = useState({});

  const load = async () => {
    setLoading(true);
    setErr("");
    try {
      const r = await fetch(`${API}/api/shop/fleet/by-unit`, {
        headers: scopeTokenHeader(scope),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const j = await r.json();
      setData(j);
      // Auto-expand any OOS-bearing units · operationally most urgent
      const auto = {};
      (j.groups || []).forEach((g) => {
        if (g.open_oos_count > 0) auto[g.unit_number] = true;
      });
      setExpanded(auto);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [scope]);

  const groups = data?.groups || [];
  const counts = useMemo(() => ({
    units: data?.count_units || 0,
    defects: data?.count_defects || 0,
    oosUnits: groups.filter((g) => g.open_oos_count > 0).length,
    monitorOnlyUnits: groups.filter((g) => g.open_oos_count === 0 && g.open_monitor_count > 0).length,
  }), [data, groups]);

  const scopeMeta = scope === "shop"
    ? { kicker: t("Shop · Fleet Repair Queue"), title: t("Trucks needing attention") }
    : scope === "dispatch"
    ? { kicker: t("Dispatch · Fleet Availability"), title: t("Fleet operational status") }
    : { kicker: t("Safety · Fleet Governance"), title: t("Open defects across fleet") };

  return (
    <div className="min-h-screen blueprint-bg" data-testid="fleet-visibility">
      <div className="caution-stripe" />
      <header className="bg-slate-900 border-b-4" style={{ borderColor: accent }}>
        <div className="max-w-7xl mx-auto px-5 sm:px-8 py-4 flex items-center justify-between gap-3">
          <MasciLogo variant="mark" size="md" homeLink="/" />
          <LangToggle />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-8 py-6 sm:py-10 pb-16">
        <div className="mb-4">
          <Link
            to={scopeHomeRoute(scope)}
            className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-slate-600 hover:text-slate-900 font-bold"
            data-testid="fleet-visibility-back"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> {scopeMeta.kicker.split(" · ")[0]}
          </Link>
        </div>

        <div className="mb-6 flex items-start gap-3 sm:gap-4">
          <div
            className="inline-flex items-center justify-center w-12 h-12 sm:w-14 sm:h-14 rounded-md text-white shrink-0"
            style={{ backgroundColor: accent }}
          >
            <Truck className="w-6 h-6 sm:w-7 sm:h-7" />
          </div>
          <div className="flex-1 min-w-0">
            <span
              className="font-mono text-[11px] sm:text-xs uppercase tracking-[0.25em] font-bold"
              style={{ color: accent }}
            >
              {scopeMeta.kicker}
            </span>
            <h1 className="font-display text-2xl sm:text-4xl font-black tracking-tight text-slate-900 mt-0.5 leading-tight">
              {scopeMeta.title}
            </h1>
          </div>
        </div>

        <div
          className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6"
          data-testid="fleet-visibility-counts"
        >
          <Chip label={t("Open OOS units")} value={counts.oosUnits} tone="red" testId="fleet-count-oos" />
          <Chip label={t("Monitor-only units")} value={counts.monitorOnlyUnits} tone="amber" testId="fleet-count-monitor" />
          <Chip label={t("Total units with defects")} value={counts.units} tone="slate" testId="fleet-count-units" />
          <Chip label={t("Total open defects")} value={counts.defects} tone="slate" testId="fleet-count-defects" />
        </div>

        {scope === "safety" && (
          <div
            className="mb-6 bg-white border-2 border-slate-200 rounded-md px-4 py-3 flex flex-wrap items-center justify-between gap-3"
            data-testid="fleet-safety-governance-bar"
          >
            <div className="flex items-center gap-2 text-sm text-slate-700">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span className="font-semibold">{t("Severity table approved")}</span>
              <span className="font-mono text-[11px] uppercase tracking-wider text-slate-500">
                v1.3-approved-2026-05-19
              </span>
            </div>
            <a
              href={`${API}/api/admin/fleet/severity-reference-card.pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider font-bold text-slate-600 hover:text-slate-900"
              data-testid="fleet-safety-pdf-link"
            >
              <FileDown className="w-3.5 h-3.5" />
              {t("Download printable reference")}
            </a>
          </div>
        )}

        <div className="flex items-center justify-between mb-3">
          <h2 className="font-display text-lg sm:text-xl font-bold text-slate-900">
            {t("Units")}
          </h2>
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            disabled={loading}
            className="h-9 text-xs"
            data-testid="fleet-visibility-refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loading ? "animate-spin" : ""}`} />
            {t("Refresh")}
          </Button>
        </div>

        {loading && (
          <div className="text-sm text-slate-600 font-mono uppercase tracking-widest">
            {t("Loading…")}
          </div>
        )}

        {!loading && err && (
          <div className="bg-red-50 border-2 border-red-300 text-red-900 rounded-md px-4 py-3 text-sm">
            {t("Could not load fleet status.")} ({err})
          </div>
        )}

        {!loading && !err && groups.length === 0 && (
          <div className="bg-emerald-50 border-2 border-emerald-300 text-emerald-900 rounded-md px-4 py-6 text-center" data-testid="fleet-empty-state">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <div className="font-display text-lg font-bold mb-1">
              {t("All clear")}
            </div>
            <div className="text-sm">
              {t("No open defects across the fleet right now. Great job out there.")}
            </div>
          </div>
        )}

        {!loading && !err && groups.length > 0 && (
          <div className="space-y-3" data-testid="fleet-units-list">
            {groups.map((g) => (
              <UnitCard
                key={g.unit_number}
                group={g}
                scope={scope}
                t={t}
                expanded={!!expanded[g.unit_number]}
                onToggle={() => setExpanded((e) => ({ ...e, [g.unit_number]: !e[g.unit_number] }))}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function Chip({ label, value, tone, testId }) {
  const map = {
    red: "border-red-300 bg-red-50",
    amber: "border-amber-300 bg-amber-50",
    slate: "border-slate-300 bg-white",
  };
  return (
    <div
      className={`rounded-md border-2 px-3 py-2.5 ${map[tone] || map.slate}`}
      data-testid={testId}
    >
      <div className="font-mono text-[10px] uppercase tracking-widest text-slate-600 font-bold">
        {label}
      </div>
      <div className="font-display text-xl sm:text-2xl font-black text-slate-900 mt-0.5">
        {value}
      </div>
    </div>
  );
}
