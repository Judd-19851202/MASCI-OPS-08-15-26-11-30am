import React from "react";
import { useT } from "@/lib/i18n";
import { operatorConfidenceLabel, operatorLabel, operatorStatusLabel } from "@/lib/operatorLanguage";

export function GovernedMetricCard({ metric, testIdPrefix = "metric-card" }) {
  const { t } = useT();
  if (!metric) return null;

  return (
    <article
      className="rounded-[1.75rem] border border-slate-200 bg-white/95 p-5 shadow-sm"
      data-testid={`${testIdPrefix}-${metric.metric_id}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-[10px] uppercase tracking-[0.24em] text-slate-500" data-testid={`${testIdPrefix}-${metric.metric_id}-owner`}>
            {operatorLabel(metric.owner, t)} · {metric.version}
          </div>
          <h3 className="mt-2 text-lg font-black text-slate-900" data-testid={`${testIdPrefix}-${metric.metric_id}-label`}>
            {metric.label}
          </h3>
        </div>
        <span
          className="rounded-full bg-slate-100 px-3 py-1 text-[11px] font-semibold text-slate-700"
          data-testid={`${testIdPrefix}-${metric.metric_id}-confidence`}
        >
          {operatorConfidenceLabel(metric.confidence, t)}
        </span>
      </div>

      <div className="mt-4 flex items-end gap-2" data-testid={`${testIdPrefix}-${metric.metric_id}-value`}>
        <span className="text-4xl font-black text-slate-900">{metric.value ?? "—"}</span>
        <span className="pb-1 text-sm text-slate-500">{metric.unit_label || ""}</span>
      </div>

      <p className="mt-3 text-sm leading-relaxed text-slate-600" data-testid={`${testIdPrefix}-${metric.metric_id}-definition`}>
        {metric.definition}
      </p>

      <div className="mt-3 rounded-2xl bg-slate-50 p-3 text-xs text-slate-600" data-testid={`${testIdPrefix}-${metric.metric_id}-formula`}>
        <div className="font-semibold uppercase tracking-wider text-slate-500">{t("How it's calculated")}</div>
        <div className="mt-1 break-words">{metric.formula}</div>
      </div>

      <div className="mt-3 grid gap-2 text-xs text-slate-600 sm:grid-cols-2">
        <div data-testid={`${testIdPrefix}-${metric.metric_id}-freshness`}>
          <span className="font-semibold text-slate-800">{t("Updated")}:</span> {operatorStatusLabel(metric.freshness?.status, t)} · {metric.freshness?.last_updated_at || metric.calculation_timestamp || "—"}
        </div>
        <div data-testid={`${testIdPrefix}-${metric.metric_id}-drilldown`}>
          <span className="font-semibold text-slate-800">{t("Drill-down")}:</span> {metric.drilldown_path || "—"}
        </div>
        <div data-testid={`${testIdPrefix}-${metric.metric_id}-source-records`}>
          <span className="font-semibold text-slate-800">{t("Source records")}:</span> {(metric.source_records || []).slice(0, 4).join(", ") || "—"}
        </div>
        <div data-testid={`${testIdPrefix}-${metric.metric_id}-work-blocks`}>
          <span className="font-semibold text-slate-800">{t("Work Blocks")}:</span> {(metric.work_block_lineage || []).slice(0, 4).join(", ") || "—"}
        </div>
      </div>

      {(metric.limitations || []).filter(Boolean).length > 0 ? (
        <ul className="mt-3 space-y-1 text-xs text-amber-900" data-testid={`${testIdPrefix}-${metric.metric_id}-limitations`}>
          {(metric.limitations || []).filter(Boolean).map((item, index) => (
            <li key={`${metric.metric_id}-limitation-${index}`} className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
              <span className="font-semibold">{t("Watchouts")}:</span> {item}
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}