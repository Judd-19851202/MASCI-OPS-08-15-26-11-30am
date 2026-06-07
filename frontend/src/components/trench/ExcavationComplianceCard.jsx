// Phase 10C · Live Compliance Card
//
// Sticky operational decision-support panel. Tells the foreman, in plain
// English, what OSHA requires for THIS excavation right now — and what's
// still missing. Reads pure compliance state from `excavationCompliance`.
import React from "react";
import { CheckCircle2, AlertTriangle, OctagonAlert, Info, Lightbulb } from "lucide-react";
import { useT } from "@/lib/i18n";

const SEVERITY = {
  danger: { color: "border-red-500 bg-red-50 text-red-900",          icon: OctagonAlert,   chip: "bg-red-700 text-white" },
  warn:   { color: "border-amber-400 bg-amber-50 text-amber-900",    icon: AlertTriangle,  chip: "bg-amber-600 text-white" },
  info:   { color: "border-cyan-400 bg-cyan-50 text-cyan-900",       icon: Info,           chip: "bg-cyan-700 text-white" },
};

const STATUS_STYLES = {
  "Ready":           { bg: "bg-emerald-700 border-emerald-800",  icon: CheckCircle2 },
  "Needs Review":    { bg: "bg-amber-600 border-amber-700",      icon: AlertTriangle },
  "Action Required": { bg: "bg-red-700 border-red-800",          icon: OctagonAlert },
};

export default function ExcavationComplianceCard({ result, testId = "excavation-compliance-card" }) {
  const { t } = useT();
  if (!result) return null;
  const { status, statusReason, requirements, suggestedPs, counts } = result;
  const styles = STATUS_STYLES[status] || STATUS_STYLES["Needs Review"];
  const StatusIcon = styles.icon;

  return (
    <div className="sticky top-0 z-30 -mx-4 sm:-mx-6 mb-3 bg-slate-50 pt-2 pb-2 px-4 sm:px-6" data-testid={testId}>
      <div className={`border-2 rounded-md text-white ${styles.bg}`} data-testid={`${testId}-banner`}>
        <div className="flex items-start gap-3 p-3">
          <StatusIcon className="w-6 h-6 mt-0.5 shrink-0" />
          <div className="flex-1">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] opacity-90">
              {t("Live OSHA Status")}
            </div>
            <div className="font-display text-xl font-black leading-tight" data-testid={`${testId}-status`}>
              {t(status)}
            </div>
            <div className="text-xs opacity-95 leading-snug mt-0.5">{t(statusReason)}</div>
          </div>
          <div className="flex flex-col gap-1 items-end text-[10px] uppercase tracking-[0.12em] font-mono">
            {counts.danger > 0 && <span className="bg-red-900 px-1.5 py-0.5 rounded">{counts.danger} {t("action")}</span>}
            {counts.warn > 0 && <span className="bg-amber-800 px-1.5 py-0.5 rounded">{counts.warn} {t("review")}</span>}
            {counts.info > 0 && <span className="bg-cyan-800 px-1.5 py-0.5 rounded">{counts.info} {t("info")}</span>}
          </div>
        </div>

        {/* Smart suggestion */}
        {suggestedPs && (
          <div className="bg-white/15 border-t border-white/20 px-3 py-1.5 text-xs flex items-center gap-2" data-testid={`${testId}-suggestion`}>
            <Lightbulb className="w-3.5 h-3.5 shrink-0" />
            <span><b>{t("Suggested protective system:")}</b> {t(suggestedPs)}</span>
          </div>
        )}
      </div>

      {/* Requirement chips */}
      {requirements.length > 0 && (
        <ul className="mt-2 space-y-1.5" data-testid={`${testId}-requirements`}>
          {requirements.map((r) => {
            const s = SEVERITY[r.severity] || SEVERITY.info;
            const Icon = s.icon;
            return (
              <li key={r.id} className={`border-l-4 ${s.color} rounded-sm p-2`} data-testid={`${testId}-req-${r.id}`}>
                <div className="flex items-start gap-2">
                  <Icon className="w-4 h-4 mt-0.5 shrink-0" />
                  <div className="flex-1 text-xs leading-snug">
                    <div className="font-bold uppercase tracking-[0.06em]">{t(r.title)}</div>
                    <div className="opacity-90 mt-0.5">{t(r.why)}</div>
                    {r.action && (
                      <div className="mt-1 font-bold">→ {t(r.action)}</div>
                    )}
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
