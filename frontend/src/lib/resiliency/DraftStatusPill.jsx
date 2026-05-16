// DraftStatusPill.jsx — Phase J · subtle inline pill showing autosave
// status. Renders nothing during the brief "idle" stretches so the
// form chrome stays calm.

import React from "react";
import { CloudUpload, Check } from "lucide-react";

export default function DraftStatusPill({ status, testId = "draft-status-pill" }) {
  if (!status || status === "idle") return null;
  if (status === "saving") {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 text-[10px] font-mono uppercase tracking-wider"
        data-testid={testId}
      >
        <CloudUpload className="w-3 h-3" /> Saving draft…
      </span>
    );
  }
  if (status === "saved") {
    return (
      <span
        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-mono uppercase tracking-wider"
        data-testid={testId}
      >
        <Check className="w-3 h-3" /> Saved as draft
      </span>
    );
  }
  return null;
}
