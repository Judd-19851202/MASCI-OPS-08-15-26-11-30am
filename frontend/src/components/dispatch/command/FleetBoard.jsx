/**
 * FleetBoard.jsx · Live Fleet Board — Dispatch Command Center V1 Phase 2.
 *
 * Reads /api/dispatch/command/fleet. Renders every asset row with:
 * unit, type, status, current driver, current job, Motive dot,
 * last DVIR, open defects. Search + status filter + sort.
 *
 * No pagination — single scroll, browser-virtualized via overflow-y-auto
 * (693 rows scrolls smooth on iPad). Polls every 30s.
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { commandApi } from "./commandApi";
import {
  BoardShell, StatusChip, IntegrationDot, SearchBar, FilterChips,
} from "./BoardShell";

const POLL_MS = 30000;

function fmtAgo(iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    const m = Math.floor((Date.now() - d.getTime()) / 60000);
    if (Number.isNaN(m)) return "—";
    if (m < 1) return "now";
    if (m < 60) return `${m}m`;
    if (m < 1440) return `${Math.floor(m / 60)}h`;
    return `${Math.floor(m / 1440)}d`;
  } catch { return "—"; }
}

export default function FleetBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("status");

  const load = useCallback(async () => {
    try {
      setRefreshing(true);
      const d = await commandApi.fleet(1000);
      setData(d); setError(null);
    } catch (e) { setError(e.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  const rows = data?.rows || [];
  const counts = data?.counts || {};

  const filterOptions = useMemo(() => [
    { value: "all",            label: "All",          count: counts.total },
    { value: "active",         label: "Active",       count: counts.active },
    { value: "oos",            label: "OOS",          count: counts.oos },
    { value: "in_shop",        label: "In Shop",      count: counts.in_shop },
    { value: "available",      label: "Available",    count: counts.available },
    { value: "needs_mapping",  label: "Needs Map",    count: counts.needs_mapping },
    { value: "unknown",        label: "Unknown",      count: counts.unknown },
  ], [counts]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let r = rows;
    if (statusFilter === "active") {
      r = r.filter(x => x.status === "active_haul" || x.status === "active_shift");
    } else if (statusFilter === "in_shop") {
      r = r.filter(x => ["in_shop", "failed_dvir", "maintenance_hold"].includes(x.status));
    } else if (statusFilter === "needs_mapping") {
      r = r.filter(x => x.status === "not_in_spine" || x.status === "motive_only");
    } else if (statusFilter !== "all") {
      r = r.filter(x => x.status === statusFilter);
    }
    if (q) {
      r = r.filter((x) => {
        const hay = [
          x.unit_number, x.asset_type, x.asset_category, x.make_model,
          x.current_driver_name, x.current_project_number, x.current_state,
        ].filter(Boolean).join(" ").toLowerCase();
        return hay.includes(q);
      });
    }
    const sorted = [...r];
    const rank = {
      oos: 0, failed_dvir: 1, in_shop: 2, maintenance_hold: 3,
      active_haul: 4, active_shift: 5, available: 6,
      motive_only: 7, not_in_spine: 8, unknown: 9,
    };
    sorted.sort((a, b) => {
      if (sortBy === "unit") {
        return String(a.unit_number || "").localeCompare(String(b.unit_number || ""));
      }
      if (sortBy === "type") {
        return String(a.asset_type || "").localeCompare(String(b.asset_type || ""));
      }
      const ra = rank[a.status] ?? 99;
      const rb = rank[b.status] ?? 99;
      if (ra !== rb) return ra - rb;
      return String(a.unit_number || "").localeCompare(String(b.unit_number || ""));
    });
    return sorted;
  }, [rows, search, statusFilter, sortBy]);

  return (
    <BoardShell
      testId="fleet-board"
      title="Fleet"
      subtitle={data?.as_of ? `as of ${fmtAgo(data.as_of)} ago` : ""}
      count={filtered.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && !error && rows.length === 0}
      emptyText="No assets returned for this tenant."
      toolbar={
        <>
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Search unit, driver, job, type…"
            testId="fleet-search"
          />
          <FilterChips
            options={filterOptions}
            value={statusFilter}
            onChange={setStatusFilter}
            testIdRoot="fleet"
          />
          <div className="ml-auto flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wider text-slate-500">
            Sort:
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              data-testid="fleet-sort"
              className="border border-slate-300 rounded px-2 py-1 text-xs"
            >
              <option value="status">Status</option>
              <option value="unit">Unit #</option>
              <option value="type">Type</option>
            </select>
          </div>
        </>
      }
    >
      <div className="overflow-x-auto -mx-3 sm:-mx-4">
        <div
          className="min-w-[760px] max-h-[70vh] overflow-y-auto"
          data-testid="fleet-board-list"
        >
          <table className="w-full text-xs sm:text-sm">
            <thead className="sticky top-0 bg-slate-50 z-10 border-b border-slate-200">
              <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-slate-600">
                <th className="px-3 py-2">Unit</th>
                <th className="px-2 py-2">Type</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Driver</th>
                <th className="px-2 py-2">Job</th>
                <th className="px-2 py-2">Dispatch</th>
                <th className="px-2 py-2 text-center">Motive</th>
                <th className="px-2 py-2">Last DVIR</th>
                <th className="px-2 py-2 text-right">Defects</th>
                <th className="px-2 py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.asset_id || r.unit_number}
                  data-testid={`fleet-row-${r.unit_number}`}
                  className="border-b border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-3 py-2 font-bold text-slate-900">
                    {r.unit_number || "—"}
                    {r.in_asset_spine === false ? (
                      <div className="text-[10px] font-mono uppercase tracking-widest text-amber-700">not_in_spine</div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2 text-slate-700">
                    <div>{r.asset_type || r.asset_category || "—"}</div>
                    {r.make_model ? (
                      <div className="text-[10px] text-slate-500 truncate max-w-[160px]">{r.make_model}</div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2">
                    <StatusChip
                      tone={r.status}
                      testId={`fleet-row-${r.unit_number}-status`}
                    >
                      {(r.status || "—").replace(/_/g, " ")}
                    </StatusChip>
                    {r.current_state ? (
                      <div className="text-[10px] text-slate-500 mt-0.5">{r.current_state}</div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2 text-slate-700">
                    {r.current_driver_name === "no_driver" ? (
                      <span className="font-mono text-[10px] text-slate-400 uppercase">no_driver</span>
                    ) : (
                      <>
                        {r.current_driver_name}
                        {!r.has_active_shift && r.current_driver_name !== "no_driver" ? (
                          <div className="text-[10px] font-mono text-slate-500">no_session</div>
                        ) : null}
                      </>
                    )}
                  </td>
                  <td className="px-2 py-2 text-slate-700">
                    {r.current_project_number === "no_job" ? (
                      <span className="font-mono text-[10px] text-slate-400 uppercase">no_job</span>
                    ) : r.current_project_number}
                  </td>
                  <td className="px-2 py-2 text-slate-700 font-mono text-[10px]">
                    {r.active_assignment_id ? r.active_assignment_id.slice(0, 8) : (
                      <span className="text-slate-400 uppercase">no_assignment</span>
                    )}
                  </td>
                  <td className="px-2 py-2 text-center">
                    <IntegrationDot
                      name="Motive"
                      connected={r.motive?.connected}
                      mapped={r.motive?.mapped}
                      stale={r.motive?.stale}
                      testId={`fleet-row-${r.unit_number}-motive`}
                    />
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      {r.motive?.connected ? fmtAgo(r.motive.last_event_at) : (
                        <span className="text-slate-400 font-mono">not_mapped</span>
                      )}
                    </div>
                  </td>
                  <td className="px-2 py-2 text-slate-700">
                    {r.last_dvir_at ? (
                      <>
                        <StatusChip tone={(r.last_dvir_fail_count || 0) > 0 ? "fail" : "pass"}>
                          {(r.last_dvir_fail_count || 0) > 0 ? "FAIL" : "PASS"}
                        </StatusChip>
                        <div className="text-[10px] text-slate-500 mt-0.5">
                          {fmtAgo(r.last_dvir_at)}
                        </div>
                      </>
                    ) : (
                      <span className="text-slate-400 text-[10px] font-mono uppercase">no_recent_activity</span>
                    )}
                  </td>
                  <td className="px-2 py-2 text-right">
                    {r.open_defect_count > 0 ? (
                      <span className="font-bold text-rose-700">{r.open_defect_count}</span>
                    ) : (
                      <span className="text-slate-300">0</span>
                    )}
                  </td>
                  <td className="px-2 py-2 text-right">
                    {!r.in_asset_spine ? (
                      <a
                        href="/admin/asset-mapping"
                        data-testid={`fleet-row-${r.unit_number}-map-asset`}
                        className="font-mono text-[10px] uppercase tracking-widest text-amber-700 hover:text-amber-900 underline"
                      >Map Asset →</a>
                    ) : !r.motive?.mapped ? (
                      <a
                        href="/admin/asset-mapping"
                        data-testid={`fleet-row-${r.unit_number}-map-motive`}
                        className="font-mono text-[10px] uppercase tracking-widest text-slate-600 hover:text-slate-900 underline"
                      >Map Motive →</a>
                    ) : r.open_defect_count > 0 || r.last_dvir_fail_count > 0 ? (
                      <a
                        href="/shop"
                        data-testid={`fleet-row-${r.unit_number}-open-shop`}
                        className="font-mono text-[10px] uppercase tracking-widest text-rose-700 hover:text-rose-900 underline"
                      >Open Shop →</a>
                    ) : r.asset_id ? (
                      <a
                        href={`/admin/asset-spine/${r.asset_id}`}
                        data-testid={`fleet-row-${r.unit_number}-open-profile`}
                        className="font-mono text-[10px] uppercase tracking-widest text-slate-500 hover:text-slate-900 underline"
                      >Profile →</a>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-3 py-8 text-center text-slate-500 text-sm">
                    No matching assets.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>
    </BoardShell>
  );
}
