import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { PortalShell } from "@/design-system";
import PmSideNavV2 from "@/components/pm/sidebar/SideNavV2";
import { PortfolioIntelligenceWorkspace } from "@/components/project_controls/PortfolioIntelligenceWorkspace";
import {
  downloadPmPortfolioIntelligenceExport,
  fetchPmPortfolioIntelligence,
  fetchProjectHealthSnapshot,
  refreshPmPortfolioIntelligence,
} from "@/lib/projectControlsApi";
import { usePageTitle } from "@/lib/usePageTitle";


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

export default function PmPortfolioIntelligence() {
  usePageTitle("PM Portfolio Intelligence · MASCI");
  const [workspace, setWorkspace] = useState(null);
  const [projectHealth, setProjectHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);

  const load = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    try {
      const [portfolio, health] = await Promise.all([
        fetchPmPortfolioIntelligence({ forceRefresh }),
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
        refreshPmPortfolioIntelligence(),
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
      const response = await downloadPmPortfolioIntelligenceExport();
      downloadResponseFile(response, "pm-portfolio-intelligence.csv");
      toast.success("Portfolio CSV downloaded.");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not export portfolio intelligence.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <PortalShell
      portalName="MASCI"
      portalRole="Project Management"
      pageTitle="Portfolio Intelligence"
      subtitle="Cross-project visibility for cost, commitments, and schedule status in your scope"
      sideNav={<PmSideNavV2 />}
      primaryActions={(
        <div className="flex items-center gap-3">
          <Link to="/pm/command-center" className="text-xs font-mono uppercase tracking-widest text-slate-600 hover:text-slate-900" data-testid="pm-portfolio-command-center-link">
            PM Command Center
          </Link>
        </div>
      )}
    >
      <div className="max-w-7xl px-4 py-6 sm:px-6" data-testid="pm-portfolio-page">
        <PortfolioIntelligenceWorkspace
          mode="pm"
          workspace={workspace}
          projectHealth={projectHealth}
          loading={loading}
          working={working}
          onRefresh={refresh}
          onExport={exportCsv}
        />
      </div>
    </PortalShell>
  );
}