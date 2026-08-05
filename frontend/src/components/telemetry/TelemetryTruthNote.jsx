import React from "react";

export function TelemetryTruthNote({ title = "Status meaning", items = [], testId = "telemetry-truth-note" }) {
  if (!Array.isArray(items) || items.length === 0) return null;
  return (
    <div
      className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] leading-5 text-slate-700"
      data-testid={testId}
    >
      <div className="mb-1 font-semibold uppercase tracking-[0.16em] text-slate-500">{title}</div>
      {items.map((item) => (
        <div key={item.label} className="mb-1 last:mb-0">
          <strong>{item.label}:</strong> {item.text}
        </div>
      ))}
    </div>
  );
}

export function TelemetryStaleNote({ text, testId = "telemetry-stale-note" }) {
  if (!text) return null;
  return (
    <div
      className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] leading-5 text-amber-900"
      data-testid={testId}
    >
        <strong>Showing the last verified update.</strong> {text}
    </div>
  );
}
