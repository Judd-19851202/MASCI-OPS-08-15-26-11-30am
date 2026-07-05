import React from "react";
import { Section } from "@/components/Section";

/**
 * DR-ROI-001F-REPAIR · Summary Readiness — inline platform Section grammar.
 */
export default function ConfidencePanel({ ai }) {
  const outputs = ai?.result?.outputs || {};
  const aggregate = ai?.result?.aggregate_confidence ?? 0;
  const pct = Math.round(aggregate * 100);
  const tone = pct >= 75 ? "emerald" : pct >= 50 ? "amber" : "red";
  const bar =
    tone === "emerald"
      ? "bg-emerald-500"
      : tone === "amber"
      ? "bg-amber-500"
      : "bg-red-500";
  const text =
    tone === "emerald"
      ? "text-emerald-700"
      : tone === "amber"
      ? "text-amber-700"
      : "text-red-700";

  return (
    <Section
      number="09b"
      title="Summary Readiness"
      testId="dr-v2-section-summary-readiness"
      dense
    >
      <div className="space-y-3" data-testid="dr-v2-panel-confidence">
        <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
          <div
            className={`h-full ${bar} transition-all`}
            style={{ width: `${pct}%` }}
            data-testid="dr-v2-confidence-bar"
          />
        </div>

        <div className="space-y-1 text-sm">
          {Object.keys(outputs).length === 0 ? (
            <div className="text-slate-500 text-xs">
              Enter Day Setup and at least one Activity Card to build the
              summary.
            </div>
          ) : (
            Object.entries(outputs).map(([source, o]) => {
              const c = Math.round((o?.confidence ?? 0) * 100);
              const rowTone =
                c >= 75
                  ? "text-emerald-700"
                  : c >= 50
                  ? "text-amber-700"
                  : "text-red-700";
              return (
                <div
                  key={source}
                  className="flex items-center justify-between"
                  data-testid={`dr-v2-confidence-agent-${source}`}
                >
                  <span className="capitalize text-slate-800">
                    {source.replaceAll("_", " ")}
                  </span>
                  <span className={`font-mono text-xs ${rowTone}`}>{c}%</span>
                </div>
              );
            })
          )}
        </div>

        {Object.values(outputs).some((o) => o?.uncertainties?.length) ? (
          <div
            className="text-xs rounded-md border border-amber-300 bg-amber-50 p-2 space-y-1 text-amber-900"
            data-testid="dr-v2-panel-uncertainties"
          >
            <div className="font-semibold">Items to verify</div>
            {Object.entries(outputs).map(([source, o]) =>
              (o?.uncertainties || []).map((u, i) => (
                <div key={`${source}-${i}`}>
                  · <span className="opacity-70">{source}:</span> {u}
                </div>
              )),
            )}
          </div>
        ) : null}

        <p className={`text-[11px] ${text}`}>
          Aggregate = weakest source · updates as you enter more evidence.
        </p>
      </div>
    </Section>
  );
}
