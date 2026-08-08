/**
 * DR-ROI-001E · Horizon primitives shared by PM / Admin / Executive
 * Operational Intelligence dashboards.
 *
 * Three horizons per dashboard (per user directive · 2026-02-05):
 *   1. What Happened  — completed operational totals for the selected range.
 *   2. What Is Happening — the live "in-range" mix (production, delays, loads).
 *   3. What Needs Attention — safety / quality / delay / readiness facts
 *      with fact_id + source traceability back to the originating record.
 *
 * Every value shown in these primitives is sourced from the Operational
 * Data Spine (`operational_facts` + `operational_kpi_snapshots`). No
 * decorative analytics. No AI branding. No placeholder charts.
 */
import React from "react";

function humanizeToken(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatAttentionContext(item) {
  const parts = [];
  if (item?.date) parts.push(item.date);
  if (item?.project_name) parts.push(item.project_name);
  else if (item?.project_id) parts.push(item.project_id);
  if (item?.source_type) parts.push(humanizeToken(item.source_type));
  if (item?.summary_scope) parts.push(humanizeToken(item.summary_scope));
  return parts.filter(Boolean).join(" · ") || "Operational records linked to this period.";
}

export const PRESETS = [
  { key: "today",      label: "Today" },
  { key: "yesterday",  label: "Yesterday" },
  { key: "this_week",  label: "This week" },
  { key: "last_week",  label: "Last week" },
  { key: "month",      label: "This month" },
  { key: "last_month", label: "Last month" },
  { key: "quarter",    label: "Quarter" },
  { key: "year",       label: "Year" },
];

export function PresetPicker({ value, onChange, testid }) {
  // Individual button testid drops the "-picker" suffix so it reads as
  // `<scope>-intel-preset-<key>` per the DR-ROI-001E spec.
  const buttonBase = testid ? testid.replace(/-picker$/, "") : "preset";
  return (
    <div className="flex gap-1 flex-wrap" data-testid={testid}>
      {PRESETS.map((p) => (
        <button
          key={p.key}
          onClick={() => onChange(p.key)}
          className={`text-xs rounded-md px-2 py-1 border transition ${
            value === p.key
              ? "border-red-600 bg-red-50 text-red-800"
              : "border-neutral-300 hover:border-neutral-500 text-neutral-700 bg-white"
          }`}
          data-testid={`${buttonBase}-${p.key}`}
        >
          {p.label}
        </button>
      ))}
    </div>
  );
}

export function HorizonHeader({ number, title, subtitle, testid }) {
  return (
    <div className="flex items-baseline gap-3 mb-3" data-testid={testid}>
      <span className="text-[10px] font-mono tracking-widest text-neutral-400">
        HORIZON {number}
      </span>
      <h2 className="text-sm font-semibold text-neutral-900">{title}</h2>
      {subtitle ? (
        <span className="text-xs text-neutral-500">· {subtitle}</span>
      ) : null}
    </div>
  );
}

export function KpiTile({ label, value, unit, testid, footnote }) {
  const displayValue =
    value === null || value === undefined || Number.isNaN(value) ? "—" : value;
  return (
    <div
      className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm"
      data-testid={testid}
    >
      <div className="text-[10px] uppercase tracking-widest text-neutral-500">
        {label}
      </div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className="text-2xl font-semibold text-neutral-900 tabular-nums">
          {displayValue}
        </span>
        {unit ? (
          <span className="text-xs font-normal text-neutral-500">{unit}</span>
        ) : null}
      </div>
      {footnote ? (
        <div className="mt-1 text-[10px] text-neutral-400">{footnote}</div>
      ) : null}
    </div>
  );
}

export function EmptyEvidence({ label }) {
  return (
    <div className="text-xs text-neutral-500 italic py-3">
      {label || "No operational records in this range."}
    </div>
  );
}

const SEVERITY_STYLE = {
  critical: "bg-red-100 text-red-800 border-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-200",
  medium: "bg-amber-100 text-amber-800 border-amber-200",
  low: "bg-yellow-100 text-yellow-800 border-yellow-200",
  unknown: "bg-neutral-100 text-neutral-700 border-neutral-200",
};

function severityClass(sev) {
  const s = String(sev || "unknown").toLowerCase();
  return SEVERITY_STYLE[s] || SEVERITY_STYLE.unknown;
}

export function AttentionList({ title, items, kind, testid }) {
  if (!items || items.length === 0) {
    return (
      <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid={testid}>
        <div className="text-xs uppercase tracking-widest text-neutral-500 mb-2">
          {title}
        </div>
        <EmptyEvidence label={`No ${kind} records in this range.`} />
      </div>
    );
  }
  return (
    <div className="rounded-lg border border-neutral-200 bg-white p-4" data-testid={testid}>
      <div className="flex items-baseline justify-between mb-2">
        <div className="text-xs uppercase tracking-widest text-neutral-500">
          {title}
        </div>
        <div className="text-[10px] text-neutral-400">
          {items.length} {items.length === 1 ? "item" : "items"}
        </div>
      </div>
      <ul className="divide-y divide-neutral-100">
        {items.map((it) => (
          <li
            key={it.fact_id}
            className="py-2 flex items-start gap-3"
            data-testid={`${testid}-item-${it.fact_id}`}
          >
            <span
              className={`inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-medium uppercase ${severityClass(
                it.severity,
              )}`}
            >
              {humanizeToken(it.severity || "review")}
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-sm text-neutral-900 truncate">{it.summary || "Operational review item"}</div>
              <div className="text-[10px] text-neutral-500 mt-0.5 font-mono">
                {formatAttentionContext(it)}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function EvidenceFooter({ children }) {
  return (
    <p
      className="text-[11px] text-neutral-400 pt-4 border-t border-neutral-100 mt-6"
      data-testid="ods-evidence-footer"
    >
      {children || (
        <>
          Sourced from current operating records · every metric traces back to
          reports, photos, and events submitted by field supervisors.
        </>
      )}
    </p>
  );
}
