import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import ForecastingCommitmentsWorkspace from "@/components/project_controls/ForecastingCommitmentsWorkspace";
import {
  createAdminProjectForecastSnapshot,
  fetchAdminProjectForecastingWorkspace,
} from "@/lib/projectControlsApi";

export default function AdminForecastingCommitments() {
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);

  useEffect(() => {
    setProjectNumber(params.get("project_number") || "");
  }, [params]);

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
      const data = await fetchAdminProjectForecastingWorkspace(pn);
      setWorkspace(data || null);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not load executive forecast workspace.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectNumber) load(projectNumber);
  }, [projectNumber]);

  const captureSnapshot = async (note) => {
    if (!projectNumber) return;
    setWorking(true);
    try {
      const data = await createAdminProjectForecastSnapshot(projectNumber, note || "");
      setWorkspace(data || null);
      toast.success("Executive version captured.");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not capture the executive version.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <AdminRouteShell pageTitle="Forecasting & Commitments" subtitle="Executive read-only governed view" crumbs={[{ label: "Governance" }, { label: "Forecasting & Commitments" }]} testId="admin-forecasting-commitments-page">
      <ForecastingCommitmentsWorkspace
        mode="executive"
        projectNumber={projectNumber}
        selector={<PmProjectSelector value={projectNumber} onChange={setProject} />}
        workspace={workspace}
        loading={loading}
        working={working}
        onRefresh={() => load(projectNumber)}
        onCaptureSnapshot={captureSnapshot}
      />
    </AdminRouteShell>
  );
}
