/**
 * ShopFeedBoard.jsx · Cross-portal Shop Feed.
 * Reads /api/shop/command-feed. Surfaces failed DVIRs, weekly-lead,
 * safety-equipment, maintenance holds, OOS assets, with project impact.
 *
 * Polls every 60s.
 */
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { commandApi } from "./commandApi";
import {
  BoardShell, StatusChip, SearchBar, FilterChips,
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

export default function ShopFeedBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    try {
      setRefreshing(true);
      const d = await commandApi.shopFeed(200);
      setData(d); setError(null);
    } catch (e) { setError(e.message || String(e)); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  const items = data?.needs_attention || [];
  const recovery = data?.active_recovery || [];
  const waitingParts = data?.waiting_on_parts || [];
  const counts = data?.counts || {};

  const filterOptions = useMemo(() => [
    { value: "all",      label: "All",        count: counts.needs_attention },
    { value: "dvir",     label: "DVIR",       count: counts.dvir_fails },
    { value: "lead",     label: "Wk Lead",    count: counts.weekly_lead_fails },
    { value: "safety",   label: "Safety Eq",  count: counts.safety_equipment_fails },
  ], [counts]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    let r = items;
    if (filter === "dvir")    r = r.filter(x => x.kind === "DVIR_FAIL");
    if (filter === "lead")    r = r.filter(x => x.kind === "WEEKLY_LEAD_FAIL");
    if (filter === "safety")  r = r.filter(x => x.kind === "SAFETY_EQUIPMENT_FAIL");
    if (q) {
      r = r.filter(x => {
        const hay = [
          x.unit_number, x.driver_name, x.item_text, x.category, x.severity,
          ...(x.project_impact || []),
        ].filter(Boolean).join(" ").toLowerCase();
        return hay.includes(q);
      });
    }
    return r;
  }, [items, search, filter]);

  return (
    <BoardShell
      testId="shop-feed"
      title="Shop Feed"
      subtitle={data?.generated_at ? `as of ${fmtAgo(data.generated_at)} ago` : ""}
      count={filtered.length}
      onRefresh={load}
      refreshing={refreshing}
      loading={loading}
      error={error}
      empty={!loading && !error && items.length === 0 && recovery.length === 0 && waitingParts.length === 0}
      emptyText="Nothing requires shop attention. Everything is moving."
      toolbar={
        <>
          <SearchBar
            value={search} onChange={setSearch}
            placeholder="Search unit, item, driver, project…"
            testId="shop-search"
          />
          <FilterChips
            options={filterOptions} value={filter} onChange={setFilter}
            testIdRoot="shop"
          />
          <div className="ml-auto flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-slate-500" data-testid="shop-summary-counts">
            <span>OOS <b className="text-slate-900">{counts.oos_units || 0}</b></span>
            <span>Recovery <b className="text-slate-900">{counts.active_recovery || 0}</b></span>
            <span>Wait Parts <b className="text-slate-900">{counts.waiting_on_parts || 0}</b></span>
            <span>Today RTS <b className="text-slate-900">{counts.returned_today || 0}</b></span>
          </div>
        </>
      }
    >
      <div className="space-y-3">
        <div className="overflow-x-auto -mx-3 sm:-mx-4">
          <div className="min-w-[860px] max-h-[55vh] overflow-y-auto" data-testid="shop-feed-list">
            <table className="w-full text-xs sm:text-sm">
              <thead className="sticky top-0 bg-slate-50 z-10 border-b border-slate-200">
                <tr className="text-left font-mono text-[10px] uppercase tracking-widest text-slate-600">
                  <th className="px-3 py-2">Kind</th>
                  <th className="px-2 py-2">Unit</th>
                  <th className="px-2 py-2">Severity</th>
                  <th className="px-2 py-2">Item</th>
                  <th className="px-2 py-2">Driver</th>
                  <th className="px-2 py-2">Reported</th>
                  <th className="px-2 py-2">Project Impact</th>
                  <th className="px-2 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((it) => (
                  <tr
                    key={it.defect_id}
                    data-testid={`shop-row-${it.defect_id}`}
                    className="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="px-3 py-2">
                      <StatusChip tone={
                        it.kind === "SAFETY_EQUIPMENT_FAIL" ? "breakdown" :
                        it.kind === "WEEKLY_LEAD_FAIL" ? "attention" : "waiting"
                      }>
                        {it.kind.replace("_FAIL", "").replace("_", " ")}
                      </StatusChip>
                    </td>
                    <td className="px-2 py-2 font-bold text-slate-900">
                      {it.unit_number || "—"}
                      {it.is_trailer ? (
                        <span className="ml-1 text-[10px] text-slate-500 uppercase">trailer</span>
                      ) : null}
                    </td>
                    <td className="px-2 py-2 text-slate-700 uppercase text-[10px] tracking-widest">{it.severity || "—"}</td>
                    <td className="px-2 py-2 text-slate-700 truncate max-w-[260px]">{it.item_text || it.category || "—"}</td>
                    <td className="px-2 py-2 text-slate-700">{it.driver_name || "—"}</td>
                    <td className="px-2 py-2 text-slate-700">{fmtAgo(it.reported_at)}</td>
                    <td className="px-2 py-2 text-slate-700">
                      {(it.project_impact || []).length === 0 ? (
                        <span className="text-slate-300">—</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {(it.project_impact || []).slice(0, 4).map((p) => (
                            <span
                              key={p}
                              className="text-[10px] font-mono bg-slate-100 border border-slate-200 rounded px-1.5 py-0.5"
                            >{p}</span>
                          ))}
                        </div>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      <StatusChip tone={it.status === "open" ? "attention" : "waiting"}>
                        {it.status}
                      </StatusChip>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-3 py-6 text-center text-slate-500 text-sm">
                      Nothing matches the current filter.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>

        {recovery.length > 0 ? (
          <details className="bg-slate-50 border border-slate-200 rounded p-2" data-testid="shop-recovery-panel">
            <summary className="text-xs font-bold uppercase tracking-widest text-slate-700 cursor-pointer">
              Active recovery · {recovery.length}
            </summary>
            <div className="mt-2 text-xs text-slate-700 space-y-1">
              {recovery.map((r) => (
                <div key={r.assignment_id} className="flex flex-wrap gap-2">
                  <span className="font-bold">{r.unit_number}</span>
                  <span>·</span><span>{r.breakdown_recovery}</span>
                  <span>·</span><span>{r.driver_name || "—"}</span>
                  <span>·</span><span>{r.project_number || "—"}</span>
                  <span>·</span><span className="font-mono text-[10px]">{fmtAgo(r.since_at)}</span>
                </div>
              ))}
            </div>
          </details>
        ) : null}

        {waitingParts.length > 0 ? (
          <details className="bg-slate-50 border border-slate-200 rounded p-2" data-testid="shop-waiting-parts">
            <summary className="text-xs font-bold uppercase tracking-widest text-slate-700 cursor-pointer">
              Waiting on parts · {waitingParts.length}
            </summary>
            <div className="mt-2 text-xs text-slate-700 space-y-1">
              {waitingParts.map((r) => (
                <div key={r.assignment_id} className="flex flex-wrap gap-2">
                  <span className="font-bold">{r.unit_number}</span>
                  <span>·</span><span>{r.driver_name || "—"}</span>
                  <span>·</span><span>{r.project_number || "—"}</span>
                  <span>·</span><span className="font-mono text-[10px]">{fmtAgo(r.since_at)}</span>
                </div>
              ))}
            </div>
          </details>
        ) : null}

        <div data-testid="shop-integration-status" className="text-[11px] font-mono uppercase tracking-widest text-slate-500">
          MaintainX · {data?.integration_readiness?.maintainx === "not_connected" ? "Pending Integration" : "Live"}
        </div>
      </div>
    </BoardShell>
  );
}
