// Phase 10A-B · OMEGA Correction 1 · Daily Report Excavation Activity Gate
//
// Asks the foreman whether excavation work happened today. When YES,
// the Daily Report cannot be submitted until at least one excavation
// record is created or linked. The backend enforces the gate (422 with
// structured error `excavation_record_required`).
//
// Two paths from the YES state:
//   1. Create New Excavation Record — opens /trench-safety/excavation/new
//      in a new tab with project_number + date + source=daily_report
//      params pre-filled. After submission, foreman returns to the
//      Daily Report and uses Link Existing to attach the EX-YYYY-### ID.
//   2. Link Existing — search by project_number to find any excavation
//      record that already exists for this job and attach it.
import React, { useEffect, useMemo, useState } from "react";
import { Link2, Plus, X, AlertTriangle, ExternalLink, Search, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

async function _loadExcavationsByProject(projectNumber) {
  if (!projectNumber) return [];
  try {
    const r = await api.get("/trench-safety/excavations", {
      params: { project_number: projectNumber, limit: 50 },
    });
    return Array.isArray(r.data?.items) ? r.data.items : [];
  } catch {
    return [];
  }
}

export default function DailyReportExcavationActivity({
  value = "No",
  onChange,
  linkedIds = [],
  onLinkedChange,
  projectNumber = "",
  projectName = "",
  reportDate = "",
  preparedBy = "",
  attemptedSubmit = false,
  testId = "dr-excavation-activity",
}) {
  const { t } = useT();
  const [state, setState] = useState({ found: [], loading: false });
  const { found, loading } = state;
  const [search, setSearch] = useState(false);

  useEffect(() => {
    if (!search) return undefined;
    let alive = true;
    setState((s) => ({ ...s, loading: true }));
    _loadExcavationsByProject(projectNumber).then((items) => {
      if (alive) setState({ found: items, loading: false });
    });
    return () => { alive = false; };
  }, [search, projectNumber]);

  const isYes = String(value).toLowerCase() === "yes";
  const missingLink = isYes && linkedIds.length === 0;
  const showAlert = missingLink && attemptedSubmit;

  // Pre-fill query params for the public excavation form
  const newRecordUrl = useMemo(() => {
    const u = new URLSearchParams({
      project_number: projectNumber,
      project_name: projectName,
      date: reportDate,
      supervisor: preparedBy,
      source: "daily_report",
    });
    return `/trench-safety/excavation/new?${u.toString()}`;
  }, [projectNumber, projectName, reportDate, preparedBy]);

  const unlinkOne = (id) => onLinkedChange((linkedIds || []).filter((x) => x !== id));
  const linkOne = (id) => {
    if (!linkedIds.includes(id)) onLinkedChange([...(linkedIds || []), id]);
  };
  const [manualId, setManualId] = useState("");

  return (
    <div className="bg-white border border-slate-200 rounded-md p-3" data-testid={testId}>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-cyan-700 font-bold mb-2">
        {t("Excavation Activity Today?")}
      </div>
      <div className="text-xs text-slate-600 mb-2">
        {t("If your crew opened or worked in any trench, hole, or excavation today, select YES and link the excavation record.")}
      </div>
      <div className="flex gap-2" data-testid={`${testId}-yesno`}>
        {[
          ["Yes", "exc-act-yes"],
          ["No", "exc-act-no"],
        ].map(([v, tid]) => (
          <button
            key={v}
            type="button"
            onClick={() => onChange(v)}
            className={"px-4 h-10 rounded border-2 text-sm font-bold uppercase tracking-[0.12em] transition " +
              (String(value) === v ? "border-cyan-700 bg-cyan-700 text-white" : "border-slate-300 bg-white text-slate-700 hover:border-cyan-500")}
            data-testid={tid}
          >
            {t(v)}
          </button>
        ))}
      </div>

      {isYes && (
        <div className="mt-3 space-y-3" data-testid={`${testId}-yes-panel`}>
          {/* Existing linked records */}
          {linkedIds.length > 0 && (
            <div data-testid={`${testId}-linked-list`}>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-emerald-700 font-bold mb-1">
                {t("Linked Excavation Records")}
              </div>
              <ul className="space-y-1">
                {linkedIds.map((id) => (
                  <li key={id} className="flex items-center justify-between bg-emerald-50 border border-emerald-300 rounded px-2 py-1.5" data-testid={`${testId}-linked-${id}`}>
                    <span className="font-mono font-bold text-emerald-900">{id}</span>
                    <button type="button" onClick={() => unlinkOne(id)} className="text-emerald-800 hover:text-red-700" aria-label={`Unlink ${id}`} data-testid={`${testId}-unlink-${id}`}>
                      <X className="w-4 h-4" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Create / Link options */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <a
              href={newRecordUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 bg-cyan-700 hover:bg-cyan-800 text-white text-sm font-bold uppercase tracking-[0.12em] rounded h-11 px-3"
              data-testid={`${testId}-create-new`}
            >
              <Plus className="w-4 h-4" /> {t("Create New Excavation Record")} <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <button
              type="button"
              onClick={() => setSearch((p) => !p)}
              className="flex items-center justify-center gap-2 bg-white border-2 border-cyan-700 text-cyan-800 hover:bg-cyan-50 text-sm font-bold uppercase tracking-[0.12em] rounded h-11 px-3"
              data-testid={`${testId}-link-existing-toggle`}
            >
              <Link2 className="w-4 h-4" /> {t("Link Existing Excavation Record")}
            </button>
          </div>

          {/* Search / manual link */}
          {search && (
            <div className="border border-slate-200 rounded p-2 bg-slate-50" data-testid={`${testId}-link-panel`}>
              {/* Manual ID input */}
              <div className="flex items-stretch gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={manualId}
                    onChange={(e) => setManualId(e.target.value.toUpperCase())}
                    placeholder="EX-2026-001"
                    className="pl-8 w-full h-10 border-2 border-slate-300 rounded font-mono uppercase text-sm"
                    data-testid={`${testId}-manual-id`}
                  />
                </div>
                <button
                  type="button"
                  onClick={() => { if (manualId.trim()) { linkOne(manualId.trim()); setManualId(""); } }}
                  className="bg-cyan-700 hover:bg-cyan-800 text-white text-xs font-bold uppercase tracking-[0.12em] rounded px-3"
                  data-testid={`${testId}-manual-link`}
                >
                  {t("Link")}
                </button>
              </div>

              {/* Suggestions for this project */}
              <div className="mt-2 text-[10px] uppercase tracking-[0.14em] font-mono text-slate-500">
                {t("Suggestions for project")} {projectNumber || t("(set project to load)")}
              </div>
              {loading ? (
                <div className="text-xs text-slate-500 inline-flex items-center gap-2 mt-1"><Loader2 className="w-3.5 h-3.5 animate-spin" /> {t("Loading…")}</div>
              ) : found.length === 0 ? (
                <div className="text-xs text-slate-500 italic mt-1">{t("No existing excavation records for this project.")}</div>
              ) : (
                <ul className="mt-1 space-y-1 max-h-40 overflow-y-auto">
                  {found.map((it) => (
                    <li key={it.id}>
                      <button
                        type="button"
                        onClick={() => linkOne(it.id)}
                        className="w-full text-left bg-white border border-slate-200 rounded px-2 py-1.5 hover:border-cyan-600 text-xs flex items-center justify-between gap-2"
                        data-testid={`${testId}-suggest-${it.id}`}
                      >
                        <span>
                          <span className="font-mono font-bold text-slate-900">{it.id}</span>
                          <span className="text-slate-500 ml-2">{it.date_of_work} · {it.foreman_name || it.supervisor_name || "Foreman"} · {it.status}</span>
                        </span>
                        {!linkedIds.includes(it.id) && <Plus className="w-4 h-4 text-cyan-700" />}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Hard alert when submit attempted with no link */}
          {showAlert && (
            <div className="bg-red-50 border-2 border-red-300 rounded p-3 flex items-start gap-2" data-testid={`${testId}-block-alert`}>
              <AlertTriangle className="w-5 h-5 text-red-700 mt-0.5 shrink-0" />
              <div className="text-sm text-red-900 leading-snug">
                <strong className="uppercase tracking-[0.08em]">{t("Action Required.")}</strong>{" "}
                {t("Excavation Activity Today is YES — create or link at least one Excavation Record before submitting the Daily Report.")}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
