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

  const toneClasses = {
    amber: "border-amber-300 bg-amber-50 text-amber-900",
    red:   "border-red-300 bg-red-50 text-red-900",
    cyan:  "border-cyan-300 bg-cyan-50 text-cyan-900",
  }[tone] || "border-amber-300 bg-amber-50 text-amber-900";

  return (
    <div className={`mt-2 border-l-4 ${toneClasses} rounded-sm p-2`} data-testid={testId}>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-start gap-2 text-left"
        data-testid={`${testId}-toggle`}
      >
        <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" />
        <div className="flex-1">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] font-bold leading-snug">
            {t("OSHA Coaching")} · {t(title)}
          </div>
          {!open && (
            <div className="text-xs leading-snug mt-1 line-clamp-2">{t(why)}</div>
          )}
        </div>
        {open ? <ChevronUp className="w-4 h-4 mt-0.5 shrink-0" /> : <ChevronDown className="w-4 h-4 mt-0.5 shrink-0" />}
      </button>

      {open && (
        <div className="mt-2 text-xs leading-relaxed space-y-1.5" data-testid={`${testId}-body`}>
          <div><span className="font-bold uppercase tracking-[0.08em] mr-1">{t("Why This Matters:")}</span>{t(why)}</div>
          {requirement && <div><span className="font-bold uppercase tracking-[0.08em] mr-1">{t("OSHA Requirement:")}</span>{t(requirement)}</div>}
          {example && <div><span className="font-bold uppercase tracking-[0.08em] mr-1">{t("Example:")}</span>{t(example)}</div>}
          {mistakes && <div><span className="font-bold uppercase tracking-[0.08em] mr-1">{t("Common Mistakes:")}</span>{t(mistakes)}</div>}
          {escalate && <div><span className="font-bold uppercase tracking-[0.08em] mr-1">{t("When To Escalate:")}</span>{t(escalate)}</div>}
          {ifUnsure && <div><span className="font-bold uppercase tracking-[0.08em] mr-1">{t("If Unsure:")}</span>{t(ifUnsure)}</div>}
        </div>
      )}
    </div>
  );
}
