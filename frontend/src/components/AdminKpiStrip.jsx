// AdminKpiStrip.jsx — iter91 + iter92
//
// Records-on-file dashboard tiles for the Admin Overview. Two sections:
//
//   1. SAFETY & FIELD FORMS — the 8 modules submitted by crews + PMs:
//      Daily Reports · Site Inspections · Safety Meetings · Incident
//      Reports · Equipment Pre-Op · Job Hazard Plans · Trench Box Data ·
//      QA/QC
//
//   2. LEADERSHIP & MEDIA — the 2 supervisor-side modules:
//      Field Leadership records (write-ups, coaching, attendance,
//      terminations, evaluations, etc. — single tile rolls them all up,
//      kind-by-kind breakdown shown in the title attribute)
//      Job Photos (the curated gallery index)
//
// Iter92 added the leadership + job photos tiles after user pointed out
// the iter91 strip was still missing whole-platform visibility.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClipboardList, FileText, Users, AlertOctagon, Wrench,
  ShieldCheck, Container, ClipboardCheck, UserCog, Camera,
} from "lucide-react";
import { api } from "@/lib/api";

const SAFETY_TILES = [
  ["daily", "Daily Reports", "report on file", "reports on file", "/daily-reports", FileText, "amber"],
  ["inspections", "Site Inspections", "report on file", "reports on file", "/inspections", ClipboardList, "red"],
  ["meetings", "Safety Meetings", "meeting logged", "meetings logged", "/meetings", Users, "amber"],
  ["incidents", "Incident Reports", "report on file", "reports on file", "/incidents", AlertOctagon, "red"],
  ["equipment", "Equipment Pre-Op", "inspection on file", "inspections on file", "/equipment-inspections", Wrench, "amber"],
  ["jhaPlans", "Job Hazard Plans", "plan uploaded", "plans uploaded", "/job-hazard-plans", ShieldCheck, "amber"],
  ["trenchBoxes", "Trench Box Data", "box on file", "boxes on file", "/trench-boxes", Container, "amber"],
  ["qaqc", "QA/QC", "inspection on file", "inspections on file", "/qaqc-inspections", ClipboardCheck, "amber"],
];

const LEADERSHIP_KIND_LABELS = {
  writeup: "Write-ups",
  coaching: "Coaching notes",
  attendance: "Attendance",
  recognition: "Recognition",
  equipment_checkout: "Equipment checkouts",
  new_employee_eval: "New-hire evaluations",
  crew_eval: "Crew evaluations",
  promotion_recommendation: "Promotion recs",
  training_deficiency: "Training deficiencies",
  employee_termination: "Terminations",
  equipment_return: "Equipment returns",
};

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
  purple: {
    border: "border-slate-200 hover:border-purple-700",
    bg: "bg-white hover:bg-purple-50",
    chip: "bg-purple-700 text-white",
    num: "text-slate-900",
  },
  slate: {
    border: "border-slate-200 hover:border-slate-700",
    bg: "bg-white hover:bg-slate-50",
    chip: "bg-slate-800 text-white",
    num: "text-slate-900",
  },
};

function Tile({ to, icon: Icon, label, num, subLabel, accent, hoverTitle, testId }) {
  const a = ACCENT[accent] || ACCENT.amber;
  return (
    <Link
      to={to}
      className={`group block rounded-md border-2 ${a.border} ${a.bg} p-3 transition-colors`}
      data-testid={testId}
      title={hoverTitle}
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
}

export default function AdminKpiStrip() {
  const [counts, setCounts] = useState({});
  const [leadership, setLeadership] = useState({ count: null, by_kind: {} });
  const [photos, setPhotos] = useState({ count: null });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [insp, mtgs, jhaPlans, trench, incs, daily, eq, qaqc, fl, jp] =
          await Promise.all([
            api.get("/inspections").catch(() => ({ data: [] })),
            api.get("/meetings").catch(() => ({ data: [] })),
            api.get("/job-hazard-plans").catch(() => ({ data: [] })),
            api.get("/trench-boxes").catch(() => ({ data: [] })),
            api.get("/incidents").catch(() => ({ data: [] })),
            api.get("/daily-reports").catch(() => ({ data: [] })),
            api.get("/equipment-inspections").catch(() => ({ data: [] })),
            api.get("/qaqc-inspections").catch(() => ({ data: [] })),
            api.get("/field-leadership", { params: { limit: 1 } }).catch(() => null),
            api.get("/job-photos", { params: { limit: 1 } }).catch(() => null),
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
        // Field leadership — rolled up across every "kind".
        // counts_by_kind comes back even when items are limited.
        if (fl?.data?.counts_by_kind) {
          const byKind = fl.data.counts_by_kind || {};
          const total = Object.values(byKind).reduce((s, n) => s + (n || 0), 0);
          setLeadership({ count: total, by_kind: byKind });
        } else {
          setLeadership({ count: 0, by_kind: {} });
        }
        // Job photos — the public list endpoint returns {items, count}.
        if (jp?.data?.count != null) {
          setPhotos({ count: jp.data.count });
        } else if (Array.isArray(jp?.data?.items)) {
          setPhotos({ count: jp.data.items.length });
        } else {
          setPhotos({ count: 0 });
        }
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, []);

  // Build tooltip showing FL kind breakdown ("Write-ups: 3 · Coaching: 5 · …")
  const leadershipTitle = (() => {
    const byKind = leadership.by_kind || {};
    const present = Object.entries(byKind).filter(([, n]) => n > 0);
    if (!present.length) return "No field-leadership records on file yet.";
    return present
      .map(([k, n]) => `${LEADERSHIP_KIND_LABELS[k] || k}: ${n}`)
      .join(" · ");
  })();

  return (
    <div className="space-y-4" data-testid="admin-kpi-strip">
      {/* Section 1 — Safety & Field forms */}
      <section>
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2">
          Safety & Field forms — Records on file
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
          {SAFETY_TILES.map(([key, label, singular, plural, to, Icon, accent]) => {
            const c = counts[key];
            const num = loading ? "—" : (c ?? 0);
            const subLabel = c === 1 ? singular : plural;
            return (
              <Tile
                key={key}
                to={to}
                icon={Icon}
                label={label}
                num={num}
                subLabel={subLabel}
                accent={accent}
                testId={`admin-kpi-${key}`}
              />
            );
          })}
        </div>
      </section>

      {/* Section 2 — Leadership & Media */}
      <section>
        <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500 font-bold mb-2">
          Leadership & Media — Records on file
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2.5">
          <Tile
            to="/leadership"
            icon={UserCog}
            label="Field Leadership"
            num={loading ? "—" : (leadership.count ?? 0)}
            subLabel={
              (leadership.count ?? 0) === 1
                ? "supervisor record"
                : "supervisor records"
            }
            accent="purple"
            hoverTitle={leadershipTitle}
            testId="admin-kpi-leadership"
          />
          <Tile
            to="/job-photos"
            icon={Camera}
            label="Job Photos"
            num={loading ? "—" : (photos.count ?? 0)}
            subLabel={(photos.count ?? 0) === 1 ? "photo indexed" : "photos indexed"}
            accent="slate"
            hoverTitle="Curated photo gallery — Daily Report attachments + Site Inspection + Incident + other module photos"
            testId="admin-kpi-job-photos"
          />
        </div>
      </section>
    </div>
  );
}
