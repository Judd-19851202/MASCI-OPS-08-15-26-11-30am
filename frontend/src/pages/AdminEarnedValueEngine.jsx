import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { AdminRouteShell } from "@/components/admin/AdminRouteShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import EarnedValueWorkspace from "@/components/project_controls/EarnedValueWorkspace";
import {
  createAdminProjectEarnedValueSnapshot,
  downloadAdminProjectEarnedValueExport,
  fetchAdminProjectEarnedValueSnapshot,
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

export default function AdminEarnedValueEngine() {
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = useState(params.get("project_number") || "");
  const [workspace, setWorkspace] = useState(null);
  const [loading, setLoading] = useState(false);
  const [working, setWorking] = useState(false);
  const bootLoadedRef = useRef(false);

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

  const load = async (pn = projectNumber, forceRefresh = false) => {
    if (!pn) return;
    setLoading(true);
    try {
      const data = await fetchAdminProjectEarnedValueSnapshot(pn, { forceRefresh });
      setWorkspace(data || null);
      if (data) bootLoadedRef.current = true;
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not load the executive earned-value workspace.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!projectNumber) return undefined;
    bootLoadedRef.current = false;
    setWorkspace(null);
    const retryTimer = window.setTimeout(() => {
      if (!bootLoadedRef.current) load(projectNumber, true);
    }, 1800);
    load(projectNumber);
    return () => window.clearTimeout(retryTimer);
  }, [projectNumber]);

  const captureSnapshot = async (note) => {
    if (!projectNumber) return;
    setWorking(true);
    try {
      const data = await createAdminProjectEarnedValueSnapshot(projectNumber, note || "");
      setWorkspace(data || null);
      toast.success("Executive earned-value version captured.");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not capture the executive earned-value version.");
    } finally {
      setWorking(false);
    }
  };

  const exportCsv = async () => {
    if (!projectNumber) return;
    setWorking(true);
    try {
      const response = await downloadAdminProjectEarnedValueExport(projectNumber);
      downloadResponseFile(response, `${projectNumber}-earned-value.csv`);
      toast.success("Executive earned-value CSV downloaded.");
    } catch (error) {
      toast.error(error?.response?.data?.detail || "Could not export executive earned value.");
    } finally {
      setWorking(false);
    }
  };

  return (
    <AdminRouteShell pageTitle="Earned Value Engine" subtitle="Executive read-only governed C8 view" crumbs={[{ label: "Governance" }, { label: "Earned Value Engine" }]} testId="admin-earned-value-page">
      <EarnedValueWorkspace
        mode="executive"
        projectNumber={projectNumber}
        selector={<PmProjectSelector value={projectNumber} onChange={setProject} />}
        workspace={workspace}
        loading={loading}
        working={working}
        onRefresh={() => load(projectNumber, true)}
        onCaptureSnapshot={captureSnapshot}
        onExport={exportCsv}
      />
    </AdminRouteShell>
  );
}