// PmHub — /pm Overview (iter105 redesign)
//
// Mirrors AdminHub: KPI tiles + Active Jobs status banner. Every panel
// that used to live on this scroll has been moved to a /pm/{section}
// sub-route reachable from the PmShell sidebar — same architecture as
// the Admin Console.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClipboardCheck, Users, AlertOctagon, ClipboardList, Wrench, Box,
  FileText, ArrowRight, Loader2, ShieldCheck, Image as ImageIcon,
  UserCheck, Briefcase, GraduationCap,
} from "lucide-react";
import PmShell from "@/components/PmShell";
import { api } from "@/lib/api";

const FORM_TILES = [
  { to: "/tasks",             icon: ClipboardCheck, title: "Tasks & Actions",     countKey: null,         sub: "Open · overdue · cross-portal", accent: "amber" },
  { to: "/pm/daily",          icon: ClipboardList, title: "Daily Reports",       countKey: "daily",      sub: "reports on file",    accent: "red" },
  { to: "/pm/inspections",    icon: ClipboardCheck, title: "Site Inspections",    countKey: "inspections", sub: "reports on file",   accent: "red" },
  { to: "/pm/meetings",       icon: Users,         title: "Safety Meetings",     countKey: "meetings",   sub: "meetings logged",    accent: "slate" },
  { to: "/pm/jha-plans",      icon: FileText,      title: "Job Hazard Plans",    countKey: "jhaPlans",   sub: "plans uploaded",     accent: "amber" },
  { to: "/pm/trench-boxes",   icon: Box,           title: "Trench Box Data",     countKey: "trenchBoxes", sub: "boxes on file",     accent: "slate" },
  { to: "/pm/incidents",      icon: AlertOctagon,  title: "Incident Reports",    countKey: "incidents",  sub: "reports on file",    accent: "redDeep" },
  { to: "/pm/equipment",      icon: Wrench,        title: "Equipment Pre-Op",    countKey: "equipment",  sub: "inspections on file", accent: "slate" },
  { to: "/pm/qaqc",           icon: ShieldCheck,   title: "QA / QC Inspections", countKey: "qaqc",       sub: "Records on your jobs", accent: "amber" },
  { to: "/pm/photos",         icon: ImageIcon,     title: "Job Photos",          countKey: null,         sub: "All photos by job & week", accent: "rose" },
  { to: "/pm/field-leadership", icon: UserCheck,   title: "Field Leadership",    countKey: null,         sub: "Crew docs · my jobs only", accent: "amber" },
  { to: "/ops-training?portal=pm", icon: GraduationCap, title: "Training & Guides", countKey: null,    sub: "Operator guides · PDF download", accent: "slate" },
];

function PmTile({ to, icon: Icon, title, count, sub, accent, testId }) {
  const accentCls =
    accent === "red"     ? "border-red-700 bg-red-700"
    : accent === "amber" ? "border-amber-600 bg-amber-600"
    : accent === "redDeep" ? "border-red-900 bg-red-900"
    : accent === "rose"  ? "border-rose-700 bg-rose-700"
    : "border-slate-800 bg-slate-800";
  return (
    <Link
      to={to}
      className="group relative bg-white border-2 border-slate-200 hover:border-amber-600 hover:shadow-lg rounded-md p-4 sm:p-5 transition-all duration-150 hover:-translate-y-0.5 flex flex-col"
      data-testid={testId}
    >
      <div className={`inline-flex items-center justify-center w-10 h-10 rounded-md ${accentCls} text-white mb-3`}>
        <Icon className="w-5 h-5" />
      </div>
      <h3 className="font-display text-base sm:text-lg font-black tracking-tight text-slate-900">{title}</h3>
      <div className="mt-3 pt-2 border-t border-slate-100 flex items-end justify-between">
        <div>
          <div className="font-display text-2xl font-black text-slate-900 leading-none">
            {count == null ? "—" : count}
          </div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 mt-1">{sub}</div>
        </div>
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-amber-700 font-bold flex items-center gap-1 group-hover:gap-2 transition-all">
          Open <ArrowRight className="w-3 h-3" />
        </div>
      </div>
    </Link>
  );
}

export default function PmHub() {
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        // Mirror the per-resource fetch the old PmHub used — every list
        // route already filters by PM scope server-side, so .length is the
        // count for tiles. Failed calls fall back to 0 so the page never
        // dies on a partial outage.
        const [insp, mtg, jha, tb, inc, dr, eq, qa] = await Promise.all([
          api.get("/inspections").catch(() => ({ data: [] })),
          api.get("/meetings").catch(() => ({ data: [] })),
          api.get("/job-hazard-plans").catch(() => ({ data: [] })),
          api.get("/trench-boxes").catch(() => ({ data: [] })),
          api.get("/incidents").catch(() => ({ data: [] })),
          api.get("/daily-reports").catch(() => ({ data: [] })),
          api.get("/equipment-inspections").catch(() => ({ data: [] })),
          api.get("/qaqc-inspections").catch(() => ({ data: [] })),
        ]);
        const len = (x) => (Array.isArray(x?.data) ? x.data.length : 0);
        setCounts({
          inspections: len(insp), meetings: len(mtg), jhaPlans: len(jha),
          trenchBoxes: len(tb), incidents: len(inc), daily: len(dr),
          equipment: len(eq), qaqc: len(qa),
        });
      } catch { /* tiles still render with em-dash */ }
      setLoading(false);
    })();
  }, []);

  return (
    <PmShell
      title="Overview"
      section="overview"
      intro={
        <div className="flex items-start gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-amber-600 text-white shrink-0">
            <Briefcase className="w-5 h-5" />
          </div>
          <div className="text-sm text-slate-700 leading-relaxed">
            Welcome to the PM Portal. The forms below cover the day-to-day — Daily Reports,
            Inspections, Incidents, Photos, Field Leadership records, and more — scoped to
            jobs assigned to you. Use the sidebar (left, or hamburger on mobile) to dig into
            Active Jobs, Equipment Fleet, People, Suppliers, Posters, Email Routing, and
            Compliance Exports. System recovery and access-control tools remain Admin-only.
          </div>
        </div>
      }
    >
      {loading ? (
        <div className="py-16 flex items-center justify-center text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading…
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 mt-5" data-testid="pm-tile-grid">
          {FORM_TILES.map((t) => (
            <PmTile
              key={t.to}
              to={t.to}
              icon={t.icon}
              title={t.title}
              count={t.countKey ? counts[t.countKey] : null}
              sub={t.sub}
              accent={t.accent}
              testId={`pm-tile-${t.to.split("/").pop()}`}
            />
          ))}
        </div>
      )}
    </PmShell>
  );
}
