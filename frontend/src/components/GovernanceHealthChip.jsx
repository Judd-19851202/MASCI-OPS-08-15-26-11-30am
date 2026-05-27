// GovernanceHealthChip — Phase IV-BETA.5A-P1A.
//
// Tiny, monochrome, secondary-hierarchy chip that reads the persisted
// doctrine baseline (captured by tests/pw_suite/test_visual_doctrine
// _baseline.py) via /api/governance/health/{portal} and surfaces the
// current loudness composite + drift state in a single line of
// font-mono text.
//
// Doctrine:
//   • Monochrome slate text · no animation · no chart · no badge stack
//   • Operationally restrained — informational, NOT a KPI
//   • Hidden silently when the endpoint has no baseline (no error noise)
//   • One per Hub V2 surface (Admin · PM · HR · Safety)
//
// Read-only · zero PII · public endpoint.

import React, { useEffect, useState } from "react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Single static testid namespace — per-portal chips use the same
// component, the data-testid attribute carries the portal disambiguation.
export default function GovernanceHealthChip({ portal }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await fetch(`${API}/governance/health/${portal}`);
        if (!r.ok) return;
        const j = await r.json();
        if (alive && j && j.ok) setData(j);
      } catch {
        /* silent · the chip simply does not render */
      }
    })();
    return () => { alive = false; };
  }, [portal]);

  if (!data) return null;

  // State tone — strictly monochrome slate. The `state` value is a
  // semantic class for testing only; it does NOT colour the text.
  const stateLabel =
    data.state === "stable"
      ? "stable"
      : data.state === "monitor"
      ? "monitor"
      : "drift";

  return (
    <div
      className="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500"
      data-testid={`governance-health-chip-${portal}`}
      data-state={data.state || "unknown"}
      title={data.summary || ""}
    >
      <span
        className="inline-block w-1.5 h-1.5 rounded-sm bg-slate-400"
        aria-hidden="true"
      />
      <span data-testid={`governance-health-label-${portal}`}>
        governance {stateLabel}
      </span>
      <span className="text-slate-400">·</span>
      <span
        className="tabular-nums text-slate-500"
        data-testid={`governance-health-loudness-${portal}`}
      >
        {Math.round(data.loudness || 0)}/100
      </span>
    </div>
  );
}
