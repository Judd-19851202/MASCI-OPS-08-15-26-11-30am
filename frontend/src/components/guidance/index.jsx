// Operational Guidance Center — reusable contextual help components.
//
// Phase A scope (preview only):
//   - HelpTip            inline tooltip for forms
//   - WhyItMattersPanel  callout explaining operational purpose
//   - WhatHappensNextPanel  callout for post-submit behaviour
//   - RelatedWorkflowsPanel  list of related-article links (RBAC-aware via backend)
//   - TroubleshootingLink  one-line "stuck? see..." pointer
//
// All components render NULL gracefully when given no data — never
// throw, never block the surrounding form.
import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Info, Lightbulb, ArrowRightCircle, LifeBuoy, X, ChevronDown, ChevronUp,
} from "lucide-react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";

// ─────────────────────────────────────────────────────────────────────
// HelpTip — small (i) icon next to a label; click reveals body
// ─────────────────────────────────────────────────────────────────────
export function HelpTip({ title, children, "data-testid": testId }) {
  const [open, setOpen] = useState(false);
  if (!children) return null;
  return (
    <span className="inline-flex items-center gap-1 relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex items-center justify-center w-4 h-4 rounded-full bg-slate-300 hover:bg-slate-400 text-slate-700 transition-colors"
        aria-label={title || "Help"}
        data-testid={testId || "help-tip-btn"}
      >
        <Info className="w-3 h-3" />
      </button>
      {open && (
        <span
          role="tooltip"
          className="absolute left-6 top-0 z-40 w-64 bg-slate-900 text-slate-100 text-[12px] leading-relaxed p-3 rounded shadow-xl"
          data-testid="help-tip-popover"
        >
          {title && (
            <strong className="block text-[11px] uppercase tracking-wider text-amber-300 mb-1">
              {title}
            </strong>
          )}
          {children}
        </span>
      )}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────
// WhyItMattersPanel — yellow / amber callout for operational purpose
// ─────────────────────────────────────────────────────────────────────
// iter199 — Pass 3 translation: default title is translation-aware via
// useT(). Callers passing their own ``title`` or ``children`` still
// control their own strings (wrap with t() at the call site).
export function WhyItMattersPanel({ title, children, dismissible = true }) {
  const { t } = useT();
  const resolvedTitle = title || t("Why this matters");
  const [dismissed, setDismissed] = useState(false);
  if (dismissed || !children) return null;
  return (
    <div
      className="border-l-4 border-amber-500 bg-amber-50 p-3 rounded-r flex gap-3 items-start"
      data-testid="why-it-matters-panel"
    >
      <Lightbulb className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
      <div className="flex-1 text-sm text-slate-800 leading-relaxed">
        <strong className="block text-[11px] uppercase tracking-wider text-amber-700 font-bold mb-1">
          {resolvedTitle}
        </strong>
        {children}
      </div>
      {dismissible && (
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="text-slate-500 hover:text-slate-800"
          aria-label="Dismiss"
          data-testid="why-it-matters-dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// WhatHappensNextPanel — collapsible "after submit" callout
// ─────────────────────────────────────────────────────────────────────
export function WhatHappensNextPanel({ items, title = "What happens next" }) {
  const [open, setOpen] = useState(true);
  if (!items || items.length === 0) return null;
  return (
    <div
      className="border border-emerald-200 bg-emerald-50 rounded"
      data-testid="what-happens-next-panel"
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between p-3 text-left"
        data-testid="what-happens-next-toggle"
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-emerald-900">
          <ArrowRightCircle className="w-5 h-5 text-emerald-600" />
          {title}
        </span>
        {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      {open && (
        <ul className="px-3 pb-3 space-y-1 text-sm text-slate-800">
          {items.map((it, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-emerald-600 mt-0.5">→</span>
              <span>{it}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// RelatedWorkflowsPanel — fetches and renders RBAC-filtered related
// articles. Pass `articleId` and we'll resolve the related list from
// the server (so the frontend never has to know what the caller is
// allowed to see).
// ─────────────────────────────────────────────────────────────────────
export function RelatedWorkflowsPanel({ articleId }) {
  const [related, setRelated] = useState([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    if (!articleId) return;
    (async () => {
      try {
        const r = await api.get(`/guidance/articles/${articleId}`);
        if (active && r?.data?.related) setRelated(r.data.related);
      } catch {
        /* article not visible to caller, render nothing */
      } finally {
        if (active) setLoaded(true);
      }
    })();
    return () => { active = false; };
  }, [articleId]);

  if (!loaded || related.length === 0) return null;
  return (
    <div
      className="border border-slate-200 bg-white rounded p-3"
      data-testid="related-workflows-panel"
    >
      <strong className="block text-[11px] uppercase tracking-wider text-slate-600 mb-2">
        Related guidance
      </strong>
      <ul className="space-y-1 text-sm">
        {related.map((r) => (
          <li key={r.id}>
            <Link
              to={`/guidance/${r.id}`}
              className="text-amber-700 hover:text-amber-900 hover:underline inline-flex items-center gap-1"
              data-testid={`related-link-${r.id}`}
            >
              <ArrowRightCircle className="w-3.5 h-3.5" />
              {r.title}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// TroubleshootingLink — single-line "stuck? see..." pointer
// ─────────────────────────────────────────────────────────────────────
export function TroubleshootingLink({ articleId, label = "Need help?" }) {
  if (!articleId) return null;
  return (
    <Link
      to={`/guidance/${articleId}`}
      className="inline-flex items-center gap-1 text-[12px] text-slate-600 hover:text-slate-900"
      data-testid={`troubleshooting-link-${articleId}`}
    >
      <LifeBuoy className="w-3.5 h-3.5" />
      {label}
    </Link>
  );
}
