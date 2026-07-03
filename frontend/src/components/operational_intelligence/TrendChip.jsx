// Track 19.54 · Operational Guidance System (OGS).
//
// Universal trend-language chip. Renders DIRECTION before number so
// humans understand movement before scanning digits:
//
//   ▲ Improving — trend_direction ∈ { "up", "▲" }
//   → Stable    — trend_direction ∈ { "flat", "→", null }
//   ▼ Declining — trend_direction ∈ { "down", "▼" }
//
// Consumes ONLY the `trend_direction` / `trend_percent` / score fields
// already returned by the certified OI summary payload.

import React from "react";

function normalize(d) {
  if (d === "up" || d === "▲") return "up";
  if (d === "down" || d === "▼") return "down";
  return "flat";
}

const CFG = {
  up:   { glyph: "▲", label: "Improving",   cls: "text-emerald-700" },
  flat: { glyph: "→", label: "Stable",      cls: "text-slate-500"   },
  down: { glyph: "▼", label: "Declining",   cls: "text-red-700"     },
};

export default function TrendChip({ direction, percent, score, testId, compact = false }) {
  const dir = normalize(direction);
  const cfg = CFG[dir];
  const hasPct = typeof percent === "number";
  const hasScore = typeof score === "number";
  return (
    <span
      data-testid={testId || "trend-chip"}
      className={`inline-flex items-baseline gap-1 font-mono text-xs font-bold ${cfg.cls}`}
    >
      <span aria-hidden="true">{cfg.glyph}</span>
      {!compact && <span>{cfg.label}</span>}
      {hasScore && <span className="text-slate-900">{score}</span>}
      {hasPct && (
        <span data-testid={`${testId || "trend-chip"}-delta`}>
          {percent > 0 ? "+" : ""}{percent.toFixed(1)}%
        </span>
      )}
    </span>
  );
}
