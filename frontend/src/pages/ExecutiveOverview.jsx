// src/pages/ExecutiveOverview.jsx
// TRACK 15.44 · Read-only Executive Overview.
//
// Doctrine (per directive): NOT a dashboard. NOT analytics. NOT BI.
// This is a 6-tile attention surface composed entirely from existing
// certified backend data via a single thin aggregator endpoint:
//     GET /api/admin/executive/overview
//
// Hard rules respected:
//   * No new collections, schemas, notifications, or background jobs.
//   * No AI summaries. No forecasting. No charting libraries.
//   * Read-only. No write actions on this page.
//
// Goal: an executive understands company health in <30 seconds.

import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { AlertTriangle, CheckCircle2, AlertOctagon, RefreshCw } from "lucide-react";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";
// TRACK 28.08 · Phase 15 fix — mount the shared PortalShell so this
// route participates in the responsive contract (mobile ••• menu,
// H1, breadcrumb, sidebar). Was previously a raw <div>.
import { PortalShell } from "@/design-system";
import SideNavV3 from "@/components/admin/sidebar/SideNavV3";
import AdminBreadcrumb from "@/components/admin/AdminBreadcrumb";

const API = process.env.REACT_APP_BACKEND_URL;

const VERDICT_THEME = {
  GREEN:  { bg: "bg-emerald-50",  bar: "bg-emerald-600",  text: "text-emerald-900",  label: "HEALTHY",        icon: CheckCircle2 },
  YELLOW: { bg: "bg-amber-50",    bar: "bg-amber-500",    text: "text-amber-900",    label: "NEEDS ATTENTION", icon: AlertTriangle },
  RED:    { bg: "bg-red-50",      bar: "bg-red-600",      text: "text-red-900",      label: "ACTION REQUIRED", icon: AlertOctagon },
};

function fmt(n) {
  return Number.isFinite(n) ? n.toLocaleString() : "—";
}

function Tile({ title, count, countTone = "slate", description, lines, sources, drillTo, testid }) {
  const toneClasses = {
    slate:  "text-slate-900",
    amber:  "text-amber-700",
    red:    "text-red-700",
    green:  "text-emerald-700",
    blue:   "text-blue-700",
  };
  return (
    <div
      className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
      data-testid={testid}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="text-xs font-mono uppercase tracking-widest text-slate-500">{title}</div>
          <div className={`mt-2 text-5xl font-extrabold leading-none ${toneClasses[countTone] || toneClasses.slate}`}>
            {fmt(count)}
          </div>
          <div className="mt-1 text-sm text-slate-600">{description}</div>
        </div>
      </div>
      {Array.isArray(lines) && lines.length > 0 && (
        <ul className="mt-4 space-y-1.5 text-sm text-slate-700">
          {lines.map((l, i) => (
            <li key={i} className="leading-snug">{l}</li>
          ))}
        </ul>
      )}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
        <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
          Source: {(sources || []).join(" · ") || "—"}
        </div>
        {drillTo && (
          <Link to={drillTo} className="text-xs font-mono uppercase tracking-wider text-blue-700 hover:text-blue-900">
            DRILL →
          </Link>
        )}
      </div>
    </div>
  );
}

export default function ExecutiveOverview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [tookMs, setTookMs] = useState(null);

  const load = async () => {
    setLoading(true);
    setErr(null);
    const t0 = performance.now();
    try {
      const r = await fetch(`${API}/api/admin/executive/overview`, {
        headers: buildScopedPortalAuthHeaders(["admin"]),
      });
      const t1 = performance.now();
      setTookMs(Math.round(t1 - t0));
      if (!r.ok) {
        setErr(`HTTP ${r.status}`);
        return;
      }
      setData(await r.json());
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        pageTitle="Executive Overview"
        subtitle="Read-only · attention surface for executives"
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <div className="p-8 text-slate-600" data-testid="executive-overview-loading">
          Loading executive overview…
        </div>
      </PortalShell>
    );
  }
  if (err || !data) {
    return (
      <PortalShell
        portalName="MASCI"
        portalRole="Admin"
        pageTitle="Executive Overview"
        subtitle="Read-only · attention surface for executives"
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <div className="p-8 text-red-700" data-testid="executive-overview-error">
          Failed to load executive overview: {err || "no data"}
        </div>
      </PortalShell>
    );
  }

  const t = data.tiles || {};
  const theme = VERDICT_THEME[data.verdict] || VERDICT_THEME.YELLOW;
  const VerdictIcon = theme.icon;

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Admin"
      pageTitle="Executive Overview"
      subtitle={`Read-only · v${data.foundation_version} · attention surface`}
      primaryActions={
        <div className="flex flex-wrap items-center gap-2 min-w-0">
          <Link
            to="/admin"
            className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 bg-white rounded-md text-xs font-semibold text-slate-800 hover:bg-slate-100 shrink-0"
            data-testid="executive-overview-back-adminos"
          >
            ← Admin OS
          </Link>
          <button
            onClick={load}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100 shrink-0"
            data-testid="executive-refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      }
      sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
    >
      <AdminBreadcrumb
        crumbs={[{ label: "Executive Overview" }]}
        testidPrefix="executive-overview-breadcrumb"
      />
      <div data-testid="executive-overview" className="min-w-0">
      {/* HEADER + VERDICT BAR */}
      <div className={`rounded-lg ${theme.bg} border-l-4 ${theme.bar.replace("bg-", "border-")} p-5 mb-6`}>
        <div className="flex flex-wrap items-center justify-between gap-4 min-w-0">
          <div className="flex items-center gap-3 min-w-0">
            <VerdictIcon className={`w-9 h-9 ${theme.text} shrink-0`} />
            <div className="min-w-0">
              <div className={`text-2xl font-extrabold ${theme.text}`} data-testid="executive-verdict">
                {theme.label}
              </div>
              <div className={`text-sm ${theme.text} opacity-80`}>
                Executive Overview · v{data.foundation_version}
              </div>
              {/* TRACK 15.46 · FR-02 · "Why RED?" deterministic reasons */}
              {Array.isArray(data.verdict_reasons) && data.verdict_reasons.length > 0 && (
                <ul
                  className="mt-2 text-sm leading-snug list-disc list-inside opacity-90"
                  data-testid="executive-verdict-reasons"
                >
                  {data.verdict_reasons.map((r, i) => (
                    <li key={i} data-testid={`executive-verdict-reason-${i}`}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
        <div className="mt-2 text-[11px] font-mono uppercase tracking-wider text-slate-500">
          Generated {formatPlatformTime(data.generated_at)} · Loaded in {tookMs}ms
        </div>
      </div>

      {/* 6 TILES */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Tile
          testid="tile-jobs"
          title="Jobs Requiring Attention"
          count={t.jobs?.total_attention_jobs || 0}
          countTone={(t.jobs?.total_attention_jobs || 0) > 0 ? "amber" : "green"}
          description="Active projects flagged by DR cadence + open incidents"
          lines={(t.jobs?.top_jobs || []).slice(0, 5).map((j) => (
            <span key={j.project_number}>
              <strong>{j.project_number}</strong>
              <span className="text-slate-500"> · {(j.reasons || []).join(" · ")}</span>
            </span>
          ))}
          sources={t.jobs?.source_modules}
          drillTo="/admin/jobs"
        />

        <Tile
          testid="tile-overdue"
          title="Overdue Operational Items"
          count={(t.overdue?.overdue_corrective_actions || 0) + (t.overdue?.stale_projects_no_dr_in_3d || 0)}
          countTone={
            ((t.overdue?.overdue_corrective_actions || 0) + (t.overdue?.stale_projects_no_dr_in_3d || 0)) > 0
              ? "amber" : "green"
          }
          description="Corrective actions past due + stale DR cadence"
          lines={[
            <span key="capa"><strong>{fmt(t.overdue?.overdue_corrective_actions)}</strong> overdue corrective actions</span>,
            <span key="dr"><strong>{fmt(t.overdue?.stale_projects_no_dr_in_3d)}</strong> projects · no DR in 3+ days</span>,
            ...((t.overdue?.stale_projects_sample || []).slice(0, 3).map((p, i) => (
              <span key={`p-${i}`} className="text-slate-500 text-xs">↳ {p}</span>
            ))),
          ]}
          sources={t.overdue?.source_modules}
          drillTo="/admin/qaqc"
        />

        <Tile
          testid="tile-staffing"
          title="Staffing Issues"
          count={(t.staffing?.projects_missing_pm || 0) + (t.staffing?.projects_missing_foreman || 0)}
          countTone={
            ((t.staffing?.projects_missing_pm || 0) + (t.staffing?.projects_missing_foreman || 0)) > 0
              ? "amber" : "green"
          }
          description={`Across ${fmt(t.staffing?.active_projects_count)} active projects (7-day DR window)`}
          lines={[
            <span key="pm"><strong>{fmt(t.staffing?.projects_missing_pm)}</strong> projects missing a PM</span>,
            <span key="fm"><strong>{fmt(t.staffing?.projects_missing_foreman)}</strong> projects missing a Foreman</span>,
            ...((t.staffing?.projects_missing_pm_sample || []).slice(0, 2).map((p, i) => (
              <span key={`pm-${i}`} className="text-slate-500 text-xs">↳ no PM · {p}</span>
            ))),
          ]}
          sources={t.staffing?.source_modules}
          drillTo="/admin/jobs"
        />

        <Tile
          testid="tile-equipment"
          title="Equipment Issues"
          count={(t.equipment?.out_of_service_units || 0) + (t.equipment?.open_defects || 0)}
          countTone={
            (t.equipment?.out_of_service_units || 0) > 0 || (t.equipment?.active_high_severity_holds || 0) > 0
              ? "red" : ((t.equipment?.monitor_units || 0) > 0 ? "amber" : "green")
          }
          description="Out-of-service units + open fleet defects"
          lines={[
            <span key="oos"><strong>{fmt(t.equipment?.out_of_service_units)}</strong> units out of service</span>,
            <span key="mon"><strong>{fmt(t.equipment?.monitor_units)}</strong> units on monitor</span>,
            <span key="def"><strong>{fmt(t.equipment?.open_defects)}</strong> open fleet defects</span>,
            <span key="holds"><strong>{fmt(t.equipment?.active_asset_holds_total)}</strong> active asset holds ({fmt(t.equipment?.active_high_severity_holds)} high-severity)</span>,
          ]}
          sources={t.equipment?.source_modules}
          drillTo="/equipment"
        />

        <Tile
          testid="tile-safety"
          title="Safety Attention Items"
          count={(t.safety?.unresolved_incidents || 0) + (t.safety?.unresolved_corrective_actions || 0)}
          countTone={
            (t.safety?.wv_incidents_90d || 0) > 0 ? "red" :
            (t.safety?.training_overdue || 0) > 0 ? "red" :
            (t.safety?.unresolved_incidents || 0) > 0 ? "red" :
            (t.safety?.unresolved_corrective_actions || 0) > 0 ? "amber" : "green"
          }
          description="Unresolved incidents + open CAPAs + workplace violence + public interaction + retraining"
          lines={[
            <span key="inc"><strong>{fmt(t.safety?.unresolved_incidents)}</strong> unresolved incidents</span>,
            <span key="capa"><strong>{fmt(t.safety?.unresolved_corrective_actions)}</strong> open corrective actions</span>,
            <span key="trench"><strong>{fmt(t.safety?.active_trench_safety_holds)}</strong> active trench-safety holds</span>,
            // TRACK 15.48 · Workplace-violence + Public-Interaction visibility.
            <span key="wv" data-testid="tile-safety-wv" className={(t.safety?.wv_incidents_90d || 0) > 0 ? "text-red-700 font-bold" : ""}>
              <strong>{fmt(t.safety?.wv_incidents_90d)}</strong> workplace-violence incidents (90d)
            </span>,
            <span key="pi" data-testid="tile-safety-public-interaction" className={(t.safety?.public_interaction_30d || 0) > 0 ? "text-amber-700 font-medium" : ""}>
              <strong>{fmt(t.safety?.public_interaction_30d)}</strong> public-interaction incidents (30d)
            </span>,
            // TRACK 15.50 · Recurrence-prevention training compliance.
            <span key="tr_req" data-testid="tile-safety-training-required">
              <strong>{fmt(t.safety?.training_required)}</strong> incident-triggered retraining required
            </span>,
            <span key="tr_done" data-testid="tile-safety-training-completed">
              <strong>{fmt(t.safety?.training_completed)}</strong> retraining completed
            </span>,
            <span key="tr_ovd" data-testid="tile-safety-training-overdue" className={(t.safety?.training_overdue || 0) > 0 ? "text-red-700 font-bold" : ""}>
              <strong>{fmt(t.safety?.training_overdue)}</strong> retraining overdue
            </span>,
          ]}
          sources={t.safety?.source_modules}
          drillTo="/safety"
        />

        <Tile
          testid="tile-activity"
          title="Activity Snapshot (Today)"
          count={
            (t.activity?.daily_reports_today || 0) +
            (t.activity?.safety_meetings_today || 0) +
            (t.activity?.jhas_today || 0) +
            (t.activity?.equipment_inspections_today || 0)
          }
          countTone="blue"
          description="Is the company operating today?"
          lines={[
            <span key="dr"><strong>{fmt(t.activity?.daily_reports_today)}</strong> Daily Reports submitted today</span>,
            <span key="dry" className="text-slate-500 text-xs">↳ vs <strong>{fmt(t.activity?.daily_reports_yesterday)}</strong> yesterday</span>,
            <span key="mtg"><strong>{fmt(t.activity?.safety_meetings_today)}</strong> Safety Meetings · <strong>{fmt(t.activity?.jhas_today)}</strong> JHAs</span>,
            <span key="ins"><strong>{fmt(t.activity?.equipment_inspections_today)}</strong> Equipment Inspections</span>,
          ]}
          sources={t.activity?.source_modules}
          drillTo="/daily-reports"
        />
      </div>

      {/* TRACEABILITY FOOTER */}
      <div className="mt-8 text-[10px] font-mono uppercase tracking-wider text-slate-400 text-center">
        Read-only · No new collections · No background jobs · No AI · Data from existing certified records only.
      </div>
      </div>
    </PortalShell>
  );
}
