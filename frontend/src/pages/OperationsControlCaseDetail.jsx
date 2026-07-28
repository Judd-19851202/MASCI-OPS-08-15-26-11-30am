import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, GitBranch, Link2, Package, RefreshCw, ShieldAlert, TimerReset } from "lucide-react";
import { toast } from "sonner";
import {
  acknowledgeOperationalCaseCommunication,
  captureOperationalCaseEvidence,
  createOperationalCaseTask,
  exportOperationalCase,
  getOperationalCaseAssembly,
  getOperationalCaseGraph,
  getOperationalCaseTimeline,
  includeOperationalCaseBaseline,
  transitionOperationalCase,
} from "@/lib/operationsControlCasesApi";
import { formatPlatformTime } from "@/lib/platformTime";

const TRANSITIONS = [
  ["UNDER_REVIEW", "Start review"],
  ["INVESTIGATING", "Investigate"],
  ["ACTION_REQUIRED", "Mark action required"],
  ["RECOVERY_ACTIVE", "Start recovery"],
  ["MONITORING", "Move to monitoring"],
  ["PENDING_VERIFICATION", "Send to verification"],
  ["RESOLVED", "Resolve"],
  ["CLOSED", "Close case"],
  ["REOPENED", "Reopen"],
];

function Pill({ children, testId }) {
  return <span className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs font-semibold tracking-wide text-slate-700" data-testid={testId}>{children}</span>;
}

export default function OperationsControlCaseDetail() {
  const { caseId } = useParams();
  const [assembly, setAssembly] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    try {
      const [nextAssembly, nextTimeline, nextGraph] = await Promise.all([
        getOperationalCaseAssembly(caseId),
        getOperationalCaseTimeline(caseId),
        getOperationalCaseGraph(caseId),
      ]);
      setAssembly(nextAssembly);
      setTimeline(nextTimeline.timeline || []);
      setGraph(nextGraph || { nodes: [], edges: [] });
      setError("");
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || "Failed to load Operational Case.");
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { load(); }, [load]);

  const caseDoc = useMemo(() => assembly?.case || {}, [assembly]);
  const records = useMemo(() => assembly?.authoritative_records || {}, [assembly]);

  const proofChain = useMemo(() => ([
    { key: "daily-report", label: "Daily Report", value: records.daily_report?.doc_id || records.daily_report?.id || "—" },
    { key: "registered-event", label: "Registered event", value: caseDoc.origin?.originating_event_id || "—" },
    { key: "policy-decision", label: "Policy decision", value: caseDoc.origin?.policy_id || "—" },
    { key: "operational-case", label: "Operational Case", value: caseDoc.case_number || "—" },
    { key: "communication-intent", label: "Communication intent", value: (records.communications || [])[0]?.communication_intent_id || "—" },
    { key: "recipient-resolution", label: "Recipient resolution", value: (records.communications || [])[0]?.resolution?.case_owner_email || (records.communications || [])[0]?.resolution?.pm_email || "—" },
    { key: "captured-delivery", label: "Captured delivery", value: (records.communications || [])[0]?.status || "—" },
    { key: "acknowledgement", label: "Acknowledgement", value: (records.communications || [])[0]?.ack_status || "—" },
    { key: "variance-recovery", label: "Variance / recovery", value: `${(records.variance_reviews || []).length} variance · ${(records.tasks || []).length} tasks` },
    { key: "forecast-confidence", label: "Forecast / confidence", value: `${(records.forecast_history?.snapshots || []).length} forecast · ${(records.confidence_history?.snapshots || []).length} confidence` },
    { key: "resolution-closure", label: "Resolution / closure", value: caseDoc.status || "—" },
    { key: "evidence-baseline", label: "Evidence / baseline", value: `${(records.evidence_packages || []).length} evidence · ${(records.baselines || []).length} baseline` },
  ]), [caseDoc, records]);

  const runTransition = useCallback(async (toStatus) => {
    if (!caseId) return;
    setActing(true);
    try {
      await transitionOperationalCase(caseId, {
        to_status: toStatus,
        reason: `Operator moved case to ${toStatus}`,
        resolution_summary: toStatus === "RESOLVED" || toStatus === "CLOSED" ? "Governed case progression from Operations Control Center." : "",
        root_cause: toStatus === "CLOSED" ? "Operator-reviewed operational issue." : "",
        verification_notes: toStatus === "PENDING_VERIFICATION" ? "Verification requested from case detail route." : "",
      });
      toast.success(`Case moved to ${toStatus}.`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || `Failed to move case to ${toStatus}.`);
    } finally {
      setActing(false);
    }
  }, [caseId, load]);

  const createTask = useCallback(async () => {
    if (!caseId) return;
    setActing(true);
    try {
      await createOperationalCaseTask(caseId, {
        title: `Corrective action for ${caseDoc.case_number || caseId}`,
        description: "Created from the Operational Case detail route.",
        assignee_role: caseDoc.assigned_role || "pm",
        priority: "High",
        due_minutes: 240,
      });
      toast.success("Case task created.");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to create case task.");
    } finally {
      setActing(false);
    }
  }, [caseDoc.assigned_role, caseDoc.case_number, caseId, load]);

  const acknowledgeFirstCommunication = useCallback(async () => {
    const first = (records.communications || [])[0];
    if (!caseId || !first?.id) return;
    setActing(true);
    try {
      await acknowledgeOperationalCaseCommunication(caseId, first.id, { note: "Acknowledged from Case detail route." });
      toast.success("Communication acknowledged.");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to acknowledge communication.");
    } finally {
      setActing(false);
    }
  }, [caseId, load, records.communications]);

  const captureEvidence = useCallback(async () => {
    if (!caseId) return;
    setActing(true);
    try {
      await captureOperationalCaseEvidence(caseId);
      toast.success("Evidence package captured.");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to capture evidence.");
    } finally {
      setActing(false);
    }
  }, [caseId, load]);

  const includeBaseline = useCallback(async () => {
    if (!caseId) return;
    setActing(true);
    try {
      await includeOperationalCaseBaseline(caseId, { baseline_name: "Operations Control Plane v1" });
      toast.success("Baseline inclusion recorded.");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to include baseline.");
    } finally {
      setActing(false);
    }
  }, [caseId, load]);

  const exportEvidence = useCallback(async () => {
    if (!caseId) return;
    setActing(true);
    try {
      const result = await exportOperationalCase(caseId);
      toast.success(`Evidence export captured: ${result?.export?.id || "done"}`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to export evidence package.");
    } finally {
      setActing(false);
    }
  }, [caseId, load]);

  return (
    <section className="rounded-[2rem] border border-slate-200 bg-white/95 p-5 shadow-sm" data-testid="occ-case-detail-page">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/admin/operations-control" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-950" data-testid="occ-case-detail-back-link">
            <ArrowLeft className="h-4 w-4" /> Back to Operations Control Center
          </Link>
          <div className="mt-3 text-[11px] uppercase tracking-[0.28em] text-slate-500">Operational Case detail route</div>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950" data-testid="occ-case-detail-number">{caseDoc.case_number || caseId}</h1>
          <p className="mt-2 text-sm text-slate-600">Governed operational reconstruction with persistent timeline, graph, communications, evidence, and closure controls.</p>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60"
          data-testid="occ-case-detail-refresh-button"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      {error ? <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid="occ-case-detail-error">{error}</div> : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-4">
          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5" data-testid="occ-case-detail-summary-card">
            <div className="flex flex-wrap items-center gap-2">
              <Pill testId="occ-case-detail-status-pill">status: {caseDoc.status || "—"}</Pill>
              <Pill testId="occ-case-detail-severity-pill">severity: {caseDoc.severity || "—"}</Pill>
              <Pill testId="occ-case-detail-priority-pill">priority: {caseDoc.priority || "—"}</Pill>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 text-sm text-slate-700">
              <div data-testid="occ-case-detail-origin-source">Origin: {caseDoc.origin?.source_doc_id || caseDoc.origin?.source_record_id || "—"}</div>
              <div data-testid="occ-case-detail-project">Project: {caseDoc.project_number || "—"} · {caseDoc.project_name || "—"}</div>
              <div data-testid="occ-case-detail-owner">Owner: {caseDoc.case_owner_name || caseDoc.case_owner_role || "—"}</div>
              <div data-testid="occ-case-detail-updated">Updated: {caseDoc.updated_at ? formatPlatformTime(caseDoc.updated_at) : "—"}</div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" onClick={acknowledgeFirstCommunication} disabled={acting} className="rounded-full border border-sky-300 bg-sky-50 px-3 py-2 text-sm font-semibold text-sky-900 hover:bg-sky-100 disabled:opacity-60" data-testid="occ-case-detail-ack-button">Acknowledge communication</button>
              <button type="button" onClick={createTask} disabled={acting} className="rounded-full border border-amber-300 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-900 hover:bg-amber-100 disabled:opacity-60" data-testid="occ-case-detail-task-button">Create corrective task</button>
              <button type="button" onClick={captureEvidence} disabled={acting} className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-900 hover:bg-emerald-100 disabled:opacity-60" data-testid="occ-case-detail-evidence-button">Capture evidence</button>
              <button type="button" onClick={includeBaseline} disabled={acting} className="rounded-full border border-violet-300 bg-violet-50 px-3 py-2 text-sm font-semibold text-violet-900 hover:bg-violet-100 disabled:opacity-60" data-testid="occ-case-detail-baseline-button">Include baseline</button>
              <button type="button" onClick={exportEvidence} disabled={acting} className="rounded-full border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60" data-testid="occ-case-detail-export-button">Export evidence package</button>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5" data-testid="occ-case-proof-chain-drilldown">
            <div className="flex items-center gap-2 text-slate-500"><GitBranch className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">OCC proof-chain drilldown</span></div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {proofChain.map((step) => (
                <div key={step.key} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-proof-chain-${step.key}`}>
                  <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">{step.label}</div>
                  <div className="mt-2 break-words text-sm font-semibold text-slate-900">{step.value || "—"}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5" data-testid="occ-case-timeline-card">
            <div className="flex items-center gap-2 text-slate-500"><TimerReset className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Unified Case timeline</span></div>
            <div className="mt-4 space-y-3" data-testid="occ-case-timeline-list">
              {timeline.map((row) => (
                <div key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-case-timeline-${row.id}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="text-sm font-semibold text-slate-950">{row.title}</div>
                    <div className="text-xs text-slate-500">{row.at ? formatPlatformTime(row.at) : "—"}</div>
                  </div>
                  <div className="mt-1 text-xs uppercase tracking-[0.14em] text-slate-500">{row.kind}</div>
                  <div className="mt-2 text-sm text-slate-600">status: {row.status || "—"}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5" data-testid="occ-case-governed-actions-card">
            <div className="flex items-center gap-2 text-slate-500"><ShieldAlert className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Server-validated transitions</span></div>
            <div className="mt-4 flex flex-wrap gap-2">
              {TRANSITIONS.map(([status, label]) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => runTransition(status)}
                  disabled={acting}
                  className="rounded-full border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60"
                  data-testid={`occ-case-transition-${status.toLowerCase()}`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5" data-testid="occ-case-communications-card">
            <div className="text-[11px] uppercase tracking-[0.26em] text-slate-500">Communications + acknowledgement</div>
            <div className="mt-4 space-y-3">
              {(records.communications || []).map((row) => (
                <div key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-case-communication-${row.id}`}>
                  <div className="text-sm font-semibold text-slate-950">{row.communication_intent_id}</div>
                  <div className="mt-1 text-sm text-slate-600">{row.status} · ack {row.ack_status}</div>
                  <div className="mt-2 text-xs text-slate-500">{(row.email_recipients || []).join(", ") || "No resolved email recipients"}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5" data-testid="occ-case-graph-card">
            <div className="flex items-center gap-2 text-slate-500"><Link2 className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Relationship graph</span></div>
            <div className="mt-4 space-y-3">
              {(graph.nodes || []).map((node) => (
                <div key={node.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-case-graph-node-${node.id}`}>
                  <div className="text-sm font-semibold text-slate-950">{node.type}</div>
                  <div className="mt-1 text-sm text-slate-600 break-words">{node.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-white p-5" data-testid="occ-case-evidence-baseline-card">
            <div className="flex items-center gap-2 text-slate-500"><Package className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Evidence + baseline</span></div>
            <div className="mt-4 space-y-3 text-sm text-slate-700">
              <div data-testid="occ-case-evidence-count">Evidence packages: {(records.evidence_packages || []).length}</div>
              <div data-testid="occ-case-baseline-count">Baseline snapshots: {(records.baselines || []).length}</div>
              <div data-testid="occ-case-forecast-count">Forecast snapshots: {(records.forecast_history?.snapshots || []).length}</div>
              <div data-testid="occ-case-confidence-count">Confidence snapshots: {(records.confidence_history?.snapshots || []).length}</div>
              <div data-testid="occ-case-task-count">Tasks / corrective actions: {(records.tasks || []).length} / {(records.corrective_actions || []).length}</div>
            </div>
          </div>

          <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5" data-testid="occ-case-release-state-card">
            <div className="flex items-center gap-2 text-slate-500"><CheckCircle2 className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Release gate state</span></div>
            <div className="mt-3 text-sm text-slate-700">This case remains auditable only when every action persists through the canonical backend and closure requirements remain satisfied.</div>
          </div>
        </div>
      </div>
    </section>
  );
}
