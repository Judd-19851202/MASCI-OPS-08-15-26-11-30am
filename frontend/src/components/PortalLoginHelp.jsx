// PortalLoginHelp.jsx — Consistent pre-login discoverability strip
// for every protected portal login page (HR · Safety · Shop · Dispatch ·
// PM · Admin · Field Leadership).
//
// iter202 fix — addresses the operational consistency gap surfaced by
// the operator: "other portals still lack visible operational
// login/training identity paths inside the Guidance ecosystem."
//
// Each portal login can pass:
//   - portal     : "hr" | "safety" | "shop" | "dispatch" | "pm" | "admin" | "leadership"
//   - identityId : guidance article id describing "what does this portal do?"
//                  (optional — until Pass 5 saturates these, falls back to
//                   /guidance which is always available)
//   - onboardId  : onboarding article id (optional)
//   - tshootId   : troubleshooting article id (optional)
//
// Missing articles → falls back to the universal /guidance landing.
// All links open the Operational Guidance Center, which is RBAC-aware
// and bilingual.
import React from "react";
import { Link } from "react-router-dom";
import { BookOpen, LifeBuoy, GraduationCap } from "lucide-react";
import { useT } from "@/lib/i18n";

const PORTAL_LABELS = {
  hr:         { en: "Human Resources",           es: "Recursos Humanos" },
  safety:     { en: "Safety Operations",         es: "Operaciones de Seguridad" },
  shop:       { en: "Shop Operations",           es: "Operaciones de Taller" },
  dispatch:   { en: "Transportation Operations", es: "Operaciones de Transporte" },
  pm:         { en: "Project Management",        es: "Gestión de Proyectos" },
  admin:      { en: "Administration",            es: "Administración" },
  leadership: { en: "Field Leadership",          es: "Liderazgo de Campo" },
};

// Pass 5a/5b/5c complete: every protected portal has the full identity
// triple (identity + onboard-first-week + tshoot-login) in the public
// guidance tier. Auto-resolve the article IDs from `portal` so each
// login page can simply render `<PortalLoginHelp portal="hr" />`.
const PORTAL_GUIDANCE = {
  hr:         { identity: "portal-hr-identity",         onboard: "onboard-hr-first-week",         tshoot: "tshoot-hr-login" },
  safety:     { identity: "portal-safety-identity",     onboard: "onboard-safety-first-week",     tshoot: "tshoot-safety-login" },
  shop:       { identity: "portal-shop-identity",       onboard: "onboard-shop-first-week",       tshoot: "tshoot-shop-login" },
  dispatch:   { identity: "portal-dispatch-identity",   onboard: "onboard-dispatch-first-week",   tshoot: "tshoot-dispatch-login" },
  pm:         { identity: "portal-pm-identity",         onboard: "onboard-pm-first-week",         tshoot: "tshoot-pm-login" },
  admin:      { identity: "portal-admin-identity",      onboard: "onboard-admin-first-week",      tshoot: "tshoot-admin-login" },
  leadership: { identity: "portal-leadership-identity", onboard: "onboard-leadership-first-week", tshoot: "tshoot-leadership-login" },
};

export function PortalLoginHelp({ portal, identityId, onboardId, tshootId }) {
  const { t, lang } = useT();
  const portalLabel = (PORTAL_LABELS[portal] || {})[lang] || (PORTAL_LABELS[portal] || {}).en || "";
  const defaults = PORTAL_GUIDANCE[portal] || {};

  // Caller can override per-link; otherwise auto-resolve from the
  // portal key. Final fallback is the universal /guidance landing.
  const onboardHref  = `/guidance/${onboardId  || defaults.onboard  || ""}`.replace(/\/$/, "/guidance");
  const identityHref = `/guidance/${identityId || defaults.identity || ""}`.replace(/\/$/, "/guidance");
  const tshootHref   = `/guidance/${tshootId   || defaults.tshoot   || "public-cant-login"}`;

  return (
    <div
      className="mt-6 pt-5 border-t border-slate-200 space-y-2"
      data-testid={`portal-login-help-${portal}`}
    >
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold flex items-center gap-1.5">
        <BookOpen className="w-3.5 h-3.5" />
        {portalLabel
          ? (lang === "es" ? `Nuevo en ${portalLabel}?` : `New to ${portalLabel}?`)
          : t("New to this portal?")}
      </div>
      <Link
        to={onboardHref}
        className="block text-sm text-amber-700 hover:text-amber-900 hover:underline inline-flex items-center gap-1.5 min-h-[44px] py-1"
        data-testid={`portal-login-help-${portal}-onboarding`}
      >
        <GraduationCap className="w-3.5 h-3.5" />
        {t("Start first-week onboarding")} →
      </Link>
      <Link
        to={identityHref}
        className="block text-sm text-amber-700 hover:text-amber-900 hover:underline inline-flex items-center gap-1.5 min-h-[44px] py-1"
        data-testid={`portal-login-help-${portal}-identity`}
      >
        <BookOpen className="w-3.5 h-3.5" />
        {portalLabel
          ? (lang === "es" ? `Cómo funciona ${portalLabel}` : `How ${portalLabel} works`)
          : t("How this portal works")}
        {" →"}
      </Link>
      <Link
        to={tshootHref}
        className="block text-sm text-slate-600 hover:text-slate-900 hover:underline inline-flex items-center gap-1.5 min-h-[44px] py-1"
        data-testid={`portal-login-help-${portal}-troubleshoot`}
      >
        <LifeBuoy className="w-3.5 h-3.5" />
        {t("Fix sign-in problems")} →
      </Link>
    </div>
  );
}
