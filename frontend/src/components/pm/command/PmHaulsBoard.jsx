/**
 * pm/command/PmHaulsBoard.jsx — Section 2.
 * Active dispatch hauls for this PM scope.
 */
import React, { useCallback, useEffect, useState } from "react";
import PmBoardShell, { TrustChip, IntegrationChip } from "./PmBoardShell";
import { pmCommandApi } from "./pmCommandApi";

export default function PmHaulsBoard({ projectNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const d = await pmCommandApi.hauls(projectNumber, 500);
      setData(d);
    } catch (e) { setError(e?.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, [projectNumber]);
  useEffect(() => { load(); }, [load]);

  const rows = data?.rows || [];

  return (
    <PmBoardShell
      title="Active Hauls"
      subtitle="dispatch_lifecycle · non-terminal"
      count={rows.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && rows.length === 0}
      emptyText="No active hauls for this PM scope."
      testId="pm-cc-hauls"
    >
      <div className="overflow-x-auto -mx-3 sm:mx-0">
        <table className="w-full min-w-[900px] text-xs sm:text-sm">
          <thead>
            <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
              <th className="py-2 pl-3 pr-2">Truck</th>
              <th className="py-2 px-2">Driver</th>
              <th className="py-2 px-2">Material</th>
              <th className="py-2 px-2">Source</th>
              <th className="py-2 px-2">Destination</th>
              <th className="py-2 px-2">Project</th>
              <th className="py-2 px-2">State</th>
              <th className="py-2 px-2">Cycles</th>
              <th className="py-2 pr-3 pl-2">FleetWatcher</th>
            </tr>
          </thead>
          <tbody data-testid="pm-cc-hauls-rows">
            {rows.map((r, i) => (
              <tr
                key={`${r.truck_id}-${r.assignment_id || i}`}
                data-testid={`pm-cc-hauls-row-${r.assignment_id || i}`}
                className="border-b border-slate-100 hover:bg-slate-50"
              >
                <td className="py-2 pl-3 pr-2 font-mono font-bold text-slate-900">{r.truck_id}</td>
                <td className="py-2 px-2 text-slate-700">{r.driver_name === "no_driver" ? <TrustChip state="no_driver">no driver</TrustChip> : r.driver_name}</td>
                <td className="py-2 px-2 text-slate-700">{r.material || "—"}</td>
                <td className="py-2 px-2 text-slate-700">{r.source || "—"}</td>
                <td className="py-2 px-2 text-slate-700">{r.destination || "—"}</td>
                <td className="py-2 px-2 font-mono text-slate-700">{r.project_number || "—"}</td>
                <td className="py-2 px-2">
                  <TrustChip state={r.trust_state === "breakdown" ? "breakdown" : "active_haul"}>
                    {r.current_state || r.trust_state}
                  </TrustChip>
                </td>
                <td className="py-2 px-2 font-mono text-slate-700">{r.cycle_count ?? 0}</td>
                <td className="py-2 pr-3 pl-2">
                  <IntegrationChip name="FleetWatcher" status="not_connected" testId={`pm-cc-hauls-fw-${r.assignment_id || i}`} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PmBoardShell>
  );
}
