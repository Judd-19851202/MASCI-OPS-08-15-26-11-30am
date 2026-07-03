// Track 19.34 · Incident Field Intake · Field-vs-Safety doctrine banner.
//
// Renders a one-line, calm, high-signal banner at the top of the field
// incident-intake experience. The banner exists to protect the field user
// from being asked investigation questions — and to protect the platform
// from field users answering OSHA / insurance / discipline / root-cause
// questions that belong to Safety.
//
// Six-Pillar alignment:
//   Simple:      one line, one message, no scary emphasis.
//   Trusted:     sets an explicit expectation — Safety takes it from here.
//   Operational: fits the mobile-first field intake header.
//
// Zero-drift: this is an additive display banner. No form fields. No state.
// No payload change. No permission change.

import React from "react";
import { ShieldCheck } from "lucide-react";
import { useT } from "@/lib/i18n";

export default function IncidentFieldDoctrineBanner() {
  const { t } = useT();
  return (
    <div
      data-testid="incident-field-doctrine-banner"
      className="flex items-start gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-slate-700"
      role="note"
    >
      <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0 text-slate-500" aria-hidden />
      <div className="text-[13px] leading-snug">
        <span className="font-semibold text-slate-800">{t("You're capturing facts.")}</span>{" "}
        <span>
          {t("Safety will investigate and decide OSHA · insurance · root cause. Just tell us what happened, where, when, who was involved, and what you did.")}
        </span>
      </div>
    </div>
  );
}
