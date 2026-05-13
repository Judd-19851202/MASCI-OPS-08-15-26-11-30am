// AdminKpiStrip.jsx — iter91
//
// At-a-glance count tiles for the Admin Overview page. Mirrors the
// PM Hub's tile grid but in a compact strip layout — 8 forms x records
// on file, each clickable to its module dashboard.
//
// Why it lives here (not on each sub-section page):
// The Admin Overview is supposed to be the "glance at the platform"
// dashboard. Removing this strip during the iter83/84 reorg made the
// landing page feel empty. Restored in iter91 by user request.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClipboardList, FileText, Users, AlertOctagon, Wrench,
  ShieldCheck, Container, ClipboardCheck,
} from "lucide-react";
import { api } from "@/lib/api";

const TILES = [
  // [key, label, sub_singular, sub_plural, to, icon, accent]
  ["daily", "Daily Reports", "report on file", "reports on file", "/daily-reports", FileText, "amber"],
  ["inspections", "Site Inspections", "report on file", "reports on file", "/inspections", ClipboardList, "red"],
  ["meetings", "Safety Meetings", "meeting logged", "meetings logged", "/meetings", Users, "amber"],
  ["incidents", "Incident Reports", "report on file", "reports on file", "/incidents", AlertOctagon, "red"],
  ["equipment", "Equipment Pre-Op", "inspection on file", "inspections on file", "/equipment-inspections", Wrench, "amber"],
  ["jhaPlans", "Job Hazard Plans", "plan uploaded", "plans uploaded", "/job-hazard-plans", ShieldCheck, "amber"],
  ["trenchBoxes", "Trench Box Data", "box on file", "boxes on file", "/trench-boxes", Container, "amber"],
  ["qaqc", "QA/QC", "inspection on file", "inspections on file", "/qaqc-inspections", ClipboardCheck, "amber"],
];

const ACCENT = {
  red: {
    border: "border-red-300 hover:border-red-700",
    bg: "bg-white hover:bg-red-50",
    chip: "bg-red-700 text-white",
    num: "text-red-700",
  },
  amber: {
    border: "border-slate-200 hover:border-amber-600",
    bg: "bg-white hover:bg-amber-50",
    chip: "bg-amber-600 text-white",
    num: "text-slate-900",
  },
};

export default function AdminKpiStrip() {
  const [counts, setCounts] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [insp, mtgs, jhaPlans, trench, incs, daily, eq, qaqc] = await Promise.all([
          api.get("/inspections").catch(() => ({ data: [] })),
          api.get("/meetings").catch(() => ({ data: [] })),
          api.get("/job-hazard-plans").catch(() => ({ data: [] })),
          api.get("/trench-boxes").catch(() => ({ data: [] })),
          api.get("/incidents").catch(() => ({ data: [] })),
          api.get("/daily-reports").catch(() => ({ data: [] })),
          api.get("/equipment-inspections").catch(() => ({ data: [] })),
          api.get("/qaqc-inspections").catch(() => ({ data: [] })),
        ]);
        if (!alive) return;
        setCounts({
          inspections: insp.data?.length ?? 0,
          meetings: mtgs.data?.length ?? 0,
          jhaPlans: jhaPlans.data?.length ?? 0,
          trenchBoxes: trench.data?.length ?? 0,
          incidents: incs.data?.length ?? 0,
          daily: daily.data?.length ?? 0,
          equipment: eq.data?.length ?? 0,
          qaqc: qaqc.data?.length ?? 0,
        });
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  return (
    <section className="mb-2" data-testid="admin-kpi-strip">
      <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2">
        Records on file
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
        {TILES.map(([key, label, singular, plural, to, Icon, accent]) => {
          const c = counts[key];
          const a = ACCENT[accent];
          const num = loading ? "—" : (c ?? 0);
          const subLabel = (c === 1) ? singular : plural;
          return (
            <Link
              key={key}
              to={to}
              className={`group block rounded-md border-2 ${a.border} ${a.bg} p-3 transition-colors`}
              data-testid={`admin-kpi-${key}`}
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <div className={`inline-flex items-center justify-center w-7 h-7 rounded ${a.chip}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <span className="font-mono text-[9px] uppercase tracking-[0.18em] text-slate-400 group-hover:text-slate-700 font-bold">
                  Open →
                </span>
              </div>
              <div className={`font-display text-2xl font-black leading-none ${a.num}`}>
                {num}
              </div>
              <div className="font-bold text-slate-900 text-sm mt-1 leading-tight truncate">
                {label}
              </div>
              <div className="text-[11px] text-slate-500 font-mono uppercase tracking-wide truncate">
                {subLabel}
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
