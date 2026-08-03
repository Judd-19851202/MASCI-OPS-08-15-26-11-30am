// PmJobsRead — calm, read-only PM view of jobs the signed-in PM is
// assigned to (primary or co-PM). Backed solely by /api/pm/jobs
// (non-admin namespace) so it never trips the iter180 admin boundary.
//
// iter437 P0 follow-up · 2026-02 · documented in
// /app/memory/PORTAL_AUTH_TOKEN_AUDIT.md §7 future follow-up.

import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, Loader2, RefreshCw, Search, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { operationalError } from "@/lib/errors";
import { useT } from "@/lib/i18n";
import { formatOperatorJobLabel, sanitizeOperatorProjectName, sanitizeOperatorProjectNumber, sanitizeOperatorReference } from "@/lib/operatorLanguage";

export default function PmJobsRead() {
  const { t } = useT();
  const [items, setItems] = useState([]);
  const [scope, setScope] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  const refresh = async () => {
    setLoading(true);
    try {
      const r = await api.get("/pm/jobs");
      setItems(Array.isArray(r.data?.items) ? r.data.items : []);
      setScope(r.data?.scope || null);
    } catch (e) {
      toast.error(operationalError(e, "Could not load jobs. Try again."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const filtered = useMemo(() => {
    if (!filter.trim()) return items;
    const q = filter.toLowerCase();
    return items.filter((j) =>
      [j.project_number, j.project_name, j.location, j.project_manager]
        .filter(Boolean)
        .some((s) => String(s).toLowerCase().includes(q))
    );
  }, [items, filter]);

  return (
    <div
      className="mb-8 bg-white border border-slate-200 rounded-md shadow-sm"
      data-testid="pm-jobs-read-panel"
    >
      <div className="bg-slate-900 text-white px-5 py-3 flex items-center gap-3 flex-wrap">
        <Briefcase className="w-5 h-5 text-amber-300" />
        <span className="font-mono text-xs uppercase tracking-[0.2em] text-amber-300 font-bold flex-1">
          {t("Jobs Assigned to You")}
        </span>
        <Button
          type="button"
          variant="outline"
          onClick={refresh}
          disabled={loading}
          className="h-8 px-3 border-2 border-slate-600 bg-slate-800 text-white hover:bg-slate-700 font-mono uppercase tracking-wide text-[11px]"
          data-testid="pm-jobs-read-refresh"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1" /> {t("Refresh")}
        </Button>
      </div>

      <div className="p-5 border-b-2 border-slate-100">
        <div className="flex items-baseline gap-3 flex-wrap">
          <span
            className="font-display text-4xl font-black text-slate-900"
            data-testid="pm-jobs-read-total"
          >
            {items.length}
          </span>
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
            {items.length === 1 ? t("active job") : t("active jobs")}
          </span>
          {scope === "admin_all" && (
            <span className="text-xs text-slate-500 flex items-center gap-1.5 ml-auto">
              <CheckCircle2 className="w-3 h-3 text-emerald-600" />
              {t("Admin view — every job visible")}
            </span>
          )}
          {scope === "pm_assigned" && (
            <span className="text-xs text-slate-500 ml-auto">
              {t("Scoped to jobs where you are primary or co-PM.")}
            </span>
          )}
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-center gap-2 mb-3">
          <Search className="w-4 h-4 text-slate-400" />
          <Input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder={t("Search project #, name, location…")}
            className="h-9 border-2 max-w-md"
            data-testid="pm-jobs-read-search"
          />
          <span className="text-xs text-slate-500 font-mono">
            {filtered.length} / {items.length}
          </span>
        </div>

        {loading ? (
          <div className="py-10 text-center text-slate-500">
          <Loader2 className="w-5 h-5 inline-block animate-spin mr-2" /> {t("Loading…")}
          </div>
        ) : items.length === 0 ? (
          <p className="text-sm text-slate-500 py-8 text-center italic">
            {t("No jobs are currently assigned to you. Ask your administrator if a job should be linked to your account.")}
          </p>
        ) : (
          <div className="overflow-auto border-2 border-slate-200 rounded max-h-[520px]">
            <table className="w-full min-w-[1040px] text-sm">
              <thead className="sticky top-0 bg-slate-50 z-[1]">
                <tr>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap">{t("Project #")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Project Name")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold">{t("Location")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap">{t("Primary PM")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap">{t("Co-PMs")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap">{t("Team")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap">{t("Setup")}</th>
                  <th className="text-left px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-700 font-bold whitespace-nowrap">{t("% Complete")}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((j) => (
                  (() => {
                    const safeProjectNumber = sanitizeOperatorProjectNumber(j.project_number, "Operations support");
                    const safeProjectName = sanitizeOperatorProjectName(j.project_name, "Operations support work");
                    const safeLocation = sanitizeOperatorReference(j.location, "Operations support yard");
                    const safeManager = sanitizeOperatorReference(j.project_manager, "Assigned PM");
                    return (
                  <tr
                    key={j.id || j.project_number}
                    className="border-t border-slate-100 hover:bg-slate-50"
                    data-testid={`pm-jobs-read-row-${j.project_number}`}
                  >
                    <td className="px-3 py-2 font-mono font-bold text-slate-900 whitespace-nowrap">
                      {j.project_number ? (
                        // Phase V-Prelude · Wave 1.1 — deep-link to
                        // per-project detail surface (hosts the
                        // Operational Timeline sidecar). No new column,
                        // no row chrome — just makes the existing
                        // project_number cell navigable.
                        <Link
                          to={`/pm/projects/${encodeURIComponent(j.project_number)}`}
                          data-testid={`pm-jobs-read-row-link-${j.project_number}`}
                          className="hover:underline underline-offset-2 hover:text-amber-700 transition-colors"
                        >
                          {safeProjectNumber}
                        </Link>
                      ) : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-800">
                      {safeProjectName || <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-700">
                      {safeLocation || <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-700 whitespace-nowrap">
                      {safeManager || <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-500 text-xs">
                      {Array.isArray(j.co_pms) && j.co_pms.length > 0
                        ? j.co_pms.map((p) => p.name || p.email).join(", ")
                        : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-500 text-xs">
                      {j.project_number ? (
                        <Link
                          to={`/pm/job/${encodeURIComponent(j.project_number)}/team`}
                          className="text-amber-700 hover:underline"
                          data-testid={`pm-jobs-team-link-${j.project_number}`}
                        >
                          Team
                        </Link>
                      ) : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-500 text-xs">
                      {j.project_number ? (
                        <Link
                          to={`/pm/projects/${encodeURIComponent(j.project_number)}`}
                          className="text-amber-700 hover:underline"
                          data-testid={`pm-jobs-setup-link-${j.project_number}`}
                        >
                          Job setup
                        </Link>
                      ) : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-3 py-2 text-slate-700 text-xs font-semibold" data-testid={`pm-jobs-progress-${j.project_number}`}>
                      {Number(j.cost_code_progress_percent || 0).toFixed(2)}%
                    </td>
                  </tr>
                    );
                  })()
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
