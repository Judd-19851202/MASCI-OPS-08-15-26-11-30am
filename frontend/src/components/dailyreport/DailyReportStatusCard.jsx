// Phase 10D · Daily Report Live Status Card.
// Same shape/feel as the Phase 10C ExcavationComplianceCard so foremen
// see one consistent operational decision-support pattern.
import React from "react";
import { CheckCircle2, AlertTriangle, OctagonAlert, Info } from "lucide-react";
import { useT } from "@/lib/i18n";

const STATUS_STYLES = {
  "Ready to Submit": { bg: "bg-emerald-700 border-emerald-800", icon: CheckCircle2 },
  "Needs Review":    { bg: "bg-amber-600 border-amber-700",     icon: AlertTriangle },
  "Action Required": { bg: "bg-red-700 border-red-800",         icon: OctagonAlert },
};
const SEV_CLASS = {
  danger: "border-red-500 bg-red-50 text-red-900",
  warn:   "border-amber-400 bg-amber-50 text-amber-900",
  info:   "border-cyan-400 bg-cyan-50 text-cyan-900",
};
const SEV_ICON = { danger: OctagonAlert, warn: AlertTriangle, info: Info };

export default function DailyReportStatusCard({ result, testId = "daily-report-status-card" }) {
  const { t } = useT();
  if (!result) return null;
  const { status, statusReason, requirements, counts } = result;
  const s = STATUS_STYLES[status] || STATUS_STYLES["Needs Review"];
  const StatusIcon = s.icon;

  return (
    <div className="sticky top-0 z-30 -mx-4 sm:-mx-6 mb-3 bg-slate-50 pt-2 pb-2 px-4 sm:px-6" data-testid={testId}>
      <div className={`border-2 rounded-md text-white ${s.bg}`}>
        <div className="flex items-start gap-3 p-3">
          <StatusIcon className="w-6 h-6 mt-0.5 shrink-0" />
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-90">{t("Live Submit Status")}</div>
            <div className="font-display text-xl font-black leading-tight" data-testid={`${testId}-status`}>{t(status)}</div>
            <div className="text-xs opacity-95 leading-snug mt-0.5">{t(statusReason)}</div>
          </div>
          <div className="flex flex-col gap-1 items-end text-[10px] uppercase tracking-[0.12em] font-mono">
            {counts.danger > 0 && <span className="bg-red-900 px-1.5 py-0.5 rounded">{counts.danger} {t("action")}</span>}
            {counts.warn   > 0 && <span className="bg-amber-800 px-1.5 py-0.5 rounded">{counts.warn} {t("review")}</span>}
            {counts.info   > 0 && <span className="bg-cyan-800 px-1.5 py-0.5 rounded">{counts.info} {t("info")}</span>}
          </div>
        </div>
      </div>
      {requirements.length > 0 && (
        <ul className="mt-2 space-y-1.5" data-testid={`${testId}-requirements`}>
          {requirements.map((r) => {
            const Icon = SEV_ICON[r.severity] || Info;
            return (
              <li key={r.id} className={`border-l-4 ${SEV_CLASS[r.severity] || SEV_CLASS.info} rounded-sm p-2`} data-testid={`${testId}-req-${r.id}`}>
                <div className="flex items-start gap-2">
                  <Icon className="w-4 h-4 mt-0.5 shrink-0" />
                  <div className="flex-1 text-xs leading-snug">
                    <div className="font-bold uppercase tracking-[0.06em]">{t(r.title)}</div>
                    <div className="opacity-90 mt-0.5">{t(r.why)}</div>
                    {r.action && <div className="mt-1 font-bold">→ {t(r.action)}</div>}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
