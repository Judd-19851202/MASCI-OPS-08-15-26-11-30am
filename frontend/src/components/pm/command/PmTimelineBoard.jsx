/**
 * pm/command/PmTimelineBoard.jsx — Section 6.
 * Chronological cross-source operational feed for this PM scope.
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  Activity, ArrowRightLeft, AlertTriangle, Wrench, Truck,
} from "lucide-react";
import PmBoardShell, { TrustChip } from "./PmBoardShell";
import { pmCommandApi } from "./pmCommandApi";

const ICON_BY_KIND = {
  asset_transfer: ArrowRightLeft,
  dispatch_state: Activity,
  incident: AlertTriangle,
  shop_event: Wrench,
  default: Truck,
};

export default function PmTimelineBoard({ projectNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const d = await pmCommandApi.timeline(projectNumber, 7, 300);
      setData(d);
    } catch (e) { setError(e?.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, [projectNumber]);
  useEffect(() => { load(); }, [load]);

  const events = data?.events || [];

  return (
    <PmBoardShell
      title="Project Timeline"
      subtitle="last 7 days"
      count={events.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && events.length === 0}
      emptyText="No recent activity for this PM scope."
      testId="pm-cc-timeline"
    >
      <ol className="space-y-1.5" data-testid="pm-cc-timeline-events">
        {events.map((ev, i) => {
          const Icon = ICON_BY_KIND[ev.kind] || ICON_BY_KIND.default;
          return (
            <li
              key={`${ev.timestamp}-${i}`}
              data-testid={`pm-cc-timeline-event-${i}`}
              className="flex items-start gap-2 border-b border-slate-100 last:border-b-0 py-1.5"
            >
              <Icon className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" aria-hidden="true" />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-baseline gap-2">
                  <span className="font-mono text-[10.5px] text-slate-500">
                    {String(ev.timestamp || "—").slice(0, 16).replace("T", " ")}
                  </span>
                  <TrustChip state={ev.trust_state || ev.kind}>{ev.kind}</TrustChip>
                  {ev.project_number ? (
                    <span className="font-mono text-[10.5px] text-slate-500">{ev.project_number}</span>
                  ) : null}
                </div>
                <div className="text-xs sm:text-sm text-slate-700 truncate" title={ev.summary}>
                  {ev.summary || "—"}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </PmBoardShell>
  );
}
