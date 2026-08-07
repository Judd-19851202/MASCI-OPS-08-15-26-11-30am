import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle, ArrowRight, CalendarClock, Download, RefreshCw,
  ShieldCheck, TrendingDown, TrendingUp, Waypoints,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { HelpTip } from "@/components/ui/HelpTip";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useT } from "@/lib/i18n";
import {
  formatOperatorJobLabel,
  sanitizeOperatorCopy,
  sanitizeOperatorProjectName,
  sanitizeOperatorProjectNumber,
} from "@/lib/operatorLanguage";
import {
  buildFinancialRows,
  buildMetricPresentation,
  operatorBandLabel,
  operatorSourceLabel,
} from "@/lib/projectControlsPresentation";


const BAND_TONE = {
  red: "bg-red-50 text-red-700 border-red-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  green: "bg-emerald-50 text-emerald-700 border-emerald-200",
  insufficient_evidence: "bg-slate-100 text-slate-700 border-slate-200",
  fresh: "bg-emerald-50 text-emerald-700 border-emerald-200",
  watch: "bg-amber-50 text-amber-700 border-amber-200",
  stale: "bg-red-50 text-red-700 border-red-200",
  missing: "bg-slate-100 text-slate-700 border-slate-200",
};

const HEALTH_TONE = {
  red: "bg-red-50 text-red-700 border-red-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  green: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

function tone(value) {
  return BAND_TONE[value] || "bg-slate-100 text-slate-700 border-slate-200";
}

function fmtMoney(value) {
  return Number.isFinite(Number(value)) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "—";
}

function fmtRatio(value) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(3) : "—";
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
  return sanitizeOperatorProjectNumber(row?.project_number, "Project record");
}

function displayProjectName(row) {
  return sanitizeOperatorProjectName(row?.project_name, "Project details not available");
}

function displayProjectLabel(row) {
  return formatOperatorJobLabel(row?.project_number, row?.project_name);
}

function hasEvidence(summary) {
  return String(summary?.status || "").trim().toLowerCase() === "ready";
}

function summaryValue(summary, value, unavailableLabel) {
  return hasEvidence(summary) ? value : unavailableLabel;
}

function summaryBadge(summary, preferred, fallback = "insufficient_evidence") {
  return hasEvidence(summary) ? preferred : fallback;
}

function decisionRuleLabel(rule) {
  const trigger = String(rule?.trigger || "");
  if (trigger.includes("Likely finish")) return "Late finish risk";
  if (trigger.includes("CPI")) return "Cost pressure";
  if (trigger.includes("commitments")) return "Commitment pressure";
  if (trigger.includes("constraints")) return "Constraint pressure";
  if (trigger.includes("stale or missing")) return "Missing or older records";
  return "Portfolio review rule";
}

function SummaryCard({ icon: Icon, label, value, note, badge, testId }) {
  return (
    <Card className="border-slate-200 shadow-sm" data-testid={testId}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">{label}</div>
            <div className="mt-3 text-3xl font-semibold text-slate-950">{value}</div>
            <div className="mt-2 text-sm text-slate-600">{note}</div>
          </div>
          <div className="rounded-full bg-slate-100 p-3 text-slate-700">
            <Icon className="h-5 w-5" />
          </div>
        </div>
        {badge ? <Badge className={`mt-4 border ${tone(badge)}`}>{String(badge).replaceAll("_", " ")}</Badge> : null}
      </CardContent>
    </Card>
  );
}

function TableCard({ title, rows, columns, testId, emptyLabel = "No governed rows are available." }) {
  return (
    <Card className="border-slate-200 shadow-sm" data-testid={testId}>
      <CardHeader>
        <CardTitle className="text-lg text-slate-950">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {rows?.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-[0.18em] text-slate-500">
                  {columns.map((column) => <th key={column.key} className="px-3 py-2">{column.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => {
                  const rowKey = row.id || [row.project_number, row.kind, row.metric, row.unit, index].filter(Boolean).join("::");
                  return (
                  <tr key={rowKey} className="border-b border-slate-100 align-top" data-testid={`${testId}-row-${index}`}>
                    {columns.map((column) => <td key={column.key} className="px-3 py-3 text-slate-700">{column.render ? column.render(row, index) : (row[column.key] ?? "—")}</td>)}
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-sm text-slate-500">{emptyLabel}</div>
        )}
      </CardContent>
    </Card>
  );
}

function ProjectCard({ row, healthRow, index, onOpenDetail }) {
  const healthStatus = healthRow?.status;
  const costPresentation = buildMetricPresentation("cpi", row.financial?.cpi, { confidence: row.freshness?.overall, status: row.priority_band });
  const schedulePresentation = buildMetricPresentation("spi", row.financial?.spi, { confidence: row.freshness?.overall, status: row.priority_band });
  return (
    <Card className="border-slate-200 shadow-sm" data-testid={`portfolio-project-card-${index}`}>
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">{displayProjectNumber(row)}</div>
            <h3 className="mt-1 text-lg font-semibold text-slate-950" data-testid={`portfolio-project-name-${index}`}>{displayProjectName(row)}</h3>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge className={`border ${tone(row.priority_band)}`} data-testid={`portfolio-project-priority-${index}`}>{row.priority_label}</Badge>
              {healthStatus ? <Badge className={`border ${HEALTH_TONE[healthStatus] || tone("amber")}`} data-testid={`portfolio-project-health-${index}`}>Job health · {operatorBandLabel(healthStatus)}</Badge> : null}
              <Badge className={`border ${tone(row.freshness?.overall)}`} data-testid={`portfolio-project-freshness-${index}`}>Record age · {operatorBandLabel(row.freshness?.overall || "missing")}</Badge>
            </div>
          </div>
          <Button variant="outline" onClick={() => onOpenDetail(row)} data-testid={`portfolio-project-detail-button-${index}`}>
            Open review <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`portfolio-project-cpi-${index}`}>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Cost performance</div>
            <div className="mt-1 text-base font-semibold text-slate-950">{costPresentation.shortValue}</div>
            <div className="mt-2 text-xs text-slate-500">{costPresentation.technicalLabel}: {costPresentation.technicalValue}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`portfolio-project-spi-${index}`}>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Schedule performance</div>
            <div className="mt-1 text-base font-semibold text-slate-950">{schedulePresentation.shortValue}</div>
            <div className="mt-2 text-xs text-slate-500">{schedulePresentation.technicalLabel}: {schedulePresentation.technicalValue}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`portfolio-project-finish-${index}`}>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Likely finish</div>
            <div className="mt-1 text-base font-semibold text-slate-950">{fmtDate(row.schedule?.likely_finish_date)}</div>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3" data-testid={`portfolio-project-commitments-${index}`}>
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Commitments at risk</div>
            <div className="mt-1 text-xl font-semibold text-slate-950">{fmtWhole(row.commitments?.at_risk)}</div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4" data-testid={`portfolio-project-why-${index}`}>
          <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Why it matters</div>
          <div className="mt-2 text-sm text-slate-700">{sanitizeOperatorCopy(row.why_it_matters, row.why_it_matters)}</div>
          <div className="mt-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Recommended action</div>
          <div className="mt-2 text-sm text-slate-700">{sanitizeOperatorCopy(row.recommended_action, row.recommended_action)}</div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Link to={row.drilldowns?.forecasting || "#"} className="inline-flex items-center rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-50" data-testid={`portfolio-project-forecast-link-${index}`}>Open forecast</Link>
          <Link to={row.drilldowns?.earned_value || "#"} className="inline-flex items-center rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-50" data-testid={`portfolio-project-earned-value-link-${index}`}>Open cost &amp; earned value</Link>
          <Link to={row.drilldowns?.project_performance || "#"} className="inline-flex items-center rounded-full border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-900 hover:bg-slate-50" data-testid={`portfolio-project-performance-link-${index}`}>Open project performance</Link>
        </div>
      </CardContent>
    </Card>
  );
}

export const PortfolioIntelligenceWorkspace = ({
  mode = "executive",
  workspace,
  projectHealth,
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
  const counts = summary?.counts || {};
  const financial = summary?.financial || {};
  const schedule = summary?.schedule || {};
  const commitments = summary?.commitments || {};
  const constraints = summary?.constraints || {};
  const production = summary?.production || {};
  const freshness = summary?.freshness || {};
  const rows = workspace?.projects || [];
  const healthMap = useMemo(() => {
    const items = projectHealth?.rows || [];
    return Object.fromEntries(items.map((row) => [row.project_number, row]));
  }, [projectHealth?.rows]);

  const filteredRows = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return rows.filter((row) => {
      if (filter !== "all" && row.priority_band !== filter) return false;
      if (!needle) return true;
      return `${row.project_number} ${row.project_name}`.toLowerCase().includes(needle);
    });
  }, [filter, rows, search]);

  const financialRows = useMemo(() => buildFinancialRows(financial, lang).map((row) => ({
    ...row,
    coverageText: row.metricKey === "cpi" || row.metricKey === "spi"
      ? `${fmtWhole(financial?.coverage?.comparable_projects)} comparable project(s)`
      : `${fmtWhole(financial?.coverage?.[`${row.metricKey}_projects`])} / ${fmtWhole(financial?.coverage?.total_projects)}`,
  })), [financial, lang]);

  const heroCards = useMemo(() => ([
    {
      icon: AlertTriangle,
      label: t("Projects needing attention"),
      value: fmtWhole(counts.red),
      note: `${fmtWhole(counts.amber)} ${t("watch closely")} · ${fmtWhole(counts.insufficient_evidence)} ${t("need evidence")}`,
      badge: counts.red > 0 ? "red" : counts.amber > 0 ? "amber" : "green",
      testId: "portfolio-summary-attention",
    },
    {
      icon: TrendingDown,
      label: t("Cost performance"),
      value: summaryValue(financial, buildMetricPresentation("cpi", financial.cpi, { confidence: freshness.overall, status: financial.cpi != null && financial.cpi < 0.9 ? "red" : financial.cpi != null && financial.cpi < 1 ? "amber" : financial.cpi != null ? "green" : "insufficient_evidence" }, lang).shortValue, t("Need more records")),
      note: hasEvidence(financial)
        ? `${t("Coverage")}: ${fmtWhole(financial?.coverage?.comparable_projects)} / ${fmtWhole(financial?.coverage?.total_projects)} · ${buildMetricPresentation("cpi", financial.cpi, { confidence: freshness.overall, status: financial.cpi != null && financial.cpi < 0.9 ? "red" : financial.cpi != null && financial.cpi < 1 ? "amber" : financial.cpi != null ? "green" : "insufficient_evidence" }, lang).technicalLabel} ${buildMetricPresentation("cpi", financial.cpi, { confidence: freshness.overall, status: financial.cpi != null && financial.cpi < 0.9 ? "red" : financial.cpi != null && financial.cpi < 1 ? "amber" : financial.cpi != null ? "green" : "insufficient_evidence" }, lang).technicalValue}`
        : t("Comparable cost records are not ready yet, so this page will not show a fake green score."),
      badge: summaryBadge(financial, financial.cpi != null && financial.cpi < 0.9 ? "red" : financial.cpi != null && financial.cpi < 1 ? "amber" : financial.cpi != null ? "green" : "insufficient_evidence"),
      testId: "portfolio-summary-cost-performance",
    },
    {
      icon: CalendarClock,
      label: t("Schedule risk"),
      value: summaryValue(schedule, fmtWhole(schedule.projects_past_commitment), t("Need more records")),
      note: hasEvidence(schedule)
        ? `${fmtWhole(schedule.projects_with_slip)} ${t("projects have a forecast slip")}`
        : t("Committed-vs-likely finish evidence is not ready yet."),
      badge: summaryBadge(schedule, (schedule.projects_past_commitment || 0) > 0 ? "red" : (schedule.projects_with_slip || 0) > 0 ? "amber" : "green"),
      testId: "portfolio-summary-schedule-risk",
    },
    {
      icon: Waypoints,
      label: t("Commitments"),
      value: summaryValue(commitments, fmtWhole(commitments.at_risk), t("Need more records")),
      note: hasEvidence(commitments)
        ? `${fmtWhole(commitments.missed)} ${t("already missed")}`
        : t("Commitment evidence is not ready yet."),
      badge: summaryBadge(commitments, (commitments.missed || 0) > 0 ? "red" : (commitments.at_risk || 0) > 0 ? "amber" : "green"),
      testId: "portfolio-summary-commitments",
    },
    {
      icon: ShieldCheck,
      label: t("Constraints"),
      value: summaryValue(constraints, fmtWhole(constraints.open_count), t("Need more records")),
      note: hasEvidence(constraints)
        ? `${fmtWhole(constraints.projects_with_open_constraints)} ${t("projects have open constraints")}`
        : t("Constraint evidence is not ready yet."),
      badge: summaryBadge(constraints, (constraints.open_count || 0) >= 3 ? "red" : (constraints.open_count || 0) > 0 ? "amber" : "green"),
      testId: "portfolio-summary-constraints",
    },
    {
      icon: TrendingUp,
      label: t("Fresh evidence"),
      value: `${fmtWhole(freshness.fresh)} / ${fmtWhole(counts.total)}`,
      note: `${fmtWhole(freshness.stale)} ${t("stale")} · ${fmtWhole(freshness.missing)} ${t("missing")}`,
      badge: (freshness.stale || 0) > 0 ? "red" : (freshness.watch || 0) > 0 || (freshness.missing || 0) > 0 ? "amber" : "green",
      testId: "portfolio-summary-freshness",
    },
  ]), [commitments, constraints, counts.amber, counts.insufficient_evidence, counts.red, counts.total, financial, freshness.fresh, freshness.missing, freshness.overall, freshness.stale, freshness.watch, lang, schedule, t]);

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 pb-10" data-testid={`portfolio-intelligence-workspace-${mode}`}>
      <div className="overflow-hidden rounded-[32px] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(15,118,110,0.14),_transparent_36%),linear-gradient(135deg,#f8fafc_0%,#ffffff_58%,#ecfccb_100%)] p-6 shadow-sm sm:p-8" data-testid="portfolio-intelligence-hero-panel">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">{t("Portfolio Intelligence")}</div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">{mode === "pm" ? t("Cross-project visibility for your assigned work") : t("One executive reporting hierarchy for the real portfolio")}</h1>
            <p className="mt-4 max-w-2xl text-sm text-slate-600 sm:text-base" data-testid="portfolio-intelligence-hero-description">
              {t("This view uses the same approved project cost, schedule, production, forecast, commitment, and cost-performance records already shown inside each project.")}
            </p>
          </div>
          <div className="flex w-full flex-col gap-3 lg:w-auto lg:min-w-[340px]">
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/60 bg-white/80 p-3" data-testid="portfolio-intelligence-hero-project-count">
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Scoped projects")}</div>
                <div className="mt-1 text-2xl font-semibold text-slate-950">{fmtWhole(workspace?.scope?.project_count)}</div>
              </div>
              <div className="rounded-2xl border border-white/60 bg-white/80 p-3" data-testid="portfolio-intelligence-hero-generated-at">
                <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">{t("Updated")}</div>
                <div className="mt-1 text-sm font-semibold text-slate-950">{fmtDate(workspace?.generated_at)}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={onRefresh} disabled={loading || working} data-testid="portfolio-intelligence-refresh-button"><RefreshCw className="mr-2 h-4 w-4" /> {working ? t("Refreshing…") : t("Refresh records")}</Button>
              <Button variant="outline" onClick={onExport} disabled={loading || working} data-testid="portfolio-intelligence-export-button"><Download className="mr-2 h-4 w-4" /> {t("Export CSV")}</Button>
            </div>
            <div className="rounded-2xl border border-white/60 bg-white/80 p-3 text-xs text-slate-600" data-testid="portfolio-intelligence-hero-note">
              {t("Every project keeps a direct path back to the records behind its cost, schedule, commitments, and production outlook.")}
            </div>
          </div>
        </div>
      </div>

      {loading ? <Card className="border-slate-200"><CardContent className="p-6 text-sm text-slate-600" data-testid="portfolio-intelligence-loading-state">{t("Loading the latest portfolio view…")}</CardContent></Card> : null}

      {!loading && workspace?.cache_status === "stale_last_good" ? (
        <Card className="border-amber-200 bg-amber-50 shadow-sm" data-testid="portfolio-cache-status-banner">
          <CardContent className="p-4 text-sm text-amber-900">
            <div className="font-semibold">{t("Showing the last good portfolio update")}</div>
            <div className="mt-1">{t("The newest refresh did not finish, so this page is holding the last good view instead of inventing a new result. Review record age before making a decision.")}</div>
          </CardContent>
        </Card>
      ) : null}

      {!loading && workspace ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{heroCards.map((card) => <SummaryCard key={card.testId} {...card} />)}</div>

          <Tabs defaultValue="overview" className="space-y-5" data-testid="portfolio-intelligence-tabs-root">
            <TabsList className="flex w-full flex-wrap justify-start gap-2 rounded-2xl bg-slate-100 p-1" data-testid="portfolio-intelligence-tabs-list">
              <TabsTrigger value="overview" data-testid="portfolio-intelligence-tab-overview">{t("Overview")}</TabsTrigger>
              <TabsTrigger value="projects" data-testid="portfolio-intelligence-tab-projects">{t("Projects needing attention")}</TabsTrigger>
              <TabsTrigger value="governance" data-testid="portfolio-intelligence-tab-governance">{t("How to read this page")}</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-5" data-testid="portfolio-intelligence-overview-panel">
              <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
                <TableCard
                  title={t("Portfolio cost and schedule picture")}
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
                    { key: "meaning", label: t("What it means"), render: (row) => row.presentation.explanation },
                    { key: "coverage", label: t("Coverage"), render: (row) => row.coverageText },
                  ]}
                />
                <Card className="border-slate-200 shadow-sm" data-testid="portfolio-comparability-card">
                  <CardHeader>
                    <CardTitle className="text-lg text-slate-950">{t("Comparability standard")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4 text-sm text-slate-700">
                    <div data-testid="portfolio-comparability-financial">{t("Only approved dollar values are added together. Portfolio cost and schedule ratios come from total dollars, not project averages.")}</div>
                    <div data-testid="portfolio-comparability-production">{t("Production quantities are only added when the unit matches. Unlike units stay separate.")}</div>
                    <div data-testid="portfolio-comparability-schedule">{t("Projects are compared using commitment dates and risk counts. This page never invents a single portfolio finish date.")}</div>
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600" data-testid="portfolio-comparability-note">{financial.math_note}</div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                <TableCard
                  title={t("What changed")}
                  rows={workspace?.change_report?.items || []}
                  testId="portfolio-change-table"
                  emptyLabel={t("No new project changes were published in this update.")}
                  columns={[
                    { key: "project_number", label: t("Project"), render: (row) => displayProjectLabel(row) },
                    { key: "message", label: t("Change"), render: (row) => sanitizeOperatorCopy(row.message, row.message) },
                    { key: "band", label: t("Band"), render: (row) => <Badge className={`border ${tone(row.band)}`}>{row.band}</Badge> },
                  ]}
                />
                <TableCard
                  title={t("Production outlook by unit")}
                  rows={production.unit_buckets || []}
                  testId="portfolio-production-buckets-table"
                  emptyLabel={t("No comparable production unit buckets are available in the current scope.")}
                  columns={[
                    { key: "unit", label: t("Unit") },
                    { key: "project_count", label: t("Projects") },
                    { key: "next_week_quantity_total", label: t("Next 7d"), render: (row) => fmtWhole(row.next_week_quantity_total) },
                    { key: "required_weekly_total", label: t("Required pace"), render: (row) => fmtWhole(row.required_weekly_total) },
                    { key: "dominant_confidence", label: t("Confidence"), render: (row) => <Badge className={`border ${tone(row.dominant_confidence)}`}>{row.dominant_confidence}</Badge> },
                  ]}
                />
              </div>

              <TableCard
                title={t("Top schedule-risk projects")}
                rows={schedule.worst_projects || []}
                testId="portfolio-schedule-risk-table"
                  emptyLabel={t("No projects are currently forecast past their commitments.")}
                columns={[
                  { key: "project_number", label: t("Project"), render: (row) => displayProjectLabel(row) },
                  { key: "days_from_commitment", label: t("Days late") },
                  { key: "likely_finish_date", label: t("Likely finish"), render: (row) => fmtDate(row.likely_finish_date) },
                  { key: "committed_finish_date", label: t("Committed finish"), render: (row) => fmtDate(row.committed_finish_date) },
                ]}
              />
            </TabsContent>

            <TabsContent value="projects" className="space-y-5" data-testid="portfolio-intelligence-projects-panel">
              <Card className="border-slate-200 shadow-sm" data-testid="portfolio-project-filter-card">
                <CardContent className="flex flex-col gap-3 p-5 lg:flex-row lg:items-center lg:justify-between">
                  <div className="flex flex-1 flex-col gap-3 sm:flex-row">
                    <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t("Search by project number or name") } data-testid="portfolio-project-search-input" />
                    <div className="flex flex-wrap gap-2" data-testid="portfolio-project-filter-group">
                      {[
                        ["all", t("All")],
                        ["red", t("Red")],
                        ["amber", t("Yellow")],
                        ["green", t("Green")],
                        ["insufficient_evidence", t("Needs evidence")],
                      ].map(([value, label]) => (
                        <Button key={value} type="button" variant={filter === value ? "default" : "outline"} onClick={() => setFilter(value)} data-testid={`portfolio-project-filter-${value}`}>{label}</Button>
                      ))}
                    </div>
                  </div>
                  <div className="text-sm text-slate-600" data-testid="portfolio-project-filter-count">{fmtWhole(filteredRows.length)} {t("project(s) shown")}</div>
                </CardContent>
              </Card>

              <div className="grid gap-4">
                {filteredRows.length ? filteredRows.map((row, index) => <ProjectCard key={row.project_number} row={row} healthRow={healthMap[row.project_number]} index={index} onOpenDetail={setSelectedProject} />) : (
                  <Card className="border-slate-200"><CardContent className="p-6 text-sm text-slate-600" data-testid="portfolio-project-empty-state">{t("No scoped projects match the current filters.")}</CardContent></Card>
                )}
              </div>
            </TabsContent>

            <TabsContent value="governance" className="space-y-5" data-testid="portfolio-intelligence-governance-panel">
              <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
                <TableCard
                  title={t("How priorities are set")}
                  rows={workspace?.decision_rules || []}
                  testId="portfolio-decision-rule-table"
                  columns={[
                    { key: "rule_id", label: t("Priority signal"), render: (row) => decisionRuleLabel(row) },
                    { key: "band", label: t("Band"), render: (row) => <Badge className={`border ${tone(row.band)}`}>{operatorBandLabel(row.band, lang)}</Badge> },
                    { key: "trigger", label: t("Trigger") },
                    { key: "recommended_action", label: t("Action") },
                  ]}
                />
                <Card className="border-slate-200 shadow-sm" data-testid="portfolio-authority-card">
                  <CardHeader>
                    <CardTitle className="text-lg text-slate-950">{t("How this result is calculated")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm text-slate-700">
                    <div data-testid="portfolio-authority-role">{t("This page brings together the same approved project records already used by each project team.")}</div>
                    {[
                      ["Project performance", t("Production, work progress, and current field signals")],
                      ["Forecast and commitments", t("Likely finish, commitment dates, and forecast cost outlook")],
                      ["Cost and earned value", t("Portfolio cost and schedule performance rollups")],
                      ["Project access", t("Only the projects you are allowed to see are included here")],
                      ["Advisory summaries", t("Not used for the numbers shown on this page")],
                    ].map(([label, detail], index) => (
                      <div key={`${label}-${index}`} className="flex items-start justify-between gap-3" data-testid={`portfolio-authority-source-${index}`}>
                        <span className="font-medium text-slate-900">{label}</span>
                        <span className="text-right text-xs text-slate-500">{detail}</span>
                      </div>
                    ))}
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600" data-testid="portfolio-authority-note">{t("Portfolio cost performance is calculated from approved project totals. Ratio shortcuts and mixed-unit production totals are never used.")}</div>
                  </CardContent>
                </Card>
              </div>

              <TableCard
                title={t("Freshness and coverage")}
                rows={[
                  { id: "fresh", label: t("Projects with up-to-date records"), value: fmtWhole(freshness.fresh) },
                  { id: "watch", label: t("Projects that should be checked soon"), value: fmtWhole(freshness.watch) },
                  { id: "stale", label: t("Projects using older records"), value: fmtWhole(freshness.stale) },
                  { id: "missing", label: t("Projects still missing source detail"), value: fmtWhole(freshness.missing) },
                  { id: "blocked", label: t("Open portfolio blockers"), value: fmtWhole(workspace?.blocked_dependencies?.open_blocked_by_c9_count) },
                ]}
                testId="portfolio-runtime-status-table"
                columns={[
                  { key: "label", label: t("Status") },
                  { key: "value", label: t("Value") },
                ]}
              />

              {workspace?.refresh_errors?.length ? (
                <TableCard
                  title={t("Projects that could not update just now")}
                  rows={workspace.refresh_errors}
                  testId="portfolio-refresh-error-table"
                  columns={[
                  { key: "project_number", label: t("Project"), render: (row) => sanitizeOperatorProjectNumber(row.project_number, "Project number not available") },
                    { key: "source", label: t("Area"), render: (row) => ({ c6: "Project performance", c7: "Forecast", c8: "Earned Value" }[row.source] || "Project records") },
                    { key: "error", label: t("Issue"), render: (row) => sanitizeOperatorCopy(row.error, "This project could not update right now.") },
                  ]}
                />
              ) : null}
            </TabsContent>
          </Tabs>
        </>
      ) : null}

      <Dialog open={Boolean(selectedProject)} onOpenChange={(open) => !open && setSelectedProject(null)}>
                <DialogContent data-testid="portfolio-project-detail-dialog">
          {selectedProject ? (
            <>
              <DialogHeader>
                <DialogTitle data-testid="portfolio-project-detail-title">{displayProjectLabel(selectedProject)}</DialogTitle>
                <DialogDescription data-testid="portfolio-project-detail-description">{sanitizeOperatorCopy(selectedProject.why_it_matters, selectedProject.why_it_matters)}</DialogDescription>
              </DialogHeader>

              <div className="grid gap-4 md:grid-cols-2">
                <Card className="border-slate-200 shadow-sm" data-testid="portfolio-project-detail-action-card">
                  <CardHeader><CardTitle className="text-base text-slate-950">{t("Recommended action")}</CardTitle></CardHeader>
                  <CardContent className="text-sm text-slate-700">{sanitizeOperatorCopy(selectedProject.recommended_action, selectedProject.recommended_action)}</CardContent>
                </Card>
                <Card className="border-slate-200 shadow-sm" data-testid="portfolio-project-detail-lineage-card">
                  <CardHeader><CardTitle className="text-base text-slate-950">{t("Where these numbers came from")}</CardTitle></CardHeader>
                  <CardContent className="space-y-2 text-sm text-slate-700">
                    <div data-testid="portfolio-project-lineage-c6">{operatorSourceLabel("c6", lang)} · {fmtDate((selectedProject.source_lineage || {}).c6_generated_at)}</div>
                    <div data-testid="portfolio-project-lineage-c7">{operatorSourceLabel("c7", lang)} · {fmtDate((selectedProject.source_lineage || {}).c7_generated_at)}</div>
                    <div data-testid="portfolio-project-lineage-c8">{operatorSourceLabel("c8", lang)} · {fmtDate((selectedProject.source_lineage || {}).c8_generated_at)}</div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <TableCard
                  title={t("Current cost and schedule picture")}
                  rows={buildFinancialRows(selectedProject.financial, lang)}
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
                    { id: "likely_finish", label: t("Likely finish"), value: fmtDate(selectedProject.schedule?.likely_finish_date) },
                    { id: "commitments", label: t("At-risk commitments"), value: fmtWhole(selectedProject.commitments?.at_risk) },
                    { id: "constraints", label: t("Open constraints"), value: fmtWhole(selectedProject.constraints?.open_count) },
                    { id: "pressure", label: t("Resource shortages"), value: fmtWhole(selectedProject.resource_pressure?.shortage_count) },
                  ]}
                  testId="portfolio-project-detail-operational-table"
                  columns={[{ key: "label", label: t("Signal") }, { key: "value", label: t("Value") }]}
                />
              </div>

              <div className="flex flex-wrap gap-2" data-testid="portfolio-project-detail-links">
                <Link to={selectedProject.drilldowns?.forecasting || "#"} className="inline-flex items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-forecast-link">Open forecast</Link>
                <Link to={selectedProject.drilldowns?.earned_value || "#"} className="inline-flex items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-earned-value-link">Open cost &amp; earned value</Link>
                <Link to={selectedProject.drilldowns?.project_performance || "#"} className="inline-flex items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-performance-link">Open project performance</Link>
                {selectedProject.drilldowns?.project_pnl ? <Link to={selectedProject.drilldowns.project_pnl} className="inline-flex items-center rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-50" data-testid="portfolio-project-detail-pnl-link">Project P&amp;L</Link> : null}
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
};
