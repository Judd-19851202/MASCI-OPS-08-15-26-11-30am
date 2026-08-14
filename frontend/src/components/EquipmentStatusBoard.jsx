import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Wrench, AlertOctagon, ChevronDown, ChevronRight, Clock, CheckCircle2, Siren } from "lucide-react";
import { api } from "@/lib/api";
import { buildWave3AdminHeaders } from "@/lib/wave3AdminHeaders";

const formatDaysAgo = (n) => {
  if (n === null || n === undefined) return "Never";
  if (n === 0) return "Today";
  if (n === 1) return "Yesterday";
  return `${n} days ago`;
};

// TRACK 19.16 · Closeout · Fleet cross-link pill.
// Reference-only: shows case number, type, and date + link to the
// Safety Case Workspace. Never shows narrative, medical, or CAPA.
function RecentIncidentPill({ items, unitKey }) {
  if (!items || !items.length) return null;
  const top = items[0];
  const date = top.occurred_at_date || (top.submitted_at || "").slice(0, 10);
  const label = String(top.incident_type || "incident").replace(/_/g, " ");
  return (
    <Link
      to={`/safety/cases/${encodeURIComponent(top.case_id)}`}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-50 text-red-800 border border-red-300 text-xs font-mono uppercase tracking-[0.14em] hover:bg-red-100"
      data-testid={`fleet-recent-incident-${unitKey}`}
      title={`${top.case_number || top.case_id} · ${label} · ${date}`}
    >
      <Siren className="w-3 h-3" />
      Recent incident · {top.case_number || "case"} · {date}
      {items.length > 1 ? ` +${items.length - 1}` : ""}
    </Link>
  );
}

const StatusBadge = ({ status, daysAgo }) => {
  if (status === "fail") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-red-700 text-white">
        <AlertOctagon className="w-3 h-3" /> Out of Service
      </span>
    );
  }
  if (status === "never") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-amber-100 text-amber-800 border border-amber-300">
        Never inspected
      </span>
    );
  }
  // ok
  if (daysAgo !== null && daysAgo >= 7) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-amber-100 text-amber-800 border border-amber-300">
        <Clock className="w-3 h-3" /> Overdue ({daysAgo}d)
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold bg-emerald-50 text-emerald-700 border border-emerald-300">
      <CheckCircle2 className="w-3 h-3" /> OK
    </span>
  );
};

export default function EquipmentStatusBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState("all"); // all | fail | overdue
  // TRACK 19.16 · Closeout · unit_number → [incident summary rows].
  const [incidentMap, setIncidentMap] = useState({});
  const adminHeaders = typeof window !== "undefined" && window.location.pathname.startsWith("/admin/")
    ? { headers: buildWave3AdminHeaders() }
    : {};

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const r = await api.get("/equipment-status-board", adminHeaders);
        if (alive) setData(r.data);
      } catch {
        /* silently fail — admin sees the standard load state */
      } finally {
        if (alive) setLoading(false);
      }
      // Read-only cross-link. Silent-fail so the Board still renders
      // even if the engine endpoint is temporarily unreachable.
      try {
        const r = await api.get("/equipment-status-board/incidents-by-unit", adminHeaders);
        if (alive && r?.data?.by_unit) setIncidentMap(r.data.by_unit);
      } catch {
        /* ignore */
      }
    })();
    return () => { alive = false; };
  }, []);

  if (loading) return null;
  if (!data || !data.units || data.units.length === 0) {
    return (
      <section
        className="bg-white border border-slate-200 rounded-md p-5 sm:p-6 mb-8"
        data-testid="equipment-status-board"
      >
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white">
            <Wrench className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900">
              Equipment Status Board
            </h2>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5">
              No equipment units logged yet
            </p>
          </div>
        </div>
        <p className="text-sm text-slate-600 mt-4">
          File your first Equipment Pre-Op Inspection at{" "}
          <span className="font-mono text-red-700">/equipment/new</span> to start tracking units.
        </p>
      </section>
    );
  }

  const { units, summary } = data;
  // GOVERNED single derivation for "overdue / never" — a unit is overdue if it
  // was never inspected OR last inspected >= 7 days ago. Counting distinct units
  // (never-inspected units carry days_ago=null) guarantees the bucket can never
  // exceed total_units, and keeps the header chip and the filter label identical.
  const isOverdue = (u) =>
    u.last_status === "never" ||
    (u.last_inspected_days_ago !== null && u.last_inspected_days_ago >= 7);
  const overdueCount = units.filter(isOverdue).length;
  const filtered = units.filter((u) => {
    if (filter === "fail") return u.last_status === "fail";
    if (filter === "overdue") return isOverdue(u);
    return true;
  });

  return (
    <section
      className="bg-white border border-slate-200 rounded-md p-5 sm:p-6 mb-8"
      data-testid="equipment-status-board"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start justify-between gap-3 flex-wrap text-left"
        data-testid="status-board-toggle"
      >
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-md bg-slate-900 text-white">
            <Wrench className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-display text-lg sm:text-xl font-black tracking-tight text-slate-900 flex items-center gap-2">
              Equipment Status Board
              {open ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
            </h2>
            <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 mt-0.5" data-testid="equipment-status-board-count-label">
              {summary.total_units} inspection unit{summary.total_units === 1 ? "" : "s"} tracked
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5" data-testid="equipment-status-board-scope-note">
              Inspection / status units — distinct from the Equipment Master (all assets).
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {summary.out_of_service > 0 && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-red-50 text-red-700 border border-red-300 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
              <AlertOctagon className="w-3 h-3" /> {summary.out_of_service} Out of Service
            </span>
          )}
          {overdueCount > 0 && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-300 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
              <Clock className="w-3 h-3" /> {overdueCount} Overdue
            </span>
          )}
          {summary.out_of_service === 0 && overdueCount === 0 && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-300 font-mono text-[10px] uppercase tracking-[0.15em] font-bold">
              <CheckCircle2 className="w-3 h-3" /> All Clear
            </span>
          )}
        </div>
      </button>

      {open && (
        <>
          <div className="mt-5 flex items-center gap-2 flex-wrap">
            {[
              { key: "all", label: `All (${units.length})` },
              { key: "fail", label: `Out of Service (${summary.out_of_service})` },
              { key: "overdue", label: `Overdue / Never (${overdueCount})` },
            ].map((f) => (
              <button
                key={f.key}
                type="button"
                onClick={() => setFilter(f.key)}
                className={`px-3 py-1.5 rounded font-mono text-[10px] uppercase tracking-[0.15em] font-bold border-2 transition-colors ${
                  filter === f.key
                    ? "bg-slate-900 text-white border-slate-900"
                    : "bg-white text-slate-600 border-slate-300 hover:border-slate-500"
                }`}
                data-testid={`status-filter-${f.key}`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {filtered.length === 0 ? (
            <p className="mt-5 text-sm text-slate-500 italic" data-testid="status-empty-filter">
              Nothing matches this filter — that&apos;s a good thing.
            </p>
          ) : (
            <ul className="mt-4 divide-y-2 divide-slate-100" data-testid="status-board-list">
              {filtered.map((u, idx) => (
                <li
                  key={u.equipment_type + "::" + u.equipment_unit + "::" + idx}
                  className={`py-3 flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-4 ${
                    u.last_status === "fail" ? "border-l-4 border-red-700 pl-3 -ml-3" : ""
                  }`}
                  data-testid={`status-row-${idx}`}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-display text-base font-bold text-slate-900 truncate">
                        {u.equipment_type} · {u.equipment_unit}
                      </span>
                      <StatusBadge status={u.last_status} daysAgo={u.last_inspected_days_ago} />
                      <RecentIncidentPill
                        items={incidentMap[String(u.equipment_unit)]}
                        unitKey={String(u.equipment_unit)}
                      />
                    </div>
                    <div className="mt-1 text-sm text-slate-600">
                      {u.last_status === "never" ? (
                        <span className="italic">No inspections logged yet.</span>
                      ) : (
                        <>
                          Last inspected <b>{formatDaysAgo(u.last_inspected_days_ago)}</b>
                          {u.last_project ? <> · {u.last_project}{u.last_project_number ? ` (#${u.last_project_number})` : ""}</> : null}
                          {" · "}{u.inspection_count} total
                        </>
                      )}
                    </div>
                    {u.top_failures && u.top_failures.length > 0 && (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <span className="font-mono text-[10px] uppercase tracking-[0.15em] text-red-700 font-bold">
                          Repeat fails (30d)
                        </span>
                        {u.top_failures.map((f, fi) => (
                          <span
                            key={fi}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-50 text-red-800 border border-red-200 text-xs"
                            data-testid={`top-fail-${idx}-${fi}`}
                          >
                            {f.item} <b className="font-mono">×{f.count}</b>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  {u.fail_count_14d > 0 && (
                    <div className="text-right sm:min-w-[120px]">
                      <div className="font-display text-2xl font-black text-red-700 leading-none">
                        {u.fail_count_14d}
                      </div>
                      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-slate-500 mt-0.5">
                        Fails / 14d
                      </div>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
