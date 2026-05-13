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
  TrendingUp,
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

function Tile({ to, icon: Icon, label, num, subLabel, accent, hoverTitle, testId, weeklyDelta, alertBadge }) {
  const a = ACCENT[accent] || ACCENT.amber;
  return (
    <Link
      to={to}
      className={`group block rounded-md border-2 ${a.border} ${a.bg} p-3 transition-colors relative`}
      data-testid={testId}
      title={hoverTitle}
    >
      {/* Top-right alert badge — only shown when a tile has urgent items pending */}
      {alertBadge != null && alertBadge > 0 && (
        <div
          className="absolute -top-2 -right-2 min-w-[22px] h-[22px] px-1.5 rounded-full bg-red-700 text-white text-[10px] font-black font-mono flex items-center justify-center border-2 border-white shadow-sm"
          data-testid={`${testId}-alert-badge`}
          title={`${alertBadge} awaiting sign-off — click tile to review`}
        >
          {alertBadge > 99 ? "99+" : alertBadge}
        </div>
      )}
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
      <div className="text-[11px] text-slate-500 font-mono uppercase tracking-wide truncate flex items-center gap-1.5">
        <span className="truncate">{subLabel}</span>
        {weeklyDelta != null && weeklyDelta > 0 && (
          <span
            className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold normal-case tracking-normal text-[10px] shrink-0"
            data-testid={`${testId}-weekly-delta`}
            title={`${weeklyDelta} added in the last 7 days`}
          >
            <TrendingUp className="w-2.5 h-2.5" /> +{weeklyDelta} 7d
          </span>
        )}
      </div>
    </Link>
  );
}

export default function AdminKpiStrip() {
  const [counts, setCounts] = useState({});
  const [weeklyDelta, setWeeklyDelta] = useState({}); // per-tile +N this week
  const [pendingSignoff, setPendingSignoff] = useState(0); // PreOp FAILs still open
  const [leadership, setLeadership] = useState({ count: null, by_kind: {} });
  const [photos, setPhotos] = useState({ count: null });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      // Date fields used by each module for the "last 7 days" delta.
      // We try the canonical record_date column first, then fall back
      // to created_at. The arrays come back already sorted desc by date
      // so we just walk from index 0 until the date is older than the
      // 7-day window — no need to filter the entire array.
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

      const countWeek = (items, dateFields) => {
        if (!Array.isArray(items)) return 0;
        let n = 0;
        for (const item of items) {
          let raw = null;
          for (const f of dateFields) {
            if (item?.[f]) { raw = item[f]; break; }
          }
          if (!raw) continue;
          const d = new Date(raw);
          if (!isNaN(d.getTime()) && d >= sevenDaysAgo) n += 1;
        }
        return n;
      };

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
            api.get("/field-leadership", { params: { limit: 500 } }).catch(() => null),
            api.get("/job-photos", { params: { limit: 5000 } }).catch(() => null),
          ]);
        if (!alive) return;

        const dailyData = daily.data || [];
        const inspData = insp.data || [];
        const mtgsData = mtgs.data || [];
        const incsData = incs.data || [];
        const eqData = eq.data || [];
        const jhaPlansData = jhaPlans.data || [];
        const trenchData = trench.data || [];
        const qaqcData = qaqc.data || [];

        setCounts({
          inspections: inspData.length,
          meetings: mtgsData.length,
          jhaPlans: jhaPlansData.length,
          trenchBoxes: trenchData.length,
          incidents: incsData.length,
          daily: dailyData.length,
          equipment: eqData.length,
          qaqc: qaqcData.length,
        });

        // Iter93 — "+N 7d" delta per tile. We walk each list and count
        // how many records carry a created_at or record-date field that
        // falls inside the last 7 days. Cheap on the client; no extra
        // API calls.
        setWeeklyDelta({
          daily:       countWeek(dailyData,    ["report_date", "created_at"]),
          inspections: countWeek(inspData,     ["inspection_date", "created_at"]),
          meetings:    countWeek(mtgsData,     ["meeting_date", "created_at"]),
          incidents:   countWeek(incsData,     ["incident_date", "created_at"]),
          equipment:   countWeek(eqData,       ["inspection_date", "created_at"]),
          jhaPlans:    countWeek(jhaPlansData, ["created_at", "upload_date"]),
          trenchBoxes: countWeek(trenchData,   ["created_at"]),
          qaqc:        countWeek(qaqcData,     ["inspection_date", "created_at"]),
          leadership:  countWeek(fl?.data?.items, ["occurred_at", "created_at"]),
          photos:      countWeek(jp?.data?.items, ["record_date", "created_at"]),
        });

        // Iter93 — Equipment Pre-Op "⚠ N awaiting sign-off" badge.
        // Each inspection exposes ``fail_count`` (number of FAIL items)
        // and ``cleared`` (true once the shop has signed off every FAIL).
        // We count inspections that have at least one FAIL and are NOT
        // yet cleared — these are the rows admin should be looking at.
        const pending = eqData.filter(
          (r) => (r?.fail_count || 0) > 0 && r?.cleared !== true
        ).length;
        setPendingSignoff(pending);

        // Field leadership totals via counts_by_kind aggregate
        if (fl?.data?.counts_by_kind) {
          const byKind = fl.data.counts_by_kind || {};
          const total = Object.values(byKind).reduce((s, n) => s + (n || 0), 0);
          setLeadership({ count: total, by_kind: byKind });
        } else {
          setLeadership({ count: 0, by_kind: {} });
        }
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
                weeklyDelta={loading ? null : weeklyDelta[key]}
                // Only Equipment Pre-Op carries the failed-signoff alert
                alertBadge={key === "equipment" && !loading ? pendingSignoff : null}
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
            weeklyDelta={loading ? null : weeklyDelta.leadership}
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
            weeklyDelta={loading ? null : weeklyDelta.photos}
          />
        </div>
      </section>
    </div>
  );
}
