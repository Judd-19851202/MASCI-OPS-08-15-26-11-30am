/**
 * <OperationsTrustCenter> — Track 15.76A capstone.
 *
 * Single read-only screen the operator can open to answer:
 *   "Is the platform healthy right now?  Why?  What needs action?"
 * in under one minute. No shell scripts. No DevTools. No Mongo.
 *
 * Consumes:
 *   GET /api/admin/operations-trust-center
 *
 * Surfaces (in order, top-to-bottom):
 *   1. Trust Score band (0-100) + headline reason
 *   2. Executive summary strip (workflows trusted / amber / idle / red,
 *      last success, last failure, master-data band, audit health)
 *   3. Master-data trust card (operator-readable findings + remediation)
 *   4. Per-workflow table with operator-friendly summary + remediation
 *      on every red/amber row; click-to-expand drill-in still available.
 *
 * Hard rules honoured:
 *   - No fake green: red caps at 59, amber caps at 84.
 *   - Every red/amber row shows what failed, why, and what to do.
 *   - Idle workflows render as "No activity 24h" (amber tone), never green.
 */
import React, { useState, useCallback, useEffect } from "react";
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
  Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

const BAND_STYLE = {
  green: {
    tone: "bg-emerald-50 border-emerald-200",
    pill: "bg-emerald-100 text-emerald-800 border-emerald-300",
    Icon: ShieldCheck,
    label: "Trusted",
  },
  amber: {
    tone: "bg-amber-50 border-amber-200",
    pill: "bg-amber-100 text-amber-800 border-amber-300",
    Icon: AlertTriangle,
    label: "Missing evidence",
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
    label: "Failing",
  },
};

function Badge({ band, children }) {
  const cfg = BAND_STYLE[band] || BAND_STYLE.amber;
  const { Icon } = cfg;
  return (
    <span
      data-testid={`otc-band-${band}`}
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
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function fmtPct(rate) {
  if (rate == null || Number.isNaN(rate)) return "—";
  return `${Math.round(rate * 1000) / 10}%`;
}

function ScoreRing({ score, band }) {
  const cfg = BAND_STYLE[band] || BAND_STYLE.amber;
  const colour =
    band === "green"
      ? "#059669"
      : band === "amber"
      ? "#d97706"
      : band === "red"
      ? "#dc2626"
      : "#475569";
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (Math.max(0, Math.min(100, score)) / 100) * circumference;
  return (
    <div
      className="relative inline-flex items-center justify-center"
      data-testid="otc-score-ring"
    >
      <svg width="108" height="108" className="-rotate-90">
        <circle cx="54" cy="54" r="42" stroke="#e2e8f0" strokeWidth="10" fill="none" />
        <circle
          cx="54"
          cy="54"
          r="42"
          stroke={colour}
          strokeWidth="10"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 600ms ease-out" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <div
          className="text-3xl font-bold"
          style={{ color: colour }}
          data-testid="otc-score-value"
        >
          {score}
        </div>
        <div className="text-xs uppercase tracking-wide text-slate-500">
          {cfg.label}
        </div>
      </div>
    </div>
  );
}

function MasterDataCard({ master }) {
  if (!master) return null;
  const findings = master.findings || [];
  const band = master.band || "green";
  const cfg = BAND_STYLE[band] || BAND_STYLE.amber;
  return (
    <div
      className={`rounded-2xl border p-4 ${cfg.tone}`}
      data-testid="otc-master-data-card"
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <Database size={16} className="text-slate-700" />
          <h4 className="text-sm font-semibold text-slate-900">
            Master Data Trust
          </h4>
        </div>
        <Badge band={band} />
      </div>
      {findings.length === 0 ? (
        <div className="text-xs text-slate-500">
          All master-data sources clean — no drift detected.
        </div>
      ) : (
        <ul className="space-y-2">
          {findings.map((f, i) => {
            const fcfg = BAND_STYLE[f.band] || BAND_STYLE.amber;
            return (
              <li
                key={`${f.code}-${i}`}
                className="flex items-start gap-3 p-3 rounded-lg bg-white border border-slate-200"
                data-testid={`otc-md-finding-${f.code}`}
              >
                <fcfg.Icon
                  size={16}
                  className={
                    f.band === "red"
                      ? "text-rose-600 mt-0.5"
                      : "text-amber-600 mt-0.5"
                  }
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-slate-900">
                    {f.summary}
                  </div>
                  <div className="text-xs text-slate-600 italic mt-0.5">
                    → {f.remediation}
                  </div>
                  {f.samples && f.samples.length > 0 && (
                    <div className="text-xs text-slate-500 mt-1 font-mono truncate">
                      Examples: {f.samples.slice(0, 5).join(" · ")}
                    </div>
                  )}
                </div>
                <Badge band={f.band} />
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function WorkflowRow({ row, expanded, onToggle, drill }) {
  const cfg = BAND_STYLE[row.band] || BAND_STYLE.amber;
  const ls = row.last_success?.ts;
  const lf = row.last_failure?.ts;
  return (
    <>
      <tr
        data-testid={`otc-row-${row.workflow}`}
        className={`border-t border-slate-100 cursor-pointer hover:bg-slate-50 ${
          row.band === "red" ? "bg-rose-50/30" : ""
        }`}
        onClick={() => onToggle(row.workflow)}
      >
        <td className="px-3 py-2 text-xs text-slate-500">
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </td>
        <td className="px-3 py-2 text-sm font-medium text-slate-900">
          {row.workflow_label || row.workflow}
          <div className="text-xs text-slate-500 font-mono">
            {row.workflow}
          </div>
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
        <td className="px-3 py-2 text-xs text-slate-600 max-w-xl">
          <div className="text-slate-800">
            {row.operator_summary || row.reason}
          </div>
          {row.operator_remediation && (
            <div className="text-xs text-slate-500 italic mt-0.5">
              → {row.operator_remediation}
            </div>
          )}
        </td>
      </tr>
      {expanded && (
        <tr className={cfg.tone}>
          <td colSpan={7} className="px-4 py-3">
            <div
              data-testid={`otc-drill-${row.workflow}`}
              className="space-y-3"
            >
              <div className="text-xs text-slate-700">
                <span className="font-semibold">Expected stages:</span>{" "}
                <code className="text-slate-600">
                  {(row.expected_stages || []).join(" → ") || "—"}
                </code>
              </div>
              {row.missing_stages && row.missing_stages.length > 0 && (
                <div
                  data-testid={`otc-missing-${row.workflow}`}
                  className="text-xs text-amber-800"
                >
                  <span className="font-semibold">
                    Missing in last 24h:
                  </span>{" "}
                  {row.missing_stages.join(", ")}
                </div>
              )}
              {row.failure_stage && (
                <div className="text-xs text-rose-800">
                  <span className="font-semibold">Failure stage:</span>{" "}
                  <code>{row.failure_stage}</code>
                </div>
              )}
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
        data-testid={`otc-drill-empty-${workflow}`}
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
            <th className="text-left px-2 py-1">Reason / Remediation</th>
          </tr>
        </thead>
        <tbody>
          {drill.events.slice(0, 50).map((e, i) => (
            <tr
              key={`${e.correlation_id}-${e.stage}-${i}`}
              className="border-t border-slate-100"
              data-testid={`otc-drill-row-${workflow}-${i}`}
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
              <td className="px-2 py-1 text-slate-600">
                {e.failure_reason && (
                  <div className="text-rose-700">{e.failure_reason}</div>
                )}
                {e.remediation && (
                  <div className="italic text-slate-500">
                    → {e.remediation}
                  </div>
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

export default function OperationsTrustCenter() {
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
      const res = await api.get("/admin/operations-trust-center");
      setData(res.data);
      setLastRun(new Date().toLocaleString());
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "load failed";
      setError(String(msg));
      toast.error(`Trust Center: ${msg}`);
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

  if (loading && !data) {
    return (
      <div
        data-testid="otc-loading"
        className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500"
      >
        <RotateCw className="inline-block animate-spin mr-2" size={14} />
        Loading Operations Trust Center…
      </div>
    );
  }

  if (error && !data) {
    return (
      <div
        data-testid="otc-error"
        className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"
      >
        <strong>Trust Center unavailable:</strong> {error}
        <div className="mt-2">
          <Button size="sm" variant="outline" onClick={run} data-testid="otc-retry">
            <RotateCw size={14} className="mr-1" /> Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const summary = data.summary || {};
  const band = data.score_band || "amber";
  const cfg = BAND_STYLE[band] || BAND_STYLE.amber;

  return (
    <div data-testid="operations-trust-center" className="space-y-4">
      {/* 1 · Headline trust score + reason */}
      <div
        className={`rounded-2xl border p-4 ${cfg.tone}`}
        data-testid="otc-headline"
      >
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <ScoreRing score={data.trust_score ?? 0} band={band} />
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Operations Trust Center
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Track 15.76A · workflow + routing + audit + master-data
                continuous verification
              </p>
              <p
                className="text-sm text-slate-800 mt-2 max-w-xl"
                data-testid="otc-headline-reason"
              >
                <strong>{data.score_band_label}.</strong>{" "}
                {data.score_reason}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge band={band} />
            <Button
              size="sm"
              variant="outline"
              onClick={run}
              disabled={loading}
              data-testid="otc-refresh"
            >
              <RotateCw
                size={14}
                className={`mr-1 ${loading ? "animate-spin" : ""}`}
              />
              Refresh
            </Button>
          </div>
        </div>

        {/* Why is the score what it is? — top 3 penalty inputs visible. */}
        {data.score_inputs && data.score_inputs.length > 0 && (
          <div
            className="mt-3 text-xs text-slate-700 grid grid-cols-1 sm:grid-cols-3 gap-2"
            data-testid="otc-score-inputs"
          >
            {data.score_inputs.slice(0, 3).map((i, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-white bg-white/70 px-3 py-2"
              >
                <div className="font-semibold text-slate-800">
                  −{i.penalty}
                </div>
                <div className="text-slate-600">{i.reason}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 2 · Executive summary strip */}
      <div
        className="rounded-2xl border border-slate-200 bg-white p-4"
        data-testid="otc-summary-strip"
      >
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2">
            <div className="text-xs text-emerald-700">Trusted</div>
            <div
              className="text-lg font-semibold text-emerald-900"
              data-testid="otc-stat-trusted"
            >
              {summary.workflows_trusted ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
            <div className="text-xs text-amber-700">Missing evidence</div>
            <div
              className="text-lg font-semibold text-amber-900"
              data-testid="otc-stat-amber"
            >
              {summary.workflows_amber ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
            <div className="text-xs text-slate-600">Idle 24h</div>
            <div
              className="text-lg font-semibold text-slate-900"
              data-testid="otc-stat-idle"
            >
              {summary.workflows_idle ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2">
            <div className="text-xs text-rose-700">Failing</div>
            <div
              className="text-lg font-semibold text-rose-900"
              data-testid="otc-stat-red"
            >
              {summary.workflows_red ?? 0}
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white px-3 py-2">
            <div className="text-xs text-slate-500">Master data</div>
            <div data-testid="otc-stat-master-data">
              <Badge band={summary.master_data_band || "green"} />
            </div>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white px-3 py-2">
            <div className="text-xs text-slate-500">Events 24h</div>
            <div
              className="text-lg font-semibold text-slate-900"
              data-testid="otc-stat-events"
            >
              {summary.events_24h ?? 0}
              {summary.failed_24h > 0 && (
                <span className="ml-1 text-xs text-rose-700">
                  · {summary.failed_24h} failed
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="mt-3 text-xs text-slate-600 flex flex-wrap items-center gap-4">
          <span className="flex items-center gap-1">
            <Activity size={12} />
            Last success:{" "}
            <strong className="text-slate-800">
              {fmtTs(summary.last_success_at)}
            </strong>
          </span>
          <span
            className={`flex items-center gap-1 ${
              summary.last_failure_at ? "text-rose-700" : "text-slate-500"
            }`}
          >
            <XCircle size={12} />
            Last failure:{" "}
            <strong>{fmtTs(summary.last_failure_at)}</strong>
          </span>
          <span className="flex items-center gap-1 text-slate-500">
            <Clock size={12} /> {lastRun && `refreshed ${lastRun}`}
          </span>
        </div>
      </div>

      {/* 3 · Master Data Trust card */}
      <MasterDataCard master={data.master_data} />

      {/* 4 · Per-workflow lifecycle table */}
      <div
        className="rounded-2xl border border-slate-200 bg-white"
        data-testid="otc-workflow-table"
      >
        <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
          <Activity size={16} className="text-slate-600" />
          <h4 className="text-sm font-semibold text-slate-900">
            Workflow Lifecycle Health
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
                <th className="text-left px-3 py-2">summary / remediation</th>
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
                    expandedRow === row.workflow && !drillLoading
                      ? drill
                      : null
                  }
                />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
