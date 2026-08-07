import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import PmShell from "@/components/PmShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import ForecastingCommitmentsWorkspace from "@/components/project_controls/ForecastingCommitmentsWorkspace";
import {
  createPmProjectForecastCommitment,
  createPmProjectForecastSnapshot,
  fetchPmProjectForecastingWorkspace,
  updatePmProjectForecastCommitment,
} from "@/lib/projectControlsApi";

export default function PmForecastingCommitments() {
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
      const data = await fetchPmProjectForecastingWorkspace(pn);
      setWorkspace(data || null);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not load forecasting workspace.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectNumber) load(projectNumber);
  }, [projectNumber]);

  const createCommitment = async (payload) => {
    if (!projectNumber) return;
    setWorking(true);
    try {
      await createPmProjectForecastCommitment(projectNumber, payload);
      toast.success("Commitment saved.");
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not save the commitment.");
    } finally {
      setWorking(false);
    }
  };

  const updateCommitment = async (row, draft) => {
    if (!projectNumber || !row?.commitment_id) return;
    setWorking(true);
    try {
      await updatePmProjectForecastCommitment(projectNumber, row.commitment_id, {
        ...row,
        status: draft?.status || row.status,
        note: draft?.note || "",
      });
      toast.success("Commitment updated.");
      await load(projectNumber);
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not update the commitment.");
    } finally {
      setWorking(false);
    }
  };

  const captureSnapshot = async (note) => {
    if (!projectNumber) return;
    setWorking(true);
    try {
      const data = await createPmProjectForecastSnapshot(projectNumber, note || "");
      setWorkspace(data || null);
      toast.success("Forecast version captured.");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not capture the forecast version.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <PmShell title="Forecasting & Commitments" subtitle="Approved forecast records for likely finish, pace, and commitments" data-testid="pm-forecasting-commitments-page">
      <ForecastingCommitmentsWorkspace
        mode="pm"
        projectNumber={projectNumber}
        selector={<PmProjectSelector value={projectNumber} onChange={setProject} />}
        workspace={workspace}
        loading={loading}
        working={working}
        onRefresh={() => load(projectNumber)}
        onCaptureSnapshot={captureSnapshot}
        canEditCommitments
        onCreateCommitment={createCommitment}
        onUpdateCommitment={updateCommitment}
      />
    </PmShell>
  );
}
