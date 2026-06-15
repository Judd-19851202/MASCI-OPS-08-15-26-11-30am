/**
 * DriverBoard.jsx · Live Driver Board — Dispatch Command Center V1 Phase 2.
 *
 * Reads /api/dispatch/command/drivers. Each row shows the driver, their
 * SOS / DVIR / assignment / communication state, and an attention chip
 * when something is off (UN_ACKED · WAITING_LONG · BREAKDOWN · DVIR_FAIL).
 *
 * Phase 3.1 · added "Contact Driver" action that hands off to Comms tab.
 *
 * Polls every 30s.
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { commandApi } from "./commandApi";
import { publishCommandAction } from "./commandActions";
import {
  BoardShell, StatusChip, SearchBar, FilterChips,
} from "./BoardShell";

const POLL_MS = 30000;

function fmtAgo(iso) {
  if (!iso) return "—";
  try {
    const m = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
    if (Number.isNaN(m)) return "—";
    if (m < 1) return "now";
    if (m < 60) return `${m}m`;
    if (m < 1440) return `${Math.floor(m / 60)}h`;
    return `${Math.floor(m / 1440)}d`;
  } catch { return "—"; }
}

export default function DriverBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    try {
      setRefreshing(true);
      const d = await commandApi.drivers(1000);
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
    { value: "all",          label: "All",        count: counts.shifted },
    { value: "unacked",      label: "Un-acked",   count: counts.un_acked },
    { value: "waiting",      label: "Waiting",    count: counts.waiting },
    { value: "breakdown",    label: "Breakdown",  count: counts.in_breakdown },
    { value: "no_assn",      label: "No Assn",    count: rows.filter(r => !r.current_assignment_id).length },
    { value: "missing_dvir", label: "No DVIR",    count: rows.filter(r => !r.last_dvir_at).length },
  ], [counts, rows]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let r = rows;
    if (filter === "unacked")      r = r.filter(x => x.attention_tag === "UN_ACKED" || (x.current_assignment_id && !x.acked));
    if (filter === "waiting")      r = r.filter(x => x.current_state === "WAITING" || x.attention_tag === "WAITING_LONG");
    if (filter === "breakdown")    r = r.filter(x => x.current_state === "BREAKDOWN" || x.attention_tag === "BREAKDOWN");
    if (filter === "no_assn")      r = r.filter(x => !x.current_assignment_id);
    if (filter === "missing_dvir") r = r.filter(x => !x.last_dvir_at);
    if (q) {
      r = r.filter((x) => {
        const hay = [
          x.driver_name, x.truck_id, x.trailer_id, x.current_project_number,
          x.material, x.company,
        ].filter(Boolean).join(" ").toLowerCase();
        return hay.includes(q);
      });
    }
    return r;
  }, [rows, search, filter]);

  return (
    <BoardShell
      testId="driver-board"
      title="Drivers"
      subtitle={data?.as_of ? `as of ${fmtAgo(data.as_of)} ago` : ""}
      count={filtered.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && !error && rows.length === 0}
      emptyText="No drivers are currently shifted."
      toolbar={
        <>
          <SearchBar
            value={search} onChange={setSearch}
            placeholder="Search driver, truck, job, trailer…"
            testId="driver-search"
          />
          <FilterChips
            options={filterOptions} value={filter} onChange={setFilter}
            testIdRoot="driver"
          />
        </>
      }
    >
      <div className="overflow-x-auto -mx-3 sm:-mx-4">
        <div className="min-w-[820px] max-h-[70vh] overflow-y-auto" data-testid="driver-board-list">
          <table className="w-full text-xs sm:text-sm">
            <thead className="sticky top-0 bg-slate-50 z-10 border-b border-slate-200">
              <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-slate-600">
                <th className="px-3 py-2">Driver</th>
                <th className="px-2 py-2">SOS</th>
                <th className="px-2 py-2">Truck</th>
                <th className="px-2 py-2">Trailer</th>
                <th className="px-2 py-2">Job</th>
                <th className="px-2 py-2">State</th>
                <th className="px-2 py-2">DVIR</th>
                <th className="px-2 py-2">Comms</th>
                <th className="px-2 py-2">Last Activity</th>
                <th className="px-2 py-2">Attention</th>
                <th className="px-2 py-2">Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.session_id}
                  data-testid={`driver-row-${r.session_id}`}
                  className="border-b border-slate-100 hover:bg-slate-50"
                >
                  <td className="px-3 py-2 font-bold text-slate-900">
                    {r.driver_name || "—"}
                    {r.source === "assignment_only" ? (
                      <div className="text-[10px] font-mono uppercase tracking-widest text-amber-700">assignment_only · needs_session</div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2">
                    {r.shift_started_at ? (
                      <StatusChip tone="info">SHIFTED · {fmtAgo(r.shift_started_at)}</StatusChip>
                    ) : r.source === "assignment_only" ? (
                      <StatusChip tone="waiting">NO SESSION</StatusChip>
                    ) : (
                      <StatusChip tone="attention">MISSING</StatusChip>
                    )}
                  </td>
                  <td className="px-2 py-2 text-slate-700">{r.truck_id || "—"}</td>
                  <td className="px-2 py-2 text-slate-700">{r.trailer_id || "—"}</td>
                  <td className="px-2 py-2 text-slate-700">{r.current_project_number || "—"}</td>
                  <td className="px-2 py-2">
                    {r.current_state ? (
                      <StatusChip tone={
                        r.current_state === "BREAKDOWN" ? "breakdown" :
                        r.current_state === "WAITING" ? "waiting" : "info"
                      }>{r.current_state}</StatusChip>
                    ) : (
                      <span className="text-slate-400 text-[10px] uppercase">no assn</span>
                    )}
                    {r.current_state_since_min != null ? (
                      <div className="text-[10px] text-slate-500 mt-0.5">{r.current_state_since_min}m</div>
                    ) : null}
                  </td>
                  <td className="px-2 py-2">
                    {r.last_dvir_at ? (
                      <StatusChip tone={r.last_dvir_pass ? "pass" : "fail"}>
                        {r.last_dvir_pass ? "PASS" : "FAIL"}
                      </StatusChip>
                    ) : (
                      <StatusChip tone="attention">MISSING</StatusChip>
                    )}
                  </td>
                  <td className="px-2 py-2 text-slate-700 text-[10px] uppercase tracking-wider">
                    {r.communication_status?.last_sms_status || "—"}
                  </td>
                  <td className="px-2 py-2 text-slate-700">{fmtAgo(r.shift_started_at)}</td>
                  <td className="px-2 py-2">
                    {r.attention_tag ? (
                      <StatusChip tone={
                        r.attention_tag === "BREAKDOWN" ? "breakdown" :
                        r.attention_tag === "UN_ACKED" ? "attention" : "waiting"
                      }>{r.attention_tag.replace("_", " ")}</StatusChip>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                  <td className="px-2 py-2">
                    {r.driver_id || r.source === "assignment_only" ? (
                      <button
                        type="button"
                        data-testid={`driver-row-${r.session_id || r.current_assignment_id}-contact`}
                        onClick={() => publishCommandAction({
                          kind: "contact_driver",
                          audience: r.driver_id ? `drivers:${r.driver_id}` :
                                    r.current_project_number && r.current_project_number !== "no_job"
                                      ? `project:${r.current_project_number}` : "all_active",
                          driver_name: r.driver_name,
                          // Track 14.0-UXS-11F · SMS greetings are
                          // personal — pass through preferred /
                          // first / legal so the receiver hears the
                          // name they actually use.
                          preferred_name: r.preferred_name,
                          legal_first_name: r.legal_first_name,
                          legal_last_name: r.legal_last_name,
                          truck_id: r.truck_id,
                          project_number: r.current_project_number,
                          suggested_message: (() => {
                            // Greeting style: preferred → first → legacy
                            const greet = (r.preferred_name || r.legal_first_name || r.driver_name || "").trim() || r.driver_name;
                            return r.attention_tag === "BREAKDOWN"
                              ? `Hi ${greet}, dispatch is reaching out about a breakdown on truck ${r.truck_id}. Please call dispatch.`
                              : r.source === "assignment_only"
                              ? `Hi ${greet}, please start your shift in the driver app and acknowledge your dispatch.`
                              : `Hi ${greet}, please reach out to dispatch.`;
                          })(),
                        })}
                        className="font-mono text-[10px] uppercase tracking-widest text-sky-700 hover:text-sky-900 underline"
                      >Contact →</button>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-3 py-8 text-center text-slate-500 text-sm">
                    No matching drivers.
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
