// LifecycleGuide.jsx — iter356 · Operational Coaching standard.
//
// Permanent platform pattern (per the 2026-05-23 operational coaching
// directive). Inline, mobile-friendly, ES-parity-ready coaching banner
// that explains:
//   - what the workflow is
//   - lifecycle / status flow
//   - role boundaries (who can do what)
//   - downstream visibility (where the record propagates)
//   - accountability implications
//
// Designed to render INSIDE existing surfaces (CAPA list, Incident detail,
// etc) — not as a modal or separate page. Field-direct language. No
// corporate filler. Collapses on small screens to a one-line summary.
//
// Usage:
//   <LifecycleGuide
//     id="capa-lifecycle"          // localStorage dismissal key
//     icon={LifecycleIcon}         // lucide-react icon
//     title={t("CAPA lifecycle")}
//     summary={t("Open → In Progress → Pending Review → Verified → Closed")}
//     sections={[
//       { label: t("Roles"),       body: t("Safety owns governance...") },
//       { label: t("Downstream"),  body: t("Open CAPAs are visible to...") },
//       { label: t("Closeout"),    body: t("Cannot close without...") },
//     ]}
//   />

import React, { useState, useEffect } from "react";
import { ChevronDown, X, BookOpen } from "lucide-react";
import { useT } from "@/lib/i18n";

export function LifecycleGuide({
  id,
  icon: Icon = BookOpen,
  title,
  summary,
  sections = [],
  defaultOpen = false,
  accent = "indigo",
  dismissible = true,
}) {
  const { t } = useT();
  const storageKey = id ? `masci.lifecycle.${id}` : null;
  const [open, setOpen] = useState(defaultOpen);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!storageKey) return;
    try {
      const v = localStorage.getItem(storageKey);
      if (v === "dismissed") setDismissed(true);
    } catch { /* ignore */ }
  }, [storageKey]);

  if (dismissed) return null;

  const handleDismiss = () => {
    if (storageKey) {
      try { localStorage.setItem(storageKey, "dismissed"); } catch { /* ignore */ }
    }
    setDismissed(true);
  };

  const accentMap = {
    indigo:  "border-l-indigo-600 bg-indigo-50/40",
    amber:   "border-l-amber-600 bg-amber-50/40",
    emerald: "border-l-emerald-600 bg-emerald-50/40",
    rose:    "border-l-rose-600 bg-rose-50/40",
    slate:   "border-l-slate-700 bg-slate-50/60",
  };
  const iconBgMap = {
    indigo:  "bg-indigo-600",
    amber:   "bg-amber-600",
    emerald: "bg-emerald-600",
    rose:    "bg-rose-600",
    slate:   "bg-slate-700",
  };

  return (
    <div
      className={`border border-slate-200 border-l-4 rounded-md ${accentMap[accent] || accentMap.indigo} text-sm`}
      data-testid={`lifecycle-guide-${id || "anon"}`}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-start gap-3 p-3 text-left"
        data-testid={`lifecycle-guide-toggle-${id || "anon"}`}
      >
        <div className={`inline-flex items-center justify-center w-8 h-8 rounded-md ${iconBgMap[accent] || iconBgMap.indigo} text-white shrink-0`}>
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-display font-black text-slate-900">{title}</span>
            <span className="font-mono text-[10px] uppercase tracking-wider text-slate-500 font-bold">
              {t("Lifecycle Guide")}
            </span>
          </div>
          {summary ? (
            <div className="text-xs text-slate-700 mt-0.5 font-mono">{summary}</div>
          ) : null}
        </div>
        <ChevronDown className={`w-4 h-4 mt-1 text-slate-500 transition-transform shrink-0 ${open ? "rotate-180" : ""}`} />
      </button>
      {open ? (
        <div className="px-3 pb-3 pt-1 space-y-2.5" data-testid={`lifecycle-guide-body-${id || "anon"}`}>
          {sections.map((s, i) => (
            <div key={i}>
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold mb-0.5">
                {s.label}
              </div>
              <div className="text-xs text-slate-700 leading-snug">{s.body}</div>
            </div>
          ))}
          {dismissible ? (
            <div className="pt-1 flex justify-end">
              <button
                type="button"
                onClick={handleDismiss}
                className="text-[11px] text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
                data-testid={`lifecycle-guide-dismiss-${id || "anon"}`}
              >
                <X className="w-3 h-3" /> {t("Don't show this again")}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export default LifecycleGuide;
