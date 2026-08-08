import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { PortfolioIntelligenceWorkspace } from "@/components/project_controls/PortfolioIntelligenceWorkspace";
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

export default function ExecutiveOverview() {
  const { t } = useT();
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);

  const load = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    try {
      const portfolio = await fetchAdminPortfolioIntelligence({ forceRefresh });
      setWorkspace(portfolio || null);
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