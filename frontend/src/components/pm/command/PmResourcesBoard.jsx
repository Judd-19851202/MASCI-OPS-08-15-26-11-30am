/**
 * pm/command/PmResourcesBoard.jsx — Section 1.
 *
 * PM-scoped roster of trucks · trailers · equipment · road plates ·
 * safety · support assets. Backed by /api/pm/command-center/resources.
 * Road Plates surfaced as first-class rows via backend normalization.
 */
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import PmBoardShell, { TrustChip, IntegrationChip } from "./PmBoardShell";
import { pmCommandApi } from "./pmCommandApi";

const KIND_LABEL = {
  truck: "Truck",
  trailer: "Trailer",
  road_plate: "Road Plate",
  safety: "Safety",
  equipment: "Equipment",
  support: "Support",
};

function kindOf(k) {
  if (!k) return "unknown";
  return KIND_LABEL[k] || k.toString().replace(/_/g, " ");
}

export default function PmResourcesBoard({ projectNumber, initialKind = "all" }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [kind, setKind] = useState(initialKind);  useEffect(() => { setKind(initialKind); }, [initialKind]);

  const load = useCallback(async () => {
    setError(null);
    setRefreshing(true);
    try {
      const d = await pmCommandApi.resources(projectNumber, 1000);
      setData(d);
    } catch (e) { setError(e?.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, [projectNumber]);
  useEffect(() => { load(); }, [load]);

  const rows = useMemo(() => {
    const r = data?.rows || [];
    if (kind === "all") return r;
    return r.filter((x) => x.asset_kind === kind);
  }, [data, kind]);

  const counts = data?.counts_by_kind || {};
  const filterOptions = [
    { value: "all", label: "All", count: (data?.rows || []).length },
    { value: "truck", label: "Trucks", count: counts.truck || 0 },
    { value: "trailer", label: "Trailers", count: counts.trailer || 0 },
    { value: "road_plate", label: "Road Plates", count: counts.road_plate || 0 },
  ];

  const toolbar = (
    <div className="flex flex-wrap items-center gap-1.5" data-testid="pm-cc-resources-filters">
      {filterOptions.map((o) => {
        const active = o.value === kind;
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => setKind(o.value)}
            data-testid={`pm-cc-resources-filter-${o.value}`}
            className={`px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded border transition-colors ${
              active
                ? "bg-slate-900 text-white border-slate-900"
                : "bg-white text-slate-700 border-slate-300 hover:border-slate-500"
            }`}
          >
            {o.label}
            <span className={`ml-1.5 font-mono ${active ? "text-slate-200" : "text-slate-500"}`}>{o.count}</span>
          </button>
        );
      })}
    </div>
  );

  return (
    <PmBoardShell
      title="Project Resources"
      subtitle="Asset Spine · live"
      count={rows.length}
      onRefresh={load}
      refreshing={refreshing}
      toolbar={toolbar}
      loading={loading}
      error={error}
      empty={!loading && rows.length === 0}
      emptyText={
        kind === "road_plate"
          ? "No road plates assigned to this PM scope."
          : "No resources for this PM scope."
      }
      testId="pm-cc-resources"
    >
      <div className="overflow-x-auto -mx-3 sm:mx-0">
        <table className="w-full min-w-[800px] text-xs sm:text-sm">
          <thead>
            <tr className="text-left text-[10px] uppercase tracking-widest text-slate-500 border-b border-slate-200">
              <th className="py-2 pl-3 pr-2">Asset</th>
              <th className="py-2 px-2">Kind</th>
              <th className="py-2 px-2">Project</th>
              <th className="py-2 px-2">Driver</th>
              <th className="py-2 px-2">Status</th>
              <th className="py-2 px-2">Shop</th>
              <th className="py-2 px-2">Last Activity</th>
              <th className="py-2 px-2">Trust</th>
              <th className="py-2 pr-3 pl-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody data-testid="pm-cc-resources-rows">
            {rows.map((r, i) => (
              <tr
                key={`${r.unit_number}-${i}`}
                data-testid={`pm-cc-resources-row-${r.unit_number}`}
                className="border-b border-slate-100 hover:bg-slate-50"
              >
                <td className="py-2 pl-3 pr-2 font-mono font-bold text-slate-900">{r.unit_number}</td>
                <td className="py-2 px-2 text-slate-700">{kindOf(r.asset_kind)}</td>
                <td className="py-2 px-2 font-mono text-slate-700">{r.project_number || "—"}</td>
                <td className="py-2 px-2 text-slate-700">{r.current_driver_name === "no_driver" ? <TrustChip state="no_driver">no driver</TrustChip> : r.current_driver_name}</td>
                <td className="py-2 px-2 text-slate-700">{r.status || "—"}</td>
                <td className="py-2 px-2">
                  {r.open_defect_count > 0 ? (
                    <TrustChip state="open_defect">{r.open_defect_count} defect{r.open_defect_count === 1 ? "" : "s"}</TrustChip>
                  ) : (
                    <span className="text-slate-400 text-[11px]">—</span>
                  )}
                </td>
                <td className="py-2 px-2 font-mono text-[11px] text-slate-600">
                  {r.last_activity_at === "no_recent_activity" ? (
                    <TrustChip state="no_activity">no recent activity</TrustChip>
                  ) : (
                    String(r.last_activity_at || "—").slice(0, 16).replace("T", " ")
                  )}
                </td>
                <td className="py-2 px-2">
                  <TrustChip state={r.trust_state}>{r.trust_state}</TrustChip>
                </td>
                <td className="py-2 pr-3 pl-2 text-right space-x-1.5 whitespace-nowrap">
                  {r.asset_id ? (
                    <Link
                      to={`/admin/asset-spine/${r.asset_id}`}
                      data-testid={`pm-cc-resources-action-asset-${r.unit_number}`}
                      className="text-[11px] text-slate-600 hover:text-slate-900 underline-offset-2 hover:underline"
                    >
                      Asset →
                    </Link>
                  ) : null}
                  {r.open_defect_count > 0 ? (
                    <Link
                      to="/shop"
                      data-testid={`pm-cc-resources-action-shop-${r.unit_number}`}
                      className="text-[11px] text-amber-700 hover:text-amber-900 underline-offset-2 hover:underline"
                    >
                      Shop →
                    </Link>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-end gap-2 pt-2">
        <IntegrationChip name="FleetWatcher" status="not_connected" testId="pm-cc-resources-fleetwatcher-chip" />
        <IntegrationChip name="MaintainX" status="not_connected" testId="pm-cc-resources-maintainx-chip" />
      </div>
    </PmBoardShell>
  );
}
