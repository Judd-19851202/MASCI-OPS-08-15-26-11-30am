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
import { Users, AlertTriangle, ArrowRight, Search } from "lucide-react";
import { getAdminToken } from "@/lib/adminAuth";
import { getPmToken } from "@/lib/pmAuth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

const API = process.env.REACT_APP_BACKEND_URL;

function authHeaders() {
  const h = { "Content-Type": "application/json" };
  const a = getAdminToken();
  const p = getPmToken();
  if (a) h["X-Admin-Token"] = a;
  if (p) h["X-PM-Token"] = p;
  return h;
}

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
  const [data, setData] = useState({ loaded: false, items: [], totals: null, role_totals: null });
  const [q, setQ] = useState("");
  const [err, setErr] = useState(null);

  useEffect(() => {
    let cancelled = false;
    Promise.resolve().then(() => {
      if (cancelled) return;
      setData((d) => ({ ...d, loaded: false }));
      setErr(null);
    });
    fetch(`${API}/api/project-staffing/summary?limit=300`, { headers: authHeaders() })
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((body) => {
        if (cancelled) return;
        setData({
          loaded: true,
          items: body.items || [],
          totals: body.totals || null,
          role_totals: body.role_totals || null,
        });
      })
      .catch((e) => { if (!cancelled) { setErr(e.message); setData((d) => ({ ...d, loaded: true })); } });
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
          <Card>
            <CardContent className="p-4">
              <p className="text-xs uppercase text-slate-500">Avg per project</p>
              <p className="text-2xl font-bold">
                {data.totals.projects
                  ? (data.totals.active_assignments / data.totals.projects).toFixed(1)
                  : "0.0"}
              </p>
            </CardContent>
          </Card>
        </div>
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
