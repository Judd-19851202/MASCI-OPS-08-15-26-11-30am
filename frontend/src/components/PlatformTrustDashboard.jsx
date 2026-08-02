/**
 * <PlatformTrustDashboard> — Track 15.76
 *
 * Single-page Platform Trust Spine dashboard. Admin-gated, read-only.
 * Consumes:
 *   GET /api/admin/trust-spine
 *   GET /api/admin/trust-spine/workflow/{workflow}
 *
 * Surfaces — per the Track 15.76 contract:
 *   - Universal platform band (red / amber / green)
 *   - Per-workflow row: band, last success, last failure, 24h success
 *     rate, missing expected stages, exact failure stage + remediation
 *   - Drill-in panel showing the most recent lifecycle events for the
 *     selected workflow, with stage / status / record_id / failure
 *     reason — so the operator can identify the exact failing record
 *     without leaving the screen.
 *
 * Hard rules honored:
 *   - No fake green: idle workflows render AMBER-NO-ACTIVITY,
 *     partial-evidence workflows render AMBER, failures render RED.
 *   - No shell scripts, no tokens to copy, no Mongo queries.
 *   - No PII: only operational identifiers are shown.
 */
import React, { useState, useCallback, useEffect, useMemo } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  RotateCw,
  Activity,
  Clock,
  ChevronRight,
  ChevronDown,
  Hourglass,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import LegacyAdminModernShell from "@/components/admin/LegacyAdminModernShell";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { sanitizeOperatorReference } from "@/lib/operatorLanguage";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime } from "@/lib/platformTime";

const BAND = {
  green: {
    tone: "bg-emerald-50 border-emerald-200",
    pill: "bg-emerald-100 text-emerald-800 border-emerald-300",
    Icon: ShieldCheck,
    label: "Evidence complete",
  },
  amber: {
    tone: "bg-amber-50 border-amber-200",
    pill: "bg-amber-100 text-amber-800 border-amber-300",
    Icon: AlertTriangle,
    label: "Incomplete evidence",
  },
  "amber-no-activity": {
    tone: "bg-slate-50 border-slate-200",
    pill: "bg-slate-100 text-slate-700 border-slate-300",
    Icon: Hourglass,
    label: "No activity 24h",
  },
  red: {
    tone: "bg-rose-50 border-rose-200",
    pill: "bg-rose-100 text-rose-800 border-rose-300",
    Icon: XCircle,
    label: "Failure observed",
  },
};

function Badge({ band, children }) {
  const cfg = BAND[band] || BAND.amber;
  const { Icon } = cfg;
  return (
    <span
      data-testid={`trust-spine-band-${band}`}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${cfg.pill}`}
    >
      <Icon size={12} />
      {children || cfg.label}
    </span>
  );
}

function fmtTs(iso) {
  if (!iso) return "—";
  try {
    return formatPlatformTime(iso);
  } catch {
    return iso;
  }
}

function fmtPct(rate) {
  if (rate == null || Number.isNaN(rate)) return "—";
  return `${Math.round(rate * 1000) / 10}%`;
}

function humanizeToken(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function OwnershipNote({ surface, relationship, primaryStatus, checkedAt }) {
  if (!surface) return null;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3" data-testid="trust-spine-owner-note">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[10px] font-mono uppercase tracking-[0.18em] text-slate-500">Evidence ownership</span>
        <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-[10px] font-mono uppercase tracking-[0.16em] text-slate-700">
          {humanizeToken(primaryStatus || relationship?.canonical_status || surface.role || "registered")}
        </span>
      </div>
      <p className="text-sm text-slate-800" data-testid="trust-spine-owner-note-summary">
        {surface.surface_name || "Platform Standards Monitor"} is the primary source for workflow lifecycle status on this page. If another screen disagrees with it, review the conflict before taking action.
      </p>
      <div className="grid gap-3 md:grid-cols-2 text-sm text-slate-700">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3" data-testid="trust-spine-owner-note-subject">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">Truth subject</div>
          <div className="mt-1 font-semibold text-slate-950">{humanizeToken(surface.truth_subject || "workflow lifecycle truth")}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3" data-testid="trust-spine-owner-note-checked-at">
          <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-slate-500">Checked at</div>
          <div className="mt-1 font-semibold text-slate-950">{fmtTs(checkedAt) || "No timestamp reported"}</div>
        </div>
      </div>
    </div>
  );
}

function boundedHeadline(ots) {
  const claim = ots?.permitted_claim || "UNKNOWN";
  const evaluation = ots?.truth_evaluation || "UNVERIFIABLE";
  if (evaluation === "MISMATCH") {
    return "Lifecycle evidence shows at least one failing workflow.";
  }
  if (evaluation === "DEGRADED") {
    return "Lifecycle evidence is incomplete or stale for at least one workflow.";
  }
  if (claim === "VALIDATED") {
    return "Lifecycle evidence validated in scope.";
  }
  if (claim === "VERIFIED") {
    return "Lifecycle evidence verified in scope, with bounded gaps.";
  }
  if (claim === "OBSERVED") {
    return "Lifecycle activity observed, but not fully validated in scope.";
  }
  return "Lifecycle evidence is available with a bounded claim.";
}

function TruthDisclosure({ ots, testidPrefix }) {
  if (!ots) return null;
  const unknowns = ots.unknowns || [];
  const contradictions = ots.contradictory_evidence || [];
  const reference = sanitizeOperatorReference(ots.audit_reference, "tracking reference");
  return (
    <div className="space-y-2" data-testid={`${testidPrefix}-wrapper`}>
      <div
        className="grid gap-2 rounded-xl border border-slate-200 bg-white/80 p-3 text-xs text-slate-700 sm:grid-cols-2 lg:grid-cols-4"
        data-testid={testidPrefix}
      >
        <div data-testid={`${testidPrefix}-subject`}>
          <span className="font-semibold text-slate-900">What this page measures:</span> {humanizeToken(ots.truth_subject || "workflow lifecycle truth")}
        </div>
        <div data-testid={`${testidPrefix}-claim`}>
          <span className="font-semibold text-slate-900">Allowed claim:</span> {humanizeToken(ots.permitted_claim || "not declared")}
        </div>
        <div data-testid={`${testidPrefix}-ceiling`}>
          <span className="font-semibold text-slate-900">Claim ceiling:</span> {humanizeToken(ots.claim_ceiling || "not declared")}
        </div>
        <div data-testid={`${testidPrefix}-confidence`}>
          <span className="font-semibold text-slate-900">Confidence:</span> {humanizeToken(ots.evidence_confidence || "not declared")}
        </div>
        <div data-testid={`${testidPrefix}-state`}>
          <span className="font-semibold text-slate-900">Evidence state:</span> {humanizeToken(ots.evidence_state || "not declared")}
        </div>
        <div data-testid={`${testidPrefix}-quality`}>
          <span className="font-semibold text-slate-900">Evidence quality:</span> {humanizeToken(ots.evidence_quality || "not declared")}
        </div>
        <div data-testid={`${testidPrefix}-basis`}>
          <span className="font-semibold text-slate-900">Evidence basis:</span> {(ots.claim_basis || []).map(humanizeToken).join(" · ") || "No basis listed"}
        </div>
        <div data-testid={`${testidPrefix}-audit`}>
          <span className="font-semibold text-slate-900">Tracking reference:</span> {reference || "No tracking reference listed"}
        </div>
      </div>
      {unknowns.length > 0 && (
        <div
          className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900"
          data-testid={`${testidPrefix}-unknowns`}
        >
          <div className="font-semibold">Coverage gaps</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {unknowns.map((item, index) => (
              <li key={`${testidPrefix}-unknown-${index}`}>{sanitizeOperatorReference(item, "Review this missing signal.")}</li>
            ))}
          </ul>
        </div>
      )}
      {contradictions.length > 0 && (
        <div
          className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-900"
          data-testid={`${testidPrefix}-contradictions`}
        >
          <div className="font-semibold">Conflicts found</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {contradictions.map((item, index) => (
              <li key={`${testidPrefix}-contradiction-${index}`}>{sanitizeOperatorReference(item, "Review this conflicting signal.")}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function WorkflowRow({ row, expanded, onToggle, drill }) {
  const cfg = BAND[row.band] || BAND.amber;
  const lastSuccess = row.last_success?.ts;
  const lastFailure = row.last_failure?.ts;
  return (
    <>
      <tr
        data-testid={`trust-spine-row-${row.workflow}`}
        className={`border-t border-slate-100 cursor-pointer hover:bg-slate-50 ${
          row.band === "red" ? "bg-rose-50/30" : ""
        }`}
        onClick={() => onToggle(row.workflow)}
      >
        <td className="px-3 py-2 text-xs text-slate-500">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </td>
        <td className="px-3 py-2 font-mono text-xs text-slate-800">
          {humanizeToken(row.workflow)}
        </td>
        <td className="px-3 py-2">
          <Badge band={row.band} />
        </td>
        <td className="px-3 py-2 text-right text-xs">{row.events_24h}</td>
        <td
          className={`px-3 py-2 text-right text-xs ${
            row.failed_24h ? "text-rose-700 font-semibold" : "text-slate-600"
          }`}
        >
          {row.failed_24h}
        </td>
        <td className="px-3 py-2 text-right text-xs text-slate-600">
          {fmtPct(row.success_rate_24h)}
        </td>
        <td className="px-3 py-2 text-xs text-slate-600 whitespace-nowrap">
          {fmtTs(lastSuccess)}
        </td>
        <td
          className={`px-3 py-2 text-xs whitespace-nowrap ${
            lastFailure ? "text-rose-700" : "text-slate-400"
          }`}
        >
          {fmtTs(lastFailure)}
        </td>
        <td className="px-3 py-2 text-xs text-slate-600 max-w-md">
          <div className="truncate" title={sanitizeOperatorReference(row.reason, "No issue or next-step note was reported.")}>
            {sanitizeOperatorReference(row.reason, "No issue or next-step note was reported.")}
          </div>
          {row.remediation && (
            <div
              className="text-xs text-slate-500 italic truncate"
              title={sanitizeOperatorReference(row.remediation, "Review this next step.")}
            >
              → {sanitizeOperatorReference(row.remediation, "Review this next step.")}
            </div>
          )}
        </td>
      </tr>
      {expanded && (
        <tr className={cfg.tone}>
          <td colSpan={9} className="px-4 py-3">
            <div
              data-testid={`trust-spine-drill-${row.workflow}`}
              className="space-y-3"
            >
              <div className="flex items-center gap-4 text-xs text-slate-700">
                <div>
                  <span className="font-semibold text-slate-800">
                    Expected stages:
                  </span>{" "}
                  <code className="text-slate-600">
                    {(row.expected_stages || []).map((item) => sanitizeOperatorReference(item, "stage")).join(" → ") || "—"}
                  </code>
                </div>
              </div>
              {row.missing_stages && row.missing_stages.length > 0 && (
                <div
                  data-testid={`trust-spine-missing-${row.workflow}`}
                  className="text-xs text-amber-800"
                >
                  <span className="font-semibold">Missing in last 24h:</span>{" "}
                  {row.missing_stages.map((item) => sanitizeOperatorReference(item, "stage")).join(", ")}
                </div>
              )}
              {row.failure_stage && (
                <div className="text-xs text-rose-800">
                  <span className="font-semibold">Failure stage:</span>{" "}
                  <code>{sanitizeOperatorReference(row.failure_stage, "stage")}</code>
                  {row.last_failure?.failure_reason && (
                    <span className="ml-2 italic">
                      — {sanitizeOperatorReference(row.last_failure.failure_reason, "Review the latest failure reason.")}
                    </span>
                  )}
                </div>
              )}
              <TruthDisclosure
                ots={row.ots_truth}
                testidPrefix={`trust-spine-workflow-truth-${row.workflow}`}
              />
              <DrillTable drill={drill} workflow={row.workflow} />
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function DrillTable({ drill, workflow }) {
  if (!drill || drill.workflow !== workflow) {
    return (
      <div className="text-xs text-slate-500">
        <RotateCw className="inline-block animate-spin mr-1" size={12} />
        Loading latest events…
      </div>
    );
  }
  if (!drill.events?.length) {
    return (
      <div
        data-testid={`trust-spine-drill-empty-${workflow}`}
        className="text-xs text-slate-500 italic"
      >
        No lifecycle events recorded for this workflow yet.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-xs">
        <thead className="bg-slate-50 text-slate-500 uppercase tracking-wide text-xs">
          <tr>
            <th className="text-left px-2 py-1">When</th>
            <th className="text-left px-2 py-1">Stage</th>
            <th className="text-left px-2 py-1">Status</th>
            <th className="text-left px-2 py-1">Record</th>
            <th className="text-left px-2 py-1">Project</th>
            <th className="text-left px-2 py-1">Module</th>
            <th className="text-left px-2 py-1">Reason / Remediation</th>
          </tr>
        </thead>
        <tbody>
          {drill.events.slice(0, 50).map((e, i) => (
            <tr
              key={`${e.correlation_id}-${e.stage}-${i}`}
              className="border-t border-slate-100"
              data-testid={`trust-spine-drill-row-${workflow}-${i}`}
            >
              <td className="px-2 py-1 text-slate-600 whitespace-nowrap">
                {fmtTs(e.ts)}
              </td>
              <td className="px-2 py-1 font-mono">{e.stage}</td>
              <td
                className={`px-2 py-1 font-medium ${
                  e.status === "failed"
                    ? "text-rose-700"
                    : e.status === "skipped"
                    ? "text-amber-700"
                    : "text-emerald-700"
                }`}
              >
                {e.status}
              </td>
              <td className="px-2 py-1 font-mono text-slate-600">
                {e.record_id || "—"}
              </td>
              <td className="px-2 py-1 text-slate-600">
                {e.project_number || "—"}
              </td>
              <td className="px-2 py-1 text-slate-500 font-mono text-xs">
                {e.module || "—"}
              </td>
              <td className="px-2 py-1 text-slate-600">
                {e.failure_reason && (
                  <div className="text-rose-700">{e.failure_reason}</div>
                )}
                {e.remediation && (
                  <div className="italic text-slate-500">→ {e.remediation}</div>
                )}
                {!e.failure_reason && !e.remediation && "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function PlatformTrustDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastRun, setLastRun] = useState("");
  const [expandedRow, setExpandedRow] = useState(null);
  const [drill, setDrill] = useState(null);
  const [drillLoading, setDrillLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await api.get("/admin/trust-spine");
      setData(res.data);
      setLastRun(formatPlatformTime());
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "load failed";
      setError(String(msg));
      toast.error(`Trust spine: ${msg}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadDrill = useCallback(async (workflow) => {
    setDrillLoading(true);
    try {
      const res = await api.get(
        `/admin/trust-spine/workflow/${encodeURIComponent(workflow)}?limit=50`
      );
      setDrill(res.data);
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "drill failed";
      toast.error(`Drill-in: ${msg}`);
    } finally {
      setDrillLoading(false);
    }
  }, []);

  const onToggle = useCallback(
    (workflow) => {
      setExpandedRow((cur) => {
        const next = cur === workflow ? null : workflow;
        if (next) loadDrill(next);
        return next;
      });
    },
    [loadDrill]
  );

  useEffect(() => {
    run();
  }, [run]);

  const platformBand = data?.platform_band || "amber-no-activity";
  const platformCfg = BAND[platformBand] || BAND.amber;

  const summary = useMemo(() => {
    if (!data) return { green: 0, amber: 0, amberIdle: 0, red: 0 };
    const out = { green: 0, amber: 0, amberIdle: 0, red: 0 };
    for (const w of data.workflows || []) {
      if (w.band === "green") out.green++;
      else if (w.band === "amber") out.amber++;
      else if (w.band === "amber-no-activity") out.amberIdle++;
      else if (w.band === "red") out.red++;
    }
    return out;
  }, [data]);

  if (loading && !data) {
    return (
      <LegacyAdminModernShell
        title="Platform Trust Spine"
        subtitle="Primary lifecycle evidence for the Admin portal's critical workflows."
        breadcrumb={[{ label: "Governance & Trust", to: "/admin/governance-trust" }, { label: "Platform Trust Spine" }]}
        testidPrefix="platform-trust-spine"
      >
        <div
          data-testid="platform-trust-spine-loading"
          className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500"
        >
          <RotateCw className="inline-block animate-spin mr-2" size={14} />
          Loading Trust Spine…
        </div>
      </LegacyAdminModernShell>
    );
  }

  if (error && !data) {
    return (
      <LegacyAdminModernShell
        title="Platform Trust Spine"
        subtitle="Primary lifecycle evidence for the Admin portal's critical workflows."
        breadcrumb={[{ label: "Governance & Trust", to: "/admin/governance-trust" }, { label: "Platform Trust Spine" }]}
        testidPrefix="platform-trust-spine"
      >
        <div
          data-testid="platform-trust-spine-error"
          className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"
        >
          <strong>Trust Spine unavailable:</strong> {error}
          <div className="mt-2">
            <Button
              size="sm"
              variant="outline"
              onClick={run}
              data-testid="platform-trust-spine-retry"
            >
              <RotateCw size={14} className="mr-1" /> Retry
            </Button>
          </div>
        </div>
      </LegacyAdminModernShell>
    );
  }

  if (!data) return null;

  return (
    <LegacyAdminModernShell
      title="Platform Trust Spine"
      subtitle="Primary lifecycle evidence for the Admin portal's critical workflows."
      breadcrumb={[{ label: "Governance & Trust", to: "/admin/governance-trust" }, { label: "Platform Trust Spine" }]}
      testidPrefix="platform-trust-spine"
    >
    <div
      data-testid="platform-trust-spine-dashboard"
      className="space-y-4"
    >
      <section className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-700">
              Workflow completion truth
            </div>
            <h2 className="text-2xl font-black text-slate-950">How to read this page</h2>
            <p className="text-sm text-slate-700 leading-relaxed">
              This page is the source of truth for whether critical workflows actually completed, failed, or simply had no activity in the last 24 hours. A quiet workflow is shown as an evidence gap, not a false pass.
            </p>
          </div>
          <div className="grid min-w-[240px] grid-cols-2 gap-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Current determination</div>
              <div className="mt-1 text-sm font-semibold text-slate-950" data-testid="trust-spine-bounded-headline">{boundedHeadline(data?.ots_truth)}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 font-mono">Latest refresh</div>
              <div className="mt-1 text-sm font-semibold text-slate-950">{lastRun || "Not refreshed in this session yet"}</div>
            </div>
          </div>
        </div>
      </section>

      <div
        className={`rounded-2xl border p-4 ${platformCfg.tone}`}
        data-testid="trust-spine-platform-band"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-3">
            <platformCfg.Icon size={22} className="text-slate-700" />
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Platform Trust Spine
              </h3>
              <p className="text-xs text-slate-500">
                Workflow lifecycle evidence across the last 24 hours ·{" "}
                {lastRun && `last refresh ${lastRun}`}
              </p>
              <p
                className="mt-1 text-xs font-medium text-slate-700"
                data-testid="trust-spine-bounded-headline"
              >
                {boundedHeadline(data?.ots_truth)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge band={platformBand} />
            <Button
              size="sm"
              variant="outline"
              onClick={run}
              disabled={loading}
              data-testid="trust-spine-refresh"
            >
              <RotateCw
                size={14}
                className={`mr-1 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>
        </div>

        <div className="mt-3 grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="rounded-xl border border-slate-200 bg-white px-3 py-2">
            <div className="text-xs text-slate-500">Workflows</div>
            <div
              className="text-lg font-semibold text-slate-900"
              data-testid="trust-spine-stat-total"
            >
              {data.workflow_count}
            </div>
          </div>
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2">
            <div className="text-xs text-emerald-700">Trusted</div>
            <div
              className="text-lg font-semibold text-emerald-900"
              data-testid="trust-spine-stat-green"
            >
              {summary.green}
            </div>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
            <div className="text-xs text-amber-700">Missing evidence</div>
            <div
              className="text-lg font-semibold text-amber-900"
              data-testid="trust-spine-stat-amber"
            >
              {summary.amber}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <div className="text-xs text-slate-600">Idle 24h</div>
            <div
              className="text-lg font-semibold text-slate-900"
              data-testid="trust-spine-stat-idle"
            >
              {summary.amberIdle}
            </div>
          </div>
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2">
            <div className="text-xs text-rose-700">Failing</div>
            <div
              className="text-lg font-semibold text-rose-900"
              data-testid="trust-spine-stat-red"
            >
              {summary.red}
            </div>
          </div>
        </div>

        <div className="mt-3 text-xs text-slate-600 flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-1">
            <Activity size={12} /> {data.total_events_24h} lifecycle events in
            last 24h
          </span>
          {data.total_failed_24h > 0 && (
            <span className="flex items-center gap-1 text-rose-700 font-medium">
              <XCircle size={12} /> {data.total_failed_24h} failed
            </span>
          )}
          <span className="flex items-center gap-1 text-slate-500">
            <Clock size={12} /> {data.generated_at && fmtTs(data.generated_at)}
          </span>
        </div>

        <TruthDisclosure ots={data?.ots_truth} testidPrefix="trust-spine-ots-disclosure" />

        <OwnershipNote
          surface={data.truth_surface}
          relationship={data.truth_relationship}
          primaryStatus={data.canonical_status}
          checkedAt={data.generated_at}
        />
      </div>

      <div
        className="rounded-2xl border border-slate-200 bg-white"
        data-testid="trust-spine-workflow-table"
      >
        <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
          <Activity size={16} className="text-slate-600" />
          <h4 className="text-sm font-semibold text-slate-900">
            Per-Workflow Lifecycle Health
          </h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs uppercase tracking-wide bg-slate-50 text-slate-500">
              <tr>
                <th className="px-3 py-2 w-6" />
                <th className="text-left px-3 py-2">workflow</th>
                <th className="text-left px-3 py-2">band</th>
                <th className="text-right px-3 py-2">events 24h</th>
                <th className="text-right px-3 py-2">failed 24h</th>
                <th className="text-right px-3 py-2">success rate</th>
                <th className="text-left px-3 py-2">last success</th>
                <th className="text-left px-3 py-2">last failure</th>
                <th className="text-left px-3 py-2">reason / remediation</th>
              </tr>
            </thead>
            <tbody>
              {(data.workflows || []).map((row) => (
                <WorkflowRow
                  key={row.workflow}
                  row={row}
                  expanded={expandedRow === row.workflow}
                  onToggle={onToggle}
                  drill={
                    expandedRow === row.workflow && !drillLoading ? drill : null
                  }
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
    </LegacyAdminModernShell>
  );
}
