/**
 * JobBoard.jsx · Live Job Board — Dispatch Command Center V1 Phase 2.
 *
 * Per-project rollup: active drivers · active assets · active trucks ·
 * active equipment · active hauls · open safety issues · open defects.
 * PM visibility tile-ready (PM Command Center will reuse this contract).
 *
 * Polls every 60s (jobs change slower than driver state).
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { commandApi } from "./commandApi";
import {
  BoardShell, StatusChip, SearchBar,
} from "./BoardShell";

const POLL_MS = 60000;

function fmtAgo(iso) {
  if (!iso) return "—";
  try {
    const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
    if (m < 1) return "now";
    if (m < 60) return `${m}m`;
    return `${Math.floor(m / 60)}h`;
  } catch { return "—"; }
}

export default function JobBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    try {
      setRefreshing(true);
      const d = await commandApi.jobs(500);
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

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => {
      const hay = [r.project_number, r.project_name].filter(Boolean).join(" ").toLowerCase();
      return hay.includes(q);
    });
  }, [rows, search]);

  return (
    <BoardShell
      testId="job-board"
      title="Jobs"
      subtitle={data?.as_of ? `as of ${fmtAgo(data.as_of)} ago` : ""}
      count={filtered.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && !error && rows.length === 0}
      emptyText="No active jobs today."
      toolbar={
        <SearchBar
          value={search} onChange={setSearch}
          placeholder="Search project number or name…"
          testId="job-search"
        />
      }
    >
      <div className="overflow-x-auto -mx-3 sm:-mx-4">
        <div className="min-w-[900px] max-h-[70vh] overflow-y-auto" data-testid="job-board-list">
          <table className="w-full text-xs sm:text-sm">
            <thead className="sticky top-0 bg-slate-50 z-10 border-b border-slate-200">
              <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-slate-600">
                <th className="px-3 py-2">Project</th>
                <th className="px-2 py-2 text-right">Drivers</th>
                <th className="px-2 py-2 text-right">Trucks</th>
                <th className="px-2 py-2 text-right">Equip</th>
                <th className="px-2 py-2 text-right">Trailers</th>
                <th className="px-2 py-2 text-right">Hauls</th>
                <th className="px-2 py-2 text-right">Loads</th>
                <th className="px-2 py-2 text-right">Mat In</th>
                <th className="px-2 py-2 text-right">Mat Out</th>
                <th className="px-2 py-2 text-right">Incidents</th>
                <th className="px-2 py-2 text-right">Breakdowns</th>
                <th className="px-2 py-2 text-right">Waiting</th>
                <th className="px-2 py-2">Attention</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.project_number}
                  data-testid={`job-row-${r.project_number}`}
                  className="border-b border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-3 py-2">
                    <div className="font-bold text-slate-900">{r.project_number}</div>
                    {r.project_name && r.project_name !== r.project_number ? (
                      <div className="text-[10px] text-slate-500 truncate max-w-[180px]">{r.project_name}</div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2 text-right font-mono">{r.drivers_today}</td>
                  <td className="px-2 py-2 text-right font-mono">{r.trucks_today}</td>
                  <td className="px-2 py-2 text-right font-mono">{r.equipment_today}</td>
                  <td className="px-2 py-2 text-right font-mono">{r.trailers_today}</td>
                  <td className="px-2 py-2 text-right font-mono">{r.assignments_today}</td>
                  <td className="px-2 py-2 text-right font-mono">{r.loads_today}</td>
                  <td className="px-2 py-2 text-right font-mono">{r.materials_in_count}</td>
                  <td className="px-2 py-2 text-right font-mono">{r.materials_out_count}</td>
                  <td className="px-2 py-2 text-right font-mono">
                    <span className={r.incidents_open > 0 ? "text-rose-700 font-bold" : ""}>
                      {r.incidents_open}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-right font-mono">
                    <span className={r.breakdowns_today > 0 ? "text-rose-700 font-bold" : ""}>
                      {r.breakdowns_today}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-right font-mono">{r.waiting_today}</td>
                  <td className="px-2 py-2">
                    {r.attention_tag ? (
                      <StatusChip tone={r.attention_tag === "BREAKDOWN" ? "breakdown" : "waiting"}>
                        {r.attention_tag}
                      </StatusChip>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={13} className="px-3 py-8 text-center text-slate-500 text-sm">
                    No matching projects.
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
