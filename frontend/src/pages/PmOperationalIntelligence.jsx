import React from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import PmShell from "@/components/PmShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import { OperationalIntelligenceSnapshotWorkspace } from "@/components/operational_intelligence/OperationalIntelligenceSnapshotWorkspace";
import {
  downloadPmOperationalIntelligenceExport,
  fetchPmOperationalIntelligenceSnapshot,
  overridePmOperationalIntelligenceRecommendation,
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

export default function PmOperationalIntelligence() {
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = React.useState(params.get("project_number") || "");
  const [snapshot, setSnapshot] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [actionBusy, setActionBusy] = React.useState(false);

  React.useEffect(() => {
    const next = params.get("project_number") || "";
    setProjectNumber(next);
  }, [params]);

  const load = React.useCallback(async (pn = projectNumber, forceRefresh = false) => {
    if (!pn) {
      setSnapshot(null);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await fetchPmOperationalIntelligenceSnapshot(pn, { forceRefresh });
      setSnapshot(data || null);
    } catch (err) {
      setError(err?.response?.data?.detail || "Operational intelligence is unavailable right now.");
    } finally {
      setLoading(false);
    }
  }, [projectNumber]);

  React.useEffect(() => {
    if (projectNumber) load(projectNumber);
  }, [projectNumber, load]);

  const chooseProject = (nextProject) => {
    setParams((prev) => {
      const next = new URLSearchParams(prev);
      if (nextProject) next.set("project_number", nextProject);
      else next.delete("project_number");
      return next;
    });
  };

  const handleExport = async () => {
    if (!projectNumber) return;
    try {
      const response = await downloadPmOperationalIntelligenceExport(projectNumber);
      downloadResponseFile(response, `${projectNumber}_governed_metrics.csv`);
      toast.success("Governed metrics export downloaded.");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not export governed metrics.");
    }
  };

  const handleOverride = async (recommendation, note) => {
    if (!projectNumber || !recommendation?.recommendation_id) return;
    setActionBusy(true);
    try {
      await overridePmOperationalIntelligenceRecommendation(projectNumber, recommendation.recommendation_id, {
        action: "override",
        note,
      });
      toast.success("Operational override recorded.");
      await load(projectNumber, true);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not record the override.");
    } finally {
      setActionBusy(false);
    }
  };

  return (
    <PmShell title="Operational Intelligence" section="operational-intelligence">
      <OperationalIntelligenceSnapshotWorkspace
        snapshot={snapshot}
        loading={loading}
        error={error}
        actionBusy={actionBusy}
        title="Operational Intelligence"
        subtitle="One governed metric engine powers every production KPI, recommendation, export, and drill-down. Work Blocks remain the operational heart, and unresolved ambiguity is routed to governed review instead of guessed."
        projectSelector={<PmProjectSelector projectNumber={projectNumber} onChange={chooseProject} />}
        onRefresh={() => load(projectNumber, true)}
        onExport={handleExport}
        onOverride={handleOverride}
        dataTestId="pm-operational-intelligence"
      />
    </PmShell>
  );
}