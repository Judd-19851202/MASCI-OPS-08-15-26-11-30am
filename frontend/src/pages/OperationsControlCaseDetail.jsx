import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, GitBranch, Link2, Package, RefreshCw, ShieldAlert, TimerReset } from "lucide-react";
import { toast } from "sonner";
import {
  acknowledgeOperationalCaseCommunication,
  createOperationalCaseTask,
  exportOperationalCase,
  getOperationalCaseAssembly,
  getOperationalCaseGraph,
  getOperationalCaseTimeline,
  transitionOperationalCase,
} from "@/lib/operationsControlCasesApi";
import { formatPlatformTime } from "@/lib/platformTime";
import {
  formatOperatorJobLabel,
  humanizeOperatorToken,
  sanitizeOperatorReference,
} from "@/lib/operatorLanguage";
import { OperationsControlShell } from "@/components/operations/OperationsControlShell";

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
      const detail = e?.response?.data?.detail || e?.message || "Failed to load Operations Case.";
      setError(detail.toLowerCase().includes("unknown case") ? "This case is not available yet." : detail);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { load(); }, [load]);

  const caseDoc = useMemo(() => assembly?.case || {}, [assembly]);
  const records = useMemo(() => assembly?.authoritative_records || {}, [assembly]);
  const caseNumber = sanitizeOperatorReference(caseDoc.case_number || caseId, "Operations case");
  const caseJobLabel = formatOperatorJobLabel(caseDoc.project_number, caseDoc.project_name);

  const proofChain = useMemo(() => ([
    { key: "daily-report", label: "Daily report", value: records.daily_report?.doc_id || records.daily_report?.id ? "Attached" : "Not attached" },
    { key: "source-record", label: "Source record", value: sanitizeOperatorReference(caseDoc.origin?.source_doc_id || caseDoc.origin?.source_record_id, "Linked record") },
    { key: "operations-case", label: "Case number", value: caseNumber },
    { key: "messages", label: "Messages", value: `${(records.communications || []).length} active` },
    { key: "message-status", label: "Latest message status", value: humanizeOperatorToken((records.communications || [])[0]?.status, "No updates yet") },
    { key: "message-confirmation", label: "Message confirmation", value: humanizeOperatorToken((records.communications || [])[0]?.ack_status, "Waiting") },
    { key: "follow-up-work", label: "Follow-up work", value: `${(records.tasks || []).length} tasks · ${(records.corrective_actions || []).length} actions` },
    { key: "forecast-confidence", label: "Forecast and confidence", value: `${(records.forecast_history?.snapshots || []).length} forecast updates · ${(records.confidence_history?.snapshots || []).length} confidence updates` },
    { key: "resolution", label: "Current status", value: humanizeOperatorToken(caseDoc.status, "Open") },
    { key: "supporting-records", label: "Supporting records", value: `${(records.evidence_packages || []).length} packets · ${(records.baselines || []).length} snapshots` },
  ]), [caseDoc, records]);

  const runTransition = useCallback(async (toStatus) => {
    if (!caseId) return;
    setActing(true);
    try {
      await transitionOperationalCase(caseId, {
        to_status: toStatus,
        reason: `Case updated to ${toStatus}`,
        resolution_summary: toStatus === "RESOLVED" || toStatus === "CLOSED" ? "Case progressed through Operations Control." : "",
        root_cause: toStatus === "CLOSED" ? "Operational issue reviewed by the assigned team." : "",
        verification_notes: toStatus === "PENDING_VERIFICATION" ? "Verification requested from Operations Cases." : "",
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
        title: `Corrective action for ${caseNumber}`,
        description: "Created from Operations Cases.",
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
      await acknowledgeOperationalCaseCommunication(caseId, first.id, { note: "Confirmed from Operations Cases." });
      toast.success("Communication acknowledged.");
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to acknowledge communication.");
    } finally {
      setActing(false);
    }
  }, [caseId, load, records.communications]);

  const exportEvidence = useCallback(async () => {
    if (!caseId) return;
    setActing(true);
    try {
      const result = await exportOperationalCase(caseId);
      toast.success(`Case packet ready: ${result?.export?.id || "done"}`);
      await load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || e?.message || "Failed to prepare the case packet.");
    } finally {
      setActing(false);
    }
  }, [caseId, load]);

  return (
    <OperationsControlShell
      pageTitle="Operations Cases"
      subtitle={caseJobLabel}
      crumbs={[{ label: "Operations Control" }, { label: "Operations Cases" }, { label: caseNumber }]}
      primaryActions={(
        <div className="flex gap-2">
          <Link to="/operations-control/cases" className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-800 hover:bg-slate-100" data-testid="occ-case-detail-back-link">
            <ArrowLeft className="h-4 w-4" /> Back to Operations Cases
          </Link>
          <button
            type="button"
            onClick={load}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60"
            data-testid="occ-case-detail-refresh-button"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /> Refresh
          </button>
        </div>
      )}
      testId="occ-case-detail-page"
    >
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div>
          <div className="text-[11px] uppercase tracking-[0.28em] text-slate-500">Operations case</div>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950" data-testid="occ-case-detail-number">{caseNumber}</h1>
          <p className="mt-2 text-sm text-slate-600">Review the current status, assigned follow-up work, messages, and linked records for this case.</p>
        </div>

        {error ? <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800" data-testid="occ-case-detail-error">{error}</div> : null}

        <div className="mt-5 grid gap-4 xl:grid-cols-[1.4fr_0.9fr]">
        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5" data-testid="occ-case-detail-summary-card">
            <div className="flex flex-wrap items-center gap-2">
              <Pill testId="occ-case-detail-status-pill">Status: {humanizeOperatorToken(caseDoc.status, "Open")}</Pill>
              <Pill testId="occ-case-detail-severity-pill">Severity: {humanizeOperatorToken(caseDoc.severity, "Standard")}</Pill>
              <Pill testId="occ-case-detail-priority-pill">Priority: {humanizeOperatorToken(caseDoc.priority, "Standard")}</Pill>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 text-sm text-slate-700">
              <div data-testid="occ-case-detail-origin-source">Source record: {sanitizeOperatorReference(caseDoc.origin?.source_doc_id || caseDoc.origin?.source_record_id, "Linked record")}</div>
              <div data-testid="occ-case-detail-project">Job: {caseJobLabel}</div>
              <div data-testid="occ-case-detail-owner">Owner: {sanitizeOperatorReference(caseDoc.case_owner_name || caseDoc.case_owner_role, "Unassigned")}</div>
              <div data-testid="occ-case-detail-updated">Updated: {caseDoc.updated_at ? formatPlatformTime(caseDoc.updated_at) : "—"}</div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button type="button" onClick={acknowledgeFirstCommunication} disabled={acting} className="rounded-md border border-sky-300 bg-sky-50 px-3 py-2 text-sm font-semibold text-sky-900 hover:bg-sky-100 disabled:opacity-60" data-testid="occ-case-detail-ack-button">Confirm message</button>
              <button type="button" onClick={createTask} disabled={acting} className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-900 hover:bg-amber-100 disabled:opacity-60" data-testid="occ-case-detail-task-button">Create follow-up task</button>
              <button type="button" onClick={exportEvidence} disabled={acting} className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100 disabled:opacity-60" data-testid="occ-case-detail-export-button">Download case packet</button>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5" data-testid="occ-case-proof-chain-drilldown">
            <div className="flex items-center gap-2 text-slate-500"><GitBranch className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Related work records</span></div>
            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {proofChain.map((step) => (
                <div key={step.key} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-proof-chain-${step.key}`}>
                  <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">{step.label}</div>
                  <div className="mt-2 break-words text-sm font-semibold text-slate-900">{step.value || "—"}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5" data-testid="occ-case-timeline-card">
            <div className="flex items-center gap-2 text-slate-500"><TimerReset className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Case activity</span></div>
            <div className="mt-4 space-y-3" data-testid="occ-case-timeline-list">
              {timeline.map((row) => (
                <div key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-case-timeline-${row.id}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="text-sm font-semibold text-slate-950">{sanitizeOperatorReference(row.title, "Case update")}</div>
                    <div className="text-xs text-slate-500">{row.at ? formatPlatformTime(row.at) : "—"}</div>
                  </div>
                  <div className="mt-1 text-xs uppercase tracking-[0.14em] text-slate-500">{humanizeOperatorToken(row.kind, "Activity")}</div>
                  <div className="mt-2 text-sm text-slate-600">Status: {humanizeOperatorToken(row.status, "Open")}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5" data-testid="occ-case-governed-actions-card">
            <div className="flex items-center gap-2 text-slate-500"><ShieldAlert className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Update case status</span></div>
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

          <div className="rounded-2xl border border-slate-200 bg-white p-5" data-testid="occ-case-communications-card">
            <div className="text-[11px] uppercase tracking-[0.26em] text-slate-500">Messages and confirmation</div>
            <div className="mt-4 space-y-3">
              {(records.communications || []).map((row) => (
                <div key={row.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-case-communication-${row.id}`}>
                  <div className="text-sm font-semibold text-slate-950">{humanizeOperatorToken(row.communication_intent_id, "Case update")}</div>
                  <div className="mt-1 text-sm text-slate-600">{humanizeOperatorToken(row.status, "Pending")} · confirmed {humanizeOperatorToken(row.ack_status, "Waiting")}</div>
                  <div className="mt-2 text-xs text-slate-500">{(row.email_recipients || []).length ? `${(row.email_recipients || []).length} recipient(s)` : "No recipients listed"}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5" data-testid="occ-case-graph-card">
            <div className="flex items-center gap-2 text-slate-500"><Link2 className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Linked records</span></div>
            <div className="mt-4 space-y-3">
              {(graph.nodes || []).map((node) => (
                <div key={node.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`occ-case-graph-node-${node.id}`}>
                  <div className="text-sm font-semibold text-slate-950">{humanizeOperatorToken(node.type, "Linked record")}</div>
                  <div className="mt-1 text-sm text-slate-600 break-words">{sanitizeOperatorReference(node.label, "Related work item")}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5" data-testid="occ-case-evidence-baseline-card">
            <div className="flex items-center gap-2 text-slate-500"><Package className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Supporting records</span></div>
            <div className="mt-4 space-y-3 text-sm text-slate-700">
              <div data-testid="occ-case-evidence-count">Case packets: {(records.evidence_packages || []).length}</div>
              <div data-testid="occ-case-baseline-count">Saved snapshots: {(records.baselines || []).length}</div>
              <div data-testid="occ-case-forecast-count">Forecast updates: {(records.forecast_history?.snapshots || []).length}</div>
              <div data-testid="occ-case-confidence-count">Confidence updates: {(records.confidence_history?.snapshots || []).length}</div>
              <div data-testid="occ-case-task-count">Tasks / follow-up actions: {(records.tasks || []).length} / {(records.corrective_actions || []).length}</div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5" data-testid="occ-case-release-state-card">
            <div className="flex items-center gap-2 text-slate-500"><CheckCircle2 className="h-4 w-4" /><span className="text-[11px] uppercase tracking-[0.26em]">Case readiness</span></div>
            <div className="mt-3 text-sm text-slate-700">This case stays open until follow-up work, messages, and supporting records are complete.</div>
          </div>
        </div>
      </div>
      </section>
    </OperationsControlShell>
  );
}
