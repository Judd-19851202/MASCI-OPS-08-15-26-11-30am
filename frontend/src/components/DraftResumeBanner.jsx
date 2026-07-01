// Track 19.16 · Phase B2 · Draft resume banner.
// Renders when an unfinished draft exists on `/incidents/report`. Shows
// last-saved time + detected incident type. User can Resume or Discard.
// Stale (>72h) drafts are auto-treated as discardable but never
// destroyed silently — the user always confirms.

import React, { useMemo } from "react";
import { useT } from "@/lib/i18n";
import { INCIDENT_FLOWS } from "@/lib/incidentReportSchema";
import { Clock, Trash2, ChevronRight } from "lucide-react";

function _timeAgo(iso, t) {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  if (!Number.isFinite(then)) return "";
  const diffMs = Date.now() - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return t("just now");
  if (mins < 60) return `${mins} ${t("min")}`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} ${t("hr")}`;
  const days = Math.floor(hours / 24);
  return `${days} ${t("day")}`;
}

export function DraftResumeBanner({ draft, onResume, onDiscard }) {
  const { t } = useT();
  const type = draft?.incident_type;
  const label = useMemo(() => (type && INCIDENT_FLOWS[type] ? t(INCIDENT_FLOWS[type].label) : t("Untitled")), [type, t]);
  const ago = _timeAgo(draft?.__updated_at__, t);
  if (!draft) return null;
  return (
    <div
      data-testid="incident-report-draft-banner"
      role="region"
      aria-label={t("Unfinished report")}
      className="rounded-xl border-2 border-amber-300 bg-amber-50 p-3 sm:p-4 flex items-center gap-3"
    >
      <div className="rounded-full bg-amber-200 text-amber-900 h-10 w-10 flex items-center justify-center shrink-0" aria-hidden>
        <Clock className="w-5 h-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-amber-800">
          {t("Unfinished report")}
        </div>
        <div className="font-display text-base font-bold text-amber-900 truncate">
          {label} {ago && <span className="font-mono text-xs font-normal">· {ago} {t("ago")}</span>}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <button
          type="button"
          onClick={onDiscard}
          className="h-10 px-3 rounded-md border border-amber-300 text-amber-900 hover:bg-amber-100 inline-flex items-center gap-1"
          data-testid="incident-report-draft-banner-discard"
          aria-label={t("Discard unfinished report")}
        >
          <Trash2 className="w-4 h-4" aria-hidden /> {t("Discard")}
        </button>
        <button
          type="button"
          onClick={onResume}
          className="h-10 px-3 rounded-md bg-amber-700 text-white font-bold hover:bg-amber-800 inline-flex items-center gap-1"
          data-testid="incident-report-draft-banner-resume"
          aria-label={t("Resume unfinished report")}
        >
          {t("Resume")} <ChevronRight className="w-4 h-4" aria-hidden />
        </button>
      </div>
    </div>
  );
}

export default DraftResumeBanner;
