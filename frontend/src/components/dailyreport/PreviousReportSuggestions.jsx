// Phase 10D · Previous Report Suggestions.
//
// One-tap "use yesterday's crew / equipment / activity" component.
// Reads the most recent Daily Report for the chosen MASCI Job and offers
// one-tap apply chips. Reuses the existing /api/daily-reports GET.
import React, { useEffect, useState } from "react";
import { Sparkles, Users, Truck, ClipboardCheck, X } from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

async function _loadPrevious(projectNumber) {
  if (!projectNumber) return null;
  try {
    const r = await api.get("/daily-reports", { params: { project_number: projectNumber, limit: 5 } });
    // api may return list directly or {items}
    const items = Array.isArray(r.data) ? r.data : (r.data?.items || []);
    // Sort by report_date desc just to be safe
    items.sort((a, b) => String(b.report_date || "").localeCompare(String(a.report_date || "")));
    return items[0] || null;
  } catch { return null; }
}

export default function PreviousReportSuggestions({ projectNumber, onApply, testId = "dr-previous-suggestions" }) {
  const { t } = useT();
  const [state, setState] = useState({ prev: null, dismissed: false });
  const { prev, dismissed } = state;

  useEffect(() => {
    if (!projectNumber) return undefined;
    let alive = true;
    _loadPrevious(projectNumber).then((p) => { if (alive) setState({ prev: p, dismissed: false }); });
    return () => { alive = false; };
  }, [projectNumber]);

  if (!prev || dismissed) return null;

  const crewCount = (prev.masci_crews || []).reduce((sum, c) => sum + (Number(c.headcount) || (c.workers?.length || 0)), 0);
  const equipCount = (prev.equipment || []).length;
  const activityLen = (prev.work_performed || prev.activity_summary || "").length;

  const applyAll = () => {
    onApply({
      masci_crews: prev.masci_crews || [],
      subcontractors: prev.subcontractors || [],
      equipment: prev.equipment || [],
      work_performed: prev.work_performed || prev.activity_summary || "",
      production: prev.production || [],
    });
    setState((p) => ({ ...p, dismissed: true }));
  };
  const applyCrew = () => onApply({ masci_crews: prev.masci_crews || [], subcontractors: prev.subcontractors || [] });
  const applyEquip = () => onApply({ equipment: prev.equipment || [] });
  const applyActivity = () => onApply({ work_performed: prev.work_performed || prev.activity_summary || "" });

  return (
    <div className="border-2 border-cyan-400 bg-cyan-50 rounded-md p-3 mt-3" data-testid={testId}>
      <div className="flex items-start gap-2">
        <Sparkles className="w-5 h-5 text-cyan-700 mt-0.5 shrink-0" />
        <div className="flex-1">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-cyan-700 font-bold">{t("Previous Daily Report Found")}</div>
              <div className="text-sm text-cyan-900 font-bold">
                {prev.report_date || prev.doc_id || "Last report"} · {prev.prepared_by || t("Last foreman")}
              </div>
              <div className="text-[11px] text-cyan-800">
                {crewCount > 0 && <>{crewCount} {t("crew members")} · </>}
                {equipCount > 0 && <>{equipCount} {t("equipment items")} · </>}
                {activityLen > 0 && <>{t("work-performed text available")}</>}
              </div>
            </div>
            <button type="button" onClick={() => setState((p) => ({ ...p, dismissed: true }))}
              className="text-cyan-700 hover:text-cyan-900" data-testid={`${testId}-dismiss`} aria-label="Dismiss">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <button type="button" onClick={applyAll}
              className="bg-cyan-700 hover:bg-cyan-800 text-white text-xs font-bold uppercase tracking-[0.10em] px-3 py-1.5 rounded inline-flex items-center gap-1"
              data-testid={`${testId}-apply-all`}>
              <Sparkles className="w-3.5 h-3.5" /> {t("Use Everything from Yesterday")}
            </button>
            {crewCount > 0 && (
              <button type="button" onClick={applyCrew}
                className="bg-white border-2 border-cyan-700 text-cyan-800 hover:bg-cyan-100 text-xs font-bold uppercase tracking-[0.10em] px-3 py-1.5 rounded inline-flex items-center gap-1"
                data-testid={`${testId}-apply-crew`}>
                <Users className="w-3.5 h-3.5" /> {t("Use Crew")}
              </button>
            )}
            {equipCount > 0 && (
              <button type="button" onClick={applyEquip}
                className="bg-white border-2 border-cyan-700 text-cyan-800 hover:bg-cyan-100 text-xs font-bold uppercase tracking-[0.10em] px-3 py-1.5 rounded inline-flex items-center gap-1"
                data-testid={`${testId}-apply-equipment`}>
                <Truck className="w-3.5 h-3.5" /> {t("Use Equipment")}
              </button>
            )}
            {activityLen > 0 && (
              <button type="button" onClick={applyActivity}
                className="bg-white border-2 border-cyan-700 text-cyan-800 hover:bg-cyan-100 text-xs font-bold uppercase tracking-[0.10em] px-3 py-1.5 rounded inline-flex items-center gap-1"
                data-testid={`${testId}-apply-activity`}>
                <ClipboardCheck className="w-3.5 h-3.5" /> {t("Copy Last Activity")}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
