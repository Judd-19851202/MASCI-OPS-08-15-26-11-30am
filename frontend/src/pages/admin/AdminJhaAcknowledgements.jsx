/**
 * OMEGA · FOCP Release 2 · TR-0001 · Admin JHP Acknowledgement Matrix
 *
 * Supervisor visibility surface. Three views in one page:
 *   1) Compliance roll-up — one row per project (files / acks / employees).
 *   2) Project drill-down — for a selected project, every file × every
 *      employee acknowledgement.
 *   3) Employee drill-down — for a selected employee, every plan they've
 *      acknowledged across all projects.
 *
 * Read-only. No mutation surface here — corrections happen at the source
 * (re-acknowledge on the /jha page).
 */
import React, { useEffect, useState, useCallback } from "react";
import AdminShell from "@/components/AdminShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { ClipboardCheck, FileText, User, Loader2, RefreshCw } from "lucide-react";
import { formatEmployeeIdentity } from "@/lib/identity";
import { buildWave3AdminHeaders } from "@/lib/wave3AdminHeaders";
// TRACK 27.03 · Final Completion · canonical platform time formatter.
import { formatPlatformTime, formatPlatformDate, formatPlatformTimeOnly } from "@/lib/platformTime";

export default function AdminJhaAcknowledgements() {
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  const [projectInput, setProjectInput] = useState("");
  const [projectView, setProjectView] = useState(null);
  const [projectLoading, setProjectLoading] = useState(false);

  const [employeeInput, setEmployeeInput] = useState("");
  const [employeeView, setEmployeeView] = useState(null);
  const [employeeLoading, setEmployeeLoading] = useState(false);

  const loadSummary = useCallback(async () => {
    setLoadingSummary(true);
    try {
      const r = await api.get("/jha-acknowledgements/compliance", { headers: buildWave3AdminHeaders() });
      setSummary(r.data || null);
    } catch {
      setSummary(null);
    } finally {
      setLoadingSummary(false);
    }
  }, []);

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  const loadProject = async (pn) => {
    const clean = (pn || "").trim();
    if (!clean) return;
    setProjectLoading(true);
    try {
      const r = await api.get(
        `/jha-acknowledgements/by-project/${encodeURIComponent(clean)}`,
        { headers: buildWave3AdminHeaders() },
      );
      setProjectView(r.data || null);
    } catch {
      setProjectView({ error: true });
    } finally {
      setProjectLoading(false);
    }
  };

  const loadEmployee = async (id) => {
    const clean = (id || "").trim();
    if (!clean) return;
    setEmployeeLoading(true);
    try {
      const r = await api.get(
        `/jha-acknowledgements/by-employee/${encodeURIComponent(clean)}`,
        { headers: buildWave3AdminHeaders() },
      );
      setEmployeeView(r.data || null);
    } catch {
      setEmployeeView({ error: true });
    } finally {
      setEmployeeLoading(false);
    }
  };

  return (
    <AdminShell>
      <div className="max-w-6xl mx-auto px-4 py-6 sm:py-8" data-testid="admin-jha-acks-page">
        <div className="mb-6 flex flex-wrap items-end gap-3">
          <div>
            <span className="font-mono text-xs uppercase tracking-[0.22em] text-amber-700">
              FOCP Release 2 · TR-0001
            </span>
            <h1 className="font-display text-3xl font-black tracking-tight text-slate-900 mt-1">
              JHP Acknowledgements
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Auditable record of every employee who has signed off on each Job Hazard Plan,
              per project, per file version.
            </p>
          </div>
          <Button
            variant="outline"
            onClick={loadSummary}
            className="ml-auto h-9 px-3 border-2 border-slate-300"
            data-testid="admin-jha-acks-refresh"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Refresh
          </Button>
        </div>

        {/* Compliance roll-up */}
        <section
          className="bg-white border-2 border-slate-200 rounded-md p-4 mb-6"
          data-testid="admin-jha-acks-compliance"
        >
          <div className="flex items-center gap-2 mb-3">
            <ClipboardCheck className="w-4 h-4 text-amber-700" />
            <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-slate-500">
              Cross-project compliance
            </span>
            {summary && (
              <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {summary.totals?.projects ?? 0} projects · {summary.totals?.files ?? 0} files ·{" "}
                {summary.totals?.acknowledgements ?? 0} acks
              </span>
            )}
          </div>

          {loadingSummary ? (
            <div className="py-6 text-center text-slate-500 text-sm">
              <Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading…
            </div>
          ) : !summary || (summary.projects || []).length === 0 ? (
            <div className="py-6 text-center text-slate-500 italic text-sm">
              No JHP files or acknowledgements on file yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="admin-jha-acks-compliance-table">
                <thead className="bg-slate-900 text-white font-mono text-[10px] uppercase tracking-[0.2em]">
                  <tr>
                    <th className="text-left px-3 py-2">Project</th>
                    <th className="text-right px-3 py-2">Files</th>
                    <th className="text-right px-3 py-2">Acks</th>
                    <th className="text-right px-3 py-2">Employees</th>
                    <th className="text-left px-3 py-2">Latest</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {(summary.projects || []).map((row, i) => (
                    <tr
                      key={row.project_number}
                      className={i % 2 === 0 ? "bg-white" : "bg-slate-50"}
                      data-testid={`admin-jha-acks-row-${row.project_number}`}
                    >
                      <td className="px-3 py-2 font-mono font-bold text-amber-700">
                        {row.project_number}
                      </td>
                      <td className="px-3 py-2 text-right">{row.files_uploaded}</td>
                      <td className="px-3 py-2 text-right">{row.acknowledgements}</td>
                      <td className="px-3 py-2 text-right">{row.distinct_employees}</td>
                      <td className="px-3 py-2 text-xs text-slate-600">
                        {row.latest_acknowledged_at
                          ? formatPlatformTime(row.latest_acknowledged_at)
                          : "—"}
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setProjectInput(row.project_number);
                            loadProject(row.project_number);
                          }}
                          className="h-7 px-2 text-[11px] border-2 border-slate-300"
                          data-testid={`admin-jha-acks-drill-${row.project_number}`}
                        >
                          Drill in
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Project drill */}
        <section
          className="bg-white border-2 border-slate-200 rounded-md p-4 mb-6"
          data-testid="admin-jha-acks-project-drill"
        >
          <div className="flex items-center gap-2 mb-3">
            <FileText className="w-4 h-4 text-amber-700" />
            <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-slate-500">
              Project drill-down
            </span>
          </div>
          <div className="flex flex-wrap gap-2 mb-3">
            <Input
              value={projectInput}
              onChange={(e) => setProjectInput(e.target.value)}
              placeholder="Project number (e.g. 2024-101)"
              className="h-10 max-w-xs border-2 border-slate-300"
              data-testid="admin-jha-acks-project-input"
              onKeyDown={(e) => {
                if (e.key === "Enter") loadProject(projectInput);
              }}
            />
            <Button
              onClick={() => loadProject(projectInput)}
              className="h-10 bg-slate-900 hover:bg-slate-800 text-white"
              data-testid="admin-jha-acks-project-load"
            >
              Load
            </Button>
          </div>

          {projectLoading ? (
            <div className="py-6 text-center text-slate-500 text-sm">
              <Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading…
            </div>
          ) : projectView?.error ? (
            <div className="py-6 text-center text-rose-700 italic text-sm">
              Could not load project.
            </div>
          ) : projectView ? (
            <div className="space-y-4" data-testid="admin-jha-acks-project-view">
              <div className="text-xs font-mono uppercase tracking-[0.18em] text-slate-500">
                {projectView.project_number} · {projectView.total_files} files ·{" "}
                {projectView.total_acknowledgements} acknowledgements
              </div>
              {(projectView.files || []).map((row) => (
                <div
                  key={row.file?.id}
                  className="border-2 border-slate-100 rounded-md p-3 bg-slate-50"
                >
                  <div className="font-mono text-sm font-bold text-slate-900 truncate">
                    {row.file?.filename}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Uploaded{" "}
                    {row.file?.uploaded_at
                      ? formatPlatformTime(row.file.uploaded_at)
                      : "—"}{" "}
                    · {row.ack_count} acknowledgements
                  </div>
                  {row.acknowledgements?.length > 0 ? (
                    <ul className="mt-2 divide-y divide-slate-200 bg-white border border-slate-200 rounded">
                      {row.acknowledgements.map((a) => (
                        <li
                          key={a.id}
                          className="px-3 py-2 text-xs flex flex-wrap items-center gap-2"
                        >
                          <b className="text-slate-900">{formatEmployeeIdentity(a) || a.employee_name}</b>
                          <span className="text-slate-500">{a.employee_email}</span>
                          <span className="ml-auto font-mono text-[10px] text-slate-500">
                            {formatPlatformTime(a.acknowledged_at)} · {a.locale}
                          </span>
                          <span className="w-full text-[11px] italic text-slate-600 pt-1">
                            Signature: &quot;{a.signature}&quot;
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="mt-2 text-[11px] italic text-slate-500">
                      No acknowledgements yet for this file.
                    </div>
                  )}
                </div>
              ))}
              {(projectView.files || []).length === 0 && (
                <div className="py-3 text-center text-slate-500 italic text-sm">
                  No files uploaded for this project.
                </div>
              )}
            </div>
          ) : null}
        </section>

        {/* Employee drill */}
        <section
          className="bg-white border-2 border-slate-200 rounded-md p-4 mb-6"
          data-testid="admin-jha-acks-employee-drill"
        >
          <div className="flex items-center gap-2 mb-3">
            <User className="w-4 h-4 text-amber-700" />
            <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-slate-500">
              Employee drill-down
            </span>
          </div>
          <div className="flex flex-wrap gap-2 mb-3">
            <Input
              value={employeeInput}
              onChange={(e) => setEmployeeInput(e.target.value)}
              placeholder="Employee id (UUID)"
              className="h-10 max-w-md border-2 border-slate-300"
              data-testid="admin-jha-acks-employee-input"
              onKeyDown={(e) => {
                if (e.key === "Enter") loadEmployee(employeeInput);
              }}
            />
            <Button
              onClick={() => loadEmployee(employeeInput)}
              className="h-10 bg-slate-900 hover:bg-slate-800 text-white"
              data-testid="admin-jha-acks-employee-load"
            >
              Load
            </Button>
          </div>

          {employeeLoading ? (
            <div className="py-6 text-center text-slate-500 text-sm">
              <Loader2 className="w-4 h-4 inline animate-spin mr-2" /> Loading…
            </div>
          ) : employeeView?.error ? (
            <div className="py-6 text-center text-rose-700 italic text-sm">
              Could not load employee.
            </div>
          ) : employeeView?.employee ? (
            <div data-testid="admin-jha-acks-employee-view">
              <div className="text-sm">
                <b>{employeeView.employee.name}</b>
                <span className="text-slate-500 ml-2">
                  {employeeView.employee.email}
                </span>
              </div>
              <div className="text-[11px] font-mono uppercase tracking-[0.18em] text-slate-500 mt-1">
                {employeeView.count} acknowledgements
              </div>
              <ul className="mt-3 divide-y divide-slate-200 bg-slate-50 rounded border border-slate-200">
                {(employeeView.acknowledgements || []).map((a) => (
                  <li
                    key={a.id}
                    className="px-3 py-2 text-xs flex flex-wrap items-center gap-2"
                  >
                    <span className="font-mono font-bold text-amber-700">
                      {a.project_number}
                    </span>
                    <span className="text-slate-800 truncate max-w-md">{a.jha_filename}</span>
                    <span className="ml-auto font-mono text-[10px] text-slate-500">
                      {formatPlatformTime(a.acknowledged_at)}
                    </span>
                  </li>
                ))}
                {(employeeView.acknowledgements || []).length === 0 && (
                  <li className="py-3 text-center text-slate-500 italic">
                    No acknowledgements on file.
                  </li>
                )}
              </ul>
            </div>
          ) : null}
        </section>
      </div>
    </AdminShell>
  );
}
