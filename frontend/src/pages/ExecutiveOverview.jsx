import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import { PortfolioIntelligenceWorkspace } from "@/components/project_controls/PortfolioIntelligenceWorkspace";
import {
  downloadAdminPortfolioIntelligenceExport,
  fetchAdminPortfolioIntelligence,
  fetchProjectHealthSnapshot,
  refreshAdminPortfolioIntelligence,
} from "@/lib/projectControlsApi";


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
  const [workspace, setWorkspace] = useState(null);
  const [projectHealth, setProjectHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);

  const load = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    try {
      const [portfolio, health] = await Promise.all([
        fetchAdminPortfolioIntelligence({ forceRefresh }),
        fetchProjectHealthSnapshot(),
      ]);
      setWorkspace(portfolio || null);
      setProjectHealth(health || null);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not load portfolio intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  const refresh = async () => {
    setWorking(true);
    try {
      const [portfolio, health] = await Promise.all([
        refreshAdminPortfolioIntelligence(),
        fetchProjectHealthSnapshot(),
      ]);
      setWorkspace(portfolio || null);
      setProjectHealth(health || null);
      toast.success("Portfolio evidence refreshed.");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not refresh portfolio intelligence.");
    } finally {
      setWorking(false);
    }
  };

  const exportCsv = async () => {
    setWorking(true);
    try {
      const response = await downloadAdminPortfolioIntelligenceExport();
      downloadResponseFile(response, "executive-portfolio-intelligence.csv");
      toast.success("Portfolio CSV downloaded.");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not export portfolio intelligence.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <AdminRouteShell
      pageTitle="Portfolio Intelligence"
      subtitle="Cross-project cost, schedule, commitments, and clear drill-back"
      crumbs={[{ label: "Executive Oversight" }, { label: "Portfolio Intelligence" }]}
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
      <PortfolioIntelligenceWorkspace
        mode="executive"
        workspace={workspace}
        projectHealth={projectHealth}
        loading={loading}
        working={working}
        onRefresh={refresh}
        onExport={exportCsv}
      />
    </AdminRouteShell>
  );
}