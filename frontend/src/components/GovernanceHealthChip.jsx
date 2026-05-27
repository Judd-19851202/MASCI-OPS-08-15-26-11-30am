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

  // iter437 IV-BETA.5A-P2A · Direction-aware chip.
  //
  // The chip surfaces one of three operational states:
  //   • stable     — current loudness within calm band AND no material trend
  //   • improving  — calmness DROPPED ≥ 4 points vs prior window (good)
  //   • drifting   — calmness ROSE ≥ 4 points vs prior window (warn)
  //
  // The endpoint's `direction` field carries: stable | improving |
  // drifting | new. We blend it with the static `state` (stable/monitor/
  // drift) to choose the chip label — but the footprint NEVER changes
  // (one slate dot + two text spans). No animation, no badge, no chart.

  const dir = data.direction || "new";
  const delta = typeof data.delta === "number" ? data.delta : null;
  const state = data.state || "stable";
  // iter437 IV-BETA.5A-P5A · Checkpoint-aware reference.
  // The endpoint distinguishes operator checkpoints from auto-deploy
  // checkpoints via `checkpoint_kind`. The chip suffix follows:
  //   • operator → "since checkpoint"   (sacred milestone reference)
  //   • auto     → "since deploy"       (operational breadcrumb)
  const sinceCp = data.reference === "checkpoint";
  const kind = data.checkpoint_kind || "operator";
  const sinceSuffix = sinceCp
    ? (kind === "auto" ? " since deploy" : " since checkpoint")
    : "";

  // Choose label by priority: a real `drift` state always wins; otherwise
  // honour the direction signal; fall back to the static state.
  let label;
  let trailing;
  if (state === "drift") {
    label = "governance drift";
    trailing = `${Math.round(data.loudness || 0)}/100`;
  } else if (dir === "improving" && delta !== null) {
    label = "governance improving";
    trailing = `${delta > 0 ? "+" : ""}${delta} drift${sinceSuffix}`;
  } else if (dir === "drifting" && delta !== null) {
    label = "governance drifting";
    trailing = `+${Math.abs(delta)} drift${sinceSuffix}`;
  } else if (state === "monitor") {
    label = "governance monitor";
    trailing = `${Math.round(data.loudness || 0)}/100`;
  } else {
    label = "governance stable";
    trailing = `${Math.round(data.loudness || 0)}/100`;
  }

  return (
    <div
      className="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500"
      data-testid={`governance-health-chip-${portal}`}
      data-state={state}
      data-direction={dir}
      data-reference={data.reference || "rolling"}
      title={data.checkpoint_label
        ? `Checkpoint: ${data.checkpoint_label}`
        : (data.summary || "")}
    >
      <span
        className="inline-block w-1.5 h-1.5 rounded-sm bg-slate-400"
        aria-hidden="true"
      />
      <span data-testid={`governance-health-label-${portal}`}>{label}</span>
      <span className="text-slate-400">·</span>
      <span
        className="tabular-nums text-slate-500"
        data-testid={`governance-health-loudness-${portal}`}
      >
        {trailing}
      </span>
    </div>
  );
}
