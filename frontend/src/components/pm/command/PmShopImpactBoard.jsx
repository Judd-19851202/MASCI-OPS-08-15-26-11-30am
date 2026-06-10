/**
 * pm/command/PmShopImpactBoard.jsx — Section 4.
 * Shop defects + OOS units affecting this PM scope.
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import PmBoardShell, { TrustChip, IntegrationChip } from "./PmBoardShell";
import { pmCommandApi } from "./pmCommandApi";

export default function PmShopImpactBoard({ projectNumber }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const d = await pmCommandApi.shopImpact(projectNumber);
      setData(d);
    } catch (e) { setError(e?.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, [projectNumber]);
  useEffect(() => { load(); }, [load]);

  const rows = data?.rows || [];
  const counts = data?.counts || {};

  return (
    <PmBoardShell
      title="Shop Impact"
      subtitle={`${counts.open_defects || 0} open defects · ${counts.oos || 0} oos`}
      count={rows.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && rows.length === 0}
      emptyText="No shop issues affecting this PM scope."
      testId="pm-cc-shop"
    >
      <div className="overflow-x-auto -mx-3 sm:mx-0">
        <table className="w-full min-w-[800px] text-xs sm:text-sm">
          <thead>
            <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
              <th className="py-2 pl-3 pr-2">Asset</th>
              <th className="py-2 px-2">Issue</th>
              <th className="py-2 px-2">Severity</th>
              <th className="py-2 px-2">Category</th>
              <th className="py-2 px-2">Reported</th>
              <th className="py-2 px-2">Status</th>
              <th className="py-2 px-2">MaintainX</th>
              <th className="py-2 pr-3 pl-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody data-testid="pm-cc-shop-rows">
            {rows.map((r, i) => (
              <tr
                key={`${r.unit_number}-${i}`}
                data-testid={`pm-cc-shop-row-${i}`}
                className="border-b border-slate-100 hover:bg-slate-50"
              >
                <td className="py-2 pl-3 pr-2 font-mono font-bold text-slate-900">{r.unit_number}</td>
                <td className="py-2 px-2 text-slate-700 max-w-xs truncate" title={r.item_text}>{r.item_text || "—"}</td>
                <td className="py-2 px-2">
                  <TrustChip state={r.severity === "critical" || r.severity === "high" ? "open_defect" : "available"}>
                    {r.severity || "—"}
                  </TrustChip>
                </td>
                <td className="py-2 px-2 text-slate-700">{r.category || "—"}</td>
                <td className="py-2 px-2 font-mono text-[11px] text-slate-600">
                  {String(r.reported_at || "—").slice(0, 16).replace("T", " ")}
                </td>
                <td className="py-2 px-2">
                  <TrustChip state={r.trust_state || "open_defect"}>{r.status}</TrustChip>
                </td>
                <td className="py-2 px-2">
                  <IntegrationChip name="MaintainX" status="not_connected" testId={`pm-cc-shop-mx-${i}`} />
                </td>
                <td className="py-2 pr-3 pl-2 text-right whitespace-nowrap">
                  <Link
                    to="/shop"
                    data-testid={`pm-cc-shop-action-shop-${i}`}
                    className="text-[11px] text-amber-700 hover:text-amber-900 underline-offset-2 hover:underline"
                  >
                    Open Shop →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PmBoardShell>
  );
}
