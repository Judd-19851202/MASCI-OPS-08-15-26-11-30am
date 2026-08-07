import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { PortalShell } from "@/design-system";
import { Button } from "@/components/ui/button";
import ForecastingCommitmentsWorkspace from "@/components/project_controls/ForecastingCommitmentsWorkspace";
import { fetchMyProjects } from "@/lib/teamRosterApi";
import { fetchFieldLeadershipProjectForecasting } from "@/lib/projectControlsApi";
import { getFlUser } from "@/lib/flAuth";

export default function FieldLeadershipForecasting() {
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [projectOptions, setProjectOptions] = useState([]);
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(false);
  const user = getFlUser();

  useEffect(() => {
    setProjectNumber(params.get("project_number") || "");
  }, [params]);

  useEffect(() => {
    let active = true;
    fetchMyProjects()
      .then((data) => {
        if (!active) return;
        const rows = Array.isArray(data?.items) ? data.items : [];
        setProjectOptions(rows.filter((row) => row?.project_number));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const setProject = (value) => {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) next.set("project_number", value);
      else next.delete("project_number");
      return next;
    });
  };

  const load = async (pn = projectNumber) => {
    if (!pn) return;
    setLoading(true);
    try {
      const data = await fetchFieldLeadershipProjectForecasting(pn);
      setWorkspace(data?.workspace || null);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not load the field forecast view.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectNumber) load(projectNumber);
  }, [projectNumber]);

  const selector = (
    <div className="flex flex-col gap-2" data-testid="field-forecast-project-selector-wrap">
      <label htmlFor="field-forecast-project-selector" className="text-[10px] uppercase tracking-[0.22em] text-slate-500">Project</label>
      <select id="field-forecast-project-selector" className="h-10 rounded-xl border border-slate-300 bg-white px-3 text-sm" value={projectNumber} onChange={(e) => setProject(e.target.value)} data-testid="field-forecast-project-selector">
        <option value="">Select a rostered project</option>
        {projectOptions.map((row) => (
          <option key={`${row.project_number}-${row.id || row.assignment_id || row.email || "row"}`} value={row.project_number}>
            {row.project_number} {row.project_name ? `· ${row.project_name}` : ""}
          </option>
        ))}
      </select>
      <Link to="/field-leadership/portal/dashboard" className="text-sm font-semibold text-teal-700 underline-offset-4 hover:underline" data-testid="field-forecast-dashboard-link">Back to dashboard</Link>
    </div>
  );

  return (
    <PortalShell portalName="MASCI" portalRole="Field Leadership Portal" pageTitle="Forecasting & Commitments" subtitle={user?.role || "Rostered operational forecast"} showNotifications={false} primaryActions={<Button asChild variant="outline" data-testid="field-forecast-back-button"><Link to="/field-leadership/portal/dashboard">Dashboard</Link></Button>}>
      <div className="px-4 py-6 sm:px-6" data-testid="field-forecast-page-shell">
        <ForecastingCommitmentsWorkspace
          mode="field"
          projectNumber={projectNumber}
          selector={selector}
          workspace={workspace}
          loading={loading}
          working={false}
          onRefresh={() => load(projectNumber)}
        />
      </div>
    </PortalShell>
  );
}
