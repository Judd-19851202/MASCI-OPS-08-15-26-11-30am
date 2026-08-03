// HelpTip.jsx — Contextual Operational Guidance component (iter209)
//
// Operator directive (2026-05-18): reusable component for embedding
// short coaching tips inside production forms. Concise, mobile-first,
// collapsible by default, bilingual.
//
// Two usage modes:
//
//   1) REGISTRY MODE — fetches tips for a form_key from the backend:
//      <HelpTipBlock formKey="daily-report.crew" />
//      Renders one collapsible card per tip the backend returns
//      (already RBAC-filtered server-side).
//
//   2) STATIC MODE — caller supplies the content directly:
//      <HelpTip kind="why" title="Why this matters" body="..." />
//      Useful for one-offs where pulling from the registry is overkill.
//
// Design constraints:
//   • Collapsed by default — operators see a small affordance, expand
//     only when they need it. Never blocks the form.
//   • Color-coded by kind (subtle, accessible).
//   • Bilingual via existing useT() hook (title_es / body_es fallback
//     to EN when not present).
//   • One H-line of vertical space when collapsed.

import React, { useEffect, useState } from "react";
import {
  Lightbulb, AlertTriangle, BookOpen, ArrowRight,
  PhoneForwarded, Users, Clock,
} from "lucide-react";
import { useT } from "@/lib/i18n";
import { buildScopedPortalAuthHeaders } from "@/lib/authHeaders";
import { sanitizeOperatorCopy } from "@/lib/operatorLanguage";

const KIND_META = {
  why: {
    icon: Lightbulb,
    label_en: "Why this matters",
    label_es: "Por qué importa",
    tone: "amber",
  },
  mistake: {
    icon: AlertTriangle,
    label_en: "Common mistakes",
    label_es: "Errores comunes",
    tone: "rose",
  },
  example: {
    icon: BookOpen,
    label_en: "Example",
    label_es: "Ejemplo",
    tone: "sky",
  },
  next: {
    icon: ArrowRight,
    label_en: "What happens next",
    label_es: "Qué pasa después",
    tone: "emerald",
  },
  escalate: {
    icon: PhoneForwarded,
    label_en: "When to escalate",
    label_es: "Cuándo escalar",
    tone: "slate",
  },
  who: {
    icon: Users,
    label_en: "Who sees this",
    label_es: "Quién lo ve",
    tone: "sky",
  },
  when: {
    icon: Clock,
    label_en: "Timing",
    label_es: "Tiempo",
    tone: "slate",
  },
};

// ─────────────────────────────────────────────────────────────────────
// Static-mode single tip
// ─────────────────────────────────────────────────────────────────────
export function HelpTip({
  kind = "why",
  title,
  body,
  title_es,
  body_es,
  testId,
  defaultOpen = false,
}) {
  const { lang } = useT();
  const meta = KIND_META[kind] || KIND_META.why;
  const Icon = meta.icon;
  const [open, setOpen] = useState(Boolean(defaultOpen));

  const rawTitle = (lang === "es" && title_es) ? title_es : (title || (lang === "es" ? meta.label_es : meta.label_en));
  const rawBody = (lang === "es" && body_es) ? body_es : body;
  const renderedTitle = sanitizeOperatorCopy(rawTitle, rawTitle);
  const renderedBody = sanitizeOperatorCopy(rawBody, rawBody);

  if (!renderedBody) return null;

  const safeKey = (testId || `${kind}`).replace(/[^a-z0-9\-]/gi, "-").toLowerCase();

  return (
    <div
      className={`wp17-coaching-card wp17-coaching-card--${meta.tone || "amber"} my-2 text-[13px]`}
      data-testid={`helptip-${safeKey}`}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full flex items-start gap-3 px-4 py-3 text-left transition-colors"
        data-testid={`helptip-${safeKey}-toggle`}
      >
        <span className="wp17-coaching-card__icon shrink-0">
          <Icon className="w-4 h-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 font-bold">
            {renderedTitle}
          </span>
          {!open ? (
            <span className="mt-2 block line-clamp-2 text-sm leading-6 text-slate-700">
              {renderedBody}
            </span>
          ) : null}
        </span>
        <span className={`mt-1 text-[10px] uppercase tracking-wider text-slate-400 ${open ? "rotate-90" : ""} transition-transform`}>›</span>
      </button>
      {open && (
        <div
          className="border-t border-slate-200/70 px-4 pb-4 pt-3 text-sm leading-6 text-slate-700"
          data-testid={`helptip-${safeKey}-body`}
        >
          <div className="pl-[3.25rem]">{renderedBody}</div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Registry-mode block — fetches all tips for a form_key
// ─────────────────────────────────────────────────────────────────────
const _tipCache = new Map(); // form_key -> promise

async function _fetchTips(formKey) {
  const base = process.env.REACT_APP_BACKEND_URL || "";
  const url = `${base}/api/guidance/tips?form_key=${encodeURIComponent(formKey)}`;
  const headers = buildScopedPortalAuthHeaders([
    "admin",
    "hr",
    "safety",
    "pm",
    "shop",
    "dispatch",
    "field_leadership",
  ]);
  const r = await fetch(url, { headers });
  if (!r.ok) return [];
  const j = await r.json();
  return Array.isArray(j?.tips) ? j.tips : [];
}

export function HelpTipBlock({ formKey, kinds, className = "", showCounter = false }) {
  const { lang } = useT();
  const [tips, setTips] = useState(null);

  useEffect(() => {
    if (!formKey) { setTips([]); return; }
    let alive = true;
    const cached = _tipCache.get(formKey);
    const p = cached || _fetchTips(formKey);
    if (!cached) _tipCache.set(formKey, p);
    p.then((rows) => { if (alive) setTips(rows || []); })
     .catch(() => { if (alive) setTips([]); });
    return () => { alive = false; };
  }, [formKey]);

  if (!tips || tips.length === 0) return null;
  const filtered = kinds && kinds.length
    ? tips.filter((t) => kinds.includes(t.kind))
    : tips;

  // Discoverability counter — single subtle line above the tips block,
  // shown only when at least 3 tips are available. Operator-approved.
  const counterLabel =
    lang === "es"
      ? `${filtered.length} consejos disponibles · toca para expandir`
      : `${filtered.length} workflow tips available · tap to expand`;

  return (
    <div
      className={`space-y-1 ${className}`}
      data-testid={`helptip-block-${formKey.replace(/[^a-z0-9\-]/gi, "-").toLowerCase()}`}
    >
      {showCounter && filtered.length >= 3 && (
        <div
          className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-500 pl-1 pb-0.5"
          data-testid={`helptip-block-${formKey.replace(/[^a-z0-9\-]/gi, "-").toLowerCase()}-counter`}
        >
          {counterLabel}
        </div>
      )}
      {filtered.map((t, i) => (
        <HelpTip
          key={`${t.form_key}-${t.kind}-${i}`}
          kind={t.kind}
          title={t.title}
          body={t.body}
          title_es={t.title_es}
          body_es={t.body_es}
          testId={`${t.form_key}-${t.kind}`}
        />
      ))}
    </div>
  );
}

export default HelpTip;
