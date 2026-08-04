import React from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import PmProjectSelector from "@/components/pm/command/PmProjectSelector";
import { Button } from "@/components/ui/button";
import { OperationalIntelligenceSnapshotWorkspace } from "@/components/operational_intelligence/OperationalIntelligenceSnapshotWorkspace";
import {
  downloadAdminOperationalIntelligenceExport,
  fetchAdminOperationalIntelligenceOverview,
  overrideAdminOperationalIntelligenceRecommendation,
  runAdminOperationalIntelligenceBackfill,
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

export default function AdminGovernanceOperationalIntelligence() {
  const [params, setParams] = useSearchParams();
  const [projectNumber, setProjectNumber] = React.useState(params.get("project_number") || "");
  const [overview, setOverview] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [actionBusy, setActionBusy] = React.useState(false);

  React.useEffect(() => {
    const next = params.get("project_number") || "";
    setProjectNumber(next);
  }, [params]);

  const load = React.useCallback(async (pn = projectNumber, forceRefresh = false) => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchAdminOperationalIntelligenceOverview(pn, { forceRefresh });
      setOverview(data || null);
    } catch (err) {
      setError(err?.response?.data?.detail || "Operational intelligence governance is unavailable right now.");
    } finally {
      setLoading(false);
    }
  }, [projectNumber]);

  React.useEffect(() => {
    load(projectNumber);
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
      const response = await downloadAdminOperationalIntelligenceExport(projectNumber);
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
      await overrideAdminOperationalIntelligenceRecommendation(projectNumber, recommendation.recommendation_id, {
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

  const handleBackfill = async () => {
    setActionBusy(true);
    try {
      await runAdminOperationalIntelligenceBackfill(true);
      toast.success("Operational intelligence backfill queued.");
      await load(projectNumber, true);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Could not run the operational intelligence backfill.");
    } finally {
      setActionBusy(false);
    }
  };

  const summary = overview?.summary || {};
  const latestRows = overview?.snapshots || [];
  const snapshot = overview?.snapshot || null;

  return (
    <LegacyAdminModernShell
      title="Operational Intelligence Governance"
      subtitle="Admin oversight for the governed metric engine, evidence lineage, review-queue pressure, and additive backfill health."
    >
      <div className="space-y-6" data-testid="admin-governance-operational-intelligence-page">
        <div className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-governance-operational-intelligence-overview">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">Governed Metric Engine</div>
              <h1 className="mt-2 text-3xl font-black text-slate-900">Operational Intelligence Governance</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">Use this surface to refresh governed snapshots, monitor orphan-event pressure, and verify that every PM-facing metric still flows from one additive authority.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={() => load(projectNumber, true)} data-testid="admin-governance-operational-intelligence-refresh-button">Refresh</Button>
              <Button type="button" onClick={handleBackfill} disabled={actionBusy} data-testid="admin-governance-operational-intelligence-backfill-button">Run backfill</Button>
            </div>
          </div>
          <div className="mt-4 max-w-sm" data-testid="admin-governance-operational-intelligence-selector">
            <PmProjectSelector projectNumber={projectNumber} onChange={chooseProject} />
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-4" data-testid="admin-governance-operational-intelligence-summary-grid">
            {[
              ["projects-with-snapshots", summary.projects_with_snapshots || 0, "Projects with snapshots"],
              ["open-review-items", summary.open_review_items || 0, "Open review items"],
              ["open-recommendations", summary.open_recommendations || 0, "Open recommendations"],
              ["orphan-events", summary.orphan_events || 0, "Orphan events"],
            ].map(([key, value, label]) => (
              <div key={key} className="rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4" data-testid={`admin-governance-operational-intelligence-summary-${key}`}>
                <div className="text-[11px] uppercase tracking-[0.2em] text-slate-500">{label}</div>
                <div className="mt-3 text-3xl font-black text-slate-900">{value}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600" data-testid="admin-governance-operational-intelligence-backfill-status">
            Backfill status: {overview?.backfill?.status || "pending_manual_run"} · Projects processed {overview?.backfill?.projects_processed ?? 0} · Snapshots built {overview?.backfill?.snapshots_built ?? 0}
          </div>
        </div>

        {projectNumber ? (
          <OperationalIntelligenceSnapshotWorkspace
            snapshot={snapshot}
            loading={loading}
            error={error}
            actionBusy={actionBusy}
            title={`Operational Intelligence · ${projectNumber}`}
            subtitle="Admin governance view over the same governed snapshot consumed by PM operators. Review-lineage issues remain additive and explainable."
            projectSelector={<PmProjectSelector projectNumber={projectNumber} onChange={chooseProject} />}
            onRefresh={() => load(projectNumber, true)}
            onExport={handleExport}
            onOverride={handleOverride}
            dataTestId="admin-governance-operational-intelligence-workspace"
          />
        ) : (
          <section className="rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-sm" data-testid="admin-governance-operational-intelligence-latest-snapshots">
            <h2 className="text-xl font-black text-slate-900">Latest governed snapshots</h2>
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 text-left text-[11px] uppercase tracking-[0.2em] text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Project</th>
                    <th className="px-4 py-3 text-right">Approved events</th>
                    <th className="px-4 py-3 text-right">Review items</th>
                    <th className="px-4 py-3 text-right">Recommendations</th>
                    <th className="px-4 py-3 text-right">Orphans</th>
                  </tr>
                </thead>
                <tbody>
                  {latestRows.map((row) => (
                    <tr key={row.project_number} className="border-t border-slate-100" data-testid={`admin-governance-operational-intelligence-snapshot-${row.project_number}`}>
                      <td className="px-4 py-3 font-semibold text-slate-900">{row.project_number}</td>
                      <td className="px-4 py-3 text-right text-slate-700">{row.summary?.approved_events || 0}</td>
                      <td className="px-4 py-3 text-right text-slate-700">{row.summary?.review_queue_open || 0}</td>
                      <td className="px-4 py-3 text-right text-slate-700">{row.summary?.open_recommendations || 0}</td>
                      <td className="px-4 py-3 text-right text-slate-700">{row.summary?.orphan_events || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </LegacyAdminModernShell>
  );
}