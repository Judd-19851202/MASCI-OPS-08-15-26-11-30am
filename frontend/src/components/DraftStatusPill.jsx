// DraftStatusPill.jsx — tiny "Saved as draft" / "Saving…" indicator.
// Subtle: fades in for ~1.2s after autosave fires, then idles. Used by
// the priority forms (Incidents · Field Leadership · Daily Reports).
//
// iter-RC1-FH · M-18 · bilingual labels (no English bleed in ES mode).

import React from "react";
import { CloudUpload, Cloud, Check } from "lucide-react";
import { useT } from "@/lib/i18n";

const ICON = {
  saving: CloudUpload,
  saved:  Check,
};

const TINT = {
  saving: "bg-slate-50  text-slate-700 border-slate-300",
  saved:  "bg-emerald-50 text-emerald-800 border-emerald-300",
};

export default function DraftStatusPill({ status }) {
  const { t } = useT();
  if (status === "idle" || !status) return null;
  const Icon = ICON[status] || Cloud;
  const label =
    status === "saving" ? t("Saving draft…") : t("Draft saved");
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full border-2 text-[10px] font-mono uppercase tracking-wider font-bold ${TINT[status]}`}
      data-testid={`draft-status-pill-${status}`}
    >
      <Icon className="w-3 h-3" />
      {label}
    </span>
  );
}
