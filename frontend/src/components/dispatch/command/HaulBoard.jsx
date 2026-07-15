/**
 * HaulBoard.jsx · Live Haul Board — Dispatch Command Center V1 Phase 2.
 *
 * Reads /api/dispatch/command/haul. Active haul cycles with material,
 * source, destination, truck, driver, job, lifecycle state. FleetWatcher
 * fields render as "—" + "Not Connected" chip until activation.
 *
 * Polls every 15s (fastest cadence — operational pulse).
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { commandApi } from "./commandApi";
import {
  BoardShell, StatusChip, SearchBar, FilterChips,
} from "./BoardShell";

const POLL_MS = 15000;

function fmtAgo(iso) {
  if (!iso) return "—";
  try {
    const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
    if (m < 1) return "now";
    if (m < 60) return `${m}m`;
    return `${Math.floor(m / 60)}h`;
  } catch { return "—"; }
}

export default function HaulBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    try {
      setRefreshing(true);
      const d = await commandApi.haul(500);
      setData(d); setError(null);
    } catch (e) { setError(e.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  const rows = useMemo(() => (data?.rows || []), [data?.rows]);
  const counts = useMemo(() => (data?.counts || {}), [data?.counts]);
  const fwConnected = data?.integration_readiness?.fleetwatcher !== "not_connected";

  const filterOptions = useMemo(() => [
    { value: "all",       label: "All",         count: counts.active_hauls },
    { value: "waiting",   label: "Waiting",     count: (counts.waiting_on_plant || 0) + (counts.waiting_on_dump || 0) },
    { value: "breakdown", label: "Breakdown",   count: counts.breakdown_impacts },
    { value: "material",  label: "Material",    count: rows.filter(r => (r.haul_type || "Material") === "Material").length },
    { value: "equipment", label: "Equip Move",  count: rows.filter(r => r.haul_type === "Equipment Move").length },
  ], [counts, rows]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let r = rows;
    if (filter === "waiting")    r = r.filter(x => x.current_state === "WAITING");
    if (filter === "breakdown")  r = r.filter(x => x.current_state === "BREAKDOWN");
    if (filter === "material")   r = r.filter(x => (x.haul_type || "Material") === "Material");
    if (filter === "equipment")  r = r.filter(x => x.haul_type === "Equipment Move");
    if (q) {
      r = r.filter(x => {
        const hay = [
          x.material, x.liquid_product, x.source, x.destination,
          x.truck_id, x.driver_name, x.project_number, x.project_name,
        ].filter(Boolean).join(" ").toLowerCase();
        return hay.includes(q);
      });
    }
    return r;
  }, [rows, search, filter]);

  return (
    <BoardShell
      testId="haul-board"
      title="Hauls"
      subtitle={data?.as_of ? `as of ${fmtAgo(data.as_of)} ago` : ""}
      count={filtered.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && !error && rows.length === 0}
      emptyText="No active hauls right now."
      toolbar={
        <>
          <SearchBar
            value={search} onChange={setSearch}
            placeholder="Search material, truck, driver, job…"
            testId="haul-search"
          />
          <FilterChips
            options={filterOptions} value={filter} onChange={setFilter}
            testIdRoot="haul"
          />
          <div className="ml-auto" data-testid="haul-integration-status">
            <StatusChip tone={fwConnected ? "active" : "pending"}>
              FleetWatcher · {fwConnected ? "Live" : "Pending Integration"}
            </StatusChip>
          </div>
        </>
      }
    >
      <div className="overflow-x-auto -mx-3 sm:-mx-4">
        <div className="min-w-[920px] max-h-[70vh] overflow-y-auto" data-testid="haul-board-list">
          <table className="w-full text-xs sm:text-sm">
            <thead className="sticky top-0 bg-slate-50 z-10 border-b border-slate-200">
              <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-slate-600">
                <th className="px-3 py-2">Truck</th>
                <th className="px-2 py-2">Driver</th>
                <th className="px-2 py-2">Material</th>
                <th className="px-2 py-2">Source</th>
                <th className="px-2 py-2">Destination</th>
                <th className="px-2 py-2">Job</th>
                <th className="px-2 py-2">State</th>
                <th className="px-2 py-2 text-right">Since</th>
                <th className="px-2 py-2 text-right">Tons (FW)</th>
                <th className="px-2 py-2 text-right">Cycle (FW)</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.assignment_id}
                  data-testid={`haul-row-${r.assignment_id}`}
                  className="border-b border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-3 py-2 font-bold text-slate-900">{r.truck_id || "—"}</td>
                  <td className="px-2 py-2 text-slate-700">{r.driver_name || "—"}</td>
                  <td className="px-2 py-2 text-slate-700">
                    {r.material || r.liquid_product || (r.haul_type === "Equipment Move" ? "Equip Move" : "—")}
                  </td>
                  <td className="px-2 py-2 text-slate-700 truncate max-w-[160px]">{r.source || "—"}</td>
                  <td className="px-2 py-2 text-slate-700 truncate max-w-[160px]">{r.destination || "—"}</td>
                  <td className="px-2 py-2 text-slate-700">{r.project_number || "—"}</td>
                  <td className="px-2 py-2">
                    <StatusChip tone={
                      r.current_state === "BREAKDOWN" ? "breakdown" :
                      r.current_state === "WAITING" ? "waiting" : "info"
                    }>{r.current_state}</StatusChip>
                  </td>
                  <td className="px-2 py-2 text-right text-slate-700 font-mono">
                    {r.current_state_since_min != null ? `${r.current_state_since_min}m` : "—"}
                  </td>
                  <td className="px-2 py-2 text-right text-slate-400 font-mono text-[10px]">
                    {r.fleetwatcher?.tons != null ? r.fleetwatcher.tons : "—"}
                  </td>
                  <td className="px-2 py-2 text-right text-slate-400 font-mono text-[10px]">
                    {r.fleetwatcher?.cycle_time_min != null ? `${r.fleetwatcher.cycle_time_min}m` : "—"}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-3 py-8 text-center text-slate-500 text-sm">
                    No matching hauls.
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
