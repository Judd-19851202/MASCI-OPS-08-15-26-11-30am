import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Download, GitBranch, RefreshCw, ShieldCheck, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { HelpTip } from "@/components/ui/HelpTip";
import { useT } from "@/lib/i18n";
import { sanitizeOperatorCopy } from "@/lib/operatorLanguage";
import {
  buildMetricPresentation,
  measurementMethodLabel,
  operatorBandLabel,
} from "@/lib/projectControlsPresentation";

const STATUS_TONE = {
  green: "bg-emerald-50 text-emerald-700 border-emerald-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  red: "bg-red-50 text-red-700 border-red-200",
  blocked: "bg-slate-100 text-slate-700 border-slate-200",
  high: "bg-emerald-50 text-emerald-700 border-emerald-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  partial: "bg-orange-50 text-orange-700 border-orange-200",
  review_required: "bg-amber-50 text-amber-700 border-amber-200",
};

function tone(status) {
  return STATUS_TONE[status] || "bg-slate-100 text-slate-700 border-slate-200";
}

function fmtMoney(value) {
  return Number.isFinite(Number(value)) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "—";
}

function fmtRatio(value) {
  return Number.isFinite(Number(value)) ? Number(value).toFixed(3) : "—";
}

function fmtPercent(value) {
  return Number.isFinite(Number(value)) ? `${(Number(value) * 100).toFixed(1)}%` : "—";
}

function SummaryCard({ icon: Icon, label, value, note, status, testId }) {
  return (
    <Card className="border-slate-200 shadow-sm" data-testid={testId}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">{label}</div>
            <div className="mt-3 text-3xl font-semibold text-slate-900">{value}</div>
            <div className="mt-2 text-sm text-slate-600">{note}</div>
          </div>
          <div className="rounded-full bg-slate-100 p-3 text-slate-700">
            <Icon className="h-5 w-5" />
          </div>
        </div>
        <Badge className={`mt-4 border ${tone(status)}`}>{String(status || "blocked").replaceAll("_", " ")}</Badge>
      </CardContent>
    </Card>
  );
}

function TableCard({ title, rows, columns, testId, emptyLabel }) {
  return (
    <Card className="border-slate-200 shadow-sm" data-testid={testId}>
      <CardHeader>
        <CardTitle className="text-lg text-slate-900">{title}</CardTitle>
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
                {rows.map((row, index) => (
                  <tr key={row.id || row.metric_id || row.budget_line_id || index} className="border-b border-slate-100 align-top" data-testid={`${testId}-row-${index}`}>
                    {columns.map((column) => <td key={column.key} className="px-3 py-3 text-slate-700">{column.render ? column.render(row, index) : (row[column.key] ?? "—")}</td>)}
                  </tr>
                ))}
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

export default function EarnedValueWorkspace({ mode = "pm", projectNumber, selector, workspace, loading, working, onRefresh, onCaptureSnapshot, onExport }) {
  const { t, lang } = useT();
  const [snapshotNote, setSnapshotNote] = useState("");
  const summary = workspace?.summary || {};
  const lines = workspace?.lines || [];
  const versionRows = workspace?.versioning?.recent_versions || [];
  const blockedActuals = workspace?.blocked_dependencies?.open_actual_costs || [];
  const blockedCommitments = workspace?.blocked_dependencies?.open_commitments || [];
  const metrics = workspace?.metric_cards || [];
  const isPm = mode === "pm";
  const budgetReviewPath = isPm ? `/pm/project-controls/budget?project_number=${encodeURIComponent(projectNumber || "")}` : `/admin/governance/project-controls/budget?project_number=${encodeURIComponent(projectNumber || "")}`;
  const sourceLabels = {
    bac_authority: t("Budget approved for this job"),
    pv_authority: t("Baseline schedule timing"),
    ev_authority: t("Approved installed quantity or approved physical progress"),
    ac_authority: t("Linked receipts and recognized cost"),
    quantity_authority: t("Approved field production"),
    forecast_authority: t("Current remaining-cost outlook"),
    metric_governance: t("Shared project-controls definitions"),
    work_block_authority: t("Field work records"),
    ai_role: t("No AI-generated truth"),
  };

  const heroCards = useMemo(() => ([
    { icon: Wallet, metricKey: "bac", value: summary.bac, status: summary.confidence || "blocked", testId: "earned-value-summary-bac" },
    { icon: TrendingUp, metricKey: "ev", value: summary.ev, status: metrics.find((row) => row.metric_id === "c8-ev" || row.label === "EV")?.status || "blocked", testId: "earned-value-summary-ev" },
    { icon: TrendingDown, metricKey: "ac", value: summary.ac, status: metrics.find((row) => row.metric_id === "c8-ac" || row.label === "AC")?.status || "blocked", testId: "earned-value-summary-ac" },
    { icon: ShieldCheck, metricKey: "eac", value: summary.eac, status: metrics.find((row) => row.metric_id === "c8-eac" || row.label === "EAC")?.status || "blocked", testId: "earned-value-summary-eac" },
  ]).map((card) => ({
    ...card,
    presentation: buildMetricPresentation(card.metricKey, card.value, { confidence: summary.confidence, status: card.status }, lang),
  })), [lang, metrics, summary.ac, summary.bac, summary.confidence, summary.eac, summary.ev]);

  const metricRows = useMemo(() => metrics.map((row) => ({
    ...row,
    presentation: buildMetricPresentation(row.metric_id || row.label, row.value, { confidence: row.confidence, status: row.status }, lang),
  })), [lang, metrics]);

  const lineRows = useMemo(() => lines.map((row) => ({
    ...row,
    bacPresentation: buildMetricPresentation("bac", row.bac, { confidence: row.confidence, status: row.status }, lang),
    evPresentation: buildMetricPresentation("ev", row.ev, { confidence: row.confidence, status: row.status }, lang),
    acPresentation: buildMetricPresentation("ac", row.ac, { confidence: row.confidence, status: row.status }, lang),
    cpiPresentation: buildMetricPresentation("cpi", row.cpi, { confidence: row.confidence, status: row.status }, lang),
    spiPresentation: buildMetricPresentation("spi", row.spi, { confidence: row.confidence, status: row.status }, lang),
  })), [lang, lines]);

  const readinessLabels = {
    budget: t("Budget evidence"),
    schedule: t("Schedule evidence"),
    quantity: t("Installed work evidence"),
    actual_cost: t("Actual cost evidence"),
    forecast: t("Remaining cost outlook"),
    freshness: t("Record age"),
    overall: t("Overall readiness"),
  };

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 pb-10" data-testid={`earned-value-workspace-${mode}`}>
      <div className="overflow-hidden rounded-[32px] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(14,116,144,0.14),_transparent_38%),linear-gradient(135deg,#f8fafc_0%,#ffffff_58%,#ecfeff_100%)] p-6 shadow-sm sm:p-8" data-testid="earned-value-hero-panel">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <div className="text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500">{t("Earned Value")}</div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">{t("Budget, progress, and cost in one project view")}</h1>
            <p className="mt-4 max-w-2xl text-sm text-slate-600 sm:text-base" data-testid="earned-value-hero-description">
              {t("See what the job should have earned by now, what it has actually earned, what it has cost, what is driving the result, and where to look next.")}
            </p>
          </div>
          <div className="flex w-full flex-col gap-3 lg:w-auto lg:min-w-[340px]">
            <div data-testid="earned-value-project-selector-wrap">{selector}</div>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={onRefresh} disabled={!projectNumber || loading || working} data-testid="earned-value-refresh-button"><RefreshCw className="mr-2 h-4 w-4" /> {t("Refresh")}</Button>
              <Button variant="outline" onClick={() => onCaptureSnapshot?.(snapshotNote)} disabled={!projectNumber || loading || working} data-testid="earned-value-capture-snapshot-button"><GitBranch className="mr-2 h-4 w-4" /> {t("Save update")}</Button>
              <Button variant="outline" onClick={onExport} disabled={!projectNumber || loading || working} data-testid="earned-value-export-button"><Download className="mr-2 h-4 w-4" /> {t("Export CSV")}</Button>
            </div>
            <Input placeholder={t("Update note (optional)")} value={snapshotNote} onChange={(event) => setSnapshotNote(event.target.value)} data-testid="earned-value-snapshot-note-input" />
          </div>
        </div>
      </div>

      {loading ? <Card className="border-slate-200"><CardContent className="p-6 text-sm text-slate-600" data-testid="earned-value-loading-state">{t("Loading Earned Value for this job…")}</CardContent></Card> : null}
      {!loading && !projectNumber ? <Card className="border-slate-200"><CardContent className="p-6 text-sm text-slate-600" data-testid="earned-value-empty-project-state">{t("Choose a project to open its Earned Value view.")}</CardContent></Card> : null}

      {!loading && projectNumber && workspace ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{heroCards.map((card) => <SummaryCard key={card.testId} icon={card.icon} label={card.presentation.primaryLabel} value={card.presentation.technicalValue} note={card.presentation.explanation} status={card.status} testId={card.testId} />)}</div>

          <Card className="border-slate-200 shadow-sm" data-testid="earned-value-decision-brief-card">
            <CardHeader>
              <CardTitle className="text-lg text-slate-900">{t("Operator decision brief")}</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 text-sm text-slate-700">
              <div data-testid="earned-value-decision-what-happened"><span className="font-semibold text-slate-900">{t("What happened")}: </span>{sanitizeOperatorCopy(workspace?.decision_brief?.what_happened, workspace?.decision_brief?.what_happened || "—")}</div>
              <div data-testid="earned-value-decision-where-we-are"><span className="font-semibold text-slate-900">{t("Where we are now")}: </span>{sanitizeOperatorCopy(workspace?.decision_brief?.where_we_are_now, workspace?.decision_brief?.where_we_are_now || "—")}</div>
              <div data-testid="earned-value-decision-what-changed"><span className="font-semibold text-slate-900">{t("What changed")}: </span>{sanitizeOperatorCopy(workspace?.decision_brief?.what_changed, workspace?.decision_brief?.what_changed || "—")}</div>
              <div data-testid="earned-value-decision-why"><span className="font-semibold text-slate-900">{t("Why")}: </span>{sanitizeOperatorCopy(workspace?.decision_brief?.why, workspace?.decision_brief?.why || "—")}</div>
              <div data-testid="earned-value-decision-risk"><span className="font-semibold text-slate-900">{t("What is at risk")}: </span>{sanitizeOperatorCopy(workspace?.decision_brief?.what_is_at_risk, workspace?.decision_brief?.what_is_at_risk || "—")}</div>
              <div data-testid="earned-value-decision-if-nothing-changes"><span className="font-semibold text-slate-900">{t("If nothing changes")}: </span>{sanitizeOperatorCopy(workspace?.decision_brief?.if_nothing_changes, workspace?.decision_brief?.if_nothing_changes || "—")}</div>
            </CardContent>
          </Card>

          <Tabs defaultValue="overview" className="space-y-5" data-testid="earned-value-tabs-root">
            <TabsList className="flex w-full flex-wrap justify-start gap-2 rounded-2xl bg-slate-100 p-1" data-testid="earned-value-tabs-list">
              <TabsTrigger value="overview" data-testid="earned-value-overview-tab-trigger">{t("Overview")}</TabsTrigger>
              <TabsTrigger value="lineage" data-testid="earned-value-lineage-tab-trigger">{t("Where these numbers came from")}</TabsTrigger>
              <TabsTrigger value="governance" data-testid="earned-value-governance-tab-trigger">{t("History & source detail")}</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-5" data-testid="earned-value-overview-tab-panel">
              <TableCard
                title={t("What each measure means")}
                rows={metricRows}
                testId="earned-value-metric-table"
                emptyLabel={t("No earned-value measures are available yet.")}
                columns={[
                  {
                    key: "label",
                    label: t("Measure"),
                    render: (row, index) => (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-900">{row.presentation.primaryLabel}</span>
                          <HelpTip
                            label={row.presentation.technicalLabel}
                            body={row.definition || row.presentation.explanation}
                            testId={`earned-value-metric-help-${index}`}
                          />
                        </div>
                        <div className="text-xs text-slate-500">{row.presentation.technicalLabel}</div>
                      </div>
                    ),
                  },
                  {
                    key: "display_value",
                    label: t("Current reading"),
                    render: (row) => (
                      <div className="space-y-1">
                        <div className="font-medium text-slate-900">{row.presentation.primaryValue}</div>
                        {row.presentation.technicalValue !== row.presentation.primaryValue ? <div className="text-xs text-slate-500">{row.presentation.technicalValue}</div> : null}
                      </div>
                    ),
                  },
                  { key: "meaning", label: t("What it means"), render: (row) => row.presentation.explanation },
                  { key: "confidence", label: t("Data confidence"), render: (row) => <Badge className={`border ${tone(row.confidence)}`}>{row.presentation.confidenceLabel}</Badge> },
                  { key: "status", label: t("Status"), render: (row) => <Badge className={`border ${tone(row.status)}`}>{row.presentation.statusLabel}</Badge> },
                  { key: "drilldown_path", label: t("Where to check"), render: (row) => <span className="text-xs text-teal-700">{row.drilldown_path || "—"}</span> },
                ]}
              />

              <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                <TableCard
                  title={t("Required actions")}
                  rows={workspace?.decision_brief?.required_actions || []}
                  testId="earned-value-actions-table"
                  emptyLabel={t("No required actions are open right now.")}
                  columns={[
                    { key: "title", label: t("Action") },
                    { key: "owner", label: t("Owner") },
                    { key: "due_date", label: t("Due") },
                    { key: "reason", label: t("Reason") },
                  ]}
                />
                <Card className="border-slate-200 shadow-sm" data-testid="earned-value-readiness-card">
                  <CardHeader>
                    <CardTitle className="text-lg text-slate-900">{t("Data readiness")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm text-slate-700">
                    {Object.entries(workspace?.readiness || {}).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-3" data-testid={`earned-value-readiness-${key}`}>
                        <span className="font-medium text-slate-900">{readinessLabels[key] || key.replaceAll("_", " ")}</span>
                        <Badge className={`border ${tone(value)}`}>{operatorBandLabel(value, lang)}</Badge>
                      </div>
                    ))}
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600" data-testid="earned-value-readiness-note">
                      {t("Missing or incomplete evidence never turns green. If confidence is partial, finish the budget review items before trusting the result.")}
                    </div>
                    <Link to={budgetReviewPath} className="text-sm font-semibold text-teal-700 underline-offset-4 hover:underline" data-testid="earned-value-budget-review-link">{t("Open budget review")}</Link>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="lineage" className="space-y-5" data-testid="earned-value-lineage-tab-panel">
              <TableCard
                title={t("Cost code and pay item detail")}
                rows={lineRows}
                testId="earned-value-line-table"
                emptyLabel={t("No earned-value detail rows are available yet.")}
                columns={[
                  { key: "label", label: t("Budget line") },
                  { key: "method", label: t("How progress is measured"), render: (row) => measurementMethodLabel(row.method, lang) },
                  { key: "planned_percent", label: t("Planned %"), render: (row) => fmtPercent(row.planned_percent) },
                  { key: "earned_percent", label: t("Earned %"), render: (row) => fmtPercent(row.earned_percent) },
                  { key: "bac", label: t("Approved budget"), render: (row) => row.bacPresentation.technicalValue },
                  { key: "ev", label: t("Work completed value"), render: (row) => row.evPresentation.technicalValue },
                  { key: "ac", label: t("Actual cost to date"), render: (row) => row.acPresentation.technicalValue },
                  { key: "cpi", label: t("Cost performance"), render: (row) => row.cpiPresentation.technicalValue },
                  { key: "spi", label: t("Schedule performance"), render: (row) => row.spiPresentation.technicalValue },
                  { key: "confidence", label: t("Confidence"), render: (row) => <Badge className={`border ${tone(row.confidence)}`}>{operatorBandLabel(row.confidence, lang)}</Badge> },
                ]}
              />

              <TableCard
                title={t("Why a measure is blocked or partial")}
                rows={lines.map((row) => ({ id: row.budget_line_id, label: row.label, limitations: (row.limitations || []).join(" "), source_records: (row.source_records || []).join(", ") || "—" }))}
                testId="earned-value-limitations-table"
                emptyLabel={t("No EV limitations were published.")}
                columns={[
                  { key: "label", label: t("Budget line") },
                  { key: "limitations", label: t("Why confidence changed") },
                  { key: "source_records", label: t("Source IDs") },
                ]}
              />
            </TabsContent>

            <TabsContent value="governance" className="space-y-5" data-testid="earned-value-governance-tab-panel">
              <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
                <TableCard
                  title={t("Recent updates")}
                  rows={versionRows}
                  testId="earned-value-version-table"
                  emptyLabel={t("No updates have been saved yet.")}
                  columns={[
                    { key: "version_number", label: t("Update") },
                    { key: "generated_at", label: t("Generated") },
                    { key: "note", label: t("Note") },
                    { key: "change_detection", label: t("Change") , render: (row) => row.change_detection?.summary?.[0] || t("No material change")},
                  ]}
                />
                <Card className="border-slate-200 shadow-sm" data-testid="earned-value-authority-card">
                  <CardHeader>
                    <CardTitle className="text-lg text-slate-900">{t("Where these numbers come from")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 text-sm text-slate-700">
                    {Object.entries(workspace?.authority_boundaries || {}).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between gap-3" data-testid={`earned-value-authority-${key}`}>
                        <span className="font-medium text-slate-900">{sourceLabels[key] || key.replaceAll("_", " ")}</span>
                        <span className="text-right text-xs text-slate-500">{sourceLabels[key] ? t("Approved project record") : (value || "—")}</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>

              <div className="grid gap-5 xl:grid-cols-2">
                <TableCard
                  title={t("Actual-cost items still under review")}
                  rows={blockedActuals}
                  testId="earned-value-blocked-actuals-table"
                  emptyLabel={t("No actual-cost items are holding this view back right now.")}
                  columns={[
                    { key: "vendor", label: t("Vendor") },
                    { key: "candidate_amount", label: t("Amount"), render: (row) => fmtMoney(row.candidate_amount) },
                    { key: "review_status", label: t("Status") },
                    { key: "description", label: t("Reason") },
                  ]}
                />
                <TableCard
                  title={t("Commitments still under review")}
                  rows={blockedCommitments}
                  testId="earned-value-blocked-commitments-table"
                  emptyLabel={t("No commitment items are holding this view back right now.")}
                  columns={[
                    { key: "vendor", label: t("Vendor") },
                    { key: "commitment_amount", label: t("Amount"), render: (row) => fmtMoney(row.commitment_amount) },
                    { key: "review_status", label: t("Status") },
                    { key: "description", label: t("Reason") },
                  ]}
                />
              </div>
            </TabsContent>
          </Tabs>
        </>
      ) : null}
    </div>
  );
}