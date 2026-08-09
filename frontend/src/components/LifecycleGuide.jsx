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
import { X, BookOpen } from "lucide-react";
import { useT } from "@/lib/i18n";
import { WorkflowCoachingDisclosure } from "@/components/WorkflowCoachingDisclosure";

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

  const safeId = id || "anon";
  const tone = {
    indigo: "sky",
    amber: "amber",
    emerald: "emerald",
    rose: "rose",
    slate: "slate",
  }[accent] || "sky";

  const blocks = [
    summary ? {
      label: t("Lifecycle Guide"),
      body: summary,
      tone,
      testId: `lifecycle-guide-summary-${safeId}`,
    } : null,
    ...sections.map((section, index) => ({
      label: section.label,
      body: section.body,
      tone,
      testId: `lifecycle-guide-section-${safeId}-${index}`,
    })),
    dismissible ? {
      label: t("Visibility"),
      body: (
        <button
          type="button"
          onClick={handleDismiss}
          className="inline-flex items-center gap-1 text-[11px] font-mono uppercase tracking-[0.15em] text-slate-500 hover:text-slate-900 transition-colors"
          data-testid={`lifecycle-guide-dismiss-${safeId}`}
        >
          <X className="w-3 h-3" /> {t("Hide this guide")}
        </button>
      ),
      tone: "slate",
      testId: `lifecycle-guide-dismiss-block-${safeId}`,
    } : null,
  ].filter(Boolean);

  return (
    <WorkflowCoachingDisclosure
      blocks={blocks}
      title={title}
      description={summary}
      icon={Icon}
      testIdPrefix={`lifecycle-guide-${safeId}`}
      containerTestId={`lifecycle-guide-${safeId}`}
      triggerTestId={`lifecycle-guide-toggle-${safeId}`}
      panelTestId={`lifecycle-guide-body-${safeId}`}
      collapsedCounterLabel={title || t("Lifecycle Guide")}
      defaultOpen={Boolean(defaultOpen)}
      storageKey={storageKey ? `${storageKey}.open` : undefined}
    />
  );
}

export default LifecycleGuide;
