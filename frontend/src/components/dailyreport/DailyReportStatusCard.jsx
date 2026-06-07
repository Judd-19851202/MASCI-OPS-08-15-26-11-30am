// Phase 10D · Daily Report Live Submit Status — Path A.
//
// One line. No paragraphs. No why. No action text.
//
//   READY TO SUBMIT ✓
//
// or
//
//   3 THINGS LEFT  →  Add Crew · Add Photos · Sign Report
//
// Each chip jumps directly to the relevant section. That's the entire
// surface. The compliance engine returns short labels; this component
// just renders them.
import React from "react";
import { CheckCircle2, OctagonAlert, AlertTriangle } from "lucide-react";
import { useT } from "@/lib/i18n";

const PALETTE = {
  "Ready to Submit": { bg: "bg-emerald-50 border-emerald-400 text-emerald-900", icon: CheckCircle2 },
  "Needs Review":    { bg: "bg-amber-50 border-amber-400 text-amber-900",        icon: AlertTriangle },
  "Action Required": { bg: "bg-red-50 border-red-400 text-red-900",              icon: OctagonAlert },
};

function jump(id) {
  if (!id) return;
  const el = document.querySelector(`[data-testid="${id}"]`) || document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    if (typeof el.focus === "function") setTimeout(() => el.focus(), 350);
  }
}

export default function DailyReportStatusCard({ result, testId = "daily-report-status-card" }) {
  const { t } = useT();
  if (!result) return null;
  const { status, items } = result;
  const p = PALETTE[status] || PALETTE["Needs Review"];
  const Icon = p.icon;

  if (status === "Ready to Submit") {
    return (
      <div className={`flex items-center gap-2 border rounded-md px-3 py-2 ${p.bg}`}
        data-testid={testId}>
        <Icon className="w-4 h-4" />
        <span className="font-bold uppercase tracking-[0.12em] text-sm" data-testid={`${testId}-status`}>{t("Ready to Submit")}</span>
      </div>
    );
  }

  return (
    <div className={`border rounded-md px-3 py-2 ${p.bg}`} data-testid={testId}>
      <div className="flex flex-wrap items-center gap-2">
        <Icon className="w-4 h-4 shrink-0" />
        <span className="font-bold uppercase tracking-[0.12em] text-sm" data-testid={`${testId}-status`}>
          {items.length} {t(items.length === 1 ? "thing left" : "things left")}
        </span>
        <span className="opacity-60 text-sm">→</span>
        {items.map((it) => (
          <button
            key={it.id}
            type="button"
            onClick={() => jump(it.jumpTo)}
            className="bg-white/70 hover:bg-white border border-current/30 rounded px-2 py-0.5 text-xs font-bold uppercase tracking-[0.06em]"
            data-testid={`${testId}-item-${it.id}`}
          >
            {t(it.label)}
          </button>
        ))}
      </div>
    </div>
  );
}
