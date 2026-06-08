/**
 * OA-1 · CoachingPanel.jsx
 * Mandatory 5-block coaching strip required on every OA screen.
 * Concise · operational language · bilingual via useT().
 */
import React from "react";
import { Lightbulb, Eye, ArrowRight, AlertTriangle, XCircle } from "lucide-react";
import { useT } from "@/lib/i18n";

const BLOCKS = [
  {
    key: "why",
    icon: Lightbulb,
    titleEn: "Why This Matters",
    bodyEn: "Operations Actions give every operator a single place to coordinate, own, and close out field issues — without spreadsheets or radio chains.",
    accent: "border-l-indigo-500",
    testid: "oa-coach-why",
  },
  {
    key: "who",
    icon: Eye,
    titleEn: "Who Sees This",
    bodyEn: "Every operator portal — Admin, HR, Safety, Dispatch, PM, Shop, Field Leadership — sees actions visible to their role.",
    accent: "border-l-sky-500",
    testid: "oa-coach-who",
  },
  {
    key: "next",
    icon: ArrowRight,
    titleEn: "What Happens Next",
    bodyEn: "You pick the owner. The owner gets a bell notification. They drive it to completion. You can update status, add notes, attach photos at any time.",
    accent: "border-l-emerald-500",
    testid: "oa-coach-next",
  },
  {
    key: "escalate",
    icon: AlertTriangle,
    titleEn: "When To Escalate",
    bodyEn: "Escalate by raising priority to High or Critical and reassigning to the right operator. Do not invent new statuses — use the six approved.",
    accent: "border-l-amber-500",
    testid: "oa-coach-escalate",
  },
  {
    key: "mistakes",
    icon: XCircle,
    titleEn: "Common Mistakes",
    bodyEn: "Vague titles · no owner · missing job number · no photos · using as a help-desk ticket. Operations Actions are for operational ownership, not support requests.",
    accent: "border-l-rose-500",
    testid: "oa-coach-mistakes",
  },
];

export default function CoachingPanel({ compact = false, className = "" }) {
  const { t } = useT();
  return (
    <section
      data-testid="oa-coaching-panel"
      className={`grid grid-cols-1 ${compact ? "" : "md:grid-cols-2 lg:grid-cols-5"} gap-2 ${className}`}
    >
      {BLOCKS.map((b) => (
        <div
          key={b.key}
          data-testid={b.testid}
          className={`bg-white border border-slate-200 border-l-4 ${b.accent} rounded-md p-3`}
        >
          <div className="flex items-center gap-2 mb-1">
            <b.icon className="w-4 h-4 text-slate-700" />
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700 font-bold">
              {t(b.titleEn)}
            </span>
          </div>
          <p className="text-xs text-slate-600 leading-snug">{t(b.bodyEn)}</p>
        </div>
      ))}
    </section>
  );
}
