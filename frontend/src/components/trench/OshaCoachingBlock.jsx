// Phase 10A-B · OSHA Coaching Block (Correction 6)
//
// Contextual coaching strip shown next to OSHA decision points on the
// Public Excavation form. Renders the six standard sections:
//   • Why This Matters
//   • OSHA Requirement
//   • Example
//   • Common Mistakes
//   • When To Escalate
//   • If Unsure
//
// Field-first, non-punitive, superintendent-friendly. Collapsible by
// default so the form stays scan-friendly on a phone.
import React, { useState } from "react";
import { ShieldAlert, ChevronDown, ChevronUp } from "lucide-react";
import { useT } from "@/lib/i18n";

export default function OshaCoachingBlock({ title, why, requirement, example, mistakes, escalate, ifUnsure, testId, defaultOpen = false, tone = "amber" }) {
  const { t } = useT();
  const [open, setOpen] = useState(defaultOpen);

  const toneClass = {
    amber: "wp17-coaching-card--amber",
    red: "wp17-coaching-card--red",
    cyan: "wp17-coaching-card--cyan",
  }[tone] || "wp17-coaching-card--amber";

  return (
    <div className={`wp17-coaching-card ${toneClass} mt-3 p-3 sm:p-4`} data-testid={testId}>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-start gap-3 text-left"
        data-testid={`${testId}-toggle`}
      >
        <span className="wp17-coaching-card__icon mt-0.5 shrink-0">
          <ShieldAlert className="w-4 h-4" />
        </span>
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold leading-snug text-slate-500">
            {t("OSHA Coaching")} · {t(title)}
          </div>
          {!open && (
            <div className="mt-2 text-sm leading-6 text-slate-700 line-clamp-2">{t(why)}</div>
          )}
        </div>
        {open ? <ChevronUp className="w-4 h-4 mt-1 shrink-0 text-slate-500" /> : <ChevronDown className="w-4 h-4 mt-1 shrink-0 text-slate-500" />}
      </button>

      {open && (
        <div className="mt-3 space-y-2.5 text-sm leading-6 text-slate-700" data-testid={`${testId}-body`}>
          <div><span className="font-mono text-[10px] uppercase tracking-[0.16em] mr-2 text-slate-500">{t("Why This Matters")}</span>{t(why)}</div>
          {requirement && <div><span className="font-mono text-[10px] uppercase tracking-[0.16em] mr-2 text-slate-500">{t("OSHA Requirement")}</span>{t(requirement)}</div>}
          {example && <div><span className="font-mono text-[10px] uppercase tracking-[0.16em] mr-2 text-slate-500">{t("Example")}</span>{t(example)}</div>}
          {mistakes && <div><span className="font-mono text-[10px] uppercase tracking-[0.16em] mr-2 text-slate-500">{t("Common Mistakes")}</span>{t(mistakes)}</div>}
          {escalate && <div><span className="font-mono text-[10px] uppercase tracking-[0.16em] mr-2 text-slate-500">{t("When To Escalate")}</span>{t(escalate)}</div>}
          {ifUnsure && <div><span className="font-mono text-[10px] uppercase tracking-[0.16em] mr-2 text-slate-500">{t("If Unsure")}</span>{t(ifUnsure)}</div>}
        </div>
      )}
    </div>
  );
}
