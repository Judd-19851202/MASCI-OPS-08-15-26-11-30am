/**
 * pm/command/PmMaterialsBoard.jsx — Section 3.
 * Material movement (in/out) from daily_reports for this PM scope.
 */
import React, { useCallback, useEffect, useState } from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import PmBoardShell, { TrustChip } from "./PmBoardShell";
import { pmCommandApi } from "./pmCommandApi";

export default function PmMaterialsBoard({ projectNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const d = await pmCommandApi.materials(projectNumber, 7);
      setData(d);
    } catch (e) { setError(e?.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, [projectNumber]);
  useEffect(() => { load(); }, [load]);

  const rows = data?.rows || [];
  const totals = data?.totals || {};

  return (
    <PmBoardShell
      title="Material Movement"
      subtitle={`last 7 days · ${totals.deliveries || 0} in · ${totals.removals || 0} out · ${totals.hauls || 0} hauls`}
      count={rows.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && rows.length === 0}
      emptyText="No material movement recorded for this PM scope."
      testId="pm-cc-materials"
    >
      <div className="overflow-x-auto -mx-3 sm:mx-0">
        <table className="w-full min-w-[800px] text-xs sm:text-sm">
          <thead>
            <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
              <th className="py-2 pl-3 pr-2">Date</th>
              <th className="py-2 px-2">Direction</th>
              <th className="py-2 px-2">Material</th>
              <th className="py-2 px-2">Source</th>
              <th className="py-2 px-2">Destination</th>
              <th className="py-2 px-2">Project</th>
              <th className="py-2 px-2">Qty</th>
              <th className="py-2 pr-3 pl-2">Trust</th>
            </tr>
          </thead>
          <tbody data-testid="pm-cc-materials-rows">
            {rows.map((r, i) => (
              <tr
                key={`${r.report_date}-${r.direction}-${i}`}
                data-testid={`pm-cc-materials-row-${i}`}
                className="border-b border-slate-100 hover:bg-slate-50"
              >
                <td className="py-2 pl-3 pr-2 font-mono text-slate-700">{r.report_date}</td>
                <td className="py-2 px-2">
                  {r.direction === "in" ? (
                    <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-xs">
                      <ArrowDownRight className="w-3 h-3" /> IN
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-sky-700 font-bold text-xs">
                      <ArrowUpRight className="w-3 h-3" /> OUT
                    </span>
                  )}
                </td>
                <td className="py-2 px-2 text-slate-900 font-bold">{r.material || "—"}</td>
                <td className="py-2 px-2 text-slate-700">{r.source || "—"}</td>
                <td className="py-2 px-2 text-slate-700">{r.destination || "—"}</td>
                <td className="py-2 px-2 font-mono text-slate-700">{r.project_number || "—"}</td>
                <td className="py-2 px-2 font-mono text-slate-700">
                  {r.actual_quantity ?? r.estimated_quantity ?? "—"}
                </td>
                <td className="py-2 pr-3 pl-2">
                  <TrustChip state={r.trust_state}>{r.trust_state}</TrustChip>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PmBoardShell>
  );
}
