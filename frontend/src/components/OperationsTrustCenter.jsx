/**
 * <OperationsTrustCenter> — Track 15.76B finalization.
 *
 * Single operator screen that answers
 *
 *   "Can I trust this platform to run operations today?"
 *
 * in under 30 seconds, with every claim backed by Trust Spine
 * evidence. Layout (top to bottom):
 *
 *   1. Executive Status Header — band + narrative + ETA
 *   2. Trust Score with 7-category breakdown
 *   3. Trend sparkline (24h / 7d / 30d toggle)
 *   4. Critical Operational Problems  (live blocking issues)
 *   5. Operational Warnings           (attention needed)
 *   6. Data Improvement Opportunities (pure hygiene)
 *   7. Operator Action Panel          (sorted, with deep links)
 *   8. Subsystem Health Cards
 *   9. Workflow Lifecycle table       (drill-down)
 *
 * Reads:
 *   GET /api/admin/operations-trust-center?trend_hours={24|168|720}
 *   GET /api/admin/trust-spine/workflow/{workflow}
 */
import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
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
  Zap,
  Wrench,
  Sparkles,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { TruthOwnerPanel } from "@/components/admin/trust/TrustPrimitives";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

const BAND_STYLE = {
  green: {
    tone: "bg-emerald-50 border-emerald-200",
    softTone: "bg-emerald-50/50",
    pill: "bg-emerald-100 text-emerald-800 border-emerald-300",
    bar: "bg-emerald-500",
    Icon: ShieldCheck,
    label: "Green score band",
    headlineColor: "#059669",
  },
  amber: {
    tone: "bg-amber-50 border-amber-200",
    softTone: "bg-amber-50/50",
    pill: "bg-amber-100 text-amber-800 border-amber-300",
    bar: "bg-amber-500",
    Icon: AlertTriangle,
    label: "Amber score band",
    headlineColor: "#d97706",
  },
  "amber-no-activity": {
    tone: "bg-slate-50 border-slate-200",
    softTone: "bg-slate-50/50",
    pill: "bg-slate-100 text-slate-700 border-slate-300",
    bar: "bg-slate-400",
    Icon: Hourglass,
    label: "Idle score band",
    headlineColor: "#475569",
  },
  red: {
    tone: "bg-rose-50 border-rose-200",
    softTone: "bg-rose-50/50",
    pill: "bg-rose-100 text-rose-800 border-rose-300",
    bar: "bg-rose-500",
    Icon: XCircle,
    label: "Red score band",
    headlineColor: "#dc2626",
  },
};

function boundedHeadline(ots) {
  const claim = ots?.permitted_claim || "UNKNOWN";
  const evaluation = ots?.truth_evaluation || "UNVERIFIABLE";
  const contradictions = ots?.contradictory_evidence || [];

  if (evaluation === "UNVERIFIABLE" || claim === "UNKNOWN") {
    return "Trust Spine owner truth is unavailable or incomplete, so this derived surface cannot advance a trust claim.";
  }
  if (contradictions.length > 0 || evaluation === "MISMATCH") {
    return "Derived operational summary found contradictions. Follow Trust Spine owner truth and investigate the conflicts below.";
  }
  if (claim === "OBSERVED") {
    return "Only observed operational conditions are supported right now. Stronger trust claims are intentionally blocked.";
  }
  if (claim === "CORRELATED") {
    return "Operational score remains a derived summary. The bounded claim is correlated only and cannot exceed Trust Spine.";
  }
    return "Derived operational summary is available, but the approved source record still stays with Trust Spine.";
}

function TruthDisclosure({ ots, scoreBandLabel, score, testidPrefix = "otc-truth-disclosure" }) {
  if (!ots) return null;
  const unknowns = ots.unknowns || [];
  const contradictions = ots.contradictory_evidence || [];

  return (
    <div className="space-y-2" data-testid={`${testidPrefix}-wrapper`}>
      <div
        className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700"
        data-testid={`${testidPrefix}-score-vs-claim`}
      >
        <span className="font-semibold text-slate-900">Score vs claim:</span>{" "}
        Score {score ?? 0} and {scoreBandLabel || "derived score band"} remain operator summaries. The approved claim stays {ots.permitted_claim || "UNKNOWN"} and cannot exceed Trust Spine.
      </div>
      <div
        className="grid gap-2 rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-700 sm:grid-cols-2 lg:grid-cols-4"
        data-testid={testidPrefix}
      >
        <div className="break-words" data-testid={`${testidPrefix}-subject`}><span className="font-semibold text-slate-900">Page focus:</span> {ots.truth_subject || "UNKNOWN"}</div>
        <div className="break-words" data-testid={`${testidPrefix}-claim`}><span className="font-semibold text-slate-900">Permitted claim:</span> {ots.permitted_claim || "UNKNOWN"}</div>
        <div className="break-words" data-testid={`${testidPrefix}-ceiling`}><span className="font-semibold text-slate-900">Claim ceiling:</span> {ots.claim_ceiling || "UNKNOWN"}</div>
        <div className="break-words" data-testid={`${testidPrefix}-confidence`}><span className="font-semibold text-slate-900">Confidence:</span> {ots.evidence_confidence || "UNKNOWN"}</div>
        <div className="break-words" data-testid={`${testidPrefix}-state`}><span className="font-semibold text-slate-900">Evidence state:</span> {ots.evidence_state || "unknown"}</div>
        <div className="break-words" data-testid={`${testidPrefix}-quality`}><span className="font-semibold text-slate-900">Evidence quality:</span> {ots.evidence_quality || "UNKNOWN"}</div>
        <div className="break-words" data-testid={`${testidPrefix}-basis`}><span className="font-semibold text-slate-900">Evidence basis:</span> {(ots.claim_basis || []).join(" · ") || "—"}</div>
        <div className="break-words" data-testid={`${testidPrefix}-audit`}><span className="font-semibold text-slate-900">Audit reference:</span> {ots.audit_reference || "—"}</div>
      </div>
      {unknowns.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900" data-testid={`${testidPrefix}-unknowns`}>
          <div className="font-semibold">Unknowns / gaps</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {unknowns.map((item, index) => <li key={`${testidPrefix}-unknown-${index}`}>{item}</li>)}
          </ul>
        </div>
      )}
      {contradictions.length > 0 && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-900" data-testid={`${testidPrefix}-contradictions`}>
          <div className="font-semibold">Contradictions</div>
          <ul className="mt-1 list-disc space-y-1 pl-4">
            {contradictions.map((item, index) => <li key={`${testidPrefix}-contradiction-${index}`}>{item}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

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
    return formatPlatformTime(iso);
  } catch {
    return iso;
  }
}

function fmtPct(rate) {
  if (rate == null || Number.isNaN(rate)) return "—";
  return `${Math.round(rate * 1000) / 10}%`;
}

function fmtEta(seconds) {
  if (!seconds) return "—";
  if (seconds < 60) return `${seconds}s`;
  const m = Math.round(seconds / 60);
  if (m < 60) return `${m} min`;
  return `${Math.round(m / 60)}h`;
}

function ScoreRing({ score, band }) {
  const cfg = BAND_STYLE[band] || BAND_STYLE.amber;
  const circ = 2 * Math.PI * 46;
  const offset = circ - (Math.max(0, Math.min(100, score)) / 100) * circ;
  return (
    <div
      className="relative inline-flex items-center justify-center"
      data-testid="otc-score-ring"
    >
      <svg width="120" height="120" className="-rotate-90">
        <circle cx="60" cy="60" r="46" stroke="#e2e8f0" strokeWidth="10" fill="none" />
        <circle
          cx="60"
          cy="60"
          r="46"
          stroke={cfg.headlineColor}
          strokeWidth="10"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 600ms ease-out" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <div
          className="text-4xl font-bold"
          style={{ color: cfg.headlineColor }}
          data-testid="otc-score-value"
        >
          {score}
        </div>
        <div className="text-[10px] uppercase tracking-wider text-slate-500">
          / 100
        </div>
      </div>
    </div>
  );
}

function TrendSparkline({ points, height = 40 }) {
  if (!points || points.length < 2) {
    return (
      <div className="text-xs text-slate-400 italic">
        Trend will appear once more snapshots are collected.
      </div>
    );
  }
  const w = 400;
  const h = height;
  const ys = points.map((p) => p.score ?? 0);
  const min = Math.min(...ys, 60);
  const max = 100;
  const span = max - min || 1;
  const stepX = w / (points.length - 1);
  const path = points
    .map((p, i) => {
      const x = i * stepX;
      const y = h - ((p.score - min) / span) * (h - 6) - 3;
      return `${i === 0 ? "M" : "L"} ${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = points[points.length - 1].score;
  const first = points[0].score;
  const delta = last - first;
  const TrendIcon =
    delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus;
  return (
    <div className="flex items-center gap-3" data-testid="otc-trend-spark">
      <svg
        width="100%"
        viewBox={`0 0 ${w} ${h}`}
        preserveAspectRatio="none"
        className="h-10 flex-1 max-w-md"
      >
        <path d={path} stroke="#0f172a" strokeWidth="1.5" fill="none" />
      </svg>
      <div
        className={`flex items-center gap-1 text-xs ${
          delta > 0
            ? "text-emerald-700"
            : delta < 0
            ? "text-rose-700"
            : "text-slate-500"
        }`}
      >
        <TrendIcon size={14} />
        {delta > 0 ? "+" : ""}
        {delta} pts
      </div>
    </div>
  );
}

function CategoryBar({ id, label, score, band, headline, onClick }) {
  const cfg = BAND_STYLE[band] || BAND_STYLE.amber;
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={`otc-category-${id}`}
      className="w-full text-left rounded-lg border border-slate-200 bg-white px-3 py-2 hover:border-slate-300 transition-colors"
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="text-xs font-medium text-slate-700">{label}</div>
        <div className="text-xs font-semibold text-slate-900">{score}</div>
      </div>
      <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
        <div
          className={`h-full ${cfg.bar}`}
          style={{ width: `${Math.max(2, score)}%`, transition: "width 500ms" }}
        />
      </div>
      <div className="text-[11px] text-slate-500 mt-1 truncate" title={headline}>
        {headline || "all clear"}
      </div>
    </button>
  );
}

function FindingItem({ f, testid }) {
  const cfg = BAND_STYLE[f.band] || BAND_STYLE.amber;
  return (
    <li
      className="flex items-start gap-3 p-3 rounded-lg bg-white border border-slate-200"
      data-testid={testid}
    >
      <cfg.Icon
        size={16}
        className={`mt-0.5 ${
          f.band === "red" ? "text-rose-600" : "text-amber-600"
        }`}
      />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-900">{f.summary}</div>
        <div className="text-xs text-slate-600 italic mt-0.5">
          → {f.remediation}
        </div>
        {f.impact && (
          <div className="text-xs text-slate-500 mt-1">
            <span className="font-medium">Impact:</span> {f.impact}
          </div>
        )}
        {f.samples && f.samples.length > 0 && (
          <div className="text-xs text-slate-500 mt-1 font-mono truncate">
            Examples: {f.samples.slice(0, 6).join(" · ")}
          </div>
        )}
        {f.remediation_link && (
          <Link
            to={f.remediation_link}
            className="inline-flex items-center gap-1 text-xs text-slate-700 hover:text-slate-900 underline mt-2"
          >
            Open fix-it page <ExternalLink size={11} />
          </Link>
        )}
      </div>
      <Badge band={f.band} />
    </li>
  );
}

function FindingSection({ id, title, Icon, findings, emptyText, tone }) {
  return (
    <div
      className={`rounded-2xl border p-4 ${tone}`}
      data-testid={`otc-section-${id}`}
    >
      <div className="flex items-center gap-2 mb-3">
        <Icon size={16} className="text-slate-700" />
        <h4 className="text-sm font-semibold text-slate-900">{title}</h4>
        <span className="text-xs text-slate-500">({findings.length})</span>
      </div>
      {findings.length === 0 ? (
        <div className="text-xs text-slate-500 italic">{emptyText}</div>
      ) : (
        <ul className="space-y-2">
          {findings.map((f, i) => (
            <FindingItem
              key={`${f.code}-${i}`}
              f={f}
              testid={`otc-${id}-${f.code}`}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

function OperatorActionPanel({ actions, totalEtaSeconds }) {
  if (!actions || actions.length === 0) {
    return (
      <div
        className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4"
        data-testid="otc-action-panel-empty"
      >
        <div className="flex items-center gap-2">
          <ShieldCheck size={16} className="text-emerald-700" />
          <h4 className="text-sm font-semibold text-emerald-900">
            No immediate derived actions surfaced
          </h4>
        </div>
        <p className="text-xs text-emerald-800 mt-1">
          The current scoring model did not surface action items. Trust Spine still remains the main owner for bounded trust claims.
        </p>
      </div>
    );
  }
  return (
    <div
      className="rounded-2xl border border-slate-200 bg-white p-4"
      data-testid="otc-action-panel"
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <Zap size={16} className="text-amber-600" />
          <h4 className="text-sm font-semibold text-slate-900">
            What should I do right now?
          </h4>
        </div>
        {totalEtaSeconds > 0 && (
          <div
            className="text-xs text-slate-600"
            data-testid="otc-action-eta"
          >
            critical work: ~{fmtEta(totalEtaSeconds)}
          </div>
        )}
      </div>
      <ol className="space-y-2">
        {actions.map((a, idx) => (
          <li
            key={a.id}
            className="flex items-start gap-3 p-3 rounded-lg bg-white border border-slate-200"
            data-testid={`otc-action-${a.id}`}
          >
            <div
              className={`shrink-0 inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-semibold border ${
                a.priority === "critical"
                  ? "bg-rose-100 text-rose-800 border-rose-300"
                  : a.priority === "warning"
                  ? "bg-amber-100 text-amber-800 border-amber-300"
                  : "bg-slate-100 text-slate-700 border-slate-300"
              }`}
            >
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-900">
                {a.title}
              </div>
              <div className="text-xs text-slate-600 italic mt-0.5">
                → {a.remediation}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                <span className="font-medium">Impact:</span> {a.impact} ·{" "}
                <span className="font-medium">Est:</span>{" "}
                {fmtEta(a.estimated_remediation_seconds)}
              </div>
            </div>
            {a.remediation_link && (
              <Link
                to={a.remediation_link}
                className="shrink-0 inline-flex items-center gap-1 text-xs text-slate-700 hover:text-slate-900 underline self-start"
              >
                Open <ExternalLink size={11} />
              </Link>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}

function SubsystemCards({ subsystems }) {
  if (!subsystems || subsystems.length === 0) return null;
  return (
    <div
      className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2"
      data-testid="otc-subsystems"
    >
      {subsystems.map((s) => (
        <CategoryBar
          key={s.id}
          id={s.id}
          label={s.label}
          score={s.score}
          band={s.band}
          headline={s.headline}
        />
      ))}
    </div>
  );
}

function WorkflowRow({ row, expanded, onToggle, drill }) {
  const cfg = BAND_STYLE[row.band] || BAND_STYLE.amber;
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
        <tr className={cfg.softTone}>
          <td colSpan={7} className="px-4 py-3">
            <div data-testid={`otc-drill-${row.workflow}`} className="space-y-3">
              <div className="text-xs text-slate-700">
                <span className="font-semibold">Expected stages:</span>{" "}
                <code className="text-slate-600">
                  {(row.expected_stages || []).join(" → ") || "—"}
                </code>
              </div>
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
      <div className="text-xs text-slate-500 italic">
        No lifecycle events recorded for this workflow yet.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-xs">
        <thead className="bg-slate-50 text-slate-500 uppercase tracking-wide text-[10px]">
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

const TREND_OPTIONS = [
  { label: "24h", hours: 24 },
  { label: "7d", hours: 168 },
  { label: "30d", hours: 720 },
];

export default function OperationsTrustCenter() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastRun, setLastRun] = useState("");
  const [trendHours, setTrendHours] = useState(24);
  const [expandedRow, setExpandedRow] = useState(null);
  const [drill, setDrill] = useState(null);
  const [drillLoading, setDrillLoading] = useState(false);
  const [showScoreDetail, setShowScoreDetail] = useState(false);

  const run = useCallback(
    async (hours = trendHours) => {
      setLoading(true);
      setError("");
      try {
        const res = await api.get(
          `/admin/operations-trust-center?trend_hours=${hours}`
        );
        setData(res.data);
        setLastRun(formatPlatformTime());
      } catch (e) {
        const msg = e?.response?.data?.detail || e?.message || "load failed";
        setError(String(msg));
        toast.error(`Trust Center: ${msg}`);
      } finally {
        setLoading(false);
      }
    },
    [trendHours]
  );

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
    run(trendHours);
  }, [trendHours, run]);

  const band = data?.score_band || "amber";
  const cfg = BAND_STYLE[band] || BAND_STYLE.amber;
  const summary = data?.summary || {};

  const categoryRows = useMemo(() => {
    if (!data?.categories) return [];
    return data.subsystems || [];
  }, [data]);

  const dispositionMeta = (
    <div
      data-testid="operations-trust-center-disposition"
      className="hidden"
      data-trust-surface-id="operations_trust_center"
      data-trust-disposition="ACTIVE_REPAIRED"
      data-trust-role="DERIVED_CONSUMER"
      data-canonical-owner="trust_spine"
    />
  );

  if (loading && !data) {
    return (
      <div
        data-testid="otc-loading"
        className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500"
      >
        {dispositionMeta}
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
        {dispositionMeta}
        <strong>Trust Center unavailable:</strong> {error}
        <div className="mt-2">
          <Button size="sm" variant="outline" onClick={() => run(trendHours)} data-testid="otc-retry">
            <RotateCw size={14} className="mr-1" /> Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div data-testid="operations-trust-center" className="space-y-4">
      {dispositionMeta}
      {/* 1 · Executive Status Header — read in 15 seconds */}
      <div
        className={`rounded-2xl border p-5 ${cfg.tone}`}
        data-testid="otc-headline"
      >
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-5">
          <div className="flex items-start gap-5 flex-1 min-w-0">
            <ScoreRing score={data.trust_score ?? 0} band={band} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-slate-900">
                  Operations Trust Center
                </h3>
                <Badge band={band} />
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Workflow + routing + audit + master-data
                derived operational summary
              </p>
              <p
                className="text-sm text-slate-800 mt-2"
                data-testid="otc-bounded-headline"
              >
                <span className="font-semibold text-slate-900">Bounded disclosure:</span>{" "}
                {boundedHeadline(data.ots_truth || {})}
              </p>
              <p
                className="text-sm text-slate-800 mt-2"
                data-testid="otc-narrative"
              >
                <strong>{data.score_band_label}.</strong>{" "}
                {data.executive_narrative}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Button
              size="sm"
              variant="outline"
              onClick={() => run(trendHours)}
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

        <div className="mt-4">
          <TruthOwnerPanel
            title="Derived trust relationship"
            surface={data.truth_surface}
            relationship={data.truth_relationship}
            checkedAt={summary.last_success_at || lastRun}
            testidPrefix="operations-trust-owner-panel"
          />
        </div>

        <div className="mt-4">
          <TruthDisclosure ots={data.ots_truth || {}} scoreBandLabel={data.score_band_label} score={data.trust_score} />
        </div>

        {/* Why isn't this 100? */}
        {data.score_inputs && data.score_inputs.length > 0 && (
          <div className="mt-4">
            <button
              type="button"
              onClick={() => setShowScoreDetail((v) => !v)}
              className="text-xs text-slate-700 underline hover:text-slate-900"
              data-testid="otc-why-toggle"
            >
              {showScoreDetail
                ? "Hide trust score breakdown"
                : "Why isn't this 100?"}
            </button>
            {showScoreDetail && (
              <div
                className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2"
                data-testid="otc-score-inputs"
              >
                {data.score_inputs.map((i, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-white bg-white/80 px-3 py-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-rose-700">
                        −{i.penalty}
                      </span>
                      <span className="text-[10px] uppercase tracking-wider text-slate-500">
                        {i.category}
                      </span>
                    </div>
                    <div className="text-slate-700 mt-1">{i.reason}</div>
                    {Array.isArray(i.evidence) && i.evidence.length > 0 && (
                      <div className="text-[11px] text-slate-500 mt-1 font-mono truncate">
                        {i.evidence.slice(0, 5).join(" · ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2 · Subsystem health cards (8 compact tiles) */}
      <SubsystemCards subsystems={categoryRows} />

      {/* 3 · Trend sparkline */}
      <div
        className="rounded-2xl border border-slate-200 bg-white p-4"
        data-testid="otc-trend"
      >
        <div className="flex items-center justify-between gap-3 mb-2">
          <div className="flex items-center gap-2">
            <TrendingUp size={16} className="text-slate-600" />
            <h4 className="text-sm font-semibold text-slate-900">
              Trust Score Trend
            </h4>
          </div>
          <div className="flex gap-1">
            {TREND_OPTIONS.map((o) => (
              <button
                key={o.hours}
                type="button"
                onClick={() => setTrendHours(o.hours)}
                data-testid={`otc-trend-${o.label}`}
                className={`text-xs px-2 py-0.5 rounded-full border ${
                  trendHours === o.hours
                    ? "bg-slate-900 text-white border-slate-900"
                    : "bg-white text-slate-600 border-slate-200"
                }`}
              >
                {o.label}
              </button>
            ))}
          </div>
        </div>
        <TrendSparkline points={data.trend || []} />
      </div>

      {/* 4 · Operator Action Panel — what to do RIGHT NOW */}
      <OperatorActionPanel
        actions={data.operator_actions || []}
        totalEtaSeconds={data.estimated_remediation_seconds || 0}
      />

      {/* 5 · Three-tier sections: critical / warnings / cleanup */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <FindingSection
          id="critical"
          title="Critical Operational Problems"
          Icon={XCircle}
          findings={data.critical_problems || []}
          emptyText="No production-blocking issues right now."
          tone="bg-rose-50/50 border-rose-200"
        />
        <FindingSection
          id="warnings"
          title="Operational Warnings"
          Icon={AlertTriangle}
          findings={data.operational_warnings || []}
          emptyText="No warnings — drift is within tolerance."
          tone="bg-amber-50/50 border-amber-200"
        />
        <FindingSection
          id="cleanup"
          title="Data Improvement Opportunities"
          Icon={Wrench}
          findings={data.cleanup_opportunities || []}
          emptyText="All master-data sources clean."
          tone="bg-slate-50 border-slate-200"
        />
      </div>

      {/* 6 · Workflow Lifecycle table (drill-in) */}
      <div
        className="rounded-2xl border border-slate-200 bg-white"
        data-testid="otc-workflow-table"
      >
        <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
          <Activity size={16} className="text-slate-600" />
          <h4 className="text-sm font-semibold text-slate-900">
            Workflow Lifecycle Health
          </h4>
          <span className="text-xs text-slate-500">
            click a row to drill into the last 50 events
          </span>
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

      {/* Footer · meta */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 px-2">
        <span className="flex items-center gap-1">
          <Sparkles size={12} /> Operations Trust Center
        </span>
        <span className="flex items-center gap-1">
          <Clock size={12} /> refreshed {lastRun}
        </span>
        <span className="flex items-center gap-1">
          <Database size={12} /> master-data band:{" "}
          <Badge band={summary.master_data_band || "green"} />
        </span>
      </div>
    </div>
  );
}
