import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  CalendarClock,
  Download,
  RefreshCw,
  ShieldCheck,
  TrendingDown,
  Waypoints,
  Wrench,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { HelpTip } from "@/components/ui/HelpTip";
import { Input } from "@/components/ui/input";
import { useT } from "@/lib/i18n";
import {
  formatOperatorJobLabel,
  sanitizeOperatorCopy,
  sanitizeOperatorProjectName,
  sanitizeOperatorProjectNumber,
} from "@/lib/operatorLanguage";
import { buildFinancialRows, buildMetricPresentation, operatorSourceLabel } from "@/lib/projectControlsPresentation";

const CONDITION_TONE = {
  critical: "bg-red-700 text-white border-red-700",
  needs_attention: "bg-orange-700 text-white border-orange-700",
  watch_closely: "bg-amber-100 text-amber-900 border-amber-300",
  on_track: "bg-emerald-100 text-emerald-900 border-emerald-300",
  needs_information: "bg-slate-100 text-slate-900 border-slate-300",
};

const CONDITION_LABEL = {
  critical: "Critical",
  needs_attention: "Needs Attention",
  watch_closely: "Watch Closely",
  on_track: "On Track",
  needs_information: "Needs Current Information",
};

const FILTERS = [
  ["all", "All"],
  ["critical", "Critical"],
  ["needs_attention", "Needs Attention"],
  ["watch_closely", "Watch Closely"],
  ["on_track", "On Track"],
  ["needs_information", "Needs Information"],
];

function conditionTone(code) {
  return CONDITION_TONE[code] || CONDITION_TONE.needs_information;
}

function fmtWhole(value) {
  return Number.isFinite(Number(value)) ? Number(value).toLocaleString() : "—";
}

function fmtDate(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
  } catch {
    return String(value);
  }
}

function displayProjectNumber(row) {
  return sanitizeOperatorProjectNumber(row?.project_number, "");
}

function displayProjectName(row, t) {
  if (row?.identity_status?.project_name_missing) return t("Project name unavailable");
  const safe = sanitizeOperatorProjectName(row?.project_name, "");
  return safe || t("Project name unavailable");
}

function displayProjectLabel(row, t) {
  const projectNumber = displayProjectNumber(row);
  const projectName = displayProjectName(row, t);
  if (!projectNumber && projectName) return projectName;
  if (projectName === t("Project name unavailable")) return projectNumber || t("Project details unavailable");
  return formatOperatorJobLabel(projectNumber, projectName);
}

function summaryCounts(summary = {}, rows = []) {
  const existing = summary?.condition_counts || {};
  if (Object.keys(existing).length) {
    return {
      critical: Number(existing.critical || 0),
      needs_attention: Number(existing.needs_attention || 0),
      watch_closely: Number(existing.watch_closely || 0),
      on_track: Number(existing.on_track || 0),
      needs_information: Number(existing.needs_information || 0),
    };
  }
  return rows.reduce((acc, row) => {
    const code = row?.primary_condition?.code || "needs_information";
    acc[code] = (acc[code] || 0) + 1;
    return acc;
  }, { critical: 0, needs_attention: 0, watch_closely: 0, on_track: 0, needs_information: 0 });
}

function attentionTotal(counts) {
  return (counts.critical || 0) + (counts.needs_attention || 0) + (counts.watch_closely || 0) + (counts.needs_information || 0);
}

function metricBand(value, thresholds) {
  if (value == null || value === "") return "needs_information";
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "needs_information";
  if (numeric <= thresholds.red) return "critical";
  if (numeric < thresholds.amber) return "needs_attention";
  if (numeric === thresholds.good) return "on_track";
  return "on_track";
}

function costBand(financial = {}) {
  if (financial?.status !== "ready") return "needs_information";
  const cpi = Number(financial?.cpi);
  if (!Number.isFinite(cpi) || cpi <= 0) return "needs_information";
  if (cpi < 0.9) return "critical";
  if (cpi < 1) return "needs_attention";
  return "on_track";
}

function scheduleBand(row = {}) {
  const spi = row?.financial?.spi;
  const daysLate = row?.schedule?.days_from_commitment;
  if (spi == null && daysLate == null) return "needs_information";
  if ((spi != null && Number(spi) < 0.9) || (daysLate != null && Number(daysLate) > 7)) return "critical";
  if ((spi != null && Number(spi) < 1) || (daysLate != null && Number(daysLate) > 0)) return "needs_attention";
  return "on_track";
}

function reportingBand(row = {}) {
  return row?.primary_condition?.code === "needs_information" ? "needs_information" : ((row?.freshness?.overall === "watch") ? "watch_closely" : "on_track");
}

function cardSeverity(counts) {
  if (counts.critical) return "critical";
  if (counts.needs_attention) return "needs_attention";
  if (counts.watch_closely) return "watch_closely";
  if (counts.needs_information) return "needs_information";
  return "on_track";
}

function SectionHeader({ kicker, title, body, testId }) {
  return (
    <div className="space-y-2" data-testid={testId}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{kicker}</div>
      <h2 className="font-display text-2xl sm:text-3xl font-black tracking-tight text-slate-950">{title}</h2>
      {body ? <p className="max-w-3xl text-sm text-slate-600 sm:text-base">{body}</p> : null}
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, note, severity = "on_track", testId }) {
  return (
    <Card className="rounded-sm border border-slate-200 shadow-none" data-testid={testId}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{label}</div>
            <div className="font-display text-3xl font-black tracking-tight text-slate-950">{value}</div>
            <div className="text-sm text-slate-600">{note}</div>
          </div>
          <div className="rounded-sm border border-slate-200 bg-slate-50 p-3 text-slate-700">
            <Icon className="h-5 w-5" />
          </div>
        </div>
        <Badge className={`mt-4 rounded-sm border ${conditionTone(severity)}`}>{CONDITION_LABEL[severity] || CONDITION_LABEL.needs_information}</Badge>
      </CardContent>
    </Card>
  );
}

function AttentionCard({ counts, scopeCount, updatedAt, working, loading, onRefresh, onExport, t }) {
  const totalAttention = attentionTotal(counts);
  return (
    <Card className="rounded-sm border border-slate-300 shadow-none xl:col-span-2" data-testid="portfolio-attention-primary-card">
      <CardContent className="grid gap-5 p-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{t("What needs attention")}</div>
          <div className="font-display text-5xl font-black tracking-tight text-slate-950" data-testid="portfolio-attention-total">{fmtWhole(totalAttention)}</div>
          <p className="max-w-xl text-sm text-slate-700 sm:text-base">
            {totalAttention > 0
              ? t("These projects need leadership review because cost, schedule, commitments, or current reporting are not where they should be.")
              : t("No scoped projects are currently asking for immediate portfolio intervention.")}
          </p>
          <div className="text-sm text-slate-600">
            {fmtWhole(counts.on_track)} {t("projects are on track")}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2" data-testid="portfolio-attention-breakdown-grid">
          {[
            ["critical", t("Critical")],
            ["needs_attention", t("Needs attention")],
            ["watch_closely", t("Watch closely")],
            ["needs_information", t("Missing current information")],
          ].map(([key, label]) => (
            <div key={key} className="rounded-sm border border-slate-200 bg-slate-50 p-4" data-testid={`portfolio-attention-count-${key}`}>
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{label}</div>
              <div className="mt-2 font-display text-3xl font-black text-slate-950">{fmtWhole(counts[key])}</div>
            </div>
          ))}
          <div className="rounded-sm border border-slate-200 bg-white p-4 sm:col-span-2" data-testid="portfolio-attention-meta">
            <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-slate-600">
              <div>{t("Scoped projects")}: <span className="font-mono text-slate-900">{fmtWhole(scopeCount)}</span></div>
              <div>{t("Updated")}: <span className="font-mono text-slate-900">{fmtDate(updatedAt)}</span></div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button variant="outline" onClick={onRefresh} disabled={loading || working} data-testid="portfolio-intelligence-refresh-button" className="rounded-sm">
                <RefreshCw className="mr-2 h-4 w-4" /> {working ? t("Refreshing…") : t("Refresh portfolio")}
              </Button>
              <Button variant="outline" onClick={onExport} disabled={loading || working} data-testid="portfolio-intelligence-export-button" className="rounded-sm">
                <Download className="mr-2 h-4 w-4" /> {t("Export CSV")}
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function MetricBox({ title, primary, secondary, severity, testId }) {
  return (
    <div className="rounded-sm border border-slate-200 bg-slate-50 p-3" data-testid={testId}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{title}</div>
          <div className="mt-1 text-base font-semibold text-slate-950">{primary}</div>
          <div className="mt-2 text-xs text-slate-500">{secondary}</div>
        </div>
        <Badge className={`rounded-sm border ${conditionTone(severity)}`}>{CONDITION_LABEL[severity] || CONDITION_LABEL.needs_information}</Badge>
      </div>
    </div>
  );
}

function ProjectCard({ row, index, onOpenDetail, t, lang }) {
  const costPresentation = buildMetricPresentation("cpi", row?.financial?.cpi, { confidence: row?.freshness?.overall, status: row?.priority_band }, lang);
  const schedulePresentation = buildMetricPresentation("spi", row?.financial?.spi, { confidence: row?.freshness?.overall, status: row?.priority_band }, lang);
  const primaryCondition = row?.primary_condition?.code || "needs_information";
  const changes = (row?.change_summary || []).slice(0, 2);
  const scheduleNote = row?.schedule?.days_from_commitment > 0
    ? `${fmtWhole(row.schedule.days_from_commitment)} ${t("day(s) later than commitment")}`
    : `${schedulePresentation.technicalLabel}: ${schedulePresentation.technicalValue}`;

  return (
    <Card className="rounded-sm border border-slate-300 shadow-none" data-testid={`portfolio-project-card-${index}`}>
      <CardContent className="space-y-5 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3 min-w-0">
            {displayProjectNumber(row) ? <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500" data-testid={`portfolio-project-number-${index}`}>{displayProjectNumber(row)}</div> : null}
            <h3 className="font-display text-2xl font-black tracking-tight text-slate-950" data-testid={`portfolio-project-name-${index}`}>{displayProjectName(row, t)}</h3>
            <Badge className={`rounded-sm border ${conditionTone(primaryCondition)}`} data-testid={`portfolio-project-condition-${index}`}>
              {row?.primary_condition?.label || CONDITION_LABEL[primaryCondition]}
            </Badge>
          </div>
          <Button variant="outline" onClick={() => onOpenDetail(row)} className="rounded-sm" data-testid={`portfolio-project-detail-button-${index}`}>
            {t("Open project")} <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-2" data-testid={`portfolio-project-why-${index}`}>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Why")}</div>
          <p className="text-sm text-slate-700">{sanitizeOperatorCopy(row?.why_it_matters, row?.why_it_matters)}</p>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <MetricBox
            title={t("Cost performance")}
            primary={costPresentation.shortValue}
            secondary={`${costPresentation.technicalLabel}: ${costPresentation.technicalValue}`}
            severity={costBand(row?.financial)}
            testId={`portfolio-project-cost-${index}`}
          />
          <MetricBox
            title={t("Schedule performance")}
            primary={schedulePresentation.shortValue}
            secondary={scheduleNote}
            severity={scheduleBand(row)}
            testId={`portfolio-project-schedule-${index}`}
          />
          <MetricBox
            title={t("Forecast completion")}
            primary={fmtDate(row?.schedule?.likely_finish_date)}
            secondary={`${t("Committed finish")}: ${fmtDate(row?.schedule?.committed_finish_date)}`}
            severity={scheduleBand(row)}
            testId={`portfolio-project-finish-${index}`}
          />
          <MetricBox
            title={t("Commitments at risk")}
            primary={fmtWhole(row?.commitments?.at_risk)}
            secondary={`${fmtWhole(row?.constraints?.open_count)} ${t("open constraints")}`}
            severity={reportingBand(row) === "needs_information" ? "needs_information" : ((row?.commitments?.missed || 0) > 0 ? "critical" : ((row?.commitments?.at_risk || 0) > 0 ? "needs_attention" : "on_track"))}
            testId={`portfolio-project-commitments-${index}`}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-sm border border-slate-200 bg-white p-4" data-testid={`portfolio-project-action-${index}`}>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("What should happen next")}</div>
            <p className="mt-2 text-sm text-slate-700">{sanitizeOperatorCopy(row?.recommended_action, row?.recommended_action)}</p>
          </div>
          <div className="rounded-sm border border-slate-200 bg-slate-50 p-4" data-testid={`portfolio-project-change-${index}`}>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("What changed")}</div>
            {changes.length ? (
              <ul className="mt-2 space-y-2 text-sm text-slate-700">
                {changes.map((item, changeIndex) => <li key={`${row?.project_number}-change-${changeIndex}`}>{sanitizeOperatorCopy(item, item)}</li>)}
              </ul>
            ) : (
              <div className="mt-2 text-sm text-slate-600">{t("No material change was posted in this update.")}</div>
            )}
          </div>
        </div>

        <div className="rounded-sm border border-slate-200 bg-slate-50 p-4" data-testid={`portfolio-project-updates-${index}`}>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Latest updates used here")}</div>
          <div className="mt-3 grid gap-3 md:grid-cols-3 text-sm text-slate-700">
            <div>{operatorSourceLabel("c6", lang)} · <span className="font-mono">{fmtDate((row?.source_lineage || {}).c6_generated_at)}</span></div>
            <div>{operatorSourceLabel("c7", lang)} · <span className="font-mono">{fmtDate((row?.source_lineage || {}).c7_generated_at)}</span></div>
            <div>{operatorSourceLabel("c8", lang)} · <span className="font-mono">{fmtDate((row?.source_lineage || {}).c8_generated_at)}</span></div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2" data-testid={`portfolio-project-links-${index}`}>
          <Link to={row?.drilldowns?.project_performance || "#"} className="inline-flex items-center rounded-sm border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid={`portfolio-project-performance-link-${index}`}>{t("Open project performance")}</Link>
          <Link to={row?.drilldowns?.forecasting || "#"} className="inline-flex items-center rounded-sm border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid={`portfolio-project-forecast-link-${index}`}>{t("Open forecast")}</Link>
          <Link to={row?.drilldowns?.earned_value || "#"} className="inline-flex items-center rounded-sm border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid={`portfolio-project-earned-value-link-${index}`}>{t("Open cost and earned value")}</Link>
        </div>
      </CardContent>
    </Card>
  );
}

function TableCard({ title, rows, columns, testId, emptyLabel = "No rows available." }) {
  return (
    <Card className="rounded-sm border border-slate-200 shadow-none" data-testid={testId}>
      <CardHeader className="border-b border-slate-200 pb-4">
        <CardTitle className="text-lg text-slate-950">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {rows?.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-[11px] uppercase tracking-[0.18em] text-slate-500">
                  {columns.map((column) => <th key={column.key} className="px-4 py-3">{column.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id || `${testId}-${index}`} className="border-b border-slate-100 align-top" data-testid={`${testId}-row-${index}`}>
                    {columns.map((column) => (
                      <td key={column.key} className="px-4 py-3 text-slate-700">
                        {column.render ? column.render(row, index) : (row[column.key] ?? "—")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-4 text-sm text-slate-500">{emptyLabel}</div>
        )}
      </CardContent>
    </Card>
  );
}

export const PortfolioIntelligenceWorkspace = ({
  mode = "executive",
  workspace,
  loading,
  working,
  onRefresh,
  onExport,
}) => {
  const { t, lang } = useT();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [selectedProject, setSelectedProject] = useState(null);

  const summary = workspace?.portfolio_summary || {};
  const rows = workspace?.projects || [];
  const counts = useMemo(() => summaryCounts(summary, rows), [summary, rows]);
  const financial = summary?.financial || {};
  const schedule = summary?.schedule || {};
  const commitments = summary?.commitments || {};
  const constraints = summary?.constraints || {};
  const resourcePressure = summary?.resource_pressure || {};
  const financialRows = useMemo(() => buildFinancialRows(financial, lang).map((row) => ({
    ...row,
    coverageText: row.metricKey === "cpi" || row.metricKey === "spi"
      ? `${fmtWhole(financial?.coverage?.comparable_projects)} / ${fmtWhole(financial?.coverage?.total_projects)}`
      : `${fmtWhole(financial?.coverage?.[`${row.metricKey}_projects`])} / ${fmtWhole(financial?.coverage?.total_projects)}`,
  })), [financial, lang]);

  const filteredRows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rows.filter((row) => {
      const conditionCode = row?.primary_condition?.code || "needs_information";
      if (filter !== "all" && conditionCode !== filter) return false;
      if (!needle) return true;
      return `${row?.project_number || ""} ${row?.project_name || ""}`.toLowerCase().includes(needle);
    });
  }, [filter, rows, search]);

  const costPresentation = buildMetricPresentation("cpi", financial?.cpi, { confidence: summary?.freshness?.overall, status: financial?.status }, lang);
  const schedulePresentation = buildMetricPresentation("spi", financial?.spi, { confidence: summary?.freshness?.overall, status: financial?.status }, lang);
  const title = mode === "pm" ? t("Your Project Portfolio") : t("Portfolio Performance");
  const subtitle = mode === "pm"
    ? t("See which of your projects need attention across cost, schedule, commitments, and current reporting.")
    : t("See which projects need leadership attention and what is driving the risk.");

  return (
    <div className="mx-auto w-full max-w-7xl space-y-8 pb-10" data-testid={`portfolio-intelligence-workspace-${mode}`}>
      <Card className="rounded-sm border border-slate-300 shadow-none" data-testid="portfolio-intelligence-hero-panel">
        <CardContent className="grid gap-6 p-6 lg:grid-cols-[1.2fr_0.8fr] lg:p-8">
          <div className="space-y-3">
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">{t("Portfolio performance")}</div>
            <h1 className="font-display text-4xl font-black tracking-tight text-slate-950 sm:text-5xl">{title}</h1>
            <p className="max-w-2xl text-sm text-slate-600 sm:text-base" data-testid="portfolio-intelligence-hero-description">{subtitle}</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-sm border border-slate-200 bg-slate-50 p-4" data-testid="portfolio-intelligence-hero-project-count">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Scoped projects")}</div>
              <div className="mt-2 font-display text-3xl font-black text-slate-950">{fmtWhole(workspace?.scope?.project_count)}</div>
            </div>
            <div className="rounded-sm border border-slate-200 bg-slate-50 p-4" data-testid="portfolio-intelligence-hero-generated-at">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Updated")}</div>
              <div className="mt-2 text-sm font-semibold text-slate-950">{fmtDate(workspace?.generated_at)}</div>
            </div>
            <div className="rounded-sm border border-slate-200 bg-white p-4 text-sm text-slate-700 sm:col-span-2" data-testid="portfolio-intelligence-hero-note">
              {t("Start with the projects needing attention, then confirm cost and schedule direction, then open the underlying project record.")}
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <Card className="rounded-sm border border-slate-200 shadow-none">
          <CardContent className="p-6 text-sm text-slate-600" data-testid="portfolio-intelligence-loading-state">{t("Loading the latest portfolio view…")}</CardContent>
        </Card>
      ) : null}

      {!loading && workspace?.cache_status === "stale_last_good" ? (
        <Card className="rounded-sm border border-amber-300 bg-amber-50 shadow-none" data-testid="portfolio-cache-status-banner">
          <CardContent className="p-4 text-sm text-amber-900">
            <div className="font-semibold">{t("Showing the last good portfolio update")}</div>
            <div className="mt-1">{t("The newest refresh did not finish, so this page is holding the last good view instead of inventing a new result. Review record age before making a decision.")}</div>
          </CardContent>
        </Card>
      ) : null}

      {!loading && workspace ? (
        <>
          <SectionHeader
            kicker={t("1 · What needs attention")}
            title={t("Current portfolio condition")}
            body={t("See the total projects needing review first, then confirm whether cost, schedule, or current reporting is driving the risk.")}
            testId="portfolio-section-attention-header"
          />

          <div className="grid gap-4 xl:grid-cols-4">
            <AttentionCard
              counts={counts}
              scopeCount={workspace?.scope?.project_count}
              updatedAt={workspace?.generated_at}
              working={working}
              loading={loading}
              onRefresh={onRefresh}
              onExport={onExport}
              t={t}
            />
            <MetricCard
              icon={TrendingDown}
              label={t("Cost performance")}
              value={financial?.status === "ready" && costPresentation.available ? costPresentation.shortValue : t("Need more records")}
              note={financial?.status === "ready" && costPresentation.available
                ? `${t("Coverage")}: ${fmtWhole(financial?.coverage?.comparable_projects)} / ${fmtWhole(financial?.coverage?.total_projects)} · ${costPresentation.technicalLabel}: ${costPresentation.technicalValue}`
                : financial?.status === "ready"
                  ? t("Cost records are present but do not yet resolve to a comparable cost-performance reading, so this page will not show a fake score.")
                  : t("Comparable cost records are not ready yet, so this page will not show a fake green score.")}
              severity={costBand(financial)}
              testId="portfolio-summary-cost-performance"
            />
            <MetricCard
              icon={CalendarClock}
              label={t("Schedule outlook")}
              value={schedule?.status === "ready" ? schedulePresentation.shortValue : t("Need more records")}
              note={schedule?.status === "ready"
                ? `${fmtWhole(schedule?.projects_past_commitment)} ${t("projects are past their commitments")}`
                : t("Committed-vs-likely finish records are not ready yet.")}
              severity={schedule?.status === "ready" ? ((schedule?.projects_past_commitment || 0) > 0 ? "critical" : ((schedule?.projects_with_slip || 0) > 0 ? "needs_attention" : "on_track")) : "needs_information"}
              testId="portfolio-summary-schedule-risk"
            />
            <MetricCard
              icon={Waypoints}
              label={t("Commitments at risk")}
              value={commitments?.status === "ready" ? fmtWhole(commitments?.at_risk) : t("Need more records")}
              note={commitments?.status === "ready"
                ? `${fmtWhole(commitments?.missed)} ${t("already missed")}`
                : t("Commitment records are not ready yet.")}
              severity={commitments?.status === "ready" ? ((commitments?.missed || 0) > 0 ? "critical" : ((commitments?.at_risk || 0) > 0 ? "needs_attention" : "on_track")) : "needs_information"}
              testId="portfolio-summary-commitments"
            />
            <MetricCard
              icon={ShieldCheck}
              label={t("Constraints affecting work")}
              value={constraints?.status === "ready" ? fmtWhole(constraints?.open_count) : t("Need more records")}
              note={constraints?.status === "ready"
                ? `${fmtWhole(constraints?.projects_with_open_constraints)} ${t("projects are carrying open constraints")}`
                : t("Constraint records are not ready yet.")}
              severity={constraints?.status === "ready" ? ((constraints?.open_count || 0) >= 3 ? "critical" : ((constraints?.open_count || 0) > 0 ? "needs_attention" : "on_track")) : "needs_information"}
              testId="portfolio-summary-constraints"
            />
            <MetricCard
              icon={AlertTriangle}
              label={t("Reporting and data gaps")}
              value={fmtWhole(counts.needs_information)}
              note={`${fmtWhole(summary?.freshness?.stale)} ${t("older records")} · ${fmtWhole(summary?.freshness?.missing)} ${t("missing records")}`}
              severity={counts.needs_information > 0 ? "needs_information" : "on_track"}
              testId="portfolio-summary-data-gaps"
            />
            <MetricCard
              icon={Wrench}
              label={t("Resource issues")}
              value={resourcePressure?.status === "ready" ? fmtWhole(resourcePressure?.shortage_count) : t("Need more records")}
              note={resourcePressure?.status === "ready"
                ? `${fmtWhole(resourcePressure?.projects_under_pressure)} ${t("projects are under resource pressure")}`
                : t("Resource pressure records are not ready yet.")}
              severity={resourcePressure?.status === "ready" ? ((resourcePressure?.shortage_count || 0) > 0 ? "needs_attention" : "on_track") : "needs_information"}
              testId="portfolio-summary-resource-issues"
            />
          </div>

          <SectionHeader
            kicker={t("2 · What changed")}
            title={t("Recent changes across the portfolio")}
            body={t("Review only the changes that materially moved a project or changed the current outlook.")}
            testId="portfolio-section-changes-header"
          />

          <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
            <TableCard
              title={t("Recent project changes")}
              rows={workspace?.change_report?.items || []}
              testId="portfolio-change-table"
              emptyLabel={t("No material project changes were posted in this update.")}
              columns={[
                { key: "project", label: t("Project"), render: (row) => displayProjectLabel(row, t) },
                { key: "message", label: t("What changed"), render: (row) => sanitizeOperatorCopy(row.message, row.message) },
                { key: "band", label: t("Condition"), render: (row) => <Badge className={`rounded-sm border ${conditionTone(row?.primary_condition?.code || row?.band === "red" ? "needs_attention" : row?.band === "amber" ? "watch_closely" : row?.band === "green" ? "on_track" : "needs_information")}`}>{row?.primary_condition?.label || CONDITION_LABEL[row?.primary_condition?.code] || t("Updated")}</Badge> },
              ]}
            />
            <TableCard
              title={t("Cost and schedule measures")}
              rows={financialRows}
              testId="portfolio-financial-table"
              columns={[
                {
                  key: "metric",
                  label: t("Measure"),
                  render: (row, index) => (
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-900">{row.presentation.primaryLabel}</span>
                        <HelpTip label={row.presentation.technicalLabel} body={row.presentation.explanation} testId={`portfolio-financial-help-${index}`} />
                      </div>
                      <div className="text-xs text-slate-500">{row.presentation.technicalLabel}</div>
                    </div>
                  ),
                },
                {
                  key: "value",
                  label: t("Current reading"),
                  render: (row) => (
                    <div className="space-y-1">
                      <div className="font-medium text-slate-900">{row.presentation.primaryValue}</div>
                      {row.presentation.technicalValue !== row.presentation.primaryValue ? <div className="text-xs text-slate-500">{row.presentation.technicalValue}</div> : null}
                    </div>
                  ),
                },
                { key: "coverage", label: t("Coverage"), render: (row) => row.coverageText },
              ]}
            />
          </div>

          <SectionHeader
            kicker={t("3 · What should happen next")}
            title={t("Open the projects that need action")}
            body={t("Search by project number or name, filter by business condition, then open the project record, forecast, or cost view.")}
            testId="portfolio-section-projects-header"
          />

          <Card className="rounded-sm border border-slate-200 shadow-none" data-testid="portfolio-project-filter-card">
            <CardContent className="flex flex-col gap-3 p-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-1 flex-col gap-3 lg:flex-row">
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder={t("Search by project number or name")}
                  data-testid="portfolio-project-search-input"
                />
                <div className="flex flex-wrap gap-2" data-testid="portfolio-project-filter-group">
                  {FILTERS.map(([value, label]) => (
                    <Button
                      key={value}
                      type="button"
                      variant={filter === value ? "default" : "outline"}
                      className="rounded-sm"
                      onClick={() => setFilter(value)}
                      data-testid={`portfolio-project-filter-${value}`}
                    >
                      {t(label)}
                    </Button>
                  ))}
                </div>
              </div>
              <div className="text-sm text-slate-600" data-testid="portfolio-project-filter-count">{fmtWhole(filteredRows.length)} {t("project(s) shown")}</div>
            </CardContent>
          </Card>

          <div className="grid gap-4 xl:grid-cols-2" data-testid="portfolio-project-grid">
            {filteredRows.length ? filteredRows.map((row, index) => (
              <ProjectCard key={row?.project_number || index} row={row} index={index} onOpenDetail={setSelectedProject} t={t} lang={lang} />
            )) : (
              <Card className="rounded-sm border border-slate-200 shadow-none xl:col-span-2">
                <CardContent className="p-6 text-sm text-slate-600" data-testid="portfolio-project-empty-state">{t("No scoped projects match the current filters.")}</CardContent>
              </Card>
            )}
          </div>

          <SectionHeader
            kicker={t("4 · How performance is measured")}
            title={t("Use these standards when you read the page")}
            body={t("Cost compares completed work value against actual cost. Schedule compares completed work value against planned work value. Mixed-unit production is never rolled into one false total.")}
            testId="portfolio-section-measurement-header"
          />

          <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
            <Card className="rounded-sm border border-slate-200 shadow-none" data-testid="portfolio-comparability-card">
              <CardHeader className="border-b border-slate-200 pb-4">
                <CardTitle className="text-lg text-slate-950">{t("Measurement standards")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 p-5 text-sm text-slate-700">
                <div>{t("Portfolio cost and schedule ratios come from total dollar values. Project ratios are never averaged together.")}</div>
                <div>{t("Production quantities are only added when the unit matches. Unlike units stay separate.")}</div>
                <div>{t("This page compares committed finish dates, likely finish dates, commitments, constraints, and current reporting without inventing a single false portfolio finish date.")}</div>
                <div className="rounded-sm border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600">{financial?.math_note}</div>
              </CardContent>
            </Card>

            <TableCard
              title={t("Current reporting confidence")}
              rows={[
                { id: "critical", label: t("Critical"), value: fmtWhole(counts.critical) },
                { id: "needs_attention", label: t("Needs attention"), value: fmtWhole(counts.needs_attention) },
                { id: "watch_closely", label: t("Watch closely"), value: fmtWhole(counts.watch_closely) },
                { id: "needs_information", label: t("Needs current information"), value: fmtWhole(counts.needs_information) },
                { id: "on_track", label: t("On track"), value: fmtWhole(counts.on_track) },
              ]}
              testId="portfolio-runtime-status-table"
              columns={[
                { key: "label", label: t("Condition") },
                { key: "value", label: t("Projects") },
              ]}
            />
          </div>

          {workspace?.refresh_errors?.length ? (
            <TableCard
              title={t("Projects that could not update just now")}
              rows={workspace.refresh_errors}
              testId="portfolio-refresh-error-table"
              columns={[
                { key: "project_number", label: t("Project"), render: (row) => sanitizeOperatorProjectNumber(row.project_number, "Project number unavailable") },
                { key: "source", label: t("Area"), render: (row) => ({ c6: t("Field update"), c7: t("Forecast"), c8: t("Cost and progress") }[row.source] || t("Project records")) },
                { key: "error", label: t("Issue"), render: (row) => sanitizeOperatorCopy(row.error, t("This project could not update right now.")) },
              ]}
            />
          ) : null}
        </>
      ) : null}

      <Dialog open={Boolean(selectedProject)} onOpenChange={(open) => !open && setSelectedProject(null)}>
        <DialogContent data-testid="portfolio-project-detail-dialog" className="max-w-5xl rounded-sm">
          {selectedProject ? (
            <>
              <DialogHeader>
                <DialogTitle data-testid="portfolio-project-detail-title">{displayProjectLabel(selectedProject, t)}</DialogTitle>
                <DialogDescription data-testid="portfolio-project-detail-description">{sanitizeOperatorCopy(selectedProject?.why_it_matters, selectedProject?.why_it_matters)}</DialogDescription>
              </DialogHeader>

              <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
                <Card className="rounded-sm border border-slate-200 shadow-none" data-testid="portfolio-project-detail-action-card">
                  <CardHeader className="border-b border-slate-200 pb-4">
                    <CardTitle className="text-base text-slate-950">{t("What should happen next")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4 p-5 text-sm text-slate-700">
                    <Badge className={`rounded-sm border ${conditionTone(selectedProject?.primary_condition?.code || "needs_information")}`}>{selectedProject?.primary_condition?.label || CONDITION_LABEL[selectedProject?.primary_condition?.code] || t("Needs Current Information")}</Badge>
                    <div>{sanitizeOperatorCopy(selectedProject?.recommended_action, selectedProject?.recommended_action)}</div>
                    <div>
                      <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("What changed")}</div>
                      {(selectedProject?.change_summary || []).length ? (
                        <ul className="mt-2 space-y-2">
                          {(selectedProject.change_summary || []).map((item, index) => <li key={`${selectedProject?.project_number}-detail-change-${index}`}>{sanitizeOperatorCopy(item, item)}</li>)}
                        </ul>
                      ) : <div className="mt-2 text-slate-600">{t("No material change was posted in this update.")}</div>}
                    </div>
                  </CardContent>
                </Card>

                <Card className="rounded-sm border border-slate-200 shadow-none" data-testid="portfolio-project-detail-lineage-card">
                  <CardHeader className="border-b border-slate-200 pb-4">
                    <CardTitle className="text-base text-slate-950">{t("Latest updates used here")}</CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-3 p-5 text-sm text-slate-700 md:grid-cols-3">
                    <div data-testid="portfolio-project-lineage-c6">{operatorSourceLabel("c6", lang)} · <span className="font-mono">{fmtDate((selectedProject?.source_lineage || {}).c6_generated_at)}</span></div>
                    <div data-testid="portfolio-project-lineage-c7">{operatorSourceLabel("c7", lang)} · <span className="font-mono">{fmtDate((selectedProject?.source_lineage || {}).c7_generated_at)}</span></div>
                    <div data-testid="portfolio-project-lineage-c8">{operatorSourceLabel("c8", lang)} · <span className="font-mono">{fmtDate((selectedProject?.source_lineage || {}).c8_generated_at)}</span></div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-4 lg:grid-cols-2">
                <TableCard
                  title={t("Current cost and schedule picture")}
                  rows={buildFinancialRows(selectedProject?.financial, lang)}
                  testId="portfolio-project-detail-financial-table"
                  columns={[
                    {
                      key: "label",
                      label: t("Measure"),
                      render: (row, index) => (
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-slate-900">{row.presentation.primaryLabel}</span>
                            <HelpTip label={row.presentation.technicalLabel} body={row.presentation.explanation} testId={`portfolio-project-detail-financial-help-${index}`} />
                          </div>
                          <div className="text-xs text-slate-500">{row.presentation.technicalLabel}</div>
                        </div>
                      ),
                    },
                    {
                      key: "value",
                      label: t("Current reading"),
                      render: (row) => (
                        <div className="space-y-1">
                          <div className="font-medium text-slate-900">{row.presentation.primaryValue}</div>
                          {row.presentation.technicalValue !== row.presentation.primaryValue ? <div className="text-xs text-slate-500">{row.presentation.technicalValue}</div> : null}
                        </div>
                      ),
                    },
                  ]}
                />
                <TableCard
                  title={t("Current operational pressure")}
                  rows={[
                    { id: "likely_finish", label: t("Likely finish"), value: fmtDate(selectedProject?.schedule?.likely_finish_date) },
                    { id: "commitments", label: t("Commitments at risk"), value: fmtWhole(selectedProject?.commitments?.at_risk) },
                    { id: "constraints", label: t("Open constraints"), value: fmtWhole(selectedProject?.constraints?.open_count) },
                    { id: "pressure", label: t("Resource shortages"), value: fmtWhole(selectedProject?.resource_pressure?.shortage_count) },
                  ]}
                  testId="portfolio-project-detail-operational-table"
                  columns={[{ key: "label", label: t("Signal") }, { key: "value", label: t("Value") }]}
                />
              </div>

              <div className="flex flex-wrap gap-2" data-testid="portfolio-project-detail-links">
                <Link to={selectedProject?.drilldowns?.project_performance || "#"} className="inline-flex items-center rounded-sm border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-performance-link">{t("Open project performance")}</Link>
                <Link to={selectedProject?.drilldowns?.forecasting || "#"} className="inline-flex items-center rounded-sm border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-forecast-link">{t("Open forecast")}</Link>
                <Link to={selectedProject?.drilldowns?.earned_value || "#"} className="inline-flex items-center rounded-sm border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-earned-value-link">{t("Open cost and earned value")}</Link>
                {selectedProject?.drilldowns?.project_pnl ? <Link to={selectedProject.drilldowns.project_pnl} className="inline-flex items-center rounded-sm border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-pnl-link">{t("Project P&L")}</Link> : null}
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
};