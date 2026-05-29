// PmExposureTile.jsx — Phase V.2 · Wave-1B.
//
// Calm PM signal aggregator. Reads /api/daily-reports/exposure-signals
// and renders a slate, non-alarming tile that surfaces:
//   - Potential RFI signals (advisory · NEVER creates an RFI)
//   - Potential schedule signals (advisory · NEVER mutates schedule)
//   - Top constraint types
//   - Recent constraint trend
//
// Doctrine:
//   /app/memory/PM_EXPOSURE_TILE_CERTIFICATION.md
//   /app/memory/ADVISORY_FLAG_CERTIFICATION.md
//   /app/memory/ODR_PLATFORM_INHERITANCE_DOCTRINE.md (one MASCI Ops feel)
//
// Operator copy is calm by contract. No red. No urgency pills. No
// exclamation marks. The tile informs; it does not interrupt.

import React from "react";
import api from "@/lib/api";

const _CONSTRAINT_LABELS = {
  weather: "Weather",
  utility: "Utility",
  survey: "Survey",
  material: "Material",
  equipment: "Equipment",
  trucking: "Trucking",
  mot: "MOT",
  cei_inspection: "CEI / Inspection",
  owner_engineer: "Owner / Engineer",
  safety: "Safety",
  other: "Other",
};

export default function PmExposureTile({ days = 14, className = "" }) {
  const [d, setD] = React.useState(null);
  const [err, setErr] = React.useState("");
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.get(`/daily-reports/exposure-signals?days=${days}`)
      .then((r) => { if (!cancelled) setD(r.data); })
      .catch((e) => { if (!cancelled) setErr(e?.message || "Load failed"); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [days]);

  if (loading) {
    return (
      <div
        data-testid="pm-exposure-tile-loading"
        className={"rounded-md border border-slate-200 bg-white p-4 text-sm text-slate-500 " + className}
      >
        Loading signals…
      </div>
    );
  }
  if (err) {
    return (
      <div className={"rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 " + className}>
        Signals unavailable.
      </div>
    );
  }
  if (!d) return null;

  return (
    <div
      data-testid="pm-exposure-tile"
      className={"rounded-md border border-slate-200 bg-white p-4 " + className}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs uppercase tracking-wider text-slate-500">
            PM Signals
          </div>
          <div className="text-sm font-medium text-slate-800">
            Last {d.window_days} days · advisory only
          </div>
        </div>
        <div className="text-[10px] uppercase tracking-wider text-slate-400">
          Signal only · no actions taken
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <SignalCell
          label="Potential RFI signals"
          value={d.rfi_signal_count}
          testId="rfi-signal-count"
        />
        <SignalCell
          label="Potential schedule signals"
          value={d.schedule_signal_count}
          testId="schedule-signal-count"
        />
      </div>

      <div className="mt-4">
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
          Top constraint types
        </div>
        <ul className="space-y-1" data-testid="top-constraint-types">
          {(d.top_constraint_types || []).length === 0 ? (
            <li className="text-xs text-slate-400">No constraints logged.</li>
          ) : null}
          {(d.top_constraint_types || []).map((row) => (
            <li
              key={row.constraint_type}
              className="flex items-center justify-between text-sm text-slate-700"
            >
              <span>{_CONSTRAINT_LABELS[row.constraint_type] || row.constraint_type}</span>
              <span className="font-mono text-slate-500">{row.count}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-4">
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
          Recent trend
        </div>
        <ul className="space-y-1" data-testid="recent-trend">
          {(d.recent_trend || []).length === 0 ? (
            <li className="text-xs text-slate-400">No recent constraints.</li>
          ) : null}
          {(d.recent_trend || []).map((row) => (
            <li
              key={row.date}
              className="flex items-center justify-between text-sm text-slate-700"
            >
              <span className="font-mono text-xs">{row.date}</span>
              <span className="font-mono text-slate-500">{row.count}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function SignalCell({ label, value, testId }) {
  return (
    <div
      data-testid={testId}
      className="rounded-md border border-slate-200 bg-slate-50 p-3"
    >
      <div className="text-2xl font-semibold text-slate-800 tabular-nums">
        {value ?? 0}
      </div>
      <div className="mt-1 text-xs text-slate-500 leading-snug">
        {label}
      </div>
    </div>
  );
}
