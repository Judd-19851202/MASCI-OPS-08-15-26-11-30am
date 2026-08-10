import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { CircleHelp } from "lucide-react";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { PortfolioIntelligenceWorkspace } from "@/components/project_controls/PortfolioIntelligenceWorkspace";
import { api } from "@/lib/api";
import { buildKpiHelpContent } from "@/lib/kpiMetadata";
import {
  downloadAdminPortfolioIntelligenceExport,
  fetchAdminPortfolioIntelligence,
  refreshAdminPortfolioIntelligence,
} from "@/lib/projectControlsApi";
import { useT } from "@/lib/i18n";


function fileNameFromResponse(response, fallback) {
  const disposition = response?.headers?.["content-disposition"] || "";
  const match = disposition.match(/filename="?([^\"]+)"?/i);
  return match?.[1] || fallback;
}

function downloadResponseFile(response, fallback) {
  const blob = new Blob([response.data], { type: response.data?.type || "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileNameFromResponse(response, fallback);
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.URL.revokeObjectURL(url);
}

function InlineKpiHelp({ metadata, fallbackLabel, testId }) {
  const help = buildKpiHelpContent(metadata, fallbackLabel);
  if (!help) return null;
  return (
    <span className="inline-flex items-center text-slate-400" title={help.description} data-testid={testId}>
      <CircleHelp className="h-3.5 w-3.5" aria-hidden />
      <span className="sr-only">{fallbackLabel} definition</span>
    </span>
  );
}

function ExecutiveTile({ id, label, value, subline, metadata }) {
  return (
    <div className="rounded-sm border border-slate-300 bg-white p-4" data-testid={`executive-overview-tile-${id}`}>
      <div className="flex items-center gap-2">
        <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{label}</div>
        <InlineKpiHelp metadata={metadata} fallbackLabel={label} testId={`executive-overview-tile-${id}-help`} />
      </div>
      <div className="mt-2 font-display text-3xl font-black tracking-tight text-slate-950" data-testid={`executive-overview-tile-${id}-value`}>{value}</div>
      <p className="mt-2 text-sm text-slate-600" data-testid={`executive-overview-tile-${id}-subline`}>{subline}</p>
    </div>
  );
}

export default function ExecutiveOverview() {
  const { t } = useT();
  const [workspace, setWorkspace] = useState(null);
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);

  const load = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    try {
      const [portfolio, overviewResp] = await Promise.all([
        fetchAdminPortfolioIntelligence({ forceRefresh }),
        api.get(`/admin/executive/overview${forceRefresh ? "?refresh=1" : ""}`),
      ]);
      setWorkspace(portfolio || null);
      setOverview(overviewResp?.data || null);
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not load portfolio performance."));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    load(false);
  }, [load]);

  const refresh = async () => {
    setWorking(true);
    try {
      const portfolio = await refreshAdminPortfolioIntelligence();
      setWorkspace(portfolio || null);
      toast.success(t("Portfolio data refreshed."));
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not refresh portfolio performance."));
    } finally {
      setWorking(false);
    }
  };

  const exportCsv = async () => {
    setWorking(true);
    try {
      const response = await downloadAdminPortfolioIntelligenceExport();
      downloadResponseFile(response, "executive-portfolio-intelligence.csv");
      toast.success(t("Portfolio CSV downloaded."));
    } catch (error) {
      toast.error(error?.response?.data?.detail || t("Could not export portfolio performance."));
    } finally {
      setWorking(false);
    }
  };

  return (
    <AdminRouteShell
      pageTitle={t("Executive Overview")}
      subtitle={t("Start with the company-level picture, then open portfolio performance, immediate operations, or briefing readiness.")}
      crumbs={[{ label: t("Executive Oversight") }, { label: t("Executive Overview") }]}
      primaryActions={(
        <div className="flex flex-wrap gap-2">
          <Link to="/admin/command-center" className="inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="executive-overview-command-center-link">
            Operations Command Center
          </Link>
          <Link to="/admin/executive-operational-intelligence" className="inline-flex items-center rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="executive-overview-operational-link">
            Executive Operations Dashboard
          </Link>
        </div>
      )}
      testId="executive-overview-page"
    >
      <div className="mb-6 grid gap-4 lg:grid-cols-3" data-testid="executive-overview-purpose-grid">
        {overview?.tiles ? (
          <div className="lg:col-span-3 grid gap-3 sm:grid-cols-2 xl:grid-cols-3" data-testid="executive-overview-kpi-grid">
            <ExecutiveTile
              id="jobs"
              label={t("Jobs needing attention")}
              value={overview.tiles.jobs?.total_attention_jobs ?? 0}
              subline={`${overview.tiles.jobs?.active_asset_holds ?? 0} active asset hold(s)`}
              metadata={overview.tiles.jobs?.kpi_metadata}
            />
            <ExecutiveTile
              id="overdue"
              label={t("Overdue work")}
              value={overview.tiles.overdue?.overdue_corrective_actions ?? 0}
              subline={`${overview.tiles.overdue?.stale_projects_no_dr_in_3d ?? 0} project(s) stale on daily reports`}
              metadata={overview.tiles.overdue?.kpi_metadata}
            />
            <ExecutiveTile
              id="staffing"
              label={t("Staffing gaps")}
              value={(overview.tiles.staffing?.projects_missing_pm ?? 0) + (overview.tiles.staffing?.projects_missing_foreman ?? 0)}
              subline={`${overview.tiles.staffing?.active_projects_count ?? 0} active project(s) in staffing scope`}
              metadata={overview.tiles.staffing?.kpi_metadata}
            />
            <ExecutiveTile
              id="equipment"
              label={t("Equipment issues")}
              value={overview.tiles.equipment?.out_of_service_units ?? 0}
              subline={`${overview.tiles.equipment?.open_defects ?? 0} open defect(s)`}
              metadata={overview.tiles.equipment?.kpi_metadata}
            />
            <ExecutiveTile
              id="safety"
              label={t("Safety attention")}
              value={overview.tiles.safety?.unresolved_incidents ?? 0}
              subline={`${overview.tiles.safety?.unresolved_corrective_actions ?? 0} corrective action(s) still unresolved`}
              metadata={overview.tiles.safety?.kpi_metadata}
            />
            <ExecutiveTile
              id="activity"
              label={t("Today’s activity")}
              value={overview.tiles.activity?.daily_reports_today ?? 0}
              subline={`${(overview.tiles.activity?.safety_meetings_today ?? 0) + (overview.tiles.activity?.jhas_today ?? 0) + (overview.tiles.activity?.equipment_inspections_today ?? 0)} meeting/JHA/inspection events today`}
              metadata={overview.tiles.activity?.kpi_metadata}
            />
          </div>
        ) : null}
        <Link to="/admin/command-center" className="rounded-sm border border-slate-300 bg-white p-5 text-left transition-colors hover:border-slate-900" data-testid="executive-overview-purpose-command-center">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{t("Operations Command Center")}</div>
          <div className="mt-2 font-display text-2xl font-black tracking-tight text-slate-950">{t("Immediate action right now")}</div>
          <p className="mt-2 text-sm text-slate-600">{t("Open the live incident, constraint, and operational queues that need intervention now.")}</p>
        </Link>
        <Link to="/admin/executive-operational-intelligence" className="rounded-sm border border-slate-300 bg-white p-5 text-left transition-colors hover:border-slate-900" data-testid="executive-overview-purpose-operations-dashboard">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-500">{t("Executive Operations Dashboard")}</div>
          <div className="mt-2 font-display text-2xl font-black tracking-tight text-slate-950">{t("What changed this period")}</div>
          <p className="mt-2 text-sm text-slate-600">{t("Review operating volume, briefing readiness, and enterprise coordination trends for the selected period.")}</p>
        </Link>
        <div className="rounded-sm border border-slate-900 bg-slate-950 p-5 text-white" data-testid="executive-overview-purpose-portfolio-performance">
          <div className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-300">{t("Portfolio Performance")}</div>
          <div className="mt-2 font-display text-2xl font-black tracking-tight">{t("Cross-project cost and schedule risk")}</div>
          <p className="mt-2 text-sm text-slate-200">{t("Use the section below to see which projects need leadership attention, why they moved, and what should happen next.")}</p>
        </div>
      </div>
      <PortfolioIntelligenceWorkspace
        mode="executive"
        workspace={workspace}
        loading={loading}
        working={working}
        onRefresh={refresh}
        onExport={exportCsv}
      />
    </AdminRouteShell>
  );
}