import React from "react";
import { Download, RefreshCw, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { GovernedMetricCard } from "@/components/operational_intelligence/GovernedMetricCard";
import { ResourceTable } from "@/components/operational_intelligence/ResourceTable";
import { useT } from "@/lib/i18n";
import { operatorConfidenceLabel, operatorLabel, operatorStatusLabel } from "@/lib/operatorLanguage";

const RESOURCE_OPTIONS = [
  ["crews", "Crews"],
  ["employees", "Employees"],
  ["equipment", "Equipment"],
  ["materials", "Materials"],
  ["vendors", "Vendors"],
  ["subcontractors", "Subcontractors"],
];

export function OperationalIntelligenceSnapshotWorkspace({
  snapshot,
  loading,
  error,
  title,
  subtitle,
  projectSelector,
  onRefresh,
  onExport,
  onOverride,
  actionBusy = false,
  dataTestId = "operational-intelligence-workspace",
}) {
  const { t } = useT();
  const [resourceKind, setResourceKind] = React.useState("crews");
  const [overrideTarget, setOverrideTarget] = React.useState(null);
  const [overrideNote, setOverrideNote] = React.useState("");

  const summary = snapshot?.summary || {};
  const quantityRows = snapshot?.quantity_by_unit || [];
  const timelineRows = snapshot?.timeline_metrics || [];
  const resources = snapshot?.resource_productivity || {};
  const currentRows = resources?.[resourceKind] || [];
  const exportEnabled = typeof onExport === "function";

  const startOverride = (recommendation) => {
    setOverrideTarget(recommendation);
    setOverrideNote("");
  };

  const submitOverride = async () => {
    if (!overrideTarget || !onOverride) return;
    await onOverride(overrideTarget, overrideNote);
    setOverrideTarget(null);
    setOverrideNote("");
  };

  return (
    <div className="space-y-6" data-testid={dataTestId}>
      <section className="overflow-hidden rounded-[2rem] border border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(14,116,144,0.18),_transparent_46%),linear-gradient(135deg,_#f8fafc,_#eff6ff_42%,_#ecfeff)] p-6 shadow-sm" data-testid={`${dataTestId}-hero`}>
        <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-4xl">
            <div className="text-[11px] font-semibold uppercase tracking-[0.3em] text-cyan-700">{t("Current project view")}</div>
            <h1 className="mt-3 text-4xl font-black text-slate-900" data-testid={`${dataTestId}-title`}>{title}</h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-700" data-testid={`${dataTestId}-subtitle`}>{subtitle}</p>
          </div>
          <div className="flex flex-col gap-3 xl:items-end">
            <div data-testid={`${dataTestId}-project-selector`}>{projectSelector}</div>
            <div className="flex flex-wrap gap-2">
              <Button type="button" variant="outline" onClick={onRefresh} data-testid={`${dataTestId}-refresh-button`}>
                <RefreshCw className="mr-2 h-4 w-4" /> {t("Refresh")}
              </Button>
              {exportEnabled ? (
                <Button type="button" onClick={onExport} disabled={!snapshot} data-testid={`${dataTestId}-export-button`}>
                  <Download className="mr-2 h-4 w-4" /> {t("Export CSV")}
                </Button>
              ) : (
                <div className="rounded-full border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-900" data-testid={`${dataTestId}-export-deferred`}>
                  {t("CSV export is deferred in this release.")}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {loading ? <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 text-sm text-slate-500" data-testid={`${dataTestId}-loading`}>{t("Loading project performance…")}</div> : null}
      {error ? <div className="rounded-[1.5rem] border border-rose-200 bg-rose-50 p-6 text-sm text-rose-800" data-testid={`${dataTestId}-error`}>{error}</div> : null}

      {!loading && !snapshot ? (
        <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-white/80 p-6 text-sm text-slate-500" data-testid={`${dataTestId}-empty`}>
          {t("Choose a project to view project performance.")}
        </div>
      ) : null}

      {snapshot ? (
        <>
          <div className="grid gap-4 md:grid-cols-4" data-testid={`${dataTestId}-summary-grid`}>
            {[
              ["approved-events", summary.approved_events || 0, t("Verified field updates")],
              ["review-queue", summary.review_queue_open || 0, t("Items needing review")],
              ["recommendations", summary.open_recommendations || 0, t("Recommended actions")],
              ["orphan-events", summary.orphan_events || 0, t("Unassigned records")],
            ].map(([key, value, label]) => (
              <div key={key} className="rounded-[1.5rem] border border-slate-200 bg-white/95 p-4 shadow-sm" data-testid={`${dataTestId}-summary-${key}`}>
                <div className="text-[11px] uppercase tracking-[0.24em] text-slate-500">{label}</div>
                <div className="mt-3 text-3xl font-black text-slate-900">{value}</div>
                <div className="mt-2 text-xs text-slate-500">{summary.last_source_event_at || snapshot.generated_at}</div>
              </div>
            ))}
          </div>

          <section className="space-y-4" data-testid={`${dataTestId}-metrics-section`}>
            <div className="flex items-center gap-3 text-sm text-slate-600">
              <ShieldCheck className="h-4 w-4 text-cyan-700" />
              {t("Every KPI below is built from Work Blocks, approved progress updates, budget lines, and schedule activities.")}
            </div>
            <div className="grid gap-4 xl:grid-cols-2">
              {(snapshot.metric_cards || []).map((metric) => (
                <GovernedMetricCard key={metric.metric_id} metric={metric} testIdPrefix={`${dataTestId}-metric`} />
              ))}
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white/95 p-5 shadow-sm" data-testid={`${dataTestId}-unit-breakdown`}>
              <h2 className="text-xl font-black text-slate-900">{t("Installed quantity by unit")}</h2>
              <div className="mt-4 space-y-3">
                {quantityRows.map((row) => (
                  <div key={row.unit} className="rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4" data-testid={`${dataTestId}-unit-${row.unit}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-500">{row.unit}</div>
                        <div className="mt-2 text-sm text-slate-700">{t("Accepted")} {row.accepted_quantity} · {t("Remaining")} {row.remaining_quantity} · {t("Rejected")} {row.rejected_quantity}</div>
                      </div>
                      <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-slate-700">{operatorConfidenceLabel(row.confidence, t)}</span>
                    </div>
                    <div className="mt-3 grid gap-2 text-xs text-slate-600 md:grid-cols-2">
                      <div>{t("Budget lines")}: {(row.budget_line_ids || []).slice(0, 4).join(", ") || "—"}</div>
                      <div>{t("Schedule activities")}: {(row.schedule_activity_ids || []).slice(0, 4).join(", ") || "—"}</div>
                      <div>{t("Work Blocks")}: {(row.work_block_ids || []).slice(0, 4).join(", ") || "—"}</div>
                      <div>{t("Reports")}: {(row.source_report_ids || []).slice(0, 4).join(", ") || "—"}</div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-slate-200 bg-white/95 p-5 shadow-sm" data-testid={`${dataTestId}-timeline-section`}>
              <h2 className="text-xl font-black text-slate-900">{t("Production pace")}</h2>
              <div className="mt-4 space-y-3">
                {timelineRows.map((row) => (
                  <div key={row.unit} className="rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4" data-testid={`${dataTestId}-timeline-${row.unit}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.unit}</div>
                      <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-slate-700">{operatorConfidenceLabel(row.confidence, t)}</span>
                    </div>
                    <div className="mt-3 grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
                      <div>{t("Daily")}: {row.daily_production ?? "—"}</div>
                      <div>{t("Weekly")}: {row.weekly_production ?? "—"}</div>
                      <div>{t("14-day")}: {row.rolling_14_day_production ?? "—"}</div>
                      <div>{t("Pace")}: {row.production_velocity ?? "—"}</div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>

          <section className="rounded-[1.75rem] border border-slate-200 bg-white/95 p-5 shadow-sm" data-testid={`${dataTestId}-resources-section`}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-black text-slate-900">{t("Resource performance")}</h2>
              <div className="flex flex-wrap gap-2">
                {RESOURCE_OPTIONS.map(([key, label]) => (
                  <Button
                    key={key}
                    type="button"
                    variant={resourceKind === key ? "default" : "outline"}
                    size="sm"
                    onClick={() => setResourceKind(key)}
                    data-testid={`${dataTestId}-resource-tab-${key}`}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </div>
            <div className="mt-4">
              <ResourceTable rows={currentRows} kind={resourceKind} dataTestId={`${dataTestId}-resource-table-${resourceKind}`} />
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <section className="rounded-[1.75rem] border border-slate-200 bg-white/95 p-5 shadow-sm" data-testid={`${dataTestId}-recommendations-section`}>
              <h2 className="text-xl font-black text-slate-900">{t("Recommended next actions")}</h2>
              <div className="mt-4 space-y-3">
                {(snapshot.recommendations || []).map((row) => (
                  <div key={row.recommendation_id} className="rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4" data-testid={`${dataTestId}-recommendation-${row.recommendation_id}`}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold text-slate-900">{row.title}</div>
                        <div className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">{operatorLabel(row.kind, t)} · {operatorConfidenceLabel(row.confidence, t)}</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-slate-700">{operatorStatusLabel(row.status, t)}</span>
                        {row.status === "open" && onOverride ? (
                          <Button type="button" size="sm" variant="outline" onClick={() => startOverride(row)} data-testid={`${dataTestId}-override-${row.recommendation_id}`}>
                            {t("Record different decision")}
                          </Button>
                        ) : null}
                      </div>
                    </div>
                    <p className="mt-3 text-sm text-slate-700">{row.explanation}</p>
                    <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
                      <div>{t("Owner")}: {row.owner || t("Not assigned yet")}</div>
                      <div>{t("Drill-down")}: {row.drilldown_path || row.drill_down_path || "—"}</div>
                      <div>{t("Source")}: {operatorLabel(row.governing_source || row.source || row.kind, t)}</div>
                      <div>{t("Confidence")}: {operatorConfidenceLabel(row.confidence, t)}</div>
                      <div className="sm:col-span-2">{t("Evidence")}: {Object.entries(row.evidence || {}).map(([key, value]) => `${operatorLabel(key, t, key)}: ${value}`).join(" · ") || "—"}</div>
                    </div>
                    {row.override ? <div className="mt-3 text-xs text-cyan-700">{t("Different field decision")}: {row.override.actor} · {row.override.note}</div> : null}
                  </div>
                ))}
                {!snapshot.recommendations?.length ? <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-white/70 p-4 text-sm text-slate-500">{t("No recommended actions are open right now.")}</div> : null}
              </div>
            </section>

            <section className="rounded-[1.75rem] border border-slate-200 bg-white/95 p-5 shadow-sm" data-testid={`${dataTestId}-review-queue-section`}>
              <h2 className="text-xl font-black text-slate-900">{t("Items needing review")}</h2>
              <div className="mt-4 space-y-3">
                {(snapshot.review_queue || []).map((row) => (
                  <div key={row.review_id} className="rounded-[1.5rem] border border-slate-200 bg-slate-50/70 p-4" data-testid={`${dataTestId}-review-${row.review_id}`}>
                    <div className="flex items-center justify-between gap-3">
                      <div className="font-semibold text-slate-900">{row.title}</div>
                      <span className="rounded-full bg-white px-3 py-1 text-[11px] font-semibold text-slate-700">{operatorStatusLabel(row.status, t)}</span>
                    </div>
                    <div className="mt-2 text-sm text-slate-700">{row.reason}</div>
                    <div className="mt-2 text-xs text-slate-500">{operatorLabel(row.review_type, t)} · {row.source_record_id || row.review_id}</div>
                  </div>
                ))}
                {!snapshot.review_queue?.length ? <div className="rounded-[1.5rem] border border-dashed border-slate-300 bg-white/70 p-4 text-sm text-slate-500">{t("No items need review right now.")}</div> : null}
              </div>
            </section>
          </div>

          <section className="rounded-[1.75rem] border border-slate-200 bg-slate-950 p-5 text-slate-50 shadow-sm" data-testid={`${dataTestId}-authority-footer`}>
            <div className="text-[11px] uppercase tracking-[0.24em] text-cyan-200">{t("What this page is based on")}</div>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <div data-testid={`${dataTestId}-authority-operators`}>{t("You are seeing")}: <strong>{t("Project Performance")}</strong></div>
              <div data-testid={`${dataTestId}-authority-engine`}>{t("Built from")}: <strong>{t("Daily Reports, Work Blocks, approved progress updates, budget lines, and schedule activities")}</strong></div>
              <div data-testid={`${dataTestId}-authority-metrics`}>{t("Update existing records")}: <strong>{operatorStatusLabel(snapshot.backfill?.status || "pending_manual_run", t)}</strong></div>
            </div>
            <div className="mt-3 text-xs text-slate-300">{t("Also used in")}: {(summary.centralized_consumers || []).map((item) => operatorLabel(item, t)).join(", ") || "—"}</div>
          </section>
        </>
      ) : null}

      <Dialog open={!!overrideTarget} onOpenChange={(open) => !open && setOverrideTarget(null)}>
        <DialogContent data-testid={`${dataTestId}-override-dialog`}>
          <DialogHeader>
            <DialogTitle>{t("Record different field decision")}</DialogTitle>
            <DialogDescription>
              {t("This keeps the original recommendation, saves your decision, and preserves the evidence trail.")}
            </DialogDescription>
          </DialogHeader>
          <Textarea
            value={overrideNote}
            onChange={(event) => setOverrideNote(event.target.value)}
            placeholder={t("Explain why you are taking a different action.")}
            data-testid={`${dataTestId}-override-note-input`}
          />
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setOverrideTarget(null)} data-testid={`${dataTestId}-override-cancel-button`}>{t("Cancel")}</Button>
            <Button type="button" onClick={submitOverride} disabled={actionBusy} data-testid={`${dataTestId}-override-save-button`}>
              {actionBusy ? t("Saving…") : t("Save decision")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}