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

const KIND_META = {
  why: {
    icon: Lightbulb,
    label_en: "Why this matters",
    label_es: "Por qué importa",
    accent: "border-amber-400 bg-amber-50/40 text-amber-900",
    iconCls: "text-amber-600",
  },
  mistake: {
    icon: AlertTriangle,
    label_en: "Common mistakes",
    label_es: "Errores comunes",
    accent: "border-rose-400 bg-rose-50/40 text-rose-900",
    iconCls: "text-rose-600",
  },
  example: {
    icon: BookOpen,
    label_en: "Example",
    label_es: "Ejemplo",
    accent: "border-sky-400 bg-sky-50/40 text-sky-900",
    iconCls: "text-sky-600",
  },
  next: {
    icon: ArrowRight,
    label_en: "What happens next",
    label_es: "Qué pasa después",
    accent: "border-emerald-400 bg-emerald-50/40 text-emerald-900",
    iconCls: "text-emerald-600",
  },
  escalate: {
    icon: PhoneForwarded,
    label_en: "When to escalate",
    label_es: "Cuándo escalar",
    accent: "border-orange-500 bg-orange-50/40 text-orange-900",
    iconCls: "text-orange-600",
  },
  who: {
    icon: Users,
    label_en: "Who sees this",
    label_es: "Quién lo ve",
    accent: "border-violet-400 bg-violet-50/40 text-violet-900",
    iconCls: "text-violet-600",
  },
  when: {
    icon: Clock,
    label_en: "Timing",
    label_es: "Tiempo",
    accent: "border-slate-400 bg-slate-50/40 text-slate-900",
    iconCls: "text-slate-600",
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

  const renderedTitle =
    (lang === "es" && title_es) ? title_es : (title || (lang === "es" ? meta.label_es : meta.label_en));
  const renderedBody = (lang === "es" && body_es) ? body_es : body;

  if (!renderedBody) return null;

  const safeKey = (testId || `${kind}`).replace(/[^a-z0-9\-]/gi, "-").toLowerCase();

  return (
    <div
      className={`my-1.5 rounded-md border-l-4 ${meta.accent} text-[13px]`}
      data-testid={`helptip-${safeKey}`}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-black/[0.02] transition-colors"
        data-testid={`helptip-${safeKey}-toggle`}
      >
        <Icon className={`w-4 h-4 shrink-0 ${meta.iconCls}`} />
        <span className="font-semibold flex-1 truncate">{renderedTitle}</span>
        <span className={`text-[10px] uppercase tracking-wider opacity-60 ${open ? "rotate-90" : ""} transition-transform`}>›</span>
      </button>
      {open && (
        <div
          className="px-3 pb-2.5 pt-0.5 pl-9 text-[12.5px] leading-snug"
          data-testid={`helptip-${safeKey}-body`}
        >
          {renderedBody}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────
// Registry-mode block — fetches all tips for a form_key
// ─────────────────────────────────────────────────────────────────────
const _tipCache = new Map(); // form_key -> promise

// Read a token from sessionStorage first (leadership uses session), then
// localStorage (admin/hr/pm/shop/safety/dispatch). Matches the actual
// canonical storage keys used across the portal-auth modules.
function _readToken(key) {
  try {
    return (
      (typeof sessionStorage !== "undefined" && sessionStorage.getItem(key)) ||
      (typeof localStorage !== "undefined" && localStorage.getItem(key)) ||
      null
    );
  } catch (_e) {
    return null;
  }
}

async function _fetchTips(formKey) {
  const base = process.env.REACT_APP_BACKEND_URL || "";
  const url = `${base}/api/guidance/tips?form_key=${encodeURIComponent(formKey)}`;
  const headers = {};
  // Best-effort auth: pass any portal token we find so RBAC-scoped tips
  // reach the right portal. Storage keys match the canonical auth libs:
  //   masci.admin.token · masci.hr.token · masci.safety.token ·
  //   masci.pm.token · masci.shop.token · masci.dispatch.token ·
  //   masci.fl.token (sessionStorage).
  const adminTok = _readToken("masci.admin.token");           if (adminTok) headers["X-Admin-Token"] = adminTok;
  const hrTok = _readToken("masci.hr.token");                 if (hrTok) headers["X-HR-Token"] = hrTok;
  const safetyTok = _readToken("masci.safety.token");         if (safetyTok) headers["X-Safety-Token"] = safetyTok;
  const pmTok = _readToken("masci.pm.token");                 if (pmTok) headers["X-PM-Token"] = pmTok;
  const shopTok = _readToken("masci.shop.token");             if (shopTok) headers["X-Shop-Token"] = shopTok;
  const dispatchTok = _readToken("masci.dispatch.token");     if (dispatchTok) headers["X-Dispatch-Token"] = dispatchTok;
  const flTok = _readToken("masci.fl.token");                 if (flTok) headers["X-FL-Token"] = flTok;
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
      : `${filtered.length} coaching tips available · tap to expand`;

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
