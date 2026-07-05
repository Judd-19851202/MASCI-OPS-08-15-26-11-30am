import React from "react";
import { SectionCard } from "../_ui";

/**
 * DR-ROI-001 · Phase C · Confidence + Validation panel.
 *
 * Consumes the aggregate confidence and per-agent scores from the
 * useDrV2Ai hook. Aggregate = min(agent confidences) — the weakest
 * link rules. Uncertainty flags surface here so the supervisor sees
 * exactly what evidence AI could not verify.
 */
export default function ConfidencePanel({ ai }) {
  const outputs = ai?.result?.outputs || {};
  const aggregate = ai?.result?.aggregate_confidence ?? 0;
  const pct = Math.round(aggregate * 100);
  const level = pct >= 75 ? "green" : pct >= 50 ? "amber" : "red";
  const cacheHits = ai?.result?.cache_hits ?? 0;
  const cacheMisses = ai?.result?.cache_misses ?? 0;

  return (
    <SectionCard id="panel-confidence" title="Confidence & Validation" badge={`${pct}%`}>
      <div className="space-y-3" data-testid="dr-v2-panel-confidence">
        <div className="text-xs opacity-70">
          Aggregate = weakest agent confidence · evidence-hashed cache: {cacheHits} hits · {cacheMisses} misses
        </div>

        <div className="w-full h-2 rounded-full bg-neutral-800 overflow-hidden">
          <div
            className={`h-full ${level === "green" ? "bg-emerald-500" : level === "amber" ? "bg-amber-500" : "bg-red-500"}`}
            style={{ width: `${pct}%` }}
            data-testid="dr-v2-confidence-bar"
          />
        </div>

        <div className="space-y-1 text-xs">
          {Object.keys(outputs).length === 0 ? (
            <div className="opacity-70">Awaiting first synthesis…</div>
          ) : (
            Object.entries(outputs).map(([agent, o]) => {
              const c = Math.round((o?.confidence ?? 0) * 100);
              return (
                <div key={agent} className="flex items-center justify-between" data-testid={`dr-v2-confidence-agent-${agent}`}>
                  <span className="capitalize opacity-90">{agent.replaceAll("_", " ")}</span>
                  <span className={c >= 75 ? "text-emerald-300" : c >= 50 ? "text-amber-300" : "text-red-300"}>{c}%</span>
                </div>
              );
            })
          )}
        </div>

        {Object.values(outputs).some((o) => o?.uncertainties?.length) ? (
          <div className="text-xs rounded-md border border-amber-800/60 bg-amber-950/20 p-2 space-y-1" data-testid="dr-v2-panel-uncertainties">
            <div className="font-semibold opacity-90">Uncertainties</div>
            {Object.entries(outputs).map(([agent, o]) => (o?.uncertainties || []).map((u, i) => (
              <div key={`${agent}-${i}`} className="opacity-90">· <span className="opacity-70">{agent}:</span> {u}</div>
            )))}
          </div>
        ) : null}
      </div>
    </SectionCard>
  );
}
