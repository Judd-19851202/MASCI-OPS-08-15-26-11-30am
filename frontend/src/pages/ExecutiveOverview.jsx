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
import { HelpTip } from "@/components/ui/HelpTip";
import { buildKpiHelpContent } from "@/lib/kpiMetadata";
import { useT } from "@/lib/i18n";

const API = process.env.REACT_APP_BACKEND_URL;

const VERDICT_THEME = {
  GREEN:  { bg: "bg-emerald-50",  bar: "bg-emerald-600",  text: "text-emerald-900",  label: "HEALTHY",        icon: CheckCircle2 },
  YELLOW: { bg: "bg-amber-50",    bar: "bg-amber-500",    text: "text-amber-900",    label: "NEEDS ATTENTION", icon: AlertTriangle },
  RED:    { bg: "bg-red-50",      bar: "bg-red-600",      text: "text-red-900",      label: "ACTION REQUIRED", icon: AlertOctagon },
};

function fmt(n) {
  return Number.isFinite(n) ? n.toLocaleString() : "—";
}

function translateExecutiveReason(value, t) {
  if (!value) return value;
  const text = String(value);
  if (/^No Daily Report in 3\+ days$/i.test(text)) return t("No Daily Report in 3+ days");
  let match = text.match(/^(\d+) open incident\(s\)$/i);
  if (match) return `${match[1]} ${t("open incident(s)")}`;
  match = text.match(/^(\d+) units out of service \(threshold > (\d+)\)$/i);
  if (match) return `${match[1]} ${t("units out of service")} (${t("threshold") } > ${match[2]})`;
  match = text.match(/^(\d+) unresolved incidents \(threshold > (\d+)\)$/i);
  if (match) return `${match[1]} ${t("unresolved incidents")} (${t("threshold")} > ${match[2]})`;
  match = text.match(/^(\d+) overdue corrective actions \(threshold > (\d+)\)$/i);
  if (match) return `${match[1]} ${t("overdue corrective actions")} (${t("threshold")} > ${match[2]})`;
  match = text.match(/^(\d+) projects with no DR in 3\+ days \(threshold > (\d+)\)$/i);
  if (match) return `${match[1]} ${t("projects with no DR in 3+ days")} (${t("threshold")} > ${match[2]})`;
  match = text.match(/^(\d+) open corrective actions \(threshold > (\d+)\)$/i);
  if (match) return `${match[1]} ${t("open corrective actions")} (${t("threshold")} > ${match[2]})`;
  match = text.match(/^(\d+) workplace-violence incident\(s\) in last 90 days$/i);
  if (match) return `${match[1]} ${t("workplace-violence incident(s) in last 90 days")}`;
  match = text.match(/^(\d+) public-interaction incidents in last 30 days \(threshold > (\d+)\)$/i);
  if (match) return `${match[1]} ${t("public-interaction incidents in last 30 days")} (${t("threshold")} > ${match[2]})`;
  return t(text);
}

function Tile({ title, count, countTone = "slate", description, lines, sources, drillTo, testid, metadata }) {
  const { t } = useT();
  const toneClasses = {
    slate:  "text-slate-900",
    amber:  "text-amber-700",
    red:    "text-red-700",
    green:  "text-emerald-700",
    blue:   "text-blue-700",
  };
  const help = buildKpiHelpContent(metadata, title);
  return (
    <div
      className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
      data-testid={testid}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-1.5">
            <div className="text-xs font-mono uppercase tracking-widest text-slate-500">{t(title)}</div>
            {help ? (
              <HelpTip
                label={help.label}
                body={help.body}
                testId={`${testid}-help`}
              />
            ) : null}
          </div>
          <div className={`mt-2 text-5xl font-extrabold leading-none ${toneClasses[countTone] || toneClasses.slate}`}>
            {fmt(count)}
          </div>
          <div className="mt-1 text-sm text-slate-600">{t(description)}</div>
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
          {t("Source")}: {(sources || []).join(" · ") || "—"}
        </div>
        {drillTo && (
          <Link to={drillTo} className="text-xs font-mono uppercase tracking-wider text-blue-700 hover:text-blue-900">
            {t("Drill")} →
          </Link>
        )}
      </div>
    </div>
  );
}

export default function ExecutiveOverview() {
  const { t } = useT();
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
        portalRole={t("Admin")}
        pageTitle={t("Executive Overview")}
        subtitle={t("Read-only · attention surface for executives")}
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <div className="p-8 text-slate-600" data-testid="executive-overview-loading">
          {t("Loading executive overview…")}
        </div>
      </PortalShell>
    );
  }
  if (err || !data) {
    return (
      <PortalShell
        portalName="MASCI"
        portalRole={t("Admin")}
        pageTitle={t("Executive Overview")}
        subtitle={t("Read-only · attention surface for executives")}
        sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
      >
        <div className="p-8 text-red-700" data-testid="executive-overview-error">
          {t("Failed to load executive overview")}: {err || t("no data")}
        </div>
      </PortalShell>
    );
  }

  const tiles = data.tiles || {};
  const theme = VERDICT_THEME[data.verdict] || VERDICT_THEME.YELLOW;
  const VerdictIcon = theme.icon;
  const verdictHelp = buildKpiHelpContent(data.kpi_metadata?.verdict, "Executive Verdict");

  return (
    <PortalShell
      portalName="MASCI"
      portalRole={t("Admin")}
      pageTitle={t("Executive Overview")}
      subtitle={`${t("Read-only")} · v${data.foundation_version} · ${t("attention surface")}`}
      primaryActions={
        <div className="flex flex-wrap items-center gap-2 min-w-0">
          <Link
            to="/admin"
            className="inline-flex items-center gap-2 px-3 py-1.5 border border-slate-300 bg-white rounded-md text-xs font-semibold text-slate-800 hover:bg-slate-100 shrink-0"
            data-testid="executive-overview-back-adminos"
          >
            ← {t("Admin OS")}
          </Link>
          <button
            onClick={load}
            className="inline-flex items-center gap-1.5 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100 shrink-0"
            data-testid="executive-refresh"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            {t("Refresh")}
          </button>
        </div>
      }
      sideNav={<SideNavV3 onOpenPalette={() => window.__masciAdminOpenPalette?.()} />}
    >
      <AdminBreadcrumb
        crumbs={[{ label: t("Executive Overview") }]}
        testidPrefix="executive-overview-breadcrumb"
      />
      <div data-testid="executive-overview" className="min-w-0">
      <section className="wp17-mission-banner mb-6" data-testid="executive-overview-mission-banner">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="wp17-kicker text-white/70">{t("Portal mission")}</div>
            <h2 className="mt-2 font-display text-xl font-black text-white">{t("Give leadership the shortest possible path to risk, not a second analytics maze.")}</h2>
            <p className="mt-2 max-w-3xl text-sm text-white/80">
              {t("Executive views now use the same shared work area while staying concise, role-appropriate, and operationally clear.")}
            </p>
          </div>
        </div>
      </section>

      {/* HEADER + VERDICT BAR */}
      <div className={`rounded-lg ${theme.bg} border-l-4 ${theme.bar.replace("bg-", "border-")} p-5 mb-6`}>
        <div className="flex flex-wrap items-center justify-between gap-4 min-w-0">
          <div className="flex items-center gap-3 min-w-0">
            <VerdictIcon className={`w-9 h-9 ${theme.text} shrink-0`} />
            <div className="min-w-0">
              <div className={`text-2xl font-extrabold ${theme.text}`} data-testid="executive-verdict">
                <span className="inline-flex items-center gap-2">
                  <span>{t(theme.label)}</span>
                  {verdictHelp ? (
                    <HelpTip
                      label={verdictHelp.label}
                      body={verdictHelp.body}
                      testId="executive-verdict-help"
                    />
                  ) : null}
                </span>
              </div>
              <div className={`text-sm ${theme.text} opacity-80`}>
                {t("Executive Overview")} · v{data.foundation_version}
              </div>
              {/* TRACK 15.46 · FR-02 · "Why RED?" deterministic reasons */}
              {Array.isArray(data.verdict_reasons) && data.verdict_reasons.length > 0 && (
                <ul
                  className="mt-2 text-sm leading-snug list-disc list-inside opacity-90"
                  data-testid="executive-verdict-reasons"
                >
                  {data.verdict_reasons.map((r, i) => (
                    <li key={i} data-testid={`executive-verdict-reason-${i}`}>{translateExecutiveReason(r, t)}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
        <div className="mt-2 text-[11px] font-mono uppercase tracking-wider text-slate-500">
          {t("Generated")} {formatPlatformTime(data.generated_at)} · {t("Loaded in")} {tookMs}ms
        </div>
      </div>

      {/* 6 TILES */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Tile
          testid="tile-jobs"
          title="Jobs Requiring Attention"
          count={tiles.jobs?.total_attention_jobs || 0}
          countTone={(tiles.jobs?.total_attention_jobs || 0) > 0 ? "amber" : "green"}
          description="Active projects flagged by DR cadence + open incidents"
          lines={(tiles.jobs?.top_jobs || []).slice(0, 5).map((j) => (
            <span key={j.project_number}>
              <strong>{j.project_number}</strong>
              <span className="text-slate-500"> · {(j.reasons || []).map((reason) => translateExecutiveReason(reason, t)).join(" · ")}</span>
            </span>
          ))}
          sources={tiles.jobs?.source_modules}
          metadata={tiles.jobs?.kpi_metadata}
          drillTo="/admin/jobs"
        />

        <Tile
          testid="tile-overdue"
          title="Overdue Operational Items"
          count={(tiles.overdue?.overdue_corrective_actions || 0) + (tiles.overdue?.stale_projects_no_dr_in_3d || 0)}
          countTone={
            ((tiles.overdue?.overdue_corrective_actions || 0) + (tiles.overdue?.stale_projects_no_dr_in_3d || 0)) > 0
              ? "amber" : "green"
          }
          description="Corrective actions past due + stale DR cadence"
          lines={[
            <span key="capa"><strong>{fmt(tiles.overdue?.overdue_corrective_actions)}</strong> {t("overdue corrective actions")}</span>,
            <span key="dr"><strong>{fmt(tiles.overdue?.stale_projects_no_dr_in_3d)}</strong> {t("projects · no DR in 3+ days")}</span>,
            ...((tiles.overdue?.stale_projects_sample || []).slice(0, 3).map((p, i) => (
              <span key={`p-${i}`} className="text-slate-500 text-xs">↳ {p}</span>
            ))),
          ]}
          sources={tiles.overdue?.source_modules}
          metadata={tiles.overdue?.kpi_metadata}
          drillTo="/admin/qaqc"
        />

        <Tile
          testid="tile-staffing"
          title="Staffing Issues"
          count={(tiles.staffing?.projects_missing_pm || 0) + (tiles.staffing?.projects_missing_foreman || 0)}
          countTone={
            ((tiles.staffing?.projects_missing_pm || 0) + (tiles.staffing?.projects_missing_foreman || 0)) > 0
              ? "amber" : "green"
          }
          description={`${t("Across")} ${fmt(tiles.staffing?.active_projects_count)} ${t("active projects (7-day DR window)")}`}
          lines={[
            <span key="pm"><strong>{fmt(tiles.staffing?.projects_missing_pm)}</strong> {t("projects missing a PM")}</span>,
            <span key="fm"><strong>{fmt(tiles.staffing?.projects_missing_foreman)}</strong> {t("projects missing a Foreman")}</span>,
            ...((tiles.staffing?.projects_missing_pm_sample || []).slice(0, 2).map((p, i) => (
              <span key={`pm-${i}`} className="text-slate-500 text-xs">↳ {t("no PM")} · {p}</span>
            ))),
          ]}
          sources={tiles.staffing?.source_modules}
          metadata={tiles.staffing?.kpi_metadata}
          drillTo="/admin/jobs"
        />

        <Tile
          testid="tile-equipment"
          title="Equipment Issues"
          count={(tiles.equipment?.out_of_service_units || 0) + (tiles.equipment?.open_defects || 0)}
          countTone={
            (tiles.equipment?.out_of_service_units || 0) > 0 || (tiles.equipment?.active_high_severity_holds || 0) > 0
              ? "red" : ((tiles.equipment?.monitor_units || 0) > 0 ? "amber" : "green")
          }
          description="Out-of-service units + open fleet defects"
          lines={[
            <span key="oos"><strong>{fmt(tiles.equipment?.out_of_service_units)}</strong> {t("units out of service")}</span>,
            <span key="mon"><strong>{fmt(tiles.equipment?.monitor_units)}</strong> {t("units on monitor")}</span>,
            <span key="def"><strong>{fmt(tiles.equipment?.open_defects)}</strong> {t("open fleet defects")}</span>,
            <span key="holds"><strong>{fmt(tiles.equipment?.active_asset_holds_total)}</strong> {t("active asset holds")} ({fmt(tiles.equipment?.active_high_severity_holds)} {t("high-severity")})</span>,
          ]}
          sources={tiles.equipment?.source_modules}
          metadata={tiles.equipment?.kpi_metadata}
          drillTo="/equipment"
        />

        <Tile
          testid="tile-safety"
          title="Safety Attention Items"
          count={(tiles.safety?.unresolved_incidents || 0) + (tiles.safety?.unresolved_corrective_actions || 0)}
          countTone={
            (tiles.safety?.wv_incidents_90d || 0) > 0 ? "red" :
            (tiles.safety?.training_overdue || 0) > 0 ? "red" :
            (tiles.safety?.unresolved_incidents || 0) > 0 ? "red" :
            (tiles.safety?.unresolved_corrective_actions || 0) > 0 ? "amber" : "green"
          }
          description="Unresolved incidents + open CAPAs + workplace violence + public interaction + retraining"
          lines={[
            <span key="inc"><strong>{fmt(tiles.safety?.unresolved_incidents)}</strong> {t("unresolved incidents")}</span>,
            <span key="capa"><strong>{fmt(tiles.safety?.unresolved_corrective_actions)}</strong> {t("open corrective actions")}</span>,
            <span key="trench"><strong>{fmt(tiles.safety?.active_trench_safety_holds)}</strong> {t("active trench-safety holds")}</span>,
            // TRACK 15.48 · Workplace-violence + Public-Interaction visibility.
            <span key="wv" data-testid="tile-safety-wv" className={(tiles.safety?.wv_incidents_90d || 0) > 0 ? "text-red-700 font-bold" : ""}>
              <strong>{fmt(tiles.safety?.wv_incidents_90d)}</strong> {t("workplace-violence incidents (90d)")}
            </span>,
            <span key="pi" data-testid="tile-safety-public-interaction" className={(tiles.safety?.public_interaction_30d || 0) > 0 ? "text-amber-700 font-medium" : ""}>
              <strong>{fmt(tiles.safety?.public_interaction_30d)}</strong> {t("public-interaction incidents (30d)")}
            </span>,
            // TRACK 15.50 · Recurrence-prevention training compliance.
            <span key="tr_req" data-testid="tile-safety-training-required">
              <strong>{fmt(tiles.safety?.training_required)}</strong> {t("incident-triggered retraining required")}
            </span>,
            <span key="tr_done" data-testid="tile-safety-training-completed">
              <strong>{fmt(tiles.safety?.training_completed)}</strong> {t("retraining completed")}
            </span>,
            <span key="tr_ovd" data-testid="tile-safety-training-overdue" className={(tiles.safety?.training_overdue || 0) > 0 ? "text-red-700 font-bold" : ""}>
              <strong>{fmt(tiles.safety?.training_overdue)}</strong> {t("retraining overdue")}
            </span>,
          ]}
          sources={tiles.safety?.source_modules}
          metadata={tiles.safety?.kpi_metadata}
          drillTo="/safety"
        />

        <Tile
          testid="tile-activity"
          title="Activity Snapshot (Today)"
          count={
            (tiles.activity?.daily_reports_today || 0) +
            (tiles.activity?.safety_meetings_today || 0) +
            (tiles.activity?.jhas_today || 0) +
            (tiles.activity?.equipment_inspections_today || 0)
          }
          countTone="blue"
          description="Is the company operating today?"
          lines={[
            <span key="dr"><strong>{fmt(tiles.activity?.daily_reports_today)}</strong> {t("Daily Reports submitted today")}</span>,
            <span key="dry" className="text-slate-500 text-xs">↳ {t("vs")} <strong>{fmt(tiles.activity?.daily_reports_yesterday)}</strong> {t("yesterday")}</span>,
            <span key="mtg"><strong>{fmt(tiles.activity?.safety_meetings_today)}</strong> {t("Safety Meetings")} · <strong>{fmt(tiles.activity?.jhas_today)}</strong> {t("JHAs")}</span>,
            <span key="ins"><strong>{fmt(tiles.activity?.equipment_inspections_today)}</strong> {t("Equipment Inspections")}</span>,
          ]}
          sources={tiles.activity?.source_modules}
          metadata={tiles.activity?.kpi_metadata}
          drillTo="/daily-reports"
        />
      </div>

      {/* TRACEABILITY FOOTER */}
      <div className="mt-8 text-[10px] font-mono uppercase tracking-wider text-slate-400 text-center">
        {t("Read-only · No new collections · No background jobs · No AI · Data from existing certified records only.")}
      </div>
      </div>
    </PortalShell>
  );
}
