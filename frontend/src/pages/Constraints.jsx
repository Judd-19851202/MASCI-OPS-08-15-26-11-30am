// Constraints.jsx — Phase V-Prelude · Wave 1 · Substrate.
//
// Operational Constraints — the list view. Calm, text-first, mobile-safe.
// Read OPERATIONAL_CONSTRAINT_FOUNDATION.md before touching this file.
//
// Capability-scoped per `constraintCapabilities.js`. Filters and a calm
// list. NO charts, NO gantt, NO badges-of-engagement.

import React from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { listConstraints } from "@/lib/operationalApi";
import { getConstraintCapabilities } from "@/lib/constraintCapabilities";
import { formatLocalShort } from "@/lib/dateUtils";
import SeverityPill from "@/components/operational/SeverityPill";

const DISCIPLINES = [
  "", "utilities", "access", "MOT", "survey",
  "QC", "FAA", "subcontractor", "other",
];
const STATUSES = ["", "open", "monitoring", "resolved", "void"];

function _ageLabel(days) {
  if (days <= 2) return "";
  if (days < 8) return `${days}d`;
  return `${days}d`;
}

export default function Constraints() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const caps = React.useMemo(() => getConstraintCapabilities(), []);
  const [rows, setRows] = React.useState(null);
  const [err, setErr] = React.useState("");

  const project_id = params.get("project_id") || "";
  const status = params.get("status") || "";
  const discipline = params.get("discipline") || "";

  React.useEffect(() => {
    let live = true;
    setRows(null);
    setErr("");
    listConstraints({
      ...(project_id ? { project_id } : {}),
      ...(status ? { status } : {}),
      ...(discipline ? { discipline } : {}),
    })
      .then((d) => { if (live) setRows(Array.isArray(d) ? d : []); })
      .catch((e) => { if (live) setErr(e.message || "Could not load"); });
    return () => { live = false; };
  }, [project_id, status, discipline]);

  const setParam = (k, v) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    setParams(next);
  };

  if (!caps["constraint.view"]) {
    return (
      <div className="max-w-3xl mx-auto p-6 text-slate-700">
        <h1 className="text-2xl font-semibold mb-2">Operational Constraints</h1>
        <p className="text-sm text-slate-500">
          You are signed in but your role does not include constraint
          visibility yet.
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="constraints-page"
      className="max-w-4xl mx-auto p-4 sm:p-6 text-slate-800"
    >
      <header className="mb-4 sm:mb-6 flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight">
            Operational Constraints
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-prose">
            Operational blocker memory · capture utility conflicts,
            owner holds, access restrictions, MOT, survey, QC, FAA, or
            sub delays.
          </p>
        </div>
        {caps["constraint.create"] && (
          <button
            data-testid="constraint-new-btn"
            onClick={() => navigate(
              project_id
                ? `/constraints/new?project_id=${encodeURIComponent(project_id)}`
                : `/constraints/new`,
            )}
            className="text-sm font-medium px-3 py-1.5 rounded-md bg-slate-900 text-white hover:bg-slate-800 transition-colors"
          >
            File constraint
          </button>
        )}
      </header>

      <section
        data-testid="constraints-filters"
        className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-4 mb-4"
      >
        <label className="text-xs text-slate-600">
          Project
          <input
            data-testid="filter-project"
            value={project_id}
            onChange={(e) => setParam("project_id", e.target.value.trim())}
            placeholder="project number"
            className="mt-1 block w-full text-sm border border-slate-200 rounded-md px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-slate-400"
          />
        </label>
        <label className="text-xs text-slate-600">
          Status
          <select
            data-testid="filter-status"
            value={status}
            onChange={(e) => setParam("status", e.target.value)}
            className="mt-1 block w-full text-sm border border-slate-200 rounded-md px-2 py-1.5"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s || "any"}</option>
            ))}
          </select>
        </label>
        <label className="text-xs text-slate-600">
          Discipline
          <select
            data-testid="filter-discipline"
            value={discipline}
            onChange={(e) => setParam("discipline", e.target.value)}
            className="mt-1 block w-full text-sm border border-slate-200 rounded-md px-2 py-1.5"
          >
            {DISCIPLINES.map((d) => (
              <option key={d} value={d}>{d || "any"}</option>
            ))}
          </select>
        </label>
      </section>

      {err && (
        <div
          data-testid="constraints-error"
          className="text-sm text-rose-700 mb-3"
        >
          {err}
        </div>
      )}

      {rows === null ? (
        <div data-testid="constraints-loading" className="text-sm text-slate-500">
          Loading…
        </div>
      ) : rows.length === 0 ? (
        <div data-testid="constraints-empty" className="text-sm text-slate-500 italic py-6 text-center border border-slate-200 rounded-md">
          No constraints recorded {project_id ? "for this project" : "yet"}.
        </div>
      ) : (
        <ul data-testid="constraints-list" className="divide-y divide-slate-200 border border-slate-200 rounded-md">
          {rows.map((c) => {
            const age = _ageLabel(c.age_days || 0);
            return (
              <li key={c.id} data-testid={`constraint-row-${c.id}`}>
                <Link
                  to={`/constraints/${c.id}`}
                  className="block px-3 py-2 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-baseline justify-between gap-2 flex-wrap">
                    <span className="font-medium text-slate-900 break-words">
                      {c.title || "(untitled)"}
                    </span>
                    <SeverityPill severity={c.severity} />
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5 flex items-baseline gap-2 flex-wrap">
                    <span>{c.project_id}</span>
                    <span>·</span>
                    <span>{c.discipline}</span>
                    <span>·</span>
                    <span>{c.kind}</span>
                    <span>·</span>
                    <span
                      data-testid={`constraint-row-status-${c.id}`}
                      className={
                        c.status === "open"
                          ? "text-slate-700"
                          : c.status === "monitoring"
                          ? "text-amber-700"
                          : c.status === "resolved"
                          ? "text-emerald-700"
                          : "text-slate-400"
                      }
                    >
                      {c.status}
                    </span>
                    <span>·</span>
                    <span>{formatLocalShort(c.created_at)}</span>
                    {age && (
                      <span data-testid={`constraint-age-${c.id}`} className="text-slate-600 font-medium">
                        · {age}
                      </span>
                    )}
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
