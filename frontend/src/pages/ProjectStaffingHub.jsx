// src/pages/ProjectStaffingHub.jsx
// Track 14.0-PM-STAFFING-UI-DISCOVERABILITY-CLOSURE
//
// Cross-project staffing overview. Reachable from:
//   • /admin/project-staffing  (admin scope — every project)
//   • /pm/project-staffing     (PM scope — PM's projects only)
//
// Purpose: answer the "who is assigned where, who is overloaded,
// who is unassigned" question at a single glance. Each project row
// links to the per-project Team page for full Add / Edit / Remove.

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Users, AlertTriangle, ArrowRight, Search, ShieldAlert, ChevronDown, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { buildWave3AdminHeaders } from "@/lib/wave3AdminHeaders";

const PRIMARY_KEYS = [
  "pm", "superintendent", "foreman",
  "project_engineer", "safety_rep", "qaqc_rep",
];

const PRIMARY_LABELS = {
  pm: "PM",
  superintendent: "Super",
  foreman: "Foreman",
  project_engineer: "PE",
  safety_rep: "Safety",
  qaqc_rep: "QA/QC",
};

export default function ProjectStaffingHub({ scope = "admin" }) {
  const [data, setData] = useState({
    loaded: false,
    items: [],
    totals: null,
    role_totals: null,
    overloaded: [],
    overload_threshold: 5,
  });
  const [q, setQ] = useState("");
  const [err, setErr] = useState(null);
  // TRACK 14.0-OVERLOADED-CREW-VISIBILITY — expand state per overloaded
  // person so leadership can drill into the projects creating the load.
  const [expandedKey, setExpandedKey] = useState(null);

  useEffect(() => {
    let cancelled = false;
    Promise.resolve().then(() => {
      if (cancelled) return;
      setData((d) => ({ ...d, loaded: false }));
      setErr(null);
    });
    api.get(
      "/project-staffing/summary?limit=300",
      scope === "admin" ? { headers: buildWave3AdminHeaders() } : undefined,
    )
      .then((response) => {
        const body = response.data || {};
        if (cancelled) return;
        setData({
          loaded: true,
          items: body.items || [],
          totals: body.totals || null,
          role_totals: body.role_totals || null,
          overloaded: body.overloaded || [],
          overload_threshold: body.overload_threshold || 5,
        });
      })
      .catch((e) => { if (!cancelled) { setErr(e?.response?.data?.detail || e.message); setData((d) => ({ ...d, loaded: true })); } });
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    if (!q) return data.items;
    const s = q.toLowerCase();
    return data.items.filter((it) =>
      String(it.project_number || "").toLowerCase().includes(s) ||
      String(it.name || "").toLowerCase().includes(s) ||
      Object.values(it.primary_snapshot || {}).some((p) =>
        String(p.display_name || "").toLowerCase().includes(s) ||
        String(p.email || "").toLowerCase().includes(s)
      )
    );
  }, [data.items, q]);

  const teamLinkBase = scope === "admin" ? "/admin/jobs" : "/pm/job";

  return (
    <div data-testid="project-staffing-hub" className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4">
      <header className="space-y-1">
        <h1 className="font-display font-black text-2xl sm:text-3xl tracking-tight flex items-center gap-2 field-glance-anchor">
          <Users className="w-6 h-6 text-amber-600" />
          Project Staffing
        </h1>
        <p className="text-sm text-slate-600 max-w-3xl">
          {scope === "admin"
            ? "Cross-project staffing across the company. See who is assigned where, who is overloaded, and where roles are unassigned. Click a project to open its full Team page."
            : "Your projects — staffing snapshot. Add or remove team members on any project you manage. Project Manager, Co-PM, and Executive Oversight are admin-managed."}
        </p>
      </header>

      {data.totals && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3" data-testid="staffing-totals">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase text-slate-500">Projects</p>
              <p className="text-2xl font-bold">{data.totals.projects}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase text-slate-500">Active Assignments</p>
              <p className="text-2xl font-bold">{data.totals.active_assignments}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase text-slate-500">Unassigned Role Slots</p>
              <p className="text-2xl font-bold text-amber-700">{data.totals.unassigned_role_slots}</p>
            </CardContent>
          </Card>
          <Card data-testid="overload-summary-card">
            <CardContent className="p-4">
              <p className="text-xs uppercase text-slate-500 flex items-center gap-1">
                <ShieldAlert className="w-3 h-3" />
                Overloaded Crew
              </p>
              <p
                className={
                  "text-2xl font-bold " +
                  ((data.overloaded?.length || 0) > 0 ? "text-rose-700" : "text-emerald-700")
                }
                data-testid="overload-count"
              >
                {data.overloaded?.length || 0}
              </p>
              <p className="text-[10px] text-slate-500 uppercase tracking-wide">
                ≥ {data.overload_threshold} active projects
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TRACK 14.0-OVERLOADED-CREW-VISIBILITY · Phase 3-6 — above-fold,
          always-visible (when data is loaded) overload section. Empty
          state explicitly confirms "no overload" so leadership trusts
          the silence. */}
      {data.loaded && !err && (
        <Card
          data-testid="overloaded-crew-section"
          className={
            (data.overloaded?.length || 0) > 0
              ? "border-rose-300 bg-rose-50/40"
              : "border-emerald-200 bg-emerald-50/30"
          }
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <ShieldAlert
                className={
                  "w-4 h-4 " +
                  ((data.overloaded?.length || 0) > 0 ? "text-rose-700" : "text-emerald-700")
                }
              />
              Overloaded Crew
              <Badge
                variant="outline"
                className={
                  "text-[10px] " +
                  ((data.overloaded?.length || 0) > 0
                    ? "border-rose-400 text-rose-800 bg-rose-100"
                    : "border-emerald-400 text-emerald-800 bg-emerald-100")
                }
                data-testid="overload-threshold-chip"
              >
                Threshold: {data.overload_threshold}+ active projects
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-2">
            {(data.overloaded?.length || 0) === 0 ? (
              <p
                className="text-sm text-emerald-800 font-medium"
                data-testid="overload-empty-state"
              >
                No crew currently overloaded in {scope === "admin" ? "the company" : "your scope"}.
              </p>
            ) : (
              <div className="space-y-2" data-testid="overload-list">
                <p className="text-xs text-rose-900/80 mb-1">
                  These team members are assigned to {data.overload_threshold} or more active
                  projects. Open a row to see exactly which projects create the load.
                </p>
                <ul className="divide-y divide-rose-100/80 rounded border border-rose-200 bg-white overflow-hidden">
                  {data.overloaded.map((p) => {
                    const key = p.email || p.user_id || p.display_name;
                    const isOpen = expandedKey === key;
                    return (
                      <li
                        key={key}
                        data-testid={`overload-row-${(p.email || p.user_id || p.display_name || "row").replace(/[^a-zA-Z0-9._-]/g, "-")}`}
                      >
                        <button
                          type="button"
                          onClick={() => setExpandedKey(isOpen ? null : key)}
                          className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-rose-50 focus:bg-rose-50 focus:outline-none"
                          aria-expanded={isOpen}
                          data-testid={`overload-toggle-${(p.email || p.user_id || p.display_name || "row").replace(/[^a-zA-Z0-9._-]/g, "-")}`}
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            {isOpen
                              ? <ChevronDown className="w-3.5 h-3.5 text-rose-700 shrink-0" />
                              : <ChevronRight className="w-3.5 h-3.5 text-rose-700 shrink-0" />
                            }
                            <span className="font-semibold text-sm text-slate-900 truncate">
                              {p.display_name || p.email || "—"}
                            </span>
                            {p.email && p.email !== p.display_name && (
                              <span className="text-xs text-slate-500 truncate hidden sm:inline">
                                · {p.email}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <Badge
                              className="bg-rose-600 hover:bg-rose-600 text-white text-[11px]"
                              data-testid={`overload-count-${(p.email || p.user_id || p.display_name || "row").replace(/[^a-zA-Z0-9._-]/g, "-")}`}
                            >
                              <AlertTriangle className="w-3 h-3 mr-1 inline" />
                              {p.active_project_count} active projects
                            </Badge>
                          </div>
                        </button>
                        {isOpen && (
                          <div className="px-3 pb-3 pt-1 border-t border-rose-100 bg-rose-50/30">
                            <p className="text-[11px] uppercase tracking-wide text-rose-900/70 mb-1">
                              Projects creating the load
                            </p>
                            <ul className="space-y-1">
                              {p.projects.map((proj) => (
                                <li
                                  key={proj.project_number}
                                  className="flex items-center justify-between gap-2 text-sm"
                                >
                                  <div className="min-w-0 flex-1">
                                    <Link
                                      to={`${teamLinkBase}/${encodeURIComponent(proj.project_number)}/team`}
                                      className="font-mono font-semibold text-slate-900 hover:text-rose-800 hover:underline"
                                      data-testid={`overload-project-link-${proj.project_number}`}
                                    >
                                      {proj.project_number}
                                    </Link>
                                    {proj.name && (
                                      <span className="text-xs text-slate-500 ml-2 truncate">
                                        {proj.name}
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex flex-wrap gap-1 justify-end">
                                    {(proj.roles || []).map((r, idx) => (
                                      <Badge
                                        key={`${proj.project_number}-${r.assignment_role}-${idx}`}
                                        variant="outline"
                                        className={
                                          "text-[10px] " +
                                          (r.is_primary
                                            ? "border-amber-500 text-amber-800 bg-amber-50"
                                            : "border-slate-300 text-slate-700 bg-white")
                                        }
                                      >
                                        {r.is_primary && <span className="mr-1">★</span>}
                                        {r.role_label || r.assignment_role}
                                      </Badge>
                                    ))}
                                  </div>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center justify-between">
            <span>Projects ({filtered.length})</span>
            <div className="relative w-72">
              <Search className="w-3.5 h-3.5 absolute left-2 top-2.5 text-slate-400" />
              <Input
                placeholder="Search project # / name / member"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className="pl-7 h-9 text-sm"
                data-testid="staffing-search"
              />
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!data.loaded && <p className="text-sm text-slate-500">Loading…</p>}
          {err && (
            <p className="text-sm text-red-700 bg-red-50 p-2 rounded">
              Failed to load staffing summary: {err}
            </p>
          )}
          {data.loaded && !err && filtered.length === 0 && (
            <p className="text-sm text-slate-500 italic">
              No projects {q ? "match the current search." : "in your scope yet."}
            </p>
          )}
          {data.loaded && filtered.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="staffing-projects-table">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-3 py-2 font-medium">Project</th>
                    <th className="text-left px-3 py-2 font-medium">Active</th>
                    <th className="text-left px-3 py-2 font-medium">Key roles filled</th>
                    <th className="text-left px-3 py-2 font-medium">Gaps</th>
                    <th className="text-right px-3 py-2 font-medium">Manage</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((it) => {
                    const snap = it.primary_snapshot || {};
                    const filled = PRIMARY_KEYS.filter((k) => snap[k]);
                    const missingKey = PRIMARY_KEYS.filter((k) => !snap[k]);
                    return (
                      <tr
                        key={it.project_number}
                        className="border-b border-slate-100 hover:bg-amber-50/40"
                        data-testid={`staffing-row-${it.project_number}`}
                      >
                        <td className="px-3 py-2">
                          <p className="font-mono font-bold text-slate-900">
                            {it.project_number}
                          </p>
                          <p className="text-xs text-slate-500">{it.name || ""}</p>
                        </td>
                        <td className="px-3 py-2">
                          <Badge variant="outline" className="text-xs">
                            {it.active_assignments} member{it.active_assignments === 1 ? "" : "s"}
                          </Badge>
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex flex-wrap gap-1">
                            {filled.length === 0 && (
                              <span className="text-xs text-slate-400 italic">none yet</span>
                            )}
                            {filled.map((k) => (
                              <Badge
                                key={k}
                                variant="secondary"
                                className="text-[10px]"
                                title={snap[k].email || snap[k].display_name}
                              >
                                {PRIMARY_LABELS[k]}: {snap[k].display_name}
                              </Badge>
                            ))}
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          {missingKey.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                              {missingKey.map((k) => (
                                <Badge
                                  key={k}
                                  className="bg-amber-100 text-amber-800 text-[10px]"
                                  data-testid={`staffing-gap-${it.project_number}-${k}`}
                                >
                                  <AlertTriangle className="w-2.5 h-2.5 mr-0.5 inline" />
                                  {PRIMARY_LABELS[k]}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-xs text-emerald-700 font-medium">All core roles filled</span>
                          )}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Link
                            to={`${teamLinkBase}/${encodeURIComponent(it.project_number)}/team`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium"
                            data-testid={`staffing-manage-${it.project_number}`}
                          >
                            Manage team
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {data.role_totals && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Role coverage across {data.totals?.projects || 0} project{data.totals?.projects === 1 ? "" : "s"}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2" data-testid="role-coverage-grid">
              {Object.entries(data.role_totals).map(([key, n]) => (
                <div
                  key={key}
                  className="flex items-center justify-between px-3 py-2 border border-slate-200 rounded text-xs"
                  data-testid={`role-total-${key}`}
                >
                  <span className="text-slate-600">{key}</span>
                  <span className={`font-mono font-bold ${n === 0 ? "text-amber-700" : "text-slate-900"}`}>
                    {n}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
