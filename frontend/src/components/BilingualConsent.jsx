import React from "react";
import { ShieldCheck } from "lucide-react";

/**
 * Bilingual sign-off line shown above each signature box on Safety Meeting
 * and JHP forms + their printable PDF views. Always renders BOTH English
 * and Spanish so the legal record (PDF) is fully bilingual regardless of
 * which UI language the form was filled in.
 *
 * Props:
 *   variant: "meeting" | "jha"
 *   compact: bool — render small 1-line block (used in printed PDF rows)
 */
export function BilingualConsent({ variant = "meeting", compact = false }) {
  const en =
    variant === "jha"
      ? "I understand the hazards and the safe work plan."
      : "I understand the hazards discussed and the safe work plan.";
  const es =
    variant === "jha"
      ? "Entiendo los peligros y el plan de trabajo seguro."
      : "Entiendo los peligros discutidos y el plan de trabajo seguro.";

  if (compact) {
    return (
      <div
        className="text-[8pt] leading-snug text-slate-700 mt-2 border-t border-slate-200 pt-1"
        data-testid="bilingual-consent-compact"
      >
        <div>
          <span className="font-mono text-[7pt] uppercase tracking-[0.15em] text-red-700 mr-1">EN</span>
          {en}
        </div>
        <div>
          <span className="font-mono text-[7pt] uppercase tracking-[0.15em] text-red-700 mr-1">ES</span>
          {es}
        </div>
      </div>
    );
  }

  return (
    <div
      className="border-l-4 border-red-700 bg-red-50/60 px-3 py-2 rounded-sm"
      data-testid="bilingual-consent"
    >
      <div className="flex items-start gap-2">
        <ShieldCheck className="w-4 h-4 text-red-700 shrink-0 mt-0.5" />
        <div className="space-y-1 text-sm leading-snug text-slate-800">
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mr-2">
              EN
            </span>
            {en}
          </div>
          <div>
            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-red-700 font-bold mr-2">
              ES
            </span>
            {es}
          </div>
        </div>
      </div>
    </div>
  );
}
