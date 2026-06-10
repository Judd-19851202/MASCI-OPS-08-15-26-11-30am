/**
 * OperationsCenterCommand.jsx · FORGEDOPS Operations Center · Phase 4C.
 *
 * Cross-company command board. ONE page · 9 layers:
 *
 *   Layer 1  Morning Operations Brief        /brief
 *   Layer 2  Project Health (risk engine)    /project-health
 *   Layer 3  Resource Allocation             /allocation
 *   Layer 4  Operational Conflicts           /conflicts
 *   Layer 5  Specialty Assets                /specialty-assets
 *   Layer 6  Shop Impact (high/med/low)      /shop-impact
 *   Layer 7  Safety Impact (crit/warn/info)  /safety-impact
 *   Layer 8  Telematics                      /telematics
 *   Layer 9  Operational Timeline            /timeline
 *
 * Executive Mode toggle hides row-level noise (allocation tables,
 * dispatch detail) while keeping the operational brief + project
 * health + risk + impact visible.
 *
 * Doctrine:
 *  - No new backend route (consumes Phase 4C API exclusively).
 *  - Specialty Asset terminology — road plates are ONE family member.
 *  - FleetWatcher / MaintainX render as calm "Pending Integration".
 *  - Honest empty states. No fake green status.
 *  - Map-ready fields already on every operational row (preps Live Map).
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, AlertTriangle, Wrench, Activity, Boxes, Truck,
  ShieldAlert, Layers, MapPin, Settings, ExternalLink, Eye, EyeOff,
} from "lucide-react";
import { MasciLogo } from "@/components/MasciLogo";
import { usePageTitle } from "@/lib/usePageTitle";
import { paletteFor } from "@/lib/portalPalette";
import { ocCommandApi } from "@/components/operations/command/ocCommandApi";

const PAL = paletteFor("admin");
const POLL_MS = 60000;

const FAMILY_LABEL = {
  trench_safety: "Trench Safety",
  access_protection: "Access / Protection",
  traffic_control: "Traffic Control",
  support: "Support",
};

export default function OperationsCenterCommand() {
  usePageTitle("Operations Center · MASCI");
  const nav = useNavigate();
  const [exec, setExec] = useState(false);
  const [brief, setBrief] = useState(null);
  const [ph, setPh] = useState(null);
  const [alloc, setAlloc] = useState(null);
  const [conf, setConf] = useState(null);
  const [sp, setSp] = useState(null);
  const [shop, setShop] = useState(null);
  const [safety, setSafety] = useState(null);
  const [telem, setTelem] = useState(null);
  const [tl, setTl] = useState(null);
  const [familyFilter, setFamilyFilter] = useState("all");

  const loadAll = useCallback(async () => {
    const wrap = (p) => p.catch(() => null);
    const [b, h, a, c, s, sh, sf, t, ti] = await Promise.all([
      wrap(ocCommandApi.brief()),
      wrap(ocCommandApi.projectHealth()),
      wrap(ocCommandApi.allocation()),
      wrap(ocCommandApi.conflicts()),
      wrap(ocCommandApi.specialtyAssets({ family: familyFilter === "all" ? null : familyFilter })),
      wrap(ocCommandApi.shopImpact()),
      wrap(ocCommandApi.safetyImpact()),
      wrap(ocCommandApi.telematics()),
      wrap(ocCommandApi.timeline(3, 200)),
    ]);
    setBrief(b); setPh(h); setAlloc(a); setConf(c); setSp(s);
    setShop(sh); setSafety(sf); setTelem(t); setTl(ti);
  }, [familyFilter]);

  useEffect(() => {
    loadAll();
    const id = setInterval(loadAll, POLL_MS);
    return () => clearInterval(id);
  }, [familyFilter, loadAll]);

  const b = brief?.brief || {};

  return (
    <div className="min-h-screen bg-slate-50" data-testid="operations-center-command">
      <header className={`${PAL.bg} text-white border-b border-slate-800`}>
        <div className="max-w-7xl mx-auto px-3 sm:px-6 py-3 sm:py-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 sm:gap-4 min-w-0">
            <button type="button" onClick={() => nav(-1)} className="text-white/80 hover:text-white p-1" aria-label="Back" data-testid="oc-cmd-back">
              <ArrowLeft className="w-4 h-4" />
            </button>
            <MasciLogo className="w-6 h-6 shrink-0" />
            <div className="min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/60 truncate">
                Operations · Command Center · V1
              </div>
              <h1 className="font-display text-base sm:text-xl font-black truncate">
                Cross-Company Operational Truth
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setExec((v) => !v)}
              data-testid="oc-cmd-exec-toggle"
              className="text-xs text-white/80 hover:text-white font-mono uppercase tracking-widest border border-white/20 hover:border-white/60 rounded px-2.5 py-1 inline-flex items-center gap-1.5"
              title="Hide row-level noise"
            >
              {exec ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
              Executive
            </button>
            <Link to="/dispatch-portal/command" className="hidden sm:inline-flex items-center gap-1 text-xs text-white/80 hover:text-white font-mono uppercase tracking-widest" data-testid="oc-cmd-link-dispatch">
              <ExternalLink className="w-3 h-3" /> Dispatch
            </Link>
            <Link to="/pm/command-center" className="hidden sm:inline-flex items-center gap-1 text-xs text-white/80 hover:text-white font-mono uppercase tracking-widest" data-testid="oc-cmd-link-pm">
              <ExternalLink className="w-3 h-3" /> PM
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-6 py-4 sm:py-6 space-y-4">
        {/* L1 — Morning Operations Brief */}
        <section data-testid="oc-cmd-brief" className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4">
          <h2 className="font-display text-base sm:text-lg font-black text-slate-900 mb-2">Today&apos;s Operations Brief</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
            <BriefTile testId="oc-brief-projects" label="Active Projects" value={b.active_projects} icon={Layers} />
            <BriefTile testId="oc-brief-hauls" label="Active Hauls" value={b.active_hauls} icon={Activity} />
            <BriefTile testId="oc-brief-trucks" label="Trucks Active" value={b.trucks_active} icon={Truck} />
            <BriefTile testId="oc-brief-drivers" label="Drivers Active" value={b.drivers_active} icon={Activity} />
            <BriefTile testId="oc-brief-equipment" label="Equipment" value={b.equipment_active} icon={Truck} />
            <BriefTile testId="oc-brief-specialty" label="Specialty Assets" value={b.specialty_assets_total} icon={Boxes} highlight />
            <BriefTile testId="oc-brief-defects" label="Shop Defects" value={b.open_shop_defects} icon={Wrench} tone={b.open_shop_defects > 0 ? "amber" : null} />
            <BriefTile testId="oc-brief-oos" label="OOS Assets" value={b.oos_assets} icon={AlertTriangle} tone={b.oos_assets > 0 ? "rose" : null} />
            <BriefTile testId="oc-brief-incidents" label="Incidents Open" value={b.incidents_open} icon={ShieldAlert} tone={b.incidents_open > 0 ? "rose" : null} />
            <BriefTile testId="oc-brief-capas" label="CAPAs Open" value={b.capas_open} icon={ShieldAlert} tone={b.capas_open > 0 ? "amber" : null} />
            <BriefTile testId="oc-brief-critical" label="Critical Safety" value={b.critical_safety_events} icon={AlertTriangle} tone={b.critical_safety_events > 0 ? "rose" : null} />
            <BriefTile testId="oc-brief-conflicts" label="Conflicts" value={b.resource_conflicts} icon={AlertTriangle} tone={b.resource_conflicts > 0 ? "rose" : null} />
          </div>
        </section>

        {/* L2 — Project Health */}
        <Section title="Project Health" subtitle={`${ph?.counts?.red || 0} red · ${ph?.counts?.yellow || 0} yellow · ${ph?.counts?.green || 0} green`} testId="oc-cmd-project-health">
          <ProjectHealthTable rows={ph?.rows || []} />
        </Section>

        {/* L5 — Specialty Assets (raised in priority per directive) */}
        <Section title="Specialty Asset Command" subtitle={sp ? `${sp.totals.total} total · ${sp.totals.assigned} assigned · ${sp.totals.available} available` : "loading…"} testId="oc-cmd-specialty">
          <FamilyFilter value={familyFilter} onChange={setFamilyFilter} counts={sp?.by_family} />
          <SpecialtyTable rows={sp?.rows || []} />
        </Section>

        {/* L3 — Resource Allocation (hidden in exec mode) */}
        {!exec && (
          <Section title="Resource Allocation" subtitle={alloc ? `${alloc.oos_assets} oos · ${alloc.unmapped_to_motive} unmapped` : "loading…"} testId="oc-cmd-allocation">
            <AllocationTable rows={alloc?.rows || []} unassigned={alloc?.unassigned} />
          </Section>
        )}

        {/* L4 — Operational Conflicts */}
        <Section title="Operational Conflicts" subtitle={conf ? `${conf.counts.total} total` : "loading…"} testId="oc-cmd-conflicts">
          <ConflictsTable rows={conf?.rows || []} />
        </Section>

        {/* L6 — Shop Impact */}
        <Section title="Shop Impact · Production Priority" subtitle={shop ? `${shop.counts.high} HIGH · ${shop.counts.medium} MED · ${shop.counts.low} LOW · ${shop.counts.oos} oos` : "loading…"} testId="oc-cmd-shop">
          <ShopTable rows={(shop?.rows || []).slice(0, exec ? 10 : 100)} />
        </Section>

        {/* L7 — Safety Impact */}
        <Section title="Safety Impact" subtitle={safety ? `${safety.counts.critical} CRITICAL · ${safety.counts.warning} WARN · ${safety.counts.informational} INFO` : "loading…"} testId="oc-cmd-safety">
          <SafetyTable incidents={safety?.incidents || []} capas={safety?.capas || []} />
        </Section>

        {/* L8 — Telematics */}
        <Section title="Truck Status · Telematics" subtitle={telem ? `${telem.mapped_trucks} mapped · ${telem.unmapped_trucks} unmapped` : "loading…"} testId="oc-cmd-telematics">
          <TelematicsBuckets buckets={telem?.buckets || {}} />
        </Section>

        {/* L9 — Operational Timeline (hidden in exec mode) */}
        {!exec && (
          <Section title="Operational Timeline" subtitle="last 3 days" testId="oc-cmd-timeline">
            <TimelineList events={(tl?.events || []).slice(0, 100)} />
          </Section>
        )}

        <div className="text-[10.5px] text-slate-500 font-mono uppercase tracking-widest py-3 flex items-center justify-between border-t border-slate-200">
          <span>Operations Center · Phase 4C</span>
          <span className="flex items-center gap-1"><MapPin className="w-3 h-3" /> Live Map · Pending Integration</span>
        </div>
      </main>
    </div>
  );
}

/* ─────────── Helper sub-components ─────────── */

function Section({ title, subtitle, children, testId }) {
  return (
    <section data-testid={testId} className="bg-white border border-slate-200 rounded-lg p-3 sm:p-4 space-y-2">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-display text-base sm:text-lg font-black text-slate-900">{title}</h2>
        {subtitle ? <span className="font-mono text-[10px] uppercase tracking-widest text-slate-500">· {subtitle}</span> : null}
      </header>
      {children}
    </section>
  );
}

function BriefTile({ label, value, icon: Icon, highlight, tone, testId }) {
  const toneCls =
    tone === "rose" ? "border-rose-300 bg-rose-50" :
    tone === "amber" ? "border-amber-300 bg-amber-50" :
    highlight ? "border-indigo-300 bg-indigo-50" :
    "border-slate-200 bg-white";
  return (
    <div data-testid={testId} className={`${toneCls} rounded-lg p-2.5 border`}>
      <div className="flex items-center justify-between mb-1">
        <Icon className="w-3.5 h-3.5 text-slate-500" />
      </div>
      <div data-testid={`${testId}-value`} className="font-mono text-xl sm:text-2xl font-black text-slate-900 leading-none">
        {value ?? "—"}
      </div>
      <div className="text-[10.5px] sm:text-xs font-bold uppercase tracking-wider text-slate-600 mt-1">{label}</div>
    </div>
  );
}

function FamilyFilter({ value, onChange, counts }) {
  const fams = [
    { v: "all", label: "All" },
    { v: "trench_safety", label: "Trench Safety", c: counts?.trench_safety },
    { v: "access_protection", label: "Access / Protection", c: counts?.access_protection },
    { v: "traffic_control", label: "Traffic Control", c: counts?.traffic_control },
    { v: "support", label: "Support", c: counts?.support },
  ];
  return (
    <div className="flex flex-wrap gap-1.5" data-testid="oc-cmd-specialty-filters">
      {fams.map((f) => {
        const active = f.v === value;
        return (
          <button
            key={f.v}
            type="button"
            onClick={() => onChange(f.v)}
            data-testid={`oc-cmd-specialty-filter-${f.v}`}
            className={`px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded border transition-colors ${active ? "bg-slate-900 text-white border-slate-900" : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"}`}
          >
            {f.label}
            {f.c != null ? <span className={`ml-1.5 font-mono ${active ? "text-slate-200" : "text-slate-500"}`}>{f.c}</span> : null}
          </button>
        );
      })}
    </div>
  );
}

function SpecialtyTable({ rows }) {
  if (!rows.length) return <div className="text-slate-500 text-sm py-4 text-center">No specialty assets for this filter.</div>;
  return (
    <div className="overflow-x-auto -mx-3 sm:mx-0">
      <table className="w-full min-w-[800px] text-xs sm:text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
            <th className="py-2 pl-3 pr-2">Asset</th><th className="py-2 px-2">Kind</th><th className="py-2 px-2">Family</th>
            <th className="py-2 px-2">Project</th><th className="py-2 px-2">Status</th><th className="py-2 px-2">Location</th>
            <th className="py-2 pr-3 pl-2">Trust</th>
          </tr>
        </thead>
        <tbody data-testid="oc-cmd-specialty-rows">
          {rows.map((r, i) => (
            <tr key={`${r.unit_number}-${i}`} data-testid={`oc-cmd-specialty-row-${i}`} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="py-2 pl-3 pr-2 font-mono font-bold text-slate-900">{r.unit_number}</td>
              <td className="py-2 px-2 text-slate-700">{r.asset_kind}</td>
              <td className="py-2 px-2 text-slate-700">{FAMILY_LABEL[r.family] || r.family}</td>
              <td className="py-2 px-2 font-mono text-slate-700">{r.project_number || <span className="text-slate-400">—</span>}</td>
              <td className="py-2 px-2 text-slate-700">{r.status}</td>
              <td className="py-2 px-2 text-slate-600">{r.location || "—"}</td>
              <td className="py-2 pr-3 pl-2"><Chip tone={r.project_number ? "emerald" : "slate"}>{r.trust_state}</Chip></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProjectHealthTable({ rows }) {
  if (!rows.length) return <div className="text-slate-500 text-sm py-4 text-center">No active projects.</div>;
  return (
    <div className="overflow-x-auto -mx-3 sm:mx-0">
      <table className="w-full min-w-[900px] text-xs sm:text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
            <th className="py-2 pl-3 pr-2">Project</th><th className="py-2 px-2">PM</th>
            <th className="py-2 px-2">Trucks</th><th className="py-2 px-2">Equipment</th>
            <th className="py-2 px-2">Specialty</th><th className="py-2 px-2">Hauls</th>
            <th className="py-2 px-2">Defects</th><th className="py-2 px-2">OOS</th>
            <th className="py-2 px-2">Incidents</th><th className="py-2 px-2">Risk</th>
            <th className="py-2 pr-3 pl-2 text-right">Action</th>
          </tr>
        </thead>
        <tbody data-testid="oc-cmd-project-health-rows">
          {rows.map((r, i) => (
            <tr key={r.project_number} data-testid={`oc-cmd-project-health-row-${r.project_number}`} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="py-2 pl-3 pr-2"><div className="font-mono font-bold text-slate-900">{r.project_number}</div><div className="text-[11px] text-slate-500 truncate max-w-[200px]">{r.project_name}</div></td>
              <td className="py-2 px-2 text-slate-700">{r.pm_name || "—"}</td>
              <td className="py-2 px-2 font-mono">{r.trucks_assigned}</td>
              <td className="py-2 px-2 font-mono">{r.equipment_assigned}</td>
              <td className="py-2 px-2 font-mono" title={`${r.road_plates} road plates`}>{r.specialty_assets}</td>
              <td className="py-2 px-2 font-mono">{r.active_hauls}</td>
              <td className="py-2 px-2 font-mono">{r.open_defects}</td>
              <td className="py-2 px-2 font-mono">{r.oos_assets}</td>
              <td className="py-2 px-2 font-mono">{r.open_incidents}</td>
              <td className="py-2 px-2"><RiskChip risk={r.risk} /></td>
              <td className="py-2 pr-3 pl-2 text-right whitespace-nowrap">
                <Link to={`/pm/command-center?project_number=${encodeURIComponent(r.project_number)}`} className="text-[11px] text-slate-600 hover:text-slate-900 underline-offset-2 hover:underline" data-testid={`oc-cmd-ph-open-${r.project_number}`}>
                  Open PM →
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AllocationTable({ rows, unassigned }) {
  if (!rows.length) return <div className="text-slate-500 text-sm py-4 text-center">No allocation data.</div>;
  return (
    <>
      <div className="overflow-x-auto -mx-3 sm:mx-0">
        <table className="w-full min-w-[700px] text-xs sm:text-sm">
          <thead>
            <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
              <th className="py-2 pl-3 pr-2">Project</th><th className="py-2 px-2">Trucks</th>
              <th className="py-2 px-2">Equipment</th><th className="py-2 px-2">Specialty</th>
              <th className="py-2 pr-3 pl-2">Drivers</th>
            </tr>
          </thead>
          <tbody data-testid="oc-cmd-allocation-rows">
            {rows.map((r) => (
              <tr key={r.project_number} className="border-b border-slate-100">
                <td className="py-2 pl-3 pr-2 font-mono font-bold">{r.project_number}</td>
                <td className="py-2 px-2 font-mono">{r.trucks}</td>
                <td className="py-2 px-2 font-mono">{r.equipment}</td>
                <td className="py-2 px-2 font-mono">{r.road_plates}</td>
                <td className="py-2 pr-3 pl-2 font-mono">{r.drivers}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {unassigned && (Object.values(unassigned).some((v) => v > 0)) ? (
        <div className="text-xs text-slate-600 mt-2" data-testid="oc-cmd-allocation-unassigned">
          Unassigned: <strong>{unassigned.trucks}</strong> trucks · <strong>{unassigned.equipment}</strong> equipment · <strong>{unassigned.road_plates}</strong> road plates
        </div>
      ) : null}
    </>
  );
}

function ConflictsTable({ rows }) {
  if (!rows.length) return <div className="text-emerald-700 text-sm py-4 text-center font-bold" data-testid="oc-cmd-conflicts-clean">No operational conflicts detected.</div>;
  return (
    <ul className="space-y-1.5" data-testid="oc-cmd-conflicts-list">
      {rows.map((r, i) => (
        <li key={i} data-testid={`oc-cmd-conflicts-row-${i}`} className="flex items-start gap-2 text-xs sm:text-sm border-b border-slate-100 last:border-b-0 py-1.5">
          <Chip tone="rose">{r.kind.replace(/_/g, " ")}</Chip>
          <span className="font-mono font-bold text-slate-900 truncate">{r.subject}</span>
          {r.projects ? <span className="text-slate-500">→ {r.projects.join(", ")}</span> : null}
          {r.trucks ? <span className="text-slate-500">→ {r.trucks.join(", ")}</span> : null}
          {r.project_number ? <span className="text-slate-500">→ {r.project_number}</span> : null}
        </li>
      ))}
    </ul>
  );
}

function ShopTable({ rows }) {
  if (!rows.length) return <div className="text-slate-500 text-sm py-4 text-center">No open shop impacts.</div>;
  return (
    <div className="overflow-x-auto -mx-3 sm:mx-0">
      <table className="w-full min-w-[700px] text-xs sm:text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
            <th className="py-2 pl-3 pr-2">Priority</th><th className="py-2 px-2">Unit</th>
            <th className="py-2 px-2">Asset Kind</th><th className="py-2 px-2">Issue</th>
            <th className="py-2 px-2">Severity</th><th className="py-2 pr-3 pl-2">Status</th>
          </tr>
        </thead>
        <tbody data-testid="oc-cmd-shop-rows">
          {rows.map((r, i) => (
            <tr key={i} className="border-b border-slate-100">
              <td className="py-2 pl-3 pr-2"><PriorityChip p={r.production_priority} /></td>
              <td className="py-2 px-2 font-mono font-bold">{r.unit_number || "—"}</td>
              <td className="py-2 px-2">{r.asset_kind}</td>
              <td className="py-2 px-2 truncate max-w-xs" title={r.item_text}>{r.item_text || "—"}</td>
              <td className="py-2 px-2">{r.severity || "—"}</td>
              <td className="py-2 pr-3 pl-2">{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SafetyTable({ incidents, capas }) {
  const empty = !incidents.length && !capas.length;
  if (empty) return <div className="text-slate-500 text-sm py-4 text-center">No open safety items.</div>;
  return (
    <div className="space-y-3" data-testid="oc-cmd-safety-rows">
      {incidents.length ? (
        <div>
          <h3 className="text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">Incidents</h3>
          <ul className="space-y-1">
            {incidents.slice(0, 20).map((r, i) => (
              <li key={`inc-${i}`} className="flex items-start gap-2 text-xs sm:text-sm py-1 border-b border-slate-100 last:border-b-0">
                <TierChip t={r.tier} />
                <span className="font-mono text-[10.5px] text-slate-500">{r.project_number || ""}</span>
                <span className="text-slate-700 truncate" title={r.summary}>{r.summary || "—"}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {capas.length ? (
        <div>
          <h3 className="text-[10px] uppercase tracking-widest font-bold text-slate-500 mb-1">CAPAs</h3>
          <ul className="space-y-1">
            {capas.slice(0, 20).map((r, i) => (
              <li key={`capa-${i}`} className="flex items-start gap-2 text-xs sm:text-sm py-1 border-b border-slate-100 last:border-b-0">
                <TierChip t={r.tier} />
                <span className="font-mono text-[10.5px] text-slate-500">{r.project_number || ""}</span>
                <span className="text-slate-700 truncate" title={r.summary}>{r.summary || "—"}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function TelematicsBuckets({ buckets }) {
  const items = [
    { k: "moving", label: "Moving", tone: "emerald" },
    { k: "idling", label: "Idling", tone: "amber" },
    { k: "at_job", label: "At Job", tone: "sky" },
    { k: "at_plant", label: "At Plant", tone: "sky" },
    { k: "at_yard", label: "At Yard", tone: "slate" },
    { k: "at_shop", label: "At Shop", tone: "amber" },
    { k: "offline", label: "Offline", tone: "rose" },
    { k: "no_gps", label: "No GPS", tone: "slate" },
    { k: "unknown", label: "Unknown", tone: "slate" },
  ];
  return (
    <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-2" data-testid="oc-cmd-telematics-buckets">
      {items.map((it) => (
        <div key={it.k} data-testid={`oc-cmd-telematics-bucket-${it.k}`} className="bg-slate-50 border border-slate-200 rounded-lg p-2 text-center">
          <div className="font-mono text-xl font-black text-slate-900">{buckets[it.k] ?? 0}</div>
          <div className="text-[10px] uppercase tracking-wider text-slate-500 mt-0.5">{it.label}</div>
        </div>
      ))}
    </div>
  );
}

function TimelineList({ events }) {
  if (!events.length) return <div className="text-slate-500 text-sm py-4 text-center">No recent activity.</div>;
  return (
    <ol className="space-y-1" data-testid="oc-cmd-timeline-events">
      {events.map((ev, i) => (
        <li key={i} className="flex items-start gap-2 border-b border-slate-100 last:border-b-0 py-1.5 text-xs sm:text-sm">
          <span className="font-mono text-[10.5px] text-slate-500">{String(ev.timestamp || "—").slice(0, 16).replace("T", " ")}</span>
          <Chip tone="slate">{ev.kind}</Chip>
          {ev.project_number ? <span className="font-mono text-[10.5px] text-slate-500">{ev.project_number}</span> : null}
          <span className="text-slate-700 truncate" title={ev.summary}>{ev.summary}</span>
        </li>
      ))}
    </ol>
  );
}

/* Chips */
function Chip({ tone = "slate", children }) {
  const t = {
    slate: "bg-slate-100 text-slate-800 border-slate-300",
    emerald: "bg-emerald-100 text-emerald-900 border-emerald-300",
    amber: "bg-amber-100 text-amber-900 border-amber-300",
    rose: "bg-rose-100 text-rose-900 border-rose-300",
    sky: "bg-sky-100 text-sky-900 border-sky-300",
  }[tone];
  return <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${t}`}>{children}</span>;
}

function RiskChip({ risk }) {
  const t = risk === "red" ? "rose" : risk === "yellow" ? "amber" : "emerald";
  return <Chip tone={t}>{risk}</Chip>;
}

function PriorityChip({ p }) {
  const t = p === "high" ? "rose" : p === "medium" ? "amber" : "slate";
  return <Chip tone={t}>{p}</Chip>;
}

function TierChip({ t }) {
  const tone = t === "critical" ? "rose" : t === "warning" ? "amber" : "slate";
  return <Chip tone={tone}>{t}</Chip>;
}
